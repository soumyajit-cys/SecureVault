import { Navigate } from "react-router-dom";

import { useAuthStore } from "@/store/authStore";

export default function RequireRole({
  role,
  children
}: {
  role: string;
  children: React.ReactNode;
}) {
  const user = useAuthStore((s) => s.user);

  const hasRole = user?.roles?.some((r) => r.name === role);

  if (!hasRole) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}