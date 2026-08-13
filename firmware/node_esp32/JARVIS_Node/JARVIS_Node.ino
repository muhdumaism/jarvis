/**
 * JARVIS Secondary Relay Node Firmware
 * 
 * Implements ESP-NOW receiver client on ESP32-S3.
 * Automatically registers coordinator gateway MAC and reports heartbeats.
 */

#include "config.h"
#include "protocol.h"
#include "relay_driver.h"
#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>

// Coordinator Gateway MAC cache
uint8_t gatewayMac[6] = {0, 0, 0, 0, 0, 0};
uint8_t broadcastMac[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
bool hasGateway = false;
unsigned long lastHeartbeat = 0;

void registerGatewayAsPeer(const uint8_t* mac) {
    if (esp_now_is_peer_exist(mac)) return;

    esp_now_peer_info_t peerInfo = {};
    memcpy(peerInfo.peer_addr, mac, 6);
    peerInfo.channel = ESP_NOW_CHANNEL;
    peerInfo.encrypt = false;
    
    esp_err_t err = esp_now_add_peer(&peerInfo);
    if (err == ESP_OK) {
        memcpy(gatewayMac, mac, 6);
        hasGateway = true;
        Serial.printf("[ESPNOW] Registered coordinator gateway MAC: %02X:%02X:%02X:%02X:%02X:%02X\n",
                      mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    } else {
        Serial.printf("[ESPNOW] Peer registration failed: %d\n", err);
    }
}

#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
void OnDataSent(const wifi_tx_info_t *tx_info, esp_now_send_status_t status) {
#else
void OnDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
#endif
    // Log send status
    Serial.printf("[ESPNOW] Send report: %s\n", status == ESP_NOW_SEND_SUCCESS ? "ACK OK" : "ACK FAILED");
}

#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
void OnDataRecv(const esp_now_recv_info_t *recv_info, const uint8_t *incomingData, int len) {
    const uint8_t* mac = recv_info->src_addr;
#else
void OnDataRecv(const uint8_t * mac, const uint8_t *incomingData, int len) {
#endif
    if (len < sizeof(JarvisPacket)) return;

    JarvisPacket packet;
    memcpy(&packet, incomingData, sizeof(JarvisPacket));

    if (packet.version != 1) return;

    // Dynamically register gateway on first packet
    if (!hasGateway) {
        registerGatewayAsPeer(mac);
    }

    if (packet.type == MSG_DEVICE_COMMAND) {
        DeviceCommandPayload cmd;
        memcpy(&cmd, packet.payload, sizeof(DeviceCommandPayload));

        Serial.printf("[CMD] Received command for %s: CH %d, Action %d\n", cmd.device_id, cmd.channel, cmd.action);

        // Perform relay command
        bool targetState = false;
        if (cmd.action == 1) {
            targetState = true;
        } else if (cmd.action == 0) {
            targetState = false;
        } else {
            // TOGGLE
            targetState = !getRelayState(cmd.channel);
        }

        setRelayState(cmd.channel, targetState);

        // Send confirmation packet back to gateway
        JarvisPacket response;
        response.version = 1;
        response.type = MSG_DEVICE_ACK;
        memcpy(response.source, WiFi.macAddress().c_str(), 6);
        memcpy(response.destination, gatewayMac, 6);
        response.message_id = packet.message_id; // Keep message_id for correlation tracking
        response.payload_len = sizeof(DeviceStatePayload);

        DeviceStatePayload statePayload;
        strncpy(statePayload.device_id, cmd.device_id, sizeof(statePayload.device_id) - 1);
        statePayload.device_id[sizeof(statePayload.device_id) - 1] = '\0';
        statePayload.channel = cmd.channel;
        statePayload.state = targetState ? 1 : 0;
        statePayload.confirmed = 1; // Mark as confirmed relay state

        memcpy(response.payload, &statePayload, sizeof(DeviceStatePayload));

        esp_err_t res = esp_now_send(gatewayMac, (uint8_t *) &response, sizeof(JarvisPacket));
        if (res != ESP_OK) {
             Serial.printf("[ESPNOW] Confirmed state send error: %d\n", res);
        }
    }
}

void sendHeartbeat() {
    uint8_t* targetMac = hasGateway ? gatewayMac : broadcastMac;

    JarvisPacket packet;
    packet.version = 1;
    packet.type = MSG_HEARTBEAT;
    
    // Read local MAC address bytes
    uint8_t localMac[6];
    WiFi.macAddress(localMac);
    memcpy(packet.source, localMac, 6);
    memcpy(packet.destination, targetMac, 6);
    packet.message_id = 0;
    packet.payload_len = sizeof(HeartbeatPayload);

    HeartbeatPayload payload;
    strncpy(payload.node_id, NODE_ID, sizeof(payload.node_id) - 1);
    payload.node_id[sizeof(payload.node_id) - 1] = '\0';
    payload.uptime = millis() / 1000;
    payload.free_heap = esp_get_free_heap_size();
    payload.device_count = 2;

    // Pack relay states into bitmask
    uint8_t states = 0;
    if (getRelayState(0)) states |= (1 << 0);
    if (getRelayState(1)) states |= (1 << 1);
    payload.device_states = states;

    memcpy(packet.payload, &payload, sizeof(HeartbeatPayload));

    esp_err_t res = esp_now_send(targetMac, (uint8_t *) &packet, sizeof(JarvisPacket));
    if (res != ESP_OK) {
         Serial.printf("[ESPNOW] Heartbeat send error: %d\n", res);
    } else {
         Serial.printf("[ESPNOW] Heartbeat sent to %s\n", hasGateway ? "gateway" : "broadcast");
    }
}

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("[BOOT] Starting JARVIS OS relay node...");

    initRelays();

    // ESP32-S3 must be in STA mode
    WiFi.mode(WIFI_STA);
    WiFi.disconnect();

    // Reduce Wi-Fi transmit power to keep the chip running cool
    WiFi.setTxPower(WIFI_POWER_11dBm);

    // Force the ESP32 Wi-Fi interface to the configured ESP-NOW channel
    esp_wifi_set_promiscuous(true);
    esp_wifi_set_channel(ESP_NOW_CHANNEL, WIFI_SECOND_CHAN_NONE);
    esp_wifi_set_promiscuous(false);

    if (esp_now_init() != ESP_OK) {
        Serial.println("[ESPNOW] Error initializing ESP-NOW");
        return;
    }

    esp_now_register_send_cb(OnDataSent);
    esp_now_register_recv_cb(OnDataRecv);

    // Register broadcast peer so we can pair dynamically
    esp_now_peer_info_t peerInfo = {};
    memcpy(peerInfo.peer_addr, broadcastMac, 6);
    peerInfo.channel = ESP_NOW_CHANNEL;
    peerInfo.encrypt = false;
    if (esp_now_add_peer(&peerInfo) != ESP_OK) {
        Serial.println("[ESPNOW] Failed to add broadcast peer");
    }

    Serial.println("[ESPNOW] ESP-NOW initialized on Node side. Waiting for gateway connection...");
}

void loop() {
    // Send periodic heartbeats (broadcast every 5s if un-paired, unicast every HEARTBEAT_INTERVAL if paired)
    unsigned long interval = hasGateway ? HEARTBEAT_INTERVAL : 5000;
    if (millis() - lastHeartbeat > interval) {
        sendHeartbeat();
        lastHeartbeat = millis();
    }
    delay(500);
}
