import { useQuery } from "@tanstack/react-query";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { Star } from "lucide-react";
import { toast } from "sonner";
import { ProductArt, ShopShell } from "@/components/shop-shell";
import { QueryBoundary, StatusBadge, inr, statusTone } from "@/components/primitives";
import { Button } from "@/components/ui/button";
import { cartStore } from "@/lib/shop-cart";
import { api } from "@/services/sarthi";

export const Route = createFileRoute("/shop/product/$id")({
  head: () => ({
    meta: [
      { title: "Product details — Kadam Athletics" },
      {
        name: "description",
        content:
          "Product detail with pricing, availability and an explained recommendation of what pairs with it.",
      },
      { property: "og:title", content: "Product details — Kadam Athletics" },
      {
        property: "og:description",
        content: "Pricing, availability and explained pairing suggestions.",
      },
      { property: "og:type", content: "product" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: ShopProductPage,
});

function ShopProductPage() {
  const { id } = Route.useParams();
  const navigate = useNavigate();
  const query = useQuery({ queryKey: ["shop-product", id], queryFn: () => api.getShopProduct(id) });
  const related = useQuery({ queryKey: ["shop-products"], queryFn: api.listShopProducts });

  return (
    <ShopShell>
      <QueryBoundary query={query} rows={2}>
        {(p) => (
          <>
            <div className="grid gap-10 lg:grid-cols-2">
              <ProductArt hue={p.imageHue} className="aspect-square w-full rounded-2xl" />
              <div>
                <p className="eyebrow">{p.category}</p>
                <h1 className="mt-3 text-3xl font-semibold tracking-tight md:text-4xl">{p.name}</h1>
                <div className="mt-4 flex flex-wrap items-center gap-3">
                  <span className="tabular text-2xl font-semibold">{inr(p.price)}</span>
                  {p.compareAtPrice ? (
                    <span className="tabular text-sm text-muted-foreground line-through">
                      {inr(p.compareAtPrice)}
                    </span>
                  ) : null}
                  <StatusBadge tone={statusTone(p.availability)}>
                    {p.availability.replace(/_/g, " ")}
                  </StatusBadge>
                </div>
                <p className="mt-3 flex items-center gap-1.5 text-sm text-muted-foreground">
                  <Star className="size-3.5 fill-current text-warning" aria-hidden />
                  <span className="tabular">{p.rating.toFixed(1)}</span> · SKU {p.sku}
                </p>

                <div className="mt-6 rounded-xl border border-primary/30 bg-primary/5 p-5">
                  <p className="eyebrow text-primary">Why this is suggested</p>
                  <p className="mt-2 text-sm leading-relaxed">{p.whyRecommended}</p>
                </div>

                <div className="mt-6 flex flex-wrap gap-3">
                  <Button
                    className="press"
                    disabled={p.availability === "out_of_stock"}
                    onClick={() => {
                      cartStore.add(p, true);
                      toast.success(`${p.name} added to cart`);
                    }}
                  >
                    Add to cart
                  </Button>
                  <Button
                    variant="outline"
                    className="press"
                    disabled={p.availability === "out_of_stock"}
                    onClick={() => {
                      cartStore.add(p, true);
                      navigate({ to: "/shop/cart" });
                    }}
                  >
                    Buy now
                  </Button>
                </div>
              </div>
            </div>

            {related.data ? (
              <section className="mt-14">
                <h2 className="text-lg font-semibold tracking-tight">Pairs well with</h2>
                <div className="mt-5 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                  {related.data
                    .filter((r) => r.id !== p.id)
                    .slice(0, 3)
                    .map((r) => (
                      <article
                        key={r.id}
                        className="lift rounded-xl border border-border bg-card p-4"
                      >
                        <Link to="/shop/product/$id" params={{ id: r.id }} aria-label={r.name}>
                          <ProductArt hue={r.imageHue} />
                        </Link>
                        <h3 className="mt-3 text-sm font-semibold">{r.name}</h3>
                        <p className="mt-2 text-xs text-muted-foreground">{r.whyRecommended}</p>
                        <p className="tabular mt-3 text-sm font-semibold">{inr(r.price)}</p>
                      </article>
                    ))}
                </div>
              </section>
            ) : null}
          </>
        )}
      </QueryBoundary>
    </ShopShell>
  );
}
