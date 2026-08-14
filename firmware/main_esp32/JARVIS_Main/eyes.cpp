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

void updateEyes(const char* state) {
    unsigned long now = millis();

    // 1. Determine targets based on states
    if (strcmp(state, "LISTENING") == 0) {
        // Look slightly wide and up
        leftEye.targetY = leftEye.y - 4;
        rightEye.targetY = rightEye.y - 4;
        leftEye.targetX = leftEye.x;
        rightEye.targetX = rightEye.x;
    } else if (strcmp(state, "THINKING") == 0) {
        // Spin/look left and right
        int offset = (now / 300) % 2 == 0 ? 8 : -8;
        leftEye.targetX = leftEye.x + offset;
        rightEye.targetX = rightEye.x + offset;
    } else if (strcmp(state, "SPEAKING") == 0) {
        // Pulsate radius or height slightly
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

    // 3. Blink handling
    if (!isBlinking && (now - lastBlinkTime > blinkInterval)) {
        isBlinking = true;
        blinkStartTime = now;
        blinkInterval = 3000 + random(2000); // randomize next blink interval
    }

    if (isBlinking && (now - blinkStartTime > blinkDuration)) {
        isBlinking = false;
        lastBlinkTime = now;
    }
}

static int lastLeftEyeX = -1;
static int lastLeftEyeY = -1;
static int lastRightEyeX = -1;
static int lastRightEyeY = -1;
static bool lastBlinking = false;

void drawEyes() {
    // Check if eyes actually moved or blink status changed
    bool eyesMoved = (leftEye.currentX != lastLeftEyeX || leftEye.currentY != lastLeftEyeY ||
                      rightEye.currentX != lastRightEyeX || rightEye.currentY != lastRightEyeY ||
                      isBlinking != lastBlinking);

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
            tft.fillCircle(leftEye.currentX, leftEye.currentY, leftEye.r / 2, ILI9341_CYAN);
            tft.fillCircle(rightEye.currentX, rightEye.currentY, rightEye.r / 2, ILI9341_CYAN);
        }

        lastLeftEyeX = leftEye.currentX;
        lastLeftEyeY = leftEye.currentY;
        lastRightEyeX = rightEye.currentX;
        lastRightEyeY = rightEye.currentY;
        lastBlinking = isBlinking;
    }
}
