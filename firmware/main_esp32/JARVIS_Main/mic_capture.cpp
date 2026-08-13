#include "mic_capture.h"
#include <Arduino.h>

void initMicrophone() {
    Serial.println("[MIC] Initializing digital INMP441 microphone...");

    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate = AUDIO_SAMPLING_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = DMA_BUF_COUNT,
        .dma_buf_len = DMA_BUF_LEN,
        .use_apll = false,
        .tx_desc_auto_clear = false,
        .fixed_mclk = 0
    };

    i2s_pin_config_t pin_config = {
        .bck_io_num = MIC_BCLK,
        .ws_io_num = MIC_WS,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num = MIC_DATA
    };

    // Install driver on I2S0 channel
    esp_err_t err = i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
    if (err != ESP_OK) {
        Serial.printf("[MIC] Failed to install I2S driver: %d\n", err);
        return;
    }

    err = i2s_set_pin(I2S_NUM_0, &pin_config);
    if (err != ESP_OK) {
        Serial.printf("[MIC] Failed to set I2S pins: %d\n", err);
        return;
    }

    Serial.println("[MIC] I2S Microphone configured successfully.");
}

bool readMicrophone(uint8_t* buffer, size_t size, size_t* bytesRead) {
    esp_err_t err = i2s_read(I2S_NUM_0, buffer, size, bytesRead, portMAX_DELAY);
    return (err == ESP_OK);
}
