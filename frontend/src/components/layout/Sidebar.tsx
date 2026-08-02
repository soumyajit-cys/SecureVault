import { useAuthStore } from "@/store/authStore";
import Button from "@/components/ui/Button";
import { NavLink } from "react-router-dom";

const links = [
  { to: "/dashboard", label: "Dashboard", icon: "◧" },
  { to: "/encrypt-text", label: "Encrypt Text", icon: "⚿" },
  { to: "/decrypt-text", label: "Decrypt Text", icon: "⚷" },
  { to: "/file-manager", label: "File Manager", icon: "🗀" },
  { to: "/folder-encryption", label: "Folder Tools", icon: "🗁" },
  { to: "/keys", label: "Key Manager", icon: "🔑" },
  { to: "/audit", label: "Audit Logs", icon: "◪" }
];

export default function Sidebar() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  return (
    <aside className="flex h-full w-64 flex-col border-r border-vault-800 bg-vault-900/60">
      <div className="flex items-center gap-2 border-b border-vault-800 px-5 py-5">
        <span className="flex h-9 w-9 items-center justify-center rounded bg-neon-cyan text-lg font-bold text-vault-950">
          ▣
        </span>
        <div>
          <p className="text-sm font-bold tracking-wide text-white">SECUREVAULT</p>
          <p className="text-[10px] uppercase tracking-widest text-slate-500">
            Crypto Vault
          </p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded px-3 py-2 text-sm transition-colors ${
                isActive
                  ? "bg-neon-cyan/15 text-neon-cyan"
                  : "text-slate-400 hover:bg-vault-800 hover:text-slate-200"
              }`
            }
          >
            <span className="text-base">{link.icon}</span>
            {link.label}
          </NavLink>
        ))}

        {user?.roles?.some((r) => r.name === "admin") && (
          <NavLink
            to="/admin"
            className={({ isActive }) =>
              `mt-4 flex items-center gap-3 rounded border border-neon-purple/40 px-3 py-2 text-sm transition-colors ${
                isActive
                  ? "bg-neon-purple/15 text-neon-purple"
                  : "text-slate-400 hover:bg-vault-800 hover:text-neon-purple"
              }`
            }
          >
            <span className="text-base">⚒</span>
            Admin Panel
          </NavLink>
        )}
      </nav>

      <div className="border-t border-vault-800 px-5 py-4">
        {user && (
          <p className="mb-2 truncate text-xs text-slate-400">
            Signed in as <span className="text-slate-200">{user.username}</span>
          </p>
        )}
        <Button
          variant="outline"
          className="w-full"
          onClick={() => {
            logout();
          }}
        >
          Sign out
        </Button>
      </div>
    </aside>
  );
}