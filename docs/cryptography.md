# SecureVault — Cryptography

All primitives come from the well-audited `cryptography` and `argon2-cffi`
libraries. No custom cryptographic primitives are implemented.

## Algorithms

| Use | Algorithm | Parameters |
| --- | --- | --- |
| File/text payload encryption | AES-256-GCM | 256-bit key, 96-bit (12-byte) nonce, 128-bit tag, optional AAD |
| Key wrapping | RSA-OAEP | RSA-4096 default (RSA-2048 supported), SHA-256 OAEP |
| Hybrid scheme | AES-GCM + RSA-OAEP | fresh AES session key per message |
| Password hashing | Argon2id | 100 MiB memory, 3 iterations, 4 parallelism (verifiable via `PasswordCryptoService`) |
| Integrity | SHA-256 | stored in file metadata; verified on download |
| JWT signing | RS256 | rotating RSA keys in `jwt_signing_keys` |
| At-rest wrapping | AES-256-GCM | master key derived from `SECRET_KEY` via HKDF with purpose labels (`core/key_material.py`) |
| Randomness | `os.urandom` / `secrets` | CSPRNG |

## Nonce policy

Nonces are 12 random bytes from `os.urandom`, generated fresh per
encryption. A 96-bit random nonce has a negligible collision risk within
the per-key message volume, and AES session keys are single-use per message,
which eliminates nonce reuse across messages entirely.

## Encryption flow (file upload)

1. Stream plaintext in 4 MiB chunks.
2. Generate a fresh AES-256 session key and a fresh nonce.
3. Stream-encrypt with AES-256-GCM; the final block produces the auth tag.
4. Compute SHA-256 of the plaintext.
5. Wrap the session key with the user's RSA-4096 public key (OAEP).
6. Serialize the SecureVault container: `MAGIC "SVLT"` + version + header
   (length-prefixed) + ciphertext stream + tag + wrapped key.
7. Store container; persist metadata (sizes, SHA-256, mime, key id).

## Container format (`services/encryption/container_serializer.py`)

```
+------------------+
| MAGIC "SVLT" (4) |
+------------------+
| FORMAT_VERSION   |
+------------------+
| header length    |
+------------------+
| header payload   |  (JSON: algorithm, key algorithm, hash algorithm,
+------------------+   key fingerprint, nonce, tag, sizes, metadata)
| ciphertext       |  (streamed; plaintext-derived SHA-256 outside the
+------------------+   container for metadata)
| wrapped key      |  (RSA-OAEP(AES session key))
+------------------+
```

Parsing validates magic and version before any further processing;
`ContainerSerializerError` is raised for malformed containers.

## Decryption flow (file download)

1. Read and validate the container header.
2. Load the recorded `CryptoKey`; reject if revoked or expired.
3. Unwrap the session key with the RSA private key (at-rest decrypted
   from the DB).
4. Stream-decrypt; GCM authentication fails on any corruption.
5. Verify the resulting SHA-256 against stored metadata before returning
   the file to the client.

## Failure modes

Every corruption class — wrong key, flipped ciphertext bit, tampered nonce,
tampered tag, truncated container, bad header, bad magic — fails closed with
a generic error (`DecryptionError` / `ContainerSerializerError`), never
partial data. This is covered by `tests/test_aes_tampering.py`,
`tests/test_file_decryptor.py`, and `tests/test_container_chunks.py`.

## Streaming

- Chunks: default 4 MiB, configurable between 64 KiB and 16 MiB
  (`crypto/streams/constants.py`).
- Encryption/decryption process constant-memory; arbitrary file sizes do not
  load into RAM.
- Upload/download endpoints stream via `StreamingResponse`/chunked reads.

## Key material separation

- `core/key_material.py` derives purpose-scoped keys from `SECRET_KEY`
  (`securevault-at-rest-encryption-v1` for the at-rest master key,
  `securevault-private-key-encryption` for user private-key wrapping).
- The at-rest master key wraps JWT signing keys; user RSA private keys are
  wrapped with their own purpose label and stored with nonce/tag/salt.
