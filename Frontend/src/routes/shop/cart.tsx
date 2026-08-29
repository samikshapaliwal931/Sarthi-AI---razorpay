import { createFileRoute, Link } from "@tanstack/react-router";
import { Minus, Plus, Trash2 } from "lucide-react";
import { ShopShell } from "@/components/shop-shell";
import { EmptyState, inr } from "@/components/primitives";
import { Button } from "@/components/ui/button";
import { cartStore, cartTotal, useCart } from "@/lib/shop-cart";

export const Route = createFileRoute("/shop/cart")({
  head: () => ({
    meta: [
      { title: "Your cart — Kadam Athletics" },
      {
        name: "description",
        content:
          "Review your trail gear, adjust quantities and continue to a fast, secure checkout.",
      },
      { property: "og:title", content: "Your cart — Kadam Athletics" },
      { property: "og:description", content: "Review items and continue to checkout." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: CartPage,
});

function CartPage() {
  const lines = useCart();
  const total = cartTotal(lines);

  return (
    <ShopShell>
      <h1 className="text-3xl font-semibold tracking-tight">Your cart</h1>

      {lines.length === 0 ? (
        <div className="mt-8">
          <EmptyState
            title="Your cart is empty"
            description="Tell us how you train and we'll shortlist gear worth carrying."
            action={
              <Button asChild className="press">
                <Link to="/shop/search">Find my gear</Link>
              </Button>
            }
          />
        </div>
      ) : (
        <div className="mt-8 grid gap-8 lg:grid-cols-[1fr_20rem]">
          <ul className="divide-y divide-border rounded-xl border border-border bg-card">
            {lines.map((l) => (
              <li
                key={l.productId}
                className="flex flex-wrap items-center justify-between gap-4 p-5"
              >
                <div>
                  <p className="text-sm font-medium">{l.name}</p>
                  {l.viaSarthi ? (
                    <p className="mt-1 text-[11px] text-primary">Suggested for you</p>
                  ) : null}
                  <p className="tabular mt-1 text-xs text-muted-foreground">{inr(l.price)} each</p>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex items-center rounded-md border border-border">
                    <button
                      className="press p-2"
                      aria-label={`Decrease ${l.name}`}
                      onClick={() => cartStore.setQty(l.productId, l.qty - 1)}
                    >
                      <Minus className="size-3.5" aria-hidden />
                    </button>
                    <span className="tabular w-8 text-center text-sm">{l.qty}</span>
                    <button
                      className="press p-2"
                      aria-label={`Increase ${l.name}`}
                      onClick={() => cartStore.setQty(l.productId, l.qty + 1)}
                    >
                      <Plus className="size-3.5" aria-hidden />
                    </button>
                  </div>
                  <span className="tabular w-24 text-right text-sm font-semibold">
                    {inr(l.price * l.qty)}
                  </span>
                  <button
                    className="press text-muted-foreground hover:text-destructive"
                    aria-label={`Remove ${l.name}`}
                    onClick={() => cartStore.remove(l.productId)}
                  >
                    <Trash2 className="size-4" aria-hidden />
                  </button>
                </div>
              </li>
            ))}
          </ul>

          <aside className="h-fit rounded-xl border border-border bg-card p-5">
            <h2 className="text-sm font-semibold">Order summary</h2>
            <dl className="mt-4 space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Subtotal</dt>
                <dd className="tabular">{inr(total)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Shipping</dt>
                <dd className="tabular text-positive">Free</dd>
              </div>
              <div className="flex justify-between border-t border-border pt-3 text-base font-semibold">
                <dt>Total</dt>
                <dd className="tabular">{inr(total)}</dd>
              </div>
            </dl>
            <Button asChild className="press mt-5 w-full">
              <Link to="/shop/checkout">Checkout</Link>
            </Button>
          </aside>
        </div>
      )}
    </ShopShell>
  );
}
