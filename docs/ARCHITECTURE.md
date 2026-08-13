# JARVIS — System Architecture

## Overview

JARVIS is a local-first AI room assistant. All processing happens on the local network. The system consists of a home server, a main ESP32 physical unit, and secondary ESP32-S3 relay nodes communicating via ESP-NOW.

---

## 1. System Topology

```
                         LOCAL LAN
                              |
                  +-----------------------+
                  |      JARVIS server      |
                  |  (FastAPI + SQLite)   |
                  |                       |
                  | ┌───────────────────┐ |
                  | │ WebSocket Manager │ |
                  | │ Device Manager    │ |
                  | │ Voice Pipeline    │ |
                  | │ Automation Engine │ |
                  | │ Scene Manager     │ |
                  | │ Spotify Bridge    │ |
                  | │ Firmware Manager  │ |
                  | └───────────────────┘ |
                  +-----------+-----------+
                              |
                    WebSocket (ws://)
                              |
                    +---------v---------+
                    |    MAIN ESP32     |
                    |   (WROOM-32)      |
                    |                   |
                    | INMP441  (I2S0)   |
                    | I2S Amp  (I2S1)   |
                    | 2.8" TFT (HSPI)   |
                    | ESP-NOW Gateway   |
                    +---------+---------+
                              |
                           ESP-NOW
                              |
                    +---------v---------+
                    |   NODE ESP32-S3   |
                    |                   |
                    |  Relay 1 (Fan)    |
                    |  Relay 2 (Light)  |
                    +-------------------+
```

Spotify audio remains on the user's phone → Bluetooth speaker path. JARVIS voice responses use a separate local speaker via the I2S amplifier.

---

## 2. Backend Architecture

### 2.1 Application Structure

Single FastAPI application with modular components. No microservices.

```
FastAPI App
├── Lifespan Manager (startup/shutdown)
├── Middleware
│   ├── CORS
│   ├── Rate Limiting
│   ├── Authentication
│   └── Structured Logging
├── REST API Routers
│   ├── /api/auth
│   ├── /api/rooms
│   ├── /api/devices
│   ├── /api/nodes
│   ├── /api/music
│   ├── /api/automations
│   ├── /api/scenes
│   ├── /api/firmware
│   ├── /api/settings
│   ├── /api/system
│   └── /api/events
├── WebSocket Endpoint
│   └── /ws
└── Services (Singletons via lifespan)
    ├── DatabaseManager
    ├── DeviceManager
    ├── NodeManager
    ├── WebSocketManager
    ├── VoicePipeline
    ├── AutomationEngine
    ├── SceneManager
    ├── SpotifyBridge
    ├── FirmwareManager
    └── EventBus
```

### 2.2 Service Lifecycle

All services are initialized during FastAPI lifespan startup:

1. Database initialized (SQLite, tables created/migrated)
2. EventBus created (in-process async pub/sub)
3. DeviceManager loads devices from DB
4. NodeManager loads nodes from DB
5. WebSocketManager started
6. VoicePipeline initialized (loads STT model, TTS engine)
7. AutomationEngine started (scheduler)
8. SpotifyBridge initialized (token refresh)
9. FirmwareManager scans firmware directory

On shutdown, all services gracefully close connections and flush state.

### 2.3 Event Bus

In-process async event bus using `asyncio.Queue`. No external message broker.

```
Publisher → EventBus → [Subscriber1, Subscriber2, ...]
```

Events flow between services without direct coupling. Example: DeviceManager publishes `DEVICE_STATE_CHANGED` → WebSocketManager broadcasts to connected clients, AutomationEngine evaluates triggers.

---

## 3. Frontend Architecture

### 3.1 Stack

- React 18 with TypeScript
- Vite (build tool)
- Tailwind CSS (neomorphic design system)
- Zustand (state management)
- React Router v6 (routing)
- Lucide React (icons)

### 3.2 Component Architecture

```
App
├── ThemeProvider
├── WebSocketProvider
├── ToastProvider
├── Layout
│   ├── Sidebar (navigation)
│   ├── Header (status bar)
│   └── PageContent
│       ├── Dashboard
│       ├── Rooms
│       ├── Devices
│       ├── Nodes
│       ├── Assistant
│       ├── Voice
│       ├── Music
│       ├── Automations
│       ├── Scenes
│       ├── Firmware
│       ├── Hardware
│       ├── Circuits
│       ├── Logs
│       └── Settings
└── UI Components
    ├── Card (raised/inset)
    ├── Button
    ├── Toggle
    ├── Modal
    ├── Toast
    ├── StatusBadge
    ├── ProgressBar
    ├── LoadingState
    └── EmptyState
```

### 3.3 State Management

Zustand store with slices:

```
Store
├── devices: Device[]
├── nodes: Node[]
├── rooms: Room[]
├── music: MusicState
├── voice: VoiceState
├── system: SystemStatus
├── events: Event[]
├── automations: Automation[]
├── scenes: Scene[]
└── settings: Settings
```

WebSocket messages dispatch directly to store actions for real-time updates.

---

## 4. ESP32 Firmware Architecture

### 4.1 Main ESP32 (WROOM-32)

FreeRTOS task-based architecture. No blocking `delay()` in any critical path.

```
┌─────────────────────────────────────┐
│           FreeRTOS Tasks            │
├─────────────────────────────────────┤
│ Task 1: UI (Core 1)                │
│   - TFT rendering                  │
│   - Eye animation                  │
│   - Music UI                       │
│   - Status overlays                │
│   Priority: 2                      │
│   Stack: 8192 bytes                │
├─────────────────────────────────────┤
│ Task 2: Audio Capture (Core 0)     │
│   - INMP441 I2S0 read              │
│   - Ring buffer fill               │
│   - Energy-based VAD               │
│   Priority: 3 (highest)            │
│   Stack: 4096 bytes                │
├─────────────────────────────────────┤
│ Task 3: Audio Playback (Core 0)    │
│   - I2S1 write                     │
│   - TTS/notification queue         │
│   - Buffer management              │
│   Priority: 3                      │
│   Stack: 4096 bytes                │
├─────────────────────────────────────┤
│ Task 4: WebSocket (Core 0)         │
│   - Server connection              │
│   - Message send/receive           │
│   - Heartbeat                      │
│   - Reconnect with backoff         │
│   Priority: 2                      │
│   Stack: 8192 bytes                │
├─────────────────────────────────────┤
│ Task 5: ESP-NOW (Core 0)           │
│   - Node communication             │
│   - Command relay                  │
│   - ACK handling                   │
│   - Retry management               │
│   Priority: 2                      │
│   Stack: 4096 bytes                │
├─────────────────────────────────────┤
│ Task 6: System (Core 0)            │
│   - Heap monitoring                │
│   - Watchdog feed                  │
│   - Wi-Fi monitoring               │
│   - Uptime tracking                │
│   Priority: 1 (lowest)             │
│   Stack: 2048 bytes                │
└─────────────────────────────────────┘
```

### 4.2 I2S Resource Allocation

ESP32 WROOM-32 has **2 I2S peripherals**. They are used separately:

| Peripheral | Direction | Purpose | Pins |
|-----------|-----------|---------|------|
| I2S0 | Input | INMP441 microphone | BCLK=26, WS=25, DATA=33 |
| I2S1 | Output | Audio amplifier | BCLK=22, WS=21, DOUT=23 |

No runtime I2S reconfiguration needed. Both can operate simultaneously.

### 4.3 Memory Budget (WROOM-32, no PSRAM)

| Component | RAM Usage |
|-----------|-----------|
| FreeRTOS tasks (6) | ~35 KB |
| I2S DMA buffers (mic) | ~4 KB |
| I2S DMA buffers (audio) | ~4 KB |
| Audio playback buffer | ~8 KB |
| WebSocket buffer | ~4 KB |
| ESP-NOW buffers | ~2 KB |
| TFT partial framebuffer | ~10 KB |
| JSON parsing buffer | ~4 KB |
| Music state / strings | ~2 KB |
| Album art (64×64 RGB565) | ~8 KB |
| WiFi stack | ~40 KB |
| **Total estimated** | **~121 KB** |
| **Available DRAM** | **~320 KB** |
| **Margin** | **~199 KB** |

### 4.4 Node ESP32-S3

Minimal firmware. No TFT, no audio, no WebSocket.

```
JARVIS_Node
├── ESP-NOW receive/send
├── Relay driver (2 channels, configurable polarity)
├── Device handler (command → relay mapping)
├── Heartbeat (every 15s to main)
├── Optional sensor reading
└── System monitor (heap, uptime)
```

Boot sequence:
1. Set relay GPIOs to safe state (OFF)
2. Wait 100ms
3. Initialize ESP-NOW
4. Register main ESP32 as peer
5. Send online heartbeat
6. Begin accepting commands

---

## 5. Communication Architecture

### 5.1 WebSocket (Server ↔ Main ESP32 ↔ Dashboard)

Persistent bidirectional connection. JSON messages with type-based routing.

```
Server ←→ Main ESP32 (device commands, voice events, music state, TTS audio)
Server ←→ Dashboard  (all state updates, control commands)
```

### 5.2 ESP-NOW (Main ESP32 ↔ Nodes)

250-byte max payload. Binary packet format with header. Reliable delivery via ACK + retry.

```
Main ESP32 → Node: device commands, config, time sync
Node → Main ESP32: ACKs, state confirmations, sensor data, heartbeats
```

### 5.3 REST API (Dashboard → Server)

Standard HTTP for CRUD operations, configuration, firmware upload.

---

## 6. Voice Architecture

```
INMP441 Mic
    │ (I2S0, 16kHz, 16-bit, mono)
    ▼
Main ESP32
    │ (energy-based pre-filter)
    │ (PCM chunks via WebSocket)
    ▼
JARVIS server
    │
    ├── VAD (webrtcvad / energy threshold)
    │   └── Detects speech start/end
    │
    ├── STT (faster-whisper, CPU, tiny model)
    │   └── Transcription text
    │
    ├── AI Intent (Ollama, local LLM)
    │   └── Structured JSON intent
    │
    ├── Validator
    │   └── Check device exists, action valid
    │
    ├── Executor
    │   └── Route to DeviceManager/SpotifyBridge/SceneManager
    │
    └── TTS (Piper, local)
        └── PCM audio response
            │
            ▼
        Main ESP32
            │ (I2S1)
            ▼
        I2S Amplifier → Speaker
```

---

## 7. Spotify Architecture

JARVIS does NOT play Spotify audio. The user's existing setup handles playback:

```
Phone (Spotify app) → Bluetooth → User's BT Speaker
```

JARVIS controls playback via the Spotify Web API:

```
Voice Command → Intent → SpotifyBridge → Spotify API → Phone → BT Speaker
                                ↓
                         Polling state
                                ↓
                    Server → WS → Main ESP32 → TFT (Now Playing)
```

Credentials stored in `.env` on server only. Never exposed to frontend or firmware.

---

## 8. Database Architecture

SQLite with SQLAlchemy async. Single file database.

Tables: `rooms`, `nodes`, `devices`, `device_states`, `events`, `automations`, `automation_runs`, `scenes`, `scene_actions`, `settings`, `firmware_versions`

See PROTOCOL.md for complete schema.

---

## 9. Security Architecture

### Defense in Depth

| Layer | Mechanism |
|-------|-----------|
| Network | LAN-only by default, configurable CORS |
| Authentication | JWT tokens for dashboard, API key for ESP32 WebSocket |
| Authorization | Role-based (admin, viewer) |
| Input Validation | Pydantic models on all endpoints |
| Command Safety | AI produces structured intents only, server validates |
| Secret Management | `.env` file, never in code/logs/responses |
| Firmware | Hash verification before flash |
| Rate Limiting | Per-endpoint, per-client |

### What AI Cannot Do

- Execute shell commands
- Access files
- Issue arbitrary GPIO commands
- Change server configuration
- Access secrets
- Run arbitrary SQL

AI output is a restricted structured intent. The server validates it against the device registry before execution.

---

## 10. Failure & Recovery Architecture

| Failure | System Behavior |
|---------|----------------|
| Server offline | Main ESP32 shows "SERVER OFFLINE" on TFT, retains ESP-NOW, retains last known state |
| Main ESP32 offline | Server marks as disconnected, dashboard shows offline |
| Node offline | Server shows "Device unavailable", commands queued with timeout |
| STT unavailable | "Voice service unavailable" on TFT, dashboard control still works |
| TTS unavailable | Commands still execute, no voice response |
| Ollama offline | "AI service unavailable", dashboard manual control works |
| Spotify offline | "Music controller unavailable" on TFT |
| Wi-Fi drops | ESP32 auto-reconnects with exponential backoff |
| WebSocket drops | Auto-reconnect with exponential backoff (1s, 2s, 4s, 8s, max 30s) |

No single subsystem failure crashes the assistant. Device control via dashboard always works if server is running.
