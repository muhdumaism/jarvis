import React from 'react';

export const LoadingState: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center p-12 w-full gap-4">
      <div className="relative w-12 h-12">
        {/* Neomorphic Spinner */}
        <div className="absolute inset-0 rounded-full border-4 border-slate-300 dark:border-slate-800" />
        <div className="absolute inset-0 rounded-full border-4 border-t-blue-500 animate-spin" />
      </div>
      <span className="text-sm text-slate-500 dark:text-slate-400 font-medium">
        Loading system assets...
      </span>
    </div>
  );
};

export const SkeletonCard: React.FC = () => {
  return (
    <div className="card-neo flex flex-col gap-4 animate-pulse w-full">
      <div className="h-6 w-1/3 bg-slate-300 dark:bg-slate-800 rounded-lg" />
      <div className="h-4 w-3/4 bg-slate-200 dark:bg-slate-900 rounded-md" />
      <div className="h-10 w-full bg-slate-200 dark:bg-slate-900 rounded-xl mt-2" />
    </div>
  );
};
