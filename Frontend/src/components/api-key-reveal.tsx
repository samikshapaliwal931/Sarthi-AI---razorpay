import { Check, Copy, ShieldAlert } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";

/**
 * One-time secret reveal, shared by onboarding (initial AI-buyer key issuance) and
 * Settings/Integrations (key regeneration). The backend never returns the raw key again
 * after this response, so this component makes that unmissable and gives a reliable
 * copy-to-clipboard control.
 */
export function ApiKeyReveal({
  apiKey,
  warning,
  label = "AI Buyer API key",
}: {
  apiKey: string;
  warning?: string;
  label?: string;
}) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(apiKey);
      setCopied(true);
      toast.success("Copied to clipboard");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Could not copy — select and copy the key manually.");
    }
  };

  return (
    <div className="rounded-xl border border-warning/40 bg-warning/5 p-5">
      <div className="flex items-start gap-3">
        <ShieldAlert className="mt-0.5 size-4 shrink-0 text-warning" aria-hidden />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold">{label} — shown once</p>
          <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
            {warning ??
              "Store this key now. For your security, Sarthi will never show it again — if you lose it, you'll need to regenerate a new one, which invalidates this one."}
          </p>
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <code className="min-w-0 flex-1 select-all break-all rounded-md border border-border bg-surface px-3 py-2 text-xs">
              {apiKey}
            </code>
            <Button
              type="button"
              size="sm"
              variant="outline"
              className="press shrink-0"
              onClick={copy}
            >
              {copied ? (
                <Check className="size-3.5" aria-hidden />
              ) : (
                <Copy className="size-3.5" aria-hidden />
              )}
              {copied ? "Copied" : "Copy"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
