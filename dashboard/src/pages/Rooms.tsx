import React, { useEffect, useState } from 'react';
import { useJarvisStore } from '../state/store';
import { api } from '../services/api';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { EmptyState } from '../components/ui/EmptyState';
import { Plus, Trash2, Home, Bed, Tv, ShieldAlert } from 'lucide-react';

export const Rooms: React.FC = () => {
  const { rooms, fetchRooms, devices, fetchDevices, addToast } = useJarvisStore();
  const [showAddModal, setShowAddModal] = useState(false);
  const [newRoomId, setNewRoomId] = useState('');
  const [newRoomName, setNewRoomName] = useState('');
  const [newRoomDesc, setNewRoomDesc] = useState('');
  const [newRoomIcon, setNewRoomIcon] = useState('home');

  useEffect(() => {
    fetchRooms();
    fetchDevices();
  }, []);

  const handleAddRoom = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.rooms.create({
        id: newRoomId,
        name: newRoomName,
        description: newRoomDesc,
        icon: newRoomIcon,
        order: rooms.length,
      });
      fetchRooms();
      setShowAddModal(false);
      setNewRoomId('');
      setNewRoomName('');
      setNewRoomDesc('');
      addToast('Room created successfully', 'success');
    } catch (e: any) {
      addToast(e.message || 'Failed to create room', 'error');
    }
  };

  const handleDeleteRoom = async (id: string) => {
    if (confirm('Are you sure you want to delete this room? This will delete all devices inside it.')) {
      try {
        await api.rooms.delete(id);
        fetchRooms();
        fetchDevices();
        addToast('Room deleted successfully', 'success');
      } catch (e: any) {
        addToast(e.message || 'Failed to delete room', 'error');
      }
    }
  };

  const getDevicesForRoom = (roomId: string) => {
    return devices.filter((d) => d.room_id === roomId);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold uppercase tracking-wider text-slate-800 dark:text-slate-100">
          Rooms Registry
        </h2>
        <Button onClick={() => setShowAddModal(true)} className="flex items-center gap-1">
          <Plus className="w-4 h-4" /> Add Room
        </Button>
      </div>

      {rooms.length === 0 ? (
        <EmptyState
          title="No Rooms Configured"
          message="Get started by creating your first room."
          actionLabel="Create Room"
          onAction={() => setShowAddModal(true)}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {rooms.map((room) => {
            const roomDevices = getDevicesForRoom(room.id);
            return (
              <Card key={room.id} className="flex flex-col justify-between h-48">
                <div>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-3 rounded-xl bg-blue-500/10 dark:bg-blue-400/10 text-blue-500">
                        {room.icon === 'bed' ? (
                          <Bed className="w-5 h-5" />
                        ) : room.icon === 'tv' ? (
                          <Tv className="w-5 h-5" />
                        ) : (
                          <Home className="w-5 h-5" />
                        )}
                      </div>
                      <div>
                        <h3 className="font-bold text-slate-800 dark:text-slate-100">
                          {room.name}
                        </h3>
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">
                          ID: {room.id}
                        </span>
                      </div>
                    </div>

                    <button
                      onClick={() => handleDeleteRoom(room.id)}
                      className="p-2 text-slate-400 hover:text-red-500 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-3 line-clamp-2">
                    {room.description || 'No description provided.'}
                  </p>
                </div>

                <div className="border-t border-slate-300/20 dark:border-slate-800/20 pt-3 flex justify-between items-center text-xs font-bold text-slate-400 uppercase tracking-wider">
                  <span>Devices: {roomDevices.length}</span>
                  <span className="text-green-500">
                    Active: {roomDevices.filter((d) => d.state === 'on' && d.confirmed).length}
                  </span>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Add Room Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="card-neo max-w-md w-full p-6 flex flex-col gap-4">
            <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wider border-b pb-2">
              Create Room
            </h3>
            <form onSubmit={handleAddRoom} className="space-y-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Room ID (lowercase, alphanumeric)
                </label>
                <input
                  type="text"
                  value={newRoomId}
                  onChange={(e) => setNewRoomId(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ''))}
                  required
                  placeholder="bedroom_main"
                  className="input-neo"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Name
                </label>
                <input
                  type="text"
                  value={newRoomName}
                  onChange={(e) => setNewRoomName(e.target.value)}
                  required
                  placeholder="Main Bedroom"
                  className="input-neo"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Description
                </label>
                <input
                  type="text"
                  value={newRoomDesc}
                  onChange={(e) => setNewRoomDesc(e.target.value)}
                  placeholder="Relay and light switches for primary bedroom."
                  className="input-neo"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Icon Style
                </label>
                <select
                  value={newRoomIcon}
                  onChange={(e) => setNewRoomIcon(e.target.value)}
                  className="input-neo bg-transparent"
                >
                  <option value="home">Home / Default</option>
                  <option value="bed">Bedroom</option>
                  <option value="tv">Living Room / TV</option>
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <Button type="button" onClick={() => setShowAddModal(false)} className="btn-neo">
                  Cancel
                </Button>
                <Button type="submit" className="btn-neo bg-blue-500 text-white font-bold">
                  Create Room
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
