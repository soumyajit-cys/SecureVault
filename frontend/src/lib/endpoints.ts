import api from "@/lib/api";
import type {
  AuditLog,
  DecryptTextResponse,
  EncryptTextResponse,
  GcResult,
  Key,
  KeyCreateResponse,
  LoginResponse,
  Paginated,
  StoredFile,
  StorageSummary,
  StorageUsage,
  User
} from "@/types";

export const auth = {
  login: (body: { email: string; password: string }) =>
    api.post<LoginResponse>("/auth/login", body).then((r) => r.data),
  register: (body: { email: string; username: string; password: string }) =>
    api.post<User>("/auth/register", body).then((r) => r.data)
};

export const profile = {
  me: () => api.get<User>("/profile/me").then((r) => r.data)
};

export const encryption = {
  encryptText: (body: {
    text: string;
    key_id?: string;
    aad?: string;
    output_format?: "hex" | "base64";
  }) => api.post<EncryptTextResponse>("/encryption/text/encrypt", body).then((r) => r.data),
  decryptText: (body: {
    ciphertext: string;
    nonce?: string;
    tag?: string;
    aad?: string;
    output_format?: "hex" | "base64";
  }) => api.post<DecryptTextResponse>("/encryption/text/decrypt", body).then((r) => r.data)
};

export const files = {
  list: (params: { page?: number; page_size?: number; status?: string; search?: string }) =>
    api.get<Paginated<StoredFile>>("/files/", { params }).then((r) => r.data),
  upload: (file: File, keyId?: string) => {
    const form = new FormData();
    form.append("file", file);
    if (keyId) form.append("key_id", keyId);
    return api.post<StoredFile>("/files/upload", form).then((r) => r.data);
  },
  download: (id: string) => api.get(`/files/${id}/download`).then((r) => r.data),
  delete: (id: string) => api.delete(`/files/${id}`).then((r) => r.data),
  summary: () => api.get<StorageSummary>("/files/summary").then((r) => r.data)
};

export const folders = {
  list: (params: { page?: number; page_size?: number }) =>
    api.get<Paginated<StoredFile>>("/folders/", { params }).then((r) => r.data),
  upload: (zip: File, keyId?: string) => {
    const form = new FormData();
    form.append("file", zip);
    if (keyId) form.append("key_id", keyId);
    return api.post<StoredFile>("/folders/upload", form).then((r) => r.data);
  },
  restore: (id: string) => api.get(`/folders/${id}/restore`).then((r) => r.data)
};

export const keys = {
  list: (params: { page?: number; page_size?: number }) =>
    api.get<Paginated<Key>>("/keys/", { params }).then((r) => r.data),
  generate: (body: { name: string; algorithm: string; key_size: number; expires_in_days?: number }) =>
    api.post<KeyCreateResponse>("/keys/generate", body).then((r) => r.data),
  rotate: (id: string, body?: { reason?: string }) =>
    api.post<KeyCreateResponse>(`/keys/${id}/rotate`, body ?? {}).then((r) => r.data),
  revoke: (id: string, body?: { reason?: string }) =>
    api.post<Key>(`/keys/${id}/revoke`, body ?? {}).then((r) => r.data),
  setActive: (id: string) => api.post<Key>(`/keys/${id}/active`).then((r) => r.data),
  publicKey: (id?: string) =>
    api.get<{ key_id: string; public_key_pem: string }>("/keys/public", {
      params: id ? { key_id: id } : {}
    }).then((r) => r.data)
};

export const audit = {
  list: (params: { page?: number; page_size?: number; action?: string }) =>
    api.get<Paginated<AuditLog>>("/audit/", { params }).then((r) => r.data)
};

export const admin = {
  summary: () => api.get<StorageSummary>("/admin/storage/summary").then((r) => r.data),
  usage: () => api.get<StorageUsage>("/admin/storage/usage").then((r) => r.data),
  gc: () => api.post<GcResult>("/admin/storage/garbage-collect").then((r) => r.data),
  gcPreview: () => api.get<GcResult>("/admin/storage/garbage-collect/preview").then((r) => r.data),
  users: (params: { page?: number; page_size?: number }) =>
    api.get<Paginated<User>>("/admin/users/", { params }).then((r) => r.data),
  deactivateUser: (id: string) =>
    api.post<{ message: string }>(`/admin/users/${id}/deactivate`).then((r) => r.data),
  activateUser: (id: string) =>
    api.post<{ message: string }>(`/admin/users/${id}/activate`).then((r) => r.data)
};