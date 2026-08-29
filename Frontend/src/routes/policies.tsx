import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { toast } from "sonner";
import { AppShell } from "@/components/app-shell";
import { PageHeader, Panel, QueryBoundary, num } from "@/components/primitives";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { api } from "@/services/sarthi";
import type { Policy } from "@/lib/types";

export const Route = createFileRoute("/policies")({
  head: () => ({
    meta: [
      { title: "Policy centre — Sarthi" },
      {
        name: "description",
        content:
          "The limits Sarthi operates inside: discount ceilings, spend caps, rate limits, communication and payment permissions.",
      },
      { property: "og:title", content: "Policy centre — Sarthi" },
      {
        property: "og:description",
        content: "Set the hard limits your AI revenue agent may never cross.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: PoliciesPage,
});

const groupLabel: Record<Policy["group"], { title: string; description: string }> = {
  spend: {
    title: "Spend limits",
    description: "Hard ceilings on discounts and budgets Sarthi may propose or commit.",
  },
  approvals: {
    title: "Approvals & rate limits",
    description: "What always routes to you, and how fast the agent may act.",
  },
  communication: {
    title: "Customer communication",
    description: "Whether and how often Sarthi may contact your customers.",
  },
  payments: {
    title: "Payment permissions",
    description: "Sarthi never charges a customer unless you explicitly allow it.",
  },
  catalog: {
    title: "Catalog scope",
    description: "Which products and inventory levels are in scope for promotion.",
  },
};

function PoliciesPage() {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["policies"], queryFn: api.listPolicies });

  const update = useMutation({
    mutationFn: ({ policy, value }: { policy: Policy; value: number | boolean }) =>
      api.updatePolicy(policy, value),
    onSuccess: () => {
      toast.success("Policy updated", {
        description: "Applied to every future agent decision and recorded in the audit trail.",
      });
      queryClient.invalidateQueries({ queryKey: ["policies"] });
    },
    onError: () =>
      toast.error("Could not update the policy", {
        description: "The previous limit is still in force.",
      }),
  });

  return (
    <AppShell>
      <PageHeader
        eyebrow="Governance"
        title="Policy centre"
        description="These limits are evaluated before any action is proposed to you, not after. A blocked action is never executed and is always logged."
      />
      <QueryBoundary
        query={query}
        rows={6}
        isEmpty={(d) => d.length === 0}
        emptyTitle="No policies configured"
      >
        {(rows) => (
          <div className="space-y-5">
            {(Object.keys(groupLabel) as Policy["group"][]).map((group) => {
              const items = rows.filter((p) => p.group === group);
              if (items.length === 0) return null;
              const meta = groupLabel[group];
              return (
                <Panel key={group} title={meta.title} description={meta.description}>
                  <div className="divide-y divide-border">
                    {items.map((p) => (
                      <div
                        key={p.id}
                        className="flex flex-wrap items-center justify-between gap-5 py-4 first:pt-0 last:pb-0"
                      >
                        <div className="max-w-md">
                          <p className="text-sm font-medium">{p.label}</p>
                          <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                            {p.description}
                          </p>
                        </div>
                        <div className="flex min-w-52 items-center justify-end gap-4">
                          {p.kind === "toggle" ? (
                            <Switch
                              checked={Boolean(p.value)}
                              aria-label={p.label}
                              onCheckedChange={(v) => update.mutate({ policy: p, value: v })}
                            />
                          ) : p.kind === "slider" ? (
                            <>
                              <Slider
                                className="w-40"
                                aria-label={p.label}
                                min={p.min ?? 0}
                                max={p.max ?? 100}
                                step={p.step ?? 1}
                                defaultValue={[Number(p.value)]}
                                onValueCommit={(v) =>
                                  update.mutate({ policy: p, value: v[0] ?? Number(p.value) })
                                }
                              />
                              <span className="tabular w-20 text-right text-sm">
                                {num(Number(p.value))}
                                {p.unit ?? ""}
                              </span>
                            </>
                          ) : (
                            <span className="tabular text-sm">
                              {p.unit === "₹" ? "₹" : ""}
                              {num(Number(p.value))}
                              {p.unit && p.unit !== "₹" ? p.unit : ""}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </Panel>
              );
            })}
          </div>
        )}
      </QueryBoundary>
    </AppShell>
  );
}
