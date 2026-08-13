import React from 'react';

interface StatusBadgeProps {
  status: 'online' | 'offline' | 'pending' | 'success' | 'error' | string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  let badgeStyle = 'bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-300';
  let dotColor = 'bg-slate-400';

  if (status === 'online' || status === 'success') {
    badgeStyle = 'bg-green-100 text-green-700 dark:bg-green-950/40 dark:text-green-400';
    dotColor = 'bg-green-500';
  } else if (status === 'offline' || status === 'error') {
    badgeStyle = 'bg-red-100 text-red-700 dark:bg-red-950/40 dark:text-red-400';
    dotColor = 'bg-red-500';
  } else if (status === 'pending') {
    badgeStyle = 'bg-yellow-100 text-yellow-700 dark:bg-yellow-950/40 dark:text-yellow-400';
    dotColor = 'bg-yellow-500 animate-pulse';
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider ${badgeStyle}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
      {status}
    </span>
  );
};
