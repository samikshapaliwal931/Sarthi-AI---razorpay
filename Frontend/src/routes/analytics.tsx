import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/app-shell";
import { CategoryBarChart, MiniLineChart, RevenueAreaChart } from "@/components/charts";
import { MetricCard, StatLine } from "@/components/metrics";
import { PageHeader, Panel, QueryBoundary, Stagger, inr, pct } from "@/components/primitives";
import { api } from "@/services/sarthi";

export const Route = createFileRoute("/analytics")({
  head: () => ({
    meta: [
      { title: "Revenue analytics — Sarthi" },
      {
        name: "description",
        content:
          "Attribution-grade analytics separating AI-driven revenue from baseline commerce performance.",
      },
      { property: "og:title", content: "Revenue analytics — Sarthi" },
      {
        property: "og:description",
        content: "Trend, attribution and conversion analytics for the revenue agent.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: AnalyticsPage,
});

function AnalyticsPage() {
  const query = useQuery({ queryKey: ["dashboard"], queryFn: api.getDashboard });
  return (
    <AppShell>
      <PageHeader
        eyebrow="Revenue"
        title="Revenue analytics"
        description="Baseline versus incremental. Sarthi only claims revenue it can reconcile against a holdout or a recovered failure."
      />
      <QueryBoundary query={query} rows={4}>
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
                label="AI-attributed"
                value={d.aiAttributedRevenue}
                format={(v) => inr(v)}
                delta={d.deltas["aiAttributedRevenue"]}
                hint="Revenue on orders where a Sarthi action was the last meaningful influence, net of holdout baseline."
              />
              <MetricCard
                label="Incremental"
                value={d.incrementalRevenue}
                format={(v) => inr(v)}
                delta={d.deltas["incrementalRevenue"]}
              />
              <MetricCard
                label="Average order value"
                value={d.aov}
                format={(v) => inr(v)}
                delta={d.deltas["aov"]}
              />
            </Stagger>

            <Panel title="Revenue trend" description="Total revenue against AI-attributed revenue">
              <RevenueAreaChart data={d.trend} />
            </Panel>

            <div className="grid gap-5 lg:grid-cols-2">
              <Panel title="Attribution mix">
                <CategoryBarChart
                  label="Revenue by attribution source"
                  data={d.attribution.map((a) => ({ name: a.label, value: a.revenue }))}
                />
              </Panel>
              <Panel title="Conversion trend">
                <MiniLineChart
                  data={d.trend}
                  dataKey="conversion"
                  label="Conversion rate over time"
                  height={240}
                />
              </Panel>
            </div>

            <Panel title="Quality of revenue">
              <dl>
                <StatLine
                  label="Conversion rate"
                  value={<span className="tabular">{pct(d.conversionRate)}</span>}
                />
                <StatLine
                  label="Recommendation acceptance"
                  value={<span className="tabular">{pct(d.acceptanceRate)}</span>}
                />
                <StatLine
                  label="Recovered revenue"
                  value={<span className="tabular text-positive">{inr(d.recoveredRevenue)}</span>}
                />
                <StatLine
                  label="Incremental share of AI revenue"
                  value={
                    <span className="tabular">
                      {pct(d.incrementalRevenue / d.aiAttributedRevenue)}
                    </span>
                  }
                />
              </dl>
            </Panel>
          </>
        )}
      </QueryBoundary>
    </AppShell>
  );
}
