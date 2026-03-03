# Roadmap

## Milestone 0 — Bootstrap (this repo)
- [x] Monorepo scaffold
- [x] FastAPI health endpoint
- [x] WebSocket echo loop (PING/PONG)
- [x] Web client connects and displays events

## Milestone 1 — “Shared tabletop”
- Token placement (spawn a few tokens)
- Pan/zoom board (implemented: wheel zoom, +/- controls, reset, background pan)
- Select token
- Move token with measurement preview (client)
- Confirm move (implemented: optional toggle, one-token-at-a-time pending confirm/cancel)

## Milestone 2 — “Play a basic scenario”
- Turn structure + active player (implemented with initiative roll + winner chooses first/second)
- Activation markers (implemented: typed activations `move|charge|shoot|rest`, repeatable per turn with count/last-type tracking, no manual deactivation, `rest` only before first activation, reset on end turn)
- Dice roller (server-side)
- Action log UI

## Milestone 3 — “Rules module interface”
- Define a `RulesModule` interface (validate commands, compute derived state)
- Make “core” run with a toy ruleset
- Add a *SAGA module* **only if you have rights/permission**

## Milestone 4 — “Accounts & persistence”
- Accounts (OAuth or email link)
- Save game state + event logs
- Spectators
- Replays

## Engineering / CI-CD hardening
- [x] CI step 1: deterministic installs (`pnpm --frozen-lockfile`, `poetry install --sync`) + API type-check (`mypy`)
- [ ] CI step 2: add API/web integration smoke test (WebSocket connect + minimal command flow)
- [ ] CI step 3: add dependency/security automation (Dependabot + security scan job)
- [ ] CI step 4: deployment workflow with manual approval gate for production
