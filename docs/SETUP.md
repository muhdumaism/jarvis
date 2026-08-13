# JARVIS — First Boot Setup & Wizard Guide

This document describes the step-by-step guide to pair nodes, configure subsystems, and complete the 19-step setup checklist.

---

## 1. Environment Configurations

Make sure you copy the environment file and customize the variables before launching the services:
```bash
cp .env.example .env
```
Fill in the parameters:
1. `SECRET_KEY` and `API_KEY` (used for authorization between dashboard, websocket, and ESP32 gateway).
2. `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, and `SPOTIFY_REFRESH_TOKEN` (see section below).
3. `OLLAMA_BASE_URL` (usually `http://localhost:11434` for local setups).

---

## 2. Setting Up Subsystems

### 2.1 local speech-to-text (Whisper)
The server runs CPU-based local whisper transcription automatically. It downloads the configured model size (default `tiny` - ~70MB) on first start.

### 2.2 local text-to-speech (Piper)
Download a pre-trained ONNX voice model from Rhasspy huggingface repository and place it in the server:
- Voice Model: [en_US-lessac-medium.onnx](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx)
- Model Configuration: [en_US-lessac-medium.onnx.json](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json)

Place both inside `jarvis/server/models/piper/` directory.

### 2.3 Local LLM (Ollama)
1. Install Ollama from [ollama.com](https://ollama.com).
2. Download the default model configured in `.env`:
   ```bash
   ollama pull llama3.2:1b
   ```
3. Make sure Ollama runs locally in the background (`ollama serve`).

### 2.4 Spotify authorization token
To get a refresh token:
1. Go to [developer.spotify.com](https://developer.spotify.com) and create an app.
2. Add `http://localhost:8000/callback` as redirect URI.
3. Retrieve client ID and client secret.
4. Run authorization scripts or fetch refresh token using standard OAuth auth flow, and save it in `.env`.

---

## 3. First Boot Sequence

1. Start the server (see DEPLOYMENT.md).
2. Open the dashboard in browser (typically `http://localhost:5173`).
3. Connect the Main ESP32 to USB, go to the **Firmware** page, verify that Web Serial is active, and click flash (or use local python flash script).
4. Power up the Main ESP32. The TFT screen will light up showing animated eyes looking around. Status bar shows "SERVER CONNECTED".
5. Power up the Secondary ESP32-S3 relay node. Once booted, it broadcasts a heartbeat packet via ESP-NOW.
6. The Main ESP32 receives the node's heartbeat, caches its MAC address dynamically, and relays the online status to the server over WebSocket.
7. Open the **Devices** page on the dashboard to register and map light switches or fans to specific nodes and relay channels.
8. Complete the 19-step setup checklist inside the **Settings** wizard page to verify all components are fully functional.
