#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>
#include <SPI.h>

// ============================================================
// TFT Pin Configuration
// ============================================================
#define TFT_CS              15  // Chip Select
#define TFT_DC              17  // Data/Command
#define TFT_RST             4   // Reset
#define TFT_MOSI            13  // SPI MOSI
#define TFT_MISO            -1  // SPI MISO (Leave disconnected / unused)
#define TFT_SCLK            14  // SPI Clock
#define TFT_BL              27  // Backlight Pin

// Dedicated HSPI Bus Class
SPIClass hspi(HSPI);

// Create the ILI9341 client using the custom HSPI bus
Adafruit_ILI9341 tft = Adafruit_ILI9341(&hspi, TFT_DC, TFT_CS, TFT_RST);

void drawDiagnosticText(const char* message, uint16_t color) {
    tft.setTextColor(color);
    tft.setTextSize(2);
    tft.setCursor(20, 40);
    tft.println("JARVIS SCREEN TEST");
    tft.setCursor(20, 80);
    tft.setTextSize(3);
    tft.println(message);
    tft.setCursor(20, 140);
    tft.setTextSize(1);
    tft.setTextColor(ILI9341_LIGHTGREY);
    tft.println("Checking connections...");
    tft.printf("Pins: SCLK=%d MOSI=%d CS=%d DC=%d\n", TFT_SCLK, TFT_MOSI, TFT_CS, TFT_DC);
}

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("===============================================");
    Serial.println("[TFT TEST] Waking up display controller...");
    Serial.println("===============================================");

    // 1. Backlight pin initialization
    pinMode(TFT_BL, OUTPUT);
    digitalWrite(TFT_BL, HIGH); // Power up backlight
    Serial.println("[TFT TEST] Backlight turned ON (Pin 27 set HIGH)");

    // 2. Clear reset lines to hard reboot display controller
    pinMode(TFT_RST, OUTPUT);
    digitalWrite(TFT_RST, HIGH);
    delay(100);
    digitalWrite(TFT_RST, LOW);
    delay(100);
    digitalWrite(TFT_RST, HIGH);
    delay(100);
    Serial.println("[TFT TEST] Completed hardware reset sequence");

    // 3. Initialize custom HSPI bus (disabling unused MISO line to prevent conflict)
    hspi.begin(TFT_SCLK, -1, TFT_MOSI, -1);
    Serial.println("[TFT TEST] HSPI Bus initialized");

    // 4. Initialize display driver at safe 8MHz frequency (robust for all cables)
    Serial.println("[TFT TEST] Initializing ILI9341 driver...");
    tft.begin(8000000); 
    tft.setRotation(1); // Set landscape layout (320x240)
    Serial.println("[TFT TEST] Initialization completed");
}

void loop() {
    // Phase 1: Clear screen to RED
    Serial.println("[TFT TEST] Cycle: RED");
    tft.fillScreen(ILI9341_RED);
    drawDiagnosticText("RED PHASE", ILI9341_WHITE);
    delay(2000);

    // Phase 2: Clear screen to GREEN
    Serial.println("[TFT TEST] Cycle: GREEN");
    tft.fillScreen(ILI9341_GREEN);
    drawDiagnosticText("GREEN PHASE", ILI9341_BLACK);
    delay(2000);

    // Phase 3: Clear screen to BLUE
    Serial.println("[TFT TEST] Cycle: BLUE");
    tft.fillScreen(ILI9341_BLUE);
    drawDiagnosticText("BLUE PHASE", ILI9341_WHITE);
    delay(2000);

    // Phase 4: Clear screen to BLACK
    Serial.println("[TFT TEST] Cycle: BLACK");
    tft.fillScreen(ILI9341_BLACK);
    drawDiagnosticText("BLACK PHASE", ILI9341_CYAN);
    delay(2000);
}
