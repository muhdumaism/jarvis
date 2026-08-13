import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Home,
  Sliders,
  Cpu,
  MessageSquareCode,
  Mic,
  Music,
  Zap,
  Layers,
  FileCode,
  Info,
  Terminal,
  Settings,
  ShieldCheck,
} from 'lucide-react';

interface NavItem {
  name: string;
  path: string;
  icon: React.ComponentType<any>;
}

const navItems: NavItem[] = [
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Rooms', path: '/rooms', icon: Home },
  { name: 'Devices', path: '/devices', icon: Sliders },
  { name: 'Nodes', path: '/nodes', icon: Cpu },
  { name: 'Assistant', path: '/assistant', icon: MessageSquareCode },
  { name: 'Voice Debug', path: '/voice', icon: Mic },
  { name: 'Music', path: '/music', icon: Music },
  { name: 'Automations', path: '/automations', icon: Zap },
  { name: 'Scenes', path: '/scenes', icon: Layers },
  { name: 'Firmware', path: '/firmware', icon: ShieldCheck },
  { name: 'Hardware', path: '/hardware', icon: Info },
  { name: 'Circuits', path: '/circuits', icon: FileCode },
  { name: 'Logs', path: '/logs', icon: Terminal },
  { name: 'Settings', path: '/settings', icon: Settings },
];

interface SidebarProps {
  onItemClick?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ onItemClick }) => {
  return (
    <aside className="w-64 h-full bg-bg-light dark:bg-bg-dark border-r border-slate-300/30 dark:border-slate-800/30 flex flex-col justify-between py-6">
      {/* Navigation List */}
      <nav className="flex-1 overflow-y-auto px-4 space-y-3">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            onClick={onItemClick}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 text-sm font-semibold uppercase tracking-wider ${
                isActive
                  ? 'shadow-neo-sm-inset-light dark:shadow-neo-sm-inset-dark text-blue-600 dark:text-blue-400'
                  : 'text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-slate-200/20 dark:hover:bg-slate-800/20'
              }`
            }
          >
            <item.icon className="w-5 h-5 shrink-0" />
            <span className="truncate">{item.name}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer copyright */}
      <div className="px-6 pt-4 border-t border-slate-300/20 dark:border-slate-800/20 text-center">
        <p className="text-[10px] font-bold text-slate-400 tracking-widest uppercase">
          JARVIS OS v1.0
        </p>
      </div>
    </aside>
  );
};
