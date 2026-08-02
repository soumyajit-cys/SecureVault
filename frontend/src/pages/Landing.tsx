import { Link } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";

const shieldIcon = (
  <svg
    className="h-5 w-5"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.8"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M12 3l9 5v6c0 4-3.5 6.5-9 8-5.5-1.5-9-4-9-8V8l9-5z" />
  </svg>
);

const features = [
  {
    title: "AES-256-GCM encryption",
    desc: "Military-grade authenticated encryption with unique per-message nonces.",
    icon: (
      <path d="M12 3l9 5-9 5-9-5 9-5zM3 13l9 5 9-5M3 17l9 5 9-5" />
    )
  },
  {
    title: "Key lifecycle management",
    desc: "Generate, rotate and revoke keys with automatic expiry and rotation policies.",
    icon: (
      <path d="M21 2l-5 5m-2 2l-3-3-6 6a4 4 0 0 0 6 6l6-6-3-3m-3 0l3 3" />
    )
  },
  {
    title: "Immutable audit trail",
    desc: "Every security-relevant action is logged and queryable in real time.",
    icon: (
      <path d="M4 19V9m5 10V5m5 14v-7m5 7V3" />
    )
  },
  {
    title: "Client-side sealing",
    desc: "Plaintext is never written to the vault — only ciphertext and integrity tags are.",
    icon: (
      <path d="M12 3v3m0 0a6 6 0 0 1 6 6v6a6 6 0 0 1-6 6 6 6 0 0 1-6-6v-6a6 6 0 0 1 6-6zm0 0a6 6 0 0 1 6 6m-6 6a6 6 0 0 1 6 6m-6-6 3 4" />
    )
  },
  {
    title: "Folder archives",
    desc: "Encrypt a whole directory as a single AES-256-GCM archive and restore it later.",
    icon: (
      <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z" />
    )
  },
  {
    title: "Role-based access",
    desc: "Fine-grained controls for Users, Auditors and Admins, enforced server-side.",
    icon: (
      <path d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm-8 10a8 8 0 0 1 16 0" />
    )
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
    desc: "Provision a key pair and share it across your encrypt and decrypt workflows."
  },
  {
    n: "03",
    title: "Encrypt, store and track",
    desc: "Seal files, folders or plain text, download them only to you, and review audit logs."
  }
];

export default function Landing() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  return (
    <div className="min-h-screen bg-white">
      {/* Nav */}
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link to="/" className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 text-white shadow-sm">
              <svg
                className="h-5 w-5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M12 3l9 5-9 5-9-5 9-5zM3 13l9 5 9-5M3 17l9 5 9-5" />
              </svg>
            </span>
            <span className="text-lg font-bold tracking-tight text-slate-900">
              SecureVault
            </span>
          </Link>

          <nav className="hidden items-center gap-8 text-sm font-medium text-slate-600 md:flex">
            <a href="#features" className="transition-colors hover:text-slate-900">
              Features
            </a>
            <a href="#how" className="transition-colors hover:text-slate-900">
              How it works
            </a>
            <a href="#security" className="transition-colors hover:text-slate-900">
              Security
            </a>
          </nav>

          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <Link
                to="/dashboard"
                className="inline-flex items-center justify-center rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-brand-700"
              >
                Open dashboard
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-sm font-semibold text-slate-700 transition-colors hover:text-slate-900"
                >
                  Sign in
                </Link>
                <Link
                  to="/register"
                  className="inline-flex items-center justify-center rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-brand-700"
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
        <div className="pointer-events-none absolute -top-32 left-1/2 h-[480px] w-[800px] -translate-x-1/2 rounded-full bg-brand-100/60 blur-3xl" />
        <div className="relative mx-auto max-w-6xl px-6 pb-20 pt-20 text-center lg:pt-28">
          <span className="inline-flex items-center gap-2 rounded-full border border-brand-200 bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700">
            {shieldIcon}
            Enterprise-grade encryption
          </span>
          <h1 className="mx-auto mt-6 max-w-3xl text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
            Encrypt files, folders and text —{" "}
            <span className="text-brand-600">by design, at rest.</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-slate-600">
            SecureVault seals your sensitive data with authenticated AES-256-GCM
            encryption, manages your keys, and keeps a complete audit trail — from
            first upload to permanent deletion.
          </p>
          <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              to={isAuthenticated ? "/dashboard" : "/register"}
              className="inline-flex w-full items-center justify-center rounded-lg bg-brand-600 px-6 py-3 text-base font-semibold text-white shadow-sm transition-colors hover:bg-brand-700 sm:w-auto"
            >
              {isAuthenticated ? "Open your vault" : "Start encrypting free"}
            </Link>
            <Link
              to={isAuthenticated ? "/file-manager" : "/login"}
              className="inline-flex w-full items-center justify-center rounded-lg border border-slate-300 bg-white px-6 py-3 text-base font-semibold text-slate-700 transition-colors hover:bg-slate-50 sm:w-auto"
            >
              Sign in
            </Link>
          </div>

          {/* Trust row */}
          <dl className="mx-auto mt-16 grid max-w-2xl grid-cols-3 gap-6">
            {[
              ["AES-256", "authenticated encryption"],
              ["Argon2id", "password hashing"],
              ["Zero-copy", "sealed plaintext paths"]
            ].map(([k, v]) => (
              <div key={k} className="text-center">
                <dt className="text-xl font-bold text-slate-900">{k}</dt>
                <dd className="mt-1 text-xs text-slate-500">{v}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="border-t border-slate-200 bg-slate-50">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-sm font-semibold uppercase tracking-wider text-brand-600">
              Features
            </p>
            <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
              Everything you need to secure your data
            </h2>
            <p className="mt-4 text-lg text-slate-600">
              A focused toolkit that makes strong crypto practical and auditable.
            </p>
          </div>

          <div className="mt-14 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((f) => (
              <div
                key={f.title}
                className="rounded-xl border border-slate-200 bg-white p-6 shadow-card"
              >
                <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
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
                <h3 className="mt-4 text-base font-semibold text-slate-900">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="border-t border-slate-200">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-sm font-semibold uppercase tracking-wider text-brand-600">
              How it works
            </p>
            <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
              Three steps to a sealed vault
            </h2>
          </div>

          <div className="mt-14 grid grid-cols-1 gap-6 md:grid-cols-3">
            {steps.map((s) => (
              <div
                key={s.n}
                className="relative rounded-xl border border-slate-200 bg-white p-6 shadow-card"
              >
                <span className="text-3xl font-extrabold tracking-tight text-brand-100">
                  {s.n}
                </span>
                <h3 className="mt-3 text-base font-semibold text-slate-900">{s.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Security */}
      <section id="security" className="border-t border-slate-200 bg-slate-900">
        <div className="mx-auto grid max-w-6xl gap-12 px-6 py-20 lg:grid-cols-2 lg:items-center">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wider text-brand-300">
              Security
            </p>
            <h2 className="mt-3 text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Garbage in never stored. Plaintext never rests.
            </h2>
            <ul className="mt-8 space-y-4">
              {[
                "AES-256-GCM with SHA-256 integrity verification on every container",
                "Hybrid RSA + session-key key wrapping for each sealed payload",
                "Rotation, revocation and expiry enforced at the key level",
                "Lockout thresholds and slow Argon2id hashing against brute force"
              ].map((item) => (
                <li key={item} className="flex items-start gap-3 text-sm text-brand-100">
                  <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-white/10 text-white">
                    ✓
                  </span>
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-xl border border-slate-700 bg-slate-800/60 p-6 font-mono text-xs leading-7">
            <p className="mb-4 font-sans text-sm font-semibold text-slate-300">
              Vault layout
            </p>
            <pre className="text-slate-400">{`storage/
├── containers/   # sealed .svlt
│   └── *.svlt    AES-256-GCM ciphertext only
├── temp/         # staging, purged by GC
└── keys/         # wrapped private material`}</pre>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-slate-200 bg-white">
        <div className="mx-auto max-w-4xl px-6 py-20 text-center">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Ready to lock down your data?
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-lg text-slate-600">
            Create your vault in under a minute and start encrypting text, files
            and folders — with full key control and audit logs.
          </p>
          <Link
            to={isAuthenticated ? "/dashboard" : "/register"}
            className="mt-8 inline-flex items-center justify-center rounded-lg bg-brand-600 px-8 py-3 text-base font-semibold text-white shadow-sm transition-colors hover:bg-brand-700"
          >
            {isAuthenticated ? "Open dashboard" : "Create a free vault"}
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-slate-50">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 py-8 sm:flex-row">
          <div className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">
              {shieldIcon}
            </span>
            <span className="text-sm font-bold tracking-tight text-slate-900">
              SecureVault
            </span>
          </div>
          <p className="text-xs text-slate-500">
            Zero plaintext storage · AES-256-GCM · Full audit trail
          </p>
          <div className="flex items-center gap-4 text-sm text-slate-500">
            <Link to="/login" className="transition-colors hover:text-slate-900">
              Sign in
            </Link>
            <Link to="/register" className="transition-colors hover:text-slate-900">
              Register
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}