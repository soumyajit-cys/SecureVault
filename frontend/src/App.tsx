import { useEffect, useMemo } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";

import AppShell from "@/components/layout/AppShell";
import ProtectedRoute from "@/components/guard/ProtectedRoute";
import RequireRole from "@/components/guard/RequireRole";

import Login from "@/pages/Login";
import Register from "@/pages/Register";
import Dashboard from "@/pages/Dashboard";
import EncryptText from "@/pages/EncryptText";
import DecryptText from "@/pages/DecryptText";
import FileManager from "@/pages/FileManager";
import FolderEncryption from "@/pages/FolderEncryption";
import KeyManager from "@/pages/KeyManager";
import AuditLogs from "@/pages/AuditLogs";
import AdminPanel from "@/pages/AdminPanel";
import Profile from "@/pages/Profile";
import Settings from "@/pages/Settings";

import { queryClient } from "@/lib/query";
import { useAuthStore } from "@/store/authStore";

export default function App() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const logout = useAuthStore((s) => s.logout);

  useEffect(() => {
    const handle = () => logout();
    window.addEventListener("auth:logout", handle);
    return () => window.removeEventListener("auth:logout", handle);
  }, [logout]);

  const protectedContent = useMemo(
    () => (
      <ProtectedRoute>
        <AppShell>
          <Routes>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/encrypt-text" element={<EncryptText />} />
            <Route path="/decrypt-text" element={<DecryptText />} />
            <Route path="/file-manager" element={<FileManager />} />
            <Route path="/folder-encryption" element={<FolderEncryption />} />
            <Route path="/keys" element={<KeyManager />} />
            <Route path="/audit" element={<AuditLogs />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/settings" element={<Settings />} />
            <Route
              path="/admin"
              element={
                <RequireRole role="Admin">
                  <AdminPanel />
                </RequireRole>
              }
            />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </App>
      </ProtectedRoute>
    ),
    []
  );

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/*"
            element={isAuthenticated ? protectedContent : <Navigate to="/login" replace />}
          />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}