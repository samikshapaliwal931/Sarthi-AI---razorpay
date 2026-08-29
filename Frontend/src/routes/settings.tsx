import { useMutation, useQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { KeyRound } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { AppShell } from "@/components/app-shell";
import { ApiKeyReveal } from "@/components/api-key-reveal";
import { PageHeader, Panel, PermissionDenied, QueryBoundary } from "@/components/primitives";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { api, integrationsApi } from "@/services/sarthi";

export const Route = createFileRoute("/settings")({
  head: () => ({
    meta: [
      { title: "Workspace settings — Sarthi" },
      {
        name: "description",
        content:
          "Store profile, agent autonomy level, appearance and team access for your Sarthi workspace.",
      },
      { property: "og:title", content: "Workspace settings — Sarthi" },
      {
        property: "og:description",
        content: "Store profile, autonomy, appearance and team access.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: SettingsPage,
});

function SettingsPage() {
  const query = useQuery({ queryKey: ["merchant"], queryFn: api.getMerchant });
  const [dark, setDark] = useState(false);
  const [regeneratedKey, setRegeneratedKey] = useState<{ api_key: string; warning: string } | null>(
    null,
  );

  const regenerateKey = useMutation({
    mutationFn: () => integrationsApi.regenerateAiBuyerKey(),
    onSuccess: (res) => {
      setRegeneratedKey(res);
      toast.success("New AI Buyer key issued", {
        description: "The previous key no longer works.",
      });
    },
    onError: () => toast.error("Could not regenerate the AI Buyer key"),
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  return (
    <AppShell>
      <PageHeader
        eyebrow="Workspace"
        title="Settings"
        description="Who you are, how much autonomy Sarthi has, and who else can approve actions on your behalf."
      />
      <QueryBoundary query={query} rows={3}>
        {(m) => (
          <div className="grid gap-5 lg:grid-cols-2">
            <Panel title="Store profile">
              <form
                className="space-y-4"
                onSubmit={(e) => {
                  e.preventDefault();
                  toast.success("Profile saved");
                }}
              >
                <div className="space-y-2">
                  <Label htmlFor="store">Store name</Label>
                  <Input id="store" defaultValue={m.name} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="domain">Domain</Label>
                  <Input id="domain" defaultValue={m.storeUrl} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="currency">Currency</Label>
                  <Input id="currency" defaultValue={m.currency} readOnly aria-readonly />
                </div>
                <Button type="submit" className="press">
                  Save profile
                </Button>
              </form>
            </Panel>

            <div className="space-y-5">
              <Panel title="Appearance">
                <div className="flex items-center justify-between gap-6">
                  <div>
                    <p className="text-sm font-medium">Dark cockpit</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Switch to the low-light palette for late trading hours.
                    </p>
                  </div>
                  <Switch checked={dark} onCheckedChange={setDark} aria-label="Toggle dark mode" />
                </div>
              </Panel>

              <Panel title="Agent autonomy">
                <div className="space-y-4 text-sm">
                  <p className="text-muted-foreground">
                    Sarthi is currently running in{" "}
                    <span className="font-medium text-foreground">supervised</span> mode: it
                    discovers and proposes freely, but every customer-facing or money-moving action
                    waits for your approval.
                  </p>
                  <PermissionDenied what="autonomy level" />
                </div>
              </Panel>

              <Panel
                title="Sarthi Open Storefront / AI Buyer"
                description="The scoped key external AI shopping agents use to search and check out on your store."
              >
                {regeneratedKey ? (
                  <ApiKeyReveal apiKey={regeneratedKey.api_key} warning={regeneratedKey.warning} />
                ) : (
                  <div className="space-y-3">
                    <p className="text-sm text-muted-foreground">
                      Manage connections and view the AI Buyer API endpoints in{" "}
                      <Link
                        to="/integrations"
                        className="text-primary underline-offset-4 hover:underline"
                      >
                        Integrations
                      </Link>
                      , or issue a fresh key here — this invalidates any previous key immediately.
                    </p>
                    <Button
                      size="sm"
                      variant="outline"
                      className="press"
                      disabled={regenerateKey.isPending}
                      onClick={() => regenerateKey.mutate()}
                    >
                      <KeyRound className="size-3.5" aria-hidden />
                      {regenerateKey.isPending
                        ? "Generating…"
                        : "Generate / regenerate AI Buyer key"}
                    </Button>
                  </div>
                )}
              </Panel>

              <Panel title="Team">
                <ul className="divide-y divide-border text-sm">
                  {[
                    { name: "You", role: "Owner · full approval rights" },
                    { name: "Ops analyst", role: "Analyst · view only" },
                    { name: "Finance", role: "Reviewer · approves spend over ₹50,000" },
                  ].map((t) => (
                    <li
                      key={t.name}
                      className="flex items-center justify-between gap-4 py-3 first:pt-0 last:pb-0"
                    >
                      <span className="font-medium">{t.name}</span>
                      <span className="text-xs text-muted-foreground">{t.role}</span>
                    </li>
                  ))}
                </ul>
              </Panel>
            </div>
          </div>
        )}
      </QueryBoundary>
    </AppShell>
  );
}
