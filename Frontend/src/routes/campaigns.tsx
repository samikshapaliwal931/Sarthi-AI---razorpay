import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";
import { AppShell } from "@/components/app-shell";
import {
  PageHeader,
  Panel,
  QueryBoundary,
  Stagger,
  StaggerItem,
  StatusBadge,
  inr,
  num,
  shortDate,
  statusTone,
} from "@/components/primitives";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/services/sarthi";

export const Route = createFileRoute("/campaigns")({
  head: () => ({
    meta: [
      { title: "Campaigns — Sarthi" },
      {
        name: "description",
        content: "Agent-drafted campaigns with budget pacing, ROAS and merchant approval gates.",
      },
      { property: "og:title", content: "Campaigns — Sarthi" },
      {
        property: "og:description",
        content: "Campaign pacing, spend limits and approvals in one governed view.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: CampaignsPage,
});

const CAMPAIGN_TYPES = ["discount", "recovery", "cross_sell", "upsell", "loyalty"];

function CampaignsPage() {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["campaigns"], queryFn: api.listCampaigns });

  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [campaignType, setCampaignType] = useState(CAMPAIGN_TYPES[0]!);
  const [budget, setBudget] = useState("5000");

  const create = useMutation({
    mutationFn: () => api.createCampaign({ name, campaignType, budget: Number(budget) || 0 }),
    onSuccess: () => {
      toast.success("Campaign drafted", {
        description: "It's saved — approve it to run through the policy gate.",
      });
      queryClient.invalidateQueries({ queryKey: ["campaigns"] });
      setShowCreate(false);
      setName("");
      setBudget("5000");
    },
    onError: (err: any) => {
      toast.error("Couldn't create campaign", { description: err?.message ?? "Try again." });
    },
  });

  const decide = useMutation({
    mutationFn: ({ id, decision }: { id: string; decision: "approve" | "reject" }) =>
      api.decideCampaign(id, decision),
    onSuccess: (_data, vars) => {
      if (vars.decision === "approve") {
        toast.success("Approved", {
          description: "Passed the policy gate. See the audit trail for the decision.",
        });
      } else {
        toast("Rejected", {
          description: "Nothing was spent. The rejection is in the audit trail.",
        });
      }
      queryClient.invalidateQueries({ queryKey: ["campaigns"] });
    },
    onError: (err: any) => {
      toast.error("Blocked by policy", {
        description: err?.message ?? "This campaign didn't pass the policy gate.",
      });
      queryClient.invalidateQueries({ queryKey: ["campaigns"] });
    },
  });

  return (
    <AppShell>
      <PageHeader
        eyebrow="Growth"
        title="Campaigns"
        description="Sarthi drafts the campaign, sizes the audience and forecasts the return. Nothing spends money until you approve it — and approval still passes through the policy gate."
        actions={<Button onClick={() => setShowCreate(true)}>New campaign</Button>}
      />
      <QueryBoundary
        query={query}
        rows={4}
        isEmpty={(d) => d.length === 0}
        emptyTitle="No campaigns yet"
      >
        {(rows) => (
          <Stagger className="grid gap-5 lg:grid-cols-2">
            {rows.map((c) => {
              const roas = c.spend > 0 ? c.revenue / c.spend : 0;
              const pacing =
                c.budget > 0 ? Math.min(100, Math.round((c.spend / c.budget) * 100)) : 0;
              const pending = decide.isPending && decide.variables?.id === c.id;
              return (
                <StaggerItem key={c.id}>
                  <article className="lift sheen h-full rounded-xl border border-border bg-card p-5">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="eyebrow text-primary">{c.channel}</span>
                      <StatusBadge tone={statusTone(c.status)}>
                        {c.status.replace(/_/g, " ")}
                      </StatusBadge>
                    </div>
                    <h2 className="mt-3 text-lg font-semibold tracking-tight">{c.name}</h2>
                    <p className="mt-1.5 text-sm text-muted-foreground">{c.objective}</p>

                    <dl className="mt-5 grid grid-cols-3 gap-4 border-t border-border pt-4 text-sm">
                      <div>
                        <dt className="eyebrow">Audience</dt>
                        <dd className="tabular mt-1.5">{num(c.audience)}</dd>
                      </div>
                      <div>
                        <dt className="eyebrow">Revenue</dt>
                        <dd className="tabular mt-1.5 text-positive">{inr(c.revenue)}</dd>
                      </div>
                      <div>
                        <dt className="eyebrow">ROAS</dt>
                        <dd className="tabular mt-1.5">{roas ? `${roas.toFixed(1)}x` : "—"}</dd>
                      </div>
                    </dl>

                    <div className="mt-5">
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>Budget pacing</span>
                        <span className="tabular">
                          {inr(c.spend)} / {inr(c.budget)}
                        </span>
                      </div>
                      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full rounded-full bg-primary transition-[width] duration-1000"
                          style={{ width: `${pacing}%` }}
                        />
                      </div>
                    </div>

                    <div className="mt-5 flex flex-wrap items-center justify-between gap-3">
                      <p className="text-xs text-muted-foreground">
                        Starts {shortDate(c.startedAt)}
                      </p>
                      {c.status === "draft" || c.status === "awaiting_approval" ? (
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            className="press"
                            disabled={pending}
                            onClick={() => decide.mutate({ id: c.id, decision: "approve" })}
                          >
                            {pending && decide.variables?.decision === "approve"
                              ? "Approving…"
                              : "Approve launch"}
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="press"
                            disabled={pending}
                            onClick={() => decide.mutate({ id: c.id, decision: "reject" })}
                          >
                            Reject
                          </Button>
                        </div>
                      ) : null}
                    </div>
                  </article>
                </StaggerItem>
              );
            })}
          </Stagger>
        )}
      </QueryBoundary>

      {showCreate ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
          <div className="w-full max-w-md rounded-lg border border-border bg-card p-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold">New campaign</h3>
              <Button variant="ghost" size="sm" onClick={() => setShowCreate(false)}>
                Close
              </Button>
            </div>
            <p className="mb-4 text-sm text-muted-foreground">
              Drafts as <code className="text-xs">draft</code>. Approving it runs the budget through
              your policy limits — an over-budget campaign is blocked, not silently launched.
            </p>
            <form
              className="space-y-4"
              onSubmit={(e) => {
                e.preventDefault();
                create.mutate();
              }}
            >
              <div className="space-y-2">
                <Label htmlFor="camp_name">Name</Label>
                <Input
                  id="camp_name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Autumn trail season"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="camp_type">Type</Label>
                <select
                  id="camp_type"
                  value={campaignType}
                  onChange={(e) => setCampaignType(e.target.value)}
                  className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-xs"
                >
                  {CAMPAIGN_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t.replace(/_/g, " ")}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="camp_budget">Budget (₹)</Label>
                <Input
                  id="camp_budget"
                  type="number"
                  min={0}
                  value={budget}
                  onChange={(e) => setBudget(e.target.value)}
                  required
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="ghost" onClick={() => setShowCreate(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={create.isPending}>
                  {create.isPending ? "Creating…" : "Create draft"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </AppShell>
  );
}
