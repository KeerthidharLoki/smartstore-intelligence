import React, { useState, useEffect } from 'react';
import LiveFeed from './components/LiveFeed';
import HeatMapOverlay from './components/HeatMapOverlay';
import StatsPanel from './components/StatsPanel';
import AlertBanner from './components/AlertBanner';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const WS_BASE = API_BASE.replace('http', 'ws');

export default function App() {
  const [stats, setStats] = useState(null);
  const [showHeatmap, setShowHeatmap] = useState(false);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/stats`);
        if (res.ok) setStats(await res.json());
      } catch (_) {}
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      {/* Header */}
      <header className="border-b border-slate-700 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-green-400 animate-pulse" />
          <h1 className="text-lg font-semibold tracking-tight">SmartStore Intelligence</h1>
        </div>
        <div className="text-xs text-slate-400">
          {stats ? `${stats.fps} FPS · Uptime ${Math.floor(stats.uptime_sec / 60)}m` : 'Connecting...'}
        </div>
      </header>

      {/* Queue Alert Banner */}
      {stats && <AlertBanner alert={stats.queue_alert} score={stats.queue_score} size={stats.queue_size} />}

      {/* Main layout */}
      <main className="flex flex-col lg:flex-row gap-4 p-4 h-[calc(100vh-64px)]">
        {/* Left: Video Feed */}
        <div className="flex-1 flex flex-col gap-3 min-w-0">
          <div className="relative bg-slate-800 rounded-xl overflow-hidden flex-1">
            <LiveFeed wsUrl={`${WS_BASE}/ws/stream`} />
            {showHeatmap && <HeatMapOverlay heatmapUrl={`${API_BASE}/heatmap`} />}
            <button
              onClick={() => setShowHeatmap(v => !v)}
              className={`absolute bottom-3 right-3 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                showHeatmap
                  ? 'bg-orange-500 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              {showHeatmap ? 'Hide Heatmap' : 'Show Heatmap'}
            </button>
          </div>
        </div>

        {/* Right: Stats */}
        <div className="w-full lg:w-80 shrink-0">
          <StatsPanel stats={stats} apiBase={API_BASE} />
        </div>
      </main>
    </div>
  );
}
