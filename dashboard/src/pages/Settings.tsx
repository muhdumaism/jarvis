import React, { useEffect, useState } from 'react';
import { useJarvisStore } from '../state/store';
import { api, clearAuthToken } from '../services/api';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { CheckCircle, Database, HelpCircle, LogOut, Settings as SettingsIcon, Wrench } from 'lucide-react';

const wizardSteps = [
  'Welcome to JARVIS OS',
  'Server settings verification',
  'WiFi and LAN connection check',
  'Main ESP32 registration',
  'TFT display interface test',
  'INMP441 digital microphone test',
  'Audio DAC amplifier check',
  'STT Faster-Whisper validation',
  'TTS Piper engine validation',
  'Ollama local LLM connection',
  'Spotify Bridge OAuth checks',
  'Secondary ESP32-S3 node pairing',
  'Device relay channel registry mapping',
  'Automated test: Relay activation',
  'Automated test: Microphone capture',
  'Automated test: Piper response synthesis',
  'Automated test: Local Speaker playback',
  'Automated test: Voice command pipeline loop',
  'Wizard complete',
];

export const Settings: React.FC = () => {
  const { addToast } = useJarvisStore();
  const [activeTab, setActiveTab] = useState<'config' | 'backup' | 'wizard'>('config');
  const [settings, setSettings] = useState<Record<string, string>>({});
  const [restoreFile, setRestoreFile] = useState<File | null>(null);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const data = await api.settings.get();
      setSettings(data);
    } catch (e: any) {
      console.warn('Failed to load settings:', e.message);
    }
  };

  const handleBackup = async () => {
    try {
      const blob = await api.settings.backup();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `jarvis_backup_${new Date().toISOString().split('T')[0]}.db`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      addToast('Database backup downloaded successfully', 'success');
    } catch (e: any) {
      addToast(`Backup failed: ${e.message}`, 'error');
    }
  };

  const handleRestore = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!restoreFile) return;

    try {
      await api.settings.restore(restoreFile);
      addToast('Database restored successfully', 'success');
      setRestoreFile(null);
      fetchSettings();
    } catch (e: any) {
      addToast(`Restore failed: ${e.message}`, 'error');
    }
  };

  const handleLogout = () => {
    clearAuthToken();
    addToast('Logged out of system dashboard session', 'info');
    window.location.hash = '/login';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold uppercase tracking-wider text-slate-800 dark:text-slate-100">
          System Configuration
        </h2>
        <Button onClick={handleLogout} className="btn-neo-danger text-xs px-4 py-2">
          <LogOut className="w-4 h-4" /> Logout Session
        </Button>
      </div>

      {/* Tabs list */}
      <div className="flex gap-4 border-b border-slate-300/30 dark:border-slate-800/30 pb-2">
        <button
          onClick={() => setActiveTab('config')}
          className={`px-4 py-2 text-xs font-bold uppercase tracking-wider transition-colors ${
            activeTab === 'config'
              ? 'text-blue-500 border-b-2 border-blue-500'
              : 'text-slate-400 hover:text-slate-600'
          }`}
        >
          Server Config
        </button>
        <button
          onClick={() => setActiveTab('backup')}
          className={`px-4 py-2 text-xs font-bold uppercase tracking-wider transition-colors ${
            activeTab === 'backup'
              ? 'text-blue-500 border-b-2 border-blue-500'
              : 'text-slate-400 hover:text-slate-600'
          }`}
        >
          Backup / Restore
        </button>
        <button
          onClick={() => setActiveTab('wizard')}
          className={`px-4 py-2 text-xs font-bold uppercase tracking-wider transition-colors ${
            activeTab === 'wizard'
              ? 'text-blue-500 border-b-2 border-blue-500'
              : 'text-slate-400 hover:text-slate-600'
          }`}
        >
          Setup Wizard Checklist
        </button>
      </div>

      {/* Tabs Viewport */}
      {activeTab === 'config' && (
        <Card className="space-y-6">
          <div className="flex items-center gap-2 border-b pb-2">
            <SettingsIcon className="w-5 h-5 text-slate-400" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              Environment Parameter Checks
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs font-bold uppercase tracking-wider text-slate-400">
            <div className="space-y-2">
              <p className="text-[10px] text-slate-400 tracking-widest block">Subsystem Settings</p>
              <div className="flex justify-between border-b pb-2">
                <span>STT Provider</span>
                <span className="text-slate-700 dark:text-slate-200">Local Whisper</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span>TTS Engine</span>
                <span className="text-slate-700 dark:text-slate-200">Piper TTS</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span>AI Intent Engine</span>
                <span className="text-slate-700 dark:text-slate-200">Ollama Local LLM</span>
              </div>
            </div>

            <div className="space-y-2">
              <p className="text-[10px] text-slate-400 tracking-widest block">Firmware Pins config</p>
              <div className="flex justify-between border-b pb-2">
                <span>INMP441 I2S0 Pins</span>
                <span className="text-slate-700 dark:text-slate-200">BCLK=26, WS=25, DATA=33</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span>Audio Out I2S1 Pins</span>
                <span className="text-slate-700 dark:text-slate-200">BCLK=22, WS=21, DOUT=23</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span>TFT SPI Pins</span>
                <span className="text-slate-700 dark:text-slate-200">CS=15, DC=2, RST=4, MOSI=13</span>
              </div>
            </div>
          </div>
        </Card>
      )}

      {activeTab === 'backup' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Backup card */}
          <Card className="flex flex-col justify-between h-48">
            <div>
              <div className="flex items-center gap-2 border-b pb-2 mb-3">
                <Database className="w-5 h-5 text-slate-400" />
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                  Export Database Backup
                </h3>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed font-semibold">
                Downloads a serialized copy of the SQLite database containing room definitions,
                nodes configuration, scenes, automations, and system settings.
              </p>
            </div>
            <Button onClick={handleBackup} className="bg-blue-600 text-white font-bold w-full">
              Export Backup File
            </Button>
          </Card>

          {/* Restore Card */}
          <Card className="flex flex-col justify-between h-48">
            <div>
              <div className="flex items-center gap-2 border-b pb-2 mb-3">
                <Wrench className="w-5 h-5 text-slate-400" />
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                  Restore Database
                </h3>
              </div>
              <form onSubmit={handleRestore} className="space-y-4">
                <input
                  type="file"
                  accept=".db"
                  required
                  onChange={(e) => setRestoreFile(e.target.files?.[0] || null)}
                  className="text-xs text-slate-500 font-bold"
                />
                <Button type="submit" className="bg-green-600 text-white font-bold w-full">
                  Import Backup File
                </Button>
              </form>
            </div>
          </Card>
        </div>
      )}

      {activeTab === 'wizard' && (
        <Card className="space-y-4 max-h-[600px] overflow-y-auto">
          <div className="flex items-center gap-2 border-b pb-2">
            <HelpCircle className="w-5 h-5 text-slate-400" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              JARVIS OS Setup Wizard Checklist
            </h3>
          </div>

          <div className="space-y-2">
            {wizardSteps.map((step, idx) => (
              <div key={idx} className="flex items-center gap-3 py-2 text-xs font-semibold text-slate-600 dark:text-slate-300">
                <CheckCircle className="w-4 h-4 text-green-500 shrink-0" />
                <span>
                  Step {idx + 1}: {step}
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};
