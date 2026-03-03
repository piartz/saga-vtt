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
- Confirm move (server validates & broadcasts)

## Milestone 2 — “Play a basic scenario”
- Turn structure + active player
- Activation markers
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
