import { useAuthStore } from "@/store/authStore";
import { NavLink } from "react-router-dom";

const icon = (path: string) => (
  <svg
    className="h-5 w-5"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.8"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <path d={path} />
  </svg>
);

const links = [
  {
    to: "/dashboard",
    label: "Dashboard",
    icon: icon("M3 12l9-9 9 9M5 10v10a1 1 0 0 0 1 1h3v-6h6v6h3a1 1 0 0 0 1-1V10")
  },
  {
    to: "/file-manager",
    label: "File Manager",
    icon: icon(
      "M12 3l9 5-9 5-9-5 9-5zM3 13l9 5 9-5M3 17l9 5 9-5"
    )
  },
  {
    to: "/folder-encryption",
    label: "Folder Tools",
    icon: icon(
      "M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z"
    )
  },
  {
    to: "/encrypt-text",
    label: "Encrypt Text",
    icon: icon(
      "M12 3v3m0 0a6 6 0 0 1 6 6v6a6 6 0 0 1-6 6 6 6 0 0 1-6-6v-6a6 6 0 0 1 6-6zm0 0a6 6 0 0 1 6 6m-6 6a6 6 0 0 1 6 6m-6-6 3 4"
    )
  },
  {
    to: "/decrypt-text",
    label: "Decrypt Text",
    icon: icon(
      "M12 21a5 5 0 0 0 5-5v-2M7 21a7 7 0 0 0 7-7V8a5 5 0 0 0-10 0v8a9 9 0 0 0 9 10z"
    )
  },
  {
    to: "/keys",
    label: "Key Manager",
    icon: icon(
      "M21 2l-5 5m-2 2l-3-3-6 6a4 4 0 0 0 6 6l6-6-3-3m-3 0l3 3"
    )
  },
  {
    to: "/audit",
    label: "Audit Logs",
    icon: icon(
      "M4 19V9m5 10V5m5 14v-7m5 7V3"
    )
  }
];

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `group relative flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors duration-150 ${
    isActive
      ? "bg-brand-50 text-brand-700"
      : "text-ink-soft hover:bg-surface-muted hover:text-ink"
  }`;

export default function Sidebar() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  return (
    <aside className="flex h-full w-64 shrink-0 flex-col border-r border-cyber-line bg-surface-elevated">
      <div className="flex items-center gap-3 px-5 pb-4 pt-5">
        <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-gradient text-white">
          <IconShield />
        </span>
        <div>
          <p className="text-sm font-bold tracking-tight text-ink">SecureVault</p>
          <p className="text-xs text-ink-faint">Enterprise Vault</p>
        </div>
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-2">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={linkClass}
          >
            <span className="shrink-0">{link.icon}</span>
            {link.label}
          </NavLink>
        ))}
        <span className="my-3 block border-t border-cyber-line" />
        <NavLink
          to="/profile"
          className={linkClass}
        >
          {icon("M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm-8 10a8 8 0 0 1 16 0")}
          Profile
        </NavLink>
        <NavLink
          to="/settings"
          className={linkClass}
        >
          {icon(
            "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm7.5-3a7.5 7.5 0 0 1-.1 1.2l2 1.5-2 3.5-2.4-1a7.5 7.5 0 0 1-2 1.2L14.5 21h-5l-.5-2.6a7.5 7.5 0 0 1-2-1.2l-2.4 1-2-3.5 2-1.5a7.5 7.5 0 0 1 0-2.4l-2-1.5 2-3.5 2.4 1a7.5 7.5 0 0 1 2-1.2L9.5 3h5l.5 2.6a7.5 7.5 0 0 1 2 1.2l2.4-1 2 3.5-2 1.5c.07.4.1.8.1 1.2z"
          )}
          Settings
        </NavLink>

        {user?.roles?.some((r) => r.name.toLowerCase() === "admin") && (
          <NavLink
            to="/admin"
            className={linkClass}
          >
            {icon(
              "M12 3l9 5v6c0 4-3.5 6.5-9 8-5.5-1.5-9-4-9-8V8l9-5zm-3 9 2 2 4-4"
            )}
            Admin Panel
            <span className="absolute right-3 top-1/2 -translate-y-1/2 rounded bg-brand-100 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-brand-700">
              Admin
            </span>
          </NavLink>
        )}
      </nav>

      <div className="border-t border-cyber-line px-4 py-4">
        {user && (
          <div className="mb-3 flex items-center gap-2.5 px-1">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-gradient text-xs font-bold text-white">
              {user.username?.slice(0, 2).toUpperCase()}
            </span>
            <div className="truncate">
              <p className="truncate text-sm font-semibold text-ink">
                {user.username}
              </p>
              <p className="truncate text-xs text-ink-faint">{user.email}</p>
            </div>
          </div>
        )}
        <button
          onClick={() => logout()}
          className="flex w-full items-center justify-center gap-2 rounded-lg border border-cyber-line bg-surface-elevated px-3 py-2 text-sm font-medium text-ink-soft transition-colors duration-150 hover:border-red-200 hover:bg-red-50 hover:text-red-600"
        >
          {icon("M15 12H3m0 0 4-4m-4 4 4 4M12 20h7a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2h-7")}
          Sign out
        </button>
      </div>
    </aside>
  );
}

function IconShield() {
  return (
    <svg
      className="h-5 w-5"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5l-8-3z" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  );
}

export { IconShield };
