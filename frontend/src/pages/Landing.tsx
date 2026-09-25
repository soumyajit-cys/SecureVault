import { Link } from "react-router-dom";

import Reveal from "@/components/auth/Reveal";
import ScrambleText from "@/components/auth/ScrambleText";
import { IconShield } from "@/components/layout/Sidebar";
import { useTheme } from "@/hooks/useTheme";
import { useAuthStore } from "@/store/authStore";

const SPEC = [
  ["AES-256-GCM", "authenticated encryption, unique nonce per message"],
  ["RSA-4096-OAEP", "per-user parent keys wrap each file's session key"],
  ["Argon2id", "slow password hashing + lockout throttling"],
  ["SHA-256", "integrity verified on every open"]
] as const;

const SEAL_STEPS = [
  {
    n: "01",
    op: "seal",
    title: "Fresh session key per file",
    desc: "Uploads generate a random 256-bit key. The plaintext is encrypted in a stream and never written to disk."
  },
  {
    n: "02",
    op: "wrap",
    title: "Key wrapped to your RSA-4096 parent",
    desc: "The session key is sealed with your public key and stored beside the ciphertext — only the private half re-opens it."
  },
  {
    n: "03",
    op: "store",
    title: "One container, ciphertext only",
    desc: "magic + header + nonce + ciphertext + tag + wrapped key. Lose the keys and the bytes are noise."
  },
  {
    n: "04",
    op: "verify",
    title: "Verified on every open",
    desc: "Header, tag and SHA-256 are checked before a single byte is streamed back. Tampering fails closed."
  }
] as const;

const FEATURES = [
  {
    title: "MFA & passkeys",
    desc: "TOTP with recovery codes, plus FIDO2 passkeys for passwordless sign-in. Workspaces can enforce MFA by policy.",
    mono: "TOTP · WebAuthn"
  },
  {
    title: "Roles, not just logins",
    desc: "User, Admin and Auditor roles enforced server-side on every query. Ownership-scoped reads — no IDOR by design.",
    mono: "RBAC · ownership scope"
  },
  {
    title: "Audit trail that can't be quietly edited",
    desc: "Every security event is hash-chained and exportable to CSV. Admins can verify the chain on demand.",
    mono: "hash-chain · CSV export"
  },
  {
    title: "Key rotation & revocation",
    desc: "Rotate parent keys on a schedule, revoke compromised ones instantly. Old containers stay readable under their recorded key.",
    mono: "rotate · revoke · expire"
  },
  {
    title: "Sealed sharing",
    desc: "Share files by wrapping the session key to the grantee's public key. Owner-only grant and revoke, grantee download.",
    mono: "per-grantee wrap"
  },
  {
    title: "Folder archives",
    desc: "Whole directory trees zipped then sealed as one container, with traversal and zip-bomb guards on restore.",
    mono: "zip + AES-GCM"
  }
] as const;

function ThemeToggle() {
  const { theme, toggle } = useTheme();
  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
      aria-pressed={theme === "light"}
      className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:border-slate-400 hover:text-slate-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500 dark:border-slate-800 dark:text-slate-300 dark:hover:border-slate-700 dark:hover:text-white"
    >
      <span aria-hidden="true">{theme === "dark" ? "◐" : "◑"}</span>
      {theme === "dark" ? "Light" : "Dark"}
    </button>
  );
}

export default function Landing() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-blue-600 focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-white"
      >
        Skip to content
      </a>

      {/* ── Nav ─────────────────────────────────────────── */}
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-slate-50/90 backdrop-blur dark:border-slate-800/80 dark:bg-slate-950/90">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link to="/" className="flex items-center gap-2.5" aria-label="SecureVault home">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600 text-white">
              <IconShield />
            </span>
            <span className="text-base font-bold tracking-tight">SecureVault</span>
          </Link>
          <nav
            className="hidden items-center gap-7 text-sm font-medium text-slate-600 dark:text-slate-400 md:flex"
            aria-label="Page sections"
          >
            <a href="#model" className="transition-colors hover:text-blue-600 dark:hover:text-blue-400">The seal</a>
            <a href="#features" className="transition-colors hover:text-blue-600 dark:hover:text-blue-400">Features</a>
            <a href="#start" className="transition-colors hover:text-blue-600 dark:hover:text-blue-400">How it starts</a>
          </nav>
          <div className="flex items-center gap-2.5">
            <ThemeToggle />
            {isAuthenticated ? (
              <Link
                to="/dashboard"
                className="inline-flex items-center justify-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500"
              >
                Open dashboard
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="hidden px-2 text-sm font-semibold text-slate-600 transition-colors hover:text-blue-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500 dark:text-slate-300 dark:hover:text-blue-400 sm:inline"
                >
                  Sign in
                </Link>
                <Link
                  to="/register"
                  className="inline-flex items-center justify-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500"
                >
                  Get started
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      <main id="main">
        {/* ── Hero ──────────────────────────────────────── */}
        <section className="relative overflow-hidden" aria-labelledby="hero-title">
          {/* faint engineering grid, not a gradient blob */}
          <div
            aria-hidden="true"
            className="cyber-bg absolute inset-0 opacity-60 dark:opacity-40"
          />
          <div className="relative mx-auto grid max-w-6xl gap-12 px-6 pb-20 pt-14 lg:grid-cols-[1.05fr_0.95fr] lg:items-center lg:pb-28 lg:pt-20">
            <div className="animate-fade-up">
              <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-blue-600 dark:text-blue-400">
                Server-side sealed vault
              </p>
              <h1
                id="hero-title"
                className="mt-5 text-4xl font-extrabold leading-[1.06] tracking-tight sm:text-5xl"
              >
                Steal the disk,
                <br />
                get nothing but noise.
              </h1>
              <p className="mt-5 max-w-xl text-lg leading-relaxed text-slate-600 dark:text-slate-400">
                SecureVault encrypts every file, folder and text snippet with{" "}
                <span className="font-mono text-[0.95em] font-semibold text-slate-800 dark:text-slate-200">
                  AES-256-GCM
                </span>{" "}
                under per-file keys wrapped by your{" "}
                <span className="font-mono text-[0.95em] font-semibold text-slate-800 dark:text-slate-200">
                  RSA-4096
                </span>{" "}
                parent key. What rests on the volume is ciphertext — verifiable,
                auditable, revocable.
              </p>
              <div className="mt-8 flex flex-wrap items-center gap-3">
                <Link
                  to={isAuthenticated ? "/dashboard" : "/register"}
                  className="inline-flex items-center justify-center rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500"
                >
                  {isAuthenticated ? "Open your vault" : "Create a free vault"}
                </Link>
                <Link
                  to="/login"
                  className="inline-flex items-center justify-center rounded-lg border border-slate-300 px-6 py-3 text-sm font-semibold text-slate-700 transition-colors hover:border-slate-400 hover:text-slate-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500 dark:border-slate-700 dark:text-slate-200 dark:hover:border-slate-600 dark:hover:text-white"
                >
                  Sign in
                </Link>
              </div>
              <dl className="mt-10 grid max-w-lg grid-cols-3 gap-6 border-t border-slate-200 pt-6 dark:border-slate-800">
                {[
                  ["AES-256", "authenticated cipher"],
                  ["4096-bit", "RSA parent keys"],
                  ["0 bytes", "plaintext at rest"]
                ].map(([k, v]) => (
                  <div key={k}>
                    <dt className="font-mono text-lg font-bold text-slate-900 dark:text-white">
                      {k}
                    </dt>
                    <dd className="mt-0.5 text-xs text-slate-500 dark:text-slate-500">{v}</dd>
                  </div>
                ))}
              </dl>
            </div>

            {/* Seal/open terminal — the hero animation */}
            <div className="animate-fade-up [animation-delay:150ms]">
              <div
                className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900 text-slate-300 shadow-modal dark:border-slate-700 dark:shadow-none"
                role="img"
                aria-label="Animation showing a filename dissolving into ciphertext and resolving back to plaintext"
              >
                <div className="flex items-center gap-2 border-b border-slate-800 px-4 py-3">
                  <span className="h-2.5 w-2.5 rounded-full bg-slate-700" aria-hidden="true" />
                  <span className="h-2.5 w-2.5 rounded-full bg-slate-700" aria-hidden="true" />
                  <span className="h-2.5 w-2.5 rounded-full bg-blue-500" aria-hidden="true" />
                  <span className="ml-2 font-mono text-xs text-slate-500">
                    seal ⇄ open — live
                  </span>
                </div>
                <div className="space-y-4 p-5">
                  <ScrambleText text="quarterly-report.pdf → 9f3a…c41d.sealed" />
                  <div className="border-t border-slate-800 pt-4 font-mono text-xs leading-6 text-slate-500">
                    <p><span className="text-slate-600 dark:text-slate-500">$</span> vault seal quarterly-report.pdf</p>
                    <p>├─ session key <span className="text-blue-400">aes-256-gcm · nonce 96-bit</span></p>
                    <p>├─ wrap <span className="text-blue-400">rsa-4096-oaep · kid 7f:2a…</span></p>
                    <p>└─ stored <span className="text-emerald-400">ciphertext only ✓ tag verified</span></p>
                  </div>
                </div>
              </div>
              <p className="mt-3 font-mono text-[11px] leading-relaxed text-slate-500 dark:text-slate-600">
                Illustrative transcript. Real nonces, keys and tags are random per operation.
              </p>
            </div>
          </div>
        </section>

        {/* ── Crypto model ──────────────────────────────── */}
        <section
          id="model"
          aria-labelledby="model-title"
          className="border-t border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900/40"
        >
          <div className="mx-auto max-w-6xl px-6 py-20 lg:py-24">
            <Reveal>
              <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-blue-600 dark:text-blue-400">
                01 — The seal, honestly
              </p>
              <h2 id="model-title" className="mt-3 max-w-2xl text-3xl font-extrabold tracking-tight sm:text-4xl">
                No &ldquo;bank-level security&rdquo;. Just the construction.
              </h2>
              <p className="mt-4 max-w-2xl leading-relaxed text-slate-600 dark:text-slate-400">
                Four operations stand between your upload and the disk. Each one
                is inspectable in{" "}
                <span className="font-mono text-[0.9em]">backend/app/crypto/</span> —
                and each one fails closed.
              </p>
            </Reveal>

            <ol className="mt-12 grid gap-4 md:grid-cols-2">
              {SEAL_STEPS.map((s, i) => (
                <Reveal as="li" key={s.n} delay={Math.min(i, 3) * 70}>
                  <div className="h-full rounded-xl border border-slate-200 bg-slate-50 p-6 dark:border-slate-800 dark:bg-slate-950">
                    <div className="flex items-baseline justify-between">
                      <span className="font-mono text-sm font-bold text-blue-600 dark:text-blue-400">
                        {s.n}
                      </span>
                      <span className="font-mono text-[11px] uppercase tracking-[0.2em] text-slate-400 dark:text-slate-600">
                        {s.op}
                      </span>
                    </div>
                    <h3 className="mt-2 font-semibold">{s.title}</h3>
                    <p className="mt-1.5 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
                      {s.desc}
                    </p>
                  </div>
                </Reveal>
              ))}
            </ol>

            <Reveal className="mt-8">
              <div className="grid gap-4 lg:grid-cols-[1fr_1fr] lg:items-stretch">
                <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900 p-5">
                  <p className="mb-3 font-mono text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                    Container layout — *.svlt
                  </p>
                  <pre className="overflow-x-auto font-mono text-xs leading-7 text-slate-400">{`magic "SVLT" · version u16
header: key_id · algorithm · nonce
ciphertext: AES-256-GCM (...)
tag: 128-bit auth tag
wrapped_key: RSA-4096-OAEP blob`}</pre>
                </div>
                <div className="rounded-xl border border-amber-500/30 bg-amber-500/[0.07] p-5 text-sm leading-relaxed">
                  <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-amber-600 dark:text-amber-400">
                    Honest scope
                  </p>
                  <p className="mt-2 text-slate-700 dark:text-slate-300">
                    SecureVault is <strong>server-side custody, not
                    zero-knowledge</strong>: the server generates your RSA
                    parent keys, holds the private halves wrapped at rest, and
                    sees plaintext in memory while sealing and opening. An
                    operator with the database <em>and</em> the secret material
                    can decrypt. What this buys you: a stolen volume, a
                    discarded disk, or a backup leak reveals nothing.
                  </p>
                </div>
              </div>
            </Reveal>

            <Reveal>
              <ul className="mt-8 flex flex-wrap gap-2" aria-label="Algorithms in use">
                {SPEC.map(([term, def]) => (
                  <li
                    key={term}
                    title={def}
                    className="inline-flex items-center gap-2 rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1.5 font-mono text-xs text-slate-600 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-400"
                  >
                    <span className="font-semibold text-slate-800 dark:text-slate-200">{term}</span>
                    <span className="hidden sm:inline">{def}</span>
                  </li>
                ))}
              </ul>
            </Reveal>
          </div>
        </section>

        {/* ── Features ──────────────────────────────────── */}
        <section id="features" aria-labelledby="features-title" className="border-t border-slate-200 dark:border-slate-800">
          <div className="mx-auto max-w-6xl px-6 py-20 lg:py-24">
            <Reveal>
              <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-blue-600 dark:text-blue-400">
                02 — Control plane
              </p>
              <h2 id="features-title" className="mt-3 text-3xl font-extrabold tracking-tight sm:text-4xl">
                Encryption is the floor. Control is the product.
              </h2>
            </Reveal>
            <ul className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {FEATURES.map((f, i) => (
                <Reveal as="li" key={f.title} delay={(i % 3) * 70}>
                  <div className="h-full rounded-xl border border-slate-200 bg-white p-6 transition-colors hover:border-blue-500/50 dark:border-slate-800 dark:bg-slate-900/40 dark:hover:border-blue-500/40">
                    <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-slate-400 dark:text-slate-600">
                      {f.mono}
                    </p>
                    <h3 className="mt-2 font-semibold">{f.title}</h3>
                    <p className="mt-1.5 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
                      {f.desc}
                    </p>
                  </div>
                </Reveal>
              ))}
            </ul>
          </div>
        </section>

        {/* ── How it starts ─────────────────────────────── */}
        <section
          id="start"
          aria-labelledby="start-title"
          className="border-t border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900/40"
        >
          <div className="mx-auto max-w-6xl px-6 py-20 lg:py-24">
            <Reveal>
              <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-blue-600 dark:text-blue-400">
                03 — How it starts
              </p>
              <h2 id="start-title" className="mt-3 text-3xl font-extrabold tracking-tight sm:text-4xl">
                Three steps to a sealed vault
              </h2>
            </Reveal>
            <ol className="mt-12 grid gap-4 md:grid-cols-3">
              {[
                ["01", "Create your account", "Sign up with a 12+ character passphrase. Argon2id hashes it; breach-listed passwords are refused with guidance, not a raw error."],
                ["02", "Get your RSA-4096 parent key", "Provision a parent key pair in Key Manager. Rotate on schedule, revoke on suspicion, expiry enforced."],
                ["03", "Seal, share, audit", "Encrypt files, folders or text. Share via per-grantee wraps, watch every event land in the hash-chained log."]
              ].map(([n, title, desc], i) => (
                <Reveal as="li" key={n} delay={i * 70}>
                  <div className="relative h-full overflow-hidden rounded-xl border border-slate-200 bg-slate-50 p-6 dark:border-slate-800 dark:bg-slate-950">
                    <span aria-hidden="true" className="absolute -right-1 -top-4 select-none text-6xl font-extrabold tracking-tight text-slate-900/[0.06] dark:text-white/[0.06]">
                      {n}
                    </span>
                    <span className="relative font-mono text-sm font-bold tracking-widest text-blue-600 dark:text-blue-400">
                      {n}
                    </span>
                    <h3 className="relative mt-2 font-semibold">{title}</h3>
                    <p className="relative mt-1.5 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
                      {desc}
                    </p>
                  </div>
                </Reveal>
              ))}
            </ol>
          </div>
        </section>

        {/* ── CTA ───────────────────────────────────────── */}
        <section aria-labelledby="cta-title" className="border-t border-slate-200 dark:border-slate-800">
          <div className="mx-auto max-w-6xl px-6 py-20 text-center lg:py-24">
            <Reveal>
              <p className="font-mono text-xs text-slate-500 dark:text-slate-500">
                $ vault init --user you
              </p>
              <h2 id="cta-title" className="mx-auto mt-4 max-w-xl text-3xl font-extrabold tracking-tight sm:text-4xl">
                Your first sealed file is a minute away.
              </h2>
              <p className="mx-auto mt-4 max-w-lg text-slate-600 dark:text-slate-400">
                Register, provision a key, upload — every step verified, every
                event logged.
              </p>
              <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
                <Link
                  to={isAuthenticated ? "/dashboard" : "/register"}
                  className="inline-flex items-center justify-center rounded-lg bg-blue-600 px-8 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500"
                >
                  {isAuthenticated ? "Open dashboard" : "Create a free vault"}
                </Link>
                {!isAuthenticated && (
                  <Link
                    to="/login"
                    className="inline-flex items-center justify-center rounded-lg border border-slate-300 px-8 py-3 text-sm font-semibold text-slate-700 transition-colors hover:border-slate-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500 dark:border-slate-700 dark:text-slate-200 dark:hover:border-slate-600"
                  >
                    Sign in
                  </Link>
                )}
              </div>
            </Reveal>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-200 dark:border-slate-800">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 py-8 sm:flex-row">
          <div className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white">
              <IconShield />
            </span>
            <span className="text-sm font-bold tracking-tight">SecureVault</span>
          </div>
          <p className="font-mono text-[11px] text-slate-500 dark:text-slate-600">
            AES-256-GCM · RSA-4096 · Argon2id · hash-chained audit
          </p>
          <div className="flex items-center gap-4 text-sm text-slate-600 dark:text-slate-400">
            <Link to="/login" className="transition-colors hover:text-blue-600 dark:hover:text-blue-400">Sign in</Link>
            <Link to="/register" className="transition-colors hover:text-blue-600 dark:hover:text-blue-400">Register</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
