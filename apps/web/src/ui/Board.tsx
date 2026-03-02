import React, { useMemo, useState } from "react";

const BOARD_WIDTH_MM = 800;
const BOARD_HEIGHT_MM = 500;

export type BoardToken = {
  id: string;
  label: string;
  x_mm: number;
  y_mm: number;
  r_mm: number;
};

type BoardProps = {
  tokens: BoardToken[];
  canMoveTokens: boolean;
  onMoveToken: (tokenId: string, xMm: number, yMm: number) => void;
};

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

export function Board({ tokens, canMoveTokens, onMoveToken }: BoardProps) {
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

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [dragPosition, setDragPosition] = useState<{ x: number; y: number } | null>(null);

  const renderedTokens = useMemo(
    () =>
      tokens.map((token) =>
        token.id === selectedId && dragPosition
          ? { ...token, x_mm: dragPosition.x, y_mm: dragPosition.y }
          : token
      ),
    [tokens, selectedId, dragPosition]
  );

  const selected = useMemo(
    () => renderedTokens.find((token) => token.id === selectedId) ?? null,
    [renderedTokens, selectedId]
  );

  function eventToBoardPoint(
    e: React.PointerEvent<SVGCircleElement>
  ): { x: number; y: number } | null {
    const svg = e.currentTarget.ownerSVGElement;
    if (!svg) return null;
    const ctm = svg.getScreenCTM();
    if (!ctm) return null;

    const pt = svg.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const pos = pt.matrixTransform(ctm.inverse());
    return { x: pos.x, y: pos.y };
  }

  function onDrag(e: React.PointerEvent<SVGCircleElement>, tokenId: string) {
    if (!canMoveTokens) return;
    e.currentTarget.setPointerCapture(e.pointerId);
    const token = tokens.find((t) => t.id === tokenId);
    if (!token) return;
    setSelectedId(tokenId);
    setDragPosition({ x: token.x_mm, y: token.y_mm });
  }

  function onMove(e: React.PointerEvent<SVGCircleElement>) {
    if (!canMoveTokens || !selectedId) return;
    const token = tokens.find((t) => t.id === selectedId);
    if (!token) return;
    const pos = eventToBoardPoint(e);
    if (!pos) return;
    setDragPosition({
      x: clamp(Math.round(pos.x), token.r_mm, BOARD_WIDTH_MM - token.r_mm),
      y: clamp(Math.round(pos.y), token.r_mm, BOARD_HEIGHT_MM - token.r_mm),
    });
  }

  function onUp(e: React.PointerEvent<SVGCircleElement>) {
    if (canMoveTokens && selectedId && dragPosition) {
      onMoveToken(selectedId, dragPosition.x, dragPosition.y);
    }
    setSelectedId(null);
    setDragPosition(null);
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
      <h2 style={{ marginTop: 0 }}>Board (server authoritative)</h2>
      <p style={{ marginTop: 0, color: theme.muted }}>
        Drag a token and release to send a MOVE_TOKEN command.
      </p>
      {!canMoveTokens && <p style={{ marginTop: 0, color: theme.muted }}>Connect to move tokens.</p>}

      <svg
        width="100%"
        viewBox={`0 0 ${BOARD_WIDTH_MM} ${BOARD_HEIGHT_MM}`}
        style={{
          border: `1px solid ${theme.border}`,
          borderRadius: 8,
          touchAction: "none",
          background: theme.boardBg,
        }}
      >
        <rect x="0" y="0" width={BOARD_WIDTH_MM} height={BOARD_HEIGHT_MM} fill={theme.boardBg} />

        {/* Grid for quick placement while gameplay actions are in progress. */}
        {Array.from({ length: 16 }).map((_, i) => (
          <line key={"v" + i} x1={i * 50} y1={0} x2={i * 50} y2={BOARD_HEIGHT_MM} stroke={theme.grid} />
        ))}
        {Array.from({ length: 10 }).map((_, i) => (
          <line key={"h" + i} x1={0} y1={i * 50} x2={BOARD_WIDTH_MM} y2={i * 50} stroke={theme.grid} />
        ))}

        {renderedTokens.map((t) => (
          <g key={t.id}>
            <circle
              cx={t.x_mm}
              cy={t.y_mm}
              r={t.r_mm}
              fill={t.id === selectedId ? theme.tokenActive : theme.token}
              stroke={theme.tokenStroke}
              strokeWidth="2"
              onPointerDown={(e) => onDrag(e, t.id)}
              onPointerMove={onMove}
              onPointerUp={onUp}
            />
            <text
              x={t.x_mm}
              y={t.y_mm + 5}
              textAnchor="middle"
              style={{ userSelect: "none", fontSize: 14, fill: theme.text }}
            >
              {t.label}
            </text>
          </g>
        ))}

        {selected && (
          <text x={12} y={24} style={{ fontSize: 14, fill: theme.muted }}>
            Selected: {selected.label} ({Math.round(selected.x_mm)}, {Math.round(selected.y_mm)})
          </text>
        )}
      </svg>
    </div>
  );
}
