# Backend

FastAPI app managed with uv. Serves the API under `/api/*` and the Next.js static export at `/`.

- `app/main.py` - FastAPI app. API routes must be registered before the static mount at `/`, which is a catch-all.
  - Auth: `POST /api/login` (hardcoded `user` / `password`), `POST /api/logout`, `GET /api/me` (401 if signed out). Session is a signed cookie via Starlette `SessionMiddleware`; secret from `SESSION_SECRET` (dev default `dev-secret`).
- `app/static/` - the Next.js export, copied in by the Dockerfile (not in git). Override with the `STATIC_DIR` env var; the mount is skipped if the directory is missing, so the API runs alone in local dev.
- `tests/` - pytest using FastAPI `TestClient`.

## Commands

Run from `backend/`:

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8000
uv run pytest
uv run pytest tests/test_main.py::test_health
```
