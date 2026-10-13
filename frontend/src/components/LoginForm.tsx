import { useState, type FormEvent } from "react";

type LoginFormProps = {
  onLogin: (username: string, password: string) => Promise<boolean>;
};

const labelClass = "block space-y-1.5 text-xs font-semibold text-[var(--navy-dark)]";
const inputClass =
  "w-full rounded-lg border border-[var(--stroke)] bg-white px-3 py-2.5 text-sm font-medium text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)] focus:ring-2 focus:ring-[var(--primary-blue)]/20";

export const LoginForm = ({ onLogin }: LoginFormProps) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(!(await onLogin(username, password)));
  };

  return (
    <main className="grid min-h-screen lg:grid-cols-[1.1fr_1fr]">
      <section className="relative hidden overflow-hidden bg-[linear-gradient(135deg,#032147_0%,#06306a_55%,#0b3f80_100%)] p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="pointer-events-none absolute -right-24 -top-24 h-96 w-96 rounded-full bg-[radial-gradient(circle,rgba(32,157,215,0.45),transparent_65%)]" />
        <div className="pointer-events-none absolute -bottom-32 -left-16 h-[28rem] w-[28rem] rounded-full bg-[radial-gradient(circle,rgba(117,57,145,0.5),transparent_65%)]" />
        <div className="relative flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[linear-gradient(135deg,#ecad0a,#f5c842)] font-display text-lg font-bold text-[var(--navy-dark)]">
            K
          </div>
          <span className="font-display text-lg font-semibold">Kanban Studio</span>
        </div>
        <div className="animate-fade-up relative max-w-md">
          <p className="font-display text-4xl font-semibold leading-tight">
            Keep every stage of your project in view.
          </p>
          <p className="mt-4 text-sm leading-6 text-white/70">
            Drag cards between stages, rename columns, and let the AI assistant
            handle the busywork.
          </p>
        </div>
        <div className="relative h-1 w-24 rounded-full bg-[var(--accent-yellow)]" />
      </section>

      <section className="flex items-center justify-center px-6 py-12">
        <form onSubmit={handleSubmit} className="animate-fade-up w-full max-w-sm space-y-5">
          <div>
            <h1 className="font-display text-3xl font-semibold text-[var(--navy-dark)]">
              Sign in
            </h1>
            <p className="mt-2 text-sm text-[var(--gray-text)]">
              Welcome back. Enter your credentials to continue.
            </p>
          </div>
          <label className={labelClass}>
            <span>Username</span>
            <input
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              className={inputClass}
              autoComplete="username"
              required
            />
          </label>
          <label className={labelClass}>
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className={inputClass}
              autoComplete="current-password"
              required
            />
          </label>
          {error ? (
            <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">
              Invalid username or password
            </p>
          ) : null}
          <button
            type="submit"
            className="w-full rounded-lg bg-[var(--secondary-purple)] px-4 py-2.5 text-sm font-semibold text-white shadow-[0_8px_20px_rgba(117,57,145,0.35)] transition duration-200 hover:-translate-y-px hover:brightness-110"
          >
            Sign in
          </button>
        </form>
      </section>
    </main>
  );
};
