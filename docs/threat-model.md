# SecureVault — Threat Model

Scope: SecureVault v1.0 (FastAPI backend, React frontend, PostgreSQL,
optional Redis). Security model: **server-side encryption, server-held key
custody** (not zero-knowledge — see `docs/security.md`).

## Assets

- File plaintext (the primary protected asset)
- Per-user RSA private keys (wrapped at rest)
- JWT signing keys (wrapped at rest)
- User credentials (Argon2id hashes), TOTP secrets
- Refresh tokens (hashed at rest), sessions
- Audit trail (hash-chained)
- `SECRET_KEY` (master at-rest key)

## Threat actors

1. **External attacker** — unauthenticated, remote.
2. **Compromised user** — valid account with stolen/leaked credentials.
3. **Malicious authenticated user** — legitimate account, hostile intent.
4. **Compromised administrator** — admin account or DB-level access.
5. **Database attacker** — read/write access to PostgreSQL.
6. **Storage attacker** — access to the vault storage volume.
7. **Network attacker** — MITM between browser, API, DB, Redis.
8. **Malicious file uploader** — crafts hostile uploads (archives, payloads).

## Threat table (STRIDE/OWASP-aligned)

| # | Threat | Attack vector | Impact | Likelihood | Mitigation | Residual risk |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | Credential stuffing / brute force | Login endpoint | Account takeover | High | Argon2id, login rate limit (per IP+email), lockout, optional HIBP check | Low (distributed bots can evade per-IP limits) |
| T2 | Password reuse on leaked hash DB | DB breach → offline cracking | Account takeover | Medium | Argon2id 100 MiB, unique salts; pwned check on registration | Low |
| T3 | Refresh-token theft/replay | Token leak, logs, XSS | Persistent session hijack | Medium | Rotation, family revocation on replay, hashed-at-rest tokens, short access TTL, logout revocation | Low |
| T4 | Access-token misuse (MFA challenge / refresh as bearer) | Token type confusion | MFA bypass | Low | `get_current_user` enforces `token_type == access` | Negligible |
| T5 | MFA bypass | TOTP brute force, recovery-code theft | Account takeover | Medium | 6-digit codes, rate limits, single-use recovery codes, lockout on MFA failure | Low |
| T6 | IDOR (cross-user file/key/folder access) | Guess/steal UUIDs, call APIs directly | Confidentiality breach | Medium | Ownership-scoped queries, 404 on foreign resources, tests assert matrix | Low |
| T7 | Privilege escalation | Role tampering, admin endpoint abuse | Full compromise | Medium | RBAC `require_permission`, admin-only role CRUD, immediate revocation on role change | Low |
| T8 | Zip bomb / archive bombs | Folder upload, restore | Disk exhaustion DoS | Medium | Compression-ratio guard, total-size cap, duplicate/traversal rejection | Low (caps are generous) |
| T9 | Path traversal / symlink attack | Filename in archive or request | Write outside vault | Medium | UUID layout, `resolve_path` containment, archive member checks | Low |
| T10 | Oversized uploads / request floods | Large multipart, large JSON | Memory/disk DoS | High | `MAX_UPLOAD_SIZE_BYTES` (413), streaming reads, text-crypto caps, crypto rate limit | Low |
| T11 | Ciphertext tampering | Modify container on storage | Data corruption | Medium | AES-GCM tag, SHA-256 verification, container header validation | Low (fail-closed) |
| T12 | Key compromise via at-rest wrap | DB + app crash dumps | Decrypt vault | Medium | Purpose-scoped HKDF keys, AES-256-GCM wrapping, `SECRET_KEY` in secret manager | Medium (server compromise defeats all) |
| T13 | Server/operator compromise | Any | Full plaintext access | Low (trust boundary) | Documented model; monitoring, least privilege | Accepted — by design |
| T14 | Session fixation / CSRF | API cookie-less? Bearer only | Session hijack | Low | Bearer tokens in headers, no cookies; CORS restricted | Low |
| T15 | Audit tampering | DB write access | Forensic blindness | Medium | Hash chain, `verify-chain` endpoint, append-only discipline | Medium (attacker with DB write can rewrite chain to match) |
| T16 | Email/password-reset abuse | Reset endpoint | Account lockout/hijack | Medium | Unenumeration-safe responses, token expiry, session revocation on reset | Low |
| T17 | Malicious upload content (not archives) | Large/odd files | Storage waste | Medium | Size caps, quota per user | Low |
| T18 | Network sniffing | MITM | Token/credential theft | Medium | TLS everywhere (proxy), HSTS | Low |
| T19 | Log leakage | Logs contain sensitive fields | Token/path disclosure | Medium | Structured logging excludes secrets; `bind_actor` logs ids only | Low |
| T20 | XSS in SPA | Reflected/stored input rendering | Token theft | Medium | React escaping by default, no `dangerouslySetInnerHTML` in critical paths, CSP headers | Low |
| T21 | Dependency vulnerabilities | Outdated packages | RCE | Medium | Vendored audited libs (`cryptography`, `argon2-cffi`); keep updated | Low |
| T22 | Rate-limit bypass via spoofed IP | `X-Forwarded-For` abuse | DoS on login/crypto | Medium | Trusted-proxy-aware extraction (only when behind proxy), Redis backend | Low |

## CIA & OWASP mapping

- **Confidentiality**: AES-256-GCM, RSA-4096 wrapping, at-rest wrapping,
  ownership scoping (T1–T7, T12).
- **Integrity**: GCM tags, SHA-256 metadata verification, audit hash chain
  (T11, T15).
- **Availability**: rate limiting, size caps, streaming, GC (T8, T10).
- **OWASP ASVS highlights**: authentication (V2), session mgmt (V3),
  access control (V4), crypto (V6), file handling (V12), API hardening (V5,
  V11).
- **OWASP API Top 10**: BOLA → T6, broken auth → T1/T3/T5, resource
  consumption → T8/T10, injection → validation-first Pydantic, logging
  leaks → T19, misconfig → CORS/proxy settings, unsafe consumption of APIs
  (zip parsing) → T8.

## Residual risk statement

The dominant residual risk is **T13 — server compromise**, inherent to the
server-held key-custody model. All other residual risks are rated Low or
Medium with concrete mitigations. Full zero-knowledge would require the
client-side key-custody redesign described in `docs/security.md` (treated
as future work).
