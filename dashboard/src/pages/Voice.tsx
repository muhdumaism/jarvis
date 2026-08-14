import React, { useState, useRef, useEffect } from 'react';
import { useJarvisStore } from '../state/store';
import { Card } from '../components/ui/Card';
import { Mic, MicOff, Cpu, Zap, Volume2, Settings, Loader2 } from 'lucide-react';
import { StatusBadge } from '../components/ui/StatusBadge';
import { AudioRecorder } from '../utils/audioRecorder';
import { sendWSMessage } from '../websocket/client';

export const Voice: React.FC = () => {
  const { voice, systemStats } = useJarvisStore();
  const [isRecording, setIsRecording] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  
  const recorderRef = useRef<AudioRecorder | null>(null);
  const messageIdRef = useRef<string | null>(null);

  // Clean up recording on unmount
  useEffect(() => {
    return () => {
      if (recorderRef.current) {
        recorderRef.current.stop();
      }
    };
  }, []);

  const startVoiceInput = async () => {
    try {
      setErrorMsg(null);
      const msgId = `dash_voice_${Math.random().toString(36).substring(7)}`;
      messageIdRef.current = msgId;

      // 1. Send VOICE_START message to the backend
      sendWSMessage({
        type: 'VOICE_START',
        message_id: msgId,
      });

      // 2. Initialize and start Audio Recorder
      const recorder = new AudioRecorder((base64Chunk) => {
        sendWSMessage({
          type: 'VOICE_AUDIO',
          message_id: msgId,
          audio: base64Chunk,
        });
      });

      await recorder.start();
      recorderRef.current = recorder;
      setIsRecording(true);
    } catch (err: any) {
      console.error('Failed to start recording:', err);
      setErrorMsg(err.message || 'Microphone access denied or failed to initialize.');
      
      if (messageIdRef.current) {
        sendWSMessage({
          type: 'VOICE_CANCEL',
          message_id: messageIdRef.current,
        });
      }
    }
  };

  const stopVoiceInput = () => {
    if (recorderRef.current) {
      recorderRef.current.stop();
      recorderRef.current = null;
    }

    if (messageIdRef.current) {
      sendWSMessage({
        type: 'VOICE_END',
        message_id: messageIdRef.current,
      });
    }

    setIsRecording(false);
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopVoiceInput();
    } else {
      startVoiceInput();
    }
  };

  const pipelineSteps = [
    {
      name: 'Microphone Capture',
      desc: 'Raw browser PCM stream (16kHz 16-bit mono)',
      status: isRecording ? 'online' : 'offline',
      icon: Mic,
      color: 'text-blue-500',
    },
    {
      name: 'Speech-to-Text',
      desc: 'Local Faster-Whisper CPU transcription',
      status: voice.status === 'thinking' ? 'pending' : voice.last_transcription ? 'online' : 'offline',
      icon: Cpu,
      color: 'text-purple-500',
      output: voice.last_transcription,
    },
    {
      name: 'Intent Extraction',
      desc: 'Ollama local LLM structured JSON output',
      status: voice.intent ? 'online' : 'offline',
      icon: Zap,
      color: 'text-yellow-500',
      output: voice.intent
        ? `Intent: ${voice.intent} | Target: ${voice.target || 'N/A'} | Action: ${voice.action || 'N/A'}`
        : undefined,
    },
    {
      name: 'TTS Response Output',
      desc: 'Piper TTS audio stream relay to I2S speaker',
      status: voice.status === 'speaking' ? 'online' : 'offline',
      icon: Volume2,
      color: 'text-green-500',
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold uppercase tracking-wider text-slate-800 dark:text-slate-100">
          Voice Diagnostics Pipeline
        </h2>
        {systemStats && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-bold uppercase">TTS Engine:</span>
            <StatusBadge status={systemStats.tts_status} />
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pipeline steps trace */}
        <div className="lg:col-span-2 space-y-4">
          {pipelineSteps.map((step, idx) => {
            const Icon = step.icon;
            return (
              <Card key={idx} className="flex gap-4 items-start border border-slate-300/30">
                <div className={`p-3 rounded-xl bg-slate-200/50 dark:bg-slate-800/50 ${step.color}`}>
                  <Icon className="w-6 h-6" />
                </div>
                <div className="flex-1 space-y-1">
                  <div className="flex items-center justify-between">
                    <h3 className="font-bold text-slate-800 dark:text-slate-200">{step.name}</h3>
                    <StatusBadge status={step.status} />
                  </div>
                  <p className="text-xs text-slate-400 font-semibold">{step.desc}</p>
                  
                  {step.output && (
                    <div className="mt-3 p-3 rounded-xl bg-slate-200/30 dark:bg-slate-900/30 text-xs font-semibold text-slate-600 dark:text-slate-300 font-mono shadow-neo-sm-inset-light dark:shadow-neo-sm-inset-dark">
                      {step.output}
                    </div>
                  )}
                </div>
              </Card>
            );
          })}
        </div>

        {/* Live Controller Terminal */}
        <div className="space-y-6">
          <Card className="flex flex-col items-center justify-center text-center p-8 relative overflow-hidden border border-slate-300/30 min-h-[300px]">
            {/* Pulsating background ring when recording */}
            {isRecording && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <span className="w-40 h-40 rounded-full border-4 border-cyan-500/30 animate-ping absolute" />
                <span className="w-48 h-48 rounded-full border-2 border-cyan-500/10 animate-pulse absolute" />
              </div>
            )}

            <div className="relative z-10 space-y-6 flex flex-col items-center">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Web Voice Terminal
              </h3>

              {/* Large interactive glowing button */}
              <button
                onClick={toggleRecording}
                className={`w-28 h-28 rounded-full flex items-center justify-center shadow-lg transition-all duration-300 transform active:scale-95 ${
                  isRecording
                    ? 'bg-red-500 shadow-red-500/50 text-white animate-pulse'
                    : voice.status === 'thinking'
                    ? 'bg-yellow-500 shadow-yellow-500/50 text-white'
                    : voice.status === 'speaking'
                    ? 'bg-green-500 shadow-green-500/50 text-white'
                    : 'bg-indigo-600 hover:bg-indigo-700 shadow-indigo-600/50 text-white'
                }`}
              >
                {voice.status === 'thinking' ? (
                  <Loader2 className="w-12 h-12 animate-spin" />
                ) : isRecording ? (
                  <MicOff className="w-12 h-12" />
                ) : (
                  <Mic className="w-12 h-12" />
                )}
              </button>

              <div className="space-y-1">
                <p className="text-sm font-bold text-slate-800 dark:text-slate-200">
                  {isRecording
                    ? 'Listening... Tap to stop'
                    : voice.status === 'thinking'
                    ? 'AI is thinking...'
                    : voice.status === 'speaking'
                    ? 'JARVIS is speaking...'
                    : 'Tap to speak to JARVIS'}
                </p>
                <p className="text-xs text-slate-400 font-semibold">
                  (Voice response plays via ESP32)
                </p>
              </div>

              {errorMsg && (
                <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-xs text-red-500 font-bold max-w-[220px]">
                  {errorMsg}
                </div>
              )}
            </div>
          </Card>

          {/* Configuration Summary */}
          <Card className="flex flex-col gap-6 border border-slate-300/30">
            <div className="flex items-center gap-2 border-b border-slate-300/30 pb-3">
              <Settings className="w-5 h-5 text-indigo-500" />
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Pipeline Settings
              </h3>
            </div>

            <div className="space-y-4 text-xs font-bold text-slate-400 uppercase">
              <div className="flex justify-between">
                <span>Voice Activity Gate</span>
                <span className="text-slate-700 dark:text-slate-300">Enabled</span>
              </div>
              <div className="flex justify-between">
                <span>Silence Threshold</span>
                <span className="text-slate-700 dark:text-slate-300">1500 ms</span>
              </div>
              <div className="flex justify-between">
                <span>Privacy Mode</span>
                <span className="text-green-500">Active (No Storage)</span>
              </div>
              <div className="flex justify-between">
                <span>STT Engine</span>
                <span className="text-slate-700 dark:text-slate-300">Whisper Local CPU</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
