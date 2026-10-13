# Code Review

Scope: whole repository at `8482b88` (branch `add-claude-md`): backend, frontend, Docker and scripts.

Checks run:
- `uv run pytest`: 19 passed
- `npx vitest run`: 22 passed
- `npm run lint`: clean
- `npx tsc --noEmit`: 98 errors, all in test files (see 9)

Overall the code is small, readable and matches the plan. Board mutations are pure and tested, the API surface is minimal, and the AI board round-trip (`ChatBoard.from_board` / `to_board`) is a tidy design. The findings below are ordered by severity.

## Medium

### 1. A chat reply overwrites board edits made while the AI is thinking
`backend/app/main.py:81-89`, `frontend/src/components/KanbanBoard.tsx:180`

`/api/chat` reads the board when the request starts. It saves the AI's full board when the request ends, which takes several seconds. The chat input is disabled while a request is pending, but the board is not. If the user drags, edits or adds a card in that window, the change is saved by `PUT /api/board` and then silently replaced, both on the server and in the UI via `onBoardUpdate={setBoard}`.

Scenario: send "add a card to Backlog", then drag card-6 to Done before the reply arrives. When the reply lands, card-6 is back in Review.

Simplest fix: disable board interactions while a chat request is pending. Or, in `chat`, have the AI return its board without saving it, and let the client apply and save it through the normal path.

### 2. Nothing enforces fixed columns on AI board updates
`backend/app/ai.py:59-78`

Only the prompt says columns are fixed. `to_board` accepts a board with columns dropped, added or re-keyed, and the result is saved. If the model drops a column, every card in it is deleted with no error. `to_board` should take the current board and reject any change to column ids or their order, just as it already rejects unknown column ids. This matches the business rule that columns are fixed.

### 3. Frontend ignores failed loads and saves
`frontend/src/lib/api.ts:3-20`

- `getBoard` parses the body without checking `response.ok`. On a 401 (expired session cookie), `setBoard({detail: "Not signed in"})` runs and `KanbanBoard` crashes on `board.columns.map`, leaving a blank page.
- `saveBoard` never checks the response. A failed `PUT` (401, 422 or backend down) leaves the UI showing changes that were never saved, and they disappear on reload without warning.

A check like the one `sendChat` already has, plus a visible error state, would cover both.

### 4. The session secret defaults to a public value in the container
`backend/app/main.py:15`, `scripts/start.*`

`SESSION_SECRET` falls back to `"dev-secret"`, and neither the Dockerfile nor `.env` sets it, so the running container uses that value. With a known secret, anyone can forge a signed session cookie for any username. This is acceptable for a local-only MVP. Still, add `SESSION_SECRET` to `.env`, or generate a random one per process with `secrets.token_hex()`; that signs everyone out on restart, which is fine here.

## Low

### 5. Backend accepts structurally inconsistent boards
`backend/app/models.py:18-28`

The validator checks that every `cardIds` entry exists, but not that:
- each card appears in exactly one column (a card listed twice renders twice, and `ChatBoard.to_board` later fails with "Duplicate card ids", so chat stops working for that user)
- `cards` keys match `card.id`
- every card is in some column (orphans are stored but never shown)

The frontend never produces these, but `PUT /api/board` is the trust boundary. Adding a single "every card in exactly one column" check would cover the first and third cases.

### 6. Unhandled OpenAI failures return a bare 500
`backend/app/ai.py:93-102`, `backend/app/main.py:82`

Network or API errors raise out of the route. If the model refuses, `output_parsed` is `None`, and `result.board` raises `AttributeError`. The frontend shows a generic error either way, so users are not affected. The logs, however, show a stack trace instead of a clear cause, and the route's own 502 path for an invalid board goes unused in these cases. Optional: map these errors to a 502 as well.

### 7. `db.get_board` crashes for a username with no `users` row
`backend/app/db.py:54`

`fetchone()` returns `None` when the user doesn't exist, so `row[0]` raises `TypeError`. This can't happen today, because only `user` can sign in and that row is seeded. It will matter once real users exist (the database is designed for multiple users).

### 8. App hangs on "loading" if `/api/me` fails
`frontend/src/components/App.tsx:12-16`

If the backend is unreachable, the fetch promise rejects, `auth` stays `"loading"` and the page stays blank. Low impact, since frontend and backend are served together.

### 9. Test files don't typecheck
`frontend/src/test/vitest.d.ts`, `frontend/vitest.config.ts:9`

`globals: true` is set, but the `describe`/`it`/`expect` globals are not typed: `/// <reference types="vitest" />` does not declare them. Tests run, but `tsc --noEmit` reports 98 errors and editors show red squiggles. Fix: change the reference to `/// <reference types="vitest/globals" />`, or import from `vitest` explicitly.

### 10. Demo board is defined twice
`frontend/src/lib/kanban.ts:18-72`, `backend/app/demo_board.json`

`initialData` is now used only by tests (`App.test.tsx`, `tests/helpers.ts`) and duplicates the backend seed. If one changes, the e2e reset (`signInWithDemoBoard`) and the backend seed drift apart. Consider having tests import `backend/app/demo_board.json` and deleting `initialData`.

## Nits

- `frontend/test-results/.last-run.json` is committed. It is Playwright output and should be gitignored (`.dockerignore` already excludes it).
- `createId` (`kanban.ts:164`) could be `` `${prefix}-${crypto.randomUUID()}` ``.
- `ai.client()` builds a new `OpenAI()` for each request. That is harmless at this scale, and keeping it as a function makes the test monkeypatching easy, so it can stay.
- Cards spread dnd-kit `attributes` (role `button`, `tabIndex`) but there is no `KeyboardSensor`, so cards are focusable yet can't be moved with the keyboard.
- `test_root_serves_static_index` calls `importlib.reload(app.main)` and leaves the reloaded module in place for any later test that imports it. It works today, but the tests depend on run order.
