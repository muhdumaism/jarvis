import React from 'react';
import { useJarvisStore } from '../state/store';
import { Card } from '../components/ui/Card';
import { Mic, Cpu, Zap, Volume2, Settings } from 'lucide-react';
import { StatusBadge } from '../components/ui/StatusBadge';

export const Voice: React.FC = () => {
  const { voice, systemStats } = useJarvisStore();

  const pipelineSteps = [
    {
      name: 'Microphone Capture',
      desc: 'Raw I2S PCM audio stream (16kHz 16-bit)',
      status: voice.status === 'listening' ? 'online' : 'offline',
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
      desc: 'Piper TTS audio stream relay to I2S',
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
              <Card key={idx} className="flex gap-4 items-start">
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

        {/* Energy bar and config notes */}
        <Card className="flex flex-col gap-6">
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
  );
};
