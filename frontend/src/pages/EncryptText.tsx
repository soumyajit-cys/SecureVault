import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import { TextArea, TextField } from "@/components/ui/Field";
import { encryption } from "@/lib/endpoints";
import { extractDetail } from "@/lib/api";
import { toastSuccess } from "@/components/ui/Toast";

export default function EncryptText() {
  const [text, setText] = useState("");
  const [aad, setAad] = useState("");
  const [result, setResult] = useState<string | null>(null);

  const encryptMutation = useMutation({
    mutationFn: () =>
      encryption.encryptText({
        plaintext: text,
        aad: aad || undefined
      }),
    onSuccess: (res) => {
      setResult(JSON.stringify(res, null, 2));
      toastSuccess("Text encrypted successfully");
    }
  });

  return (
    <div className="mx-auto max-w-3xl space-y-6">
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
            <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {extractDetail(encryptMutation.error)}
            </p>
          )}
        </div>
      </Card>

      {result && (
        <Card title="Ciphertext result">
          <pre className="overflow-x-auto rounded-lg border border-cyber-line bg-cyber p-4 text-xs text-emerald-300">
            {result}
          </pre>
        </Card>
      )}
    </div>
  );
}