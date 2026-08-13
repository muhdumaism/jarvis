import React, { useEffect, useState } from 'react';
import { useJarvisStore } from '../state/store';
import { api } from '../services/api';
import { Card } from '../components/ui/Card';
import { Toggle } from '../components/ui/Toggle';
import { Button } from '../components/ui/Button';
import { StatusBadge } from '../components/ui/StatusBadge';
import { EmptyState } from '../components/ui/EmptyState';
import { Plus, Trash2, Sliders, Layers } from 'lucide-react';

export const Devices: React.FC = () => {
  const {
    devices,
    rooms,
    nodes,
    fetchDevices,
    fetchRooms,
    fetchNodes,
    controlDevice,
    addToast,
  } = useJarvisStore();

  const [showAddModal, setShowAddModal] = useState(false);
  const [newDevId, setNewDevId] = useState('');
  const [newDevName, setNewDevName] = useState('');
  const [newDevRoom, setNewDevRoom] = useState('');
  const [newDevNode, setNewDevNode] = useState('');
  const [newDevChannel, setNewDevChannel] = useState(0);

  useEffect(() => {
    fetchDevices();
    fetchRooms();
    fetchNodes();
  }, []);

  const handleCreateDevice = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDevRoom || !newDevNode) {
      addToast('Please assign room and target node first', 'warning');
      return;
    }

    try {
      await api.devices.create({
        id: newDevId,
        name: newDevName,
        room_id: newDevRoom,
        node_id: newDevNode,
        type: 'relay',
        channel: newDevChannel,
        capabilities: ['on', 'off', 'toggle'],
      });
      fetchDevices();
      setShowAddModal(false);
      setNewDevId('');
      setNewDevName('');
      addToast('Device registered successfully', 'success');
    } catch (e: any) {
      addToast(e.message || 'Failed to create device', 'error');
    }
  };

  const handleDeleteDevice = async (id: string) => {
    if (confirm('Are you sure you want to delete this device?')) {
      try {
        await api.devices.delete(id);
        fetchDevices();
        addToast('Device removed from registry', 'success');
      } catch (e: any) {
        addToast(e.message || 'Failed to delete device', 'error');
      }
    }
  };

  // Find room and node names for displays
  const getRoomName = (roomId: string) => rooms.find((r) => r.id === roomId)?.name || roomId;
  const isNodeOnline = (nodeId: string) => nodes.find((n) => n.id === nodeId)?.status === 'online';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold uppercase tracking-wider text-slate-800 dark:text-slate-100">
          Devices Registry
        </h2>
        <Button onClick={() => setShowAddModal(true)} className="flex items-center gap-1">
          <Plus className="w-4 h-4" /> Add Device
        </Button>
      </div>

      {devices.length === 0 ? (
        <EmptyState
          title="No Devices Found"
          message="Get started by registering a new smart device module."
          actionLabel="Register Device"
          onAction={() => setShowAddModal(true)}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {devices.map((device) => {
            const online = isNodeOnline(device.node_id);
            const isPending = device.state.startsWith('pending');
            const isOn = device.state === 'on';

            return (
              <Card key={device.id} className="relative flex flex-col justify-between h-40">
                <div>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-3 rounded-xl bg-blue-500/10 dark:bg-blue-400/10 text-blue-500">
                        <Sliders className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="font-bold text-slate-800 dark:text-slate-100">
                          {device.name}
                        </h3>
                        <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest block">
                          Room: {getRoomName(device.room_id)}
                        </span>
                      </div>
                    </div>

                    <button
                      onClick={() => handleDeleteDevice(device.id)}
                      className="p-2 text-slate-400 hover:text-red-500 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  
                  <div className="flex items-center gap-2 mt-3">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                      Node: {device.node_id} (CH: {device.channel})
                    </span>
                    <StatusBadge status={online ? (isPending ? 'pending' : device.state) : 'offline'} />
                  </div>
                </div>

                <div className="border-t border-slate-300/20 dark:border-slate-800/20 pt-3 flex justify-between items-center">
                  <span className="text-xs text-slate-400 font-bold uppercase tracking-wider">
                    Relay State
                  </span>
                  <Toggle
                    checked={isOn}
                    disabled={!online || isPending}
                    onChange={(checked) =>
                      controlDevice(device.id, checked ? 'turn_on' : 'turn_off')
                    }
                  />
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Add Device Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="card-neo max-w-md w-full p-6 flex flex-col gap-4">
            <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wider border-b pb-2">
              Add Device
            </h3>
            <form onSubmit={handleCreateDevice} className="space-y-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Device ID (lowercase, alphanumeric)
                </label>
                <input
                  type="text"
                  value={newDevId}
                  onChange={(e) => setNewDevId(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ''))}
                  required
                  placeholder="bedroom_light"
                  className="input-neo"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Name
                </label>
                <input
                  type="text"
                  value={newDevName}
                  onChange={(e) => setNewDevName(e.target.value)}
                  required
                  placeholder="Overhead Light"
                  className="input-neo"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Assign Room
                </label>
                <select
                  value={newDevRoom}
                  onChange={(e) => setNewDevRoom(e.target.value)}
                  required
                  className="input-neo bg-transparent"
                >
                  <option value="">Select Room...</option>
                  {rooms.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Assign Node
                </label>
                <select
                  value={newDevNode}
                  onChange={(e) => setNewDevNode(e.target.value)}
                  required
                  className="input-neo bg-transparent"
                >
                  <option value="">Select Node...</option>
                  {nodes.map((n) => (
                    <option key={n.id} value={n.id}>
                      {n.name} ({n.id})
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Relay Node Channel (0 to 7)
                </label>
                <input
                  type="number"
                  min="0"
                  max="7"
                  value={newDevChannel}
                  onChange={(e) => setNewDevChannel(parseInt(e.target.value) || 0)}
                  className="input-neo"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <Button type="button" onClick={() => setShowAddModal(false)} className="btn-neo">
                  Cancel
                </Button>
                <Button type="submit" className="btn-neo bg-blue-500 text-white font-bold">
                  Add Device
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
