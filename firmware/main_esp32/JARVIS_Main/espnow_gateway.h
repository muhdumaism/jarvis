#ifndef ESPNOW_GATEWAY_H
#define ESPNOW_GATEWAY_H

#include "config.h"
#include "protocol.h"
#include <esp_now.h>
#include <WiFi.h>

void initESPNOWGateway();
void routeDeviceCommand(const char* nodeId, const char* deviceId, int channel, const char* action, const char* messageId);

#endif // ESPNOW_GATEWAY_H
