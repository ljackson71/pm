# Project Plan

Each part is completed in order. Check off substeps as they are done. A part is complete only when all its tests pass and its success criteria are met. Parts marked "user sign-off" stop and wait for approval.

## Key decisions

- Single Docker container, one port (8000). FastAPI serves the API under `/api/*` and the statically exported Next.js site at `/`.
- Multi-stage Dockerfile: Node stage runs `next build` with `output: "export"`; Python stage (uv) copies the exported `out/` into the image as static files.
- Frontend calls the API with relative URLs (`/api/...`), so the same build works in the container with no config. In `npm run dev`, a Next.js rewrite proxies `/api` to `localhost:8000`.
- Auth: hardcoded `user` / `password`. Login sets a signed session cookie (Starlette `SessionMiddleware`). All board and chat routes require the session.
- SQLite file at a path from `DB_PATH` env var (default `data/app.db`), mounted as a Docker volume so data survives restarts. Created on startup if missing.
- AI: `openai` Python SDK pointed at `https://openrouter.ai/api/v1`, model `openai/gpt-oss-120b`, key from `OPENROUTER_API_KEY` in root `.env` (passed with `--env-file`).
- Board is read and written as a whole (`GET` / `PUT /api/board`). Simple, and it matches how the AI returns updates.

## Part 1: Plan

- [x] Enrich this document with substeps, tests and success criteria
- [x] Create `frontend/AGENTS.md` describing the existing frontend
- [x] User reviews and approves this plan (user sign-off)

Success: user approves the plan.

## Part 2: Scaffolding

- [x] `backend/pyproject.toml` managed by uv (fastapi, uvicorn); dev deps pytest, httpx2
- [x] `backend/app/main.py` with `GET /api/health` returning `{"status": "ok"}` and a static `hello world` HTML page served at `/`
- [x] `Dockerfile` at repo root (python base with uv, `uv sync`, run uvicorn on 0.0.0.0:8000)
- [x] `.dockerignore` (node_modules, .venv, .next, out, data, .env)
- [x] `scripts/start.sh` and `scripts/stop.sh` (Mac/Linux), `scripts/start.ps1` and `scripts/stop.ps1` (Windows): build image, run container named `pm` with `--env-file .env`, port 8000, data volume; stop removes the container
- [x] Update `backend/AGENTS.md` and `scripts/AGENTS.md`

Tests:
- pytest: `/api/health` returns 200 and expected JSON; `/` returns the hello world HTML

Success: `scripts/start` brings up the container; `http://localhost:8000/` shows hello world; `http://localhost:8000/api/health` returns ok; `scripts/stop` stops it.

## Part 3: Add in Frontend

- [x] Set `output: "export"` in `next.config.ts`; confirm `npm run build` produces `out/`
- [x] Add Node build stage to Dockerfile; copy `out/` into the Python image
- [x] FastAPI mounts the exported site at `/` (`StaticFiles(html=True)`), registered after API routes so `/api/*` still works
- [x] Remove the hello world page

Tests:
- Existing Vitest and Playwright tests still pass
- pytest: `/` returns the built `index.html` when a static dir is present (use a temp dir fixture)
- Playwright run against the container (`baseURL` overridable via env var) loads the board and drags a card

Success: `http://localhost:8000/` in the container shows the Kanban demo, fully interactive.

## Part 4: Fake user sign in

- [x] Backend: `POST /api/login` (checks `user` / `password`, sets session), `POST /api/logout` (clears session), `GET /api/me` (401 if not signed in)
- [x] Session secret from env var `SESSION_SECRET` with a dev default
- [x] Frontend: on load call `/api/me`; show a login form if 401, otherwise the board
- [x] Login form: username, password, submit (purple), error message on bad credentials
- [x] Logout button in the board header
- [x] Next.js dev rewrite of `/api/*` to `http://localhost:8000`

Tests:
- pytest: login success sets cookie; bad credentials return 401; `/api/me` before and after login and after logout
- Vitest: login form renders, submits credentials, shows error on 401, shows board on success
- Playwright: unauthenticated visit shows login; wrong password shows error; correct login shows board; logout returns to login; reload keeps the session

Success: board is only reachable after logging in with `user` / `password`; logout works.

## Part 5: Database modeling (user sign-off)

- [ ] Write `docs/DATABASE.md` proposing the schema and approach. Initial proposal:
  - `users(id INTEGER PK, username TEXT UNIQUE, created_at)`
  - `boards(id INTEGER PK, user_id INTEGER UNIQUE REFERENCES users, data TEXT JSON, updated_at)`
  - Board stored as JSON in the `BoardData` shape the frontend already uses (columns with ordered `cardIds`, `cards` keyed by id). One board per user is enforced by the unique `user_id`; multiple users are supported.
  - On first access, a user's board is seeded with the demo board (5 columns, 8 cards) from the current frontend `initialData`.
- [ ] Include an example board JSON document
- [ ] User reviews and approves the schema

Success: user signs off on `docs/DATABASE.md`.

## Part 6: Backend board API

- [ ] `backend/app/db.py`: create tables on startup if missing (stdlib `sqlite3`); seed the `user` row
- [ ] Seed new boards with the demo data (5 columns, 8 cards)
- [ ] Pydantic models `Card`, `Column`, `Board` mirroring the frontend types
- [ ] `GET /api/board` returns the signed-in user's board (seeding it on first access)
- [ ] `PUT /api/board` validates and replaces the board (rejects card ids in columns that are not in `cards`)

Tests (pytest, temp DB per test via `DB_PATH`):
- DB file and tables are created when missing
- GET returns the seeded board for a new user
- PUT then GET round-trips the board
- PUT with invalid shape or dangling card id returns 422
- Both routes return 401 without a session
- Two users have independent boards (insert a second user directly)

Success: all backend tests pass; data persists across container restarts via the volume.

## Part 7: Frontend + Backend

- [ ] `src/lib/api.ts` with `getBoard()` and `saveBoard(board)`
- [ ] `KanbanBoard` loads the board from the API on mount (loading state) instead of `initialData`
- [ ] Every mutation (move, rename, add, delete) updates local state and saves the full board
- [ ] Column rename saves on blur / Enter rather than per keystroke
- [ ] Add card editing (title and details) since the requirements need it and the demo lacks it

Tests:
- Vitest: board renders data from a mocked API; each mutation calls `saveBoard` with the expected board; card edit updates title and details
- Playwright (against the container): add, edit, move, rename, delete, then reload and verify each change persisted; logout and login again shows the same board

Success: the board is fully persistent per user across reloads and container restarts.

## Part 8: AI connectivity

- [ ] Add `openai` dependency; `backend/app/ai.py` creates a client for OpenRouter using `OPENROUTER_API_KEY`
- [ ] `POST /api/ai/test` sends "What is 2+2?" and returns the model's reply (temporary diagnostic route; removed or kept behind auth)

Tests:
- pytest with the client mocked: route returns the mocked reply
- pytest live test (skipped when `OPENROUTER_API_KEY` is not set): reply contains "4"

Success: live test passes from inside the container.

## Part 9: AI with board context and structured outputs

- [ ] `POST /api/chat` body: `{ message, history: [{role, content}] }`
- [ ] Backend builds the prompt: system instructions describing the board format and rules, the current board JSON, history, and the new message
- [ ] Call with `response_format` JSON schema (Structured Outputs) for `{ reply: string, board: Board | null }`
- [ ] If `board` is present, validate it with the Pydantic `Board` model and save it; respond with `{ reply, board }`
- [ ] Remove the Part 8 test route

Tests:
- pytest with mocked client: reply-only response leaves the board unchanged; response with a board saves it; invalid board from the model returns an error and does not save; history and board JSON are included in the request sent to the model
- Live tests (skipped without key): "add a card called X to Backlog" results in a saved board containing X in Backlog; "move X to Done" moves it

Success: chat can create, edit and move one or more cards via natural language, and changes persist.

## Part 10: AI chat sidebar

- [ ] `ChatSidebar` component: collapsible right sidebar, message list, input, send button (purple), pending indicator
- [ ] Conversation history kept in component state and sent with each message
- [ ] When the response includes a board, replace the board state so the UI updates immediately
- [ ] Styling uses the project color scheme and matches the existing board design

Tests:
- Vitest with mocked API: sending shows user message, pending state, then the reply; a response with a board updates the rendered columns and cards; error shows a message
- Playwright (live, skipped without key): ask the AI to add a card and see it appear on the board without reload

Success: user can chat with the AI in the sidebar, and AI-driven board changes appear immediately and persist.
