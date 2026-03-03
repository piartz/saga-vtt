import React, { useEffect, useMemo, useRef, useState } from "react";

const BOARD_WIDTH_MM = 800;
const BOARD_HEIGHT_MM = 500;
const GRID_STEP_MM = 50;
const MIN_ZOOM = 0.5;
const MAX_ZOOM = 2.5;
const ZOOM_STEP = 0.1;
const HOVER_MENU_CLOSE_DELAY_MS = 180;

export type ActivationType = "move" | "charge" | "shoot" | "rest";

export type BoardToken = {
  id: string;
  label: string;
  x_mm: number;
  y_mm: number;
  r_mm: number;
  activation_count_this_turn: number;
  last_activation_type: ActivationType | null;
};

type BoardProps = {
  tokens: BoardToken[];
  canMoveTokens: boolean;
  canActivateTokens: boolean;
  confirmMoves: boolean;
  onMoveToken: (tokenId: string, xMm: number, yMm: number) => void;
  onActivateToken: (tokenId: string, activationType: ActivationType) => void;
};

type PanSession = {
  pointerId: number;
  startClientX: number;
  startClientY: number;
  startViewX: number;
  startViewY: number;
};

type PendingMove = {
  tokenId: string;
  x: number;
  y: number;
};

type ActiveDrag = {
  tokenId: string;
  pointerId: number;
};

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function clampViewOrigin(x: number, y: number, width: number, height: number): { x: number; y: number } {
  const centeredX = (BOARD_WIDTH_MM - width) / 2;
  const centeredY = (BOARD_HEIGHT_MM - height) / 2;
  const minX = width >= BOARD_WIDTH_MM ? centeredX : 0;
  const maxX = width >= BOARD_WIDTH_MM ? centeredX : BOARD_WIDTH_MM - width;
  const minY = height >= BOARD_HEIGHT_MM ? centeredY : 0;
  const maxY = height >= BOARD_HEIGHT_MM ? centeredY : BOARD_HEIGHT_MM - height;

  return {
    x: clamp(x, minX, maxX),
    y: clamp(y, minY, maxY),
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

export function Board({
  tokens,
  canMoveTokens,
  canActivateTokens,
  confirmMoves,
  onMoveToken,
  onActivateToken,
}: BoardProps) {
  const theme = {
    surface: "#171b24",
    border: "#2c3446",
    muted: "#aab4c8",
    boardBg: "#0f131b",
    grid: "#232b39",
    token: "#2a3345",
    tokenActive: "#3a4b66",
    tokenStroke: "#99b3ff",
    activationMove: "#67e8f9",
    activationCharge: "#fb923c",
    activationShoot: "#a78bfa",
    activationRest: "#4ade80",
    activationFill: "#18202d",
    text: "#e7ebf3",
  } as const;

  const activationStyles: Record<ActivationType, { label: string; color: string }> = {
    move: { label: "Move", color: theme.activationMove },
    charge: { label: "Charge", color: theme.activationCharge },
    shoot: { label: "Shoot", color: theme.activationShoot },
    rest: { label: "Rest", color: theme.activationRest },
  };

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [hoveredTokenId, setHoveredTokenId] = useState<string | null>(null);
  const [dragPosition, setDragPosition] = useState<{ x: number; y: number } | null>(null);
  const [dragMoved, setDragMoved] = useState(false);
  const [pendingMove, setPendingMove] = useState<PendingMove | null>(null);
  const [activeDrag, setActiveDrag] = useState<ActiveDrag | null>(null);
  const [zoom, setZoom] = useState(1);
  const [viewOrigin, setViewOrigin] = useState({ x: 0, y: 0 });
  const [panSession, setPanSession] = useState<PanSession | null>(null);
  const boardSvgRef = useRef<SVGSVGElement | null>(null);
  const hoverCloseTimerRef = useRef<number | null>(null);

  const viewportWidth = BOARD_WIDTH_MM / zoom;
  const viewportHeight = BOARD_HEIGHT_MM / zoom;

  const renderedTokens = useMemo(
    () =>
      tokens.map((token) => {
        if (token.id === selectedId && dragPosition) {
          return { ...token, x_mm: dragPosition.x, y_mm: dragPosition.y };
        }
        if (confirmMoves && pendingMove && token.id === pendingMove.tokenId) {
          return { ...token, x_mm: pendingMove.x, y_mm: pendingMove.y };
        }
        return token;
      }),
    [tokens, selectedId, dragPosition, confirmMoves, pendingMove]
  );

  const selected = useMemo(
    () => renderedTokens.find((token) => token.id === selectedId) ?? null,
    [renderedTokens, selectedId]
  );
  const pendingToken = useMemo(
    () => (pendingMove ? tokens.find((token) => token.id === pendingMove.tokenId) ?? null : null),
    [tokens, pendingMove]
  );

  useEffect(() => {
    const svg = boardSvgRef.current;
    if (!svg) return;

    const blockPageScroll = (event: WheelEvent) => {
      event.preventDefault();
    };

    // React wheel handlers can behave passively on some browsers/input devices.
    // Use a native non-passive listener so page scrolling never steals board gestures.
    svg.addEventListener("wheel", blockPageScroll, { passive: false });
    return () => {
      svg.removeEventListener("wheel", blockPageScroll);
    };
  }, []);

  useEffect(
    () => () => {
      if (hoverCloseTimerRef.current !== null) {
        window.clearTimeout(hoverCloseTimerRef.current);
      }
    },
    []
  );

  useEffect(() => {
    if (!confirmMoves && pendingMove) {
      setPendingMove(null);
    }
  }, [confirmMoves, pendingMove]);

  useEffect(() => {
    if (!pendingMove) return;
    const token = tokens.find((t) => t.id === pendingMove.tokenId);
    if (!token) {
      setPendingMove(null);
      return;
    }
    if (token.x_mm === pendingMove.x && token.y_mm === pendingMove.y) {
      setPendingMove(null);
    }
  }, [tokens, pendingMove]);

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
    const deltaY = wheelDeltaToPixels(e.deltaY, e.deltaMode);
    const deltaX = wheelDeltaToPixels(e.deltaX, e.deltaMode);
    const wantsZoom = e.altKey || e.ctrlKey || e.metaKey;

    if (wantsZoom) {
      e.preventDefault();
      const anchor = clientToBoardPoint(e.currentTarget, e.clientX, e.clientY);
      const delta = deltaY < 0 ? ZOOM_STEP : -ZOOM_STEP;
      setZoomAround(zoom + delta, anchor);
      return;
    }

    if (zoom <= 1) {
      // At or below 100%, wheel gestures should not trigger board zoom.
      e.preventDefault();
      return;
    }

    e.preventDefault();
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

  function confirmPendingMove() {
    if (!canMoveTokens || !pendingMove) return;
    const move = pendingMove;
    setPendingMove(null);
    setDragPosition(null);
    setDragMoved(false);
    setActiveDrag(null);
    onMoveToken(move.tokenId, move.x, move.y);
  }

  function cancelPendingMove() {
    setPendingMove(null);
  }

  function onDrag(e: React.PointerEvent<SVGCircleElement>, tokenId: string) {
    if (!canMoveTokens) return;
    if (confirmMoves && pendingMove && pendingMove.tokenId !== tokenId) return;
    clearHoverCloseTimer();
    setHoveredTokenId(null);
    e.currentTarget.setPointerCapture(e.pointerId);
    const token = tokens.find((t) => t.id === tokenId);
    if (!token) return;
    const startingPosition =
      confirmMoves && pendingMove && pendingMove.tokenId === tokenId
        ? { x: pendingMove.x, y: pendingMove.y }
        : { x: token.x_mm, y: token.y_mm };

    setSelectedId(tokenId);
    setDragPosition(startingPosition);
    setDragMoved(false);
    setActiveDrag({ tokenId, pointerId: e.pointerId });
  }

  function onMove(e: React.PointerEvent<SVGCircleElement>) {
    if (!canMoveTokens || !selectedId || !activeDrag) return;
    if (activeDrag.pointerId !== e.pointerId || activeDrag.tokenId !== selectedId) return;
    if (!e.currentTarget.hasPointerCapture(e.pointerId)) return;
    const token = tokens.find((t) => t.id === selectedId);
    if (!token) return;
    const pos = eventToBoardPoint(e);
    if (!pos) return;
    const next = {
      x: clamp(Math.round(pos.x), token.r_mm, BOARD_WIDTH_MM - token.r_mm),
      y: clamp(Math.round(pos.y), token.r_mm, BOARD_HEIGHT_MM - token.r_mm),
    };
    if (!dragMoved && dragPosition && (next.x !== dragPosition.x || next.y !== dragPosition.y)) {
      setDragMoved(true);
    }
    setDragPosition({
      x: next.x,
      y: next.y,
    });
  }

  function endDrag(e: React.PointerEvent<SVGCircleElement>, commitMove: boolean) {
    if (
      commitMove &&
      canMoveTokens &&
      selectedId &&
      dragPosition &&
      dragMoved &&
      activeDrag &&
      activeDrag.pointerId === e.pointerId
    ) {
      const token = tokens.find((t) => t.id === selectedId);
      if (token && (token.x_mm !== dragPosition.x || token.y_mm !== dragPosition.y)) {
        if (confirmMoves) {
          setPendingMove({
            tokenId: selectedId,
            x: dragPosition.x,
            y: dragPosition.y,
          });
        } else {
          onMoveToken(selectedId, dragPosition.x, dragPosition.y);
        }
      }
    }
    setDragPosition(null);
    setDragMoved(false);
    setActiveDrag(null);
    try {
      e.currentTarget.releasePointerCapture(e.pointerId);
    } catch {
      // ignore
    }
  }

  function onUp(e: React.PointerEvent<SVGCircleElement>) {
    endDrag(e, true);
  }

  function onCancelDrag(e: React.PointerEvent<SVGCircleElement>) {
    endDrag(e, false);
  }

  function clearHoverCloseTimer() {
    if (hoverCloseTimerRef.current !== null) {
      window.clearTimeout(hoverCloseTimerRef.current);
      hoverCloseTimerRef.current = null;
    }
  }

  function openHoverMenu(tokenId: string) {
    clearHoverCloseTimer();
    setHoveredTokenId(tokenId);
  }

  function scheduleHoverMenuClose(tokenId: string) {
    clearHoverCloseTimer();
    hoverCloseTimerRef.current = window.setTimeout(() => {
      setHoveredTokenId((prev) => (prev === tokenId ? null : prev));
      hoverCloseTimerRef.current = null;
    }, HOVER_MENU_CLOSE_DELAY_MS);
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
        {confirmMoves
          ? "Drag a token to stage a move, then confirm or cancel it."
          : "Drag a token and release to send a MOVE_TOKEN command immediately."}
      </p>
      <p style={{ marginTop: 0, color: theme.muted }}>
        Hover a token to pick activation type: M (move), C (charge), S (shoot), R (rest).
      </p>
      <p style={{ marginTop: 0, color: theme.muted }}>
        Hold Option/Alt (or pinch/Cmd/Ctrl gesture) to zoom. When zoomed in, use drag or two-finger scroll to pan.
      </p>
      {confirmMoves && pendingMove && (
        <p style={{ marginTop: 0, color: theme.muted }}>
          One token can have a pending move at a time.
        </p>
      )}
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
      {confirmMoves && pendingMove && (
        <div
          style={{
            display: "flex",
            gap: 8,
            alignItems: "center",
            marginBottom: 8,
            flexWrap: "wrap",
            color: theme.muted,
          }}
        >
          <span>
            Pending: {pendingToken?.label ?? pendingMove.tokenId} to ({pendingMove.x}, {pendingMove.y}) mm
          </span>
          <button
            onClick={confirmPendingMove}
            disabled={!canMoveTokens}
            style={{
              padding: "4px 8px",
              borderRadius: 6,
              border: `1px solid ${theme.border}`,
              background: theme.tokenActive,
              color: theme.text,
              cursor: canMoveTokens ? "pointer" : "not-allowed",
            }}
          >
            Confirm Move
          </button>
          <button
            onClick={cancelPendingMove}
            style={{
              padding: "4px 8px",
              borderRadius: 6,
              border: `1px solid ${theme.border}`,
              background: theme.token,
              color: theme.text,
              cursor: "pointer",
            }}
          >
            Cancel
          </button>
        </div>
      )}

      <svg
        ref={boardSvgRef}
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
        {Array.from({ length: BOARD_WIDTH_MM / GRID_STEP_MM + 1 }).map((_, i) => (
          <line
            key={"v" + i}
            x1={i * GRID_STEP_MM}
            y1={0}
            x2={i * GRID_STEP_MM}
            y2={BOARD_HEIGHT_MM}
            stroke={theme.grid}
            style={{ pointerEvents: "none" }}
          />
        ))}
        {Array.from({ length: BOARD_HEIGHT_MM / GRID_STEP_MM + 1 }).map((_, i) => (
          <line
            key={"h" + i}
            x1={0}
            y1={i * GRID_STEP_MM}
            x2={BOARD_WIDTH_MM}
            y2={i * GRID_STEP_MM}
            stroke={theme.grid}
            style={{ pointerEvents: "none" }}
          />
        ))}

        {renderedTokens.map((t) => {
          const isLockedByPending = confirmMoves && pendingMove !== null && pendingMove.tokenId !== t.id;
          const activationStyle = t.last_activation_type ? activationStyles[t.last_activation_type] : null;
          const showActivationMenu =
            hoveredTokenId === t.id &&
            canActivateTokens &&
            !isLockedByPending &&
            activeDrag === null;
          const activationButtons = [
            { type: "move" as const, label: "M" },
            { type: "charge" as const, label: "C" },
            { type: "shoot" as const, label: "S" },
            { type: "rest" as const, label: "R" },
          ].filter((button) => !(button.type === "rest" && t.activation_count_this_turn > 0));
          const buttonWidth = 18;
          const buttonHeight = 14;
          const buttonGap = 4;
          const totalWidth = activationButtons.length * buttonWidth + (activationButtons.length - 1) * buttonGap;
          const menuX = t.x_mm - totalWidth / 2;
          const menuY = t.y_mm - t.r_mm - 22;

          return (
            <g
              key={t.id}
              onPointerEnter={() => openHoverMenu(t.id)}
              onPointerLeave={() => scheduleHoverMenuClose(t.id)}
            >
              {activationStyle && (
                <circle
                  cx={t.x_mm}
                  cy={t.y_mm}
                  r={t.r_mm + 5}
                  fill={theme.activationFill}
                  stroke={activationStyle.color}
                  strokeWidth="2"
                  style={{ pointerEvents: "none" }}
                />
              )}
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
                onPointerCancel={onCancelDrag}
                style={{
                  cursor: isLockedByPending ? "not-allowed" : canMoveTokens ? "grab" : "default",
                }}
              />
              <text
                x={t.x_mm}
                y={t.y_mm + 5}
                textAnchor="middle"
                style={{ userSelect: "none", pointerEvents: "none", fontSize: 14, fill: theme.text }}
              >
                {t.label}
              </text>
              {activationStyle && (
                <>
                  <circle
                    cx={t.x_mm + t.r_mm * 0.62}
                    cy={t.y_mm - t.r_mm * 0.62}
                    r="5"
                    fill={activationStyle.color}
                    style={{ pointerEvents: "none" }}
                  />
                  <text
                    x={t.x_mm}
                    y={t.y_mm + t.r_mm + 14}
                    textAnchor="middle"
                    style={{ userSelect: "none", pointerEvents: "none", fontSize: 11, fill: activationStyle.color }}
                  >
                    {activationStyle.label} x{t.activation_count_this_turn}
                  </text>
                </>
              )}
              {showActivationMenu && (
                <g
                  onPointerEnter={() => openHoverMenu(t.id)}
                  onPointerLeave={() => scheduleHoverMenuClose(t.id)}
                >
                  {activationButtons.map((button, index) => {
                    const x = menuX + index * (buttonWidth + buttonGap);
                    const y = menuY;
                    const buttonStyle = activationStyles[button.type];
                    return (
                      <g
                        key={button.type}
                        onPointerDown={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          clearHoverCloseTimer();
                          setHoveredTokenId(null);
                          onActivateToken(t.id, button.type);
                        }}
                      >
                        <rect
                          x={x}
                          y={y}
                          width={buttonWidth}
                          height={buttonHeight}
                          rx="3"
                          fill={buttonStyle.color}
                          stroke={theme.border}
                          strokeWidth="1"
                          style={{ cursor: "pointer" }}
                        />
                        <text
                          x={x + buttonWidth / 2}
                          y={y + 10}
                          textAnchor="middle"
                          style={{
                            pointerEvents: "none",
                            userSelect: "none",
                            fontSize: 10,
                            fill: "#0f1115",
                            fontWeight: 700,
                          }}
                        >
                          {button.label}
                        </text>
                      </g>
                    );
                  })}
                </g>
              )}
            </g>
          );
        })}

        {selected && (
          <text x={12} y={24} style={{ pointerEvents: "none", fontSize: 14, fill: theme.muted }}>
            Selected: {selected.label} ({Math.round(selected.x_mm)}, {Math.round(selected.y_mm)})
            {selected.last_activation_type
              ? ` | ${activationStyles[selected.last_activation_type].label} x${selected.activation_count_this_turn}`
              : ""}
          </text>
        )}
      </svg>
    </div>
  );
}
