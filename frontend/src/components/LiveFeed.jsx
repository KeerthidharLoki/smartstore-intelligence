import React, { useRef, useEffect, useState } from 'react';

export default function LiveFeed({ wsUrl }) {
  const canvasRef = useRef(null);
  const wsRef = useRef(null);
  const [connected, setConnected] = useState(false);
  const [metadata, setMetadata] = useState(null);

  useEffect(() => {
    let active = true;
    let pendingMetadata = null;

    const connect = () => {
      if (!active) return;
      const ws = new WebSocket(wsUrl);
      ws.binaryType = 'arraybuffer';
      wsRef.current = ws;

      ws.onopen = () => { if (active) setConnected(true); };
      ws.onclose = () => {
        if (active) {
          setConnected(false);
          setTimeout(connect, 2000);
        }
      };

      ws.onmessage = (event) => {
        if (!active) return;
        if (typeof event.data === 'string') {
          // JSON metadata frame
          try { pendingMetadata = JSON.parse(event.data); } catch (_) {}
        } else {
          // Binary JPEG frame
          if (pendingMetadata) {
            setMetadata(pendingMetadata);
            pendingMetadata = null;
          }
          const blob = new Blob([event.data], { type: 'image/jpeg' });
          const url = URL.createObjectURL(blob);
          const img = new Image();
          img.onload = () => {
            const canvas = canvasRef.current;
            if (!canvas) { URL.revokeObjectURL(url); return; }
            const ctx = canvas.getContext('2d');
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0);
            URL.revokeObjectURL(url);
          };
          img.src = url;
        }
      };
    };

    connect();
    return () => {
      active = false;
      wsRef.current?.close();
    };
  }, [wsUrl]);

  return (
    <div className="relative w-full h-full min-h-[320px]">
      <canvas
        ref={canvasRef}
        className="w-full h-full object-contain"
        style={{ display: connected ? 'block' : 'none' }}
      />
      {!connected && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-900 text-slate-500">
          <svg className="w-12 h-12 mb-3 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M15 10l4.553-2.069A1 1 0 0121 8.87v6.26a1 1 0 01-1.447.894L15 14M3 8a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" />
          </svg>
          <p className="text-sm font-medium">No Signal</p>
          <p className="text-xs text-slate-600 mt-1">Connecting to stream...</p>
        </div>
      )}
      {connected && metadata && (
        <div className="absolute top-2 left-2 bg-black/50 rounded px-2 py-1 text-xs text-green-400 font-mono">
          {metadata.current_count} person{metadata.current_count !== 1 ? 's' : ''} · {metadata.fps} fps
        </div>
      )}
    </div>
  );
}
