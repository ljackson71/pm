import { useState, type FormEvent } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import clsx from "clsx";
import { Pencil, Trash2 } from "lucide-react";
import type { Card } from "@/lib/kanban";
import { CardFields } from "@/components/NewCardForm";

type KanbanCardProps = {
  card: Card;
  onEdit: (card: Card) => void;
  onDelete: (cardId: string) => void;
};

const iconButtonClass =
  "flex h-7 w-7 items-center justify-center rounded-lg text-[var(--gray-text)] transition duration-150";

export const KanbanCard = ({ card, onEdit, onDelete }: KanbanCardProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: card.id, disabled: isEditing });
  // While editing, drop the drag props: dnd-kit marks a disabled sortable as
  // an aria-disabled button, which would disable the form fields inside it.
  const dragProps = isEditing ? {} : { ...attributes, ...listeners };

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const title = String(form.get("title")).trim();
    if (!title) {
      return;
    }
    onEdit({ ...card, title, details: String(form.get("details")).trim() });
    setIsEditing(false);
  };

  return (
    <article
      ref={setNodeRef}
      style={style}
      className={clsx(
        "group relative shrink-0 rounded-xl border bg-white shadow-[var(--shadow-card)] outline-none",
        "transition-[box-shadow,border-color,opacity] duration-200",
        isEditing
          ? "border-[var(--primary-blue)] p-2.5"
          : "cursor-grab border-[var(--stroke)] py-3 pl-4 pr-3 hover:border-[color-mix(in_srgb,var(--accent)_45%,transparent)] hover:shadow-[var(--shadow-lift)] focus-visible:ring-2 focus-visible:ring-[var(--primary-blue)] active:cursor-grabbing",
        isDragging && "opacity-40 shadow-none"
      )}
      {...dragProps}
      data-testid={`card-${card.id}`}
    >
      {isEditing ? (
        <form onSubmit={handleSubmit} className="space-y-2">
          <CardFields
            titleProps={{ name: "title", defaultValue: card.title, "aria-label": "Edit title" }}
            detailsProps={{
              name: "details",
              defaultValue: card.details,
              "aria-label": "Edit details",
            }}
            submitLabel="Save"
            onCancel={() => setIsEditing(false)}
          />
        </form>
      ) : (
        <>
          <span className="absolute inset-y-3 left-0 w-[3px] rounded-r-full bg-[var(--accent)] opacity-70 transition-opacity group-hover:opacity-100" />
          <h4 className="font-display text-sm font-semibold leading-snug text-[var(--navy-dark)]">
            {card.title}
          </h4>
          {card.details && (
            <p className="mt-1 text-[13px] leading-5 text-[var(--gray-text)]">{card.details}</p>
          )}
          <div className="absolute right-1.5 top-1.5 flex gap-0.5 rounded-lg bg-white/95 p-0.5 opacity-0 shadow-[var(--shadow-card)] backdrop-blur transition-opacity duration-200 group-focus-within:opacity-100 group-hover:opacity-100 [@media(hover:none)]:opacity-100">
            <button
              type="button"
              onClick={() => setIsEditing(true)}
              className={clsx(
                iconButtonClass,
                "hover:bg-[var(--surface)] hover:text-[var(--primary-blue)]"
              )}
              aria-label={`Edit ${card.title}`}
              title="Edit"
            >
              <Pencil className="h-3.5 w-3.5" aria-hidden />
            </button>
            <button
              type="button"
              onClick={() => onDelete(card.id)}
              className={clsx(iconButtonClass, "hover:bg-red-50 hover:text-red-600")}
              aria-label={`Delete ${card.title}`}
              title="Delete"
            >
              <Trash2 className="h-3.5 w-3.5" aria-hidden />
            </button>
          </div>
        </>
      )}
    </article>
  );
};
