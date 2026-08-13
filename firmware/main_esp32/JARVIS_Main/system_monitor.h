#ifndef SYSTEM_MONITOR_H
#define SYSTEM_MONITOR_H

#include <Arduino.h>
#include <esp_system.h>
#include <esp_task_wdt.h>

void initSystemMonitor();
void checkWatchdog();
void feedWatchdog();
void printSystemStats();

#endif // SYSTEM_MONITOR_H
