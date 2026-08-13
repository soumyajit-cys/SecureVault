# SecureVault — Security Model

## Summary

SecureVault provides **server-side encryption with server-held key custody**.
It is **NOT zero-knowledge**: the server can decrypt user data.

## Key custody analysis

| Question | Answer |
| --- | --- |
| Who generates encryption keys? | The server (`KeyManagementService.generate_key_pair`) |
| Who possesses the RSA private keys? | The server, in the database |
| Can the server decrypt user files? | Yes — it holds the RSA private keys and unwraps session keys during download |
| Where does plaintext exist? | In server memory during encrypt/decrypt; in the browser during upload/download; never on disk in the normal flow |
| Where does the AES session key exist? | In server memory during an operation; wrapped inside the container at rest |
| Where does the RSA private key exist? | In the DB, wrapped at rest with a master key derived from `SECRET_KEY`; in server memory when unlocked |
| Can administrators access plaintext? | Yes, if they control the server/DB + `SECRET_KEY` (or code) |
| Can the backend decrypt user files? | Yes |

Because the private key material is wrapped with a server-held master key
rather than a user-held secret, a database breach alone does not expose keys,
but a server compromise (code or secret material) fully compromises the
vault. Files are additionally protected by AES-256-GCM authentication, so
ciphertext is not forgeable even by an attacker who obtains the wrapped keys.

## What the protection actually gives you

- **Storage-volume compromise**: ciphertext only; AES-256-GCM + RSA-4096
  make plaintext recovery infeasible without the keys.
- **Database compromise**: wrapped private keys and wrapped JWT signing keys;
  `SECRET_KEY` (env/secret manager) is required to unwrap.
- **API-level attacks**: ownership-scoped queries (no IDOR), RBAC, rate
  limiting, validated inputs.
- **File integrity**: SHA-256 of the plaintext is stored in metadata and
  verified on download; GCM tags detect any tampering.
- **Not protected against**: a fully compromised server/operator.

## Changes required for true zero-knowledge (future work)

1. **Client-side key generation**: generate the RSA parent keypair in the
   browser (WebCrypto); upload only the public half.
2. **Client-side private-key protection**: wrap the private key with a
   key derived from the user's password (PBKDF2/Argon2id in the browser);
   the server stores only the wrapped blob and never sees the unwrapping
   secret.
3. **Client-side crypto**: encrypt/decrypt file payloads in the browser so
   plaintext never reaches the server.
4. **Server role reduction**: the server becomes a metadata + ciphertext
   store (encrypted blob upload/download) and an audit/access authority.

These changes are intentionally NOT implemented automatically: they alter the
threat model, the API, the UI and the container format, and must be a
deliberate product decision.

## Secret management

- `SECRET_KEY` is read from the environment (`.env` in development, secret
  manager in production). It is used to derive the master encryption key for
  at-rest wrapping (HKDF with a purpose label; see `core/key_material.py`).
- No hardcoded passwords, API keys, JWT secrets, or private keys exist in the
  source tree. The Docker Compose file uses `SECRET_KEY` from the environment
  with a mandatory variable guard (`${SECRET_KEY:?}`).
- JWT signing keys are randomly generated RSA keys stored in
  `jwt_signing_keys`, wrapped at rest, rotated on a schedule with a grace
  period for old keys.
- Logs never contain tokens, keys, passwords, or plaintext content.

## Hardening measures in place

- Rate limiting on login (per IP+email) and crypto/upload/download paths.
  In production the rate limiter **must** use the Redis backend so state is
  shared across instances; startup refuses to run otherwise
  (`RATE_LIMIT_BACKEND=redis` required when `APP_ENV=production`).
- Account lockout after `MAX_LOGIN_ATTEMPTS` failures.
- Refresh-token rotation with family revocation on replay.
- Refresh tokens travel only in an **HttpOnly, Secure, SameSite=Strict**
  cookie scoped to `/api/v1/auth`; the access token is kept in browser
  memory and never persisted. `/auth/refresh` and `/auth/logout` require
  a CSRF double-submit (`X-CSRF-Token` header matching the `sv_csrf`
  cookie). API clients may still refresh via a JSON body token (legacy
  path, no cookie involved).
- MFA enforcement policy (`Admin` setting, optional|required). Even in
  "optional" mode, **Admin and Auditor roles must have MFA enrolled**
  before they can use privileged endpoints (403 otherwise).
- Token-type validation: only `access` tokens satisfy `get_current_user`;
  MFA challenge and refresh tokens are rejected as access tokens.
- Expired keys are excluded from key selection.
- Zip-bomb guards (total size cap + compression-ratio check) and archive
  traversal/duplicate rejection.
- Upload size enforcement (413) and bounded text-crypto payloads.
- Ownership-scoped repository queries; cross-user access returns 404.
- Global exception handler: client errors never leak stack traces, SQL, or
  filesystem paths.
- Security headers: `X-Content-Type-Options`, `X-Frame-Options`,
  `Content-Security-Policy` (`default-src 'self'`, Google Fonts origins
  whitelisted, `frame-ancestors 'none'`), HSTS (production),
  `Referrer-Policy`, `Cross-Origin-*`.
- Breached-password screening at registration/password change
  (`PWNED_CHECK_ENABLED=true` by default; k-anonymity HIBP query).
- Startup validation fails loudly in production on placeholder
  `SECRET_KEY`/`VAULT_ADMIN_PASSWORD` values and on the local rate-limit
  backend (see `core/security_settings.py`).

## What we explicitly do not claim

- Zero-knowledge / end-to-end encryption.
- Client-side key custody.
- Deniable storage.
- Perfect forward secrecy for at-rest data after master-key compromise.
