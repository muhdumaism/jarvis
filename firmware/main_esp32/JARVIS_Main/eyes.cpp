#include "eyes.h"

extern char currentSystemState[];
extern char currentTitle[64];

Eye leftEye;
Eye rightEye;

unsigned long lastBlinkTime = 0;
unsigned long blinkInterval = 4000; // Blink every 4 seconds
bool isBlinking = false;
unsigned long blinkStartTime = 0;
const int blinkDuration = 150; // 150ms blink speed

void initEyes() {
    int eyeSpacing = 52;
    int centerY = 110;
    
    // Left Eye configuration
    leftEye.x = TFT_WIDTH / 2 - eyeSpacing / 2; // 160 - 26 = 134
    leftEye.y = centerY;
    leftEye.r = 18; // Smaller to fit inside center hologram circle
    leftEye.targetX = leftEye.x;
    leftEye.targetY = leftEye.y;
    leftEye.currentX = leftEye.x;
    leftEye.currentY = leftEye.y;

    // Right Eye configuration
    rightEye.x = TFT_WIDTH / 2 + eyeSpacing / 2; // 160 + 26 = 186
    rightEye.y = centerY;
    rightEye.r = 18;
    rightEye.targetX = rightEye.x;
    rightEye.targetY = rightEye.y;
    rightEye.currentX = rightEye.x;
    rightEye.currentY = rightEye.y;
    
    lastBlinkTime = millis();
}

static char currentEyeState[32] = "IDLE";
static int blinkStage = 0; // 0=Idle, 1=First blink, 2=Open gap, 3=Second blink

void updateEyes(const char* state) {
    unsigned long now = millis();
    strncpy(currentEyeState, state, sizeof(currentEyeState) - 1);
    currentEyeState[sizeof(currentEyeState) - 1] = '\0';

    // 1. Determine targets based on states
    if (strcmp(state, "LISTENING") == 0) {
        // Look slightly wide and up
        leftEye.targetY = leftEye.y - 4;
        rightEye.targetY = rightEye.y - 4;
        leftEye.targetX = leftEye.x;
        rightEye.targetX = rightEye.x;
    } else if (strcmp(state, "THINKING") == 0) {
        // Look left and right
        int offset = (now / 300) % 2 == 0 ? 8 : -8;
        leftEye.targetX = leftEye.x + offset;
        rightEye.targetX = rightEye.x + offset;
    } else if (strcmp(state, "SPEAKING") == 0) {
        // Keep centered
        leftEye.targetY = leftEye.y;
        rightEye.targetY = rightEye.y;
    } else {
        // Idle - occasionally look around randomly
        if (now % 3000 < 50) {
            int randomX = random(-6, 7);
            int randomY = random(-4, 5);
            leftEye.targetX = leftEye.x + randomX;
            leftEye.targetY = leftEye.y + randomY;
            rightEye.targetX = rightEye.x + randomX;
            rightEye.targetY = rightEye.y + randomY;
        }
    }

    // 2. Linear interpolation (LERP) movement
    leftEye.currentX += (leftEye.targetX - leftEye.currentX) * 0.2;
    leftEye.currentY += (leftEye.targetY - leftEye.currentY) * 0.2;
    rightEye.currentX += (rightEye.targetX - rightEye.currentX) * 0.2;
    rightEye.currentY += (rightEye.targetY - rightEye.currentY) * 0.2;

    // 3. Natural Double-Blink state machine
    if (blinkStage == 0 && (now - lastBlinkTime > blinkInterval)) {
        blinkStage = 1;
        blinkStartTime = now;
        isBlinking = true;
    }

    if (blinkStage == 1) {
        if (now - blinkStartTime > blinkDuration) {
            isBlinking = false;
            if (random(100) < 30) { // 30% chance of double blink
                blinkStage = 2;
                blinkStartTime = now;
            } else {
                blinkStage = 0;
                lastBlinkTime = now;
                blinkInterval = 4000 + random(3000); // Randomize next blink
            }
        }
    } else if (blinkStage == 2) {
        // Keep eyes open for 120ms between blinks
        if (now - blinkStartTime > 120) {
            blinkStage = 3;
            blinkStartTime = now;
            isBlinking = true;
        }
    } else if (blinkStage == 3) {
        if (now - blinkStartTime > blinkDuration) {
            isBlinking = false;
            blinkStage = 0;
            lastBlinkTime = now;
            blinkInterval = 4000 + random(3000);
        }
    }
}

static int lastLeftEyeX = -1;
static int lastLeftEyeY = -1;
static int lastRightEyeX = -1;
static int lastRightEyeY = -1;
static int lastLeftPupilR = -1;
static int lastRightPupilR = -1;
static bool lastBlinking = false;
static char lastDrawnEyeState[32] = "";

void resetEyesDrawCache() {
    lastLeftEyeX = -1;
    lastLeftEyeY = -1;
    lastRightEyeX = -1;
    lastRightEyeY = -1;
    lastLeftPupilR = -1;
    lastRightPupilR = -1;
    lastBlinking = false;
    lastDrawnEyeState[0] = '\0';
}

void drawThickUpperArc(int x0, int y0, int r, int thickness, uint16_t color) {
    for (int curR = r - thickness + 1; curR <= r; curR++) {
        int x = 0;
        int y = curR;
        int d = 3 - 2 * curR;
        
        while (y >= x) {
            // Draw upper half of circle
            tft.drawPixel(x0 + x, y0 - y, color);
            tft.drawPixel(x0 - x, y0 - y, color);
            tft.drawPixel(x0 + y, y0 - x, color);
            tft.drawPixel(x0 - y, y0 - x, color);
            
            if (d < 0) {
                d += 4 * x + 6;
            } else {
                d += 4 * (x - y) + 10;
                y--;
            }
            x++;
        }
    }
}

void drawRobot(int centerX, int centerY, const char* state, bool isBlinking) {
    // Colors
    uint16_t DarkBrown = 0x4901;
    uint16_t GoldMain = 0xFEC8;
    uint16_t GoldLight = 0xFFF6;
    uint16_t GoldShadow = 0xE520;
    uint16_t MintGreen = 0x3F2A;
    uint16_t VisorBlack = 0x18C3;
    uint16_t Cyan = ILI9341_CYAN;
    uint16_t Red = ILI9341_RED;

    // Bobbing animations based on state
    int bodyBob = 0;
    int earBob = 0;
    
    if (strcmp(state, "SPEAKING") == 0) {
        bodyBob = (int)(2.0 * sin(millis() / 150.0));
        earBob = (int)(3.0 * sin(millis() / 150.0 + 1.0));
    } else if (strcmp(state, "LISTENING") == 0) {
        bodyBob = (int)(1.0 * sin(millis() / 100.0));
        earBob = -3; // Ears perk up
    } else if (strcmp(state, "THINKING") == 0) {
        bodyBob = (int)(3.0 * sin(millis() / 80.0));
        earBob = (int)(4.0 * cos(millis() / 80.0));
    } else if (strcmp(state, "ALARM_TRIGGERED") == 0) {
        bodyBob = (int)(4.0 * sin(millis() / 50.0)); // Shaking
        earBob = 2; // Ears droop
    } else {
        // Idle bobbing
        bodyBob = (int)(1.5 * sin(millis() / 250.0));
        earBob = (int)(1.5 * sin(millis() / 250.0));
    }

    int cy = centerY + bodyBob;

    // 1. Draw Left Ear
    tft.fillTriangle(centerX - 27, cy - 35 + earBob, centerX - 37, cy - 12 + earBob, centerX - 17, cy - 10 + earBob, DarkBrown);
    tft.fillTriangle(centerX - 27, cy - 33 + earBob, centerX - 35, cy - 12 + earBob, centerX - 18, cy - 11 + earBob, GoldMain);
    tft.drawLine(centerX - 24, cy - 25 + earBob, centerX - 29, cy - 12 + earBob, GoldShadow);
    tft.drawLine(centerX - 35, cy - 12 + earBob, centerX - 18, cy - 11 + earBob, MintGreen);

    // 2. Draw Right Ear
    tft.fillTriangle(centerX + 27, cy - 35 + earBob, centerX + 17, cy - 10 + earBob, centerX + 37, cy - 12 + earBob, DarkBrown);
    tft.fillTriangle(centerX + 27, cy - 33 + earBob, centerX + 18, cy - 11 + earBob, centerX + 35, cy - 12 + earBob, GoldMain);
    tft.drawLine(centerX + 24, cy - 25 + earBob, centerX + 29, cy - 12 + earBob, GoldShadow);
    tft.drawLine(centerX + 18, cy - 11 + earBob, centerX + 35, cy - 12 + earBob, MintGreen);

    // 3. Draw Body
    tft.fillCircle(centerX, cy, 33, DarkBrown);
    tft.fillCircle(centerX, cy, 31, GoldMain);
    for (int r = 26; r <= 30; r++) {
        tft.drawCircleHelper(centerX + 1, cy + 1, r, 2, GoldShadow);
        tft.drawCircleHelper(centerX + 1, cy + 1, r, 4, GoldShadow);
    }
    tft.fillCircle(centerX - 13, cy - 13, 5, GoldLight);
    tft.drawCircleHelper(centerX, cy, 29, 4, MintGreen);
    tft.drawCircleHelper(centerX, cy, 28, 4, MintGreen);

    // Earpieces
    tft.fillCircle(centerX - 31, cy, 5, DarkBrown);
    tft.fillCircle(centerX - 31, cy, 3, VisorBlack);
    tft.fillCircle(centerX + 31, cy, 5, DarkBrown);
    tft.fillCircle(centerX + 31, cy, 3, VisorBlack);

    // 4. Draw Visor
    uint16_t visorBg = (strcmp(state, "ALARM_TRIGGERED") == 0) ? tft.color565(120, 0, 0) : VisorBlack;
    tft.fillRoundRect(centerX - 22, cy - 8, 44, 18, 5, DarkBrown);
    tft.fillRoundRect(centerX - 20, cy - 7, 40, 16, 4, visorBg);

    // 5. Draw Face
    if (strcmp(state, "THINKING") == 0) {
        int scan = (millis() / 120) % 4;
        if (scan == 0) {
            tft.fillRect(centerX - 12, cy - 4, 4, 2, Cyan);
            tft.fillRect(centerX + 8, cy - 4, 4, 2, Cyan);
        } else if (scan == 1) {
            tft.fillRect(centerX - 10, cy - 6, 2, 4, Cyan);
            tft.fillRect(centerX + 10, cy - 6, 2, 4, Cyan);
        } else if (scan == 2) {
            tft.fillRect(centerX - 12, cy - 2, 4, 2, Cyan);
            tft.fillRect(centerX + 8, cy - 2, 4, 2, Cyan);
        } else {
            tft.fillRect(centerX - 14, cy - 6, 2, 4, Cyan);
            tft.fillRect(centerX + 6, cy - 6, 2, 4, Cyan);
        }
        tft.drawLine(centerX - 4, cy + 4, centerX - 2, cy + 6, Cyan);
        tft.drawLine(centerX - 2, cy + 6, centerX, cy + 4, Cyan);
        tft.drawLine(centerX, cy + 4, centerX + 2, cy + 6, Cyan);
        tft.drawLine(centerX + 2, cy + 6, centerX + 4, cy + 4, Cyan);
    } 
    else if (strcmp(state, "LISTENING") == 0) {
        tft.fillCircle(centerX - 11, cy - 3, 3, Cyan);
        tft.fillCircle(centerX + 11, cy - 3, 3, Cyan);
        tft.fillCircle(centerX - 11, cy - 3, 1, VisorBlack);
        tft.fillCircle(centerX + 11, cy - 3, 1, VisorBlack);
        tft.drawCircle(centerX, cy + 4, 2, Cyan);
    } 
    else if (strcmp(state, "ALARM_TRIGGERED") == 0) {
        tft.drawLine(centerX - 13, cy - 1, centerX - 9, cy - 4, Red);
        tft.drawLine(centerX + 9, cy - 4, centerX + 13, cy - 1, Red);
        tft.drawLine(centerX - 3, cy + 5, centerX, cy + 3, Red);
        tft.drawLine(centerX, cy + 3, centerX + 3, cy + 5, Red);
        tft.drawFastVLine(centerX - 11, cy + 1, 10, Cyan);
        tft.drawFastVLine(centerX + 11, cy + 1, 10, Cyan);
    } 
    else {
        if (isBlinking) {
            tft.drawFastHLine(centerX - 13, cy - 3, 6, Cyan);
            tft.drawFastHLine(centerX + 7, cy - 3, 6, Cyan);
        } else {
            tft.fillRoundRect(centerX - 13, cy - 5, 5, 5, 1, Cyan);
            tft.fillRoundRect(centerX + 8, cy - 5, 5, 5, 1, Cyan);
        }
        if (strcmp(state, "SPEAKING") == 0) {
            if ((millis() / 150) % 2 == 0) {
                tft.fillRoundRect(centerX - 2, cy + 3, 4, 4, 1, Cyan);
            } else {
                tft.drawFastHLine(centerX - 2, cy + 4, 4, Cyan);
            }
        } else {
            tft.drawLine(centerX - 4, cy + 4, centerX - 2, cy + 6, Cyan);
            tft.drawLine(centerX - 2, cy + 6, centerX, cy + 4, Cyan);
            tft.drawLine(centerX, cy + 4, centerX + 2, cy + 6, Cyan);
            tft.drawLine(centerX + 2, cy + 6, centerX + 4, cy + 4, Cyan);
        }
    }
}

void drawEyes() {
    bool isMusicMode = (currentTitle[0] != '\0' && 
                        strcmp(currentSystemState, "BACKEND_DISCONNECTED") != 0 &&
                        strcmp(currentSystemState, "SPEAKER_DISCONNECTED") != 0);

    // Bouncing offset for music mode
    int bobOffset = 0;
    if (isMusicMode) {
        bobOffset = (int)(4.0 * sin(millis() / 150.0));
    }

    // Determine Y coordinate based on mode and bobbing
    int leftEyeY = isMusicMode ? (145 + bobOffset) : 110;
    int rightEyeY = isMusicMode ? (145 + bobOffset) : 110;

    // Force eyesMoved to be true in music mode or animated states to keep bobbing active
    bool eyesMoved = (leftEyeY != lastLeftEyeY || rightEyeY != lastRightEyeY ||
                      isBlinking != lastBlinking ||
                      isMusicMode || 
                      strcmp(currentEyeState, "IDLE") != 0 || // Always update for assistant bobbing
                      strcmp(currentEyeState, lastDrawnEyeState) != 0);

    if (eyesMoved) {
        if (isMusicMode) {
            // Clear music eyes bounding box (X: 110 to 210, Y: 120 to 165)
            tft.fillRect(110, 120, 100, 45, ILI9341_BLACK);

            int r = 15;
            int thick = 3;
            if (isBlinking) {
                tft.drawFastHLine(135 - r, leftEyeY, r * 2, ILI9341_CYAN);
                tft.drawFastHLine(185 - r, rightEyeY, r * 2, ILI9341_CYAN);
            } else {
                drawThickUpperArc(135, leftEyeY, r, thick, ILI9341_CYAN);
                drawThickUpperArc(185, rightEyeY, r, thick, ILI9341_CYAN);
            }
        } else {
            // Clear assistant robot bounding box (X: 115 to 205, Y: 60 to 158)
            tft.fillRect(115, 60, 90, 98, ILI9341_BLACK);

            // Draw full animated robot character!
            drawRobot(160, 110, currentEyeState, isBlinking);
        }

        lastLeftEyeX = leftEye.currentX; 
        lastLeftEyeY = leftEyeY;
        lastRightEyeX = rightEye.currentX;
        lastRightEyeY = rightEyeY;
        lastBlinking = isBlinking;
        strncpy(lastDrawnEyeState, currentEyeState, sizeof(lastDrawnEyeState) - 1);
        lastDrawnEyeState[sizeof(lastDrawnEyeState) - 1] = '\0';
    }
}
