import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { Lock } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { ShopShell } from "@/components/shop-shell";
import { EmptyState, ProcessingRow, inr } from "@/components/primitives";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cartStore, cartTotal, useCart } from "@/lib/shop-cart";
import { api } from "@/services/sarthi";

export const Route = createFileRoute("/shop/checkout")({
  head: () => ({
    meta: [
      { title: "Checkout — Kadam Athletics" },
      {
        name: "description",
        content:
          "Secure checkout with UPI and card payment, address validation and instant order confirmation.",
      },
      { property: "og:title", content: "Checkout — Kadam Athletics" },
      { property: "og:description", content: "Secure UPI and card checkout." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: CheckoutPage,
});

function CheckoutPage() {
  const lines = useCart();
  const total = cartTotal(lines);
  const navigate = useNavigate();
  const [processing, setProcessing] = useState(false);
  const [method, setMethod] = useState<"upi" | "card">("upi");

  if (lines.length === 0 && !processing) {
    return (
      <ShopShell>
        <EmptyState
          title="Nothing to check out"
          description="Add something to your cart first."
          action={
            <Button asChild className="press">
              <Link to="/shop">Browse the store</Link>
            </Button>
          }
        />
      </ShopShell>
    );
  }

  const placeOrder = async () => {
    setProcessing(true);
    try {
      const items = lines.map((l) => ({ product_id: l.productId, quantity: l.qty }));
      const checkout = await api.shopCheckout(items);
      // In demo/test mode, confirm the payment capture immediately.
      await api.shopConfirmPayment(checkout.order_id ?? checkout.razorpay_order_id);
      cartStore.checkout();
      toast.success("Payment captured — order placed");
      navigate({ to: "/shop/order-success" });
    } catch (err) {
      toast.error("Checkout failed", {
        description: err instanceof Error ? err.message : "Could not complete the order.",
      });
      setProcessing(false);
    }
  };

  return (
    <ShopShell>
      <h1 className="text-3xl font-semibold tracking-tight">Checkout</h1>
      <form
        className="mt-8 grid gap-8 lg:grid-cols-[1fr_20rem]"
        onSubmit={(e) => {
          e.preventDefault();
          placeOrder();
        }}
      >
        <div className="space-y-6">
          <fieldset className="rounded-xl border border-border bg-card p-5">
            <legend className="px-1 text-sm font-semibold">Delivery</legend>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="name">Full name</Label>
                <Input id="name" required autoComplete="name" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone">Phone</Label>
                <Input id="phone" required inputMode="tel" autoComplete="tel" />
              </div>
              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="address">Address</Label>
                <Input id="address" required autoComplete="street-address" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="city">City</Label>
                <Input id="city" required autoComplete="address-level2" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="pin">PIN code</Label>
                <Input id="pin" required inputMode="numeric" autoComplete="postal-code" />
              </div>
            </div>
          </fieldset>

          <fieldset className="rounded-xl border border-border bg-card p-5">
            <legend className="px-1 text-sm font-semibold">Payment</legend>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {(["upi", "card"] as const).map((m) => (
                <button
                  key={m}
                  type="button"
                  aria-pressed={method === m}
                  onClick={() => setMethod(m)}
                  className={
                    method === m
                      ? "press rounded-lg border border-primary bg-primary/5 p-4 text-left text-sm font-medium"
                      : "press rounded-lg border border-border p-4 text-left text-sm text-muted-foreground"
                  }
                >
                  {m === "upi" ? "UPI" : "Card"}
                  <span className="mt-1 block text-xs font-normal text-muted-foreground">
                    {m === "upi" ? "Pay via any UPI app" : "Visa, Mastercard, RuPay"}
                  </span>
                </button>
              ))}
            </div>
            <div className="mt-4 space-y-2">
              <Label htmlFor="pay">{method === "upi" ? "UPI ID" : "Card number"}</Label>
              <Input
                id="pay"
                required
                placeholder={method === "upi" ? "name@bank" : "4111 1111 1111 1111"}
                inputMode={method === "upi" ? "text" : "numeric"}
              />
            </div>
            <p className="mt-4 flex items-center gap-1.5 text-xs text-muted-foreground">
              <Lock className="size-3.5" aria-hidden /> Test mode. No real payment is taken.
            </p>
          </fieldset>
        </div>

        <aside className="h-fit rounded-xl border border-border bg-card p-5">
          <h2 className="text-sm font-semibold">Order summary</h2>
          <ul className="mt-4 space-y-2 text-sm">
            {lines.map((l) => (
              <li key={l.productId} className="flex justify-between gap-4">
                <span className="text-muted-foreground">
                  {l.name} × {l.qty}
                </span>
                <span className="tabular">{inr(l.price * l.qty)}</span>
              </li>
            ))}
          </ul>
          <div className="mt-4 flex justify-between border-t border-border pt-3 text-base font-semibold">
            <span>Total</span>
            <span className="tabular">{inr(total)}</span>
          </div>
          <Button type="submit" className="press mt-5 w-full" disabled={processing}>
            Pay {inr(total)}
          </Button>
          {processing ? (
            <div className="mt-3">
              <ProcessingRow label="Confirming payment with your bank" />
            </div>
          ) : null}
        </aside>
      </form>
    </ShopShell>
  );
}
