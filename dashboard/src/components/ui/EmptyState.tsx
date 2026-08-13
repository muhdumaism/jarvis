import React from 'react';
import { HelpCircle } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  message,
  actionLabel,
  onAction,
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center gap-4 card-neo-inset max-w-lg mx-auto mt-6">
      <div className="p-4 rounded-full bg-slate-200/50 dark:bg-slate-800/50">
        <HelpCircle className="w-8 h-8 text-slate-400 dark:text-slate-600" />
      </div>
      <div>
        <h3 className="text-lg font-bold text-slate-700 dark:text-slate-300">{title}</h3>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">{message}</p>
      </div>
      {actionLabel && onAction && (
        <button onClick={onAction} className="btn-neo font-semibold px-6 mt-2 text-blue-600 dark:text-blue-400">
          {actionLabel}
        </button>
      )}
    </div>
  );
};
