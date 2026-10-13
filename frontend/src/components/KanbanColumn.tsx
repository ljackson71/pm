import clsx from "clsx";
import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import type { Card, Column } from "@/lib/kanban";
import { KanbanCard } from "@/components/KanbanCard";
import { NewCardForm } from "@/components/NewCardForm";

const accents = ["#209dd7", "#753991", "#ecad0a", "#0fa37f", "#e2557b"];

export const columnAccent = (index: number) => accents[Math.max(index, 0) % accents.length];

type KanbanColumnProps = {
  column: Column;
  accent: string;
  index: number;
  cards: Card[];
  onRename: (columnId: string, title: string) => void;
  onAddCard: (columnId: string, title: string, details: string) => void;
  onEditCard: (card: Card) => void;
  onDeleteCard: (cardId: string) => void;
};

export const KanbanColumn = ({
  column,
  accent,
  index,
  cards,
  onRename,
  onAddCard,
  onEditCard,
  onDeleteCard,
}: KanbanColumnProps) => {
  const { setNodeRef, isOver } = useDroppable({ id: column.id });

  return (
    <section
      ref={setNodeRef}
      style={{ "--accent": accent, animationDelay: `${index * 60}ms` } as React.CSSProperties}
      className={clsx(
        "animate-fade-up flex min-h-0 snap-start flex-col rounded-2xl border bg-white/70 shadow-[var(--shadow-card)] backdrop-blur transition-[border-color,box-shadow,background-color] duration-300",
        isOver
          ? "border-[var(--accent)] bg-white shadow-[0_0_0_3px_color-mix(in_srgb,var(--accent)_22%,transparent)]"
          : "border-[var(--stroke)]"
      )}
      data-testid={`column-${column.id}`}
    >
      <div className="h-1 shrink-0 rounded-t-2xl bg-[var(--accent)]" />
      <div className="flex items-center gap-2 px-4 pb-2 pt-3">
        <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-[var(--accent)]" />
        <input
          key={column.title}
          defaultValue={column.title}
          onBlur={(event) => {
            const title = event.target.value.trim();
            if (title && title !== column.title) {
              onRename(column.id, title);
            } else {
              event.target.value = column.title;
            }
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.currentTarget.blur();
            }
          }}
          className="min-w-0 flex-1 rounded-md bg-transparent px-1 py-0.5 font-display text-[15px] font-semibold text-[var(--navy-dark)] outline-none transition hover:bg-[var(--surface)] focus:bg-[var(--surface)] focus:ring-2 focus:ring-[color-mix(in_srgb,var(--accent)_35%,transparent)]"
          aria-label="Column title"
        />
        <span
          className="rounded-full bg-[color-mix(in_srgb,var(--accent)_14%,transparent)] px-2 py-0.5 text-xs font-semibold tabular-nums text-[var(--navy-dark)]"
          title={`${cards.length} cards`}
        >
          {cards.length}
        </span>
      </div>
      <div className="scroll-thin flex min-h-0 flex-1 flex-col gap-2.5 overflow-y-auto px-3 pb-2 pt-1">
        <SortableContext items={column.cardIds} strategy={verticalListSortingStrategy}>
          {cards.map((card) => (
            <KanbanCard
              key={card.id}
              card={card}
              onEdit={onEditCard}
              onDelete={onDeleteCard}
            />
          ))}
        </SortableContext>
        {cards.length === 0 && (
          <div className="flex flex-1 items-center justify-center rounded-xl border-2 border-dashed border-[var(--stroke)] px-3 py-10 text-center text-xs font-medium text-[var(--gray-text)]">
            Drop a card here
          </div>
        )}
      </div>
      <div className="shrink-0 px-3 pb-3">
        <NewCardForm onAdd={(title, details) => onAddCard(column.id, title, details)} />
      </div>
    </section>
  );
};
