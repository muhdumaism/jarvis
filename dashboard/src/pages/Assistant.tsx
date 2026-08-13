import React, { useEffect, useState } from 'react';
import { useJarvisStore } from '../state/store';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { MessageSquare, Send, Bot, User } from 'lucide-react';

interface LocalMessage {
  sender: 'user' | 'jarvis';
  text: string;
  timestamp: Date;
}

export const Assistant: React.FC = () => {
  const { voice, fetchEvents, events } = useJarvisStore();
  const [chatLog, setChatLog] = useState<LocalMessage[]>([
    {
      sender: 'jarvis',
      text: 'Hello! I am JARVIS, your room assistant. How can I help you control your room today?',
      timestamp: new Date(),
    },
  ]);

  // Poll database event logs for recent voice transcibed & response text
  useEffect(() => {
    fetchEvents('voice', undefined, undefined, 20);
  }, []);

  useEffect(() => {
    // Reconstruct conversation from event logs
    const voiceEvents = events
      .filter((e) => e.event_type === 'VOICE_TRANSCRIBED' || e.event_type === 'ASSISTANT_RESPONSE')
      .reverse();

    const messages: LocalMessage[] = [
      {
        sender: 'jarvis',
        text: 'Hello! I am JARVIS, your room assistant. How can I help you control your room today?',
        timestamp: new Date(Date.now() - 10000),
      },
    ];

    voiceEvents.forEach((e) => {
      if (e.event_type === 'VOICE_TRANSCRIBED') {
        messages.push({
          sender: 'user',
          text: e.message,
          timestamp: new Date(e.timestamp),
        });
      } else if (e.event_type === 'ASSISTANT_RESPONSE') {
        messages.push({
          sender: 'jarvis',
          text: e.message,
          timestamp: new Date(e.timestamp),
        });
      }
    });

    setChatLog(messages);
  }, [events]);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Bot className="w-6 h-6 text-blue-500" />
        <h2 className="text-xl font-bold uppercase tracking-wider text-slate-800 dark:text-slate-100">
          Assistant Interaction Log
        </h2>
      </div>

      <Card className="flex flex-col h-[500px] p-6 justify-between">
        {/* Chat message history viewport */}
        <div className="flex-1 overflow-y-auto space-y-4 pr-2">
          {chatLog.map((msg, idx) => {
            const isJarvis = msg.sender === 'jarvis';
            return (
              <div
                key={idx}
                className={`flex gap-3 max-w-[80%] ${isJarvis ? 'mr-auto' : 'ml-auto flex-row-reverse'}`}
              >
                <div
                  className={`p-3 rounded-full shrink-0 flex items-center justify-center h-10 w-10 ${
                    isJarvis
                      ? 'bg-blue-500/10 dark:bg-blue-400/10 text-blue-500 shadow-neo-sm-light dark:shadow-neo-sm-dark'
                      : 'bg-indigo-500/10 dark:bg-indigo-400/10 text-indigo-500 shadow-neo-sm-light dark:shadow-neo-sm-dark'
                  }`}
                >
                  {isJarvis ? <Bot className="w-5 h-5" /> : <User className="w-5 h-5" />}
                </div>

                <div
                  className={`p-4 rounded-2xl text-sm ${
                    isJarvis
                      ? 'bg-bg-light dark:bg-bg-dark text-slate-800 dark:text-slate-200 shadow-neo-sm-inset-light dark:shadow-neo-sm-inset-dark'
                      : 'bg-gradient-to-r from-blue-500 to-indigo-500 text-white shadow-neo-sm-light dark:shadow-neo-sm-dark'
                  }`}
                >
                  <p>{msg.text}</p>
                  <span
                    className={`text-[9px] font-bold mt-1 block text-right leading-none ${
                      isJarvis ? 'text-slate-400' : 'text-blue-100'
                    }`}
                  >
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Status overlay */}
        <div className="border-t border-slate-300/20 dark:border-slate-800/20 pt-4 flex items-center justify-between text-xs text-slate-400 uppercase tracking-widest font-bold">
          <span>Active State: {voice.status}</span>
          {voice.status === 'listening' && (
            <span className="text-blue-500 animate-pulse">Streaming Audio...</span>
          )}
          {voice.status === 'thinking' && (
            <span className="text-indigo-500 animate-pulse">Extracting Intent...</span>
          )}
        </div>
      </Card>
    </div>
  );
};
