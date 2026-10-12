# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

The project is built in phases defined in `docs/PLAN.md`. Read it before starting work, and check off substeps there as they are completed. Several phases require explicit user sign-off before proceeding (the plan itself in Part 1, the database schema in Part 5).

## Current state

Parts 2-3 are done: a multi-stage `Dockerfile` builds the Next.js static export (`output: "export"`) and FastAPI serves it at `/` alongside `/api/health`; start/stop scripts in `scripts/`. See `backend/AGENTS.md` and `scripts/AGENTS.md`; keep them updated as those parts grow.

## Backend and Docker commands

```bash
cd backend && uv run pytest                      # all backend tests
cd backend && uv run pytest tests/test_main.py::test_health
cd backend && uv run uvicorn app.main:app --reload --port 8000
scripts/start.sh  | scripts/start.ps1            # build image and run container "pm" on :8000
scripts/stop.sh   | scripts/stop.ps1
```

## Frontend commands

Run from `frontend/`:

```bash
npm install
npm run dev              # Next.js dev server on :3000
npm run build
npm run lint
npm run test:unit        # Vitest (jsdom), files matching src/**/*.{test,spec}.{ts,tsx}
npm run test:e2e         # Playwright (chromium), tests/ dir; auto-starts dev server on 127.0.0.1:3000
npx vitest run src/lib/kanban.test.ts        # single unit test file
npx vitest run -t "test name"                # single unit test by name
npx playwright test tests/kanban.spec.ts     # single e2e file
BASE_URL=http://localhost:8000 npx playwright test   # e2e against the running container (no dev server)
```

## Frontend architecture

- Next.js 16 App Router, React 19, Tailwind v4, `@dnd-kit` for drag and drop. Path alias `@/` maps to `frontend/src/`.
- `src/app/page.tsx` renders `KanbanBoard`, which owns all board state in a single `useState<BoardData>` seeded from `initialData`. There is no persistence yet; state is lost on reload.
- `src/lib/kanban.ts` holds the data model and pure logic: `BoardData` is normalized as an ordered `columns` array (each with ordered `cardIds`) plus a `cards` record keyed by id. `moveCard` handles both reordering within a column and moving across columns (drop target may be a card id or a column id). Keep board mutations as pure functions here so they stay unit-testable and can later be reused when applying AI-driven or backend updates.
- Components (`KanbanColumn`, `KanbanCard`, `KanbanCardPreview` for the drag overlay, `NewCardForm`) are presentational; mutations flow up via callbacks to `KanbanBoard`.

## Target architecture (per AGENTS.md / PLAN.md)

FastAPI backend in `backend/` (managed with `uv`) serves the statically exported Next.js build at `/` plus API routes, backed by SQLite (created on first run). Everything runs in a single Docker container started/stopped via scripts in `scripts/` for Mac, Windows, and Linux. AI chat calls OpenRouter (`openai/gpt-oss-120b`, key in root `.env`) with the board JSON and conversation history, and receives a structured output containing a reply plus an optional board update.
