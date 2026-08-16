/**
 * JARVIS TFT Pin Diagnostic Test (Separate Project)
 * 
 * Tests with DC moved to GPIO 2 (built-in LED pin)
 * to rule out a dead GPIO 17.
 * 
 * WIRING CHANGE NEEDED: Move the DC wire from GPIO 17 to GPIO 2
 */

#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>

// Same pins as JARVIS config, but DC moved to GPIO 2
#define TFT_CS    15
#define TFT_DC     2   // <-- CHANGED: Move wire from 17 to 2
#define TFT_RST    4
#define TFT_MOSI  13
#define TFT_SCLK  14
#define TFT_BL    27

SPIClass hspi(HSPI);
Adafruit_ILI9341 tft = Adafruit_ILI9341(&hspi, TFT_DC, TFT_CS, TFT_RST);

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("=== DC PIN DIAGNOSTIC TEST ===");

    pinMode(TFT_RST, OUTPUT);
    digitalWrite(TFT_RST, HIGH); delay(50);
    digitalWrite(TFT_RST, LOW);  delay(50);
    digitalWrite(TFT_RST, HIGH); delay(50);

    hspi.begin(TFT_SCLK, -1, TFT_MOSI, -1);
    tft.begin(8000000);
    tft.setRotation(1);

    pinMode(TFT_BL, OUTPUT);
    digitalWrite(TFT_BL, HIGH);

    Serial.println("[TEST] Init done. If you see RED, your old GPIO 17 is dead.");
    Serial.println("[TEST] If still WHITE, the display itself is dead.");
    
    tft.fillScreen(ILI9341_RED);
    delay(2000);
    tft.fillScreen(ILI9341_GREEN);
    delay(2000);
    tft.fillScreen(ILI9341_BLUE);
    delay(2000);
    tft.fillScreen(ILI9341_BLACK);

    tft.setCursor(40, 100);
    tft.setTextColor(ILI9341_CYAN);
    tft.setTextSize(3);
    tft.print("DC PIN OK!");
}

void loop() {
    delay(1000);
}
