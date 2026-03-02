import React, { useMemo, useState } from "react";

type Token = {
  id: string;
  x: number; // px (placeholder; move to mm later)
  y: number;
  r: number;
  label: string;
};

export function Board() {
  // Placeholder tokens: replace with server state later
  const [tokens, setTokens] = useState<Token[]>([
    { id: "A", x: 160, y: 140, r: 22, label: "A" },
    { id: "B", x: 320, y: 260, r: 22, label: "B" },
  ]);

  const [selectedId, setSelectedId] = useState<string | null>(null);

  const selected = useMemo(() => tokens.find((t) => t.id === selectedId) ?? null, [tokens, selectedId]);

  function onDrag(e: React.PointerEvent, tokenId: string) {
    (e.currentTarget as any).setPointerCapture(e.pointerId);
    setSelectedId(tokenId);
  }

  function onMove(e: React.PointerEvent) {
    if (!selectedId) return;
    const svg = (e.currentTarget as any).ownerSVGElement as SVGSVGElement;
    const pt = svg.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const { x, y } = pt.matrixTransform(svg.getScreenCTM()?.inverse());
    setTokens((prev) =>
      prev.map((t) => (t.id === selectedId ? { ...t, x, y } : t))
    );
  }

  function onUp(e: React.PointerEvent) {
    setSelectedId(null);
    try {
      (e.currentTarget as any).releasePointerCapture(e.pointerId);
    } catch {
      // ignore
    }
  }

  return (
    <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12 }}>
      <h2 style={{ marginTop: 0 }}>Board (placeholder)</h2>
      <p style={{ marginTop: 0, opacity: 0.75 }}>
        Drag tokens locally. Next milestone: server-authoritative move commands.
      </p>

      <svg
        width="100%"
        viewBox="0 0 800 500"
        style={{ border: "1px solid #eee", borderRadius: 8, touchAction: "none" }}
      >
        <rect x="0" y="0" width="800" height="500" fill="white" />

        {/* A light "table" grid as a temporary visual aid */}
        {Array.from({ length: 16 }).map((_, i) => (
          <line key={"v" + i} x1={i * 50} y1={0} x2={i * 50} y2={500} stroke="#f5f5f5" />
        ))}
        {Array.from({ length: 10 }).map((_, i) => (
          <line key={"h" + i} x1={0} y1={i * 50} x2={800} y2={i * 50} stroke="#f5f5f5" />
        ))}

        {tokens.map((t) => (
          <g key={t.id}>
            <circle
              cx={t.x}
              cy={t.y}
              r={t.r}
              fill={t.id === selectedId ? "#e8f0ff" : "#f7f7f7"}
              stroke="#444"
              strokeWidth="2"
              onPointerDown={(e) => onDrag(e, t.id)}
              onPointerMove={onMove}
              onPointerUp={onUp}
            />
            <text x={t.x} y={t.y + 5} textAnchor="middle" style={{ userSelect: "none", fontSize: 14 }}>
              {t.label}
            </text>
          </g>
        ))}

        {selected && (
          <text x={12} y={24} style={{ fontSize: 14, opacity: 0.8 }}>
            Selected: {selected.label} ({Math.round(selected.x)}, {Math.round(selected.y)})
          </text>
        )}
      </svg>
    </div>
  );
}
