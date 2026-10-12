# Backend

FastAPI app managed with uv. Serves the API under `/api/*` and the Next.js static export at `/`.

- `app/main.py` - FastAPI app. API routes must be registered before the static mount at `/`, which is a catch-all.
  - Auth: `POST /api/login` (hardcoded `user` / `password`), `POST /api/logout`, `GET /api/me` (401 if signed out). Session is a signed cookie via Starlette `SessionMiddleware`; secret from `SESSION_SECRET` (dev default `dev-secret`). Routes needing a user take the `CurrentUser` dependency (401 if signed out).
  - Board: `GET /api/board` (seeds the demo board on first access), `PUT /api/board` (validates and replaces the whole board).
  - Lifespan runs `db.init_db()` on startup.
  - `POST /api/chat` `{message, history}`: sends the board, history and message to the AI; if it returns a board, validates and saves it. Responds `{reply, board | null}`; 502 if the AI board is invalid (nothing saved).
- `app/db.py` - SQLite via stdlib `sqlite3`. Path from `DB_PATH` (default `data/app.db`, relative to the working directory), read on each call. `init_db` creates the file, tables, and the `user` row. Board stored as JSON; schema in `docs/DATABASE.md`.
- `app/ai.py` - OpenAI API via the `openai` SDK, model `gpt-5.4-mini`, key from `OPENAI_API_KEY`. `chat()` uses Structured Outputs (`responses.parse`, `text_format=ChatResult`). The AI works on `ChatBoard`: columns without card lists, and cards as an ordered list each with a `column_id`, so a card cannot be in two columns; `from_board` / `to_board` convert to and from `Board`. The client is created per call so the app starts without a key; tests monkeypatch `ai.client`.
- `app/models.py` - Pydantic `Card`, `Column` (`cardIds` alias), `Board` (rejects column card ids missing from `cards`, 422), and `ChatMessage` / `ChatRequest`.
- `app/demo_board.json` - seed board, a copy of the frontend `initialData`.
- `app/static/` - the Next.js export, copied in by the Dockerfile (not in git). Override with the `STATIC_DIR` env var; the mount is skipped if the directory is missing, so the API runs alone in local dev.
- `tests/` - pytest using FastAPI `TestClient`. `conftest.py` points `DB_PATH` at a temp file for every test. Use `with TestClient(app)` when a test needs the database, so startup runs. `test_ai.py` loads the root `.env`; its live test (add a card, then move it, through `/api/chat`) is skipped when `OPENAI_API_KEY` is not set.

## Commands

Run from `backend/`:

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8000
uv run pytest
uv run pytest tests/test_main.py::test_health
```
