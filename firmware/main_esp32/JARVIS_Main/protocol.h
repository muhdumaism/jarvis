/**
 * JARVIS — Protocol Definitions
 * 
 * Defines binary structures for ESP-NOW packets and shared constants.
 * Must match PROTOCOL.md exactly.
 */

#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <Arduino.h>

// ESP-NOW Message Type Constants
enum JarvisMessageType {
    MSG_HEARTBEAT       = 0x01,
    MSG_HEARTBEAT_ACK   = 0x02,
    MSG_DEVICE_COMMAND  = 0x10,
    MSG_DEVICE_ACK      = 0x11,
    MSG_DEVICE_STATE    = 0x12,
    MSG_STATE_REQUEST   = 0x13,
    MSG_STATE_RESPONSE  = 0x14,
    MSG_SENSOR_DATA     = 0x20,
    MSG_CONFIG_SET      = 0x30,
    MSG_CONFIG_ACK      = 0x31,
    MSG_PING            = 0xF0,
    MSG_PONG            = 0xF1,
};

// Binary ESP-NOW Packet Struct (Max 250 bytes)
struct __attribute__((packed)) JarvisPacket {
    uint8_t  version;        // Protocol version (1)
    uint8_t  type;           // Message type (JarvisMessageType)
    uint8_t  source[6];      // MAC address of sender
    uint8_t  destination[6]; // MAC address of receiver
    uint16_t message_id;     // Sequential transaction ID
    uint8_t  payload_len;    // Length of payload
    uint8_t  payload[229];   // Payload buffer (250 - 21 header bytes)
};

// Device Command Payload Struct
struct __attribute__((packed)) DeviceCommandPayload {
    char     device_id[16];  // Null-terminated device ID
    uint8_t  channel;        // Relay index
    uint8_t  action;         // 0 = OFF, 1 = ON, 2 = TOGGLE
};

// Device State Payload Struct
struct __attribute__((packed)) DeviceStatePayload {
    char     device_id[16];  // Null-terminated device ID
    uint8_t  channel;
    uint8_t  state;          // 0 = OFF, 1 = ON
    uint8_t  confirmed;      // 1 = Relay confirmed
};

// Heartbeat Payload Struct
struct __attribute__((packed)) HeartbeatPayload {
    char     node_id[16];    // Null-terminated node ID
    uint32_t uptime;         // Seconds since boot
    uint32_t free_heap;      // Heap size
    uint8_t  device_count;
    uint8_t  device_states;  // Bitmask of relay states
};

#endif // PROTOCOL_H
