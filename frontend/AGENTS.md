# Frontend

Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, `@dnd-kit` for drag and drop, `lucide-react` for icons. Built as a static export (`output: "export"`) served by the FastAPI backend. In `npm run dev`, `next.config.ts` rewrites `/api/*` to `http://localhost:8000`. The board is loaded from and saved to the backend (`/api/board`).

## Structure

- `src/app/layout.tsx` - root layout; loads Space Grotesk (`--font-display`) and Manrope (`--font-body`) via `next/font/google`.
- `src/app/page.tsx` - renders `App`.
- `src/components/App.tsx` - calls `/api/me` on load; shows `LoginForm` when signed out, otherwise `KanbanBoard`. Handles login and logout requests.
- `src/components/LoginForm.tsx` - username/password form; shows an error when login fails.
- `src/app/globals.css` - Tailwind import and color tokens as CSS variables (`--accent-yellow`, `--primary-blue`, `--secondary-purple`, `--navy-dark`, `--gray-text`, plus surface/stroke/shadow tokens) and shared animations (`animate-fade-up`, `animate-slide-in`, `typing-dot`, `scroll-thin`), disabled under `prefers-reduced-motion`. Components reference tokens via `var(--...)`.
- `src/lib/kanban.ts` - data model and pure logic:
  - `BoardData = { columns: Column[]; cards: Record<string, Card> }`. Columns are ordered and each holds ordered `cardIds`.
  - `initialData` - demo board with 5 columns and 8 cards (the backend seeds new users with a copy; used by tests).
  - `renameColumn`, `addCard`, `updateCard`, `deleteCard` - pure board mutations returning a new `BoardData`.
  - `moveCard(columns, activeId, overId)` - reorders within a column or moves across columns; `overId` may be a card id or a column id (drop at end).
  - `createId(prefix)` - random id generator.
- `src/lib/api.ts` - `getBoard()` and `saveBoard(board)` (chained so saves reach the server in order); `sendChat(message, history)` posts to `/api/chat` and returns `{ reply, board | null }`, throwing on non-2xx.
- `src/components/KanbanBoard.tsx` - client component owning board state. Loads it with `getBoard()` on mount (shows a loading message), and every mutation updates state then calls `saveBoard` with the full board. Uses `DndContext` with `PointerSensor` (6px activation) and `closestCorners`, and handlers for rename column, add card, delete card, and drag end. Full-height layout: a navy header bar (title, card count, AI chat toggle, Log out icon button via `onLogout`) over a horizontally scrolling grid of columns (`auto-cols-[minmax(272px,1fr)]`, scroll snap) that fills the width; each column scrolls its cards vertically. Owns the chat open state.
- `src/components/ChatSidebar.tsx` - AI chat panel beside the board, closed by default and toggled by the header button ("Open AI chat" / "Close AI chat") or its Hide icon button. It stays mounted while hidden (`isOpen` prop) so the conversation survives closing; full-screen on small screens. Keeps the conversation in state and sends it as history with each message; shows a "Thinking..." status while pending and an error on failure. A returned board is passed to `onBoardUpdate` (`KanbanBoard`'s `setBoard`); it is not saved again because the backend already saved it.
- `src/components/KanbanColumn.tsx` - droppable column, given an accent color (`columnAccent(index)`, exposed as the `--accent` CSS variable used by its cards), with an inline-editable title input (uncontrolled; saves on blur or Enter, keyed by title so external changes reset it), a `SortableContext` of cards, and `NewCardForm`.
- `src/components/KanbanCard.tsx` - sortable card with Edit and Delete icon buttons (shown on hover/focus, always on touch) and an inline edit form. While editing, dragging is disabled and the dnd-kit attributes/listeners are not applied, because dnd-kit would mark the card `aria-disabled` and disable the form fields inside it.
- `src/components/KanbanCardPreview.tsx` - card rendering used in the `DragOverlay`.
- `src/components/NewCardForm.tsx` - toggleable form to add a card (title required, details optional). Also exports `CardFields`, the fields and Cancel/submit buttons shared with the card edit form.

## Behavior today

- Columns can be renamed; cards can be added, edited, deleted, and dragged. All changes persist per user.
- Sign in required (`user` / `password`); session survives reload.
- The AI chat sidebar can create, edit, and move cards; changes appear immediately.
- Columns are at least 272px wide and share the available width; the board scrolls horizontally when they do not fit.
- Saves are fire-and-forget: a change made immediately before a page reload can be lost.

## Tests

- Unit (Vitest + Testing Library, jsdom): `src/**/*.test.{ts,tsx}`. Setup in `src/test/setup.ts`. Run `npm run test:unit`.
- E2E (Playwright, chromium): `tests/`. Starts the backend on :8000 (uv) and `npm run dev` on 127.0.0.1:3000. Set `BASE_URL` to test an already-running server (e.g. the container) instead. Tests share one persisted board, so `workers: 1`. The config loads the root `.env` (if present) so the backend it starts and the live chat test (`tests/chat.spec.ts`, skipped without `OPENAI_API_KEY`) have the key. `tests/helpers.ts` has `signIn`, `signInWithDemoBoard` (resets the board via the API; use in `beforeEach`), and `dragCard`. Run `npm run test:e2e`.
- Tests locate elements via `data-testid` (e.g. `column-<id>`) and aria labels.
