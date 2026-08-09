# SecureVault — Authentication

## Flow overview

```
register ─► email verification (optional) ─► login ─► access + refresh tokens
                                                          │
                                             refresh rotation on 401 (SPA)
                                                          │
                                                      logout ─► tokens revoked
```

## Registration

- `POST /auth/register` — email, username, password.
- Password policy enforced (min length, complexity classes) and optional
  HIBP pwned check (`PWNED_CHECK_ENABLED`).
- If `EMAIL_VERIFICATION_REQUIRED` is set, an email is "sent"
  (`EMAIL_BACKEND`; in development the token is logged) and login is gated
  until verified.

## Login

- `POST /auth/login` — validates credentials, applies account lockout
  (`MAX_LOGIN_ATTEMPTS` / `ACCOUNT_LOCK_MINUTES`), enforces MFA policy
  (`AppSetting["mfa_policy"]` optional|required — enforced logins return
  `mfa_required`).
- On success: creates a session row (device fingerprint + user-agent +
  IP), issues an access token (15 min) and a refresh token (7 days), and
  records `user.login` (+ `device.new` on first device).
- If TOTP is enabled, returns `mfa_required: true` and an `mfa_token`
  (5-min MFA challenge) instead of tokens.

## MFA (TOTP)

- `GET /auth/mfa/status`, `POST /auth/mfa/setup|enable|disable`,
  `POST /auth/mfa/verify`.
- Setup returns the TOTP secret; enable requires a correct TOTP code.
- `POST /auth/mfa/verify` exchanges the mfa_token + TOTP/recovery code for
  real tokens. Wrong codes increment the lockout counter.
- Recovery codes: 10 one-time codes, single-use, hashed at rest.

## WebAuthn passkeys

- Registration: `POST /auth/passkeys/register/begin|complete`.
- Login: `POST /auth/passkeys/login/begin|complete`.
- List/remove: `GET /auth/passkeys`, `DELETE /auth/passkeys/{id}`.
- Signatures verified with FIDO2 semantics; sign count is monotonic.
- When `mfa_policy=required`, users must enroll TOTP or a passkey before
  login completes (enforcement lives in `auth_service.login`).

## Tokens

- **Access token** — RS256 JWT, claims: `sub` (user id), `email`,
  `session_id`, `token_type: access`, `exp`.
- **Refresh token** — same claims + `jti`, `token_type: refresh`,
  hashed at rest in `refresh_tokens` with a family id.
- **MFA challenge** — `token_type: mfa_challenge`, 5-min lifetime.

Only `token_type == access` satisfies `get_current_user`; using a refresh or
mfa-challenge token as a bearer token returns 401 (see
`api/dependencies/current_user.py`).

## Refresh rotation & replay protection

- `POST /auth/refresh` — the presented refresh token is marked revoked and a
  new token is issued in the same family.
- Presenting an **already-revoked** token (replay) revokes the **entire
  family** and returns 401 — both the stolen token and the current session's
  token become useless.
- Logout revokes the refresh token; refresh after logout fails.
- Expired or unknown tokens fail with 401.

## Sessions & device awareness

- `GET /auth/sessions` — list active sessions (device name derived from
  user-agent, fingerprint).
- `DELETE /auth/sessions/{id}` — revoke one session.
- `POST /auth/sessions/revoke-all` — revoke all other sessions.
- Changing the password revokes all other sessions.
- Login reports `new_device` so the UI can flag unrecognized devices.

## Email verification & password reset

- `POST /auth/verify-email` (token from the verification email),
  `POST /auth/resend-verification`.
- `POST /auth/password-reset/request` — always returns the same response
  whether or not the email exists (no user enumeration).
- `POST /auth/password-reset/confirm` — token + new password; resets
  sessions and revokes refresh tokens.

## Rate limiting (auth)

- Login attempts: per IP+email bucket (`RATE_LIMIT_LOGIN_PER_MINUTE`),
  returns 429 with `Retry-After` when exceeded.
- `RATE_LIMIT_BACKEND=local` (in-memory) or `redis` (shared across workers).
- Trusted-proxy-aware: reads `X-Forwarded-For` when `TRUSTED_PROXY_COUNT > 0`.
