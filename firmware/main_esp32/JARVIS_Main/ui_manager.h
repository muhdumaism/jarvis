#ifndef UI_MANAGER_H
#define UI_MANAGER_H

#include <Arduino.h>

void initUI();
void updateUI();
void setSystemState(const char* newState);
void setSpeakerConnected(bool connected);
void setTrackInfo(const char* title, const char* artist, int positionMs, int durationMs);
void setWifiConnected(bool connected);

// Room Assistant telemetry inputs
void setLastUserQuery(const char* query);
void setLastJarvisReply(const char* reply);
void updateTFTDeviceState(const char* deviceId, const char* state);
void invalidateUICaches();

#endif // UI_MANAGER_H
