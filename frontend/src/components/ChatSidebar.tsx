import { useEffect, useRef, useState, type FormEvent } from "react";
import clsx from "clsx";
import { ArrowUp, Sparkles, X } from "lucide-react";
import { sendChat, type ChatMessage } from "@/lib/api";
import type { BoardData } from "@/lib/kanban";

type ChatSidebarProps = {
  isOpen: boolean;
  onBoardUpdate: (board: BoardData) => void;
  onClose: () => void;
};

export const ChatSidebar = ({ isOpen, onBoardUpdate, onClose }: ChatSidebarProps) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isPending, setIsPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const listEndRef = useRef<HTMLLIElement>(null);

  useEffect(() => {
    listEndRef.current?.scrollIntoView?.({ behavior: "smooth", block: "end" });
  }, [messages, isPending, isOpen]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const message = input.trim();
    if (!message || isPending) {
      return;
    }
    const history = messages;
    setMessages([...history, { role: "user", content: message }]);
    setInput("");
    setError(null);
    setIsPending(true);
    try {
      const response = await sendChat(message, history);
      setMessages((prev) => [...prev, { role: "assistant", content: response.reply }]);
      if (response.board) {
        onBoardUpdate(response.board);
      }
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setIsPending(false);
    }
  };

  // Stays mounted while hidden so the conversation survives closing the panel.
  if (!isOpen) {
    return null;
  }

  return (
    <aside
      aria-label="AI chat"
      className="animate-slide-in flex w-[380px] shrink-0 max-sm:fixed max-sm:inset-0 max-sm:z-20 max-sm:w-full flex-col border-l border-[var(--stroke)] bg-white shadow-[-12px_0_32px_rgba(3,33,71,0.08)]"
    >
      <header className="flex items-center justify-between border-b border-[var(--stroke)] px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[linear-gradient(135deg,#753991,#209dd7)] text-white shadow-[0_6px_16px_rgba(117,57,145,0.35)]">
            <Sparkles className="h-4 w-4" aria-hidden />
          </div>
          <div>
            <h2 className="font-display text-base font-semibold leading-tight text-[var(--navy-dark)]">
              AI assistant
            </h2>
            <p className="text-xs text-[var(--gray-text)]">Creates, edits and moves cards</p>
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Hide"
          title="Hide"
          className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--gray-text)] transition hover:bg-[var(--surface)] hover:text-[var(--navy-dark)]"
        >
          <X className="h-4 w-4" aria-hidden />
        </button>
      </header>

      <ol className="scroll-thin flex flex-1 flex-col gap-3 overflow-y-auto bg-[var(--surface)]/60 px-5 py-5">
        {messages.length === 0 && (
          <li className="rounded-xl border border-dashed border-[var(--stroke)] bg-white px-4 py-3 text-sm leading-6 text-[var(--gray-text)]">
            Ask me to add, edit, or move cards. For example: &quot;Add a card to
            Backlog called Plan the launch.&quot;
          </li>
        )}
        {messages.map((message, index) => (
          <li
            key={index}
            className={clsx(
              "animate-fade-up max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm leading-6",
              message.role === "user"
                ? "self-end rounded-br-md bg-[linear-gradient(135deg,#209dd7,#1b7fc0)] text-white shadow-[0_6px_16px_rgba(32,157,215,0.25)]"
                : "self-start rounded-bl-md border border-[var(--stroke)] bg-white text-[var(--navy-dark)] shadow-[var(--shadow-card)]"
            )}
          >
            {message.content}
          </li>
        ))}
        {isPending && (
          <li
            role="status"
            className="flex items-center gap-2 self-start rounded-2xl rounded-bl-md border border-[var(--stroke)] bg-white px-4 py-3 text-sm text-[var(--gray-text)]"
          >
            <span className="flex gap-1" aria-hidden>
              {[0, 150, 300].map((delay) => (
                <span
                  key={delay}
                  className="typing-dot h-1.5 w-1.5 rounded-full bg-[var(--secondary-purple)]"
                  style={{ animationDelay: `${delay}ms` }}
                />
              ))}
            </span>
            Thinking...
          </li>
        )}
        {error && (
          <li className="self-start rounded-xl bg-red-50 px-4 py-2 text-sm text-red-600">
            {error}
          </li>
        )}
        <li ref={listEndRef} aria-hidden className="h-0" />
      </ol>

      <form onSubmit={handleSubmit} className="border-t border-[var(--stroke)] p-4">
        <div className="flex items-center gap-2 rounded-xl border border-[var(--stroke)] bg-white py-1.5 pl-4 pr-1.5 transition focus-within:border-[var(--primary-blue)] focus-within:ring-2 focus-within:ring-[var(--primary-blue)]/20">
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask the AI..."
            aria-label="Message"
            className="min-w-0 flex-1 bg-transparent text-sm text-[var(--navy-dark)] outline-none placeholder:text-[var(--gray-text)]"
          />
          <button
            type="submit"
            disabled={isPending}
            aria-label="Send"
            title="Send"
            className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--secondary-purple)] text-white transition hover:brightness-110 disabled:opacity-50"
          >
            <ArrowUp className="h-4 w-4" aria-hidden />
          </button>
        </div>
      </form>
    </aside>
  );
};
