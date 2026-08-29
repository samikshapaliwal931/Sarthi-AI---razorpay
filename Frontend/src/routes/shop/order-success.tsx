import { createFileRoute, Link } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { CheckCircle2 } from "lucide-react";
import { ShopShell } from "@/components/shop-shell";
import { EmptyState, inr } from "@/components/primitives";
import { Button } from "@/components/ui/button";
import { cartStore } from "@/lib/shop-cart";

export const Route = createFileRoute("/shop/order-success")({
  head: () => ({
    meta: [
      { title: "Order confirmed — Kadam Athletics" },
      {
        name: "description",
        content:
          "Your order is confirmed. Track delivery and see what pairs well with what you just bought.",
      },
      { property: "og:title", content: "Order confirmed — Kadam Athletics" },
      { property: "og:description", content: "Order confirmation and delivery details." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: OrderSuccessPage,
});

function OrderSuccessPage() {
  const order = cartStore.getLastOrder();

  if (!order) {
    return (
      <ShopShell>
        <EmptyState
          title="No recent order"
          description="Once you complete a purchase, your confirmation appears here."
          action={
            <Button asChild className="press">
              <Link to="/shop">Browse the store</Link>
            </Button>
          }
        />
      </ShopShell>
    );
  }

  return (
    <ShopShell>
      <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
        className="mx-auto max-w-xl rounded-2xl border border-border bg-card p-8 text-center"
      >
        <span className="pulse-ring mx-auto grid size-12 place-items-center rounded-full bg-positive/10">
          <CheckCircle2 className="size-6 text-positive" aria-hidden />
        </span>
        <h1 className="mt-5 text-2xl font-semibold tracking-tight">Order confirmed</h1>
        <p className="tabular mt-2 text-sm text-muted-foreground">{order.id}</p>
        <p className="mt-4 text-sm text-muted-foreground">
          Payment captured. You'll get a delivery update on WhatsApp within 24 hours.
        </p>

        <ul className="mt-6 space-y-2 text-left text-sm">
          {order.lines.map((l) => (
            <li
              key={l.productId}
              className="flex justify-between gap-4 border-b border-border pb-2 last:border-0"
            >
              <span className="text-muted-foreground">
                {l.name} × {l.qty}
              </span>
              <span className="tabular">{inr(l.price * l.qty)}</span>
            </li>
          ))}
        </ul>
        <div className="mt-4 flex justify-between text-base font-semibold">
          <span>Total paid</span>
          <span className="tabular">{inr(order.total)}</span>
        </div>

        <Button asChild className="press mt-7">
          <Link to="/shop">Continue shopping</Link>
        </Button>
      </motion.div>
    </ShopShell>
  );
}
