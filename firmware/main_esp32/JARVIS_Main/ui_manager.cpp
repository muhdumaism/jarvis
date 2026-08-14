#include "ui_manager.h"
#include "eyes.h"
#include "tft_driver.h"
#include <HTTPClient.h>
#include <WiFi.h>

// Album art binary storage (64x64 pixels, 16-bit color = 8192 bytes)
uint16_t albumArtBuffer[64 * 64];
bool albumArtLoaded = false;
char lastLoadedTrackTitle[64] = "";

void fetchAlbumArt() {
    if (WiFi.status() != WL_CONNECTED) {
        albumArtLoaded = false;
        return;
    }
    
    HTTPClient http;
    char url[128];
    snprintf(url, sizeof(url), "http://%s:%d/api/music/album-art-rgb565", SERVER_HOST, SERVER_PORT);
    
    Serial.printf("[HTTP] Downloading album art from: %s\n", url);
    http.begin(url);
    http.setTimeout(4000); // 4 seconds timeout
    
    int httpCode = http.GET();
    if (httpCode == HTTP_CODE_OK) {
        WiFiClient* stream = http.getStreamPtr();
        int totalBytes = 64 * 64 * 2;
        int bytesRead = 0;
        uint8_t* ptr = (uint8_t*)albumArtBuffer;
        
        unsigned long startMs = millis();
        while (http.connected() && bytesRead < totalBytes && (millis() - startMs < 5000)) {
            size_t size = stream->available();
            if (size > 0) {
                int toRead = min((int)size, totalBytes - bytesRead);
                int readCount = stream->readBytes(ptr + bytesRead, toRead);
                bytesRead += readCount;
            }
            delay(1);
        }
        
        if (bytesRead == totalBytes) {
            // Swap byte order because ESP32 is little-endian but HTTP stream is network (big-endian) bytes
            for (int i = 0; i < 64 * 64; i++) {
                uint16_t val = albumArtBuffer[i];
                albumArtBuffer[i] = (val << 8) | (val >> 8);
            }
            albumArtLoaded = true;
            Serial.println("[HTTP] Album art loaded successfully!");
        } else {
            Serial.printf("[HTTP] Download incomplete. Got %d of %d bytes.\n", bytesRead, totalBytes);
            albumArtLoaded = false;
        }
    } else {
        Serial.printf("[HTTP] GET failed, code: %d\n", httpCode);
        albumArtLoaded = false;
    }
    http.end();
}

char currentSystemState[32] = "IDLE";
bool wifiConnected = false;
bool speakerConnected = true;

// Music track cache
char currentTitle[64] = "";
char currentArtist[64] = "";
int trackPosition = 0;
int trackDuration = 0;
unsigned long lastMusicUpdate = 0;

// Room Assistant status variables
int activeLightsCount = 0;
bool isFanActive = false;
float roomTemperature = 26.5;
bool doorLocked = true;

char lastUserQuery[64] = "Waiting...";
char lastJarvisReply[64] = "Hello, Umais.";

// Rendering state caches to reduce SPI bandwidth usage
static char lastTitle[64] = "";
static char lastArtist[64] = "";
static int lastTrackPosition = -1;
static int lastTrackDuration = -1;
static bool lastWifiConnected = false;
static bool lastSpeakerConnected = false;
static char lastSystemState[32] = "";
static unsigned long lastHeaderDraw = 0;
static char lastDrawnState[32] = "";

void initUI() {
    initTFT();
    initEyes();
}

// Static cache variables for left/right dashboard panels
static int lastActiveLightsCount = -1;
static bool lastIsFanActive = false;
static float lastRoomTemperature = -1.0;
static bool lastDoorLocked = false;

static char lastUserQueryCache[64] = "";
static char lastJarvisReplyCache[64] = "";
static char lastDashboardState[32] = "";

void invalidateUICaches() {
    lastTitle[0] = '\0';
    lastArtist[0] = '\0';
    lastTrackPosition = -1;
    lastTrackDuration = -1;
    lastWifiConnected = !wifiConnected;
    lastSpeakerConnected = !speakerConnected;
    lastSystemState[0] = '\0';
    lastHeaderDraw = 0;
    lastDrawnState[0] = '\0';
    
    // Invalidate Room Assistant panels caches
    lastActiveLightsCount = -1;
    lastIsFanActive = !isFanActive;
    lastRoomTemperature = -1.0;
    lastDoorLocked = !doorLocked;
    
    lastUserQueryCache[0] = '\0';
    lastJarvisReplyCache[0] = '\0';
    lastDashboardState[0] = '\0';
    
    // Reset the coordinate caches inside eyes.cpp
    resetEyesDrawCache();
}

void setSystemState(const char* newState) {
    if (strcmp(currentSystemState, newState) != 0) {
        strncpy(currentSystemState, newState, sizeof(currentSystemState) - 1);
        currentSystemState[sizeof(currentSystemState) - 1] = '\0';
        invalidateUICaches(); // Force redraw of all graphics elements
        Serial.printf("[UI] State changed to: %s\n", currentSystemState);
    }
}

void setWifiConnected(bool connected) {
    wifiConnected = connected;
}

void setSpeakerConnected(bool connected) {
    speakerConnected = connected;
}

void setTrackInfo(const char* title, const char* artist, int positionMs, int durationMs) {
    strncpy(currentTitle, title, sizeof(currentTitle) - 1);
    currentTitle[sizeof(currentTitle) - 1] = '\0';
    strncpy(currentArtist, artist, sizeof(currentArtist) - 1);
    currentArtist[sizeof(currentArtist) - 1] = '\0';
    trackPosition = positionMs;
    trackDuration = durationMs;
    lastMusicUpdate = millis();
}

void drawWifiIcon(int x, int y, bool connected) {
    uint16_t color = connected ? ILI9341_CYAN : ILI9341_RED;
    tft.fillRect(x, y + 8, 2, 2, color);
    tft.fillRect(x + 3, y + 6, 2, 4, color);
    tft.fillRect(x + 6, y + 4, 2, 6, color);
    tft.fillRect(x + 9, y + 2, 2, 8, color);
}

void drawHeader() {
    if (wifiConnected != lastWifiConnected || millis() - lastHeaderDraw > 5000) {
        lastWifiConnected = wifiConnected;
        lastHeaderDraw = millis();
        
        // Clear top header area (Y: 0 to 30)
        tft.fillRect(0, 0, TFT_WIDTH, 30, ILI9341_BLACK);
        
        // Futurist JARVIS Logo and Underline
        tft.setTextSize(2);
        tft.setTextColor(ILI9341_WHITE);
        tft.setCursor(10, 8);
        tft.print("JARVIS");
        tft.drawFastHLine(10, 27, 72, ILI9341_CYAN);
        
        // System Online Status and Wifi Bars
        tft.setTextSize(1);
        tft.setTextColor(ILI9341_CYAN);
        tft.setCursor(TFT_WIDTH - 110, 12);
        tft.print(wifiConnected ? "SYSTEM ONLINE" : "OFFLINE");
        
        drawWifiIcon(TFT_WIDTH - 20, 8, wifiConnected);
    }
}

void drawMusicOverlay(const char* state) {
    // Only redraw metadata and static text if the track, speaker, or overall state changes
    bool trackChanged = (strcmp(currentTitle, lastTitle) != 0 || 
                         strcmp(currentArtist, lastArtist) != 0 || 
                         speakerConnected != lastSpeakerConnected || 
                         strcmp(state, lastSystemState) != 0);

    if (trackChanged) {
        // Clear music metadata area (X: 0 to 320, Y: 30 to 110)
        tft.fillRect(0, 30, TFT_WIDTH, 80, ILI9341_BLACK);

        // Fetch album art on track change
        if (strcmp(currentTitle, lastLoadedTrackTitle) != 0) {
            strncpy(lastLoadedTrackTitle, currentTitle, sizeof(lastLoadedTrackTitle) - 1);
            lastLoadedTrackTitle[sizeof(lastLoadedTrackTitle) - 1] = '\0';
            albumArtLoaded = false;
            fetchAlbumArt();
        }

        // Draw Album Art (64x64 at X=20, Y=40)
        if (albumArtLoaded) {
            tft.drawRGBBitmap(20, 40, albumArtBuffer, 64, 64);
        } else {
            // Draw Art Placeholder
            tft.fillRect(20, 40, 64, 64, ILI9341_DARKGREY);
            tft.drawRect(20, 40, 64, 64, ILI9341_CYAN);
            tft.setTextSize(1);
            tft.setTextColor(ILI9341_LIGHTGREY);
            tft.setCursor(38, 68);
            tft.print("ART");
        }

        // Title
        tft.setTextSize(2);
        tft.setTextColor(ILI9341_WHITE);
        tft.setCursor(95, 45);
        char titleCopy[18];
        strncpy(titleCopy, currentTitle, sizeof(titleCopy) - 1);
        titleCopy[sizeof(titleCopy) - 1] = '\0';
        tft.print(titleCopy[0] ? titleCopy : "No Track");

        // Artist
        tft.setTextSize(1);
        tft.setTextColor(ILI9341_LIGHTGREY);
        tft.setCursor(95, 68);
        char artistCopy[32];
        strncpy(artistCopy, currentArtist, sizeof(artistCopy) - 1);
        artistCopy[sizeof(artistCopy) - 1] = '\0';
        tft.print(artistCopy[0] ? artistCopy : "Unknown Artist");

        // Speaker status
        tft.setCursor(95, 85);
        if (speakerConnected) {
            tft.setTextColor(ILI9341_GREEN);
            tft.print("SPK: CONNECTED");
        } else {
            tft.setTextColor(ILI9341_RED);
            tft.print("SPK: OFFLINE");
        }

        strncpy(lastTitle, currentTitle, sizeof(lastTitle) - 1);
        lastTitle[sizeof(lastTitle) - 1] = '\0';
        strncpy(lastArtist, currentArtist, sizeof(lastArtist) - 1);
        lastArtist[sizeof(lastArtist) - 1] = '\0';
        lastSpeakerConnected = speakerConnected;
        strncpy(lastSystemState, state, sizeof(lastSystemState) - 1);
        lastSystemState[sizeof(lastSystemState) - 1] = '\0';
    }

    // Calculate progress position
    int currentPos = trackPosition;
    if (trackDuration > 0 && strcmp(state, "SPOTIFY_PLAYING") == 0) {
        unsigned long elapsed = millis() - lastMusicUpdate;
        currentPos = min(trackDuration, trackPosition + (int)elapsed);
    }

    // Only update progress bar and time readouts if the position changes by >=1 second
    if (abs(currentPos - lastTrackPosition) >= 1000 || trackDuration != lastTrackDuration || trackChanged) {
        int barWidth = TFT_WIDTH - 40;
        int barHeight = 6;
        int barX = 20;
        int barY = 190;

        // Clear and draw progress bar
        tft.fillRect(barX, barY, barWidth, barHeight, ILI9341_BLACK);
        tft.drawRect(barX, barY, barWidth, barHeight, ILI9341_DARKGREY);
        if (trackDuration > 0) {
            int fillWidth = (int)(((float)currentPos / trackDuration) * barWidth);
            if (fillWidth > barWidth) fillWidth = barWidth;
            tft.fillRect(barX + 1, barY + 1, fillWidth - 2, barHeight - 2, ILI9341_BLUE);
        }

        // Time Label (partial area redraw)
        tft.fillRect(20, 205, 120, 12, ILI9341_BLACK);
        tft.setTextColor(ILI9341_LIGHTGREY);
        tft.setTextSize(1);
        tft.setCursor(20, 205);
        tft.printf("%d:%02d / %d:%02d", currentPos / 60000, (currentPos % 60000) / 1000,
                                        trackDuration / 60000, (trackDuration % 60000) / 1000);

        // State bottom overlay
        tft.fillRect(20, 220, 200, 12, ILI9341_BLACK);
        tft.setCursor(20, 220);
        tft.setTextColor(ILI9341_CYAN);
        tft.print(state);

        lastTrackPosition = currentPos;
        lastTrackDuration = trackDuration;
    }
}

void drawWrappedText(const char* text, int x, int y, int maxChars, int maxLines) {
    int len = strlen(text);
    int start = 0;
    int line = 0;
    while (start < len && line < maxLines) {
        int chars = maxChars;
        if (start + chars > len) {
            chars = len - start;
        } else {
            // Wrap on word boundary if possible
            int lastSpace = -1;
            for (int i = start + chars - 1; i >= start; i--) {
                if (text[i] == ' ') {
                    lastSpace = i;
                    break;
                }
            }
            if (lastSpace != -1) {
                chars = lastSpace - start;
            }
        }
        
        char lineBuf[24];
        if (chars >= sizeof(lineBuf)) chars = sizeof(lineBuf) - 1;
        strncpy(lineBuf, text + start, chars);
        lineBuf[chars] = '\0';
        
        tft.setCursor(x, y + (line * 10));
        tft.print(lineBuf);
        
        start += chars;
        if (start < len && text[start] == ' ') start++; // skip space
        line++;
    }
}

void drawDashboardLayout() {
    // Unused in current clean layout mode but retained for function signatures consistency
}

void setLastUserQuery(const char* query) {
    if (strcmp(lastUserQuery, query) != 0) {
        strncpy(lastUserQuery, query, sizeof(lastUserQuery) - 1);
        lastUserQuery[sizeof(lastUserQuery) - 1] = '\0';
    }
}

void setLastJarvisReply(const char* reply) {
    if (strcmp(lastJarvisReply, reply) != 0) {
        strncpy(lastJarvisReply, reply, sizeof(lastJarvisReply) - 1);
        lastJarvisReply[sizeof(lastJarvisReply) - 1] = '\0';
    }
}

void updateTFTDeviceState(const char* deviceId, const char* state) {
    String id = String(deviceId);
    String st = String(state);
    
    if (id.indexOf("light") >= 0 || id.indexOf("lamp") >= 0) {
        if (st == "on") {
            if (activeLightsCount < 4) activeLightsCount++;
        } else if (st == "off") {
            if (activeLightsCount > 0) activeLightsCount--;
        }
    }
    else if (id.indexOf("fan") >= 0) {
        isFanActive = (st == "on");
    }
    else if (id.indexOf("door") >= 0 || id.indexOf("lock") >= 0) {
        doorLocked = (st == "lock" || st == "locked" || st == "on");
    }
    else if (id.indexOf("temp") >= 0) {
        roomTemperature = atof(state);
    }
}

void drawWaveform(int centerX, int centerY) {
    int numBars = 9;
    int barWidth = 3;
    int spacing = 3;
    int maxH = 20;
    
    // Clear only the waveform horizontal area to reduce flicker
    tft.fillRect(centerX - 30, centerY - 12, 60, 24, ILI9341_BLACK);
    
    for (int i = 0; i < numBars; i++) {
        int h = 2;
        if (strcmp(currentSystemState, "LISTENING") == 0) {
            h = 4 + random(maxH - 4);
        } else if (strcmp(currentSystemState, "SPEAKING") == 0) {
            h = 4 + (int)((maxH - 4) * abs(sin(millis() / 80.0 + i)));
        } else if (strcmp(currentSystemState, "THINKING") == 0) {
            h = 4 + (int)(6 * sin(millis() / 150.0 + i));
        }
        
        int x = centerX - ((numBars * (barWidth + spacing) - spacing) / 2) + i * (barWidth + spacing);
        tft.fillRect(x, centerY - h/2, barWidth, h, ILI9341_CYAN);
    }
}

void updateUI() {
    drawHeader();

    static bool lastMusicMode = false;
    bool isMusicMode = (currentTitle[0] != '\0' && 
                        strcmp(currentSystemState, "BACKEND_DISCONNECTED") != 0 &&
                        strcmp(currentSystemState, "SPEAKER_DISCONNECTED") != 0);

    if (isMusicMode != lastMusicMode) {
        // Layout switched! Clear screen area below header (Y: 30 to 320)
        tft.fillRect(0, 30, TFT_WIDTH, TFT_HEIGHT - 30, ILI9341_BLACK);
        
        // Reset last Title and last Artist to force redrawing metadata
        lastTitle[0] = '\0';
        lastArtist[0] = '\0';
        lastSystemState[0] = '\0';
        lastTrackPosition = -9999;
        
        lastMusicMode = isMusicMode;
    }

    if (isMusicMode) {
        // 1. Music mode UI with Album Art and progress
        drawMusicOverlay(currentSystemState);
        
        // Show assistant animations in eyes during music mode
        if (strcmp(currentSystemState, "LISTENING") == 0 || 
            strcmp(currentSystemState, "THINKING") == 0 || 
            strcmp(currentSystemState, "SPEAKING") == 0) {
            updateEyes(currentSystemState);
        } else {
            updateEyes("IDLE"); // Music bobs eyes normally
        }
        drawEyes();
    } else {
        // 2. Minimal Clean Assistant Screen (Mockup matching)
        updateEyes(currentSystemState);
        drawEyes();
        
        // Animated audio waveform
        drawWaveform(160, 195);
        
        // Status text overlay
        static char lastStatusText[32] = "";
        char currentStatusText[32] = "";
        
        if (strcmp(currentSystemState, "BACKEND_DISCONNECTED") == 0) {
            strcpy(currentStatusText, "SERVER OFFLINE");
        } else if (strcmp(currentSystemState, "SPEAKER_DISCONNECTED") == 0) {
            strcpy(currentStatusText, "SPEAKER OFFLINE");
        } else {
            strncpy(currentStatusText, currentSystemState, sizeof(currentStatusText) - 1);
            currentStatusText[sizeof(currentStatusText) - 1] = '\0';
        }
        
        if (strcmp(currentStatusText, lastStatusText) != 0) {
            tft.fillRect(60, 212, 200, 12, ILI9341_BLACK);
            tft.setTextSize(1);
            tft.setTextColor(ILI9341_CYAN);
            
            // Center the text
            int textWidth = strlen(currentStatusText) * 6;
            tft.setCursor(160 - textWidth / 2, 212);
            tft.print(currentStatusText);
            
            strncpy(lastStatusText, currentStatusText, sizeof(lastStatusText) - 1);
            lastStatusText[sizeof(lastStatusText) - 1] = '\0';
        }
    }
}
