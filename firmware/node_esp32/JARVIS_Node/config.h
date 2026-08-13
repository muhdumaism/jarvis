/**
 * JARVIS Secondary Node Configuration Header
 * 
 * Centralizes GPIO allocations and boot properties for the ESP32-S3 relay module.
 */

#ifndef CONFIG_H
#define CONFIG_H

// Node Identity Configuration
#define NODE_ID             "room_node_01" // Unique node identifier on network
#define CHIP_TYPE           "esp32s3"

// ============================================================
// GPIO Allocation (ESP32-S3)
// ============================================================
#define RELAY_1_PIN         4
#define RELAY_2_PIN         5

// Active low relay triggers config (Common on 5V relay shields)
// Set to true if relay closes when pin is LOW.
#define RELAY_ACTIVE_LOW    true 

// ============================================================
// ESP-NOW Configuration
// ============================================================
#define ESP_NOW_CHANNEL     6   // Must match coordinator WiFi channel
#define HEARTBEAT_INTERVAL  15000 // Send heartbeat to gateway every 15s

#endif // CONFIG_H
