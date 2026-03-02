.PHONY: help dev api web

help:
	@echo "Targets:"
	@echo "  make api   - run FastAPI with reload (port 8000)"
	@echo "  make web   - run web dev server (port 5173)"
	@echo "  make dev   - run both (requires two terminals unless you use a process manager)"

api:
	cd services/api && poetry install && poetry run uvicorn app.main:app --reload --port 8000

web:
	cd apps/web && pnpm install && pnpm dev

dev:
	@echo "Run 'make api' in one terminal and 'make web' in another."
