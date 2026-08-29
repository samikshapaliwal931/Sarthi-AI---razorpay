import { useSyncExternalStore } from "react";
import type { CartLine, ShopProduct } from "@/lib/types";
import { shopApi } from "@/services/sarthi";

/**
 * Shopper session id — deliberately stored under a DIFFERENT localStorage key than the
 * merchant auth token ("sarthi_token", see src/services/client.ts). Keeping these keys
 * distinct avoids the merchant cockpit session and the shopper storefront session ever
 * clobbering one another when someone navigates between /shop/* and the merchant routes
 * in the same browser.
 */
const SHOP_SESSION_KEY = "sarthi_shop_session_id";

export function getShopSessionId(): string {
  if (typeof window === "undefined") return "server-session";
  let id = window.localStorage.getItem(SHOP_SESSION_KEY);
  if (!id) {
    id = `shop_${crypto.randomUUID?.() ?? Date.now().toString(36) + Math.random().toString(36).slice(2)}`;
    window.localStorage.setItem(SHOP_SESSION_KEY, id);
  }
  return id;
}

/**
 * Client-side cart store for snappy UI, kept in sync with the real backend session cart
 * (POST /storefront/cart/{session_id}/add) so abandoned-cart / recovery data on the merchant
 * side reflects real shopper activity rather than only living in the browser.
 */
let lines: CartLine[] = [];
let lastOrder: { id: string; lines: CartLine[]; total: number } | null = null;
const listeners = new Set<() => void>();

const emit = () => listeners.forEach((l) => l());

export const cartStore = {
  subscribe(listener: () => void) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
  get: () => lines,
  add(product: ShopProduct, viaSarthi = false) {
    const existing = lines.find((l) => l.productId === product.id);
    lines = existing
      ? lines.map((l) => (l.productId === product.id ? { ...l, qty: l.qty + 1 } : l))
      : [
          ...lines,
          { productId: product.id, name: product.name, price: product.price, qty: 1, viaSarthi },
        ];
    emit();

    // Sync to the real backend session cart. Fire-and-forget so the UI stays snappy;
    // failures are logged but don't roll back the optimistic local line — checkout still
    // sends the authoritative local cart to /storefront/checkout.
    shopApi.addToCart(getShopSessionId(), product.id, 1).catch((err) => {
      console.error("Failed to sync cart item to backend session cart", err);
    });
  },
  setQty(productId: string, qty: number) {
    lines =
      qty <= 0
        ? lines.filter((l) => l.productId !== productId)
        : lines.map((l) => (l.productId === productId ? { ...l, qty } : l));
    emit();
  },
  remove(productId: string) {
    lines = lines.filter((l) => l.productId !== productId);
    emit();
  },
  checkout() {
    const total = lines.reduce((s, l) => s + l.price * l.qty, 0);
    lastOrder = { id: `ORD-${Date.now().toString(36).toUpperCase()}`, lines, total };
    lines = [];
    emit();
    return lastOrder;
  },
  getLastOrder: () => lastOrder,
};

const empty: CartLine[] = [];

export function useCart() {
  return useSyncExternalStore(
    (l) => cartStore.subscribe(l),
    () => lines,
    () => empty,
  );
}

export const cartTotal = (items: CartLine[]) => items.reduce((s, l) => s + l.price * l.qty, 0);
export const cartCount = (items: CartLine[]) => items.reduce((s, l) => s + l.qty, 0);
