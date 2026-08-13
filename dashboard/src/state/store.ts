/**
 * JARVIS Dashboard State Store (Zustand)
 */

import { create } from 'zustand';
import type { Device, Node, Room, MusicState, VoiceState, SystemStatus, Automation, Scene, FirmwareVersion, EventLog } from '../types';
import { api } from '../services/api';

interface Toast {
  id: string;
  message: string;
  level: 'info' | 'success' | 'warning' | 'error';
  timestamp: number;
}

interface JarvisStore {
  // State
  rooms: Room[];
  nodes: Node[];
  devices: Device[];
  music: MusicState;
  voice: VoiceState;
  systemConnected: boolean;
  systemStats: SystemStatus | null;
  automations: Automation[];
  scenes: Scene[];
  firmwares: FirmwareVersion[];
  events: EventLog[];
  toasts: Toast[];

  // Setters / Handlers
  setSystemConnected: (connected: boolean) => void;
  setSystemStats: (stats: SystemStatus) => void;
  setMusicState: (music: MusicState) => void;
  setVoiceStatus: (status: VoiceState['status']) => void;
  setVoiceData: (data: Partial<VoiceState>) => void;
  addToast: (message: string, level?: Toast['level']) => void;
  removeToast: (id: string) => void;

  // Real-time State Updates (WS)
  updateDeviceState: (deviceId: string, state: string, confirmed: boolean) => void;
  updateNodeStatus: (nodeId: string, status: Node['status']) => void;

  // Actions (REST API fetches)
  fetchRooms: () => Promise<void>;
  fetchNodes: () => Promise<void>;
  fetchDevices: () => Promise<void>;
  fetchMusicState: () => Promise<void>;
  fetchAutomations: () => Promise<void>;
  fetchScenes: () => Promise<void>;
  fetchFirmwares: () => Promise<void>;
  fetchEvents: (component?: string, severity?: string, messageId?: string, limit?: number) => Promise<void>;

  // Device / Music Controls
  controlDevice: (deviceId: string, action: string) => Promise<void>;
  controlMusic: (action: string, query?: string, value?: number) => Promise<void>;
  activateScene: (sceneId: number) => Promise<void>;
  testAutomation: (autoId: number) => Promise<void>;
}

export const useJarvisStore = create<JarvisStore>((set, get) => ({
  // Initial State
  rooms: [],
  nodes: [],
  devices: [],
  music: { is_playing: false, track: null },
  voice: { status: 'idle' },
  systemConnected: false,
  systemStats: null,
  automations: [],
  scenes: [],
  firmwares: [],
  events: [],
  toasts: [],

  // Setters
  setSystemConnected: (connected) => set({ systemConnected: connected }),
  setSystemStats: (stats) => set({ systemStats: stats }),
  setMusicState: (music) => set({ music }),
  setVoiceStatus: (status) => set((state) => ({ voice: { ...state.voice, status } })),
  setVoiceData: (data) => set((state) => ({ voice: { ...state.voice, ...data } })),
  
  addToast: (message, level = 'info') => {
    const id = Math.random().toString(36).substring(7);
    set((state) => ({
      toasts: [...state.toasts, { id, message, level, timestamp: Date.now() }],
    }));
    // Auto-remove after 4 seconds
    setTimeout(() => {
      get().removeToast(id);
    }, 4000);
  },
  
  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),

  // Real-time Updates (WS)
  updateDeviceState: (deviceId, state, confirmed) =>
    set((store) => ({
      devices: store.devices.map((d) =>
        d.id === deviceId ? { ...d, state, confirmed, last_changed: new Date().toISOString() } : d
      ),
    })),

  updateNodeStatus: (nodeId, status) => {
    const exists = get().nodes.some((n) => n.id === nodeId);
    if (!exists && status === 'online') {
      get().fetchNodes();
      return;
    }
    set((store) => ({
      nodes: store.nodes.map((n) => (n.id === nodeId ? { ...n, status } : n)),
      devices: store.devices.map((d) => (d.node_id === nodeId ? { ...d, online: status === 'online' } : d)),
    }));
  },

  // REST API Actions
  fetchRooms: async () => {
    try {
      const rooms = await api.rooms.list();
      set({ rooms });
    } catch (e: any) {
      get().addToast(`Failed to load rooms: ${e.message}`, 'error');
    }
  },

  fetchNodes: async () => {
    try {
      const nodes = await api.nodes.list();
      set({ nodes });
    } catch (e: any) {
      get().addToast(`Failed to load nodes: ${e.message}`, 'error');
    }
  },

  fetchDevices: async () => {
    try {
      const devices = await api.devices.list();
      set({ devices });
    } catch (e: any) {
      get().addToast(`Failed to load devices: ${e.message}`, 'error');
    }
  },

  fetchMusicState: async () => {
    try {
      const music = await api.music.getState();
      set({ music });
    } catch (e: any) {
      console.warn('Failed to load music state:', e.message);
    }
  },

  fetchAutomations: async () => {
    try {
      const automations = await api.automations.list();
      set({ automations });
    } catch (e: any) {
      get().addToast(`Failed to load automations: ${e.message}`, 'error');
    }
  },

  fetchScenes: async () => {
    try {
      const scenes = await api.scenes.list();
      set({ scenes });
    } catch (e: any) {
      get().addToast(`Failed to load scenes: ${e.message}`, 'error');
    }
  },

  fetchFirmwares: async () => {
    try {
      const firmwares = await api.firmware.list();
      set({ firmwares });
    } catch (e: any) {
      get().addToast(`Failed to load firmwares: ${e.message}`, 'error');
    }
  },

  fetchEvents: async (component, severity, messageId, limit) => {
    try {
      const events = await api.system.events(component, severity, messageId, limit);
      set({ events });
    } catch (e: any) {
      get().addToast(`Failed to load events log: ${e.message}`, 'error');
    }
  },

  // Device / Music Controls
  controlDevice: async (deviceId, action) => {
    // Optimistic pending update
    const targetState = action === 'turn_on' ? 'on' : action === 'turn_off' ? 'off' : 'toggled';
    get().updateDeviceState(deviceId, `pending_${targetState}`, false);

    try {
      await api.devices.control(deviceId, action);
    } catch (e: any) {
      // Revert state
      get().updateDeviceState(deviceId, 'unknown', false);
      get().addToast(`Device command failed: ${e.message}`, 'error');
    }
  },

  controlMusic: async (action, query, value) => {
    try {
      await api.music.control(action, query, value);
    } catch (e: any) {
      get().addToast(`Music control failed: ${e.message}`, 'error');
    }
  },

  activateScene: async (sceneId) => {
    try {
      await api.scenes.activate(sceneId);
      get().addToast('Scene command sent successfully', 'success');
    } catch (e: any) {
      get().addToast(`Failed to activate scene: ${e.message}`, 'error');
    }
  },

  testAutomation: async (autoId) => {
    try {
      await api.automations.test(autoId);
      get().addToast('Automation execution test sent', 'info');
    } catch (e: any) {
      get().addToast(`Automation test failed: ${e.message}`, 'error');
    }
  },
}));
