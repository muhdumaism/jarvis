/**
 * JARVIS API REST Client Service
 */

const API_BASE_URL = '/api';

export const getAuthToken = (): string | null => {
  return localStorage.getItem('jarvis_auth_token');
};

export const setAuthToken = (token: string): void => {
  localStorage.setItem('jarvis_auth_token', token);
};

export const clearAuthToken = (): void => {
  localStorage.removeItem('jarvis_auth_token');
};

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAuthToken();
  const headers = new Headers(options.headers || {});

  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  // Set Content-Type to application/json by default if body is present and not FormData
  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    clearAuthToken();
    window.location.hash = '/login';
    throw new Error('Unauthorized session expired');
  }

  if (!response.ok) {
    const errorText = await response.text();
    let errorDetail = '';
    try {
      const parsed = JSON.parse(errorText);
      errorDetail = parsed.detail || errorText;
    } catch {
      errorDetail = errorText;
    }
    throw new Error(errorDetail || `HTTP Error ${response.status}`);
  }

  // Handle file response (for DB backups and firmware bin downloads)
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/octet-stream')) {
    return response.blob() as any;
  }

  return response.json() as Promise<T>;
}

export const api = {
  auth: {
    login: (username: string, password: string) =>
      request<{ token: string; expires_in: number; role: string }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      }),
  },
  rooms: {
    list: () => request<any[]>('/rooms'),
    create: (data: any) =>
      request<any>('/rooms', { method: 'POST', body: JSON.stringify(data) }),
    delete: (id: string) => request<any>(`/rooms/${id}`, { method: 'DELETE' }),
  },
  devices: {
    list: () => request<any[]>('/devices'),
    create: (data: any) =>
      request<any>('/devices', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: string, data: any) =>
      request<any>(`/devices/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id: string) => request<any>(`/devices/${id}`, { method: 'DELETE' }),
    control: (id: string, action: string) =>
      request<any>(`/devices/${id}/control`, {
        method: 'POST',
        body: JSON.stringify({ action }),
      }),
    history: (id: string, limit = 50) =>
      request<any[]>(`/devices/${id}/history?limit=${limit}`),
  },
  nodes: {
    list: () => request<any[]>('/nodes'),
    create: (data: any) =>
      request<any>('/nodes', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: string, data: any) =>
      request<any>(`/nodes/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id: string) => request<any>(`/nodes/${id}`, { method: 'DELETE' }),
  },
  music: {
    getState: () => request<any>('/music/state'),
    control: (action: string, query?: string, value?: number) =>
      request<any>('/music/control', {
        method: 'POST',
        body: JSON.stringify({ action, query, value }),
      }),
    search: (query: string) => request<any[]>(`/music/search?q=${encodeURIComponent(query)}`),
    getAuthUrl: () => request<{ url: string }>('/music/auth-url'),
    disconnect: () => request<{ success: boolean }>('/music/disconnect', { method: 'POST' }),
    getAudioDevices: () => request<{ id: string; name: string }[]>('/music/audio-devices'),
    setBluetoothSpeaker: (name: string) =>
      request<{ success: boolean; name: string }>('/music/bluetooth-speaker', {
        method: 'POST',
        body: JSON.stringify({ name }),
      }),
  },
  automations: {
    list: () => request<any[]>('/automations'),
    create: (data: any) =>
      request<any>('/automations', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: any) =>
      request<any>(`/automations/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id: number) => request<any>(`/automations/${id}`, { method: 'DELETE' }),
    test: (id: number) => request<any>(`/automations/${id}/test`, { method: 'POST' }),
  },
  scenes: {
    list: () => request<any[]>('/scenes'),
    create: (data: any) =>
      request<any>('/scenes', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: any) =>
      request<any>(`/scenes/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id: number) => request<any>(`/scenes/${id}`, { method: 'DELETE' }),
    activate: (id: number) => request<any>(`/scenes/${id}/activate`, { method: 'POST' }),
  },
  firmware: {
    list: () => request<any[]>('/firmware'),
    upload: (formData: FormData) =>
      request<any>('/firmware/upload', { method: 'POST', body: formData }),
    delete: (id: number) => request<any>(`/firmware/${id}`, { method: 'DELETE' }),
    downloadUrl: (id: number) => `/api/firmware/${id}/download`,
  },
  settings: {
    get: () => request<Record<string, string>>('/settings'),
    update: (key: string, value: string) =>
      request<any>(`/settings/${key}`, {
        method: 'PUT',
        body: JSON.stringify({ value }),
      }),
    backup: () => request<Blob>('/settings/backup', { method: 'POST' }),
    restore: (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return request<any>('/settings/restore', {
        method: 'POST',
        body: formData,
      });
    },
  },
  system: {
    getStatus: () => request<any>('/system/status'),
    events: (component?: string, severity?: string, messageId?: string, limit = 100) => {
      let url = `/events?limit=${limit}`;
      if (component) url += `&component=${component}`;
      if (severity) url += `&severity=${severity}`;
      if (messageId) url += `&message_id=${messageId}`;
      return request<any[]>(url);
    },
  },
};
