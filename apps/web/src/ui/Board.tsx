import React, { useMemo, useState } from "react";

type Token = {
  id: string;
  x: number; // px (placeholder; move to mm later)
  y: number;
  r: number;
  label: string;
};

export function Board() {
  const theme = {
    surface: "#171b24",
    border: "#2c3446",
    muted: "#aab4c8",
    boardBg: "#0f131b",
    grid: "#232b39",
    token: "#2a3345",
    tokenActive: "#3a4b66",
    tokenStroke: "#99b3ff",
    text: "#e7ebf3",
  } as const;

  // Placeholder tokens: replace with server state later
  const [tokens, setTokens] = useState<Token[]>([
    { id: "A", x: 160, y: 140, r: 22, label: "A" },
    { id: "B", x: 320, y: 260, r: 22, label: "B" },
  ]);

  const [selectedId, setSelectedId] = useState<string | null>(null);

  const selected = useMemo(() => tokens.find((t) => t.id === selectedId) ?? null, [tokens, selectedId]);

  function onDrag(e: React.PointerEvent<SVGCircleElement>, tokenId: string) {
    e.currentTarget.setPointerCapture(e.pointerId);
    setSelectedId(tokenId);
  }

  function onMove(e: React.PointerEvent<SVGCircleElement>) {
    if (!selectedId) return;
    const svg = e.currentTarget.ownerSVGElement;
    if (!svg) return;
    const ctm = svg.getScreenCTM();
    if (!ctm) return;
    const pt = svg.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const { x, y } = pt.matrixTransform(ctm.inverse());
    setTokens((prev) => prev.map((t) => (t.id === selectedId ? { ...t, x, y } : t)));
  }

  function onUp(e: React.PointerEvent<SVGCircleElement>) {
    setSelectedId(null);
    try {
      e.currentTarget.releasePointerCapture(e.pointerId);
    } catch {
      // ignore
    }
  }

  return (
    <div
      style={{
        border: `1px solid ${theme.border}`,
        borderRadius: 8,
        padding: 12,
        background: theme.surface,
        color: theme.text,
      }}
    >
      <h2 style={{ marginTop: 0 }}>Board (placeholder)</h2>
      <p style={{ marginTop: 0, color: theme.muted }}>
        Drag tokens locally. Next milestone: server-authoritative move commands.
      </p>

      <svg
        width="100%"
        viewBox="0 0 800 500"
        style={{
          border: `1px solid ${theme.border}`,
          borderRadius: 8,
          touchAction: "none",
          background: theme.boardBg,
        }}
      >
        <rect x="0" y="0" width="800" height="500" fill={theme.boardBg} />

        {/* Grid for quick placement while gameplay actions are in progress. */}
        {Array.from({ length: 16 }).map((_, i) => (
          <line key={"v" + i} x1={i * 50} y1={0} x2={i * 50} y2={500} stroke={theme.grid} />
        ))}
        {Array.from({ length: 10 }).map((_, i) => (
          <line key={"h" + i} x1={0} y1={i * 50} x2={800} y2={i * 50} stroke={theme.grid} />
        ))}

        {tokens.map((t) => (
          <g key={t.id}>
            <circle
              cx={t.x}
              cy={t.y}
              r={t.r}
              fill={t.id === selectedId ? theme.tokenActive : theme.token}
              stroke={theme.tokenStroke}
              strokeWidth="2"
              onPointerDown={(e) => onDrag(e, t.id)}
              onPointerMove={onMove}
              onPointerUp={onUp}
            />
            <text
              x={t.x}
              y={t.y + 5}
              textAnchor="middle"
              style={{ userSelect: "none", fontSize: 14, fill: theme.text }}
            >
              {t.label}
            </text>
          </g>
        ))}

        {selected && (
          <text x={12} y={24} style={{ fontSize: 14, fill: theme.muted }}>
            Selected: {selected.label} ({Math.round(selected.x)}, {Math.round(selected.y)})
          </text>
        )}
      </svg>
    </div>
  );
}
