import asyncio
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime

from zhipuai import ZhipuAI
from config import settings


@dataclass
class BuildContext:
    """Context for ESP32 project build"""
    project_name: str
    board_type: str
    description: str
    features: List[str] = field(default_factory=list)
    libraries: List[Dict[str, str]] = field(default_factory=list)
    wifi_config: Optional[Dict[str, str]] = None
    custom_code: Optional[str] = None
    board_context: Optional[str] = None
    materials: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "board_type": self.board_type,
            "description": self.description,
            "features": self.features,
            "libraries": self.libraries,
            "wifi_config": self.wifi_config,
            "custom_code": self.custom_code,
            "board_context": self.board_context,
            "materials": self.materials,
        }


@dataclass
class BuildResult:
    """Result of a build operation"""
    success: bool
    project_path: Optional[Path] = None
    code_files: Dict[str, str] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    platformio_ini: str = ""
    error: Optional[str] = None
    build_log: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ESP32Builder:
    """ESP32 Program Builder using GLM 4.7"""

    def __init__(self):
        self.client = ZhipuAI(api_key=settings.glm_api_key)
        self.model = settings.glm_model
        self.projects_path = Path(settings.esp32_projects_path)
        self.projects_path.mkdir(exist_ok=True)

    async def search_libraries(self, query: str, board_type: str = "esp32") -> List[Dict[str, str]]:
        """Search for ESP32 libraries using GLM 4.7"""
        prompt = f"""Search for ESP32 libraries related to: {query}

Board type: {board_type}

Return a JSON array of libraries with this exact structure:
[
  {{
    "name": "Library Name",
    "version": "1.0.0",
    "author": "Author Name",
    "url": "https://github.com/...",
    "description": "Brief description",
    "platformio_name": "library_name"
  }}
]

Only return valid JSON, no other text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an ESP32 library expert. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )

            content = response.choices[0].message.content.strip()

            # Clean up markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            libraries = json.loads(content)
            return libraries if isinstance(libraries, list) else []

        except Exception as e:
            print(f"Library search error: {e}")
            return []

    async def search_materials(self, query: str, board_type: str = "esp32") -> List[Dict[str, Any]]:
        """Search for ESP32 project materials, components, and references"""
        prompt = f"""Search for ESP32 project materials and components related to: {query}

Board type: {board_type}

Return a JSON array of materials with this exact structure:
[
  {{
    "name": "Component/Material Name",
    "category": "sensor|actuator|communication|power|display|other",
    "description": "Description of what it does",
    "pin_count": 4,
    "voltage": "3.3V",
    "protocol": "I2C|SPI|UART|GPIO|Analog",
    "library_needed": "Library Name",
    "example_url": "https://...",
    "typical_use_case": "Brief use case description"
  }}
]

Only return valid JSON, no other text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an ESP32 hardware expert. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )

            content = response.choices[0].message.content.strip()

            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            materials = json.loads(content)
            return materials if isinstance(materials, list) else []

        except Exception as e:
            print(f"Materials search error: {e}")
            return []

    async def generate_code(self, context: BuildContext) -> BuildResult:
        """Generate ESP32 code using GLM 4.7"""
        result = BuildResult(success=False)

        # Build the prompt with all context
        prompt = self._build_generation_prompt(context)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
            )

            content = response.choices[0].message.content

            # Parse the response
            parsed = self._parse_generation_response(content)
            result.code_files = parsed.get("files", {})
            result.platformio_ini = parsed.get("platformio_ini", "")
            result.config = parsed.get("config", {})

            # Create project directory and files
            project_path = self.projects_path / context.project_name.replace(" ", "_").lower()
            project_path.mkdir(exist_ok=True)

            result.project_path = project_path

            # Write generated files
            for filename, code_content in result.code_files.items():
                file_path = project_path / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(code_content)

            # Write platformio.ini
            if result.platformio_ini:
                (project_path / "platformio.ini").write_text(result.platformio_ini)

            result.success = True
            result.build_log.append(f"Project created at: {project_path}")

        except Exception as e:
            result.error = str(e)
            result.build_log.append(f"Error: {e}")

        return result

    def _get_system_prompt(self) -> str:
        return """You are an expert ESP32 developer. Generate clean, well-documented C++ code for ESP32 projects.

Always respond with valid JSON in this exact format:
{
  "files": {
    "src/main.cpp": "// code here",
    "include/config.h": "// code here"
  },
  "platformio_ini": "// platformio.ini content",
  "config": {
    "board": "esp32dev",
    "framework": "arduino",
    "lib_deps": ["lib1", "lib2"]
  }
}

Requirements:
- Use modern C++ practices
- Include comprehensive comments
- Follow Arduino/ESP32 conventions
- Handle errors appropriately
- Include Serial debugging at 115200 baud
- Never use emojis
- Keep code modular and organized"""

    def _build_generation_prompt(self, context: BuildContext) -> str:
        prompt = f"""Generate a complete ESP32 project with the following specifications:

Project Name: {context.project_name}
Board Type: {context.board_type}
Description: {context.description}

Features requested:
{chr(10).join(f'- {f}' for f in context.features) if context.features else '- Basic functionality'}

"""

        if context.board_context:
            prompt += f"\nBoard Context:\n{context.board_context}\n"

        if context.libraries:
            prompt += "\nLibraries to use:\n"
            for lib in context.libraries:
                prompt += f"- {lib.get('name', 'N/A')}: {lib.get('description', '')}\n"

        if context.materials:
            prompt += "\nHardware Components:\n"
            for mat in context.materials:
                prompt += f"- {mat.get('name', 'N/A')}: {mat.get('description', '')}\n"

        if context.wifi_config:
            prompt += f"\nWiFi Configuration: SSID will be provided at runtime\n"

        if context.custom_code:
            prompt += f"\nCustom Code Snippet to include:\n{context.custom_code}\n"

        prompt += """
Generate:
1. All necessary source files (main.cpp, headers)
2. platformio.ini configuration
3. Proper library dependencies
4. WiFi/AP functionality if requested
5. Error handling and serial debugging
6. README with build instructions

Respond only with valid JSON."""

        return prompt

    def _parse_generation_response(self, content: str) -> Dict[str, Any]:
        """Parse the GLM response"""
        try:
            # Clean up markdown code blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback: try to extract JSON from response
            try:
                start = content.find("{")
                end = content.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(content[start:end])
            except:
                pass

            return {"files": {}, "platformio_ini": "", "config": {}}


class ESP32Simulator:
    """WACWI-like ESP32 simulator for testing"""

    def __init__(self):
        self.active_simulations: Dict[str, Any] = {}

    async def simulate_project(self, project_path: Path, board_type: str = "esp32") -> Dict[str, Any]:
        """Simulate an ESP32 project without actual hardware"""
        project_name = project_path.name

        simulation = {
            "project_name": project_name,
            "board_type": board_type,
            "status": "starting",
            "ip_address": None,
            "ap_ssid": None,
            "web_server": False,
            "logs": [],
            "started_at": datetime.now().isoformat(),
        }

        self.active_simulations[project_name] = simulation

        # Read and analyze main.cpp
        main_cpp = project_path / "src" / "main.cpp"

        if main_cpp.exists():
            code = main_cpp.read_text()

            # Check for WiFi
            if "WiFi" in code or "WIFI" in code:
                simulation["has_wifi"] = True
                simulation["ip_address"] = "192.168.1.100"  # Simulated IP

            # Check for AP mode
            if "WiFi.softAP" in code or "softAP" in code:
                simulation["ap_ssid"] = f"{project_name}_AP"
                simulation["ip_address"] = "192.168.4.1"

            # Check for web server
            if "WebServer" in code or "server.begin" in code or "HTTPServer" in code:
                simulation["web_server"] = True

            simulation["status"] = "running"
            simulation["logs"].append("Simulation started successfully")
            simulation["logs"].append(f"Board: {board_type}")
            if simulation.get("ip_address"):
                simulation["logs"].append(f"IP Address: {simulation['ip_address']}")
            if simulation.get("ap_ssid"):
                simulation["logs"].append(f"AP SSID: {simulation['ap_ssid']}")
            if simulation.get("web_server"):
                simulation["logs"].append(f"Web server running on http://{simulation['ip_address']}")
        else:
            simulation["status"] = "error"
            simulation["logs"].append("Error: main.cpp not found")

        return simulation

    def get_simulation(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Get simulation status"""
        return self.active_simulations.get(project_name)

    def stop_simulation(self, project_name: str) -> bool:
        """Stop a simulation"""
        if project_name in self.active_simulations:
            del self.active_simulations[project_name]
            return True
        return False
