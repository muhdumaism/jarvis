import React, { useEffect, useState } from 'react';
import { useJarvisStore } from '../state/store';
import { api } from '../services/api';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { EmptyState } from '../components/ui/EmptyState';
import { Plus, Trash2, Layers, Play } from 'lucide-react';

export const Scenes: React.FC = () => {
  const { scenes, fetchScenes, activateScene, addToast } = useJarvisStore();
  const [showAddModal, setShowAddModal] = useState(false);
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');
  
  // Custom simple action helpers
  const [devId, setDevId] = useState('');
  const [devAction, setDevAction] = useState('turn_on');

  useEffect(() => {
    fetchScenes();
  }, []);

  const handleCreateScene = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!devId) {
      addToast('A scene requires at least one action step', 'warning');
      return;
    }

    try {
      await api.scenes.create({
        name,
        description: desc,
        icon: 'layers',
        actions: [
          {
            order: 0,
            action_type: 'device_control',
            target: devId,
            action: devAction,
            parameters: {},
          },
        ],
      });
      fetchScenes();
      setShowAddModal(false);
      setName('');
      setDesc('');
      setDevId('');
      addToast('Scene created successfully', 'success');
    } catch (e: any) {
      addToast(e.message || 'Failed to create scene', 'error');
    }
  };

  const handleDeleteScene = async (id: number) => {
    if (confirm('Are you sure you want to delete this scene?')) {
      try {
        await api.scenes.delete(id);
        fetchScenes();
        addToast('Scene configuration deleted', 'success');
      } catch (e: any) {
        addToast(e.message || 'Failed to delete scene', 'error');
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold uppercase tracking-wider text-slate-800 dark:text-slate-100">
          Smart Scenes
        </h2>
        <Button onClick={() => setShowAddModal(true)} className="flex items-center gap-1">
          <Plus className="w-4 h-4" /> Add Scene
        </Button>
      </div>

      {scenes.length === 0 ? (
        <EmptyState
          title="No Scenes Active"
          message="Activate multiple device states instantly with one click."
          actionLabel="Create Scene"
          onAction={() => setShowAddModal(true)}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {scenes.map((scene) => (
            <Card key={scene.id} className="flex flex-col justify-between h-48">
              <div>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-3 rounded-xl bg-blue-500/10 dark:bg-blue-400/10 text-blue-500">
                      <Layers className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="font-bold text-slate-800 dark:text-slate-100">
                        {scene.name}
                      </h3>
                      <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">
                        Steps: {scene.actions?.length || 0}
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={() => handleDeleteScene(scene.id)}
                    className="p-2 text-slate-400 hover:text-red-500 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-3 line-clamp-2">
                  {scene.description || 'No description provided.'}
                </p>
              </div>

              <div className="border-t border-slate-300/20 dark:border-slate-800/20 pt-3 flex justify-end">
                <Button
                  onClick={() => activateScene(scene.id)}
                  className="flex items-center gap-1 text-xs px-4 py-2 font-bold uppercase text-blue-500"
                >
                  <Play className="w-3.5 h-3.5" /> Run Scene
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Add Scene Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="card-neo max-w-md w-full p-6 flex flex-col gap-4">
            <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wider border-b pb-2">
              Create Scene
            </h3>
            <form onSubmit={handleCreateScene} className="space-y-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Scene Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  placeholder="Movie Time"
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
                  placeholder="Dim lights and turn on speaker system"
                  className="input-neo"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Action 1: Target Device ID
                </label>
                <input
                  type="text"
                  value={devId}
                  onChange={(e) => setDevId(e.target.value)}
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
                  value={devAction}
                  onChange={(e) => setDevAction(e.target.value)}
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
                  Create Scene
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
