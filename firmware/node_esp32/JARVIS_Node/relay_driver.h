#ifndef RELAY_DRIVER_H
#define RELAY_DRIVER_H

#include "config.h"

void initRelays();
void setRelayState(int channel, bool state);
bool getRelayState(int channel);

#endif // RELAY_DRIVER_H
