# JARVIS — Deployment Guide

This document describes how to execute server scripts, start the dashboard, build binaries, flash the firmware, and configure variables.

---

## 1. How to Run the Server

### 1.1 Virtual Environment & Dependencies Setup
Navigate to the server folder and install dependencies:
```bash
cd server
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 1.2 Launching the Server
Run the FastAPI application using uvicorn:
```bash
python main.py
# Or directly using uvicorn:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Open `http://localhost:8000/health` or `http://localhost:8000/docs` to verify the API docs are running.

---

## 2. How to Run the Dashboard

### 2.1 Dependencies Installation
```bash
cd dashboard
npm install
```

### 2.2 Dev Mode
```bash
npm run dev
```
Open `http://localhost:5173` to open the control panel.

---

## 3. How to Flash ESP32 Firmware

Firmwares can be flashed using Arduino IDE, PlatformIO, or esptool CLI.

### 3.1 Arduino IDE setup
1. Install Arduino IDE.
2. In Board Manager, install `esp32` by Espressif Systems (v2.x or v3.x).
3. Install dependencies from Library Manager:
   - `WebSockets` by Markus Sattler
   - `ArduinoJson` by Benoit Blanchon
   - `Adafruit GFX Library`
   - `Adafruit ILI9341`
4. Open `firmware/main_esp32/JARVIS_Main/JARVIS_Main.ino` or `firmware/node_esp32/JARVIS_Node/JARVIS_Node.ino` inside Arduino IDE.
5. In `config.h`, set your Wi-Fi SSID, Password, and server IP address.
6. Select target board (e.g., `ESP32 Dev Module` for Main, `ESP32S3 Dev Module` for Node).
7. Connect board via USB and click **Upload**.

### 3.2 Command Line Flashing (CLI)
You can compile and upload using `arduino-cli` or `esptool.py`.
Example using `esptool`:
```bash
esptool.py --chip esp32 --port COM3 --baud 115200 write_flash -z 0x10000 jarvis_main.bin
```

---

## 4. Required Libraries Summary

### 4.1 Python Server Packages
- `fastapi`
- `uvicorn`
- `sqlalchemy[asyncio]`
- `aiosqlite`
- `python-jose`
- `passlib`
- `websockets`
- `webrtcvad`
- `faster-whisper`
- `piper-tts`
- `httpx`
- `ollama`
- `spotipy`
- `psutil`
- `Pillow`
- `structlog`

### 4.2 Arduino Libraries
- `WebSocketsClient` (Markus Sattler)
- `ArduinoJson` (Benoit Blanchon)
- `Adafruit_GFX` (Adafruit)
- `Adafruit_ILI9341` (Adafruit)
- `SPI` (Native)
- `WiFi` (Native)
- `esp_now` (Native)

### 4.3 Node Dashboard Packages
- `react` (v19)
- `react-dom`
- `react-router-dom`
- `zustand`
- `lucide-react`
- `@tailwindcss/postcss` (Tailwind v4 PostCSS plugin)
- `autoprefixer`
- `postcss`
- `vite`
