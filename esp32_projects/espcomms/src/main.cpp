/**
 * ESP32 Communications Hub (AP Mode)
 * 
 * This sketch creates a WiFi Access Point and starts a TCP Server.
 * It allows clients to connect and send messages. The ESP32 acts as a
 * simple relay/echo server to demonstrate communication capabilities.
 */

#include <Arduino.h>
#include <WiFi.h>
#include "config.h"

// Global server object listening on the defined port
WiFiServer server(TCP_PORT);

// Current connected client
WiFiClient currentClient;

void setup() {
  // Initialize Serial communication for debugging
  Serial.begin(SERIAL_BAUD_RATE);
  while (!Serial) {
    ; // Wait for serial port to connect (needed for some USB-serial adapters)
  }
  
  delay(1000);
  Serial.println("\n--- ESP32 Comms Hub Starting ---");

  // 1. Configure Access Point
  Serial.print("Setting up AP (Access Point)...");
  
  // We explicitly set the mode to AP to ensure it doesn't try to connect to a router
  WiFi.mode(WIFI_AP);

  // Start the AP
  bool result = WiFi.softAP(AP_SSID, AP_PASSWORD, AP_CHANNEL, 0, MAX_CONNECTIONS);

  if (!result) {
    Serial.println("Failed!");
    Serial.println("Unable to start Access Point. Halting execution.");
    while (1) {
      delay(1000); // Halt on error
    }
  }

  Serial.println("Success!");

  // 2. Display Network Details
  Serial.println("Access Point Configuration:");
  Serial.print("SSID: ");
  Serial.println(AP_SSID);
  Serial.print("Password: ");
  Serial.println(AP_PASSWORD);
  Serial.print("IP Address: ");
  Serial.println(WiFi.softAPIP()); // Usually 192.168.4.1
  Serial.print("MAC Address: ");
  Serial.println(WiFi.softAPmacAddress());

  // 3. Start TCP Server
  server.begin();
  server.setNoDelay(true); // Disable Nagle's algorithm for faster small packet transmission
  
  Serial.println("TCP Server started on port " + String(TCP_PORT));
  Serial.println("Waiting for clients...");
}

void loop() {
  // Check for new client connections if we don't have one
  if (!currentClient || !currentClient.connected()) {
    if (currentClient) {
      // Clean up disconnected client
      currentClient.stop();
      Serial.println("Client disconnected.");
    }

    // Attempt to accept a new connection
    currentClient = server.available();
    
    if (currentClient) {
      Serial.println("New client connected!");
      Serial.print("Client IP: ");
      Serial.println(currentClient.remoteIP());
      
      // Send a welcome message to the client
      currentClient.println("Welcome to ESP32 Comms Hub.");
      currentClient.println("Send a message and it will be echoed back.");
      currentClient.println("> "); 
    }
  }

  // Handle data from connected client
  if (currentClient && currentClient.connected()) {
    if (currentClient.available()) {
      // Read incoming byte
      char c = currentClient.read();
      
      // Echo to Serial Monitor for debugging
      Serial.write(c);

      // Echo back to the client (Loopback)
      currentClient.write(c);

      // If newline is received, send prompt again
      if (c == '\n') {
        currentClient.print("> ");
      }
    }
  }

  // Small delay to prevent watchdog triggering in heavy load scenarios
  // (though typically not needed with yield() inside WiFi libs)
  delay(10); 
}