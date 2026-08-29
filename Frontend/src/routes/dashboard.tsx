import { useQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowUpRight } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { CategoryBarChart, RevenueAreaChart } from "@/components/charts";
import { MetricCard } from "@/components/metrics";
import {
  EmptyState,
  PageHeader,
  Panel,
  QueryBoundary,
  Stagger,
  StatusBadge,
  inr,
  pct,
  shortDate,
  statusTone,
} from "@/components/primitives";
import { Button } from "@/components/ui/button";
import { api } from "@/services/sarthi";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Revenue dashboard — Sarthi" },
      {
        name: "description",
        content:
          "Total, AI-attributed, recovered and incremental revenue with AI impact breakdown and live agent activity.",
      },
      { property: "og:title", content: "Revenue dashboard — Sarthi" },
      {
        property: "og:description",
        content: "See exactly how much revenue your AI agent influenced this period.",
      },
    ],
  }),
  component: Dashboard,
});

function Dashboard() {
  const dashboard = useQuery({ queryKey: ["dashboard"], queryFn: api.getDashboard });
  const opportunities = useQuery({ queryKey: ["opportunities"], queryFn: api.listOpportunities });
  const activity = useQuery({ queryKey: ["agent-activity"], queryFn: api.listAgentActivity });

  return (
    <AppShell>
      <PageHeader
        eyebrow="Revenue overview"
        title="AI Revenue Overview"
        description="Everything Sarthi discovered, proposed and executed for Kadam Athletics in the last 30 days."
        actions={
          <Button asChild size="sm">
            <Link to="/opportunities">Review opportunities</Link>
          </Button>
        }
      />

      <QueryBoundary query={dashboard} rows={3}>
        {(d) => (
          <>
            <Stagger className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <MetricCard
                label="Total revenue"
                value={d.totalRevenue}
                format={(v) => inr(v)}
                delta={d.deltas["totalRevenue"]}
              />
              <MetricCard
                label="AI-attributed revenue"
                value={d.aiAttributedRevenue}
                format={(v) => inr(v)}
                delta={d.deltas["aiAttributedRevenue"]}
                hint="Revenue from transactions influenced by a Sarthi recommendation, a recovery workflow, or an approved campaign — measured against a holdout, not claimed on every order."
              />
              <MetricCard
                label="Recovered revenue"
                value={d.recoveredRevenue}
                format={(v) => inr(v)}
                delta={d.deltas["recoveredRevenue"]}
                hint="Revenue from carts and payments that had already failed or been abandoned before Sarthi intervened."
              />
              <MetricCard label="Average order value" value={d.aov} format={(v) => inr(v)} />
              <MetricCard
                label="Conversion rate"
                value={d.conversionRate}
                format={(v) => v.toFixed(2)}
                suffix="%"
              />
              <MetricCard
                label="Recommendation CTR"
                value={d.acceptanceRate * 100}
                format={(v) => `${Math.round(v)}`}
                suffix="%"
                hint="Click-through rate on Sarthi's on-site recommendations."
              />
              <MetricCard
                label="Open opportunities"
                value={
                  opportunities.data?.filter(
                    (o) => o.status === "new" || o.status === "under_review",
                  ).length ?? 0
                }
              />
            </Stagger>

            <div className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
              <Panel
                title="Revenue trend"
                description="Total revenue against AI-attributed revenue over time."
              >
                {d.trend.length > 0 ? (
                  <RevenueAreaChart data={d.trend} />
                ) : (
                  <EmptyState
                    title="No trend history yet"
                    description="Sarthi doesn't yet have a time-series analytics endpoint — this will populate once historical revenue snapshots are available. The current-period totals above are real."
                  />
                )}
              </Panel>
              <Panel
                title="AI impact breakdown"
                description="Where AI-attributed revenue came from."
              >
                {d.attribution.length > 0 ? (
                  <>
                    <CategoryBarChart
                      label="AI attributed revenue by source"
                      height={200}
                      data={d.attribution.map((a) => ({
                        name: a.label.split(" ")[0]!,
                        value: a.revenue,
                      }))}
                    />
                    <dl className="mt-5 space-y-3">
                      {d.attribution.map((a) => (
                        <div
                          key={a.source}
                          className="flex items-baseline justify-between gap-4 border-b border-border/60 pb-2.5 last:border-0"
                        >
                          <dt className="text-sm">{a.label}</dt>
                          <dd className="flex items-baseline gap-3">
                            <span className="tabular text-sm font-medium">{inr(a.revenue)}</span>
                            <span
                              className={`tabular text-xs ${a.deltaPct >= 0 ? "text-positive" : "text-destructive"}`}
                            >
                              {a.deltaPct >= 0 ? "+" : ""}
                              {a.deltaPct.toFixed(1)}%
                            </span>
                          </dd>
                        </div>
                      ))}
                    </dl>
                  </>
                ) : (
                  <EmptyState
                    title="No source breakdown yet"
                    description="A per-source attribution breakdown isn't exposed by the backend yet. AI-attributed revenue total is shown above."
                  />
                )}
              </Panel>
            </div>
          </>
        )}
      </QueryBoundary>

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel
          title="Top opportunities"
          description="Highest expected revenue awaiting your decision."
          actions={
            <Button asChild size="sm" variant="ghost">
              <Link to="/opportunities">
                All <ArrowUpRight className="size-3.5" aria-hidden />
              </Link>
            </Button>
          }
        >
          <QueryBoundary query={opportunities} rows={3} isEmpty={(d) => d.length === 0}>
            {(list) => (
              <ul className="space-y-4">
                {list.slice(0, 3).map((o) => (
                  <li key={o.id} className="border-b border-border/60 pb-4 last:border-0 last:pb-0">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <Link
                        to="/opportunities/$id"
                        params={{ id: o.id }}
                        className="text-sm font-medium hover:underline"
                      >
                        {o.title}
                      </Link>
                      <StatusBadge tone={statusTone(o.status)}>
                        {o.status.replace(/_/g, " ")}
                      </StatusBadge>
                    </div>
                    <p className="mt-1.5 text-xs text-muted-foreground">
                      <span className="tabular text-positive">{inr(o.expectedRevenue)}</span>{" "}
                      expected · <span className="tabular">{pct(o.confidence, 0)}</span> confidence
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </QueryBoundary>
        </Panel>

        <Panel
          title="Agent activity"
          description="What Sarthi has been doing."
          actions={
            <Button asChild size="sm" variant="ghost">
              <Link to="/agent-activity">
                Timeline <ArrowUpRight className="size-3.5" aria-hidden />
              </Link>
            </Button>
          }
        >
          <QueryBoundary query={activity} rows={3} isEmpty={(d) => d.length === 0}>
            {(list) => (
              <ul className="space-y-4">
                {list.slice(0, 5).map((a) => (
                  <li
                    key={a.id}
                    className="flex gap-3 border-b border-border/60 pb-3.5 last:border-0 last:pb-0"
                  >
                    <span className="tabular w-24 shrink-0 text-xs text-muted-foreground">
                      {shortDate(a.at)}
                    </span>
                    <div className="min-w-0">
                      <p className="text-sm">
                        <span className="text-primary">{a.agent}</span> · {a.action}
                      </p>
                      <p className="mt-1 text-xs text-muted-foreground">{a.detail}</p>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </QueryBoundary>
        </Panel>
      </div>
    </AppShell>
  );
}
