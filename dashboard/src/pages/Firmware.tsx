import React, { useEffect, useState } from 'react';
import { useJarvisStore } from '../state/store';
import { api } from '../services/api';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { StatusBadge } from '../components/ui/StatusBadge';
import { EmptyState } from '../components/ui/EmptyState';
import { Upload, Cpu, FileCode, CheckCircle, ShieldAlert } from 'lucide-react';

export const Firmware: React.FC = () => {
  const { firmwares, fetchFirmwares, addToast } = useJarvisStore();
  const [file, setFile] = useState<File | null>(null);
  const [version, setVersion] = useState('');
  const [chip, setChip] = useState('esp32s3');
  const [target, setTarget] = useState('node');
  const [desc, setDesc] = useState('');
  const [uploading, setUploading] = useState(false);
  
  // Web Serial availability check
  const [serialSupported, setSerialSupported] = useState(false);

  useEffect(() => {
    fetchFirmwares();
    if ('serial' in navigator) {
      setSerialSupported(true);
    }
  }, []);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      addToast('Please select a compiled .bin file', 'warning');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('version', version);
    formData.append('chip_type', chip);
    formData.append('target', target);
    formData.append('description', desc);

    try {
      await api.firmware.upload(formData);
      fetchFirmwares();
      setFile(null);
      setVersion('');
      setDesc('');
      addToast('Firmware registered successfully', 'success');
    } catch (e: any) {
      addToast(e.message || 'Failed to upload firmware', 'error');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (confirm('Are you sure you want to delete this firmware version?')) {
      try {
        await api.firmware.delete(id);
        fetchFirmwares();
        addToast('Firmware binary removed', 'success');
      } catch (e: any) {
        addToast(e.message || 'Failed to delete firmware', 'error');
      }
    }
  };

  const handleWebSerialFlash = async () => {
    addToast('Requesting connection to USB COM port...', 'info');
    try {
      // Prompt user to select port
      const port = await (navigator as any).serial.requestPort();
      await port.open({ baudRate: 115200 });
      addToast('Serial port opened. Ready to flash. Trigger local script fallback for flashing.', 'success');
      await port.close();
    } catch (err: any) {
      addToast(`USB Serial Connection Failed: ${err.message}`, 'error');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold uppercase tracking-wider text-slate-800 dark:text-slate-100">
          Firmware Management
        </h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Form */}
        <Card className="flex flex-col gap-4">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 border-b pb-2">
            Upload Compiled Binary
          </h3>
          <form onSubmit={handleUpload} className="space-y-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                Binary File (.bin)
              </label>
              <input
                type="file"
                accept=".bin"
                required
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="text-xs text-slate-500 font-bold"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                Version (e.g. 1.0.0)
              </label>
              <input
                type="text"
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                required
                placeholder="1.0.1"
                className="input-neo"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                Hardware Chip Target
              </label>
              <select
                value={chip}
                onChange={(e) => setChip(e.target.value)}
                className="input-neo bg-transparent"
              >
                <option value="esp32s3">ESP32-S3</option>
                <option value="esp32">ESP32</option>
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                Functional Target
              </label>
              <select
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                className="input-neo bg-transparent"
              >
                <option value="node">Secondary Node</option>
                <option value="main">Main Gateway Assistant</option>
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold uppercase tracking-widest text-slate-400">
                Release Notes
              </label>
              <input
                type="text"
                value={desc}
                onChange={(e) => setDesc(e.target.value)}
                placeholder="Bug fixes for relay activation glitches"
                className="input-neo"
              />
            </div>

            <Button
              type="submit"
              disabled={uploading}
              className="w-full bg-blue-500 text-white font-bold"
            >
              <Upload className="w-4 h-4" /> {uploading ? 'Uploading...' : 'Publish Update'}
            </Button>
          </form>
        </Card>

        {/* Firmware list & Web Serial Flashing */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="space-y-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 border-b pb-2">
              USB Serial Flasher Tool
            </h3>

            {serialSupported ? (
              <div className="space-y-4">
                <p className="text-xs text-slate-400 font-semibold leading-relaxed">
                  Web Serial API is available in this browser. Connect your ESP32 device via USB,
                  select a firmware binary download below, and click flash.
                </p>
                <Button
                  onClick={handleWebSerialFlash}
                  className="bg-green-600 text-white font-bold"
                >
                  <Cpu className="w-4 h-4" /> Initialize Flash Connection
                </Button>
              </div>
            ) : (
              <div className="flex items-start gap-3 p-4 rounded-xl bg-yellow-100 dark:bg-yellow-950/40 border border-yellow-200/50 dark:border-yellow-900/30 text-xs text-yellow-700 dark:text-yellow-400 leading-relaxed font-semibold">
                <ShieldAlert className="w-5 h-5 shrink-0" />
                <div>
                  <p className="font-bold">USB Flashing Unavailable in this Browser</p>
                  <p className="mt-1">
                    USB flashing is unavailable in this browser/device. Use a supported Chromium
                    desktop browser or the documented CLI fallback in docs/DEPLOYMENT.md.
                  </p>
                </div>
              </div>
            )}
          </Card>

          <Card className="space-y-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 border-b pb-2">
              Published Binaries
            </h3>
            {firmwares.length === 0 ? (
              <div className="text-center text-xs text-slate-400 py-6">
                No firmware binaries uploaded yet.
              </div>
            ) : (
              <div className="divide-y divide-slate-300/20 dark:divide-slate-800/20">
                {firmwares.map((f) => (
                  <div key={f.id} className="py-3 flex justify-between items-center text-xs">
                    <div>
                      <p className="font-bold text-slate-700 dark:text-slate-300">
                        {f.filename} (v{f.version})
                      </p>
                      <p className="text-[10px] text-slate-400 font-semibold mt-0.5">
                        Target: {f.target.toUpperCase()} | Chip: {f.chip_type.toUpperCase()}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <a
                        href={api.firmware.downloadUrl(f.id)}
                        className="btn-neo text-xs px-3 py-1 bg-blue-500/10 text-blue-500"
                      >
                        Download
                      </a>
                      <Button onClick={() => handleDelete(f.id)} className="btn-neo-danger text-xs px-3 py-1">
                        Delete
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};
