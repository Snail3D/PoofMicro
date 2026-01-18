# ESP32 Comms Hub

This project configures an ESP32 to act as a WiFi Access Point (AP) and a simple TCP Server. It is designed to facilitate basic messaging between the ESP32 and a connected client device (e.g., Laptop, Phone, or another microcontroller).

## Features

*   **WiFi Access Point:** Creates a secure WiFi network (`ESP32_Comms_Hub`).
*   **TCP Server:** Listens for connections on port 8080.
*   **Echo/Relay:** Receives messages from clients and echoes them back, verifying the communication channel.
*   **Serial Debugging:** Outputs connection status and message content to the Serial Monitor at 115200 baud.

## Hardware Requirements

*   ESP32 Development Board
*   USB Cable for programming

## Software Requirements

*   PlatformIO (recommended) or Arduino IDE
*   Terminal client software (e.g., PuTTY, TeraTerm, or `telnet` command line)

## Configuration

Network settings can be adjusted in `include/config.h`:

*   `AP_SSID`: The name of the WiFi network.
*   `AP_PASSWORD`: The WiFi password (must be at least 8 characters).
*   `TCP_PORT`: The port the server listens on (default 8080).

## Build and Upload Instructions (PlatformIO)

1.  Clone or download this project.
2.  Open the project folder in VS Code with the PlatformIO extension installed.
3.  Connect your ESP32 via USB.
4.  Click the "Upload" arrow icon at the bottom status bar.
5.  Open the Serial Monitor to view startup logs.

## Usage

1.  **Connect to WiFi:** On your computer or phone, search for WiFi networks and connect to `ESP32_Comms_Hub` using the password `securepassword123`.
2.  **Connect to Server:** Open a TCP terminal client (like Telnet).
    *   Host: `192.168.4.1` (Default IP of ESP32 SoftAP)
    *   Port: `8080`
3.  **Send Message:** Type text and press Enter. You should see the text echoed back to you in the terminal window.
4.  **Monitor:** Check the Arduino Serial Monitor to see the raw data being received by the ESP32.

## Troubleshooting

*   **Cannot see SSID:** Ensure the ESP32 is powered adequately. Try resetting the board.
*   **Connection Refused:** Ensure you are connecting to IP `192.168.4.1` and port `8080`.
*   **Garbage Text:** Ensure your terminal client and Serial Monitor are both set to the correct baud rate (115200 for Serial, usually default for TCP).