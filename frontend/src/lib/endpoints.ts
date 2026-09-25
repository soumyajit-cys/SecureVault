import api from "@/lib/api";
import type {
  AuditLog,
  DecryptTextResponse,
  EncryptTextResponse,
  FileShare,
  GcResult,
  Key,
  KeyCreateResponse,
  KeyRotateResponse,
  LoginResponse,
  Paginated,
  SharedFileItem,
  StoredFile,
  StorageSummary,
  StorageUsage,
  User
} from "@/types";

export interface PasskeyLoginOptions {
  challenge: string;
  allowCredentials?: Array<{
    id: string;
    type: string;
    transports?: string[];
  }>;
  rpId?: string;
  userVerification?: string;
  timeout?: number;
  [key: string]: unknown;
}

export const auth = {
  login: (body: { email: string; password: string }) =>
    api.post<LoginResponse>("/auth/login", body).then((r) => r.data),
  register: (body: { email: string; username: string; password: string }) =>
    api.post<User>("/auth/register", body).then((r) => r.data),
  verifyMfa: (body: { mfa_token: string; code: string }) =>
    api.post<LoginResponse>("/auth/mfa/verify", body).then((r) => r.data),
  requestPasswordReset: (body: { email: string }) =>
    api
      .post<{ message: string }>("/auth/password-reset/request", body)
      .then((r) => r.data),
  confirmPasswordReset: (body: { token: string; new_password: string }) =>
    api
      .post<{ message: string }>("/auth/password-reset/confirm", body)
      .then((r) => r.data),
  verifyEmail: (body: { token: string }) =>
    api
      .post<{ message: string }>("/auth/verify-email", body)
      .then((r) => r.data),
  resendVerification: (body: { email: string }) =>
    api
      .post<{ message: string }>("/auth/resend-verification", body)
      .then((r) => r.data),
  passkeyLoginBegin: (body: { email?: string }) =>
    api
      .post<{ options: PasskeyLoginOptions }>("/auth/passkeys/login/begin", body)
      .then((r) => r.data),
  passkeyLoginComplete: (body: { response: unknown }) =>
    api
      .post<LoginResponse>("/auth/passkeys/login/complete", body)
      .then((r) => r.data)
};

export const profile = {
  me: () => api.get<User>("/profile/me").then((r) => r.data)
};

export const encryption = {
  encryptText: (body: {
    plaintext: string;
    aad?: string;
  }) => api.post<EncryptTextResponse>("/encryption/text/encrypt", body).then((r) => r.data),
  decryptText: (body: {
    ciphertext: string;
    nonce: string;
    tag: string;
    encrypted_key: string;
    aad?: string;
  }) => api.post<DecryptTextResponse>("/encryption/text/decrypt", body).then((r) => r.data)
};

export const files = {
  list: (params: { page?: number; page_size?: number; status?: string; search?: string }) =>
    api.get<Paginated<StoredFile>>("/files", { params }).then((r) => r.data),
  upload: (file: File) => {
    const form = new FormData();
    form.append("upload", file);
    return api.post<StoredFile>("/files/upload", form).then((r) => r.data);
  },
  download: (id: string) =>
    api
      .get(`/files/${id}/download`, { responseType: "blob" })
      .then((r) => r.data as Blob),
  delete: (id: string) => api.delete(`/files/${id}`).then((r) => r.data),
  summary: () => api.get<StorageSummary>("/files/summary").then((r) => r.data)
};

export const folders = {
  list: (params: { page?: number; page_size?: number }) =>
    api.get<Paginated<StoredFile>>("/folders", { params }).then((r) => r.data),
  upload: (zip: File) => {
    const form = new FormData();
    form.append("upload", zip);
    return api.post<StoredFile>("/folders/upload", form).then((r) => r.data);
  },
  restore: (id: string) =>
    api
      .post<{
        file_id: string;
        restored_path: string;
        restored_files: number;
        restored_directories: number;
      }>(`/folders/${id}/restore`)
      .then((r) => r.data)
};

export const keys = {
  list: (params: { page?: number; page_size?: number; status?: string }) =>
    api.get<Paginated<Key>>("/keys", { params }).then((r) => r.data),
  generate: (body: { name: string; validity_days?: number }) =>
    api.post<KeyCreateResponse>("/keys", body).then((r) => r.data),
  rotate: (body: {
    current_key_id: string;
    name?: string;
    validity_days?: number;
  }) => api.post<KeyRotateResponse>("/keys/rotate", body).then((r) => r.data),
  revoke: (id: string) =>
    api
      .post<{ key_id: string; revoked: boolean; revoked_at: string | null }>(
        `/keys/${id}/revoke`
      )
      .then((r) => r.data)
};

export const audit = {
  list: (params: { page?: number; page_size?: number; action?: string }) =>
    api.get<Paginated<AuditLog>>("/audit/logs", { params }).then((r) => r.data)
};

export const shares = {
  shareFile: (fileId: string, body: { grantee_email: string }) =>
    api
      .post<FileShare>(`/shares/files/${fileId}/share`, body)
      .then((r) => r.data),
  revokeShare: (fileId: string, granteeId: string) =>
    api
      .delete(`/shares/files/${fileId}/shares/${granteeId}`)
      .then((r) => r.data),
  listForFile: (fileId: string) =>
    api
      .get<FileShare[]>(`/shares/files/${fileId}/shares`)
      .then((r) => r.data),
  received: () =>
    api.get<SharedFileItem[]>("/shares/received").then((r) => r.data),
  sent: () => api.get<FileShare[]>("/shares/sent").then((r) => r.data)
};

export const admin = {
  usage: () => api.get<StorageUsage>("/admin/storage").then((r) => r.data),
  gc: () => api.post<GcResult>("/admin/garbage-collect").then((r) => r.data),
  users: (params: { page?: number; page_size?: number }) =>
    api.get<Paginated<User>>("/admin/users", { params }).then((r) => r.data),
  deactivateUser: (id: string) =>
    api.post<{ message: string }>(`/admin/users/${id}/deactivate`).then((r) => r.data),
  activateUser: (id: string) =>
    api.post<{ message: string }>(`/admin/users/${id}/activate`).then((r) => r.data)
};