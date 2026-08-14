import React, { useEffect, useState } from 'react';
import { useJarvisStore } from '../state/store';
import { 
  Mic, 
  Lightbulb, 
  Wind, 
  Thermometer, 
  Lock, 
  Unlock, 
  Wifi, 
  Clock, 
  Calendar,
  MessageSquare
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const {
    devices,
    voice,
    events,
    fetchDevices,
    fetchEvents,
    controlDevice
  } = useJarvisStore();

  // Local state for interactive door lock
  const [doorLocked, setDoorLocked] = useState(true);

  // Live clock and date state
  const [timeStr, setTimeStr] = useState('');
  const [dateStr, setDateStr] = useState('');

  // Eye blinking state
  const [isBlinking, setIsBlinking] = useState(false);

  // Poll database event logs for recent voice transcibed & response text
  useEffect(() => {
    fetchDevices();
    fetchEvents('voice', undefined, undefined, 10);
    const interval = setInterval(() => {
      fetchEvents('voice', undefined, undefined, 10);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  // Update clock every second
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
      setDateStr(now.toLocaleDateString([], { weekday: 'short', day: '2-digit', month: 'short' }).toUpperCase());
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  // Natural random blinking interval (every 4-6 seconds)
  useEffect(() => {
    const triggerBlink = () => {
      setIsBlinking(true);
      setTimeout(() => {
        setIsBlinking(false);
      }, 150);
    };

    const runBlinkTimer = () => {
      const randomDelay = 3000 + Math.random() * 3000;
      return setTimeout(() => {
        triggerBlink();
        blinkTimeoutId = runBlinkTimer();
      }, randomDelay);
    };

    let blinkTimeoutId = runBlinkTimer();
    return () => clearTimeout(blinkTimeoutId);
  }, []);

  // Count active lights and fans
  const activeLights = devices.filter(
    (d) => (d.type === 'relay' || d.type === 'dimmer') && 
           (d.name.toLowerCase().includes('light') || d.name.toLowerCase().includes('lamp')) &&
           d.state === 'on'
  ).length;

  const totalLights = devices.filter(
    (d) => (d.type === 'relay' || d.type === 'dimmer') && 
           (d.name.toLowerCase().includes('light') || d.name.toLowerCase().includes('lamp'))
  ).length;

  const isFanOn = devices.some(
    (d) => d.type === 'relay' && 
           d.name.toLowerCase().includes('fan') && 
           d.state === 'on'
  );

  // Find a temperature reading from sensors or fallback to a default
  const tempDevice = devices.find((d) => d.type === 'sensor' && d.name.toLowerCase().includes('temp'));
  const currentTemp = tempDevice ? `${tempDevice.state}°C` : '26°C';

  // Toggle all lights helper
  const handleToggleLights = async () => {
    const lightDevices = devices.filter(
      (d) => (d.type === 'relay' || d.type === 'dimmer') && 
             (d.name.toLowerCase().includes('light') || d.name.toLowerCase().includes('lamp'))
    );
    const targetAction = activeLights > 0 ? 'off' : 'on';
    for (const d of lightDevices) {
      await controlDevice(d.id, targetAction);
    }
  };

  // Toggle fan helper
  const handleToggleFan = async () => {
    const fanDevice = devices.find((d) => d.type === 'relay' && d.name.toLowerCase().includes('fan'));
    if (fanDevice) {
      await controlDevice(fanDevice.id, isFanOn ? 'off' : 'on');
    }
  };

  // Reconstruct conversation from event logs
  const voiceEvents = events
    .filter((e) => e.event_type === 'VOICE_TRANSCRIBED' || e.event_type === 'ASSISTANT_RESPONSE')
    .reverse();

  const lastUserQuery = voiceEvents.find((e) => e.event_type === 'VOICE_TRANSCRIBED')?.message || 'No transcription yet';
  const lastJarvisReply = voiceEvents.find((e) => e.event_type === 'ASSISTANT_RESPONSE')?.message || 'Hello, Umais. How can I help you today?';

  // SVG Eye path definitions based on state
  const getEyePath = (side: 'left' | 'right') => {
    if (isBlinking) {
      // Flat blink lines
      return side === 'left' ? 'M 10 25 L 50 25' : 'M 10 25 L 50 25';
    }

    if (voice.status === 'listening') {
      // Highly curves, excited arcs
      return side === 'left' 
        ? 'M 10 30 Q 30 10 50 30 Q 30 20 10 30' 
        : 'M 10 30 Q 30 10 50 30 Q 30 20 10 30';
    }

    if (voice.status === 'thinking') {
      // Flat slanting squint
      return side === 'left' 
        ? 'M 10 28 L 50 22 Q 30 25 10 28' 
        : 'M 10 22 L 50 28 Q 30 25 10 22';
    }

    if (voice.status === 'speaking') {
      // Happy eyes arching up
      return side === 'left'
        ? 'M 12 32 Q 30 12 48 32 Q 30 22 12 32'
        : 'M 12 32 Q 30 12 48 32 Q 30 22 12 32';
    }

    // Default resting eye arcs
    return side === 'left'
      ? 'M 10 28 Q 30 14 50 28'
      : 'M 10 28 Q 30 14 50 28';
  };

  return (
    <div className="relative min-h-[calc(100vh-6rem)] w-full bg-[#030712] text-slate-100 rounded-3xl overflow-hidden p-8 border border-cyan-500/20 shadow-[0_0_50px_rgba(6,182,212,0.15)] flex flex-col justify-between">
      
      {/* Dynamic embedded Sci-Fi style definitions */}
      <style>{`
        @keyframes rot-slow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes pulse-glow {
          0%, 100% { box-shadow: 0 0 15px rgba(6, 182, 212, 0.4); border-color: rgba(6, 182, 212, 0.3); }
          50% { box-shadow: 0 0 40px rgba(6, 182, 212, 0.8); border-color: rgba(6, 182, 212, 0.8); }
        }
        @keyframes float-subtle {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-4px); }
        }
        .anim-spin-slow {
          animation: rot-slow 20s linear infinite;
        }
        .anim-spin-reverse {
          animation: rot-slow 15s linear infinite reverse;
        }
        .anim-pulse-glow {
          animation: pulse-glow 3s ease-in-out infinite;
        }
        .anim-float {
          animation: float-subtle 4s ease-in-out infinite;
        }
      `}</style>

      {/* Grid Pattern Background */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#0c4a6e_1px,transparent_1px),linear-gradient(to_bottom,#0c4a6e_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] opacity-[0.07] pointer-events-none" />

      {/* 1. Header Section */}
      <div className="flex justify-between items-center border-b border-cyan-500/10 pb-6 z-10">
        <div>
          <h1 className="text-3xl font-extrabold tracking-wider bg-gradient-to-r from-cyan-400 via-blue-500 to-indigo-400 bg-clip-text text-transparent drop-shadow-[0_0_15px_rgba(6,182,212,0.4)]">
            JARVIS
          </h1>
          <p className="text-[10px] tracking-[0.25em] font-bold uppercase text-cyan-400/70">
            Room Assistant v1.0
          </p>
        </div>

        {/* Clock & Status info */}
        <div className="flex items-center gap-6">
          <div className="text-right">
            <div className="flex items-center gap-2 text-2xl font-bold font-mono text-cyan-400 drop-shadow-[0_0_10px_rgba(6,182,212,0.3)]">
              <Clock className="w-5 h-5 text-cyan-400" />
              {timeStr || '--:--'}
            </div>
            <div className="flex items-center justify-end gap-1.5 text-[10px] font-bold text-slate-400 tracking-wider mt-1">
              <Calendar className="w-3 h-3 text-slate-500" />
              {dateStr || 'LOADING...'}
            </div>
          </div>
          <div className="h-10 w-[1px] bg-cyan-500/10" />
          <Wifi className="w-6 h-6 text-cyan-400 animate-pulse drop-shadow-[0_0_8px_rgba(6,182,212,0.4)]" />
        </div>
      </div>

      {/* 2. Main Hologram & Side Panels Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 my-auto items-center z-10">
        
        {/* Left Control Cards (5 cols) */}
        <div className="lg:col-span-4 space-y-4">
          
          {/* Microphone Card */}
          <div className="relative group overflow-hidden bg-slate-950/60 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-4 shadow-[0_4px_20px_rgba(0,0,0,0.3)] hover:border-cyan-400/40 transition-all duration-300">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-3">
                <div className={`p-2.5 rounded-xl ${voice.status === 'listening' ? 'bg-cyan-500/20 text-cyan-400 animate-pulse' : 'bg-slate-900 text-slate-400'}`}>
                  <Mic className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">System Input</span>
                  <span className="text-sm font-extrabold capitalize text-slate-200">
                    {voice.status === 'listening' ? 'Listening...' : 
                     voice.status === 'thinking' ? 'Thinking...' : 
                     voice.status === 'speaking' ? 'Speaking...' : 'Idle / Standby'}
                  </span>
                </div>
              </div>
              
              {/* Waveform graphic */}
              <div className="flex items-center gap-[3px] h-6">
                {[1, 2, 3, 4, 5].map((bar) => (
                  <div
                    key={bar}
                    className={`w-[3px] bg-cyan-400 rounded-full transition-all duration-300 ${
                      voice.status === 'listening' ? 'anim-waveform' : 'h-1.5'
                    }`}
                    style={{
                      animation: voice.status === 'listening' ? `waveform-pulse 0.8s ease-in-out infinite alternate` : 'none',
                      animationDelay: `${bar * 0.15}s`
                    }}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Lights Controller Card */}
          <button 
            onClick={handleToggleLights}
            className="w-full text-left bg-slate-950/60 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-4 shadow-[0_4px_20px_rgba(0,0,0,0.3)] hover:border-cyan-400/40 active:scale-[0.98] transition-all duration-300"
          >
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-3">
                <div className={`p-2.5 rounded-xl ${activeLights > 0 ? 'bg-yellow-500/20 text-yellow-400' : 'bg-slate-900 text-slate-400'}`}>
                  <Lightbulb className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">Lights Control</span>
                  <span className="text-sm font-extrabold text-slate-200">
                    {activeLights > 0 ? `${activeLights} Active` : 'All Off'}
                  </span>
                </div>
              </div>
              <span className={`text-[10px] font-extrabold px-2.5 py-1 rounded-full uppercase tracking-wider ${
                activeLights > 0 ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20' : 'bg-slate-900 text-slate-500 border border-slate-800'
              }`}>
                {activeLights > 0 ? 'Toggle Off' : 'Toggle On'}
              </span>
            </div>
          </button>

          {/* Fan Controller Card */}
          <button
            onClick={handleToggleFan}
            className="w-full text-left bg-slate-950/60 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-4 shadow-[0_4px_20px_rgba(0,0,0,0.3)] hover:border-cyan-400/40 active:scale-[0.98] transition-all duration-300"
          >
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-3">
                <div className={`p-2.5 rounded-xl ${isFanOn ? 'bg-green-500/20 text-green-400 animate-spin-slow' : 'bg-slate-900 text-slate-400'}`}>
                  <Wind className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">Air Circulation</span>
                  <span className="text-sm font-extrabold text-slate-200">
                    {isFanOn ? 'Fan Running' : 'Fan Stopped'}
                  </span>
                </div>
              </div>
              <span className={`text-[10px] font-extrabold px-2.5 py-1 rounded-full uppercase tracking-wider ${
                isFanOn ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-slate-900 text-slate-500 border border-slate-800'
              }`}>
                {isFanOn ? 'Switch Off' : 'Switch On'}
              </span>
            </div>
          </button>

          {/* Room Temperature Card */}
          <div className="bg-slate-950/60 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-4 shadow-[0_4px_20px_rgba(0,0,0,0.35)]">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-orange-500/20 text-orange-400">
                  <Thermometer className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">Room Temp</span>
                  <span className="text-sm font-extrabold text-slate-200">Climate Monitoring</span>
                </div>
              </div>
              <span className="text-lg font-mono font-black text-orange-400 drop-shadow-[0_0_6px_rgba(251,146,60,0.3)]">
                {currentTemp}
              </span>
            </div>
          </div>

          {/* Interactive Door Card */}
          <button 
            onClick={() => setDoorLocked(!doorLocked)}
            className="w-full text-left bg-slate-950/60 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-4 shadow-[0_4px_20px_rgba(0,0,0,0.3)] hover:border-cyan-400/40 active:scale-[0.98] transition-all duration-300"
          >
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-3">
                <div className={`p-2.5 rounded-xl ${doorLocked ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'}`}>
                  {doorLocked ? <Lock className="w-5 h-5" /> : <Unlock className="w-5 h-5" />}
                </div>
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">Security Gate</span>
                  <span className="text-sm font-extrabold text-slate-200">
                    {doorLocked ? 'Main Door Locked' : 'Main Door Unlocked'}
                  </span>
                </div>
              </div>
              <span className={`text-[10px] font-extrabold px-2.5 py-1 rounded-full uppercase tracking-wider ${
                doorLocked ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 'bg-green-500/10 text-green-400 border border-green-500/20'
              }`}>
                {doorLocked ? 'Unlock' : 'Lock'}
              </span>
            </div>
          </button>

        </div>

        {/* Center Hologram Ring (4 cols) */}
        <div className="lg:col-span-4 flex justify-center items-center py-6">
          <div className="relative w-72 h-72 rounded-full flex items-center justify-center">
            
            {/* Outer dotted decorative rotating ring */}
            <div className="absolute inset-0 rounded-full border border-dashed border-cyan-500/30 anim-spin-slow scale-110" />

            {/* Middle technical/hologram ring */}
            <div className="absolute inset-2 rounded-full border-2 border-double border-cyan-500/20 anim-spin-reverse" />
            <div className="absolute inset-2 rounded-full border-t-2 border-b-2 border-cyan-400/40 anim-spin-slow" />

            {/* Inner glowing pulsing ring */}
            <div className="absolute inset-8 rounded-full border border-cyan-500/50 bg-[#020617]/90 shadow-[0_0_20px_rgba(6,182,212,0.3)] anim-pulse-glow" />

            {/* Floating Cyan Arc Eyes */}
            <svg 
              className="absolute w-40 h-24 text-cyan-400 drop-shadow-[0_0_12px_rgba(34,211,238,0.85)] anim-float" 
              viewBox="0 0 160 60"
              fill="none" 
              stroke="currentColor" 
              strokeWidth="4" 
              strokeLinecap="round"
            >
              {/* Left Eye */}
              <g transform="translate(10, 0)">
                <path d={getEyePath('left')} />
              </g>

              {/* Right Eye */}
              <g transform="translate(90, 0)">
                <path d={getEyePath('right')} />
              </g>
            </svg>

          </div>
        </div>

        {/* Right Interaction Display Dialogue (4 cols) */}
        <div className="lg:col-span-4 space-y-6">
          
          {/* Dialogue display container */}
          <div className="bg-slate-950/60 backdrop-blur-md border border-cyan-500/20 rounded-3xl p-6 shadow-[0_8px_32px_rgba(0,0,0,0.35)] min-h-[220px] flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-cyan-400 border-b border-cyan-500/10 pb-2">
                <MessageSquare className="w-4 h-4" />
                <span className="text-[10px] font-bold uppercase tracking-widest">Active Dialogue</span>
              </div>
              
              <div className="space-y-3">
                <div className="text-xs">
                  <span className="font-extrabold text-cyan-400/80 block uppercase text-[9px] tracking-wider mb-0.5">Umais</span>
                  <p className="text-slate-300 italic font-medium leading-relaxed">
                    "{lastUserQuery}"
                  </p>
                </div>
                
                <div className="text-xs pt-2 border-t border-slate-900">
                  <span className="font-extrabold text-blue-400 block uppercase text-[9px] tracking-wider mb-0.5">JARVIS</span>
                  <p className="text-cyan-200 font-bold leading-relaxed text-sm">
                    {lastJarvisReply}
                  </p>
                </div>
              </div>
            </div>

            {/* Speaker voice output wave visualization */}
            {voice.status === 'speaking' && (
              <div className="flex items-center gap-1.5 pt-4 border-t border-cyan-500/10">
                <div className="h-2 w-2 rounded-full bg-cyan-400 animate-ping" />
                <span className="text-[9px] font-bold text-cyan-400/70 tracking-widest uppercase">Output Waveform Active</span>
              </div>
            )}
          </div>

        </div>

      </div>

      {/* 3. Footer Branding */}
      <div className="flex justify-between items-center border-t border-cyan-500/10 pt-6 z-10 text-[9px] font-extrabold text-cyan-500/40 uppercase tracking-[0.3em]">
        <span>Location: Main Bedroom</span>
        <span>Secure Connection Established</span>
      </div>

    </div>
  );
};
