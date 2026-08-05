import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import Button from "@/components/ui/Button";
import { TextField } from "@/components/ui/Field";
import { auth, profile } from "@/lib/endpoints";
import { extractDetail } from "@/lib/api";
import { IconShield } from "@/components/layout/Sidebar";

const shieldIcon = (
  <path d="M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5l-8-3z" />
);
const shieldCheck = (
  <path d="M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5l-8-3zm-3 9 2 2 4-4" />
);

const features = [
  {
    title: "AES-256-GCM encryption",
    desc: "Military-grade authenticated encryption with unique per-message nonces.",
    icon: <path d="M12 3l9 5-9 5-9-5 9-5zM3 13l9 5 9-5M3 17l9 5 9-5" />
  },
  {
    title: "Key lifecycle management",
    desc: "Generate, rotate and revoke keys with automatic expiry and rotation policies.",
    icon: <path d="M21 2l-5 5m-2 2l-3-3-6 6a4 4 0 0 0 6 6l6-6-3-3m-3 0l3 3" />
  },
  {
    title: "Immutable audit trail",
    desc: "Every security-relevant action is logged, timestamped and queryable in real time.",
    icon: <path d="M4 19V9m5 10V5m5 14v-7m5 7V3" />
  },
  {
    title: "Zero plaintext at rest",
    desc: "Plaintext is never written to the vault — only ciphertext and integrity tags are.",
    icon: shieldIcon
  },
  {
    title: "Folder archives",
    desc: "Encrypt a whole directory as a single AES-256-GCM archive and restore it later.",
    icon: <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z" />
  },
  {
    title: "Role-based access",
    desc: "Fine-grained controls for Users, Auditors and Admins, enforced server-side.",
    icon: <path d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm-8 10a8 8 0 0 1 16 0" />
  }
];

const steps = [
  {
    n: "01",
    title: "Create your vault account",
    desc: "Sign up with a strong password. Argon2 hashing protects your credentials."
  },
  {
    n: "02",
    title: "Generate an encryption key",
    desc: "Provision an RSA-4096 key pair and share it across your workflows."
  },
  {
    n: "03",
    title: "Encrypt, store and track",
    desc: "Seal files, folders or plain text, download them only to you, and review audit logs."
  }
];

export default function Landing() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const setTokens = useAuthStore((s) => s.setTokens);
  const setUser = useAuthStore((s) => s.setUser);
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await auth.login({ email, password });
      setTokens(res.access_token, res.refresh_token);
      try {
        const me = await profile.me();
        setUser(me);
      } catch {
        setUser(null);
      }
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(extractDetail(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-surface-soft">
      {/* Nav */}
      <header className="sticky top-0 z-40 border-b border-cyber-line bg-surface-elevated">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link to="/" className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-gradient text-white">
              <svg
                className="h-5 w-5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                {shieldIcon}
              </svg>
            </span>
            <span className="text-lg font-bold tracking-tight text-ink">
              SecureVault
            </span>
          </Link>

          <nav className="hidden items-center gap-8 text-sm font-medium text-ink-soft md:flex">
            <a href="#features" className="transition-colors hover:text-brand-600">
              Features
            </a>
            <a href="#how" className="transition-colors hover:text-brand-600">
              How it works
            </a>
            <a href="#security" className="transition-colors hover:text-brand-600">
              Security
            </a>
          </nav>

          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <Link
                to="/dashboard"
                className="inline-flex items-center justify-center rounded-lg bg-brand-gradient px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:brightness-110"
              >
                Open dashboard
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-sm font-semibold text-ink-soft transition-colors hover:text-brand-600"
                >
                  Sign in
                </Link>
                <Link
                  to="/register"
                  className="inline-flex items-center justify-center rounded-lg bg-brand-gradient px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:brightness-110"
                >
                  Get started
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="mx-auto grid max-w-6xl items-center gap-14 px-6 pb-24 pt-16 lg:grid-cols-2 lg:pb-28 lg:pt-24">
          {/* Left: marketing copy */}
          <div className="text-center lg:text-left">
            <span className="inline-flex animate-fade-up items-center gap-2 rounded-full border border-brand-200 bg-brand-50 px-3.5 py-1.5 text-xs font-semibold text-brand-700">
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                {shieldCheck}
              </svg>
              Enterprise-grade encryption
            </span>

            <h1 className="mt-8 animate-fade-up text-4xl font-extrabold tracking-tight text-ink [animation-delay:80ms] sm:text-5xl lg:text-6xl">
              Encrypt files, folders and text —{" "}
              <span className="bg-brand-gradient-warm bg-clip-text text-transparent">
                by design, at rest.
              </span>
            </h1>

            <p className="mx-auto mt-6 max-w-xl animate-fade-up text-lg leading-relaxed text-ink-soft [animation-delay:160ms] lg:mx-0">
              SecureVault seals your sensitive data with authenticated AES-256-GCM
              encryption, manages your RS256 keys, and keeps a complete audit trail — from
              first upload to permanent deletion.
            </p>

            <div className="mt-8 animate-fade-up [animation-delay:240ms]">
              {isAuthenticated ? (
                <Link
                  to="/dashboard"
                  className="inline-flex items-center justify-center rounded-lg bg-brand-gradient px-7 py-3 text-base font-semibold text-white shadow-sm transition-colors hover:brightness-110"
                >
                  Open your vault
                </Link>
              ) : (
                <Link
                  to="/register"
                  className="inline-flex items-center justify-center rounded-lg bg-brand-gradient px-7 py-3 text-base font-semibold text-white shadow-sm transition-colors hover:brightness-110"
                >
                  Start encrypting free
                </Link>
              )}
            </div>

            {/* Trust row */}
            <dl className="mx-auto mt-14 grid max-w-lg grid-cols-3 gap-6 lg:mx-0">
              {[
                ["AES-256", "authenticated encryption"],
                ["Argon2id", "password hashing"],
                ["Zero-copy", "sealed plaintext paths"]
              ].map(([k, v]) => (
                <div key={k} className="text-center lg:text-left">
                  <dt className="bg-brand-gradient-warm bg-clip-text text-xl font-extrabold text-transparent">
                    {k}
                  </dt>
                  <dd className="mt-1 text-xs text-ink-faint">{v}</dd>
                </div>
              ))}
            </dl>
          </div>

          {/* Right: embedded login */}
          {isAuthenticated ? (
            <div className="animate-fade-up mx-auto w-full max-w-md text-center lg:justify-self-end">
              <div className="rounded-2xl border border-cyber-line bg-surface-elevated p-8 shadow-card">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-gradient text-white">
                  <IconShield />
                </div>
                <h2 className="mt-5 text-xl font-extrabold tracking-tight text-ink">
                  You&apos;re already signed in
                </h2>
                <p className="mt-1.5 text-sm text-ink-faint">
                  Continue to your sealed workspace.
                </p>
                <Link
                  to="/dashboard"
                  className="mt-6 inline-flex w-full items-center justify-center rounded-lg bg-brand-gradient px-6 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:brightness-110"
                >
                  Open dashboard
                </Link>
              </div>
            </div>
          ) : (
            <div className="animate-fade-up mx-auto w-full max-w-sm [animation-delay:120ms] lg:justify-self-end">
              <div className="rounded-2xl border border-cyber-line bg-surface-elevated p-8 shadow-card">
                <div className="flex items-center gap-3">
                  <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-brand-gradient text-white">
                    <IconShield />
                  </span>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-ink-faint">
                      Access control
                    </p>
                    <h2 className="text-lg font-extrabold tracking-tight text-ink">
                      Sign in
                    </h2>
                    <p className="text-xs text-ink-faint">Welcome back to the vault</p>
                  </div>
                </div>

                <form onSubmit={handleLogin} className="mt-7 space-y-4">
                  <TextField
                    label="Email"
                    type="email"
                    required
                    autoComplete="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@company.com"
                  />
                  <TextField
                    label="Password"
                    type="password"
                    required
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                  />

                  {error && (
                    <div className="animate-fade-in rounded-lg border border-red-200 bg-red-50 px-3.5 py-2.5 text-sm text-red-700">
                      {error}
                    </div>
                  )}

                  <Button
                    type="submit"
                    className="w-full py-3"
                    loading={loading}
                  >
                    {loading ? "Signing in…" : "Sign in"}
                  </Button>
                </form>

                <p className="mt-5 text-center text-sm text-ink-faint">
                  No account?{" "}
                  <Link
                    to="/register"
                    className="font-semibold text-brand-600 transition-colors hover:text-brand-700"
                  >
                    Create one
                  </Link>
                </p>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Features */}
      <section id="features" className="border-t border-cyber-line bg-surface-elevated">
        <div className="mx-auto max-w-6xl px-6 py-24">
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-xs font-semibold uppercase tracking-wider text-ink-faint">
              Features
            </p>
            <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-ink sm:text-4xl">
              Everything you need to secure your data
            </h2>
            <p className="mt-4 text-lg text-ink-soft">
              A focused toolkit that makes strong crypto practical and auditable.
            </p>
          </div>

          <div className="mt-14 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((f) => (
              <div
                key={f.title}
                className="group rounded-xl border border-cyber-line bg-surface-elevated p-6 shadow-card transition-all duration-200 hover:border-brand-300 hover:shadow-card-hover"
              >
                <span className="flex h-10 w-10 items-center justify-center rounded-lg border border-brand-100 bg-brand-50 text-brand-600 transition-colors duration-200 group-hover:bg-brand-gradient group-hover:text-white">
                  <svg
                    className="h-5 w-5"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    {f.icon}
                  </svg>
                </span>
                <h3 className="mt-4 text-base font-semibold text-ink">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-ink-soft">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="border-t border-cyber-line bg-surface-soft">
        <div className="mx-auto max-w-6xl px-6 py-24">
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-xs font-semibold uppercase tracking-wider text-ink-faint">
              How it works
            </p>
            <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-ink sm:text-4xl">
              Three steps to a sealed vault
            </h2>
          </div>

          <div className="mt-14 grid grid-cols-1 gap-5 md:grid-cols-3">
            {steps.map((s) => (
              <div
                key={s.n}
                className="relative overflow-hidden rounded-xl border border-cyber-line bg-surface-elevated p-6 shadow-card"
              >
                <span className="absolute -right-2 -top-3 text-6xl font-extrabold tracking-tight text-ink/10">
                  {s.n}
                </span>
                <div className="relative">
                  <span className="font-mono text-sm font-bold tracking-widest text-brand-600">
                    {s.n}
                  </span>
                  <h3 className="mt-2 text-base font-semibold text-ink">{s.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-ink-soft">{s.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Security */}
      <section id="security" className="border-t border-cyber-line bg-surface-elevated">
        <div className="mx-auto grid max-w-6xl gap-14 px-6 py-24 lg:grid-cols-2 lg:items-center">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-ink-faint">
              Security
            </p>
            <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-ink sm:text-4xl">
              Garbage in never stored.{" "}
              <span className="bg-brand-gradient-warm bg-clip-text text-transparent">
                Plaintext never rests.
              </span>
            </h2>
            <ul className="mt-8 space-y-4">
              {[
                "AES-256-GCM with SHA-256 integrity verification on every container",
                "Rotating RS256 signing keys with kid-based verification",
                "Rotation, revocation and expiry enforced at the key level",
                "Lockout thresholds and slow Argon2id hashing against brute force"
              ].map((item) => (
                <li key={item} className="flex items-start gap-3 text-sm text-ink-soft">
                  <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-brand-100 bg-brand-50 text-brand-600">
                    <svg className="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M5 12l5 5L20 7" />
                    </svg>
                  </span>
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-card">
            <p className="mb-5 flex items-center gap-2 font-mono text-sm font-semibold text-slate-300">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
              </span>
              vault layout
            </p>
            <pre className="overflow-x-auto font-mono text-xs leading-7 text-slate-400">{`storage/
├── containers/   # sealed .svlt
│   └── *.svlt    AES-256-GCM ciphertext only
├── temp/         # staging, purged by GC
└── keys/         # wrapped private material`}</pre>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative overflow-hidden border-t border-cyber-line bg-brand-gradient">
        <div className="relative mx-auto max-w-4xl px-6 py-24 text-center">
          <h2 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            Ready to lock down your data?
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-lg text-white/80">
            Create your vault in under a minute and start encrypting text, files
            and folders — with full key control and audit logs.
          </p>
          <Link
            to={isAuthenticated ? "/dashboard" : "/register"}
            className="mt-8 inline-flex items-center justify-center rounded-lg bg-white px-8 py-3 text-base font-semibold text-brand-700 shadow-sm transition-all duration-200 hover:bg-brand-50 active:scale-[0.98]"
          >
            {isAuthenticated ? "Open dashboard" : "Create a free vault"}
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-cyber-line bg-surface-elevated">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 py-8 sm:flex-row">
          <div className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-gradient text-white">
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                {shieldIcon}
              </svg>
            </span>
            <span className="text-sm font-bold tracking-tight text-ink">
              SecureVault
            </span>
          </div>
          <p className="text-xs text-ink-faint">
            Zero plaintext storage · AES-256-GCM · Full audit trail
          </p>
          <div className="flex items-center gap-4 text-sm text-ink-soft">
            <Link to="/login" className="transition-colors hover:text-brand-600">
              Sign in
            </Link>
            <Link to="/register" className="transition-colors hover:text-brand-600">
              Register
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
