"use client";

import { useEffect, useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { LogOut, Sparkles } from "lucide-react";
import { KanbanColumn, columnAccent } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import { ChatSidebar } from "@/components/ChatSidebar";
import { getBoard, saveBoard } from "@/lib/api";
import {
  addCard,
  createId,
  deleteCard,
  moveCard,
  renameColumn,
  updateCard,
  type BoardData,
  type Card,
} from "@/lib/kanban";

type KanbanBoardProps = {
  onLogout: () => void;
};

export const KanbanBoard = ({ onLogout }: KanbanBoardProps) => {
  const [board, setBoard] = useState<BoardData | null>(null);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [isChatOpen, setIsChatOpen] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    })
  );

  useEffect(() => {
    getBoard().then(setBoard);
  }, []);

  if (!board) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="animate-pulse text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
          Loading board...
        </p>
      </div>
    );
  }

  const update = (next: BoardData) => {
    setBoard(next);
    saveBoard(next);
  };

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    if (!over || active.id === over.id) {
      return;
    }

    update({
      ...board,
      columns: moveCard(board.columns, active.id as string, over.id as string),
    });
  };

  const handleRenameColumn = (columnId: string, title: string) => {
    update(renameColumn(board, columnId, title));
  };

  const handleAddCard = (columnId: string, title: string, details: string) => {
    const id = createId("card");
    update(
      addCard(board, columnId, { id, title, details: details || "No details yet." })
    );
  };

  const handleEditCard = (card: Card) => {
    update(updateCard(board, card));
  };

  const handleDeleteCard = (cardId: string) => {
    update(deleteCard(board, cardId));
  };

  const activeCard = activeCardId ? board.cards[activeCardId] : null;
  const activeAccent = activeCardId
    ? columnAccent(board.columns.findIndex((column) => column.cardIds.includes(activeCardId)))
    : undefined;
  const cardCount = Object.keys(board.cards).length;

  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <header className="relative z-10 flex shrink-0 items-center justify-between gap-4 bg-[linear-gradient(110deg,#032147_0%,#06306a_60%,#0b3f80_100%)] px-6 py-4 text-white max-sm:px-4 shadow-[0_8px_24px_rgba(3,33,71,0.25)]">
        <div className="flex items-center gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[linear-gradient(135deg,#ecad0a,#f5c842)] font-display text-lg font-bold text-[var(--navy-dark)] shadow-[0_6px_16px_rgba(236,173,10,0.35)]">
            K
          </div>
          <div>
            <h1 className="whitespace-nowrap font-display text-xl font-semibold leading-tight tracking-tight">
              Kanban Studio
            </h1>
            <p className="text-xs text-white/60">
              {board.columns.length} stages &middot; {cardCount} cards
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setIsChatOpen((open) => !open)}
            aria-pressed={isChatOpen}
            className="flex shrink-0 items-center gap-2 rounded-full bg-[var(--secondary-purple)] px-4 py-2 max-sm:px-2.5 text-sm font-semibold text-white shadow-[0_6px_18px_rgba(117,57,145,0.45)] transition duration-200 hover:-translate-y-px hover:brightness-110 aria-pressed:bg-white aria-pressed:text-[var(--secondary-purple)]"
          >
            <Sparkles className="h-4 w-4" aria-hidden />
            <span className="max-sm:sr-only">{isChatOpen ? "Close AI chat" : "Open AI chat"}</span>
          </button>
          <button
            type="button"
            onClick={onLogout}
            aria-label="Log out"
            title="Log out"
            className="flex h-9 w-9 items-center justify-center rounded-full text-white/70 transition duration-200 hover:bg-white/10 hover:text-white"
          >
            <LogOut className="h-4 w-4" aria-hidden />
          </button>
        </div>
      </header>

      <div className="flex min-h-0 flex-1">
        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
          onDragCancel={() => setActiveCardId(null)}
        >
          <main className="scroll-thin grid min-w-0 flex-1 snap-x snap-proximity auto-cols-[minmax(272px,1fr)] grid-flow-col grid-rows-[minmax(0,1fr)] gap-4 overflow-x-auto scroll-smooth scroll-px-6 px-6 py-6 max-sm:scroll-px-4 max-sm:px-4">
            {board.columns.map((column, index) => (
              <KanbanColumn
                key={column.id}
                column={column}
                accent={columnAccent(index)}
                index={index}
                cards={column.cardIds.map((cardId) => board.cards[cardId])}
                onRename={handleRenameColumn}
                onAddCard={handleAddCard}
                onEditCard={handleEditCard}
                onDeleteCard={handleDeleteCard}
              />
            ))}
          </main>
          <DragOverlay dropAnimation={{ duration: 220, easing: "cubic-bezier(0.22, 1, 0.36, 1)" }}>
            {activeCard ? (
              <div className="w-[272px] rotate-[2deg] scale-[1.03]">
                <KanbanCardPreview card={activeCard} accent={activeAccent} />
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>
        <ChatSidebar
          isOpen={isChatOpen}
          onBoardUpdate={setBoard}
          onClose={() => setIsChatOpen(false)}
        />
      </div>
    </div>
  );
};
