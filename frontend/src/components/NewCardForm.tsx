import { useState, type ComponentProps, type FormEvent } from "react";
import { Plus } from "lucide-react";

const fieldClass =
  "w-full rounded-lg border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition placeholder:text-[var(--gray-text)] focus:border-[var(--primary-blue)] focus:ring-2 focus:ring-[var(--primary-blue)]/20";

type CardFieldsProps = {
  titleProps: ComponentProps<"input">;
  detailsProps: ComponentProps<"textarea">;
  submitLabel: string;
  onCancel: () => void;
};

// Title, details and actions shared by the add and edit card forms.
export const CardFields = ({ titleProps, detailsProps, submitLabel, onCancel }: CardFieldsProps) => (
  <>
    <input {...titleProps} className={`${fieldClass} font-medium`} required autoFocus />
    <textarea {...detailsProps} rows={3} className={`${fieldClass} resize-none`} />
    <div className="flex items-center justify-end gap-2">
      <button
        type="button"
        onClick={onCancel}
        className="rounded-lg px-3 py-1.5 text-xs font-semibold text-[var(--gray-text)] transition hover:bg-[var(--surface)] hover:text-[var(--navy-dark)]"
      >
        Cancel
      </button>
      <button
        type="submit"
        className="rounded-lg bg-[var(--secondary-purple)] px-3.5 py-1.5 text-xs font-semibold text-white shadow-[0_4px_12px_rgba(117,57,145,0.3)] transition hover:brightness-110"
      >
        {submitLabel}
      </button>
    </div>
  </>
);

const initialFormState = { title: "", details: "" };

type NewCardFormProps = {
  onAdd: (title: string, details: string) => void;
};

export const NewCardForm = ({ onAdd }: NewCardFormProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [formState, setFormState] = useState(initialFormState);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!formState.title.trim()) {
      return;
    }
    onAdd(formState.title.trim(), formState.details.trim());
    setFormState(initialFormState);
    setIsOpen(false);
  };

  if (!isOpen) {
    return (
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-sm font-medium text-[var(--gray-text)] transition hover:bg-[color-mix(in_srgb,var(--accent)_10%,transparent)] hover:text-[var(--navy-dark)]"
      >
        <Plus className="h-4 w-4" aria-hidden />
        Add a card
      </button>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="animate-fade-up space-y-2 rounded-xl border border-[var(--stroke)] bg-white p-2.5 shadow-[var(--shadow-card)]"
    >
      <CardFields
        titleProps={{
          value: formState.title,
          onChange: (event) => setFormState((prev) => ({ ...prev, title: event.target.value })),
          placeholder: "Card title",
        }}
        detailsProps={{
          value: formState.details,
          onChange: (event) =>
            setFormState((prev) => ({ ...prev, details: event.target.value })),
          placeholder: "Details",
        }}
        submitLabel="Add card"
        onCancel={() => {
          setIsOpen(false);
          setFormState(initialFormState);
        }}
      />
    </form>
  );
};
