#include "eyes.h"

Eye leftEye;
Eye rightEye;

unsigned long lastBlinkTime = 0;
unsigned long blinkInterval = 4000; // Blink every 4 seconds
bool isBlinking = false;
unsigned long blinkStartTime = 0;
const int blinkDuration = 150; // 150ms blink speed

void initEyes() {
    int eyeSpacing = 80;
    int centerY = TFT_HEIGHT / 2 - 10;
    
    // Left Eye configuration
    leftEye.x = TFT_WIDTH / 2 - eyeSpacing / 2;
    leftEye.y = centerY;
    leftEye.r = 30;
    leftEye.targetX = leftEye.x;
    leftEye.targetY = leftEye.y;
    leftEye.currentX = leftEye.x;
    leftEye.currentY = leftEye.y;

    // Right Eye configuration
    rightEye.x = TFT_WIDTH / 2 + eyeSpacing / 2;
    rightEye.y = centerY;
    rightEye.r = 30;
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

void drawEyes() {
    // 1. Calculate state-based pupil sizes
    int leftPupilR = leftEye.r / 2;
    int rightPupilR = rightEye.r / 2;

    if (strcmp(currentEyeState, "SPEAKING") == 0) {
        // Pulsate pupil size to simulate talking
        leftPupilR = leftEye.r / 2 + (int)(3.5 * sin(millis() / 120.0));
        rightPupilR = rightEye.r / 2 + (int)(3.5 * sin(millis() / 120.0));
    } else if (strcmp(currentEyeState, "LISTENING") == 0) {
        // Dilate pupils when listening
        leftPupilR = leftEye.r / 2 + 4;
        rightPupilR = rightEye.r / 2 + 4;
    } else if (strcmp(currentEyeState, "THINKING") == 0) {
        // Contract pupils when thinking
        leftPupilR = leftEye.r / 2 - 3;
        rightPupilR = rightEye.r / 2 - 3;
    }

    // Check if eyes actually moved, pupil dilated, blink status changed, or state changed
    bool eyesMoved = (leftEye.currentX != lastLeftEyeX || leftEye.currentY != lastLeftEyeY ||
                      rightEye.currentX != lastRightEyeX || rightEye.currentY != lastRightEyeY ||
                      leftPupilR != lastLeftPupilR || rightPupilR != lastRightPupilR ||
                      isBlinking != lastBlinking ||
                      strcmp(currentEyeState, lastDrawnEyeState) != 0);

    if (eyesMoved) {
        // Clear only the bounding box of the eyes to save SPI bandwidth
        tft.fillRect(0, 30, TFT_WIDTH, 115, ILI9341_BLACK);

        if (isBlinking) {
            // Draw blink state as horizontal lines
            tft.drawFastHLine(leftEye.x - leftEye.r, leftEye.y, leftEye.r * 2, ILI9341_CYAN);
            tft.drawFastHLine(rightEye.x - rightEye.r, rightEye.y, rightEye.r * 2, ILI9341_CYAN);
        } else {
            // Draw outer eyeballs
            tft.drawCircle(leftEye.x, leftEye.y, leftEye.r, ILI9341_CYAN);
            tft.drawCircle(rightEye.x, rightEye.y, rightEye.r, ILI9341_CYAN);

            // Draw inner pupils (procedurally shifted)
            tft.fillCircle(leftEye.currentX, leftEye.currentY, leftPupilR, ILI9341_CYAN);
            tft.fillCircle(rightEye.currentX, rightEye.currentY, rightPupilR, ILI9341_CYAN);

            // Draw expressive eyebrows based on states
            if (strcmp(currentEyeState, "LISTENING") == 0) {
                // Raise eyebrows high (curious/attentive)
                tft.drawFastHLine(leftEye.x - 20, leftEye.y - 38, 40, ILI9341_CYAN);
                tft.drawFastHLine(rightEye.x - 20, rightEye.y - 38, 40, ILI9341_CYAN);
            } else if (strcmp(currentEyeState, "THINKING") == 0) {
                // Slant eyebrows inwards (focused frowny eyebrows)
                tft.drawLine(leftEye.x - 20, leftEye.y - 34, leftEye.x + 15, leftEye.y - 40, ILI9341_CYAN);
                tft.drawLine(rightEye.x - 15, rightEye.y - 40, rightEye.x + 20, rightEye.y - 34, ILI9341_CYAN);
            } else if (strcmp(currentEyeState, "SPEAKING") == 0) {
                // Bouncing eyebrows matching speech sine wave
                int yOffset = (int)(2.0 * sin(millis() / 120.0));
                tft.drawFastHLine(leftEye.x - 20, leftEye.y - 36 + yOffset, 40, ILI9341_CYAN);
                tft.drawFastHLine(rightEye.x - 20, rightEye.y - 36 + yOffset, 40, ILI9341_CYAN);
            } else {
                // Relaxed horizontal eyebrows
                tft.drawFastHLine(leftEye.x - 20, leftEye.y - 35, 40, ILI9341_CYAN);
                tft.drawFastHLine(rightEye.x - 20, rightEye.y - 35, 40, ILI9341_CYAN);
            }
        }

        lastLeftEyeX = leftEye.currentX;
        lastLeftEyeY = leftEye.currentY;
        lastRightEyeX = rightEye.currentX;
        lastRightEyeY = rightEye.currentY;
        lastLeftPupilR = leftPupilR;
        lastRightPupilR = rightPupilR;
        lastBlinking = isBlinking;
        strncpy(lastDrawnEyeState, currentEyeState, sizeof(lastDrawnEyeState) - 1);
        lastDrawnEyeState[sizeof(lastDrawnEyeState) - 1] = '\0';
    }
}
