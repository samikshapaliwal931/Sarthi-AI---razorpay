import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { Sparkles } from "lucide-react";
import { useState } from "react";
import { AppShell } from "@/components/app-shell";
import { DataTable, type Column } from "@/components/data-table";
import {
  PageHeader,
  Panel,
  QueryBoundary,
  StatusBadge,
  inr,
  shortDate,
  statusTone,
} from "@/components/primitives";
import { api } from "@/services/sarthi";
import type { Order } from "@/lib/types";

const STATUS_OPTIONS = [
  "all",
  "created",
  "confirmed",
  "paid",
  "failed",
  "cancelled",
  "refunded",
] as const;

export const Route = createFileRoute("/orders")({
  head: () => ({
    meta: [
      { title: "Orders — Sarthi" },
      {
        name: "description",
        content: "Live order flow with AI attribution, payment status and recovery signals.",
      },
      { property: "og:title", content: "Orders — Sarthi" },
      {
        property: "og:description",
        content: "Every order, with the Sarthi action that influenced it.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: OrdersPage,
});

const columns: Column<Order>[] = [
  {
    key: "id",
    header: "Order",
    primary: true,
    cell: (o) => <span className="tabular font-medium">{o.id}</span>,
  },
  { key: "customer", header: "Customer", mobileLabel: "Customer", cell: (o) => o.customerName },
  {
    key: "items",
    header: "Items",
    align: "right",
    mobileLabel: "Items",
    cell: (o) => <span className="tabular">{o.items}</span>,
  },
  {
    key: "amount",
    header: "Amount",
    align: "right",
    mobileLabel: "Amount",
    cell: (o) => <span className="tabular">{inr(o.amount)}</span>,
  },
  {
    key: "ai",
    header: "Attribution",
    mobileLabel: "Attribution",
    cell: (o) =>
      o.aiAttributed ? (
        <span className="inline-flex items-center gap-1.5 text-xs text-primary">
          <Sparkles className="size-3.5" aria-hidden />
          {o.attributionSource?.replace(/_/g, " ") ?? "sarthi"}
        </span>
      ) : (
        <span className="text-xs text-muted-foreground">Organic</span>
      ),
  },
  {
    key: "status",
    header: "Status",
    mobileLabel: "Status",
    cell: (o) => <StatusBadge tone={statusTone(o.status)}>{o.status}</StatusBadge>,
  },
  {
    key: "at",
    header: "Placed",
    align: "right",
    mobileLabel: "Placed",
    cell: (o) => (
      <span className="tabular text-xs text-muted-foreground">{shortDate(o.placedAt)}</span>
    ),
  },
];

function OrdersPage() {
  const [status, setStatus] = useState<(typeof STATUS_OPTIONS)[number]>("all");
  // Filter is a real query param to GET /orders, not a client-side slice of one page.
  const query = useQuery({
    queryKey: ["orders", status],
    queryFn: () => api.listOrders({ status: status === "all" ? undefined : status }),
  });
  return (
    <AppShell>
      <PageHeader
        eyebrow="Commerce"
        title="Orders"
        description="The order ledger, annotated with which Sarthi action influenced each purchase and where payments are at risk."
        actions={
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as (typeof STATUS_OPTIONS)[number])}
            aria-label="Filter orders by status"
            className="flex h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-xs"
          >
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s === "all" ? "All statuses" : s[0]!.toUpperCase() + s.slice(1)}
              </option>
            ))}
          </select>
        }
      />
      <QueryBoundary
        query={query}
        rows={5}
        isEmpty={(d) => d.length === 0}
        emptyTitle="No orders yet"
      >
        {(rows) => {
          const aiRevenue = rows.filter((o) => o.aiAttributed).reduce((s, o) => s + o.amount, 0);
          return (
            <>
              <Panel className="bg-surface">
                <div className="flex flex-wrap items-center gap-10">
                  <div>
                    <p className="eyebrow">Orders shown</p>
                    <p className="tabular mt-2 text-2xl font-semibold">{rows.length}</p>
                  </div>
                  <div>
                    <p className="eyebrow">AI-attributed value</p>
                    <p className="tabular mt-2 text-2xl font-semibold text-positive">
                      {inr(aiRevenue)}
                    </p>
                  </div>
                  <div>
                    <p className="eyebrow">Failed payments</p>
                    <p className="tabular mt-2 text-2xl font-semibold text-destructive">
                      {rows.filter((o) => o.status === "failed").length}
                    </p>
                  </div>
                </div>
              </Panel>
              <Panel title="Recent orders">
                <DataTable
                  caption="Recent orders with AI attribution"
                  columns={columns}
                  rows={rows}
                />
              </Panel>
            </>
          );
        }}
      </QueryBoundary>
    </AppShell>
  );
}
