import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/app-shell";
import { CategoryBarChart } from "@/components/charts";
import { DataTable, type Column } from "@/components/data-table";
import { PageHeader, Panel, QueryBoundary, inr, num, pct } from "@/components/primitives";
import { api } from "@/services/sarthi";
import type { Recommendation } from "@/lib/types";

export const Route = createFileRoute("/recommendations")({
  head: () => ({
    meta: [
      { title: "Recommendations — Sarthi" },
      {
        name: "description",
        content:
          "Recommendation surfaces, attach rates and revenue per placement across storefront, cart, checkout and email.",
      },
      { property: "og:title", content: "Recommendations — Sarthi" },
      {
        property: "og:description",
        content: "Attach rate and revenue for every recommendation surface.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: RecommendationsPage,
});

const columns: Column<Recommendation>[] = [
  {
    key: "product",
    header: "Placement",
    primary: true,
    cell: (r) => (
      <div>
        <p className="font-medium">{r.productName}</p>
        <p className="text-xs text-muted-foreground">
          {r.surface} · {r.segment}
        </p>
      </div>
    ),
  },
  {
    key: "impr",
    header: "Impressions",
    align: "right",
    mobileLabel: "Impressions",
    cell: (r) => <span className="tabular">{num(r.impressions)}</span>,
  },
  {
    key: "clicks",
    header: "Clicks",
    align: "right",
    mobileLabel: "Clicks",
    cell: (r) => <span className="tabular">{num(r.clicks)}</span>,
  },
  {
    key: "atc",
    header: "Add to cart",
    align: "right",
    mobileLabel: "Add to cart",
    cell: (r) => <span className="tabular">{num(r.addToCart)}</span>,
  },
  {
    key: "purch",
    header: "Purchases",
    align: "right",
    mobileLabel: "Purchases",
    cell: (r) => <span className="tabular">{num(r.purchases)}</span>,
  },
  {
    key: "attach",
    header: "Attach rate",
    align: "right",
    mobileLabel: "Attach rate",
    cell: (r) => <span className="tabular">{pct(r.attachRate)}</span>,
  },
  {
    key: "rev",
    header: "Revenue",
    align: "right",
    mobileLabel: "Revenue",
    cell: (r) => <span className="tabular text-positive">{inr(r.revenue)}</span>,
  },
];

function RecommendationsPage() {
  const query = useQuery({ queryKey: ["recommendations"], queryFn: api.listRecommendations });
  return (
    <AppShell>
      <PageHeader
        eyebrow="Growth"
        title="Recommendations"
        description="What Sarthi is showing, where it is showing it, and what each surface returns. Weak surfaces get retired automatically."
      />
      <QueryBoundary
        query={query}
        rows={4}
        isEmpty={(d) => d.length === 0}
        emptyTitle="No live recommendations"
      >
        {(rows) => (
          <>
            <Panel title="Revenue by surface">
              <CategoryBarChart
                label="Recommendation revenue by surface"
                data={rows.map((r) => ({ name: r.surface, value: r.revenue }))}
              />
            </Panel>
            <Panel title="Placement performance">
              <DataTable
                caption="Recommendation placements with attach rate and revenue"
                columns={columns}
                rows={rows}
              />
            </Panel>
          </>
        )}
      </QueryBoundary>
    </AppShell>
  );
}
