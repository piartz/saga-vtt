# Contributing

Thanks for helping! This project is early-stage and optimizes for:
- clarity over cleverness
- server-authoritative behavior
- testability and replayability

## Development setup

### Web
```bash
cd apps/web
pnpm install
pnpm dev
```

### API
```bash
cd services/api
poetry install
poetry run uvicorn app.main:app --reload --port 8000
```

## Suggested workflow
1. Pick an issue from the roadmap (`docs/roadmap.md`)
2. Create a small PR (ideally < 300 lines of code)
3. Include tests where it makes sense
4. Update docs if you change protocol / data model

## Style
- TypeScript: keep components small, prefer pure functions
- Python: ruff formatting/lint, type hints where helpful

## IP / licensing reminder
Do not commit copyrighted rule text, unit profiles, or artwork from commercial games.
Keep rules modules as generic logic and keep faction/unit data in separate “data packs”
that can be privately owned by users who have the rights to them.
