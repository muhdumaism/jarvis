#ifndef AUDIO_OUTPUT_H
#define AUDIO_OUTPUT_H

#include "config.h"
#include <driver/i2s.h>

void initAudioOutput();
bool writeAudioOutput(const uint8_t* buffer, size_t size, size_t* bytesWritten);
void setAudioOutputEnabled(bool enabled);

#endif // AUDIO_OUTPUT_H
