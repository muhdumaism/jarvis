import React from 'react';
import { useJarvisStore } from '../../state/store';
import { AlertCircle, CheckCircle, Info, X } from 'lucide-react';

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useJarvisStore();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3 max-w-sm w-full">
      {toasts.map((toast) => {
        let levelColor = 'text-blue-500';
        let Icon = Info;

        if (toast.level === 'success') {
          levelColor = 'text-green-500';
          Icon = CheckCircle;
        } else if (toast.level === 'warning') {
          levelColor = 'text-yellow-500';
          Icon = AlertCircle;
        } else if (toast.level === 'error') {
          levelColor = 'text-red-500';
          Icon = AlertCircle;
        }

        return (
          <div
            key={toast.id}
            className="flex items-center gap-3 p-4 rounded-xl card-neo animate-slide-up"
          >
            <Icon className={`w-5 h-5 ${levelColor} shrink-0`} />
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
              {toast.message}
            </span>
            <button
              onClick={() => removeToast(toast.id)}
              className="ml-auto p-1 rounded-lg hover:bg-slate-200/50 dark:hover:bg-slate-700/50 transition-colors"
            >
              <X className="w-4 h-4 text-slate-400" />
            </button>
          </div>
        );
      })}
    </div>
  );
};
