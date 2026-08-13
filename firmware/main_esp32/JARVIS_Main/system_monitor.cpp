#include "system_monitor.h"

void initSystemMonitor() {
    Serial.println("[SYSTEM] Task Watchdog monitor bypassed to prevent task-conflict panics.");
}

void checkWatchdog() {
    // No-op
}

void feedWatchdog() {
    // No-op
}

void printSystemStats() {
    uint32_t freeHeap = esp_get_free_heap_size();
    uint32_t minFreeHeap = esp_get_minimum_free_heap_size();
    uint32_t maxAlloc = heap_caps_get_largest_free_block(MALLOC_CAP_8BIT);

    Serial.printf("[SYSTEM] Uptime: %lu s | Free Heap: %u bytes (Min: %u) | Max Block: %u bytes\n",
                  millis() / 1000, freeHeap, minFreeHeap, maxAlloc);
}
