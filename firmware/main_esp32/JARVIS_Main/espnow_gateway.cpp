#include "espnow_gateway.h"
#include "ws_client.h"
#include <map>

// Dynamic node routing cache: Node ID string -> 6-byte MAC Address
std::map<String, std::vector<uint8_t>> nodeRouteCache;

// Transaction tracker: maps transaction message_id to websocket correlation UUID string
std::map<uint16_t, String> correlationCache;
uint16_t currentMsgId = 0;

#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
void OnDataSent(const wifi_tx_info_t *tx_info, esp_now_send_status_t status) {
    const uint8_t* mac_addr = tx_info->des_addr;
#else
void OnDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
#endif
    // Log transmission status
    Serial.printf("[ESPNOW] Packet sent to %02X:%02X:%02X:%02X:%02X:%02X - Status: %s\n",
                  mac_addr[0], mac_addr[1], mac_addr[2], mac_addr[3], mac_addr[4], mac_addr[5],
                  status == ESP_NOW_SEND_SUCCESS ? "DELIVERED" : "FAILED");
}

#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
void OnDataRecv(const esp_now_recv_info_t *recv_info, const uint8_t *incomingData, int len) {
    const uint8_t* mac = recv_info->src_addr;
#else
void OnDataRecv(const uint8_t * mac, const uint8_t *incomingData, int len) {
#endif
    if (len < sizeof(JarvisPacket)) {
        Serial.println("[ESPNOW] Received corrupted packet size.");
        return;
    }
    
    JarvisPacket packet;
    memcpy(&packet, incomingData, sizeof(JarvisPacket));
    
    if (packet.version != 1) return;

    if (packet.type == MSG_HEARTBEAT) {
        HeartbeatPayload payload;
        memcpy(&payload, packet.payload, sizeof(HeartbeatPayload));
        
        String nodeIdStr = String(payload.node_id);
        
        // Dynamic cache updates
        if (nodeRouteCache.find(nodeIdStr) == nodeRouteCache.end()) {
            std::vector<uint8_t> macVec(mac, mac + 6);
            nodeRouteCache[nodeIdStr] = macVec;
            Serial.printf("[ESPNOW] Cached route for %s -> %02X:%02X:%02X:%02X:%02X:%02X\n",
                          payload.node_id, mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
        }
        
        // Forward heartbeat to Server via WS
        char macStr[18];
        snprintf(macStr, sizeof(macStr), "%02X:%02X:%02X:%02X:%02X:%02X",
                 mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);

        StaticJsonDocument<256> doc;
        doc["type"] = "NODE_HEARTBEAT";
        doc["node_id"] = payload.node_id;
        doc["uptime"] = payload.uptime;
        doc["free_heap"] = payload.free_heap;
        doc["mac_address"] = macStr;
        doc["chip_type"] = "esp32c3";
        doc["device_count"] = payload.device_count;
        doc["device_states"] = payload.device_states;
        
        String json;
        serializeJson(doc, json);
        sendWSMessage(json);

        // Reply with HEARTBEAT_ACK over ESP-NOW to pair the Node dynamically
        JarvisPacket ack;
        ack.version = 1;
        ack.type = MSG_HEARTBEAT_ACK;
        uint8_t localMac[6];
        WiFi.macAddress(localMac);
        memcpy(ack.source, localMac, 6);
        memcpy(ack.destination, mac, 6);
        ack.payload_len = 0;
        
        if (!esp_now_is_peer_exist(mac)) {
            esp_now_peer_info_t peerInfo = {};
            memcpy(peerInfo.peer_addr, mac, 6);
            peerInfo.channel = WiFi.channel();
            peerInfo.encrypt = false;
            esp_now_add_peer(&peerInfo);
        }
        
        esp_now_send(mac, (uint8_t*)&ack, sizeof(JarvisPacket));
    }
    else if (packet.type == MSG_DEVICE_ACK || packet.type == MSG_DEVICE_STATE) {
        DeviceStatePayload payload;
        memcpy(&payload, packet.payload, sizeof(DeviceStatePayload));
        
        // Find correlation websocket UUID using packet message_id
        String wsUuid = "";
        if (correlationCache.find(packet.message_id) != correlationCache.end()) {
            wsUuid = correlationCache[packet.message_id];
            correlationCache.erase(packet.message_id); // clean cache
        }
        
        // Forward confirmed state to Server via WS
        StaticJsonDocument<256> doc;
        doc["type"] = "DEVICE_STATE_CHANGED";
        doc["device_id"] = payload.device_id;
        doc["state"] = payload.state == 1 ? "on" : "off";
        doc["confirmed"] = payload.confirmed == 1;
        if (wsUuid.length() > 0) {
            doc["message_id"] = wsUuid;
        }
        
        String json;
        serializeJson(doc, json);
        sendWSMessage(json);
        Serial.printf("[ESPNOW] Relayed state: %s is %s\n", payload.device_id, payload.state == 1 ? "ON" : "OFF");
    }
}

void initESPNOWGateway() {
    Serial.println("[ESPNOW] Initializing coordinator gateway...");
    
    // ESP32 must be in STA mode for ESP-NOW
    WiFi.mode(WIFI_AP_STA);
    
    if (esp_now_init() != ESP_OK) {
        Serial.println("[ESPNOW] Error initializing ESP-NOW");
        return;
    }
    
    esp_now_register_send_cb(OnDataSent);
    esp_now_register_recv_cb(OnDataRecv);
    
    Serial.println("[ESPNOW] ESP-NOW gateway initialized.");
}

void routeDeviceCommand(const char* nodeId, const char* deviceId, int channel, const char* action, const char* messageId) {
    String nodeKey = String(nodeId);
    
    if (nodeRouteCache.find(nodeKey) == nodeRouteCache.end()) {
        Serial.printf("[ESPNOW] Route to node %s not in cache yet. Wait for heartbeat.\n", nodeId);
        return;
    }
    
    std::vector<uint8_t>& targetMac = nodeRouteCache[nodeKey];
    
    // Add peer if not already present
    if (!esp_now_is_peer_exist(targetMac.data())) {
        esp_now_peer_info_t peerInfo = {};
        memcpy(peerInfo.peer_addr, targetMac.data(), 6);
        peerInfo.channel = ESP_NOW_CHANNEL;
        peerInfo.encrypt = false;
        esp_err_t err = esp_now_add_peer(&peerInfo);
        if (err != ESP_OK) {
            Serial.printf("[ESPNOW] Add peer error: %d\n", err);
            return;
        }
    }
    
    // Assemble packet
    uint16_t msgId = currentMsgId++;
    
    // Correlation cache mapping
    if (messageId) {
        correlationCache[msgId] = String(messageId);
    }
    
    JarvisPacket packet;
    packet.version = 1;
    packet.type = MSG_DEVICE_COMMAND;
    memcpy(packet.source, WiFi.macAddress().c_str(), 6); // Set source MAC
    memcpy(packet.destination, targetMac.data(), 6);
    packet.message_id = msgId;
    packet.payload_len = sizeof(DeviceCommandPayload);
    
    DeviceCommandPayload payload;
    strncpy(payload.device_id, deviceId, sizeof(payload.device_id) - 1);
    payload.device_id[sizeof(payload.device_id) - 1] = '\0';
    payload.channel = channel;
    
    // Translate action text to byte
    if (strcmp(action, "turn_on") == 0) {
        payload.action = 1;
    } else if (strcmp(action, "turn_off") == 0) {
        payload.action = 0;
    } else {
        payload.action = 2; // TOGGLE
    }
    
    memcpy(packet.payload, &payload, sizeof(DeviceCommandPayload));
    
    esp_err_t result = esp_now_send(targetMac.data(), (uint8_t *) &packet, sizeof(JarvisPacket));
    if (result != ESP_OK) {
         Serial.printf("[ESPNOW] Send error: %d\n", result);
    }
}
