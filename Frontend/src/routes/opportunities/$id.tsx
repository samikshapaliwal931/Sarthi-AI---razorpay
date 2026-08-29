import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import { AppShell } from "@/components/app-shell";
import { CategoryBarChart } from "@/components/charts";
import { StatLine } from "@/components/metrics";
import { EvidenceTimeline, PolicyChecklist, opportunityTypeLabel } from "@/components/opportunity";
import {
  ConfidenceMeter,
  EmptyState,
  Panel,
  ProcessingRow,
  QueryBoundary,
  StatusBadge,
  inr,
  num,
  shortDate,
  statusTone,
} from "@/components/primitives";
import { Button } from "@/components/ui/button";
import { api } from "@/services/sarthi";

export const Route = createFileRoute("/opportunities/$id")({
  head: () => ({
    meta: [
      { title: "Opportunity investigation — Sarthi" },
      {
        name: "description",
        content:
          "Full investigation view: evidence, affected products, expected impact, risk, policy constraints, approval and outcome.",
      },
      { property: "og:title", content: "Opportunity investigation — Sarthi" },
      {
        property: "og:description",
        content: "Why Sarthi found this, what it proposes, and what your policies allow.",
      },
    ],
  }),
  component: OpportunityDetail,
});

function OpportunityDetail() {
  const { id } = Route.useParams();
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["opportunity", id], queryFn: () => api.getOpportunity(id) });
  const products = useQuery({ queryKey: ["products"], queryFn: () => api.listProducts() });

  const decide = useMutation({
    mutationFn: (decision: "approve" | "reject") => api.decideOpportunity(id, decision),
    onSuccess: (res) => {
      toast.success(res.status === "approved" ? "Approved — queued for execution" : "Rejected", {
        description: "Recorded in the audit trail with a correlation ID.",
      });
      queryClient.invalidateQueries({ queryKey: ["opportunity", id] });
      queryClient.invalidateQueries({ queryKey: ["opportunities"] });
    },
    onError: () => toast.error("Decision could not be recorded"),
  });

  return (
    <AppShell>
      <Button asChild variant="ghost" size="sm" className="-ml-2 w-fit">
        <Link to="/opportunities">
          <ArrowLeft className="size-3.5" aria-hidden /> All opportunities
        </Link>
      </Button>

      <QueryBoundary query={query} rows={5}>
        {(o) => (
          <motion.div layoutId={`opp-${o.id}`} className="space-y-8">
            <header className="border-b border-border pb-6">
              <div className="flex flex-wrap items-center gap-2">
                <span className="eyebrow text-primary">{opportunityTypeLabel[o.type]}</span>
                <StatusBadge tone={statusTone(o.status)}>{o.status.replace(/_/g, " ")}</StatusBadge>
                <span className="text-xs text-muted-foreground">
                  Discovered {shortDate(o.discoveredAt)}
                </span>
              </div>
              <h1 className="mt-4 max-w-3xl text-3xl font-semibold tracking-tight md:text-4xl">
                {o.title}
              </h1>
              <p className="mt-4 max-w-2xl text-sm leading-relaxed text-muted-foreground">
                {o.summary}
              </p>
              <div className="mt-6 flex flex-wrap items-center gap-6">
                <ConfidenceMeter value={o.confidence} />
                <span className="tabular text-sm text-positive">
                  {inr(o.expectedRevenue)} expected
                </span>
                <span className="tabular text-sm text-muted-foreground">
                  {num(o.expectedOrders)} est. orders
                </span>
              </div>
            </header>

            <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
              <div className="space-y-6">
                <Panel title="Why Sarthi found this">
                  <p className="text-sm leading-relaxed text-muted-foreground">{o.rationale}</p>
                </Panel>

                <Panel
                  title="Supporting evidence"
                  description="Factual observations that produced the recommendation."
                >
                  <EvidenceTimeline evidence={o.evidence} />
                </Panel>

                <Panel title="Affected products">
                  <QueryBoundary query={products} rows={2}>
                    {(all) => (
                      <ul className="space-y-3">
                        {o.affectedProductIds.map((pid) => {
                          const p = all.find((x) => x.id === pid);
                          if (!p) return null;
                          return (
                            <li
                              key={pid}
                              className="flex items-center justify-between gap-4 border-b border-border/60 pb-3 last:border-0 last:pb-0"
                            >
                              <div>
                                <Link
                                  to="/products/$id"
                                  params={{ id: p.id }}
                                  className="text-sm font-medium hover:underline"
                                >
                                  {p.name}
                                </Link>
                                <p className="text-xs text-muted-foreground">
                                  {p.category} · {p.sku}
                                </p>
                              </div>
                              <div className="text-right">
                                <p className="tabular text-sm">{inr(p.price)}</p>
                                <p className="tabular text-xs text-muted-foreground">
                                  {num(p.inventory)} in stock
                                </p>
                              </div>
                            </li>
                          );
                        })}
                      </ul>
                    )}
                  </QueryBoundary>
                </Panel>

                <Panel title="Simulation" description="Modelled outcomes across scenarios.">
                  <CategoryBarChart
                    label="Simulated revenue by scenario"
                    height={210}
                    data={o.simulation.map((s) => ({ name: s.scenario, value: s.revenue }))}
                  />
                  <dl className="mt-4">
                    {o.simulation.map((s) => (
                      <StatLine
                        key={s.scenario}
                        label={s.scenario}
                        value={`${num(s.orders)} orders · ${inr(s.revenue)}`}
                      />
                    ))}
                  </dl>
                </Panel>

                <Panel title="Execution history">
                  {o.executionHistory.length === 0 ? (
                    <EmptyState
                      title="Not executed yet"
                      description="Once approved, every agent step appears here with its correlation ID."
                    />
                  ) : (
                    <ol className="space-y-4">
                      {o.executionHistory.map((a) => (
                        <li
                          key={a.id}
                          className="flex flex-wrap items-start gap-3 border-b border-border/60 pb-3.5 last:border-0 last:pb-0"
                        >
                          <span className="tabular w-24 shrink-0 text-xs text-muted-foreground">
                            {shortDate(a.at)}
                          </span>
                          <div className="min-w-0 flex-1">
                            <p className="text-sm">
                              <span className="text-primary">{a.agent}</span> · {a.action}
                            </p>
                            <p className="mt-1 text-xs text-muted-foreground">{a.detail}</p>
                            <p className="tabular mt-1 text-[11px] text-muted-foreground">
                              {a.correlationId}
                            </p>
                          </div>
                          <StatusBadge tone={statusTone(a.status)}>
                            {a.status.replace(/_/g, " ")}
                          </StatusBadge>
                        </li>
                      ))}
                    </ol>
                  )}
                </Panel>

                <Panel title="Outcome">
                  {o.outcome ? (
                    <dl>
                      <StatLine
                        label="Revenue generated"
                        value={<span className="text-positive">{inr(o.outcome.revenue)}</span>}
                      />
                      <StatLine label="Orders" value={num(o.outcome.orders)} />
                      <StatLine label="Incremental revenue" value={inr(o.outcome.incremental)} />
                      <StatLine
                        label="Note"
                        value={<span className="text-muted-foreground">{o.outcome.note}</span>}
                      />
                    </dl>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      Outcome measurement starts once the action executes. Attribution reconciles
                      daily against a holdout.
                    </p>
                  )}
                </Panel>
              </div>

              <aside className="space-y-6">
                <Panel title="Expected impact">
                  <dl>
                    <StatLine label="Additional orders" value={num(o.expectedOrders)} />
                    <StatLine
                      label="Additional revenue"
                      value={<span className="text-positive">{inr(o.expectedRevenue)}</span>}
                    />
                    <StatLine
                      label="80% interval"
                      value={`${inr(o.confidenceIntervalLow)} – ${inr(o.confidenceIntervalHigh)}`}
                    />
                    <StatLine label="Confidence" value={`${Math.round(o.confidence * 100)}%`} />
                    <StatLine
                      label="Historical evidence"
                      value={`${o.evidence.length} observations`}
                    />
                  </dl>
                </Panel>

                <Panel title="Customer segment">
                  <dl>
                    <StatLine label="Segment" value={o.segment} />
                    <StatLine label="Size" value={`${num(o.segmentSize)} customers`} />
                  </dl>
                </Panel>

                <Panel title="Risk">
                  <StatusBadge
                    tone={
                      o.risk === "low" ? "positive" : o.risk === "medium" ? "warning" : "danger"
                    }
                  >
                    {o.risk} risk
                  </StatusBadge>
                  <p className="mt-3 text-sm text-muted-foreground">{o.riskNotes}</p>
                </Panel>

                <Panel
                  title="Policy constraints"
                  description="Evaluated before anything can execute."
                >
                  <PolicyChecklist checks={o.policyChecks} />
                </Panel>

                <Panel title="Recommended action">
                  <p className="text-sm leading-relaxed">{o.recommendedAction}</p>
                </Panel>

                <Panel title="Approval">
                  {o.status === "blocked" ? (
                    <p className="text-sm text-destructive">
                      Blocked by policy. Approval is unavailable until the proposal is re-scoped
                      inside your limits.
                    </p>
                  ) : o.status === "approved" || o.status === "executed" ? (
                    <p className="text-sm text-positive">
                      Approved by merchant. Execution is under way or complete.
                    </p>
                  ) : (
                    <div className="space-y-3">
                      <div className="flex gap-2">
                        <Button
                          className="flex-1"
                          disabled={decide.isPending}
                          onClick={() => decide.mutate("approve")}
                        >
                          Approve
                        </Button>
                        <Button
                          variant="outline"
                          className="flex-1"
                          disabled={decide.isPending}
                          onClick={() => decide.mutate("reject")}
                        >
                          Reject
                        </Button>
                      </div>
                      {decide.isPending ? (
                        <ProcessingRow label="Recording decision and re-running policy checks…" />
                      ) : null}
                      {decide.isError ? (
                        <p role="alert" className="text-xs text-destructive">
                          The decision was not recorded and nothing executed. Try again.
                        </p>
                      ) : null}
                    </div>
                  )}
                </Panel>
              </aside>
            </div>
          </motion.div>
        )}
      </QueryBoundary>
    </AppShell>
  );
}
