# Skirmish VTT Bootstrap (Saga-ready)

This repository is a **starter scaffold** for building a **server‑authoritative, web‑based client** to play a tabletop miniature skirmish game online (e.g., *SAGA*).

It is intentionally **generic**:
- **No SAGA rules text** is included.
- **No copyrighted art / unit profiles / battle boards** are included.
- The design supports adding a *rule module* later (including a SAGA module, if you have the rights/permission).

> **Trademark / affiliation note:** “SAGA” is a trademark and product of Studio Tomahawk and its partners. This project is not affiliated with or endorsed by them.

## What you get

- A **monorepo** with:
  - `apps/web`: React + TypeScript web client (SVG-based board placeholder)
  - `services/api`: Python FastAPI backend with WebSocket game room
  - `docs/`: architecture, roadmap, data model, ADRs
  - `.github/`: CI workflow + issue / PR templates
- A working “hello game” loop:
  - open a room
  - connect via WebSocket
  - send a `PING` command
  - receive `PONG` + server timestamp
- A foundation that’s friendly to “code-assisting LLMs”:
  - clear folder map
  - “first issues” in the roadmap
  - a command/event protocol described in docs
  - ADRs to capture decisions as they happen

## Quick start (local)

### Prereqs
- Node.js 20+ (or 18+)
- Python 3.11+
- Homebrew (recommended on macOS for automatic tool install prompts)

`pnpm` and `Poetry` are installed by `tools/setup-and-run.sh` when missing
(with interactive confirmation).

### One-command setup + run
From the repo root:
```bash
make setup-run
```
or:
```bash
./tools/setup-and-run.sh
```

This command checks tool versions, installs dependencies, and starts:
- API: http://127.0.0.1:8000
- Web: http://127.0.0.1:5173

When a required tool is missing or too old, the script:
- detects platform (`linux` or `macos`)
- asks for confirmation before install/upgrade
- tries platform-specific installers/fallbacks (for `pnpm`: Homebrew first on macOS)

Press `Ctrl+C` to stop both services.

### Setup troubleshooting
- If tool install fails due to permissions, rerun and accept the targeted `sudo` prompt when offered.
- On macOS, install Homebrew first to improve installer reliability:
  - https://brew.sh/
- If an install path fails, run the script again; it will retry with fallbacks.

### 1) Backend
```bash
cd services/api
poetry install
poetry run uvicorn app.main:app --reload --port 8000
```

Health check:
```bash
curl http://localhost:8000/health
```

### 2) Frontend
```bash
cd apps/web
pnpm install
pnpm dev
```

Open:
- Web: http://localhost:5173
- API: http://localhost:8000/docs (OpenAPI)

## Repo map

```
.
├── apps/
│   └── web/                # React client
├── services/
│   └── api/                # FastAPI server (WebSocket authoritative state)
├── docs/                   # Architecture + roadmap + ADRs
├── infra/                  # Dev infra (docker compose: postgres/redis placeholder)
└── tools/                  # Scripts (OpenAPI TS client generation placeholder)
```

## How to use this scaffold

Start with the **generic VTT core**:
1. Lobby + invite link
2. Board rendering + pan/zoom + tokens
3. Measurement tool (continuous coordinates)
4. Server-authoritative actions (move / rotate / roll)
5. Event log + replays

Then implement a **rules module**:
- game phases and turn/activation structure
- combat resolution and special abilities
- scenario objectives and victory conditions
- faction/army data (kept as *data packs* to avoid IP problems)

See:
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/protocol.md`
- `docs/agent-context.md` (fast context for agentic AI sessions)

## License

This scaffold is released under the MIT license (see `LICENSE`).
