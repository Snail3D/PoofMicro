#ifndef CONFIG_H
#define CONFIG_H

// WiFi Access Point Configuration
#define AP_SSID "ESP32_Comms_Hub"
#define AP_PASSWORD "securepassword123"

// The AP channel (1-13)
#define AP_CHANNEL 1

// Maximum number of clients connected to the AP
#define MAX_CONNECTIONS 4

// TCP Server Configuration
#define TCP_PORT 8080

// Serial Debug Configuration
#define SERIAL_BAUD_RATE 115200

#endif // CONFIG_H