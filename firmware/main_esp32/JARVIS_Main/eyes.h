#ifndef EYES_H
#define EYES_H

#include <Arduino.h>
#include "tft_driver.h"

// Define eye coordinates
struct Eye {
    int x;
    int y;
    int r;       // Radius
    int targetX;
    int targetY;
    int currentX;
    int currentY;
};

void initEyes();
void updateEyes(const char* state);
void drawEyes();

#endif // EYES_H
