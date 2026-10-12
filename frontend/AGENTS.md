# Frontend

Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, `@dnd-kit` for drag and drop. Currently a frontend-only demo: all state is in memory and resets on reload.

## Structure

- `src/app/layout.tsx` - root layout; loads Space Grotesk (`--font-display`) and Manrope (`--font-body`) via `next/font/google`.
- `src/app/page.tsx` - renders `KanbanBoard`.
- `src/app/globals.css` - Tailwind import and color tokens as CSS variables (`--accent-yellow`, `--primary-blue`, `--secondary-purple`, `--navy-dark`, `--gray-text`, plus surface/stroke/shadow). Components reference these via `var(--...)`.
- `src/lib/kanban.ts` - data model and pure logic:
  - `BoardData = { columns: Column[]; cards: Record<string, Card> }`. Columns are ordered and each holds ordered `cardIds`.
  - `initialData` - seed board with 5 columns and 8 cards.
  - `moveCard(columns, activeId, overId)` - reorders within a column or moves across columns; `overId` may be a card id or a column id (drop at end).
  - `createId(prefix)` - random id generator.
- `src/components/KanbanBoard.tsx` - client component owning board state (`useState<BoardData>`), `DndContext` with `PointerSensor` (6px activation) and `closestCorners`, and handlers for rename column, add card, delete card, and drag end.
- `src/components/KanbanColumn.tsx` - droppable column with an inline-editable title input, a `SortableContext` of cards, and `NewCardForm`.
- `src/components/KanbanCard.tsx` - sortable card with delete button.
- `src/components/KanbanCardPreview.tsx` - card rendering used in the `DragOverlay`.
- `src/components/NewCardForm.tsx` - toggleable form to add a card (title required, details optional).

## Behavior today

- Columns can be renamed; cards can be added, deleted, and dragged. Cards cannot yet be edited after creation.
- No auth, no API calls, no persistence.

## Tests

- Unit (Vitest + Testing Library, jsdom): `src/**/*.test.{ts,tsx}`. Setup in `src/test/setup.ts`. Run `npm run test:unit`.
- E2E (Playwright, chromium): `tests/`. Starts `npm run dev` on 127.0.0.1:3000. Run `npm run test:e2e`.
- Tests locate elements via `data-testid` (e.g. `column-<id>`) and aria labels.
