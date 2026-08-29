import { useQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { OpportunityCard } from "@/components/opportunity";
import { StatLine } from "@/components/metrics";
import {
  PageHeader,
  Panel,
  QueryBoundary,
  Reveal,
  StatusBadge,
  inr,
  num,
  pct,
  statusTone,
} from "@/components/primitives";
import { Button } from "@/components/ui/button";
import { api } from "@/services/sarthi";

export const Route = createFileRoute("/products/$id")({
  head: () => ({
    meta: [
      { title: "Product detail — Sarthi" },
      {
        name: "description",
        content:
          "Product performance, inventory posture and the revenue actions Sarthi has proposed for it.",
      },
      { property: "og:title", content: "Product detail — Sarthi" },
      {
        property: "og:description",
        content: "Per-product AI scoring and proposed revenue actions.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: ProductDetail,
});

function ProductDetail() {
  const { id } = Route.useParams();
  const query = useQuery({ queryKey: ["product", id], queryFn: () => api.getProduct(id) });
  const opportunities = useQuery({ queryKey: ["opportunities"], queryFn: api.listOpportunities });

  return (
    <AppShell>
      <Button asChild variant="ghost" size="sm" className="press -ml-2 w-fit">
        <Link to="/products">
          <ArrowLeft className="size-4" aria-hidden /> Back to catalog
        </Link>
      </Button>

      <QueryBoundary query={query} rows={3}>
        {(p) => (
          <>
            <PageHeader
              eyebrow={p.category}
              title={p.name}
              description={`SKU ${p.sku} · ${num(p.unitsSold30d)} units sold in the last 30 days`}
              actions={
                <StatusBadge tone={statusTone(p.status)}>{p.status.replace(/_/g, " ")}</StatusBadge>
              }
            />

            <div className="grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
              <Reveal>
                <Panel title="Performance">
                  <dl>
                    <StatLine
                      label="Price"
                      value={<span className="tabular">{inr(p.price)}</span>}
                    />
                    {p.compareAtPrice ? (
                      <StatLine
                        label="Compare at"
                        value={
                          <span className="tabular text-muted-foreground">
                            {inr(p.compareAtPrice)}
                          </span>
                        }
                      />
                    ) : null}
                    <StatLine
                      label="Inventory on hand"
                      value={<span className="tabular">{num(p.inventory)}</span>}
                    />
                    <StatLine
                      label="Conversion rate"
                      value={<span className="tabular">{pct(p.conversionRate)}</span>}
                    />
                    <StatLine
                      label="Contribution to AOV"
                      value={<span className="tabular">{pct(p.aovContribution)}</span>}
                    />
                    <StatLine
                      label="Customer rating"
                      value={<span className="tabular">{p.rating.toFixed(1)} / 5</span>}
                    />
                  </dl>
                </Panel>
              </Reveal>

              <Reveal delay={0.06}>
                <Panel
                  title="Sarthi score"
                  description="How much headroom the agent sees on this product"
                >
                  <div className="flex items-end gap-4">
                    <p className="tabular text-5xl font-semibold tracking-tight">{p.aiScore}</p>
                    <p className="pb-2 text-sm text-muted-foreground">/ 100 revenue headroom</p>
                  </div>
                  <div className="mt-5 h-2 overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-primary transition-[width] duration-1000"
                      style={{ width: `${p.aiScore}%` }}
                    />
                  </div>
                  <p className="mt-5 text-sm leading-relaxed text-muted-foreground">
                    {p.crossSellOpportunities} open cross-sell paths detected from co-purchase
                    behaviour in the last 30 days.
                  </p>
                </Panel>
              </Reveal>
            </div>

            <QueryBoundary query={opportunities} rows={2}>
              {(list) => {
                const linked = list.filter((o) => o.affectedProductIds.includes(p.id));
                return linked.length === 0 ? (
                  <Panel title="Proposed actions">
                    <p className="py-8 text-center text-sm text-muted-foreground">
                      No open opportunities reference this product right now.
                    </p>
                  </Panel>
                ) : (
                  <div className="grid gap-5 xl:grid-cols-2">
                    {linked.map((o) => (
                      <OpportunityCard key={o.id} opportunity={o} />
                    ))}
                  </div>
                );
              }}
            </QueryBoundary>
          </>
        )}
      </QueryBoundary>
    </AppShell>
  );
}
