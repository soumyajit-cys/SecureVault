import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import { TextArea, TextField } from "@/components/ui/Field";
import { encryption } from "@/lib/endpoints";
import { errorMessage } from "@/lib/api";
import { toastSuccess } from "@/components/ui/Toast";

interface ParsedPayload {
  nonce?: string;
  ciphertext?: string;
  tag?: string;
  encrypted_key?: string;
  aad?: string;
}

export default function DecryptText() {
  const [payload, setPayload] = useState("");
  const [aad, setAad] = useState("");
  const [plaintext, setPlaintext] = useState<string | null>(null);

  const decryptMutation = useMutation({
    mutationFn: () => {
      let parsed: ParsedPayload = {};
      try {
        parsed = JSON.parse(payload) as ParsedPayload;
      } catch {
        parsed = { ciphertext: payload };
      }
      const body = {
        ciphertext: (parsed.ciphertext ?? "").trim(),
        nonce: (parsed.nonce ?? "").trim(),
        tag: (parsed.tag ?? "").trim(),
        encrypted_key: (parsed.encrypted_key ?? "").trim(),
        aad: aad || parsed.aad || undefined
      };
      if (!body.nonce || !body.tag || !body.encrypted_key) {
        throw new Error(
          "Missing fields. Paste the full JSON result from the Encrypt page."
        );
      }
      return encryption.decryptText(body);
    },
    onSuccess: (res) => {
      setPlaintext(res.plaintext);
      toastSuccess("Decryption successful");
    }
  });

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <Card title="Ciphertext">
        <div className="space-y-4">
          <TextArea
            label="Encrypted payload (JSON result from Encrypt page, or raw ciphertext with nonce/tag/encrypted_key filled in)"
            required
            placeholder='Paste the JSON result from "Encrypt Text"'
            value={payload}
            onChange={(e) => setPayload(e.target.value)}
          />
          <div className="grid gap-4 sm:grid-cols-3">
            <TextField
              label="AAD (optional — override AAD in the JSON)"
              placeholder="AAD"
              value={aad}
              onChange={(e) => setAad(e.target.value)}
            />
          </div>

          <Button
            variant="success"
            loading={decryptMutation.isPending}
            disabled={!payload.trim()}
            onClick={() => decryptMutation.mutate()}
          >
            Decrypt &amp; verify
          </Button>
          {decryptMutation.error && (
            <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {errorMessage(decryptMutation.error)}
            </p>
          )}
        </div>
      </Card>

      {plaintext !== null && (
        <Card title="Plaintext">
          <pre className="whitespace-pre-wrap rounded-lg border border-cyber-line bg-cyber p-4 text-sm text-ink">
            {plaintext}
          </pre>
        </Card>
      )}
    </div>
  );
}