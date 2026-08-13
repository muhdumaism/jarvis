import React, { useState } from 'react';
import { Card } from '../components/ui/Card';
import { FileCode, ShieldAlert, Cpu } from 'lucide-react';

interface DiagramDetails {
  title: string;
  pins: Record<string, string>;
  notes: string;
}

const diagramsList: DiagramDetails[] = [
  {
    title: 'Main ESP32 + TFT Display',
    pins: {
      'TFT VCC': '3.3V',
      'TFT GND': 'GND',
      'TFT CS': 'GPIO 15',
      'TFT RESET': 'GPIO 4',
      'TFT D/C': 'GPIO 2',
      'TFT MOSI': 'GPIO 13',
      'TFT SCK': 'GPIO 14',
      'TFT LED': 'GPIO 27 (PWM)',
    },
    notes: 'Uses hardware HSPI bus on ESP32 WROOM-32. Do not use standard VSPI to avoid conflicts.',
  },
  {
    title: 'Main ESP32 + INMP441 Mic',
    pins: {
      'MIC VDD': '3.3V',
      'MIC GND': 'GND',
      'MIC L/R': 'GND (Left Channel)',
      'MIC BCLK': 'GPIO 26',
      'MIC WS': 'GPIO 25',
      'MIC SD': 'GPIO 33 (Data Input)',
    },
    notes: 'INMP441 is a digital I2S microphone. Do NOT connect SD to analog inputs.',
  },
  {
    title: 'Main ESP32 + I2S Amplifier',
    pins: {
      'AMP VCC': '5V (External)',
      'AMP GND': 'GND',
      'AMP BCLK': 'GPIO 22',
      'AMP LRC': 'GPIO 21 (WS)',
      'AMP DIN': 'GPIO 23 (Data Output)',
      'AMP SD': 'GPIO 19 (Shutdown/Enable)',
    },
    notes: 'Verify amplifier chip specifications before final wiring. SD pin controls sleep state.',
  },
  {
    title: 'Secondary Node ESP32-S3 + Relays',
    pins: {
      'Relay 1': 'GPIO 4',
      'Relay 2': 'GPIO 5',
      'Relay VCC': '5V',
      'Relay GND': 'GND',
    },
    notes: 'Relay board logic must be configured in config.h as ACTIVE_LOW or ACTIVE_HIGH.',
  },
];

export const Circuits: React.FC = () => {
  const [selected, setSelected] = useState<DiagramDetails>(diagramsList[0]);

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold uppercase tracking-wider text-slate-800 dark:text-slate-100">
        Circuit Wiring Pinouts
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Selector side */}
        <div className="lg:col-span-1 space-y-3">
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest px-2">
            Select Wiring Setup
          </p>
          {diagramsList.map((d) => (
            <button
              key={d.title}
              onClick={() => setSelected(d)}
              className={`w-full text-left p-4 rounded-xl border-none outline-none text-xs transition-all duration-200 active:scale-95 flex items-center gap-3 ${
                selected.title === d.title
                  ? 'shadow-neo-sm-inset-light dark:shadow-neo-sm-inset-dark text-blue-500 font-bold'
                  : 'bg-bg-light dark:bg-bg-dark text-slate-600 dark:text-slate-400 shadow-neo-sm-light dark:shadow-neo-sm-dark'
              }`}
            >
              <Cpu className="w-4 h-4 shrink-0" />
              <span>{d.title}</span>
            </button>
          ))}
        </div>

        {/* Viewport side */}
        <Card className="lg:col-span-2 space-y-6">
          <div>
            <h3 className="text-lg font-bold text-slate-800 dark:text-slate-200">
              {selected.title}
            </h3>
            <p className="text-xs text-slate-400 font-semibold mt-1">
              Wiring connections mapping table matching physical firmware config.
            </p>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-300/30 dark:border-slate-800/30 shadow-neo-sm-inset-light dark:shadow-neo-sm-inset-dark p-4">
            <table className="min-w-full text-left text-xs font-bold">
              <thead className="border-b border-slate-300/30 dark:border-slate-800/30 text-slate-400 uppercase tracking-wider">
                <tr>
                  <th className="py-2.5 px-4">Component Pin</th>
                  <th className="py-2.5 px-4">ESP32 GPIO Connection</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-300/20 dark:divide-slate-800/20 text-slate-700 dark:text-slate-300 font-mono">
                {Object.entries(selected.pins).map(([compPin, espPin]) => (
                  <tr key={compPin}>
                    <td className="py-3 px-4">{compPin}</td>
                    <td className="py-3 px-4 text-blue-500">{espPin}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex gap-3 p-4 rounded-xl bg-blue-100 dark:bg-blue-950/40 border border-blue-200/50 dark:border-blue-900/30 text-xs text-blue-700 dark:text-blue-400 leading-relaxed font-semibold">
            <ShieldAlert className="w-5 h-5 shrink-0" />
            <div>
              <p className="font-bold uppercase tracking-wider">Flashing Checklist Note</p>
              <p className="mt-0.5">{selected.notes}</p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
