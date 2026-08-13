import React, { useEffect } from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useJarvisStore } from './state/store';
import { connectWebSocket, disconnectWebSocket } from './websocket/client';
import { getAuthToken } from './services/api';
import { Layout } from './components/layout/Layout';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Rooms } from './pages/Rooms';
import { Devices } from './pages/Devices';
import { Nodes } from './pages/Nodes';
import { Assistant } from './pages/Assistant';
import { Voice } from './pages/Voice';
import { Music } from './pages/Music';
import { Automations } from './pages/Automations';
import { Scenes } from './pages/Scenes';
import { Firmware } from './pages/Firmware';
import { Hardware } from './pages/Hardware';
import { Circuits } from './pages/Circuits';
import { Logs } from './pages/Logs';
import { Settings } from './pages/Settings';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = getAuthToken();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <Layout>{children}</Layout>;
};

function App() {
  const { setSystemConnected } = useJarvisStore();

  useEffect(() => {
    // Check if authenticated
    const token = getAuthToken();
    if (token) {
      connectWebSocket();
    } else {
      setSystemConnected(false);
    }

    return () => {
      disconnectWebSocket();
    };
  }, []);

  return (
    <HashRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        
        {/* Protected routes wrapped in layout */}
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/rooms" element={<ProtectedRoute><Rooms /></ProtectedRoute>} />
        <Route path="/devices" element={<ProtectedRoute><Devices /></ProtectedRoute>} />
        <Route path="/nodes" element={<ProtectedRoute><Nodes /></ProtectedRoute>} />
        <Route path="/assistant" element={<ProtectedRoute><Assistant /></ProtectedRoute>} />
        <Route path="/voice" element={<ProtectedRoute><Voice /></ProtectedRoute>} />
        <Route path="/music" element={<ProtectedRoute><Music /></ProtectedRoute>} />
        <Route path="/automations" element={<ProtectedRoute><Automations /></ProtectedRoute>} />
        <Route path="/scenes" element={<ProtectedRoute><Scenes /></ProtectedRoute>} />
        <Route path="/firmware" element={<ProtectedRoute><Firmware /></ProtectedRoute>} />
        <Route path="/hardware" element={<ProtectedRoute><Hardware /></ProtectedRoute>} />
        <Route path="/circuits" element={<ProtectedRoute><Circuits /></ProtectedRoute>} />
        <Route path="/logs" element={<ProtectedRoute><Logs /></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
        
        {/* Fallbacks */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </HashRouter>
  );
}

export default App;
