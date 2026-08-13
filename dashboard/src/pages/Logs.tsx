import React, { useEffect, useState } from 'react';
import { useJarvisStore } from '../state/store';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { RefreshCw, Filter, ShieldAlert } from 'lucide-react';

export const Logs: React.FC = () => {
  const { events, fetchEvents } = useJarvisStore();
  const [component, setComponent] = useState('');
  const [severity, setSeverity] = useState('');
  const [messageId, setMessageId] = useState('');

  useEffect(() => {
    fetchEvents(
      component || undefined,
      severity || undefined,
      messageId || undefined,
      100
    );
  }, [component, severity, messageId]);

  const getSeverityStyle = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'error':
      case 'critical':
        return 'text-red-500';
      case 'warning':
        return 'text-yellow-500';
      case 'info':
        return 'text-blue-500';
      default:
        return 'text-slate-400';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold uppercase tracking-wider text-slate-800 dark:text-slate-100">
          Live Event Monitor
        </h2>
        <Button
          onClick={() => fetchEvents(component || undefined, severity || undefined, messageId || undefined, 100)}
          className="flex items-center gap-1.5"
        >
          <RefreshCw className="w-4 h-4" /> Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Filters Panel */}
        <Card className="flex flex-col gap-4 h-fit">
          <div className="flex items-center gap-2 border-b pb-2">
            <Filter className="w-5 h-5 text-slate-400" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              Query Filters
            </h3>
          </div>

          <div className="flex flex-col gap-3">
            <div className="flex flex-col gap-1">
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                Subsystem Component
              </label>
              <select
                value={component}
                onChange={(e) => setComponent(e.target.value)}
                className="input-neo bg-transparent"
              >
                <option value="">All Components</option>
                <option value="voice">Voice Pipeline</option>
                <option value="device">Device Registry</option>
                <option value="node">Node Gateway</option>
                <option value="music">Spotify Bridge</option>
                <option value="automation">Automations</option>
                <option value="scenes">Scenes</option>
              </select>
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                Severity Level
              </label>
              <select
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
                className="input-neo bg-transparent"
              >
                <option value="">All Levels</option>
                <option value="info">Info / Normal</option>
                <option value="warning">Warning / Alert</option>
                <option value="error">Error / Fault</option>
              </select>
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                Correlation Message ID (UUID)
              </label>
              <input
                type="text"
                value={messageId}
                onChange={(e) => setMessageId(e.target.value)}
                placeholder="uuid..."
                className="input-neo text-xs font-mono"
              />
            </div>
          </div>
        </Card>

        {/* Viewport logs terminal */}
        <Card className="lg:col-span-3 flex flex-col justify-between h-[500px] p-6 bg-slate-900 text-slate-200 border-none font-mono">
          <div className="flex-1 overflow-y-auto space-y-2 pr-2 text-xs leading-relaxed">
            {events.length === 0 ? (
              <div className="text-center text-slate-500 py-12">No event records match query.</div>
            ) : (
              events.map((e) => (
                <div key={e.id} className="hover:bg-slate-800/40 p-1.5 rounded transition-colors">
                  <span className="text-slate-500">[{new Date(e.timestamp).toLocaleTimeString()}]</span>{' '}
                  <span className={`${getSeverityStyle(e.severity)} uppercase font-bold`}>
                    [{e.severity}]
                  </span>{' '}
                  <span className="text-indigo-400 font-bold">[{e.component}]</span>{' '}
                  <span className="text-slate-300">{e.message}</span>
                  {e.message_id && (
                    <span className="text-teal-400 font-bold block text-[10px] pl-4">
                      Correlation ID: {e.message_id}
                    </span>
                  )}
                </div>
              ))
            )}
          </div>

          <div className="border-t border-slate-800 pt-4 flex gap-2 items-center text-[10px] text-slate-500 uppercase tracking-wider font-bold">
            <ShieldAlert className="w-4 h-4 shrink-0 text-slate-600" />
            <span>Sensitive tokens (passwords, secrets) are redacted prior to write.</span>
          </div>
        </Card>
      </div>
    </div>
  );
};
