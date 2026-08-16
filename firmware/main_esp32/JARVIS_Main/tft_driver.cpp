#include "tft_driver.h"

// Instantiate Adafruit ILI9341 driver using custom hardware HSPI
SPIClass hspi(HSPI);
Adafruit_ILI9341 tft = Adafruit_ILI9341(&hspi, TFT_DC, TFT_CS, TFT_RST);

void initTFT() {
    Serial.println("[TFT] Initializing SPI display...");
    
    // Hardware reset the TFT controller to guarantee initialization
    pinMode(TFT_RST, OUTPUT);
    digitalWrite(TFT_RST, HIGH);
    delay(50);
    digitalWrite(TFT_RST, LOW);
    delay(50);
    digitalWrite(TFT_RST, HIGH);
    delay(50);
    
    // Explicit SPI pins configuration on HSPI
    // Pass -1 to ss_pin to let Adafruit library manually control CS pin 15
    hspi.begin(TFT_SCLK, -1, TFT_MOSI, -1);  // MISO=-1 (not connected, GPIO 12 is a strapping pin)
    
    tft.begin(40000000); // 40MHz SPI speed for 60 FPS buttery smooth animations
    tft.setRotation(TFT_ROTATION);
    tft.fillScreen(ILI9341_BLACK);

    // Setup backlight pin
    pinMode(TFT_BL, OUTPUT);
    digitalWrite(TFT_BL, HIGH); // Fully turned on
    
    Serial.println("[TFT] Display initialized successfully.");
}

void clearDisplay() {
    tft.fillScreen(ILI9341_BLACK);
}

void drawStatusOverlay(const char* status, uint16_t color) {
    // Render text updates directly without full frame refreshes (partial updates)
    tft.fillRect(0, TFT_HEIGHT - 30, TFT_WIDTH, 30, ILI9341_BLACK);
    tft.setCursor(10, TFT_HEIGHT - 22);
    tft.setTextColor(color);
    tft.setTextSize(1);
    tft.print(status);
}
