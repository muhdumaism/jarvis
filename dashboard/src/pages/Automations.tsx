import React, { useEffect, useState } from 'react';
import { useJarvisStore } from '../state/store';
import { api } from '../services/api';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Toggle } from '../components/ui/Toggle';
import { EmptyState } from '../components/ui/EmptyState';
import { Plus, Trash2, Zap, Play, Check } from 'lucide-react';

export const Automations: React.FC = () => {
  const { automations, fetchAutomations, testAutomation, addToast } = useJarvisStore();
  const [showAddModal, setShowAddModal] = useState(false);
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');
  const [trigType, setTrigType] = useState('time');
  
  // Simple configurations helper state
  const [timeVal, setTimeVal] = useState('12:00');
  const [targetDevice, setTargetDevice] = useState('');
  const [targetAction, setTargetAction] = useState('turn_on');

  useEffect(() => {
    fetchAutomations();
  }, []);

  const handleCreateAuto = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetDevice) {
      addToast('Please specify a device target action first', 'warning');
      return;
    }

    const trigger_config = trigType === 'time' ? { time: timeVal } : {};

    try {
      await api.automations.create({
        name,
        description: desc,
        enabled: true,
        trigger_type: trigType,
        trigger_config,
        actions: [{ device_id: targetDevice, action: targetAction }],
        conditions: [],
        cooldown_seconds: 30,
      });
      fetchAutomations();
      setShowAddModal(false);
      setName('');
      setDesc('');
      addToast('Automation created successfully', 'success');
    } catch (e: any) {
      addToast(e.message || 'Failed to create automation', 'error');
    }
  };

  const handleDeleteAuto = async (id: number) => {
    if (confirm('Are you sure you want to delete this automation?')) {
      try {
        await api.automations.delete(id);
        fetchAutomations();
        addToast('Automation rule removed', 'success');
      } catch (e: any) {
        addToast(e.message || 'Failed to delete automation', 'error');
      }
    }
  };

  const handleToggleEnable = async (auto: any) => {
    try {
      await api.automations.update(auto.id, { enabled: !auto.enabled });
      fetchAutomations();
      addToast(`Automation ${!auto.enabled ? 'enabled' : 'disabled'}`, 'info');
    } catch (e: any) {
      addToast(e.message || 'Failed to toggle automation state', 'error');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold uppercase tracking-wider text-slate-800 dark:text-slate-100">
          Automations Log
        </h2>
        <Button onClick={() => setShowAddModal(true)} className="flex items-center gap-1">
          <Plus className="w-4 h-4" /> Add Rule
        </Button>
      </div>

      {automations.length === 0 ? (
        <EmptyState
          title="No Automations Set"
          message="Run conditional scripts (e.g. at 23:00 turn off lights)."
          actionLabel="Create Rule"
          onAction={() => setShowAddModal(true)}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {automations.map((auto) => (
            <Card key={auto.id} className="flex flex-col justify-between h-48">
              <div>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-3 rounded-xl bg-blue-500/10 dark:bg-blue-400/10 text-blue-500">
                      <Zap className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="font-bold text-slate-800 dark:text-slate-100">
                        {auto.name}
                      </h3>
                      <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                        Trigger: {auto.trigger_type}
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={() => handleDeleteAuto(auto.id)}
                    className="p-2 text-slate-400 hover:text-red-500 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-3 line-clamp-2">
                  {auto.description || 'No description.'}
                </p>
              </div>

              <div className="border-t border-slate-300/20 dark:border-slate-800/20 pt-3 flex justify-between items-center">
                <Button onClick={() => testAutomation(auto.id)} className="px-3 py-1.5 text-xs">
                  <Play className="w-3 h-3" /> Test
                </Button>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400 font-bold uppercase">
                    {auto.enabled ? 'Enabled' : 'Disabled'}
                  </span>
                  <Toggle checked={auto.enabled} onChange={() => handleToggleEnable(auto)} />
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Add Automation Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="card-neo max-w-md w-full p-6 flex flex-col gap-4">
            <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wider border-b pb-2">
              Add Automation
            </h3>
            <form onSubmit={handleCreateAuto} className="space-y-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  placeholder="Night Light Shut Off"
                  className="input-neo"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Description
                </label>
                <input
                  type="text"
                  value={desc}
                  onChange={(e) => setDesc(e.target.value)}
                  placeholder="Turns off bedroom lights at 23:00"
                  className="input-neo"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Trigger Type
                </label>
                <select
                  value={trigType}
                  onChange={(e) => setTrigType(e.target.value)}
                  className="input-neo bg-transparent"
                >
                  <option value="time">Time of Day</option>
                </select>
              </div>

              {trigType === 'time' && (
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                    Time (HH:MM format)
                  </label>
                  <input
                    type="time"
                    value={timeVal}
                    onChange={(e) => setTimeVal(e.target.value)}
                    required
                    className="input-neo"
                  />
                </div>
              )}

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Target Device ID
                </label>
                <input
                  type="text"
                  value={targetDevice}
                  onChange={(e) => setTargetDevice(e.target.value)}
                  required
                  placeholder="bedroom_light"
                  className="input-neo"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Action
                </label>
                <select
                  value={targetAction}
                  onChange={(e) => setTargetAction(e.target.value)}
                  className="input-neo bg-transparent"
                >
                  <option value="turn_on">Turn On</option>
                  <option value="turn_off">Turn Off</option>
                  <option value="toggle">Toggle</option>
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <Button type="button" onClick={() => setShowAddModal(false)} className="btn-neo">
                  Cancel
                </Button>
                <Button type="submit" className="btn-neo bg-blue-500 text-white font-bold">
                  Create Rule
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
