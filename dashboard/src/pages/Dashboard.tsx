import React, { useEffect } from 'react';
import { useJarvisStore } from '../state/store';
import { Card } from '../components/ui/Card';
import { ProgressBar } from '../components/ui/ProgressBar';
import {
  Cpu,
  Database,
  HardDrive,
  Clock,
  Layers,
  Activity,
  Server,
  Play,
  Pause,
  SkipForward,
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const {
    rooms,
    nodes,
    devices,
    music,
    systemStats,
    fetchRooms,
    fetchNodes,
    fetchDevices,
    fetchMusicState,
    controlMusic,
  } = useJarvisStore();

  useEffect(() => {
    fetchRooms();
    fetchNodes();
    fetchDevices();
    fetchMusicState();
  }, []);

  const formatUptime = (sec: number) => {
    const hrs = Math.floor(sec / 3600);
    const mins = Math.floor((sec % 3600) / 60);
    return `${hrs}h ${mins}m`;
  };

  const activeDevicesCount = devices.filter((d) => d.state === 'on' && d.confirmed).length;
  const onlineNodesCount = nodes.filter((n) => n.status === 'online').length;

  return (
    <div className="space-y-6">
      {/* Overview stats cards grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="flex items-center gap-4">
          <div className="p-4 rounded-xl bg-blue-500/10 dark:bg-blue-400/10 text-blue-500">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
              Active Devices
            </span>
            <span className="text-2xl font-bold text-slate-800 dark:text-slate-100">
              {activeDevicesCount} / {devices.length}
            </span>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="p-4 rounded-xl bg-green-500/10 dark:bg-green-400/10 text-green-500">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
              Nodes Online
            </span>
            <span className="text-2xl font-bold text-slate-800 dark:text-slate-100">
              {onlineNodesCount} / {nodes.length}
            </span>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="p-4 rounded-xl bg-indigo-500/10 dark:bg-indigo-400/10 text-indigo-500">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
              System Uptime
            </span>
            <span className="text-2xl font-bold text-slate-800 dark:text-slate-100">
              {systemStats ? formatUptime(systemStats.server_uptime) : '0h 0m'}
            </span>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="p-4 rounded-xl bg-purple-500/10 dark:bg-purple-400/10 text-purple-500">
            <Database className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
              DB File Size
            </span>
            <span className="text-2xl font-bold text-slate-800 dark:text-slate-100">
              {systemStats ? `${systemStats.db_size_mb} MB` : '0.0 MB'}
            </span>
          </div>
        </Card>
      </div>

      {/* Main Body Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Resource monitoring panel */}
        <Card className="lg:col-span-2 space-y-6">
          <div className="flex items-center gap-2 border-b border-slate-300/30 pb-3">
            <Server className="w-5 h-5 text-blue-500" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              Server Host Resource Loads
            </h3>
          </div>

          {systemStats ? (
            <div className="space-y-5">
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-slate-400">
                  <span className="flex items-center gap-1.5">
                    <Cpu className="w-4 h-4" /> CPU Load
                  </span>
                  <span>{systemStats.cpu_percent}%</span>
                </div>
                <ProgressBar progress={systemStats.cpu_percent} />
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-slate-400">
                  <span className="flex items-center gap-1.5">
                    <Activity className="w-4 h-4" /> RAM Utilization
                  </span>
                  <span>{systemStats.ram_percent}%</span>
                </div>
                <ProgressBar progress={systemStats.ram_percent} />
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-slate-400">
                  <span className="flex items-center gap-1.5">
                    <HardDrive className="w-4 h-4" /> Disk Capacity
                  </span>
                  <span>{systemStats.disk_percent}%</span>
                </div>
                <ProgressBar progress={systemStats.disk_percent} />
              </div>
            </div>
          ) : (
            <div className="text-center py-6 text-sm text-slate-400">
              Diagnostics metrics unavailable.
            </div>
          )}
        </Card>

        {/* Music Widget */}
        <Card className="flex flex-col justify-between p-6">
          <div className="flex items-center gap-2 border-b border-slate-300/30 pb-3">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              Now Playing
            </h3>
          </div>

          {music.track ? (
            <div className="flex-1 flex flex-col justify-center items-center py-6 gap-4 text-center">
              {music.track.album_art_url ? (
                <img
                  src={music.track.album_art_url}
                  alt={music.track.title}
                  className="w-32 h-32 rounded-xl shadow-neo-sm-light dark:shadow-neo-sm-dark object-cover"
                />
              ) : (
                <div className="w-32 h-32 rounded-xl bg-slate-300 dark:bg-slate-800 shadow-neo-sm-inset-light dark:shadow-neo-sm-inset-dark flex items-center justify-center text-slate-400">
                  Music
                </div>
              )}

              <div>
                <h4 className="font-bold text-slate-800 dark:text-slate-200">
                  {music.track.title}
                </h4>
                <p className="text-xs text-slate-400 font-semibold">{music.track.artist}</p>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={() => controlMusic(music.is_playing ? 'pause' : 'resume')}
                  className="p-3.5 rounded-full bg-bg-light dark:bg-bg-dark shadow-neo-sm-light dark:shadow-neo-sm-dark text-slate-600 dark:text-slate-400 active:scale-90 transition-all"
                >
                  {music.is_playing ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
                </button>
                <button
                  onClick={() => controlMusic('next')}
                  className="p-3.5 rounded-full bg-bg-light dark:bg-bg-dark shadow-neo-sm-light dark:shadow-neo-sm-dark text-slate-600 dark:text-slate-400 active:scale-90 transition-all"
                >
                  <SkipForward className="w-5 h-5" />
                </button>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center text-sm text-slate-400 py-12">
              Spotify inactive.
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};
