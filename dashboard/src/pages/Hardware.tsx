import React, { useState } from 'react';
import { Card } from '../components/ui/Card';
import { Cpu, Mic, Volume2, ToggleRight, HelpCircle, AlertTriangle } from 'lucide-react';

interface BOMItem {
  name: string;
  purpose: string;
  voltage: string;
  pins: string;
  safety: string;
}

const mainBOM: BOMItem[] = [
  {
    name: 'ESP32 WROOM 32',
    purpose: 'Main unit CPU & WS Gateway receiver',
    voltage: '5V (micro USB) or 3.3V',
    pins: 'Refer to config.h allocation',
    safety: 'Verify strapping pins logic during flashing.',
  },
  {
    name: 'INMP441 I2S Microphone',
    purpose: 'Digital voice capture mic module',
    voltage: '3.3V only',
    pins: 'BCLK=26, WS=25, DATA=33',
    safety: 'Do NOT feed 5V. Sensitive MEMS component.',
  },
  {
    name: 'I2S Audio Amplifier Breakout',
    purpose: 'Speaker digital audio DAC & Amp',
    voltage: '2.5V - 5.5V',
    pins: 'BCLK=22, WS=21, DOUT=23, SD=19',
    safety: 'Verify output speaker impedance compatibility.',
  },
  {
    name: '2.8-inch TFT Display',
    purpose: 'Eyes visual interface display panel',
    voltage: '3.3V',
    pins: 'CS=15, DC=2, RST=4, MOSI=13, CLK=14',
    safety: 'Ensure proper LED backlight current limiting.',
  },
];

const nodeBOM: BOMItem[] = [
  {
    name: 'ESP32-S3',
    purpose: 'Secondary room relay nodes CPU',
    voltage: '5V or 3.3V',
    pins: 'Relay 1=4, Relay 2=5',
    safety: 'Boot-safe check: keep all relays off at boot.',
  },
  {
    name: '2-Channel Relay Module',
    purpose: 'Controls AC/DC appliances (lights/fan)',
    voltage: '5V (VCC logic)',
    pins: 'Relay IN1=4, IN2=5',
    safety: 'AC Mains wiring is highly dangerous! Isolate high voltages.',
  },
];

export const Hardware: React.FC = () => {
  const [selectedPart, setSelectedPart] = useState<BOMItem | null>(mainBOM[0]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold uppercase tracking-wider text-slate-800 dark:text-slate-100">
          Hardware Architecture & BOM
        </h2>
      </div>

      {/* Safety Banner */}
      <div className="flex gap-4 p-4 rounded-2xl bg-red-100 dark:bg-red-950/40 border border-red-200/50 dark:border-red-900/30 text-xs text-red-700 dark:text-red-400 font-semibold leading-relaxed">
        <AlertTriangle className="w-6 h-6 shrink-0 text-red-500 animate-pulse" />
        <div>
          <p className="font-bold uppercase tracking-wide text-sm">Critical Safety Warning</p>
          <p className="mt-1">
            MAINS AC IS DANGEROUS. Do not experiment with exposed wires on a breadboard. Ensure
            all mains connections use properly rated terminal boxes, strain relief, and fuses.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Component click grid */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="space-y-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 border-b pb-2">
              BOM Interactive Selector
            </h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                  Main Gateway Assistant (WROOM-32)
                </p>
                {mainBOM.map((part) => (
                  <button
                    key={part.name}
                    onClick={() => setSelectedPart(part)}
                    className={`w-full text-left p-3.5 rounded-xl border-none outline-none text-xs transition-all duration-200 active:scale-95 ${
                      selectedPart?.name === part.name
                        ? 'shadow-neo-sm-inset-light dark:shadow-neo-sm-inset-dark text-blue-500 font-bold'
                        : 'bg-bg-light dark:bg-bg-dark text-slate-600 dark:text-slate-400 shadow-neo-sm-light dark:shadow-neo-sm-dark'
                    }`}
                  >
                    {part.name}
                  </button>
                ))}
              </div>

              <div className="space-y-2">
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                  Secondary Node (ESP32-S3)
                </p>
                {nodeBOM.map((part) => (
                  <button
                    key={part.name}
                    onClick={() => setSelectedPart(part)}
                    className={`w-full text-left p-3.5 rounded-xl border-none outline-none text-xs transition-all duration-200 active:scale-95 ${
                      selectedPart?.name === part.name
                        ? 'shadow-neo-sm-inset-light dark:shadow-neo-sm-inset-dark text-blue-500 font-bold'
                        : 'bg-bg-light dark:bg-bg-dark text-slate-600 dark:text-slate-400 shadow-neo-sm-light dark:shadow-neo-sm-dark'
                    }`}
                  >
                    {part.name}
                  </button>
                ))}
              </div>
            </div>
          </Card>
        </div>

        {/* Highlight Panel */}
        <Card className="flex flex-col justify-between p-6">
          {selectedPart ? (
            <div className="space-y-4">
              <h3 className="text-sm font-bold uppercase tracking-wider text-blue-500 border-b pb-2">
                {selectedPart.name}
              </h3>
              
              <div className="space-y-3 text-xs">
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase block">Purpose</span>
                  <p className="font-semibold text-slate-700 dark:text-slate-300 mt-0.5">{selectedPart.purpose}</p>
                </div>
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase block">Working Voltage</span>
                  <p className="font-semibold text-slate-700 dark:text-slate-300 mt-0.5">{selectedPart.voltage}</p>
                </div>
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase block">GPIO Allocation</span>
                  <p className="font-mono text-slate-700 dark:text-slate-300 mt-0.5">{selectedPart.pins}</p>
                </div>
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase block text-yellow-500">Safety Notes</span>
                  <p className="font-semibold text-slate-700 dark:text-slate-300 mt-0.5 leading-relaxed">{selectedPart.safety}</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center text-slate-400 text-xs py-12">
              Select a part on the left to review documentation.
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};
