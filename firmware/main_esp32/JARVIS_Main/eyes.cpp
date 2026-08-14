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

static float currentX = 160.0;
static float currentY = 110.0;
static float vx = 0.5;
static float vy = 0.4;
static float lastRobotX = -1.0;
static float lastRobotY = -1.0;

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
    currentX = 160.0;
    currentY = 110.0;
    vx = 0.5;
    vy = 0.4;
    lastRobotX = -1.0;
    lastRobotY = -1.0;
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

static int lastCy = -1;
static int lastEarBob = 0;
static bool lastWasMusic = false;

void drawRobotNew(int cx, int cy, const char* state, bool isBlinking) {
    // Colors matching the pixel art robot
    uint16_t Red = ILI9341_RED;
    uint16_t DarkGrey = 0x3186;     // Outer borders
    uint16_t VisorBlack = 0x10A2;    // Very dark visor background
    uint16_t HeadphoneBlue = 0x32AA; // Dark slate blue headphones
    uint16_t BodyWhite = 0xE75C;     // Light blueish grey body
    uint16_t HandBlue = 0xAD7A;      // Light blue detached hands
    uint16_t Cyan = ILI9341_CYAN;
    uint16_t Green = ILI9341_GREEN;
    
    // 1. Draw Helmet (Red rounded rect with borders)
    tft.fillRoundRect(cx - 24, cy - 35, 48, 42, 10, Red);
    tft.drawRoundRect(cx - 24, cy - 35, 48, 42, 10, DarkGrey);
    
    // 2. Draw Visor Screen
    tft.fillRoundRect(cx - 18, cy - 30, 36, 32, 6, VisorBlack);
    
    // 3. Draw Visor Face/Eye animations
    if (strcmp(state, "ALARM_TRIGGERED") == 0) {
        // Red flashing warning bars
        uint16_t alarmColor = ((millis() / 250) % 2 == 0) ? ILI9341_RED : VisorBlack;
        tft.fillRoundRect(cx - 10, cy - 22, 4, 16, 2, alarmColor);
        tft.fillRoundRect(cx + 6,  cy - 22, 4, 16, 2, alarmColor);
    } 
    else if (isBlinking) {
        // Flat blinking lines
        tft.fillRect(cx - 10, cy - 14, 4, 2, Cyan);
        tft.fillRect(cx + 6,  cy - 14, 4, 2, Cyan);
    } 
    else if (strcmp(state, "THINKING") == 0) {
        // Horizontal scanning eyes
        int scanOffset = (int)(6.0 * sin(millis() / 150.0));
        tft.fillRoundRect(cx - 10 + scanOffset, cy - 22, 4, 16, 2, Cyan);
        tft.fillRoundRect(cx + 6 + scanOffset,  cy - 22, 4, 16, 2, Cyan);
    } 
    else if (strcmp(state, "SPEAKING") == 0) {
        // Bouncing/speaking vertical eye bars
        int eyeHeight = 10 + (int)(6.0 * abs(sin(millis() / 100.0)));
        int topOffset = (16 - eyeHeight) / 2;
        tft.fillRoundRect(cx - 10, cy - 22 + topOffset, 4, eyeHeight, 2, Cyan);
        tft.fillRoundRect(cx + 6,  cy - 22 + topOffset, 4, eyeHeight, 2, Cyan);
    } 
    else if (strcmp(state, "LISTENING") == 0) {
        // Taller attentive eyes for listening mode
        tft.fillRoundRect(cx - 10, cy - 24, 4, 20, 2, Cyan);
        tft.fillRoundRect(cx + 6,  cy - 24, 4, 20, 2, Cyan);
    } 
    else {
        // Idle / Music mode standard vertical pill eyes
        tft.fillRoundRect(cx - 10, cy - 22, 4, 16, 2, Cyan);
        tft.fillRoundRect(cx + 6,  cy - 22, 4, 16, 2, Cyan);
    }
    
    // 4. Draw Headphone Ear Cups
    tft.fillRoundRect(cx - 29, cy - 24, 5, 20, 3, HeadphoneBlue);
    tft.fillRoundRect(cx + 24, cy - 24, 5, 20, 3, HeadphoneBlue);
    
    // 5. Draw Neck
    tft.fillRect(cx - 4, cy + 7, 8, 4, Red);
    
    // 6. Draw White Body (with red stripe and green light)
    tft.fillRoundRect(cx - 16, cy + 11, 32, 24, 6, BodyWhite);
    tft.fillRect(cx - 16, cy + 23, 32, 4, Red);
    tft.fillRect(cx - 2, cy + 14, 4, 7, Green);
    
    // 7. Draw Detached Floating Hands (Spheres)
    tft.fillCircle(cx - 28, cy + 22, 6, HandBlue);
    tft.fillCircle(cx + 28, cy + 22, 6, HandBlue);
}

void drawEyes() {
    bool isMusicMode = (currentTitle[0] != '\0' && 
                        strcmp(currentSystemState, "BACKEND_DISCONNECTED") != 0 &&
                        strcmp(currentSystemState, "SPEAKER_DISCONNECTED") != 0);

    float targetX = 160.0;
    float targetY = 110.0;
    bool shouldFloat = false;

    // Check system state to choose animation mode
    if (isMusicMode) {
        // Music mode: quick center at Y=145 with a small rhythmic dance bob
        targetX = 160.0;
        targetY = 145.0 + (int)(4.0 * sin(millis() / 150.0));
    } 
    else if (strcmp(currentEyeState, "IDLE") == 0) {
        // Idle state: float around the screen!
        shouldFloat = true;
    } 
    else {
        // Active states (LISTENING, THINKING, SPEAKING, ALARM): Center at Y=110
        targetX = 160.0;
        targetY = 110.0;
    }

    // Update positions
    if (shouldFloat) {
        currentX += vx;
        currentY += vy;

        // Bounce check on boundaries (keeps robot safely visible below header and above waveform)
        if (currentX < 40) {
            currentX = 40;
            vx = -vx;
            float speed = 0.3 + (random(60) / 100.0);
            vx = (vx > 0) ? speed : -speed;
        }
        if (currentX > 280) {
            currentX = 280;
            vx = -vx;
            float speed = 0.3 + (random(60) / 100.0);
            vx = (vx > 0) ? speed : -speed;
        }
        if (currentY < 65) {
            currentY = 65;
            vy = -vy;
            float speed = 0.3 + (random(60) / 100.0);
            vy = (vy > 0) ? speed : -speed;
        }
        if (currentY > 145) {
            currentY = 145;
            vy = -vy;
            float speed = 0.3 + (random(60) / 100.0);
            vy = (vy > 0) ? speed : -speed;
        }
    } else {
        // Fast glide transition to target center coordinates
        currentX += (targetX - currentX) * 0.35;
        currentY += (targetY - currentY) * 0.35;
        
        if (abs(currentX - targetX) < 0.5) currentX = targetX;
        if (abs(currentY - targetY) < 0.5) currentY = targetY;
    }

    // Flicker-free clearing of old frame position
    if (lastRobotX != -1.0) {
        tft.fillRect((int)lastRobotX - 37, (int)lastRobotY - 37, 74, 74, ILI9341_BLACK);
    }

    // Draw the new design robot in the updated coordinates
    drawRobotNew((int)currentX, (int)currentY, currentEyeState, isBlinking);

    // Save cache state for the next frame
    lastRobotX = currentX;
    lastRobotY = currentY;
    lastBlinking = isBlinking;
    lastDrawnEyeStateWasMusic = isMusicMode;
    strncpy(lastDrawnEyeState, currentEyeState, sizeof(lastDrawnEyeState) - 1);
    lastDrawnEyeState[sizeof(lastDrawnEyeState) - 1] = '\0';
}
