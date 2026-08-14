/**
 * JARVIS WebSocket Client Manager
 *
 * Automatically handles reconnection with exponential backoff, auth handshake,
 * and dispatching incoming real-time messages to the state store.
 */

import { getAuthToken } from '../services/api';
import { useJarvisStore } from '../state/store';

let ws: WebSocket | null = null;
let reconnectTimeout: number | null = null;
let reconnectDelay = 1000;
const MAX_RECONNECT_DELAY = 30000;
let isIntentionalDisconnect = false;

export const connectWebSocket = (): void => {
  if (ws && (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN)) {
    return;
  }

  isIntentionalDisconnect = false;
  
  // Detect protocol, host and hostname
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;
  const hostname = window.location.hostname;
  
  // Proxy through Vite's server proxy to support tunnels, secure contexts, and local IPs cleanly
  const wsUrl = `${protocol}//${host}/ws`;

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    reconnectDelay = 1000; // Reset backoff delay
    
    // Perform authentication handshake immediately
    const token = getAuthToken();
    if (token) {
      sendWSMessage({
        type: 'AUTH',
        token,
        client_type: 'dashboard',
        client_id: `dashboard_${Math.random().toString(36).substring(7)}`,
      });
    }
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleIncomingMessage(data);
    } catch (e) {
      console.error('Failed to parse WebSocket message:', e);
    }
  };

  ws.onclose = (event) => {
    if (isIntentionalDisconnect) return;

    ws = null;
    // Exponential backoff reconnect
    reconnectTimeout = window.setTimeout(() => {
      reconnectDelay = Math.min(reconnectDelay * 2, MAX_RECONNECT_DELAY);
      connectWebSocket();
    }, reconnectDelay);
  };

  ws.onerror = (error) => {
    console.error('WebSocket Error:', error);
    ws?.close();
  };
};

export const disconnectWebSocket = (): void => {
  isIntentionalDisconnect = true;
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout);
    reconnectTimeout = null;
  }
  if (ws) {
    ws.close();
    ws = null;
  }
};

export const sendWSMessage = (msg: Record<string, any>): boolean => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(jsonStableStringify(msg));
    return true;
  }
  return false;
};

// Stable serializer
function jsonStableStringify(obj: Record<string, any>): string {
  return JSON.stringify(obj);
}

function handleIncomingMessage(msg: Record<string, any>): void {
  const store = useJarvisStore.getState();
  
  switch (msg.type) {
    case 'AUTH_RESPONSE':
      if (msg.success) {
        store.setSystemConnected(true);
      } else {
        console.error('WebSocket Authentication Failed:', msg.error);
        disconnectWebSocket();
      }
      break;

    case 'HEARTBEAT_ACK':
      // System active
      break;

    case 'DEVICE_STATE_CHANGED':
      store.updateDeviceState(msg.device_id, msg.state, true);
      break;

    case 'DEVICE_STATE_PENDING':
      store.updateDeviceState(msg.device_id, msg.requested_state, false);
      break;

    case 'DEVICE_STATE_FAILED':
      store.updateDeviceState(msg.device_id, 'unknown', false);
      store.addToast(`Device control failed: ${msg.error}`, 'error');
      break;

    case 'NODE_ONLINE':
      store.updateNodeStatus(msg.node_id, 'online');
      break;

    case 'NODE_OFFLINE':
      store.updateNodeStatus(msg.node_id, 'offline');
      break;

    case 'MUSIC_STATE':
      store.setMusicState({
        is_playing: msg.is_playing,
        track: msg.track || null,
        speaker_connected: msg.speaker_connected,
        current_output_device: msg.current_output_device,
      });
      break;

    case 'speaker_state':
      store.setMusicState({
        ...store.music,
        speaker_connected: msg.connected,
      });
      break;

    case 'VOICE_LISTENING':
      store.setVoiceStatus('listening');
      store.setVoiceData({ error: undefined });
      break;

    case 'VOICE_THINKING':
      store.setVoiceStatus('thinking');
      break;

    case 'VOICE_TRANSCRIBED':
      store.setVoiceData({ last_transcription: msg.text });
      break;

    case 'ASSISTANT_INTENT':
      store.setVoiceData({
        intent: msg.intent,
        target: msg.target,
        action: msg.action,
      });
      break;

    case 'ASSISTANT_RESPONSE':
      store.setVoiceStatus(msg.success ? 'success' : 'error');
      break;

    case 'ASSISTANT_ERROR':
      store.setVoiceStatus('error');
      store.setVoiceData({ error: msg.error });
      store.addToast(msg.error, 'error');
      break;

    case 'SYSTEM_STATUS':
      store.setSystemStats({
        server_uptime: msg.server_uptime,
        cpu_percent: msg.cpu_percent,
        ram_percent: msg.ram_percent,
        disk_percent: msg.disk_percent,
        db_size_mb: msg.db_size_mb,
        ws_connections: msg.ws_connections,
        stt_status: msg.stt_status,
        tts_status: msg.tts_status,
        ai_status: msg.ai_status,
        spotify_status: msg.spotify_status,
      });
      break;

    case 'NOTIFICATION':
      store.addToast(msg.message, msg.level as any);
      break;

    case 'ERROR':
      store.addToast(msg.message, 'error');
      break;

    default:
      console.warn('Unhandled WebSocket message type:', msg.type);
  }
}
