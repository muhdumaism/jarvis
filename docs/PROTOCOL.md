# JARVIS — Communication Protocol Specification

All server code, ESP32 firmware, and dashboard code MUST implement this exact protocol. Do not independently invent message formats.

---

## 1. WebSocket Protocol

### 1.1 Connection

**Endpoint**: `ws://<server>:8000/ws`

**Authentication**: First message must be an `AUTH` message:
```json
{
  "type": "AUTH",
  "token": "<api_key_or_jwt>",
  "client_type": "esp32_main" | "esp32_node" | "dashboard",
  "client_id": "main_esp32_01",
  "firmware_version": "1.0.0"
}
```

**Response**:
```json
{
  "type": "AUTH_RESPONSE",
  "success": true,
  "server_time": "2024-01-01T00:00:00Z"
}
```

### 1.2 Heartbeat

**Interval**: 30 seconds from client, server expects within 60 seconds.

```json
{
  "type": "HEARTBEAT",
  "client_id": "main_esp32_01",
  "uptime": 3600,
  "free_heap": 180000,
  "wifi_rssi": -45
}
```

**Response**:
```json
{
  "type": "HEARTBEAT_ACK",
  "server_time": "2024-01-01T00:00:00Z"
}
```

### 1.3 Message Types

Every message has a `type` field and optional `message_id` (UUID for correlation).

#### Voice Events

```json
{"type": "VOICE_START", "message_id": "uuid", "timestamp": "iso8601"}
```
```json
{"type": "VOICE_AUDIO", "message_id": "uuid", "audio": "<base64 PCM>", "seq": 0}
```
```json
{"type": "VOICE_END", "message_id": "uuid"}
```
```json
{"type": "VOICE_CANCEL", "message_id": "uuid"}
```

#### Assistant Events (Server → Clients)

```json
{"type": "VOICE_LISTENING", "message_id": "uuid"}
```
```json
{"type": "VOICE_THINKING", "message_id": "uuid"}
```
```json
{
  "type": "VOICE_TRANSCRIBED",
  "message_id": "uuid",
  "text": "turn on the fan"
}
```
```json
{
  "type": "ASSISTANT_INTENT",
  "message_id": "uuid",
  "intent": "device_control",
  "target": "bedroom_fan",
  "action": "turn_on"
}
```
```json
{
  "type": "ASSISTANT_EXECUTING",
  "message_id": "uuid",
  "description": "Turning on bedroom fan"
}
```
```json
{
  "type": "ASSISTANT_RESPONSE",
  "message_id": "uuid",
  "text": "Sure, the fan is on.",
  "success": true
}
```
```json
{
  "type": "ASSISTANT_ERROR",
  "message_id": "uuid",
  "error": "Device not found: unknown_device",
  "code": "DEVICE_NOT_FOUND"
}
```

#### TTS Audio (Server → Main ESP32)

```json
{
  "type": "TTS_START",
  "message_id": "uuid",
  "sample_rate": 22050,
  "channels": 1,
  "bit_depth": 16,
  "total_chunks": 10
}
```
```json
{
  "type": "TTS_AUDIO",
  "message_id": "uuid",
  "chunk": 0,
  "audio": "<base64 PCM>"
}
```
```json
{"type": "TTS_END", "message_id": "uuid"}
```

#### Device Events

```json
{
  "type": "DEVICE_COMMAND",
  "message_id": "uuid",
  "device_id": "room_fan",
  "node_id": "room_node_01",
  "action": "turn_on",
  "source": "voice" | "dashboard" | "automation" | "scene"
}
```
```json
{
  "type": "DEVICE_STATE_CHANGED",
  "message_id": "uuid",
  "device_id": "room_fan",
  "state": "on",
  "confirmed": true,
  "changed_at": "iso8601"
}
```
```json
{
  "type": "DEVICE_STATE_PENDING",
  "message_id": "uuid",
  "device_id": "room_fan",
  "requested_state": "on"
}
```
```json
{
  "type": "DEVICE_STATE_FAILED",
  "message_id": "uuid",
  "device_id": "room_fan",
  "error": "Node offline",
  "code": "NODE_OFFLINE"
}
```

#### Node Events

```json
{
  "type": "NODE_ONLINE",
  "node_id": "room_node_01",
  "firmware_version": "1.0.0",
  "device_count": 2
}
```
```json
{
  "type": "NODE_OFFLINE",
  "node_id": "room_node_01",
  "last_seen": "iso8601"
}
```

#### Music Events

```json
{
  "type": "MUSIC_STATE",
  "is_playing": true,
  "track": {
    "title": "Blinding Lights",
    "artist": "The Weeknd",
    "album": "After Hours",
    "album_art_url": "/api/music/album-art",
    "duration_ms": 200000,
    "position_ms": 84000
  }
}
```
```json
{
  "type": "MUSIC_COMMAND",
  "action": "play" | "pause" | "next" | "previous" | "seek" | "volume",
  "value": null
}
```

#### System Events

```json
{
  "type": "SYSTEM_STATUS",
  "server_uptime": 86400,
  "cpu_percent": 12.5,
  "ram_percent": 45.2,
  "disk_percent": 23.1,
  "db_size_mb": 5.2,
  "ws_connections": 2,
  "stt_status": "ready",
  "tts_status": "ready",
  "ai_status": "ready",
  "spotify_status": "connected"
}
```
```json
{
  "type": "ERROR",
  "code": "string",
  "message": "string",
  "component": "string"
}
```
```json
{
  "type": "NOTIFICATION",
  "level": "info" | "warning" | "error",
  "title": "string",
  "message": "string"
}
```

---

## 2. REST API

### 2.1 Authentication

```
POST /api/auth/login
  Body: {"username": "admin", "password": "..."}
  Response: {"token": "jwt...", "expires_in": 86400}

POST /api/auth/refresh
  Header: Authorization: Bearer <token>
  Response: {"token": "new_jwt...", "expires_in": 86400}
```

### 2.2 Rooms

```
GET    /api/rooms              → Room[]
POST   /api/rooms              → Room
GET    /api/rooms/{id}         → Room
PUT    /api/rooms/{id}         → Room
DELETE /api/rooms/{id}         → {success: true}
```

### 2.3 Devices

```
GET    /api/devices                     → Device[]
POST   /api/devices                     → Device
GET    /api/devices/{id}                → Device
PUT    /api/devices/{id}                → Device
DELETE /api/devices/{id}                → {success: true}
POST   /api/devices/{id}/control        → {message_id, state: "pending"}
  Body: {"action": "turn_on" | "turn_off" | "toggle"}
GET    /api/devices/{id}/state          → DeviceState
GET    /api/devices/{id}/history        → DeviceState[]
```

### 2.4 Nodes

```
GET    /api/nodes              → Node[]
POST   /api/nodes              → Node
GET    /api/nodes/{id}         → Node
PUT    /api/nodes/{id}         → Node
DELETE /api/nodes/{id}         → {success: true}
```

### 2.5 Music

```
GET    /api/music/state                 → MusicState
POST   /api/music/play                  → {success: true}
POST   /api/music/pause                 → {success: true}
POST   /api/music/next                  → {success: true}
POST   /api/music/previous              → {success: true}
POST   /api/music/seek                  → {success: true}
  Body: {"position_ms": 60000}
POST   /api/music/volume                → {success: true}
  Body: {"volume_percent": 50}
POST   /api/music/search-play           → {success: true}
  Body: {"query": "Blinding Lights"}
GET    /api/music/album-art             → image/jpeg (resized for ESP32)
```

### 2.6 Automations

```
GET    /api/automations                 → Automation[]
POST   /api/automations                 → Automation
GET    /api/automations/{id}            → Automation
PUT    /api/automations/{id}            → Automation
DELETE /api/automations/{id}            → {success: true}
POST   /api/automations/{id}/enable     → Automation
POST   /api/automations/{id}/disable    → Automation
POST   /api/automations/{id}/test       → {success: true, result: ...}
```

### 2.7 Scenes

```
GET    /api/scenes                      → Scene[]
POST   /api/scenes                      → Scene
GET    /api/scenes/{id}                 → Scene
PUT    /api/scenes/{id}                 → Scene
DELETE /api/scenes/{id}                 → {success: true}
POST   /api/scenes/{id}/activate        → {success: true, results: [...]}
```

### 2.8 Firmware

```
GET    /api/firmware                    → FirmwareVersion[]
POST   /api/firmware/upload             → FirmwareVersion
  Multipart: file, chip_type, version, description
GET    /api/firmware/{id}/download      → binary
GET    /api/firmware/{id}/info          → FirmwareVersion (with hash)
DELETE /api/firmware/{id}               → {success: true}
```

### 2.9 Settings

```
GET    /api/settings                    → Settings
PUT    /api/settings                    → Settings
POST   /api/settings/backup             → {download_url: "..."}
POST   /api/settings/restore            → {success: true}
  Multipart: file (SQLite backup)
```

### 2.10 System

```
GET    /api/system/status               → SystemStatus
GET    /api/system/events               → Event[] (paginated, filterable)
GET    /api/system/events/stream        → SSE stream (live events)
```

---

## 3. ESP-NOW Protocol

### 3.1 Packet Format

Binary struct, max 250 bytes total.

```c
typedef struct __attribute__((packed)) {
    uint8_t  version;        // Protocol version (1)
    uint8_t  type;           // Message type enum
    uint8_t  source[6];      // Source MAC address
    uint8_t  destination[6]; // Destination MAC (or broadcast)
    uint16_t message_id;     // Unique message ID (wraps at 65535)
    uint8_t  payload_len;    // Length of payload
    uint8_t  payload[229];   // Payload data (250 - 21 header bytes)
} JarvisPacket;
```

### 3.2 Message Types

```c
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
```

### 3.3 Device Command Payload

```c
typedef struct __attribute__((packed)) {
    char     device_id[16];  // Null-terminated device ID
    uint8_t  channel;        // Relay channel (0-based)
    uint8_t  action;         // 0=OFF, 1=ON, 2=TOGGLE
} DeviceCommandPayload;
```

### 3.4 Device State Payload

```c
typedef struct __attribute__((packed)) {
    char     device_id[16];  // Null-terminated device ID
    uint8_t  channel;        // Relay channel
    uint8_t  state;          // 0=OFF, 1=ON
    uint8_t  confirmed;      // 1=confirmed (relay actually changed)
} DeviceStatePayload;
```

### 3.5 Heartbeat Payload

```c
typedef struct __attribute__((packed)) {
    char     node_id[16];    // Null-terminated node ID
    uint32_t uptime;         // Seconds since boot
    uint32_t free_heap;      // Free heap bytes
    uint8_t  device_count;   // Number of devices
    uint8_t  device_states;  // Bitmask of relay states (up to 8)
} HeartbeatPayload;
```

### 3.6 Sensor Data Payload

```c
typedef struct __attribute__((packed)) {
    char     sensor_id[16];  // Null-terminated sensor ID
    uint8_t  sensor_type;    // 0=temperature, 1=humidity, 2=light
    float    value;          // Sensor reading
} SensorDataPayload;
```

### 3.7 Acknowledgement & Retry

1. Sender transmits packet with unique `message_id`
2. Receiver processes and sends ACK with same `message_id`
3. If no ACK within timeout, sender retries:
   - Retry 1: after 500ms
   - Retry 2: after 1000ms
   - Retry 3: after 2000ms
4. After 3 retries with no ACK: mark node as potentially offline
5. Duplicate detection: receiver tracks last 16 message_ids per peer, ignores duplicates

### 3.8 Heartbeat Schedule

- **Node → Main ESP32**: Every 15 seconds
- If main ESP32 misses 3 consecutive heartbeats (45s): node marked offline
- When node comes back online: full state synchronization

---

## 4. Correlation IDs

Every voice command generates a UUID that flows through the entire pipeline:

```
VOICE_START (message_id = "abc-123")
  → VOICE_AUDIO (message_id = "abc-123")
  → VOICE_END (message_id = "abc-123")
  → VOICE_TRANSCRIBED (message_id = "abc-123")
  → ASSISTANT_INTENT (message_id = "abc-123")
  → DEVICE_COMMAND (message_id = "abc-123")
  → ESP-NOW packet (message_id = mapped_uint16)
  → DEVICE_STATE_CHANGED (message_id = "abc-123")
  → ASSISTANT_RESPONSE (message_id = "abc-123")
  → TTS_START (message_id = "abc-123")
  → TTS_AUDIO (message_id = "abc-123")
  → TTS_END (message_id = "abc-123")
```

The ESP-NOW `uint16` message_id is mapped to/from the UUID on the main ESP32.

---

## 5. Error Codes

```
AUTH_FAILED          - Authentication failed
AUTH_EXPIRED         - Token expired
DEVICE_NOT_FOUND     - Device ID not in registry
NODE_NOT_FOUND       - Node ID not in registry
NODE_OFFLINE         - Node not responding
INVALID_ACTION       - Action not valid for device type
INVALID_PARAMETERS   - Missing or invalid parameters
COMMAND_TIMEOUT      - No ACK from node within timeout
STT_UNAVAILABLE      - STT engine not ready
TTS_UNAVAILABLE      - TTS engine not ready
AI_UNAVAILABLE       - Ollama not responding
SPOTIFY_UNAVAILABLE  - Spotify bridge not connected
SPOTIFY_AUTH_FAILED  - Spotify token refresh failed
RATE_LIMITED         - Too many requests
INTERNAL_ERROR       - Server internal error
FIRMWARE_INVALID     - Invalid firmware binary
FIRMWARE_MISMATCH    - Firmware doesn't match target chip
```

---

## 6. Audio Format

### Microphone → Server

- Format: Raw PCM
- Sample rate: 16000 Hz
- Bit depth: 16-bit signed
- Channels: 1 (mono)
- Encoding in WebSocket: Base64
- Chunk size: 4096 bytes (~128ms of audio)

### TTS Server → ESP32

- Format: Raw PCM
- Sample rate: 22050 Hz (Piper default, configurable)
- Bit depth: 16-bit signed
- Channels: 1 (mono)
- Encoding in WebSocket: Base64
- Chunk size: 4096 bytes

---

## 7. State Machines

### Device State

```
UNKNOWN → PENDING → ON/OFF (confirmed)
                  → FAILED (timeout/error)
```

### Voice State

```
IDLE → LISTENING → THINKING → EXECUTING → SPEAKING → IDLE
                                        → ERROR → IDLE
```

### Node State

```
UNKNOWN → ONLINE → OFFLINE → ONLINE
```

### Music State

```
IDLE → PLAYING → PAUSED → PLAYING
              → STOPPED → IDLE
```
