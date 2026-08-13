# JARVIS — System Implementation Status

This file tracks the implementation state, hardware verification, test procedures, and known boundaries of each subsystem.

---

## 1. Subsystem Status Matrix

| Component | Status | Tested? | Known Limitations | How to Test |
|-----------|--------|---------|-------------------|-------------|
| **Backend Core** | IMPLEMENTED | YES | None (Local LAN only) | Run `pytest` inside `server/` directory. |
| **Dashboard UI** | IMPLEMENTED | YES | Requires Chromium for Web Serial | Run `npm run build` inside `dashboard/` |
| **Main ESP32 Firmware** | COMPILES | HARDWARE TEST REQUIRED | WROOM-32 RAM limits (procedural graphics only) | Compile & upload using Arduino IDE. Check Serial log. |
| **INMP441 Mic** | IMPLEMENTED | HARDWARE TEST REQUIRED | Noise floor threshold needs calibration | Look for I2S audio frames in ESP32 serial output. |
| **I2S Amplifier** | IMPLEMENTED | HARDWARE TEST REQUIRED | Mono output only | Synthesize speech on dashboard; check speaker output. |
| **ESP-NOW Network** | IMPLEMENTED | TESTED | Maximum payload of 250 bytes | Boot Node and verify Main Gateway prints heartbeats. |
| **TTS (Piper)** | IMPLEMENTED | YES | Local CPU execution speed | Trigger speech synthesis on dashboard settings check. |
| **Spotify Control** | INTEGRATION READY | YES | Spotify Premium required | Issue a music control command from the panel. |
| **Firmware Flashing** | IMPLEMENTED | YES | Browser dependent (requires Web Serial) | Connect ESP32, navigate to dashboard Firmware tool. |

---

## 2. Dynamic Integration Testing

To run the unified testing framework:
1. Start the server:
   ```bash
   cd server
   python main.py
   ```
2. Run backend tests:
   ```bash
   cd server
   pytest tests/test_backend.py
   ```
3. Open the Dashboard panel `http://localhost:5173`, login as `admin` / `CHANGE_ME`, and run individual tests inside the **Settings** Setup Wizard.
