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
static bool lastDrawnEyeStateWasMusic = false;
static char lastDrawnEyeState[32] = "";

void resetEyesDrawCache() {
    lastLeftEyeX = -1;
    lastLeftEyeY = -1;
    lastRightEyeX = -1;
    lastRightEyeY = -1;
    lastLeftPupilR = -1;
    lastRightPupilR = -1;
    lastBlinking = false;
    lastDrawnEyeStateWasMusic = false;
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

void drawEyes() {
    bool isMusicMode = (currentTitle[0] != '\0' && 
                        strcmp(currentSystemState, "BACKEND_DISCONNECTED") != 0 &&
                        strcmp(currentSystemState, "SPEAKER_DISCONNECTED") != 0);

    // Bouncing offset for music mode
    int bobOffset = 0;
    if (isMusicMode) {
        bobOffset = (int)(4.0 * sin(millis() / 150.0));
    }

    // Determine target/current coordinate positions based on mode and bobbing
    int leftEyeX = leftEye.currentX;
    int rightEyeX = rightEye.currentX;
    int leftEyeY = isMusicMode ? (145 + bobOffset) : leftEye.currentY;
    int rightEyeY = isMusicMode ? (145 + bobOffset) : rightEye.currentY;

    // Check state and blinking transitions
    bool stateChanged = (strcmp(currentEyeState, lastDrawnEyeState) != 0 || isMusicMode != lastDrawnEyeStateWasMusic);
    bool blinkChanged = (isBlinking != lastBlinking);
    
    // Check if coordinates moved (L-R LERP or Music bobbing)
    bool eyesMoved = (leftEyeX != lastLeftEyeX || leftEyeY != lastLeftEyeY || 
                      rightEyeX != lastRightEyeX || rightEyeY != lastRightEyeY ||
                      stateChanged || blinkChanged);

    if (eyesMoved) {
        // Localized clear to reduce screen flickering completely
        if (lastDrawnEyeStateWasMusic) {
            // Clear music eyes bounding box
            tft.fillRect(110, 120, 100, 45, ILI9341_BLACK);
        } else {
            // Clear assistant eyes bounding box
            tft.fillRect(110, 85, 100, 45, ILI9341_BLACK);
        }

        int r = 15;
        int thick = 3;
        if (isBlinking) {
            // Draw closed line eyes
            tft.drawFastHLine(leftEyeX - r, leftEyeY, r * 2, ILI9341_CYAN);
            tft.drawFastHLine(rightEyeX - r, rightEyeY, r * 2, ILI9341_CYAN);
        } else {
            // Draw open line eyes (arcs)
            drawThickUpperArc(leftEyeX, leftEyeY, r, thick, ILI9341_CYAN);
            drawThickUpperArc(rightEyeX, rightEyeY, r, thick, ILI9341_CYAN);
        }

        // Update coordinate cache
        lastLeftEyeX = leftEyeX;
        lastLeftEyeY = leftEyeY;
        lastRightEyeX = rightEyeX;
        lastRightEyeY = rightEyeY;
        lastBlinking = isBlinking;
        lastDrawnEyeStateWasMusic = isMusicMode;
        strncpy(lastDrawnEyeState, currentEyeState, sizeof(lastDrawnEyeState) - 1);
        lastDrawnEyeState[sizeof(lastDrawnEyeState) - 1] = '\0';
    }
}
