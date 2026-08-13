# JARVIS — Hardware Bill of Materials (BOM)

This document lists all components required to build the JARVIS Physical Room Assistant (Main unit + Secondary Node).

---

## 1. Main Gateway Coordinator Unit

| Part Description | Quantity | Purpose | Operating Voltage | Est. Price | Reference Link / Notes |
|------------------|----------|---------|-------------------|------------|------------------------|
| **ESP32 WROOM 32** | 1 | Main gateway controller CPU | 5V (USB) / 3.3V | $4.00 | Standard dev kit (30-pin or 38-pin version) |
| **ILI9341 2.8" SPI TFT** | 1 | Animated visual screen eyes UI | 3.3V | $8.00 | 240x320 resolution with SPI headers |
| **INMP441 I2S Mic** | 1 | Digital audio capture MEMS mic | 3.3V | $3.00 | Omni-directional digital microphone |
| **MAX98357A I2S Amp** | 1 | Speaker output digital DAC & Amp | 5V / 3.3V | $4.00 | Mono I2S Class-D amplifier breakout |
| **4Ω 3W Speaker** | 1 | Audio vocal playback output | N/A | $2.50 | 2-inch diameter voice coil speaker |
| **Breadboard / Perfboard** | 1 | Mounting components & wiring | N/A | $2.00 | Prototype mounting block |
| **Jumper Wires Pack** | 1 | Pin connection links | N/A | $1.50 | Male-to-Male & Female-to-Female assortment |

---

## 2. Secondary Room Control Node

| Part Description | Quantity | Purpose | Operating Voltage | Est. Price | Reference Link / Notes |
|------------------|----------|---------|-------------------|------------|------------------------|
| **ESP32-S3 Dev Kit** | 1 | Node processor & ESP-NOW client | 5V (USB) / 3.3V | $6.00 | ESP32-S3-WROOM-1 module |
| **2-Channel Relay Shield** | 1 | High voltage power toggle (Light/Fan) | 5V | $3.50 | Active Low trigger recommended |
| **AC-to-DC 5V Supply** | 1 | Node local power supply | AC 110V-220V | $5.00 | 5V 2A USB wall block power adapter |

---

## 3. Recommended Enclosure (Optional)

- **3D Printed Main Base Case**: Fits ESP32, TFT, Mic, Amp, and Speaker safely. Look for "2.8 TFT ESP32 stand" on Thingiverse.
- **Node Junction Box**: Rigid ABS plastic enclosure to mount the ESP32-S3 and Relay Shield. Keeps high-voltage terminals isolated.
