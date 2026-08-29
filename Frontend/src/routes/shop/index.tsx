import { useQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { toast } from "sonner";
import { ProductArt, ShopShell } from "@/components/shop-shell";
import {
  QueryBoundary,
  Stagger,
  StaggerItem,
  StatusBadge,
  inr,
  statusTone,
} from "@/components/primitives";
import { Button } from "@/components/ui/button";
import { cartStore } from "@/lib/shop-cart";
import { api } from "@/services/sarthi";

export const Route = createFileRoute("/shop/")({
  head: () => ({
    meta: [
      { title: "Kadam Athletics — trail running gear" },
      {
        name: "description",
        content:
          "Shop trail running shoes, apparel and accessories with personalised recommendations that explain themselves.",
      },
      { property: "og:title", content: "Kadam Athletics — trail running gear" },
      {
        property: "og:description",
        content: "Trail running gear with recommendations that explain why.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: ShopHome,
});

function ShopHome() {
  const query = useQuery({ queryKey: ["shop-products"], queryFn: api.listShopProducts });

  return (
    <ShopShell>
      <section className="grain rounded-2xl border border-border p-8 md:p-12">
        <p className="eyebrow">Autumn trail season</p>
        <h1 className="mt-4 max-w-2xl text-4xl font-semibold tracking-tight md:text-5xl">
          Gear that holds up on the long, ugly climbs.
        </h1>
        <p className="mt-4 max-w-xl text-sm leading-relaxed text-muted-foreground">
          Tell us how you train and we'll shortlist the kit — with the reason behind every
          suggestion, in plain language.
        </p>
        <Button asChild className="press mt-6">
          <Link to="/shop/search">Find my gear</Link>
        </Button>
      </section>

      <QueryBoundary
        query={query}
        rows={3}
        isEmpty={(d) => d.length === 0}
        emptyTitle="Catalog is empty"
      >
        {(products) => (
          <Stagger className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {products.map((p) => (
              <StaggerItem key={p.id}>
                <article className="lift flex h-full flex-col rounded-xl border border-border bg-card p-4">
                  <Link to="/shop/product/$id" params={{ id: p.id }} aria-label={p.name}>
                    <ProductArt hue={p.imageHue} />
                  </Link>
                  <div className="mt-4 flex flex-1 flex-col">
                    <div className="flex items-start justify-between gap-3">
                      <h2 className="text-sm font-semibold">
                        <Link to="/shop/product/$id" params={{ id: p.id }} className="link-sweep">
                          {p.name}
                        </Link>
                      </h2>
                      <StatusBadge tone={statusTone(p.availability)}>
                        {p.availability.replace(/_/g, " ")}
                      </StatusBadge>
                    </div>
                    <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                      {p.whyRecommended}
                    </p>
                    <div className="mt-4 flex items-center justify-between gap-3 pt-2">
                      <span className="tabular text-base font-semibold">{inr(p.price)}</span>
                      <Button
                        size="sm"
                        className="press"
                        disabled={p.availability === "out_of_stock"}
                        onClick={() => {
                          cartStore.add(p, true);
                          toast.success(`${p.name} added to cart`);
                        }}
                      >
                        Add to cart
                      </Button>
                    </div>
                  </div>
                </article>
              </StaggerItem>
            ))}
          </Stagger>
        )}
      </QueryBoundary>
    </ShopShell>
  );
}
