import React, { useState, useEffect, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const StatCard = ({ label, value, unit, accent }) => (
  <div className="bg-slate-800 rounded-xl p-4">
    <div className="text-xs text-slate-400 mb-1">{label}</div>
    <div className={`text-2xl font-bold ${accent || 'text-white'}`}>
      {value}<span className="text-sm font-normal text-slate-400 ml-1">{unit}</span>
    </div>
  </div>
);

export default function StatsPanel({ stats, apiBase }) {
  const historyRef = useRef([]);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    if (!stats) return;
    const now = new Date();
    const label = `${now.getHours()}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')}`;
    historyRef.current = [...historyRef.current.slice(-299), { time: label, count: stats.current_count }];
    setHistory([...historyRef.current]);
  }, [stats]);

  if (!stats) {
    return (
      <div className="h-full flex items-center justify-center text-slate-500 text-sm">
        Waiting for data...
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3 h-full overflow-y-auto">
      <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider px-1">Live Analytics</h2>

      <div className="grid grid-cols-2 gap-3">
        <StatCard label="Current" value={stats.current_count} unit="people" accent="text-green-400" />
        <StatCard label="Session (60s)" value={stats.session_count} unit="seen" />
        <StatCard label="Avg Dwell" value={stats.avg_dwell_sec} unit="sec" accent="text-blue-400" />
        <StatCard label="Peak (5m)" value={stats.peak_count} unit="max" accent="text-purple-400" />
      </div>

      {/* Queue Score */}
      <div className="bg-slate-800 rounded-xl p-4">
        <div className="text-xs text-slate-400 mb-2">Queue Score</div>
        <div className="flex items-center gap-3">
          <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
            <div
              className={`h-2 rounded-full transition-all duration-500 ${
                stats.queue_score > 0.7 ? 'bg-red-500' :
                stats.queue_score > 0.4 ? 'bg-yellow-500' : 'bg-green-500'
              }`}
              style={{ width: `${(stats.queue_score * 100).toFixed(0)}%` }}
            />
          </div>
          <span className="text-sm font-mono text-slate-300 w-10">
            {(stats.queue_score * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {/* Rolling Chart */}
      <div className="bg-slate-800 rounded-xl p-4 flex-1 min-h-[160px]">
        <div className="text-xs text-slate-400 mb-3">Customer Count (last 5 min)</div>
        <ResponsiveContainer width="100%" height={120}>
          <LineChart data={history.slice(-100)} margin={{ top: 0, right: 5, bottom: 0, left: -20 }}>
            <XAxis dataKey="time" tick={false} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 8, fontSize: 11 }}
              labelStyle={{ color: '#94a3b8' }}
              itemStyle={{ color: '#4ade80' }}
            />
            <Line type="monotone" dataKey="count" stroke="#4ade80" strokeWidth={2}
              dot={false} activeDot={{ r: 4 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
