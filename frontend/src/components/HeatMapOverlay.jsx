import React, { useState, useEffect } from 'react';

export default function HeatMapOverlay({ heatmapUrl }) {
  const [src, setSrc] = useState(null);

  useEffect(() => {
    const refresh = () => {
      setSrc(`${heatmapUrl}?t=${Date.now()}`);
    };
    refresh();
    const id = setInterval(refresh, 2000);
    return () => clearInterval(id);
  }, [heatmapUrl]);

  if (!src) return null;

  return (
    <img
      src={src}
      alt="heatmap"
      className="absolute inset-0 w-full h-full object-contain pointer-events-none"
      style={{ opacity: 0.55, mixBlendMode: 'screen' }}
    />
  );
}
