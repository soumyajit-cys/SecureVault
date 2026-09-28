import { useEffect, useMemo, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";

import AppShell from "@/components/layout/AppShell";
import ProtectedRoute from "@/components/guard/ProtectedRoute";
import RequireRole from "@/components/guard/RequireRole";

import Login from "@/pages/Login";
import Register from "@/pages/Register";
import VerifyEmail from "@/pages/VerifyEmail";
import ResetPassword from "@/pages/ResetPassword";
import Landing from "@/pages/Landing";
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
  const sessionChecked = useAuthStore((s) => s.sessionChecked);
  const wakingUp = useAuthStore((s) => s.wakingUp);
  const logout = useAuthStore((s) => s.logout);
  const restoreSession = useAuthStore((s) => s.restoreSession);
  const [coldStart, setColdStart] = useState(false);

  useEffect(() => {
    const handle = () => logout();
    window.addEventListener("auth:logout", handle);
    return () => window.removeEventListener("auth:logout", handle);
  }, [logout]);

  useEffect(() => {
    const onWake = () => setColdStart(true);
    const onDone = () => setColdStart(false);
    window.addEventListener("api:cold-start", onWake);
    window.addEventListener("api:cold-start-done", onDone);
    return () => {
      window.removeEventListener("api:cold-start", onWake);
      window.removeEventListener("api:cold-start-done", onDone);
    };
  }, []);

  useEffect(() => {
    void restoreSession();
  }, [restoreSession]);

  const pending = !sessionChecked;

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
        </AppShell>
      </ProtectedRoute>
    ),
    []
  );

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {coldStart && (
          <div
            role="status"
            className="fixed inset-x-0 top-0 z-50 flex items-center justify-center gap-2 bg-brand-600 px-4 py-2 text-center text-xs font-medium text-white"
          >
            <span
              className="h-3 w-3 animate-spin rounded-full border-2 border-white/60 border-t-white"
              aria-hidden="true"
            />
            Waking up the server — Render&apos;s free tier sleeps when idle.
            This can take up to a minute; your request will retry automatically.
          </div>
        )}
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/verify-email" element={<VerifyEmail />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route
            path="/*"
            element={
              pending ? (
                <div className="flex min-h-screen items-center justify-center px-4">
                  <div className="text-center">
                    {wakingUp ? (
                      <>
                        <span
                          className="mx-auto mb-4 block h-8 w-8 animate-spin rounded-full border-2 border-brand-600/30 border-t-brand-600"
                          aria-hidden="true"
                        />
                        <p className="text-sm font-medium text-ink">
                          Waking up the server…
                        </p>
                        <p className="mx-auto mt-1 max-w-xs text-xs text-ink-faint">
                          Render&apos;s free tier sleeps after idle.
                          First load can take up to a minute — retrying
                          automatically.
                        </p>
                      </>
                    ) : (
                      <div className="text-sm text-ink-faint">
                        Restoring session…
                      </div>
                    )}
                  </div>
                </div>
              ) : isAuthenticated ? (
                protectedContent
              ) : (
                <Navigate to="/login" replace />
              )
            }
          />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}