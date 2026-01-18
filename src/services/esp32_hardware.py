import asyncio
import serial
import serial.tools.list_ports
from typing import Optional, Dict, Any, List
from pathlib import Path
import time

from config import settings


class ESP32Hardware:
    """ESP32 Hardware Operations: Upload, Monitor, Test"""

    def __init__(self):
        self.serial_conn: Optional[serial.Serial] = None
        self.baud_rate = 115200
        self.timeout = 5

    def list_ports(self) -> List[Dict[str, str]]:
        """List available serial ports"""
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append({
                "device": port.device,
                "description": port.description or "",
                "hwid": port.hwid or "",
                "vid": hex(port.vid) if hasattr(port, 'vid') else "0000",
                "pid": hex(port.pid) if hasattr(port, 'pid') else "0000",
            })
        return ports

    async def detect_esp32(self) -> Optional[str]:
        """Detect ESP32 connected to USB"""
        ports = self.list_ports()
        esp32_vids = ["0x10c4", "0x1a86", "0x0403", "0x303a"]  # Common USB-serial chip VIDs

        for port in ports:
            # Check if it's likely an ESP32
            desc_lower = port['description'].lower()
            if any(vid in port['vid'] for vid in esp32_vids) or \
               'ch340' in desc_lower or 'cp210' in desc_lower or 'ft232' in desc_lower or \
               'usb serial' in desc_lower or 'uart' in desc_lower:
                return port['device']

        # Fallback: first usb serial port
        for port in ports:
            if 'usbserial' in port['device'].lower():
                return port['device']

        return None

    async def connect(self, port: Optional[str] = None) -> bool:
        """Connect to ESP32 over serial"""
        if port is None:
            port = await self.detect_esp32()

        if port is None:
            return False

        try:
            self.serial_conn = serial.Serial(
                port=port,
                baudrate=self.baud_rate,
                timeout=self.timeout,
                write_timeout=5
            )
            # Reset the connection
            self.serial_conn.setDTR(False)
            time.sleep(0.1)
            self.serial_conn.setDTR(True)
            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"Serial connect error: {e}")
            return False

    def disconnect(self):
        """Disconnect from serial"""
        if self.serial_conn:
            try:
                self.serial_conn.close()
            except:
                pass
            self.serial_conn = None

    async def upload_firmware(self, firmware_path: Path, port: Optional[str] = None) -> Dict[str, Any]:
        """Upload firmware to ESP32 using esptool"""
        import subprocess

        if port is None:
            port = await self.detect_esp32()
            if port is None:
                return {"success": False, "error": "No ESP32 detected"}

        # Build esptool command
        cmd = [
            "esptool.py",
            "--chip", "esp32",
            "--port", port,
            "--baud", "460800",
            "write_flash",
            "0x10000", str(firmware_path)
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            success = result.returncode == 0

            return {
                "success": success,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "port": port,
                "error": None if success else result.stderr
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Upload timeout"}
        except FileNotFoundError:
            # esptool not installed, try platformio
            return await self.upload_with_platformio(firmware_path, port)
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def upload_with_platformio(self, firmware_path: Path, port: str) -> Dict[str, Any]:
        """Fallback: Upload using platformio"""
        import subprocess

        cmd = [
            "platformio", "run",
            "--target", "upload",
            "--upload-port", port
        ]

        # Change to project directory
        project_dir = firmware_path.parent.parent

        try:
            result = subprocess.run(
                cmd,
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                timeout=120
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "port": port,
                "error": result.stderr if result.returncode != 0 else None
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def read_serial(self, duration: float = 5.0) -> List[str]:
        """Read from serial for specified duration"""
        if not self.serial_conn:
            if not await self.connect():
                return []

        lines = []
        start_time = time.time()

        while time.time() - start_time < duration:
            try:
                if self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        lines.append(line)
            except:
                break
            await asyncio.sleep(0.1)

        return lines

    async def run_test(self, test_code: str, timeout: float = 30.0) -> Dict[str, Any]:
        """Upload and run test code on ESP32"""
        # This would create a test sketch, upload it, and monitor output
        results = {
            "success": False,
            "output": [],
            "test_passed": False,
            "error": None
        }

        # Connect to serial
        if not await self.connect():
            results["error"] = "Could not connect to ESP32"
            return results

        try:
            # Read serial output for test results
            output = await self.read_serial(timeout)

            results["output"] = output
            results["success"] = True

            # Analyze output for test results
            for line in output:
                if "PASS" in line.upper() or "OK" in line.upper():
                    results["test_passed"] = True
                elif "FAIL" in line.upper() or "ERROR" in line.upper():
                    results["test_passed"] = False
                    break

        except Exception as e:
            results["error"] = str(e)

        finally:
            self.disconnect()

        return results

    async def monitor_serial(self, callback=None, duration: float = 60.0):
        """Monitor serial output and call callback for each line"""
        if not await self.connect():
            return

        try:
            start_time = time.time()
            while time.time() - start_time < duration:
                if self.serial_conn and self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                    if line and callback:
                        await callback(line)
                await asyncio.sleep(0.05)

        finally:
            self.disconnect()

    def get_status(self) -> Dict[str, Any]:
        """Get current hardware status"""
        return {
            "connected": self.serial_conn is not None,
            "port": self.serial_conn.port if self.serial_conn else None,
            "baud_rate": self.baud_rate if self.serial_conn else None,
            "available_ports": self.list_ports()
        }


# Global hardware instance
hardware = ESP32Hardware()
