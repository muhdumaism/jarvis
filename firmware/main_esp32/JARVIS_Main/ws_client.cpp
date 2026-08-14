#include "ws_client.h"
#include "ui_manager.h"
#include "audio_output.h"
#include "espnow_gateway.h"
#include <mbedtls/base64.h>
#include <WiFi.h>

WebSocketsClient webSocket;
bool wsConnected = false;

// Base64 decode helper using mbedtls
size_t decodeBase64(const char* input, uint8_t* output, size_t maxLen) {
    size_t outLen = 0;
    int ret = mbedtls_base64_decode(output, maxLen, &outLen, (const unsigned char*)input, strlen(input));
    if (ret != 0) {
        Serial.printf("[WS] Base64 decode error: %d\n", ret);
        return 0;
    }
    return outLen;
}

void handleWebSocketMessage(WStype_t type, uint8_t * payload, size_t length) {
    switch(type) {
        case WStype_DISCONNECTED:
            wsConnected = false;
            setWifiConnected(false);
            setSystemState("BACKEND_DISCONNECTED");
            Serial.println("[WS] Disconnected from server.");
            break;
            
        case WStype_CONNECTED:
            wsConnected = true;
            setWifiConnected(true);
            Serial.println("[WS] Connected! Sending Auth handshake...");
            
            // Send AUTH message
            {
                StaticJsonDocument<256> doc;
                doc["type"] = "AUTH";
                doc["token"] = API_KEY;
                doc["client_type"] = "esp32_main";
                doc["client_id"] = CLIENT_ID;
                doc["firmware_version"] = "1.0.0";
                doc["wifi_channel"] = WiFi.channel();
                
                String authMsg;
                serializeJson(doc, authMsg);
                webSocket.sendTXT(authMsg);
            }
            break;
            
        case WStype_TEXT:
            {
                StaticJsonDocument<1024> doc;
                DeserializationError error = deserializeJson(doc, payload, length);
                if (error) {
                    Serial.printf("[WS] JSON Parse error: %s\n", error.c_str());
                    return;
                }
                
                const char* msgType = doc["type"];
                if (!msgType) return;
                
                if (strcmp(msgType, "AUTH_RESPONSE") == 0) {
                    bool success = doc["success"];
                    Serial.printf("[WS] Auth result: %s\n", success ? "SUCCESS" : "FAILED");
                }
                else if (strcmp(msgType, "DEVICE_COMMAND") == 0) {
                    const char* deviceId = doc["device_id"];
                    const char* action = doc["action"];
                    const char* nodeId = doc["node_id"];
                    int channel = doc["channel"];
                    const char* msgId = doc["message_id"];
                    
                    Serial.printf("[WS] Command: %s %s on node %s CH %d\n", action, deviceId, nodeId, channel);
                    
                    if (strcmp(nodeId, "gateway_main") == 0) {
                        Serial.printf("[WS] Executing local command on Main Gateway: %s on CH %d\n", action, channel);
                        
                        // Main gateway local GPIO mapping: Channel 0 -> GPIO 22, Channel 1 -> GPIO 23
                        int pin = (channel == 0) ? 22 : 23;
                        pinMode(pin, OUTPUT);
                        
                        bool targetState = false;
                        if (strcmp(action, "on") == 0) {
                            targetState = true;
                        } else if (strcmp(action, "off") == 0) {
                            targetState = false;
                        } else {
                            // Toggle state
                            targetState = (digitalRead(pin) == LOW);
                        }
                        digitalWrite(pin, targetState ? HIGH : LOW);
                        
                        // Send state confirmation back to server over WebSocket
                        StaticJsonDocument<256> respDoc;
                        respDoc["type"] = "DEVICE_STATE_CHANGED";
                        respDoc["device_id"] = deviceId;
                        respDoc["state"] = targetState ? "on" : "off";
                        respDoc["confirmed"] = true;
                        if (msgId) {
                            respDoc["message_id"] = msgId;
                        }
                        
                        String json;
                        serializeJson(respDoc, json);
                        sendWSMessage(json);
                    } else {
                        // Route to ESP-NOW gateway
                        routeDeviceCommand(nodeId, deviceId, channel, action, msgId);
                    }
                }
                else if (strcmp(msgType, "TTS_START") == 0) {
                    Serial.println("[WS] TTS Audio playing started.");
                    setAudioOutputEnabled(true);
                    setSystemState("SPEAKING");
                }
                else if (strcmp(msgType, "TTS_AUDIO") == 0) {
                    const char* audioB64 = doc["audio"];
                    if (audioB64) {
                        static uint8_t pcmBuffer[8192];
                        size_t decodedBytes = decodeBase64(audioB64, pcmBuffer, sizeof(pcmBuffer));
                        if (decodedBytes > 0) {
                            size_t written = 0;
                            writeAudioOutput(pcmBuffer, decodedBytes, &written);
                        }
                    }
                }
                else if (strcmp(msgType, "TTS_END") == 0) {
                    Serial.println("[WS] TTS Audio playing completed.");
                    setAudioOutputEnabled(false);
                    setSystemState("IDLE");
                }
                else if (strcmp(msgType, "MUSIC_STATE") == 0) {
                    bool isPlaying = doc["is_playing"];
                    JsonObject track = doc["track"];
                    if (!track.isNull()) {
                        setTrackInfo(
                            track["title"] | "",
                            track["artist"] | "",
                            track["position_ms"] | 0,
                            track["duration_ms"] | 0
                        );
                        if (isPlaying) {
                            setSystemState("SPOTIFY_PLAYING");
                        } else {
                            setTrackInfo("", "", 0, 0);
                            setSystemState("IDLE");
                        }
                    } else {
                        setTrackInfo("", "", 0, 0);
                        setSystemState("IDLE");
                    }
                }
                else if (strcmp(msgType, "speaker_state") == 0) {
                    bool connected = doc["connected"];
                    setSpeakerConnected(connected);
                    if (!connected) {
                        setSystemState("SPEAKER_DISCONNECTED");
                    } else {
                        setSystemState("IDLE");
                    }
                }
                else if (strcmp(msgType, "VOICE_LISTENING") == 0) {
                    setSystemState("LISTENING");
                }
                else if (strcmp(msgType, "VOICE_THINKING") == 0) {
                    setSystemState("THINKING");
                }
                else if (strcmp(msgType, "VOICE_TRANSCRIBED") == 0) {
                    setLastUserQuery(doc["message"] | "");
                }
                else if (strcmp(msgType, "ASSISTANT_RESPONSE") == 0) {
                    setLastJarvisReply(doc["message"] | "");
                    setSystemState("IDLE");
                }
                else if (strcmp(msgType, "DEVICE_STATE_CHANGED") == 0 || strcmp(msgType, "DEVICE_COMMAND") == 0) {
                    updateTFTDeviceState(doc["device_id"] | "", doc["state"] | "");
                }
            }
            break;
            
        case WStype_BIN:
            // Bin messages not used
            break;
        default:
            break;
    }
}

void initWebSocket() {
    webSocket.begin(SERVER_HOST, SERVER_PORT, WS_PATH);
    webSocket.onEvent(handleWebSocketMessage);
    webSocket.setReconnectInterval(5000); // 5s reconnect period
    webSocket.enableHeartbeat(15000, 3000, 2); // Ping every 15s, expect pong within 3s
}

void loopWebSocket() {
    webSocket.loop();
}

bool sendWSMessage(const String& message) {
    if (wsConnected) {
        String temp = message;
        return webSocket.sendTXT(temp);
    }
    return false;
}

bool isWSConnected() {
    return wsConnected;
}
