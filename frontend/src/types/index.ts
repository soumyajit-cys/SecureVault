export interface Role {
  id: string;
  name: string;
}

export interface User {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  is_verified: boolean;
  roles: Role[];
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
}

export interface Key {
  id: string;
  name: string;
  algorithm: string;
  key_size: number;
  status: "active" | "revoked" | "expired";
  fingerprint: string;
  expires_at: string | null;
  revoked_at: string | null;
  replaced_by_key_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface KeyCreateResponse extends Key {
  public_key_pem: string;
}

export interface EncryptTextResponse {
  nonce: string;
  ciphertext: string;
  tag: string;
  encrypted_key: string;
  algorithm: string;
  key_algorithm: string;
  hash_algorithm: string;
}

export interface DecryptTextResponse {
  plaintext: string;
}

export interface StoredFile {
  id: string;
  user_id: string;
  key_id: string | null;
  original_filename: string;
  mime_type: string;
  original_size: number;
  encrypted_size: number;
  sha256: string;
  is_folder: boolean;
  folder_file_count: number;
  status: string;
  deleted_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface AuditLog {
  id: string;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  details: string | null;
  created_at: string;
  updated_at: string;
}

export interface StorageSummary {
  file_count: number;
  folder_count: number;
  encrypted_bytes: number;
  original_bytes: number;
}

export interface GcResult {
  orphaned_containers: number;
  missing_records: number;
  purged_deleted: number;
  temp_files: number;
}

export interface StorageUsage {
  storage_bytes: number;
  stored_file_count: number;
  temp_file_count: number;
}