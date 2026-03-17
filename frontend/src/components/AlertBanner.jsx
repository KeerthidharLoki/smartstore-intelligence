import React from 'react';

export default function AlertBanner({ alert, score, size }) {
  if (!alert) return null;

  return (
    <div className="flex items-center gap-3 bg-red-900/60 border-b border-red-700/50 px-6 py-2.5 text-sm">
      <div className="w-2 h-2 rounded-full bg-red-400 animate-ping" />
      <span className="font-semibold text-red-200">Queue Detected</span>
      <span className="text-red-300">—</span>
      <span className="text-red-300">{size} people in queue</span>
      <span className="ml-auto text-red-400 text-xs font-mono">
        score: {(score * 100).toFixed(0)}%
      </span>
    </div>
  );
}
