# SecureVault — Authorization (RBAC)

## Model

```
User ──< UserRole >── Role ──< RolePermission >── Permission
```

- **Permissions** are string constants (`app/scripts/seed_permissions.py`):
  `user:create/read/update/delete`, `audit:read`, `audit:export`,
  `file:encrypt/decrypt/upload/download`, `share:create`, `share:revoke`,
  `admin:access`.
- **Roles** (`app/scripts/seed_roles.py`):
  - `Admin` — `*` (all permissions)
  - `User` — `file:encrypt`, `file:decrypt`, `file:upload`,
    `file:download`, `share:create`
  - `Auditor` — `audit:read`, `audit:export`
- **Superuser / special cases**: the bootstrapped admin
  (`VAULT_ADMIN_*` env) is granted `Admin` at startup. Role management
  (create/update/delete roles, assign to users) is itself admin-only.

## Enforcement points

1. **Authentication** — `get_current_user` (bearer token, validated as
   access type, user must exist and be active).
2. **Permission checks** — `require_permission("admin:access")`-style
   dependencies on admin routes (403 when missing).
3. **Object ownership** — all repository queries filter by `user_id`:
   `StoredFile`, `CryptoKey`, sessions. Cross-user access yields **404**
   (not 403) to avoid resource enumeration.
4. **Audit scoping** — regular users see their own audit events; admins see
   everything (`/audit/admin/logs`).

## Route → requirement map (relevant subset)

| Route group | Requirement |
| --- | --- |
| `/api/v1/profile/*`, `/files/*`, `/folders/*`, `/keys/*`, `/encryption/*` | authenticated user (own data only) |
| `/api/v1/audit/logs` | authenticated user (own events) |
| `/api/v1/audit/admin/logs`, `/api/v1/audit/export` | `audit:read` / `audit:export` (Auditor+, Admin) |
| `/api/v1/admin/*` | `admin:access` (Admin) |

## Verification

`tests/test_integration_security.py` asserts:
- role removal immediately revokes admin access (403 on next request);
- the Auditor role cannot reach admin endpoints;
- cross-user file/folder/key operations are rejected (404);
- the MFA enforcement path issues no tokens without TOTP.

## Notes

- Permission checks run against the user's *current* role membership, so
  role changes take effect immediately (no token-claim caching of roles).
- Deactivated users are rejected at authentication time.
