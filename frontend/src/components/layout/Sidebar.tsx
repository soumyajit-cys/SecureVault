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

export default function Sidebar() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  return (
    <aside className="flex h-full w-64 shrink-0 flex-col border-r border-slate-200 bg-white">
      <div className="flex items-center gap-3 px-5 py-5">
        <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 text-white shadow-sm">
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
            <path d="M12 3l9 5-9 5-9-5 9-5z" />
            <path d="M3 13l9 5 9-5" />
          </svg>
        </span>
        <div>
          <p className="text-sm font-bold tracking-tight text-slate-900">
            SecureVault
          </p>
          <p className="text-[10px] font-medium uppercase tracking-widest text-slate-400">
            Crypto Vault
          </p>
        </div>
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-2">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-brand-50 text-brand-700"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
              }`
            }
          >
            <span className={link.to === "/dashboard" ? "text-slate-400" : ""}>
              {link.icon}
            </span>
            {link.label}
          </NavLink>
        ))}
        <span className="my-3 block border-t border-slate-100" />
        <NavLink
          to="/profile"
          className={({ isActive }) =>
            `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              isActive
                ? "bg-brand-50 text-brand-700"
                : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
            }`
          }
        >
          {icon("M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm-8 10a8 8 0 0 1 16 0")}
          Profile
        </NavLink>
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              isActive
                ? "bg-brand-50 text-brand-700"
                : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
            }`
          }
        >
          {icon(
            "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm7.5-3a7.5 7.5 0 0 1-.1 1.2l2 1.5-2 3.5-2.4-1a7.5 7.5 0 0 1-2 1.2L14.5 21h-5l-.5-2.6a7.5 7.5 0 0 1-2-1.2l-2.4 1-2-3.5 2-1.5a7.5 7.5 0 0 1 0-2.4l-2-1.5 2-3.5 2.4 1a7.5 7.5 0 0 1 2-1.2L9.5 3h5l.5 2.6a7.5 7.5 0 0 1 2 1.2l2.4-1 2 3.5-2 1.5c.07.4.1.8.1 1.2z"
          )}
          Settings
        </NavLink>

        {user?.roles?.some((r) => r.name.toLowerCase() === "admin") && (
          <NavLink
            to="/admin"
            className={({ isActive }) =>
              `mt-1 flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-brand-50 text-brand-700"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
              }`
            }
          >
            {icon(
              "M12 3l9 5v6c0 4-3.5 6.5-9 8-5.5-1.5-9-4-9-8V8l9-5zm-3 9 2 2 4-4"
            )}
            Admin Panel
          </NavLink>
        )}
      </nav>

      <div className="border-t border-slate-200 px-4 py-4">
        {user && (
          <div className="mb-2 flex items-center gap-2 px-1">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-100 text-xs font-bold text-brand-700">
              {user.username?.slice(0, 2).toUpperCase()}
            </span>
            <div className="truncate">
              <p className="truncate text-sm font-medium text-slate-800">
                {user.username}
              </p>
              <p className="truncate text-xs text-slate-400">{user.email}</p>
            </div>
          </div>
        )}
        <button
          onClick={() => logout()}
          className="flex w-full items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-900"
        >
          {icon("M15 12H3m0 0 4-4m-4 4 4 4M12 20h7a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2h-7")}
          Sign out
        </button>
      </div>
    </aside>
  );
}