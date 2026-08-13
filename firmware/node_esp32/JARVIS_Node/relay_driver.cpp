#include "relay_driver.h"
#include <Arduino.h>

bool relayStates[2] = {false, false};
int relayPins[2] = {RELAY_1_PIN, RELAY_2_PIN};

// Helper to resolve physical GPIO pin voltage logic
uint8_t getPhysicalPinLevel(bool active) {
    if (RELAY_ACTIVE_LOW) {
        return active ? LOW : HIGH;
    }
    return active ? HIGH : LOW;
}

void initRelays() {
    Serial.println("[RELAY] Initializing relays with BOOT-SAFE checks...");
    
    for (int i = 0; i < 2; i++) {
        // 1. Force write safe (OFF) level BEFORE setting pin as output!
        // This prevents relay clicking/pulsing during boot sequence.
        digitalWrite(relayPins[i], getPhysicalPinLevel(false));
        pinMode(relayPins[i], OUTPUT);
        
        relayStates[i] = false;
        Serial.printf("[RELAY] Channel %d initialized OFF on GPIO %d\n", i, relayPins[i]);
    }
}

void setRelayState(int channel, bool state) {
    if (channel < 0 || channel >= 2) return;
    
    digitalWrite(relayPins[channel], getPhysicalPinLevel(state));
    relayStates[channel] = state;
    Serial.printf("[RELAY] Channel %d set to %s\n", channel, state ? "ON" : "OFF");
}

bool getRelayState(int channel) {
    if (channel < 0 || channel >= 2) return false;
    return relayStates[channel];
}
