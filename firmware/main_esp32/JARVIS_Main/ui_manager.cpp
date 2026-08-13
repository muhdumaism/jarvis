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
    tft.fillRect(0, 0, TFT_WIDTH, 24, ILI9341_DARKGREY);
    tft.setTextSize(1);
    tft.setTextColor(ILI9341_WHITE);
    tft.setCursor(8, 8);
    tft.print("JARVIS ASSISTANT");

    // WiFi status indicator dot
    tft.fillCircle(TFT_WIDTH - 15, 12, 4, wifiConnected ? ILI9341_GREEN : ILI9341_RED);
}

void drawMusicOverlay(const char* state) {
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

    // Progress bar calculation
    int currentPos = trackPosition;
    if (trackDuration > 0 && strcmp(state, "SPOTIFY_PLAYING") == 0) {
        unsigned long elapsed = millis() - lastMusicUpdate;
        currentPos = min(trackDuration, trackPosition + (int)elapsed);
    }

    int barWidth = TFT_WIDTH - 40;
    int barHeight = 6;
    int barX = 20;
    int barY = 190;

    tft.drawRect(barX, barY, barWidth, barHeight, ILI9341_DARKGREY);
    if (trackDuration > 0) {
        int fillWidth = (int)(((float)currentPos / trackDuration) * barWidth);
        if (fillWidth > barWidth) fillWidth = barWidth;
        tft.fillRect(barX + 1, barY + 1, fillWidth - 2, barHeight - 2, ILI9341_BLUE);
    }

    // Time Label
    tft.setTextColor(ILI9341_LIGHTGREY);
    tft.setTextSize(1);
    tft.setCursor(20, 205);
    tft.printf("%d:%02d / %d:%02d", currentPos / 60000, (currentPos % 60000) / 1000,
                                    trackDuration / 60000, (trackDuration % 60000) / 1000);

    // Speaker status bottom right
    tft.setCursor(TFT_WIDTH - 130, 205);
    if (speakerConnected) {
        tft.setTextColor(ILI9341_GREEN);
        tft.print("SPK: CONNECTED");
    } else {
        tft.setTextColor(ILI9341_RED);
        tft.print("SPK: DISCONNECTED");
    }

    // State bottom overlay
    tft.setCursor(20, 220);
    tft.setTextColor(ILI9341_CYAN);
    tft.print(state);
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
        drawSpeakerDisconnectedScreen();
    } else if (strcmp(currentSystemState, "BACKEND_DISCONNECTED") == 0) {
        updateEyes("THINKING"); // Reconnecting eyes
        drawEyes();
        drawBackendDisconnectedScreen();
    } else {
        // Standard non-music rendering
        updateEyes(currentSystemState);
        drawEyes();
        drawStatusOverlay(currentSystemState, ILI9341_CYAN);
    }
}
