import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import { TextArea, TextField } from "@/components/ui/Field";
import { encryption } from "@/lib/endpoints";
import { errorMessage } from "@/lib/api";
import { toastSuccess } from "@/components/ui/Toast";

export default function DecryptText() {
  const [ciphertext, setCiphertext] = useState("");
  const [nonce, setNonce] = useState("");
  const [tag, setTag] = useState("");
  const [aad, setAad] = useState("");
  const [plaintext, setPlaintext] = useState<string | null>(null);

  const decryptMutation = useMutation({
    mutationFn: () =>
      encryption.decryptText({
        ciphertext: ciphertext.trim(),
        nonce: nonce.trim() || undefined,
        tag: tag.trim() || undefined,
        aad: aad || undefined,
        output_format: "base64"
      }),
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
            label="Encrypted payload"
            required
            placeholder='Paste the JSON result from "Encrypt Text"'
            value={ciphertext}
            onChange={(e) => setCiphertext(e.target.value)}
          />
          <div className="grid gap-4 sm:grid-cols-3">
            <TextField
              label="Nonce"
              placeholder="hex/base64"
              value={nonce}
              onChange={(e) => setNonce(e.target.value)}
            />
            <TextField
              label="Tag"
              placeholder="hex/base64"
              value={tag}
              onChange={(e) => setTag(e.target.value)}
            />
            <TextField
              label="AAD (optional)"
              placeholder="AAD"
              value={aad}
              onChange={(e) => setAad(e.target.value)}
            />
          </div>

          <Button
            variant="success"
            loading={decryptMutation.isPending}
            disabled={!ciphertext.trim()}
            onClick={() => decryptMutation.mutate()}
          >
            Decrypt &amp; verify
          </Button>
          {decryptMutation.error && (
            <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
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