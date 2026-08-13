#ifndef TFT_DRIVER_H
#define TFT_DRIVER_H

#include "config.h"
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>
#include <SPI.h>

extern Adafruit_ILI9341 tft;

void initTFT();
void clearDisplay();
void drawStatusOverlay(const char* status, uint16_t color);

#endif // TFT_DRIVER_H
