import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";
import { AppShell } from "@/components/app-shell";
import { OpportunityCard, opportunityTypeLabel } from "@/components/opportunity";
import { PageHeader, Panel, QueryBoundary, Stagger, inr } from "@/components/primitives";
import { Button } from "@/components/ui/button";
import { api } from "@/services/sarthi";
import type { OpportunityStatus } from "@/lib/types";

export const Route = createFileRoute("/opportunities/")({
  head: () => ({
    meta: [
      { title: "Revenue opportunities — Sarthi" },
      {
        name: "description",
        content:
          "Every bounded revenue action Sarthi proposes, with expected impact, confidence, supporting evidence and policy status.",
      },
      { property: "og:title", content: "Revenue opportunities — Sarthi" },
      {
        property: "og:description",
        content: "Review, approve or reject AI-discovered revenue opportunities.",
      },
    ],
  }),
  component: OpportunitiesPage,
});

const filters: { key: OpportunityStatus | "all"; label: string }[] = [
  { key: "all", label: "All" },
  { key: "new", label: "New" },
  { key: "under_review", label: "Under review" },
  { key: "approved", label: "Approved" },
  { key: "executed", label: "Executed" },
  { key: "blocked", label: "Blocked" },
];

function OpportunitiesPage() {
  const [filter, setFilter] = useState<OpportunityStatus | "all">("all");
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["opportunities"], queryFn: api.listOpportunities });

  const decide = useMutation({
    mutationFn: ({ id, decision }: { id: string; decision: "approve" | "reject" }) =>
      api.decideOpportunity(id, decision),
    onSuccess: (res) => {
      toast.success(res.status === "approved" ? "Opportunity approved" : "Opportunity rejected", {
        description: "Routed to the policy engine and recorded in the audit trail.",
      });
      queryClient.invalidateQueries({ queryKey: ["opportunities"] });
      queryClient.invalidateQueries({ queryKey: ["opportunity", res.id] });
    },
    onError: () =>
      toast.error("Decision failed", { description: "No action was executed. Try again." }),
  });

  return (
    <AppShell>
      <PageHeader
        eyebrow="Discover → propose"
        title="Revenue opportunities"
        description="Each opportunity is a bounded action with an expected impact, a confidence interval, the evidence that produced it, and the policies that allow or block it."
      />

      <QueryBoundary
        query={query}
        rows={4}
        isEmpty={(d) => d.length === 0}
        emptyTitle="No opportunities yet"
        emptyDescription="Sarthi is still analysing your catalog and order history. New findings appear here automatically."
      >
        {(list) => {
          const filtered = filter === "all" ? list : list.filter((o) => o.status === filter);
          const pipeline = list
            .filter((o) => o.status !== "blocked" && o.status !== "rejected")
            .reduce((sum, o) => sum + o.expectedRevenue, 0);

          return (
            <>
              <Panel className="bg-surface">
                <div className="flex flex-wrap items-center justify-between gap-6">
                  <div>
                    <p className="eyebrow">Open pipeline</p>
                    <p className="tabular mt-2 text-2xl font-semibold text-positive">
                      {inr(pipeline)}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Expected revenue across {list.length} live findings ·{" "}
                      {opportunityTypeLabel[list[0]!.type]} leads the queue
                    </p>
                  </div>
                  <div
                    className="flex flex-wrap gap-2"
                    role="group"
                    aria-label="Filter opportunities by status"
                  >
                    {filters.map((f) => (
                      <Button
                        key={f.key}
                        size="sm"
                        variant={filter === f.key ? "secondary" : "ghost"}
                        aria-pressed={filter === f.key}
                        onClick={() => setFilter(f.key)}
                      >
                        {f.label}
                      </Button>
                    ))}
                  </div>
                </div>
              </Panel>

              {filtered.length === 0 ? (
                <Panel>
                  <p className="py-8 text-center text-sm text-muted-foreground">
                    No opportunities with this status right now.
                  </p>
                </Panel>
              ) : (
                <Stagger className="grid gap-5 xl:grid-cols-2">
                  {filtered.map((o) => (
                    <OpportunityCard
                      key={o.id}
                      opportunity={o}
                      pending={decide.isPending}
                      onDecide={(id, decision) => decide.mutate({ id, decision })}
                    />
                  ))}
                </Stagger>
              )}
            </>
          );
        }}
      </QueryBoundary>
    </AppShell>
  );
}
