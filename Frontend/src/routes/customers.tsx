import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/app-shell";
import { DataTable, type Column } from "@/components/data-table";
import {
  PageHeader,
  Panel,
  QueryBoundary,
  StatusBadge,
  inr,
  shortDate,
} from "@/components/primitives";
import { api } from "@/services/sarthi";
import type { Customer } from "@/lib/types";

export const Route = createFileRoute("/customers")({
  head: () => ({
    meta: [
      { title: "Customers — Sarthi" },
      {
        name: "description",
        content:
          "Customer segments, lifetime value and how much revenue Sarthi influenced per person.",
      },
      { property: "og:title", content: "Customers — Sarthi" },
      {
        property: "og:description",
        content: "Segment-level customer value and AI-influenced revenue.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: CustomersPage,
});

const segmentTone = {
  vip: "primary",
  returning: "positive",
  new: "info",
  at_risk: "warning",
} as const;

const columns: Column<Customer>[] = [
  {
    key: "name",
    header: "Customer",
    primary: true,
    cell: (c) => (
      <div>
        <p className="font-medium">{c.name}</p>
        <p className="text-xs text-muted-foreground">{c.email}</p>
      </div>
    ),
  },
  {
    key: "segment",
    header: "Segment",
    mobileLabel: "Segment",
    cell: (c) => (
      <StatusBadge tone={segmentTone[c.segment]}>{c.segment.replace(/_/g, " ")}</StatusBadge>
    ),
  },
  {
    key: "orders",
    header: "Orders",
    align: "right",
    mobileLabel: "Orders",
    cell: (c) => <span className="tabular">{c.orders}</span>,
  },
  {
    key: "ltv",
    header: "Lifetime value",
    align: "right",
    mobileLabel: "Lifetime value",
    cell: (c) => <span className="tabular">{inr(c.lifetimeValue)}</span>,
  },
  {
    key: "ai",
    header: "AI-influenced",
    align: "right",
    mobileLabel: "AI-influenced",
    cell: (c) => <span className="tabular text-positive">{inr(c.aiInfluencedRevenue)}</span>,
  },
  {
    key: "last",
    header: "Last order",
    align: "right",
    mobileLabel: "Last order",
    cell: (c) => (
      <span className="tabular text-xs text-muted-foreground">{shortDate(c.lastOrderAt)}</span>
    ),
  },
];

function CustomersPage() {
  const query = useQuery({ queryKey: ["customers"], queryFn: api.listCustomers });
  return (
    <AppShell>
      <PageHeader
        eyebrow="Commerce"
        title="Customers"
        description="Who buys, how often, and how much of their spend Sarthi influenced. Segments drive which proposals are eligible."
      />
      <QueryBoundary
        query={query}
        rows={5}
        isEmpty={(d) => d.length === 0}
        emptyTitle="No customers yet"
      >
        {(rows) => (
          <Panel title="Customer base" description={`${rows.length} customers in view`}>
            <DataTable
              caption="Customers with lifetime value and AI-influenced revenue"
              columns={columns}
              rows={rows}
            />
          </Panel>
        )}
      </QueryBoundary>
    </AppShell>
  );
}
