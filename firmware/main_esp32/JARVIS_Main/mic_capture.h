#ifndef MIC_CAPTURE_H
#define MIC_CAPTURE_H

#include "config.h"
#include <driver/i2s.h>

void initMicrophone();
bool readMicrophone(uint8_t* buffer, size_t size, size_t* bytesRead);

#endif // MIC_CAPTURE_H
