import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { CreditCard, Code, KeyRound, RefreshCw, ShoppingBag, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { AppShell } from "@/components/app-shell";
import { ApiKeyReveal } from "@/components/api-key-reveal";
import {
  PageHeader,
  Panel,
  QueryBoundary,
  Stagger,
  StaggerItem,
  StatusBadge,
} from "@/components/primitives";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { integrationsApi, type IntegrationRecord } from "@/services/sarthi";

export const Route = createFileRoute("/integrations")({
  head: () => ({
    meta: [
      { title: "Integrations — Sarthi" },
      {
        name: "description",
        content:
          "Connect Razorpay, your storefront widget and the AI Buyer API so Sarthi can see the full revenue picture.",
      },
      { property: "og:title", content: "Integrations — Sarthi" },
      {
        property: "og:description",
        content: "Payments, widget and AI Buyer connections.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: IntegrationsPage,
});

function IntegrationsPage() {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["integrations"], queryFn: integrationsApi.list });

  const [showRazorpayForm, setShowRazorpayForm] = useState(false);
  const [keyId, setKeyId] = useState("");
  const [keySecret, setKeySecret] = useState("");
  const [webhookSecret, setWebhookSecret] = useState("");

  const [showWidgetModal, setShowWidgetModal] = useState(false);
  const [widgetCode, setWidgetCode] = useState("");
  const [widgetLoading, setWidgetLoading] = useState(false);

  const [showCatalogModal, setShowCatalogModal] = useState(false);
  const [catalogSyncing, setCatalogSyncing] = useState(false);

  const [regeneratedKey, setRegeneratedKey] = useState<{ api_key: string; warning: string } | null>(
    null,
  );

  const connectRazorpay = useMutation({
    mutationFn: () =>
      integrationsApi.connectRazorpay(
        keyId.trim(),
        keySecret.trim(),
        webhookSecret.trim() || undefined,
      ),
    onSuccess: () => {
      toast.success("Razorpay connected", {
        description: "Test-mode keys are stored encrypted server-side.",
      });
      setShowRazorpayForm(false);
      setKeyId("");
      setKeySecret("");
      setWebhookSecret("");
      queryClient.invalidateQueries({ queryKey: ["integrations"] });
    },
    onError: (err) =>
      toast.error("Could not connect Razorpay", {
        description:
          err instanceof Error ? err.message : "Check your key ID and secret and try again.",
      }),
  });

  const deleteIntegration = useMutation({
    mutationFn: (id: string) => integrationsApi.delete(id),
    onSuccess: () => {
      toast.success("Integration disconnected");
      queryClient.invalidateQueries({ queryKey: ["integrations"] });
    },
    onError: () => toast.error("Could not disconnect that integration"),
  });

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

  const generateWidgetCode = async () => {
    setWidgetLoading(true);
    try {
      const response = await fetch("/api/v1/integrations/widget/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      const data = await response.json();
      setWidgetCode(data.html_snippet);
      setShowWidgetModal(true);
    } catch (error) {
      console.error("Failed to generate widget code:", error);
      toast.error("Could not generate widget code", {
        description: "Ensure the backend is reachable.",
      });
    } finally {
      setWidgetLoading(false);
    }
  };

  const handleCatalogSync = async (syncType: string) => {
    setCatalogSyncing(true);
    try {
      const response = await fetch("/api/v1/integrations/catalog/sync", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sync_type: syncType,
          products_data: syncType === "json" ? [] : undefined,
        }),
      });
      const data = await response.json();
      toast.success("Catalog sync completed", {
        description: `${data.products_created ?? 0} created, ${data.products_updated ?? 0} updated.`,
      });
      setShowCatalogModal(false);
    } catch (error) {
      console.error("Catalog sync failed:", error);
      toast.error("Catalog sync failed", { description: "Ensure the backend is reachable." });
    } finally {
      setCatalogSyncing(false);
    }
  };

  const razorpayIntegration = query.data?.find((i) => i.provider === "razorpay" && i.is_active);

  return (
    <AppShell>
      <PageHeader
        eyebrow="Workspace"
        title="Integrations"
        description="Sarthi reads broadly and writes narrowly. Every connection here is a real, live credential — nothing on this page is a demo."
      />

      <QueryBoundary query={query} rows={2}>
        {(integrations) => (
          <Stagger className="grid gap-5 md:grid-cols-2">
            <StaggerItem>
              <IntegrationCard
                icon={CreditCard}
                name="Razorpay"
                status={razorpayIntegration ? "connected" : "disconnected"}
                detail="Real Razorpay TEST-mode keys for payments, refunds and payouts on this store."
                scope="Read payments · charge only with policy approval"
              >
                {razorpayIntegration ? (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">
                      Key ID: {String(razorpayIntegration.config?.["key_id"] ?? "—")}
                    </span>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="press text-destructive"
                      disabled={deleteIntegration.isPending}
                      onClick={() => deleteIntegration.mutate(razorpayIntegration.id)}
                    >
                      <Trash2 className="size-3.5" aria-hidden /> Disconnect
                    </Button>
                  </div>
                ) : (
                  <Button
                    size="sm"
                    variant="outline"
                    className="press"
                    onClick={() => setShowRazorpayForm(true)}
                  >
                    Connect Razorpay
                  </Button>
                )}
              </IntegrationCard>
            </StaggerItem>

            <StaggerItem>
              <IntegrationCard
                icon={ShoppingBag}
                name="Storefront catalog"
                status="connected"
                detail="Sync your product catalog from JSON/CSV, an API feed, or a database source."
                scope="Read catalog, inventory, pricing"
              >
                <Button
                  size="sm"
                  variant="outline"
                  className="press"
                  onClick={() => setShowCatalogModal(true)}
                >
                  Sync products
                </Button>
              </IntegrationCard>
            </StaggerItem>

            <StaggerItem>
              <IntegrationCard
                icon={Code}
                name="Sarthi Widget"
                status="disconnected"
                detail="Embed code for the AI shopping assistant widget on your storefront."
                scope="Customer-facing AI chat"
              >
                <Button
                  size="sm"
                  variant="outline"
                  className="press"
                  disabled={widgetLoading}
                  onClick={generateWidgetCode}
                >
                  {widgetLoading ? "Generating…" : "Generate widget"}
                </Button>
              </IntegrationCard>
            </StaggerItem>

            {integrations
              .filter((i) => i.provider !== "razorpay")
              .map((i) => (
                <StaggerItem key={i.id}>
                  <IntegrationCard
                    icon={ShoppingBag}
                    name={i.provider}
                    status={i.is_active ? "connected" : "disconnected"}
                    detail={`${i.integration_type} integration`}
                    scope="Managed connection"
                  >
                    <Button
                      size="sm"
                      variant="ghost"
                      className="press text-destructive"
                      disabled={deleteIntegration.isPending}
                      onClick={() => deleteIntegration.mutate(i.id)}
                    >
                      <Trash2 className="size-3.5" aria-hidden /> Disconnect
                    </Button>
                  </IntegrationCard>
                </StaggerItem>
              ))}
          </Stagger>
        )}
      </QueryBoundary>

      {showRazorpayForm ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
          <div className="w-full max-w-md rounded-lg border border-border bg-card p-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold">Connect Razorpay</h3>
              <Button variant="ghost" size="sm" onClick={() => setShowRazorpayForm(false)}>
                Close
              </Button>
            </div>
            <p className="mb-4 text-sm text-muted-foreground">
              Paste your Razorpay TEST-mode key ID and secret. They're encrypted server-side and
              never stored in the browser.
            </p>
            <form
              className="space-y-4"
              onSubmit={(e) => {
                e.preventDefault();
                connectRazorpay.mutate();
              }}
            >
              <div className="space-y-2">
                <Label htmlFor="key_id">Key ID</Label>
                <Input
                  id="key_id"
                  value={keyId}
                  onChange={(e) => setKeyId(e.target.value)}
                  placeholder="rzp_test_…"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="key_secret">Key secret</Label>
                <Input
                  id="key_secret"
                  type="password"
                  value={keySecret}
                  onChange={(e) => setKeySecret(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="webhook_secret">Webhook secret (optional)</Label>
                <Input
                  id="webhook_secret"
                  type="password"
                  value={webhookSecret}
                  onChange={(e) => setWebhookSecret(e.target.value)}
                />
              </div>
              <div className="flex gap-2">
                <Button
                  type="submit"
                  className="press flex-1"
                  disabled={connectRazorpay.isPending || !keyId.trim() || !keySecret.trim()}
                >
                  {connectRazorpay.isPending ? "Connecting…" : "Connect"}
                </Button>
                <Button type="button" variant="outline" onClick={() => setShowRazorpayForm(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </div>
        </div>
      ) : null}

      {showWidgetModal ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
          <div className="w-full max-w-2xl rounded-lg border border-border bg-card p-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold">Sarthi Widget Embed Code</h3>
              <Button variant="ghost" size="sm" onClick={() => setShowWidgetModal(false)}>
                Close
              </Button>
            </div>
            <p className="mb-4 text-sm text-muted-foreground">
              Add this code to your website's HTML before the closing &lt;/body&gt; tag.
            </p>
            <pre className="mb-4 overflow-auto rounded bg-surface p-4 text-xs">
              <code>{widgetCode}</code>
            </pre>
            <div className="flex gap-2">
              <Button
                size="sm"
                onClick={() => {
                  navigator.clipboard.writeText(widgetCode);
                  toast.success("Code copied to clipboard");
                }}
              >
                Copy to clipboard
              </Button>
              <Button size="sm" variant="outline" onClick={() => setShowWidgetModal(false)}>
                Done
              </Button>
            </div>
          </div>
        </div>
      ) : null}

      {showCatalogModal ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
          <div className="w-full max-w-md rounded-lg border border-border bg-card p-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold">Sync product catalog</h3>
              <Button variant="ghost" size="sm" onClick={() => setShowCatalogModal(false)}>
                Close
              </Button>
            </div>
            <p className="mb-4 text-sm text-muted-foreground">
              Choose how you want to sync your catalog to Sarthi.
            </p>
            <div className="space-y-2">
              <Button
                className="w-full justify-start"
                variant="outline"
                disabled={catalogSyncing}
                onClick={() => handleCatalogSync("json")}
              >
                <RefreshCw className="mr-2 size-4" /> Sync from JSON/CSV
              </Button>
              <Button
                className="w-full justify-start"
                variant="outline"
                disabled={catalogSyncing}
                onClick={() => handleCatalogSync("api")}
              >
                <ShoppingBag className="mr-2 size-4" /> Sync from API feed
              </Button>
              <Button
                className="w-full justify-start"
                variant="outline"
                disabled={catalogSyncing}
                onClick={() => handleCatalogSync("database")}
              >
                <CreditCard className="mr-2 size-4" /> Sync from database
              </Button>
            </div>
          </div>
        </div>
      ) : null}

      <Panel title="Data handling">
        <p className="text-sm leading-relaxed text-muted-foreground">
          Sarthi stores derived signals, not raw card data. Customer identifiers are pseudonymised
          before they reach any model, and every write action is gated by the policy centre and
          recorded in the audit trail.
        </p>
      </Panel>

      <Panel
        title="AI Buyer API"
        description="Lets external AI shopping agents search and check out on your store through a dedicated, scoped key."
      >
        <div className="space-y-4">
          <div className="space-y-2">
            <div className="rounded bg-surface p-3 text-xs font-mono">
              POST /api/v1/ai-buyer/search
            </div>
            <div className="rounded bg-surface p-3 text-xs font-mono">
              POST /api/v1/ai-buyer/checkout
            </div>
            <div className="rounded bg-surface p-3 text-xs font-mono">
              GET /api/v1/ai-buyer/catalog
            </div>
          </div>

          {regeneratedKey ? (
            <ApiKeyReveal apiKey={regeneratedKey.api_key} warning={regeneratedKey.warning} />
          ) : (
            <Button
              size="sm"
              variant="outline"
              className="press"
              disabled={regenerateKey.isPending}
              onClick={() => regenerateKey.mutate()}
            >
              <KeyRound className="size-3.5" aria-hidden />
              {regenerateKey.isPending ? "Generating…" : "Generate / regenerate AI Buyer key"}
            </Button>
          )}
          {regeneratedKey ? (
            <Button
              size="sm"
              variant="ghost"
              className="press"
              disabled={regenerateKey.isPending}
              onClick={() => regenerateKey.mutate()}
            >
              <RefreshCw className="size-3.5" aria-hidden /> Regenerate again
            </Button>
          ) : null}
        </div>
      </Panel>
    </AppShell>
  );
}

function IntegrationCard({
  icon: Icon,
  name,
  status,
  detail,
  scope,
  children,
}: {
  icon: React.ComponentType<{ className?: string }>;
  name: string;
  status: "connected" | "pending" | "disconnected";
  detail: string;
  scope: string;
  children: React.ReactNode;
}) {
  return (
    <article className="lift sheen h-full rounded-xl border border-border bg-card p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="grid size-10 place-items-center rounded-lg border border-border bg-surface">
            <Icon className="size-4 text-primary" aria-hidden />
          </span>
          <div>
            <h2 className="text-sm font-semibold capitalize">{name}</h2>
            <p className="text-xs text-muted-foreground">{scope}</p>
          </div>
        </div>
        <StatusBadge
          tone={status === "connected" ? "positive" : status === "pending" ? "warning" : "neutral"}
        >
          {status}
        </StatusBadge>
      </div>
      <p className="mt-4 text-sm text-muted-foreground">{detail}</p>
      <div className="mt-5 flex items-center justify-between border-t border-border pt-4">
        {children}
      </div>
    </article>
  );
}
