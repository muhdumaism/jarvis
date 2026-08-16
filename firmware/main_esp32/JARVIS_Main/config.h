/**
 * JARVIS Main Unit Configuration Header
 * 
 * Centralizes all GPIO pinouts, Wi-Fi details, and API configuration.
 * Single source of truth.
 */

#ifndef CONFIG_H
#define CONFIG_H

// ============================================================
// WiFi & Server Settings
// ============================================================
#define WIFI_SSID           "MOYIKKAL"
#define WIFI_PASSWORD       "KAMAL4148"
#define SERVER_HOST         "192.168.1.71" // Replace with home server LAN IP
#define SERVER_PORT         8000
#define WS_PATH             "/ws"
#define API_KEY             "CHANGE_ME_GENERATE_A_REAL_KEY" // Match .env settings
#define CLIENT_ID           "main_esp32_01"

// ============================================================
// Hardware Pin Mapping (ESP32-WROOM-32)
// ============================================================

// 1. SPI TFT Display (ILI9341 or ST7789)
#define TFT_CS              15  // Chip Select
#define TFT_DC              2   // Data/Command (Moved from 17)
#define TFT_RST             4   // Reset
#define TFT_MOSI            13  // SPI MOSI
#define TFT_MISO            12  // SPI MISO (safe boot pin check)
#define TFT_SCLK            14  // SPI Clock
#define TFT_BL              27  // Backlight PWM Pin

// TFT Dimensions
#define TFT_WIDTH           320
#define TFT_HEIGHT          240
#define TFT_ROTATION        1   // Landscape

// 2. INMP441 I2S Microphone (I2S0)
#define MIC_BCLK            26  // Bit Clock
#define MIC_WS              25  // Word Select / LRCLK
#define MIC_DATA            33  // Serial Data Output (SD)
#define MIC_LR_CHANNEL      0   // 0 = Left Channel (GND), 1 = Right Channel (3.3V)

// 3. I2S Audio Output Amplifier (I2S1)
#define AUDIO_BCLK          22  // Bit Clock
#define AUDIO_WS            21  // Word Select / LRCLK
#define AUDIO_DOUT          23  // Serial Data Input (DIN)
#define AUDIO_SD            19  // Shutdown / Enable Pin (Active HIGH)

// ============================================================
// ESP-NOW Configuration
// ============================================================
#define ESP_NOW_CHANNEL     1   // Must match WiFi router channel for coexistence
#define ESP_NOW_RETRIES     3
#define ESP_NOW_TIMEOUT_MS  2000

// ============================================================
// Audio Buffers & Rates
// ============================================================
#define AUDIO_SAMPLING_RATE 16000 // Voice sampling rate (16kHz)
#define AUDIO_PLAYBACK_RATE 22050 // Piper TTS playback rate (22.05kHz)
#define DMA_BUF_COUNT       4
#define DMA_BUF_LEN         512

#endif // CONFIG_H
