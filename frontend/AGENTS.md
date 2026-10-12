# Frontend

Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, `@dnd-kit` for drag and drop. Built as a static export (`output: "export"`) served by the FastAPI backend. In `npm run dev`, `next.config.ts` rewrites `/api/*` to `http://localhost:8000`. Board state is still in memory and resets on reload.

## Structure

- `src/app/layout.tsx` - root layout; loads Space Grotesk (`--font-display`) and Manrope (`--font-body`) via `next/font/google`.
- `src/app/page.tsx` - renders `App`.
- `src/components/App.tsx` - calls `/api/me` on load; shows `LoginForm` when signed out, otherwise `KanbanBoard`. Handles login and logout requests.
- `src/components/LoginForm.tsx` - username/password form; shows an error when login fails.
- `src/app/globals.css` - Tailwind import and color tokens as CSS variables (`--accent-yellow`, `--primary-blue`, `--secondary-purple`, `--navy-dark`, `--gray-text`, plus surface/stroke/shadow). Components reference these via `var(--...)`.
- `src/lib/kanban.ts` - data model and pure logic:
  - `BoardData = { columns: Column[]; cards: Record<string, Card> }`. Columns are ordered and each holds ordered `cardIds`.
  - `initialData` - seed board with 5 columns and 8 cards.
  - `moveCard(columns, activeId, overId)` - reorders within a column or moves across columns; `overId` may be a card id or a column id (drop at end).
  - `createId(prefix)` - random id generator.
- `src/components/KanbanBoard.tsx` - client component owning board state (`useState<BoardData>`), `DndContext` with `PointerSensor` (6px activation) and `closestCorners`, and handlers for rename column, add card, delete card, and drag end. Header has a Log out button (`onLogout` prop).
- `src/components/KanbanColumn.tsx` - droppable column with an inline-editable title input, a `SortableContext` of cards, and `NewCardForm`.
- `src/components/KanbanCard.tsx` - sortable card with delete button.
- `src/components/KanbanCardPreview.tsx` - card rendering used in the `DragOverlay`.
- `src/components/NewCardForm.tsx` - toggleable form to add a card (title required, details optional).

## Behavior today

- Columns can be renamed; cards can be added, deleted, and dragged. Cards cannot yet be edited after creation.
- Sign in required (`user` / `password`); session survives reload. No board persistence yet.

## Tests

- Unit (Vitest + Testing Library, jsdom): `src/**/*.test.{ts,tsx}`. Setup in `src/test/setup.ts`. Run `npm run test:unit`.
- E2E (Playwright, chromium): `tests/`. Starts the backend on :8000 (uv) and `npm run dev` on 127.0.0.1:3000. Set `BASE_URL` to test an already-running server (e.g. the container) instead. `tests/helpers.ts` has `signIn`. Run `npm run test:e2e`.
- Tests locate elements via `data-testid` (e.g. `column-<id>`) and aria labels.
