import type { Card } from "@/lib/kanban";

type KanbanCardPreviewProps = {
  card: Card;
  accent?: string;
};

export const KanbanCardPreview = ({ card, accent }: KanbanCardPreviewProps) => (
  <article
    style={{ "--accent": accent } as React.CSSProperties}
    className="relative cursor-grabbing rounded-xl border border-[color-mix(in_srgb,var(--accent)_45%,transparent)] bg-white py-3 pl-4 pr-3 shadow-[0_24px_48px_rgba(3,33,71,0.22)]"
  >
    <span className="absolute inset-y-3 left-0 w-[3px] rounded-r-full bg-[var(--accent)]" />
    <h4 className="font-display text-sm font-semibold leading-snug text-[var(--navy-dark)]">
      {card.title}
    </h4>
    {card.details && (
      <p className="mt-1 text-[13px] leading-5 text-[var(--gray-text)]">{card.details}</p>
    )}
  </article>
);
