# AGENTS.md

This file provides the minimum context-loading workflow for agentic coding tools (Codex, etc.) in this repository.

## Start Here
1. Read [`docs/agent-context.md`](docs/agent-context.md) first.
2. Use it as the primary project summary and task orientation file.
3. If it conflicts with code, trust code and update `docs/agent-context.md`.

## Working Rules
- Keep this project server-authoritative: clients send commands, server emits events.
- Keep rules/IP separate from VTT core. Do not add copyrighted rules text/art.
- Prefer small, test-backed changes and keep docs in sync when behavior changes.

## When You Finish Work
- Update `docs/agent-context.md` sections:
  - "Current Implementation Snapshot"
  - "Next Recommended Tasks"
  - "Open Decisions / Risks"
- If protocol or data model changed, also update:
  - `docs/protocol.md`
  - `docs/data-model.md`
