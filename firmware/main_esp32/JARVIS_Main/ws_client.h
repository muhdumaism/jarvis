#ifndef WS_CLIENT_H
#define WS_CLIENT_H

#include "config.h"
#include <WebSocketsClient.h>
#include <ArduinoJson.h>

extern WebSocketsClient webSocket;

void initWebSocket();
void loopWebSocket();
bool sendWSMessage(const String& message);
bool isWSConnected();

#endif // WS_CLIENT_H
