/**
 * JARVIS Dashboard Types Definitions
 */

export interface Room {
  id: string;
  name: string;
  description: string;
  icon: string;
  order: number;
  created_at: string;
}

export interface Node {
  id: string;
  name: string;
  room_id: string;
  mac_address?: string;
  chip_type: string;
  firmware_version: string;
  status: 'online' | 'offline' | 'unknown';
  last_seen?: string;
  uptime: number;
  free_heap: number;
  device_count: number;
  config: Record<string, any>;
  created_at: string;
}

export interface Device {
  id: string;
  name: string;
  room_id: string;
  node_id: string;
  type: 'relay' | 'sensor' | 'switch' | 'dimmer';
  channel: number;
  capabilities: string[];
  state: 'on' | 'off' | 'unknown' | string;
  confirmed: boolean;
  last_changed?: string;
  metadata: Record<string, any>;
  online: boolean;
  created_at: string;
}

export interface TrackInfo {
  title: string;
  artist: string;
  album: string;
  album_art_url?: string;
  duration_ms: number;
  position_ms: number;
}

export interface MusicState {
  is_playing: boolean;
  track: TrackInfo | null;
  speaker_connected?: boolean;
  current_output_device?: string;
}

export interface VoiceState {
  status: 'idle' | 'listening' | 'thinking' | 'speaking' | 'success' | 'error';
  last_transcription?: string;
  intent?: string;
  target?: string;
  action?: string;
  error?: string;
  isAlarmRinging?: boolean;
}

export interface SystemStatus {
  server_uptime: number;
  cpu_percent: number;
  ram_percent: number;
  disk_percent: number;
  db_size_mb: number;
  ws_connections: number;
  stt_status: string;
  tts_status: string;
  ai_status: string;
  spotify_status: string;
}

export interface EventLog {
  id: number;
  timestamp: string;
  severity: 'debug' | 'info' | 'warning' | 'error' | 'critical';
  component: string;
  event_type: string;
  message: string;
  message_id?: string;
  payload?: Record<string, any>;
}

export interface Automation {
  id: number;
  name: string;
  description: string;
  enabled: boolean;
  trigger_type: 'time' | 'temperature' | 'device_state' | 'sensor';
  trigger_config: Record<string, any>;
  conditions: Record<string, any>[];
  actions: Record<string, any>[];
  cooldown_seconds: number;
  last_triggered?: string;
  trigger_count: number;
  created_at: string;
  updated_at: string;
}

export interface SceneAction {
  id: number;
  order: number;
  action_type: 'device_control' | 'music_control' | 'delay';
  target?: string;
  action: string;
  parameters: Record<string, any>;
}

export interface Scene {
  id: number;
  name: string;
  description: string;
  icon: string;
  actions: SceneAction[];
  created_at: string;
  updated_at: string;
}

export interface FirmwareVersion {
  id: number;
  version: string;
  chip_type: string;
  target: string;
  filename: string;
  file_size: number;
  sha256: string;
  description: string;
  uploaded_at: string;
}
