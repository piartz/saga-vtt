import React, { useMemo, useState } from "react";

const BOARD_WIDTH_MM = 800;
const BOARD_HEIGHT_MM = 500;
const MIN_ZOOM = 0.5;
const MAX_ZOOM = 2.5;
const ZOOM_STEP = 0.1;

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

type PanSession = {
  pointerId: number;
  startClientX: number;
  startClientY: number;
  startViewX: number;
  startViewY: number;
};

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function clampViewOrigin(x: number, y: number, width: number, height: number): { x: number; y: number } {
  return {
    x: clamp(x, 0, BOARD_WIDTH_MM - width),
    y: clamp(y, 0, BOARD_HEIGHT_MM - height),
  };
}

function wheelDeltaToPixels(delta: number, deltaMode: number): number {
  // 0=pixel, 1=line, 2=page. Browsers typically emit pixel on touchpads.
  if (deltaMode === 1) return delta * 16;
  if (deltaMode === 2) return delta * 800;
  return delta;
}

function clientToBoardPoint(
  svg: SVGSVGElement,
  clientX: number,
  clientY: number
): { x: number; y: number } | null {
  const ctm = svg.getScreenCTM();
  if (!ctm) return null;

  const pt = svg.createSVGPoint();
  pt.x = clientX;
  pt.y = clientY;
  const pos = pt.matrixTransform(ctm.inverse());
  return { x: pos.x, y: pos.y };
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
  const [zoom, setZoom] = useState(1);
  const [viewOrigin, setViewOrigin] = useState({ x: 0, y: 0 });
  const [panSession, setPanSession] = useState<PanSession | null>(null);

  const viewportWidth = BOARD_WIDTH_MM / zoom;
  const viewportHeight = BOARD_HEIGHT_MM / zoom;

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
    return clientToBoardPoint(svg, e.clientX, e.clientY);
  }

  function setZoomAround(nextZoom: number, anchor: { x: number; y: number } | null = null) {
    const boundedZoom = clamp(Number(nextZoom.toFixed(2)), MIN_ZOOM, MAX_ZOOM);
    if (boundedZoom === zoom) return;

    const oldWidth = BOARD_WIDTH_MM / zoom;
    const oldHeight = BOARD_HEIGHT_MM / zoom;
    const newWidth = BOARD_WIDTH_MM / boundedZoom;
    const newHeight = BOARD_HEIGHT_MM / boundedZoom;

    const anchorPoint = anchor ?? {
      x: viewOrigin.x + oldWidth / 2,
      y: viewOrigin.y + oldHeight / 2,
    };
    const anchorX = clamp(anchorPoint.x, 0, BOARD_WIDTH_MM);
    const anchorY = clamp(anchorPoint.y, 0, BOARD_HEIGHT_MM);

    const ratioX = (anchorX - viewOrigin.x) / oldWidth;
    const ratioY = (anchorY - viewOrigin.y) / oldHeight;

    const nextOrigin = clampViewOrigin(
      anchorX - ratioX * newWidth,
      anchorY - ratioY * newHeight,
      newWidth,
      newHeight
    );

    setZoom(boundedZoom);
    setViewOrigin(nextOrigin);
  }

  function onWheelZoom(e: React.WheelEvent<SVGSVGElement>) {
    e.preventDefault();
    const deltaY = wheelDeltaToPixels(e.deltaY, e.deltaMode);
    const deltaX = wheelDeltaToPixels(e.deltaX, e.deltaMode);
    const isZoomGesture = e.ctrlKey || e.metaKey || zoom <= 1;

    if (isZoomGesture) {
      const anchor = clientToBoardPoint(e.currentTarget, e.clientX, e.clientY);
      const delta = deltaY < 0 ? ZOOM_STEP : -ZOOM_STEP;
      setZoomAround(zoom + delta, anchor);
      return;
    }

    const mmPerPxX = viewportWidth / e.currentTarget.clientWidth;
    const mmPerPxY = viewportHeight / e.currentTarget.clientHeight;
    setViewOrigin((prev) =>
      clampViewOrigin(
        prev.x + deltaX * mmPerPxX,
        prev.y + deltaY * mmPerPxY,
        viewportWidth,
        viewportHeight
      )
    );
  }

  function onPanStart(e: React.PointerEvent<SVGRectElement>) {
    if (zoom <= 1) return;
    e.currentTarget.setPointerCapture(e.pointerId);
    setPanSession({
      pointerId: e.pointerId,
      startClientX: e.clientX,
      startClientY: e.clientY,
      startViewX: viewOrigin.x,
      startViewY: viewOrigin.y,
    });
  }

  function onPanMove(e: React.PointerEvent<SVGRectElement>) {
    if (!panSession || panSession.pointerId !== e.pointerId) return;
    const svg = e.currentTarget.ownerSVGElement;
    if (!svg || svg.clientWidth === 0 || svg.clientHeight === 0) return;

    const dxPx = e.clientX - panSession.startClientX;
    const dyPx = e.clientY - panSession.startClientY;
    const mmPerPxX = viewportWidth / svg.clientWidth;
    const mmPerPxY = viewportHeight / svg.clientHeight;

    setViewOrigin(
      clampViewOrigin(
        panSession.startViewX - dxPx * mmPerPxX,
        panSession.startViewY - dyPx * mmPerPxY,
        viewportWidth,
        viewportHeight
      )
    );
  }

  function onPanEnd(e: React.PointerEvent<SVGRectElement>) {
    if (panSession?.pointerId === e.pointerId) {
      try {
        e.currentTarget.releasePointerCapture(e.pointerId);
      } catch {
        // ignore
      }
      setPanSession(null);
    }
  }

  function resetView() {
    setPanSession(null);
    setZoom(1);
    setViewOrigin({ x: 0, y: 0 });
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
      <p style={{ marginTop: 0, color: theme.muted }}>
        Use mouse wheel (or pinch/Cmd+wheel) to zoom and drag/two-finger scroll to pan when zoomed in.
      </p>
      {!canMoveTokens && <p style={{ marginTop: 0, color: theme.muted }}>Connect to move tokens.</p>}
      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8, flexWrap: "wrap" }}>
        <button
          onClick={() => setZoomAround(zoom - ZOOM_STEP)}
          disabled={zoom <= MIN_ZOOM}
          style={{
            padding: "4px 8px",
            borderRadius: 6,
            border: `1px solid ${theme.border}`,
            background: theme.token,
            color: theme.text,
            cursor: zoom <= MIN_ZOOM ? "not-allowed" : "pointer",
          }}
        >
          -
        </button>
        <strong style={{ color: theme.muted }}>{Math.round(zoom * 100)}%</strong>
        <button
          onClick={() => setZoomAround(zoom + ZOOM_STEP)}
          disabled={zoom >= MAX_ZOOM}
          style={{
            padding: "4px 8px",
            borderRadius: 6,
            border: `1px solid ${theme.border}`,
            background: theme.token,
            color: theme.text,
            cursor: zoom >= MAX_ZOOM ? "not-allowed" : "pointer",
          }}
        >
          +
        </button>
        <button
          onClick={resetView}
          disabled={zoom === 1 && viewOrigin.x === 0 && viewOrigin.y === 0}
          style={{
            padding: "4px 8px",
            borderRadius: 6,
            border: `1px solid ${theme.border}`,
            background: theme.token,
            color: theme.text,
            cursor: zoom === 1 && viewOrigin.x === 0 && viewOrigin.y === 0 ? "not-allowed" : "pointer",
          }}
        >
          Reset View
        </button>
      </div>

      <svg
        width="100%"
        viewBox={`${viewOrigin.x} ${viewOrigin.y} ${viewportWidth} ${viewportHeight}`}
        onWheel={onWheelZoom}
        style={{
          border: `1px solid ${theme.border}`,
          borderRadius: 8,
          touchAction: "none",
          background: theme.boardBg,
        }}
      >
        <rect
          x="0"
          y="0"
          width={BOARD_WIDTH_MM}
          height={BOARD_HEIGHT_MM}
          fill={theme.boardBg}
          onPointerDown={onPanStart}
          onPointerMove={onPanMove}
          onPointerUp={onPanEnd}
          onPointerCancel={onPanEnd}
          style={{ cursor: zoom > 1 ? (panSession ? "grabbing" : "grab") : "default" }}
        />

        {/* Grid for quick placement while gameplay actions are in progress. */}
        {Array.from({ length: 16 }).map((_, i) => (
          <line
            key={"v" + i}
            x1={i * 50}
            y1={0}
            x2={i * 50}
            y2={BOARD_HEIGHT_MM}
            stroke={theme.grid}
            style={{ pointerEvents: "none" }}
          />
        ))}
        {Array.from({ length: 10 }).map((_, i) => (
          <line
            key={"h" + i}
            x1={0}
            y1={i * 50}
            x2={BOARD_WIDTH_MM}
            y2={i * 50}
            stroke={theme.grid}
            style={{ pointerEvents: "none" }}
          />
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
              style={{ userSelect: "none", pointerEvents: "none", fontSize: 14, fill: theme.text }}
            >
              {t.label}
            </text>
          </g>
        ))}

        {selected && (
          <text x={12} y={24} style={{ pointerEvents: "none", fontSize: 14, fill: theme.muted }}>
            Selected: {selected.label} ({Math.round(selected.x_mm)}, {Math.round(selected.y_mm)})
          </text>
        )}
      </svg>
    </div>
  );
}
