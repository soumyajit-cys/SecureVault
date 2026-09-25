import { useEffect, useRef, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { IconShield } from "@/components/layout/Sidebar";
import { useTheme } from "@/hooks/useTheme";

interface AuthLayoutProps {
  eyebrow: string;
  title: string;
  subtitle: string;
  children: ReactNode;
  /** Cross-link rendered under the card, e.g. "No account? Create one". */
  footer?: ReactNode;
}

/**
 * Shared shell for the sign-in / register / recovery pages so they read as
 * one connected flow: same dark-first panel, same card, same entrance
 * animation, same theme toggle. The left panel explains the crypto model in
 * honest, specific terms instead of "bank-level security" boilerplate.
 */
export default function AuthLayout({
  eyebrow,
  title,
  subtitle,
  children,
  footer
}: AuthLayoutProps) {
  const { theme, toggle } = useTheme();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 dark:bg-slate-950 dark:text-slate-100">
      {/* Light-mode support: when toggled, the `dark` class is removed and
          these light: overrides take over. Base styles are the dark theme. */}
      <div className="min-h-screen bg-slate-950 text-slate-100 light:bg-slate-100 light:text-slate-900">
        <header className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-5">
          <Link
            to="/"
            className="flex items-center gap-2.5 rounded-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-blue-400"
            aria-label="SecureVault home"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600 text-white">
              <IconShield />
            </span>
            <span className="text-base font-bold tracking-tight">
              SecureVault
            </span>
          </Link>
          <div className="flex items-center gap-3">
            <span
              className="hidden font-mono text-[11px] uppercase tracking-widest text-slate-500 sm:inline"
              aria-hidden="true"
            >
              AES-256-GCM · RSA-4096
            </span>
            <button
              type="button"
              onClick={toggle}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs font-medium text-slate-300 transition-colors hover:border-slate-700 hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-400"
              aria-label={
                theme === "dark"
                  ? "Switch to light mode"
                  : "Switch to dark mode"
              }
              aria-pressed={theme === "light"}
            >
              <span aria-hidden="true">{theme === "dark" ? "◐" : "◑"}</span>
              {theme === "dark" ? "Light" : "Dark"}
            </button>
          </div>
        </header>

        <main className="mx-auto grid w-full max-w-6xl gap-10 px-6 pb-16 pt-6 lg:grid-cols-[1.05fr_0.95fr] lg:items-center lg:pt-12">
          {/* Explainer panel */}
          <section
            className="hidden animate-fade-up lg:block"
            aria-label="How SecureVault protects data"
          >
            <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-blue-400">
              Server-side sealed vault
            </p>
            <h1 className="mt-4 max-w-md text-4xl font-extrabold leading-[1.08] tracking-tight">
              Ciphertext at rest.
              <br />
              <span className="text-slate-400">Plaintext never touches disk.</span>
            </h1>
            <dl className="mt-8 max-w-md space-y-4 font-mono text-[13px] leading-relaxed">
              {[
                ["AES-256-GCM", "per-file session keys, authenticated + integrity-checked"],
                ["RSA-4096", "per-user parent keys wrap each session key"],
                ["Argon2id", "slow password hashing with lockout"],
                ["hash-chained log", "every security event, tamper-evident"]
              ].map(([term, def]) => (
                <div
                  key={term}
                  className="flex gap-3 rounded-lg border border-slate-800/80 bg-slate-900/60 px-4 py-3"
                >
                  <dt className="shrink-0 font-semibold text-blue-300">{term}</dt>
                  <dd className="text-slate-400">{def}</dd>
                </div>
              ))}
            </dl>
            <p className="mt-6 max-w-md text-sm leading-relaxed text-slate-500">
              Honest scope: the server holds keys in memory while it seals and
              opens your files, so this is hardened server-side custody — not
              zero-knowledge. A stolen disk alone reveals nothing.
            </p>
          </section>

          {/* Form panel */}
          <section
            className="mx-auto w-full max-w-md animate-fade-up [animation-delay:120ms]"
            aria-labelledby="auth-title"
          >
            <div className="mb-6 text-center lg:hidden">
              <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.2em] text-blue-400">
                {eyebrow}
              </p>
            </div>
            <div className="rounded-2xl border border-slate-800 bg-slate-900 p-8 shadow-modal">
              <div className="mb-6 hidden lg:block">
                <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.2em] text-blue-400">
                  {eyebrow}
                </p>
                <h2
                  id="auth-title"
                  className="mt-2 text-2xl font-extrabold tracking-tight text-white"
                >
                  {title}
                </h2>
                <p className="mt-1 text-sm text-slate-400">{subtitle}</p>
              </div>
              <div className="mb-6 lg:hidden">
                <h2
                  id="auth-title"
                  className="text-center text-2xl font-extrabold tracking-tight text-white"
                >
                  {title}
                </h2>
                <p className="mt-1 text-center text-sm text-slate-400">
                  {subtitle}
                </p>
              </div>
              {children}
            </div>
            {footer && (
              <div className="mt-6 text-center text-sm text-slate-400">
                {footer}
              </div>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}

/** Re-exported so pages share one import point. */
export function useAuthTheme() {
  const ref = useRef(false);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    if (!ref.current) {
      ref.current = true;
      setReady(true);
    }
  }, []);
  return ready;
}
