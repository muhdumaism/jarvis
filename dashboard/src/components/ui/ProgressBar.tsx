import React from 'react';

interface ProgressBarProps {
  progress: number; // 0 to 100
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ progress, className = '' }) => {
  const clampedProgress = Math.max(0, Math.min(100, progress));

  return (
    <div className={`w-full h-3 rounded-full bg-slate-300 dark:bg-slate-900 shadow-neo-sm-inset-light dark:shadow-neo-sm-inset-dark p-0.5 ${className}`}>
      <div
        className="h-full rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 shadow-neo-sm-light dark:shadow-neo-sm-dark transition-all duration-300"
        style={{ width: `${clampedProgress}%` }}
      />
    </div>
  );
};
