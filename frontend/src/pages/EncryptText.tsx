import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";

import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import { SelectField, TextArea, TextField } from "@/components/ui/Field";
import { encryption, keys } from "@/lib/endpoints";
import { extractDetail } from "@/lib/api";
import { toastSuccess } from "@/components/ui/Toast";

export default function EncryptText() {
  const [text, setText] = useState("");
  const [keyId, setKeyId] = useState("");
  const [aad, setAad] = useState("");
  const [result, setResult] = useState<string | null>(null);

  const { data: keyPage } = useQuery({
    queryKey: ["keys", { page: 1, page_size: 100 }],
    queryFn: () => keys.list({ page: 1, page_size: 100 })
  });

  const encryptMutation = useMutation({
    mutationFn: () =>
      encryption.encryptText({
        text,
        key_id: keyId || undefined,
        aad: aad || undefined,
        output_format: "base64"
      }),
    onSuccess: (res) => {
      setResult(JSON.stringify(res, null, 2));
      toastSuccess("Text encrypted successfully");
    }
  });

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Encrypt Text</h1>
        <p className="text-sm text-slate-500">
          AES-256-GCM with per-message nonce and authenticated encryption.
        </p>
      </div>

      <Card title="Plaintext">
        <div className="space-y-4">
          <TextArea
            label="Message"
            required
            placeholder="Enter the secret message…"
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <SelectField
              label="Encryption key"
              value={keyId}
              onChange={(e) => setKeyId(e.target.value)}
            >
              <option value="">Auto (active key)</option>
              {(keyPage?.items ?? [])
                .filter((k) => k.status === "active")
                .map((k) => (
                  <option key={k.id} value={k.id}>
                    {k.name} · {k.fingerprint?.slice(0, 8)}
                  </option>
                ))}
            </SelectField>
            <TextField
              label="Additional authenticated data (optional)"
              placeholder="AAD"
              value={aad}
              onChange={(e) => setAad(e.target.value)}
            />
          </div>

          <Button
            loading={encryptMutation.isPending}
            disabled={!text.trim()}
            onClick={() => encryptMutation.mutate()}
          >
            Encrypt
          </Button>
          {encryptMutation.error && (
            <p className="text-sm text-neon-red">{extractDetail(encryptMutation.error)}</p>
          )}
        </div>
      </Card>

      {result && (
        <Card title="Ciphertext result">
          <pre className="overflow-x-auto rounded bg-vault-950 p-4 text-xs text-neon-green">
            {result}
          </pre>
        </Card>
      )}
    </div>
  );
}