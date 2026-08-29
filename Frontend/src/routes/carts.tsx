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
  statusTone,
} from "@/components/primitives";
import { api } from "@/services/sarthi";
import type { Cart } from "@/lib/types";

export const Route = createFileRoute("/carts")({
  head: () => ({
    meta: [
      { title: "Carts — Sarthi" },
      {
        name: "description",
        content: "Live and abandoned carts with recovery attempts and value at risk.",
      },
      { property: "og:title", content: "Carts — Sarthi" },
      {
        property: "og:description",
        content: "Cart state, value at risk and recovery attempts in one view.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: CartsPage,
});

const columns: Column<Cart>[] = [
  {
    key: "id",
    header: "Cart",
    primary: true,
    cell: (c) => <span className="tabular font-medium">{c.id}</span>,
  },
  { key: "customer", header: "Customer", mobileLabel: "Customer", cell: (c) => c.customerName },
  {
    key: "items",
    header: "Items",
    align: "right",
    mobileLabel: "Items",
    cell: (c) => <span className="tabular">{c.items}</span>,
  },
  {
    key: "value",
    header: "Value",
    align: "right",
    mobileLabel: "Value",
    cell: (c) => <span className="tabular">{inr(c.value)}</span>,
  },
  {
    key: "state",
    header: "State",
    mobileLabel: "State",
    cell: (c) => <StatusBadge tone={statusTone(c.state)}>{c.state.replace(/_/g, " ")}</StatusBadge>,
  },
  {
    key: "att",
    header: "Recovery attempts",
    align: "right",
    mobileLabel: "Attempts",
    cell: (c) => <span className="tabular">{c.recoveryAttempts}</span>,
  },
  {
    key: "at",
    header: "Last activity",
    align: "right",
    mobileLabel: "Last activity",
    cell: (c) => (
      <span className="tabular text-xs text-muted-foreground">{shortDate(c.lastActivityAt)}</span>
    ),
  },
];

function CartsPage() {
  const query = useQuery({ queryKey: ["carts"], queryFn: api.listCarts });
  return (
    <AppShell>
      <PageHeader
        eyebrow="Commerce"
        title="Carts"
        description="Every cart Sarthi is watching, the value at stake and how many bounded recovery attempts your policies have allowed."
      />
      <QueryBoundary
        query={query}
        rows={5}
        isEmpty={(d) => d.length === 0}
        emptyTitle="No carts yet"
      >
        {(rows) => {
          const atRisk = rows
            .filter((c) => c.state === "abandoned" || c.state === "checkout_started")
            .reduce((s, c) => s + c.value, 0);
          return (
            <>
              <Panel className="bg-surface">
                <div className="flex flex-wrap items-center gap-10">
                  <div>
                    <p className="eyebrow">Value at risk</p>
                    <p className="tabular mt-2 text-2xl font-semibold text-warning">
                      {inr(atRisk)}
                    </p>
                  </div>
                  <div>
                    <p className="eyebrow">Recovered carts</p>
                    <p className="tabular mt-2 text-2xl font-semibold text-positive">
                      {rows.filter((c) => c.state === "recovered").length}
                    </p>
                  </div>
                </div>
              </Panel>
              <Panel title="Cart activity">
                <DataTable
                  caption="Carts with state and recovery attempts"
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
