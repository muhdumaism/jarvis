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

void setSystemState(const char* newState) {
    if (strcmp(currentSystemState, newState) != 0) {
        strncpy(currentSystemState, newState, sizeof(currentSystemState) - 1);
        currentSystemState[sizeof(currentSystemState) - 1] = '\0';
        clearDisplay(); // clear whole frame on state change
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
        // Standard non-music rendering
        updateEyes(currentSystemState);
        drawEyes();
        
        static char lastStatusOverlay[32] = "";
        if (strcmp(currentSystemState, lastStatusOverlay) != 0) {
            drawStatusOverlay(currentSystemState, ILI9341_CYAN);
            strncpy(lastStatusOverlay, currentSystemState, sizeof(lastStatusOverlay) - 1);
            lastStatusOverlay[sizeof(lastStatusOverlay) - 1] = '\0';
        }
    }
}
