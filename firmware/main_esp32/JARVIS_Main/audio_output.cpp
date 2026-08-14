#include "audio_output.h"
#include <Arduino.h>

void initAudioOutput() {
    Serial.println("[AUDIO] Initializing I2S audio amplifier output...");

    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
        .sample_rate = AUDIO_PLAYBACK_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = DMA_BUF_COUNT,
        .dma_buf_len = DMA_BUF_LEN,
        .use_apll = false,
        .tx_desc_auto_clear = true, // Auto clear descriptor to prevent clicking sounds on stop
        .fixed_mclk = 0
    };

    i2s_pin_config_t pin_config = {
        .bck_io_num = AUDIO_BCLK,
        .ws_io_num = AUDIO_WS,
        .data_out_num = AUDIO_DOUT,
        .data_in_num = I2S_PIN_NO_CHANGE,
        .mck_io_num = I2S_PIN_NO_CHANGE
    };

    // Install driver on I2S1 channel
    esp_err_t err = i2s_driver_install(I2S_NUM_1, &i2s_config, 0, NULL);
    if (err != ESP_OK) {
        Serial.printf("[AUDIO] Failed to install I2S driver: %d\n", err);
        return;
    }

    err = i2s_set_pin(I2S_NUM_1, &pin_config);
    if (err != ESP_OK) {
        Serial.printf("[AUDIO] Failed to set I2S pins: %d\n", err);
        return;
    }

    // Set SD pin as output and turn off (enable is active HIGH)
    pinMode(AUDIO_SD, OUTPUT);
    setAudioOutputEnabled(false);

    Serial.println("[AUDIO] Audio output configured successfully.");
}

void setAudioOutputEnabled(bool enabled) {
    digitalWrite(AUDIO_SD, enabled ? HIGH : LOW);
    if (enabled) {
        i2s_zero_dma_buffer(I2S_NUM_1);
    }
}

bool writeAudioOutput(const uint8_t* buffer, size_t size, size_t* bytesWritten) {
    esp_err_t err = i2s_write(I2S_NUM_1, buffer, size, bytesWritten, portMAX_DELAY);
    return (err == ESP_OK);
}
