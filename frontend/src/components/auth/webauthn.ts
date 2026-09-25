import type { PasskeyLoginOptions } from "@/lib/endpoints";

function bufferFromBase64Url(input: string): ArrayBuffer {
  const normalized = input.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized.padEnd(
    normalized.length + ((4 - (normalized.length % 4)) % 4),
    "="
  );
  const binary = atob(padded);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes.buffer;
}

function base64UrlFromBuffer(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (const b of bytes) binary += String.fromCharCode(b);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function isWebAuthnAvailable(): boolean {
  return (
    typeof window !== "undefined" &&
    "credentials" in navigator &&
    typeof window.PublicKeyCredential === "function"
  );
}

/**
 * Run the browser side of the backend's passwordless login:
 * `POST /auth/passkeys/login/begin` → `navigator.credentials.get` →
 * caller forwards the assertion to `/auth/passkeys/login/complete`.
 * Throws a user-readable Error when the OS dialog is dismissed or
 * WebAuthn is unavailable.
 */
export async function getPasskeyAssertion(
  options: PasskeyLoginOptions
): Promise<unknown> {
  if (!isWebAuthnAvailable()) {
    throw new Error("This browser or device doesn't support passkeys.");
  }

  const publicKey: PublicKeyCredentialRequestOptions = {
    challenge: bufferFromBase64Url(options.challenge),
    rpId: options.rpId,
    timeout: options.timeout ?? 60000,
    userVerification:
      (options.userVerification as UserVerificationRequirement) ?? "preferred",
    allowCredentials: (options.allowCredentials ?? []).map((c) => ({
      id: bufferFromBase64Url(c.id),
      type: c.type as PublicKeyCredentialType,
      transports: c.transports as AuthenticatorTransport[] | undefined
    }))
  };

  let credential: Credential | null;
  try {
    credential = await navigator.credentials.get({ publicKey });
  } catch (err) {
    if (err instanceof DOMException && err.name === "NotAllowedError") {
      throw new Error("Passkey prompt was dismissed. Try again when ready.");
    }
    throw new Error("Couldn't complete the passkey ceremony. Try again.");
  }

  if (
    !credential ||
    !(credential instanceof PublicKeyCredential) ||
    !(credential.response instanceof AuthenticatorAssertionResponse)
  ) {
    throw new Error("Couldn't read the passkey response. Try again.");
  }

  const response = credential.response;
  return {
    id: credential.id,
    rawId: base64UrlFromBuffer(credential.rawId),
    type: credential.type,
    response: {
      clientDataJSON: base64UrlFromBuffer(response.clientDataJSON),
      authenticatorData: base64UrlFromBuffer(response.authenticatorData),
      signature: base64UrlFromBuffer(response.signature),
      userHandle: response.userHandle
        ? base64UrlFromBuffer(response.userHandle)
        : null
    }
  };
}
