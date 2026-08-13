import React from 'react';
import { useJarvisStore } from '../../state/store';
import { useTheme } from '../../hooks/useTheme';
import { Sun, Moon, Wifi, WifiOff, Cpu, RefreshCw, Menu, X } from 'lucide-react';
import { StatusBadge } from '../ui/StatusBadge';

interface HeaderProps {
  onMenuToggle: () => void;
  menuOpen: boolean;
}

export const Header: React.FC<HeaderProps> = ({ onMenuToggle, menuOpen }) => {
  const { systemConnected, systemStats } = useJarvisStore();
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="flex items-center justify-between px-4 md:px-8 py-4 bg-bg-light dark:bg-bg-dark border-b border-slate-300/30 dark:border-slate-800/30">
      {/* Brand & Mobile Toggle */}
      <div className="flex items-center gap-2 md:gap-3">
        {/* Mobile Menu Toggle Button */}
        <button
          onClick={onMenuToggle}
          className="p-2 md:hidden btn-neo text-slate-600 dark:text-slate-400 active:scale-95 transition-all mr-1"
          aria-label="Toggle Navigation Menu"
        >
          {menuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>

        <div className="relative flex items-center justify-center w-8 h-8 md:w-10 md:h-10 rounded-full bg-blue-500/10 dark:bg-blue-400/10 border border-blue-500/20 dark:border-blue-400/20">
          <div className="w-3 h-3 md:w-4 md:h-4 rounded-full bg-blue-500 animate-ping absolute" />
          <div className="w-2.5 h-2.5 md:w-3.5 md:h-3.5 rounded-full bg-blue-500 z-10" />
        </div>
        <div>
          <h1 className="text-sm md:text-lg font-bold uppercase tracking-wider text-slate-800 dark:text-slate-100 leading-tight">
            Jarvis OS
          </h1>
          <p className="text-[10px] md:text-xs text-slate-400 font-semibold leading-none">Smart Room Assistant</p>
        </div>
      </div>

      {/* Subsystem status indicators */}
      {systemConnected && systemStats && (
        <div className="hidden md:flex items-center gap-6 text-xs font-bold uppercase tracking-wider text-slate-400">
          <div className="flex items-center gap-2">
            <span className="shrink-0">AI:</span>
            <StatusBadge status={systemStats.ai_status} />
          </div>
          <div className="flex items-center gap-2">
            <span className="shrink-0">STT:</span>
            <StatusBadge status={systemStats.stt_status} />
          </div>
          <div className="flex items-center gap-2">
            <span className="shrink-0">TTS:</span>
            <StatusBadge status={systemStats.tts_status} />
          </div>
        </div>
      )}

      {/* System Actions */}
      <div className="flex items-center gap-4">
        {/* Connection status */}
        {systemConnected ? (
          <div className="flex items-center gap-2 text-green-500 dark:text-green-400 text-sm font-semibold">
            <Wifi className="w-4 h-4" />
            <span className="hidden sm:inline">Server Connected</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-red-500 dark:text-red-400 text-sm font-semibold">
            <WifiOff className="w-4 h-4 animate-pulse" />
            <span className="hidden sm:inline">Offline</span>
          </div>
        )}

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="p-3 rounded-xl bg-bg-light dark:bg-bg-dark shadow-neo-sm-light dark:shadow-neo-sm-dark text-slate-600 dark:text-slate-400 active:scale-95 transition-all"
        >
          {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>
      </div>
    </header>
  );
};
