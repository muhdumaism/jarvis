#include "ui_manager.h"
#include "eyes.h"
#include "tft_driver.h"

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
        clearDisplay(); // clear whole frame on state change
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

void drawHeader() {
    // Only draw header if WiFi status changes, or periodically every 5 seconds
    if (wifiConnected != lastWifiConnected || millis() - lastHeaderDraw > 5000) {
        lastWifiConnected = wifiConnected;
        lastHeaderDraw = millis();
        tft.fillRect(0, 0, TFT_WIDTH, 24, ILI9341_DARKGREY);
        tft.setTextSize(1);
        tft.setTextColor(ILI9341_WHITE);
        tft.setCursor(8, 8);
        tft.print("JARVIS ASSISTANT");

        // WiFi status indicator dot
        tft.fillCircle(TFT_WIDTH - 15, 12, 4, wifiConnected ? ILI9341_GREEN : ILI9341_RED);
    }
}

void drawMusicOverlay(const char* state) {
    // Only redraw metadata and static text if the track, speaker, or overall state changes
    bool trackChanged = (strcmp(currentTitle, lastTitle) != 0 || 
                         strcmp(currentArtist, lastArtist) != 0 || 
                         speakerConnected != lastSpeakerConnected || 
                         strcmp(state, lastSystemState) != 0);

    if (trackChanged) {
        tft.fillRect(0, 150, TFT_WIDTH, TFT_HEIGHT - 150, ILI9341_BLACK);

        // Title
        tft.setTextSize(2);
        tft.setTextColor(ILI9341_WHITE);
        tft.setCursor(20, 155);
        char titleCopy[24];
        strncpy(titleCopy, currentTitle, sizeof(titleCopy) - 1);
        titleCopy[sizeof(titleCopy) - 1] = '\0';
        tft.print(titleCopy[0] ? titleCopy : "No Track");

        // Artist
        tft.setTextSize(1);
        tft.setTextColor(ILI9341_LIGHTGREY);
        tft.setCursor(20, 175);
        char artistCopy[32];
        strncpy(artistCopy, currentArtist, sizeof(artistCopy) - 1);
        artistCopy[sizeof(artistCopy) - 1] = '\0';
        tft.print(artistCopy[0] ? artistCopy : "");

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

        // Speaker status (partial area redraw)
        tft.fillRect(TFT_WIDTH - 130, 205, 120, 12, ILI9341_BLACK);
        tft.setCursor(TFT_WIDTH - 130, 205);
        if (speakerConnected) {
            tft.setTextColor(ILI9341_GREEN);
            tft.print("SPK: CONNECTED");
        } else {
            tft.setTextColor(ILI9341_RED);
            tft.print("SPK: DISCONNECTED");
        }

        // State bottom overlay (partial area redraw)
        tft.fillRect(20, 220, 200, 12, ILI9341_BLACK);
        tft.setCursor(20, 220);
        tft.setTextColor(ILI9341_CYAN);
        tft.print(state);

        lastTrackPosition = currentPos;
        lastTrackDuration = trackDuration;
    }
}

void drawSpeakerDisconnectedScreen() {
    tft.fillRect(0, 150, TFT_WIDTH, TFT_HEIGHT - 150, ILI9341_BLACK);
    tft.setTextSize(2);
    tft.setTextColor(ILI9341_RED);
    tft.setCursor(20, 160);
    tft.print("Speaker Offline");

    tft.setTextSize(1);
    tft.setTextColor(ILI9341_LIGHTGREY);
    tft.setCursor(20, 190);
    tft.print("Check Bluetooth Speaker connection");
}

void drawBackendDisconnectedScreen() {
    tft.fillRect(0, 150, TFT_WIDTH, TFT_HEIGHT - 150, ILI9341_BLACK);
    tft.setTextSize(2);
    tft.setTextColor(ILI9341_RED);
    tft.setCursor(20, 160);
    tft.print("Server Offline");

    tft.setTextSize(1);
    tft.setTextColor(ILI9341_LIGHTGREY);
    tft.setCursor(20, 190);
    tft.print("Reconnecting to JARVIS Backend...");
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
    // 1. Draw static dividers and frames once
    static bool dividersDrawn = false;
    if (!dividersDrawn || strcmp(currentSystemState, lastDashboardState) != 0) {
        tft.drawFastVLine(106, 24, TFT_HEIGHT - 24, ILI9341_DARKGREY);
        tft.drawFastVLine(214, 24, TFT_HEIGHT - 24, ILI9341_DARKGREY);
        tft.drawRoundRect(217, 30, 100, 202, 4, ILI9341_DARKGREY);
        
        dividersDrawn = true;
        strncpy(lastDashboardState, currentSystemState, sizeof(lastDashboardState) - 1);
        lastDashboardState[sizeof(lastDashboardState) - 1] = '\0';
    }

    // 2. Draw Left Column (Room Telemetry Cards)
    bool leftChanged = (activeLightsCount != lastActiveLightsCount ||
                        isFanActive != lastIsFanActive ||
                        abs(roomTemperature - lastRoomTemperature) > 0.05 ||
                        doorLocked != lastDoorLocked);
                        
    if (leftChanged) {
        // Clear panel area X: 0 to 105, Y: 25 to 240
        tft.fillRect(0, 25, 105, TFT_HEIGHT - 25, ILI9341_BLACK);
        
        // Temperature
        tft.setTextColor(ILI9341_ORANGE);
        tft.setTextSize(1);
        tft.setCursor(6, 32);
        tft.print("ROOM TEMP");
        tft.setTextColor(ILI9341_WHITE);
        tft.setTextSize(2);
        tft.setCursor(6, 44);
        tft.printf("%.1f C", roomTemperature);

        // Lights
        tft.setTextColor(ILI9341_YELLOW);
        tft.setTextSize(1);
        tft.setCursor(6, 82);
        tft.print("LIGHTS");
        tft.setTextColor(ILI9341_WHITE);
        tft.setTextSize(2);
        tft.setCursor(6, 94);
        if (activeLightsCount > 0) {
            tft.printf("%d ON", activeLightsCount);
        } else {
            tft.print("OFF");
        }

        // Fan
        tft.setTextColor(ILI9341_GREEN);
        tft.setTextSize(1);
        tft.setCursor(6, 132);
        tft.print("FAN");
        tft.setTextColor(ILI9341_WHITE);
        tft.setTextSize(2);
        tft.setCursor(6, 144);
        tft.print(isFanActive ? "RUNNING" : "STOPPED");

        // Door Lock
        tft.setTextColor(ILI9341_RED);
        tft.setTextSize(1);
        tft.setCursor(6, 182);
        tft.print("SECURITY");
        tft.setTextColor(ILI9341_WHITE);
        tft.setTextSize(2);
        tft.setCursor(6, 194);
        tft.print(doorLocked ? "LOCKED" : "OPEN");

        lastActiveLightsCount = activeLightsCount;
        lastIsFanActive = isFanActive;
        lastRoomTemperature = roomTemperature;
        lastDoorLocked = doorLocked;
    }

    // 3. Draw Right Column (Speech Bubble)
    bool rightChanged = (strcmp(lastUserQuery, lastUserQueryCache) != 0 ||
                         strcmp(lastJarvisReply, lastJarvisReplyCache) != 0);
                         
    if (rightChanged) {
        tft.fillRect(218, 31, 95, 200, ILI9341_BLACK);
        tft.drawRoundRect(217, 30, 100, 202, 4, ILI9341_DARKGREY);

        // User Query
        tft.setTextColor(ILI9341_CYAN);
        tft.setTextSize(1);
        tft.setCursor(221, 36);
        tft.print("UMAI:");
        
        tft.setTextColor(ILI9341_WHITE);
        drawWrappedText(lastUserQuery, 221, 47, 15, 6);

        // Assistant Response
        tft.setTextColor(ILI9341_BLUE);
        tft.setTextSize(1);
        tft.setCursor(221, 115);
        tft.print("JARVIS:");
        
        tft.setTextColor(ILI9341_GREEN);
        drawWrappedText(lastJarvisReply, 221, 126, 15, 9);

        strncpy(lastUserQueryCache, lastUserQuery, sizeof(lastUserQueryCache) - 1);
        lastUserQueryCache[sizeof(lastUserQueryCache) - 1] = '\0';
        strncpy(lastJarvisReplyCache, lastJarvisReply, sizeof(lastJarvisReplyCache) - 1);
        lastJarvisReplyCache[sizeof(lastJarvisReplyCache) - 1] = '\0';
    }
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

void updateUI() {
    drawHeader();

    // Map system state to eye animations & overlays
    if (strcmp(currentSystemState, "SPOTIFY_PLAYING") == 0 || strcmp(currentSystemState, "SPOTIFY_PAUSED") == 0) {
        updateEyes("IDLE");
        drawEyes();
        drawMusicOverlay(currentSystemState);
    } else if (strcmp(currentSystemState, "SPEAKER_DISCONNECTED") == 0) {
        updateEyes("THINKING"); // Spin/searching animation
        drawEyes();
        
        if (strcmp(currentSystemState, lastDrawnState) != 0) {
            drawSpeakerDisconnectedScreen();
            strncpy(lastDrawnState, currentSystemState, sizeof(lastDrawnState) - 1);
            lastDrawnState[sizeof(lastDrawnState) - 1] = '\0';
        }
    } else if (strcmp(currentSystemState, "BACKEND_DISCONNECTED") == 0) {
        updateEyes("THINKING"); // Reconnecting eyes
        drawEyes();
        
        if (strcmp(currentSystemState, lastDrawnState) != 0) {
            drawBackendDisconnectedScreen();
            strncpy(lastDrawnState, currentSystemState, sizeof(lastDrawnState) - 1);
            lastDrawnState[sizeof(lastDrawnState) - 1] = '\0';
        }
    } else {
        // Holographic split room dashboard rendering
        drawDashboardLayout();
        updateEyes(currentSystemState);
        drawEyes();
    }
}
