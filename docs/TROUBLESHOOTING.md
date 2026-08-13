# JARVIS — Troubleshooting Guide

This guide helps diagnose, isolate, and fix common software/hardware issues with the JARVIS system.

---

## 1. Subsystem Errors

### 1.1 "Ollama Offline" / "AI Service Unavailable"
- Verify Ollama is running: Open `http://localhost:11434` in browser. You should see "Ollama is running".
- Verify model is downloaded:
  ```bash
  ollama list
  ```
  Make sure `llama3.2:1b` (or your configured model) is in the list. Download using `ollama pull llama3.2:1b` if missing.
- Check server log: Verify `OLLAMA_BASE_URL` in `.env` is correct.

### 1.2 "STT Engine Not Ready"
- Whisper downloads models on first start, which can take several minutes on slow connections. Check server console output.
- CPU compatibility check: Make sure your CPU supports INT8 computation instructions. If you get CPU errors, switch `STT_DEVICE=cpu` and ensure `faster-whisper` is compiled cleanly.

### 1.3 "TTS Engine Failures"
- Verify that ONNX voice model files (`en_US-lessac-medium.onnx` and `en_US-lessac-medium.onnx.json`) are downloaded and placed inside the exact directory configured in your `.env`.
- Check if `piper` CLI executable is installed:
  ```bash
  piper --help
  ```
  If it returns command not found, run `pip install piper-tts` inside virtual environment.

---

## 2. Firmware / ESP32 Gateway Issues

### 2.1 Main ESP32 displays "SERVER OFFLINE"
- Verify WiFi SSID and Password in `config.h` are correct.
- Verify the server IP address (`SERVER_HOST`) in `config.h` matches the server host LAN IP (usually starts with `192.168.1.x`).
- Verify server port is open. Ensure your desktop firewall is not blocking incoming TCP port `8000`.

### 2.2 Relays do not switch on commands
- Node status indicator: Verify the node is marked as `online` on the dashboard.
- Heartbeats check: Look at the Main ESP32 serial monitor. You should see heartbeats like `[ESPNOW] Received heartbeat from room_node_01`.
- If no heartbeats, check that both the Main and Node are running on the same ESP-NOW channel (default `1`). If your home WiFi router runs on channel `6`, you must change `ESP_NOW_CHANNEL` in `config.h` to `6` so they align.

---

## 3. Spotify Control Issues

- Verify Spotify Premium: Spotify Web API modify playback states commands require a Spotify Premium account.
- Active device requirement: Spotify requires an active session. If you have not played music on your phone recently, Spotify suspends the active session. Start playing music on your phone manually first, then issue voice commands to control it.
