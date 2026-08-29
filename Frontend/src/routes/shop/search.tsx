import { useMutation } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { ProductArt, ShopShell } from "@/components/shop-shell";
import { ErrorState, ProcessingRow, inr } from "@/components/primitives";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cartStore } from "@/lib/shop-cart";
import { api } from "@/services/sarthi";

export const Route = createFileRoute("/shop/search")({
  head: () => ({
    meta: [
      { title: "Find your gear — Kadam Athletics" },
      {
        name: "description",
        content:
          "Describe how you train and get a shortlist of trail gear with the reasoning behind each pick.",
      },
      { property: "og:title", content: "Find your gear — Kadam Athletics" },
      {
        property: "og:description",
        content: "Conversational product discovery with explained recommendations.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: ShopSearch,
});

const examples = [
  "cushioned trail shoes under ₹8,000",
  "socks for long runs",
  "lightweight rain jacket",
];

function ShopSearch() {
  const [q, setQ] = useState("");
  const search = useMutation({ mutationFn: (query: string) => api.searchCatalog(query) });

  return (
    <ShopShell>
      <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">
        What are you training for?
      </h1>
      <p className="mt-3 max-w-xl text-sm leading-relaxed text-muted-foreground">
        Describe it the way you'd tell a shop assistant. You'll get a short, honest shortlist — not
        200 results.
      </p>

      <form
        className="mt-6 flex flex-col gap-3 sm:flex-row"
        onSubmit={(e) => {
          e.preventDefault();
          if (q.trim()) search.mutate(q.trim());
        }}
      >
        <Input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="e.g. muddy 20km trail runs, wide feet"
          aria-label="Describe what you need"
        />
        <Button type="submit" className="press" disabled={search.isPending || !q.trim()}>
          <Sparkles className="size-4" aria-hidden /> Find gear
        </Button>
      </form>

      <div className="mt-4 flex flex-wrap gap-2">
        {examples.map((e) => (
          <button
            key={e}
            type="button"
            className="rounded-full border border-border px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
            onClick={() => {
              setQ(e);
              search.mutate(e);
            }}
          >
            {e}
          </button>
        ))}
      </div>

      {search.isPending ? (
        <div className="mt-8">
          <ProcessingRow label="Matching your description against the catalog" />
        </div>
      ) : null}
      {search.isError ? (
        <div className="mt-8">
          <ErrorState message="Search is unavailable right now." onRetry={() => search.mutate(q)} />
        </div>
      ) : null}

      {search.data && !search.isPending ? (
        <section className="mt-10">
          <motion.p
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
            className="rounded-xl border border-primary/30 bg-primary/5 p-5 text-sm"
          >
            {search.data.reply}
          </motion.p>

          <div className="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {search.data.products.map((p, i) => (
              <motion.article
                key={p.id}
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: i * 0.06, ease: [0.22, 1, 0.36, 1] }}
                className="lift flex flex-col rounded-xl border border-border bg-card p-4"
              >
                <Link to="/shop/product/$id" params={{ id: p.id }} aria-label={p.name}>
                  <ProductArt hue={p.imageHue} />
                </Link>
                <h2 className="mt-3 text-sm font-semibold">{p.name}</h2>
                <p className="mt-2 flex-1 text-xs leading-relaxed text-muted-foreground">
                  {p.whyRecommended}
                </p>
                <div className="mt-4 flex items-center justify-between">
                  <span className="tabular text-sm font-semibold">{inr(p.price)}</span>
                  <Button
                    size="sm"
                    className="press"
                    disabled={p.availability === "out_of_stock"}
                    onClick={() => {
                      cartStore.add(p, true);
                      toast.success(`${p.name} added to cart`);
                    }}
                  >
                    Add
                  </Button>
                </div>
              </motion.article>
            ))}
          </div>
        </section>
      ) : null}
    </ShopShell>
  );
}
