import type { ReactNode } from "react";
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
 * one connected flow: same panel, same card, same entrance animation, same
 * theme toggle. Base classes describe the light theme; `dark:` overrides
 * describe the default dark theme (dark is the default — see useTheme).
 *
 * The side panel states the crypto model in honest, specific terms instead
 * of "bank-level security" boilerplate.
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
    <div className="min-h-screen bg-slate-100 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <header className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-5">
        <Link
          to="/"
          className="flex items-center gap-2.5 rounded-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-blue-500 dark:focus-visible:outline-blue-400"
          aria-label="SecureVault home"
        >
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600 text-white">
            <IconShield />
          </span>
          <span className="text-base font-bold tracking-tight">SecureVault</span>
        </Link>
        <div className="flex items-center gap-3">
          <span
            className="hidden font-mono text-[11px] uppercase tracking-widest text-slate-500 dark:text-slate-500 sm:inline"
            aria-hidden="true"
          >
            AES-256-GCM · RSA-4096
          </span>
          <button
            type="button"
            onClick={toggle}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:border-slate-400 hover:text-slate-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-slate-700 dark:hover:text-white dark:focus-visible:outline-blue-400"
            aria-label={
              theme === "dark" ? "Switch to light mode" : "Switch to dark mode"
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
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-blue-600 dark:text-blue-400">
            Server-side sealed vault
          </p>
          <h1 className="mt-4 max-w-md text-4xl font-extrabold leading-[1.08] tracking-tight">
            Ciphertext at rest.
            <br />
            <span className="text-slate-500 dark:text-slate-400">
              Plaintext never touches disk.
            </span>
          </h1>
          <dl className="mt-8 max-w-md space-y-3 font-mono text-[13px] leading-relaxed">
            {[
              ["AES-256-GCM", "per-file session keys, authenticated + integrity-checked"],
              ["RSA-4096", "per-user parent keys wrap each session key"],
              ["Argon2id", "slow password hashing with lockout"],
              ["hash-chained log", "every security event, tamper-evident"]
            ].map(([term, def]) => (
              <div
                key={term}
                className="flex gap-3 rounded-lg border border-slate-200 bg-white px-4 py-3 dark:border-slate-800/80 dark:bg-slate-900/60"
              >
                <dt className="shrink-0 font-semibold text-blue-700 dark:text-blue-300">
                  {term}
                </dt>
                <dd className="text-slate-600 dark:text-slate-400">{def}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-6 max-w-md text-sm leading-relaxed text-slate-500 dark:text-slate-500">
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
          <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-modal dark:border-slate-800 dark:bg-slate-900">
            <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.2em] text-blue-600 dark:text-blue-400">
              {eyebrow}
            </p>
            <h2
              id="auth-title"
              className="mt-2 text-2xl font-extrabold tracking-tight"
            >
              {title}
            </h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              {subtitle}
            </p>
            <div className="mt-6">{children}</div>
          </div>
          {footer && (
            <div className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
              {footer}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
