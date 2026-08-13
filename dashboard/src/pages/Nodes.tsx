import React, { useEffect, useState } from 'react';
import { useJarvisStore } from '../state/store';
import { api } from '../services/api';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { StatusBadge } from '../components/ui/StatusBadge';
import { EmptyState } from '../components/ui/EmptyState';
import { Plus, Trash2, Cpu, Database, HardDrive, Wifi, Edit } from 'lucide-react';

export const Nodes: React.FC = () => {
  const { nodes, rooms, fetchNodes, fetchRooms, addToast } = useJarvisStore();
  const [showAddModal, setShowAddModal] = useState(false);
  const [newNodeId, setNewNodeId] = useState('');
  const [newNodeName, setNewNodeName] = useState('');
  const [newNodeRoom, setNewNodeRoom] = useState('');
  const [newNodeMac, setNewNodeMac] = useState('');
  const [newNodeChip, setNewNodeChip] = useState('esp32s3');

  // Edit Node state
  const [editingNode, setEditingNode] = useState<any | null>(null);
  const [editName, setEditName] = useState('');
  const [editRoom, setEditRoom] = useState('');
  const [editMac, setEditMac] = useState('');
  const [editChip, setEditChip] = useState('esp32s3');

  useEffect(() => {
    fetchNodes();
    fetchRooms();
  }, []);

  const handleCreateNode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNodeRoom) {
      addToast('Please assign a room first', 'warning');
      return;
    }

    try {
      await api.nodes.create({
        id: newNodeId,
        name: newNodeName,
        room_id: newNodeRoom,
        mac_address: newNodeMac || undefined,
        chip_type: newNodeChip,
        config: {},
      });
      fetchNodes();
      setShowAddModal(false);
      setNewNodeId('');
      setNewNodeName('');
      setNewNodeMac('');
      addToast('Node added successfully', 'success');
    } catch (e: any) {
      addToast(e.message || 'Failed to add node', 'error');
    }
  };

  const handleDeleteNode = async (id: string) => {
    if (confirm('Are you sure you want to delete this node? This will remove all mapped devices.')) {
      try {
        await api.nodes.delete(id);
        fetchNodes();
        addToast('Node deleted successfully', 'success');
      } catch (e: any) {
        addToast(e.message || 'Failed to delete node', 'error');
      }
    }
  };

  const handleStartEdit = (node: any) => {
    setEditingNode(node);
    setEditName(node.name);
    setEditRoom(node.room_id || '');
    setEditMac(node.mac_address || '');
    setEditChip(node.chip_type);
  };

  const handleUpdateNode = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.nodes.update(editingNode.id, {
        name: editName,
        room_id: editRoom || null,
        mac_address: editMac || undefined,
        chip_type: editChip,
      });
      fetchNodes();
      setEditingNode(null);
      addToast('Node updated successfully', 'success');
    } catch (e: any) {
      addToast(e.message || 'Failed to update node', 'error');
    }
  };

  const getRoomName = (roomId: string) => rooms.find((r) => r.id === roomId)?.name || roomId;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold uppercase tracking-wider text-slate-800 dark:text-slate-100">
          Secondary Nodes
        </h2>
        <Button onClick={() => setShowAddModal(true)} className="flex items-center gap-1">
          <Plus className="w-4 h-4" /> Add Node
        </Button>
      </div>

      {nodes.length === 0 ? (
        <EmptyState
          title="No Nodes Registered"
          message="Smart room relays and sensor hubs communicate via physical nodes."
          actionLabel="Register Node"
          onAction={() => setShowAddModal(true)}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {nodes.map((node) => (
            <Card key={node.id} className="flex flex-col justify-between h-56">
              <div>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-3 rounded-xl bg-blue-500/10 dark:bg-blue-400/10 text-blue-500">
                      <Cpu className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="font-bold text-slate-800 dark:text-slate-100">
                        {node.name}
                      </h3>
                      <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest block">
                        Room: {getRoomName(node.room_id)}
                      </span>
                    </div>
                  </div>

                  <div className="flex gap-1">
                    <button
                      onClick={() => handleStartEdit(node)}
                      className="p-2 text-slate-400 hover:text-blue-500 transition-colors"
                      title="Edit Node"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDeleteNode(node.id)}
                      className="p-2 text-slate-400 hover:text-red-500 transition-colors"
                      title="Delete Node"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <div className="space-y-2 mt-4">
                  <div className="flex justify-between text-xs font-bold text-slate-400 uppercase">
                    <span>Chip Type</span>
                    <span className="text-slate-700 dark:text-slate-300 font-semibold">{node.chip_type}</span>
                  </div>
                  <div className="flex justify-between text-xs font-bold text-slate-400 uppercase">
                    <span>MAC Address</span>
                    <span className="text-slate-700 dark:text-slate-300 font-semibold">{node.mac_address || 'Unregistered'}</span>
                  </div>
                  <div className="flex justify-between text-xs font-bold text-slate-400 uppercase">
                    <span>Heap Free</span>
                    <span className="text-slate-700 dark:text-slate-300 font-semibold">
                      {node.status === 'online' ? `${Math.round(node.free_heap / 1024)} KB` : 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs font-bold text-slate-400 uppercase">
                    <span>Uptime</span>
                    <span className="text-slate-700 dark:text-slate-300 font-semibold">
                      {node.status === 'online' ? `${Math.round(node.uptime / 60)} mins` : 'N/A'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="border-t border-slate-300/20 dark:border-slate-800/20 pt-3 flex justify-between items-center">
                <span className="text-xs text-slate-400 font-bold uppercase">
                  Status
                </span>
                <StatusBadge status={node.status} />
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Add Node Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="card-neo max-w-md w-full p-6 flex flex-col gap-4">
            <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wider border-b pb-2">
              Add Node
            </h3>
            <form onSubmit={handleCreateNode} className="space-y-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Node ID (lowercase, alphanumeric)
                </label>
                <input
                  type="text"
                  value={newNodeId}
                  onChange={(e) => setNewNodeId(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ''))}
                  required
                  placeholder="bedroom_node_01"
                  className="input-neo"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Name
                </label>
                <input
                  type="text"
                  value={newNodeName}
                  onChange={(e) => setNewNodeName(e.target.value)}
                  required
                  placeholder="Relay Hub S3"
                  className="input-neo"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Assign Room
                </label>
                <select
                  value={newNodeRoom}
                  onChange={(e) => setNewNodeRoom(e.target.value)}
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
                  MAC Address (Optional)
                </label>
                <input
                  type="text"
                  value={newNodeMac}
                  onChange={(e) => setNewNodeMac(e.target.value)}
                  placeholder="AA:BB:CC:DD:EE:FF"
                  className="input-neo"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Chip Hardware Target
                </label>
                <select
                  value={newNodeChip}
                  onChange={(e) => setNewNodeChip(e.target.value)}
                  className="input-neo bg-transparent"
                >
                  <option value="esp32s3">ESP32-S3</option>
                  <option value="esp32">ESP32 Standard</option>
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <Button type="button" onClick={() => setShowAddModal(false)} className="btn-neo">
                  Cancel
                </Button>
                <Button type="submit" className="btn-neo bg-blue-500 text-white font-bold">
                  Add Node
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Node Modal */}
      {editingNode && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="card-neo max-w-md w-full p-6 flex flex-col gap-4">
            <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wider border-b pb-2">
              Edit Node
            </h3>
            <form onSubmit={handleUpdateNode} className="space-y-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Node ID (Read Only)
                </label>
                <input
                  type="text"
                  value={editingNode.id}
                  disabled
                  className="input-neo bg-slate-100 dark:bg-slate-800 text-slate-400 cursor-not-allowed"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Name
                </label>
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  required
                  placeholder="Relay Hub S3"
                  className="input-neo"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Assign Room
                </label>
                <select
                  value={editRoom}
                  onChange={(e) => setEditRoom(e.target.value)}
                  className="input-neo bg-transparent"
                >
                  <option value="">Unassigned</option>
                  {rooms.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  MAC Address
                </label>
                <input
                  type="text"
                  value={editMac}
                  onChange={(e) => setEditMac(e.target.value)}
                  placeholder="AA:BB:CC:DD:EE:FF"
                  className="input-neo"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Chip Hardware Target
                </label>
                <select
                  value={editChip}
                  onChange={(e) => setEditChip(e.target.value)}
                  className="input-neo bg-transparent"
                >
                  <option value="esp32s3">ESP32-S3</option>
                  <option value="esp32">ESP32 Standard</option>
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <Button type="button" onClick={() => setEditingNode(null)} className="btn-neo">
                  Cancel
                </Button>
                <Button type="submit" className="btn-neo bg-blue-500 text-white font-bold">
                  Save Changes
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
