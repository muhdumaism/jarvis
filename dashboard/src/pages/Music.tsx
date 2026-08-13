import React, { useEffect, useState } from 'react';
import { useJarvisStore } from '../state/store';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { ProgressBar } from '../components/ui/ProgressBar';
import { Play, Pause, SkipForward, SkipBack, Volume2, Search, Music as MusicIcon, Bluetooth, Wifi, LogOut } from 'lucide-react';
import { api } from '../services/api';

export const Music: React.FC = () => {
  const { music, fetchMusicState, controlMusic, addToast } = useJarvisStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [localProgress, setLocalProgress] = useState(0);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  // Bluetooth and Audio devices state
  const [audioDevices, setAudioDevices] = useState<{ id: string; name: string }[]>([]);
  const [selectedDeviceName, setSelectedDeviceName] = useState('');
  const [isLoadingDevices, setIsLoadingDevices] = useState(false);

  // Poll state and fetch audio devices
  useEffect(() => {
    fetchMusicState();
    loadAudioDevices();

    // Listen for Spotify OAuth message from popup
    const handleSpotifyMessage = (event: MessageEvent) => {
      if (event.data === 'spotify_connected') {
        addToast('Spotify account authorized successfully!', 'success');
        fetchMusicState();
      }
    };
    window.addEventListener('message', handleSpotifyMessage);

    return () => window.removeEventListener('message', handleSpotifyMessage);
  }, []);

  // Update selected device name when music state changes
  useEffect(() => {
    if (music.current_output_device) {
      setSelectedDeviceName(music.current_output_device);
    }
  }, [music.current_output_device]);

  // Interpolate progress locally for smooth slider updates
  useEffect(() => {
    if (!music.track) return;
    setLocalProgress(music.track.position_ms);

    if (!music.is_playing) return;

    const timer = setInterval(() => {
      setLocalProgress((prev) => {
        if (!music.track || prev >= music.track.duration_ms) {
          clearInterval(timer);
          return prev;
        }
        return prev + 1000;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [music]);

  const loadAudioDevices = async () => {
    setIsLoadingDevices(true);
    try {
      const devices = await api.music.getAudioDevices();
      setAudioDevices(devices || []);
    } catch (err) {
      console.error('Failed to load audio devices:', err);
    } finally {
      setIsLoadingDevices(false);
    }
  };

  const handleConnectSpotify = async () => {
    try {
      const res = await api.music.getAuthUrl();
      if (res.url) {
        // Open Spotify auth in a popup window centered
        const width = 600;
        const height = 700;
        const left = window.screen.width / 2 - width / 2;
        const top = window.screen.height / 2 - height / 2;
        window.open(
          res.url,
          'spotify-auth',
          `width=${width},height=${height},left=${left},top=${top}`
        );
      }
    } catch (err: any) {
      addToast(err.message || 'Failed to get Spotify authorization URL', 'error');
    }
  };

  const handleDisconnectSpotify = async () => {
    if (!confirm('Are you sure you want to disconnect Spotify?')) return;
    try {
      await api.music.disconnect();
      addToast('Spotify account disconnected.', 'success');
      fetchMusicState();
    } catch (err: any) {
      addToast(err.message || 'Failed to disconnect Spotify', 'error');
    }
  };

  const handleSpeakerChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const name = e.target.value;
    setSelectedDeviceName(name);
    if (!name) return;
    try {
      await api.music.setBluetoothSpeaker(name);
      addToast(`Bluetooth speaker target name updated to: ${name}`, 'success');
      fetchMusicState();
    } catch (err: any) {
      addToast(err.message || 'Failed to update Bluetooth speaker setting', 'error');
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    try {
      const results = await api.music.search(searchQuery);
      setSearchResults(results || []);
    } catch (err) {
      console.error('Search failed:', err);
      addToast('Spotify search failed. Verify connection status.', 'error');
    } finally {
      setIsSearching(false);
    }
  };

  const handlePlayTrack = (trackUri: string) => {
    controlMusic('play', trackUri);
    setSearchResults([]);
    setSearchQuery('');
  };

  const formatTime = (ms: number) => {
    const mins = Math.floor(ms / 60000);
    const secs = Math.floor((ms % 60000) / 1000);
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const progressPercent = music.track
    ? (localProgress / music.track.duration_ms) * 100
    : 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h2 className="text-xl font-bold uppercase tracking-wider text-slate-800 dark:text-slate-100">
          Spotify Playback Controller
        </h2>
        
        {/* Connection Management Actions */}
        <div className="flex gap-2 w-full sm:w-auto">
          {music.track !== undefined ? (
            <button
              onClick={handleConnectSpotify}
              className="flex-1 sm:flex-initial btn-neo bg-emerald-500 hover:bg-emerald-400 text-black font-bold text-xs uppercase px-4 py-2 border-2 border-black"
            >
              Connect Spotify
            </button>
          ) : null}
          <button
            onClick={handleDisconnectSpotify}
            className="flex-1 sm:flex-initial btn-neo bg-rose-500 hover:bg-rose-400 text-white font-bold text-xs uppercase px-4 py-2 border-2 border-black flex items-center justify-center gap-2"
          >
            <LogOut className="w-3.5 h-3.5" /> Disconnect
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Playback Console */}
        <Card className="lg:col-span-2 flex flex-col justify-between p-6 md:p-8 gap-8 border-2 border-black shadow-neo">
          {music.track ? (
            <div className="flex flex-col md:flex-row gap-8 items-center">
              {music.track.album_art_url ? (
                <img
                  src={music.track.album_art_url}
                  alt={music.track.title}
                  className="w-40 h-40 md:w-48 md:h-48 border-2 border-black shadow-neo-sm object-cover"
                />
              ) : (
                <div className="w-40 h-40 md:w-48 md:h-48 border-2 border-black bg-zinc-200 dark:bg-zinc-800 flex items-center justify-center text-slate-400">
                  <MusicIcon className="w-12 h-12" />
                </div>
              )}

              <div className="flex-1 space-y-4 text-center md:text-left w-full">
                <div>
                  <h3 className="text-2xl font-black text-slate-900 dark:text-white leading-tight">
                    {music.track.title}
                  </h3>
                  <p className="text-sm text-slate-500 dark:text-zinc-400 font-bold uppercase tracking-wider mt-1">
                    {music.track.artist}
                  </p>
                  <p className="text-xs text-slate-400 dark:text-zinc-500 font-semibold">{music.track.album}</p>
                </div>

                {/* Progress bar */}
                <div className="space-y-1">
                  <ProgressBar progress={progressPercent} />
                  <div className="flex justify-between text-[10px] font-bold text-slate-500 font-mono">
                    <span>{formatTime(localProgress)}</span>
                    <span>{formatTime(music.track.duration_ms)}</span>
                  </div>
                </div>

                {/* Console control buttons */}
                <div className="flex items-center justify-center md:justify-start gap-4">
                  <button
                    onClick={() => controlMusic('previous')}
                    className="p-3 border-2 border-black bg-white dark:bg-zinc-900 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-slate-800 dark:text-white shadow-neo-sm active:scale-95 transition-all"
                  >
                    <SkipBack className="w-5 h-5" />
                  </button>

                  <button
                    onClick={() => controlMusic(music.is_playing ? 'pause' : 'resume')}
                    className="p-4 border-2 border-black bg-yellow-400 hover:bg-yellow-300 text-black shadow-neo-sm active:scale-95 transition-all"
                  >
                    {music.is_playing ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6" />}
                  </button>

                  <button
                    onClick={() => controlMusic('next')}
                    className="p-3 border-2 border-black bg-white dark:bg-zinc-900 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-slate-800 dark:text-white shadow-neo-sm active:scale-95 transition-all"
                  >
                    <SkipForward className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-16 text-slate-500 dark:text-zinc-400 text-sm font-bold flex flex-col items-center justify-center gap-4">
              <div className="w-16 h-16 rounded-full border-2 border-black bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center">
                <MusicIcon className="w-8 h-8 text-slate-400" />
              </div>
              <div>
                <p>Spotify playback inactive on connected devices.</p>
                <p className="text-xs text-slate-400 mt-1 font-medium">Click "Connect Spotify" above or open Spotify on your PC.</p>
              </div>
            </div>
          )}
        </Card>

        {/* Search Play & Volume Console */}
        <Card className="flex flex-col justify-between p-6 gap-6 border-2 border-black shadow-neo bg-white dark:bg-zinc-900">
          <div className="space-y-4">
            <h3 className="text-sm font-black uppercase tracking-wider text-slate-800 dark:text-zinc-200 border-b-2 border-black pb-2">
              Spotify Search & Play
            </h3>
            <form onSubmit={handleSearch} className="flex gap-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Track name or artist..."
                className="input-neo flex-1 border-2 border-black px-3 py-2 text-sm bg-white dark:bg-zinc-950"
              />
              <button
                type="submit"
                disabled={isSearching}
                className="p-3 border-2 border-black bg-yellow-400 hover:bg-yellow-300 text-black shadow-neo-sm active:scale-95"
              >
                <Search className="w-5 h-5" />
              </button>
            </form>

            {/* Search results list */}
            {searchResults.length > 0 && (
              <div className="mt-4 space-y-2 max-h-48 overflow-y-auto border-t-2 border-black pt-3">
                {searchResults.map((track) => (
                  <div
                    key={track.uri}
                    onClick={() => handlePlayTrack(track.uri)}
                    className="flex gap-3 items-center p-2 border-2 border-black bg-zinc-50 dark:bg-zinc-950 cursor-pointer hover:bg-yellow-100 dark:hover:bg-zinc-800 transition-colors"
                  >
                    {track.album_art_url ? (
                      <img src={track.album_art_url} alt={track.title} className="w-10 h-10 object-cover border border-black" />
                    ) : (
                      <div className="w-10 h-10 bg-zinc-200 dark:bg-zinc-800 flex items-center justify-center border border-black">
                        <MusicIcon className="w-5 h-5 text-slate-400" />
                      </div>
                    )}
                    <div className="flex-1 min-w-0 text-left">
                      <p className="text-xs font-bold text-slate-900 dark:text-slate-100 truncate">{track.title}</p>
                      <p className="text-[10px] text-slate-500 dark:text-zinc-400 font-bold truncate">{track.artist}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="space-y-4">
            <h3 className="text-sm font-black uppercase tracking-wider text-slate-800 dark:text-zinc-200 border-b-2 border-black pb-2">
              Volume Control
            </h3>
            <div className="flex items-center gap-4">
              <Volume2 className="w-5 h-5 text-slate-800 dark:text-zinc-200" />
              <input
                type="range"
                min="0"
                max="100"
                defaultValue="50"
                onChange={(e) => controlMusic('volume', undefined, parseInt(e.target.value))}
                className="w-full h-3 bg-zinc-200 dark:bg-zinc-800 border-2 border-black appearance-none cursor-pointer rounded-none outline-none accent-black dark:accent-yellow-400"
              />
            </div>
          </div>
        </Card>
      </div>

      {/* Speaker and Hardware Output Settings Panel */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Speaker Connection Status */}
        <Card className="p-6 border-2 border-black shadow-neo bg-white dark:bg-zinc-900 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className={`p-4 border-2 border-black rounded-none ${music.speaker_connected ? 'bg-emerald-400' : 'bg-rose-400'}`}>
              <Bluetooth className="w-6 h-6 text-black" />
            </div>
            <div>
              <h4 className="font-black text-sm uppercase text-slate-800 dark:text-zinc-200">Bluetooth Audio Speaker</h4>
              <p className="text-xs text-slate-500 dark:text-zinc-400 font-bold mt-0.5">
                {music.speaker_connected ? '🔊 Speaker Connected and Active' : '⚠ Speaker Offline / Disconnected'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className={`w-3.5 h-3.5 border border-black rounded-full ${music.speaker_connected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
            <span className="text-[10px] font-black uppercase">{music.speaker_connected ? 'Online' : 'Offline'}</span>
          </div>
        </Card>

        {/* Selected Audio Output Device */}
        <Card className="p-6 border-2 border-black shadow-neo bg-white dark:bg-zinc-900 space-y-3">
          <h4 className="font-black text-sm uppercase text-slate-800 dark:text-zinc-200 flex items-center gap-2">
            <Wifi className="w-4 h-4 text-yellow-400" /> PC Audio Output Device
          </h4>
          <div className="flex flex-col gap-2">
            <label className="text-[10px] font-black uppercase text-slate-500 dark:text-zinc-400">
              Select Bluetooth or PC Output Endpoint
            </label>
            <div className="flex gap-2">
              <select
                value={selectedDeviceName}
                onChange={handleSpeakerChange}
                disabled={isLoadingDevices}
                className="select-neo flex-1 border-2 border-black bg-white dark:bg-zinc-950 px-3 py-2 text-xs font-bold font-mono outline-none"
              >
                <option value="">-- No Device Selected (Fallback to Default) --</option>
                {audioDevices.map((device) => (
                  <option key={device.id} value={device.name}>
                    {device.name}
                  </option>
                ))}
              </select>
              <button
                onClick={loadAudioDevices}
                disabled={isLoadingDevices}
                className="px-3 border-2 border-black bg-yellow-400 hover:bg-yellow-300 font-bold text-xs uppercase shadow-neo-sm active:scale-95"
              >
                Refresh
              </button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
