import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { toast } from "sonner";
import { AppShell } from "@/components/app-shell";
import { DataTable, type Column } from "@/components/data-table";
import { MetricCard } from "@/components/metrics";
import {
  PageHeader,
  Panel,
  QueryBoundary,
  Stagger,
  StatusBadge,
  inr,
  shortDate,
  statusTone,
} from "@/components/primitives";
import { Button } from "@/components/ui/button";
import { api } from "@/services/sarthi";
import type { RecoveryCase } from "@/lib/types";

export const Route = createFileRoute("/revenue-recovery")({
  head: () => ({
    meta: [
      { title: "Revenue recovery — Sarthi" },
      {
        name: "description",
        content:
          "Failed payments, abandoned carts and incomplete checkouts, with what Sarthi recovered and how.",
      },
      { property: "og:title", content: "Revenue recovery — Sarthi" },
      {
        property: "og:description",
        content: "Recover failed payments and abandoned carts inside your policy limits.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: RecoveryPage,
});

const kindLabel: Record<RecoveryCase["kind"], string> = {
  payment_failure: "Payment failure",
  abandoned_cart: "Abandoned cart",
  incomplete_checkout: "Incomplete checkout",
};

function RecoveryPage() {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["recovery"], queryFn: api.listRecoveryCases });

  const detect = useMutation({
    mutationFn: api.detectRecoveryCases,
    onSuccess: (found) => {
      toast.success(
        found.length > 0
          ? `Found ${found.length} new case${found.length === 1 ? "" : "s"}`
          : "No new cases",
        {
          description:
            found.length > 0
              ? "Scanned abandoned carts and failed payments."
              : "Everything open is already tracked.",
        },
      );
      queryClient.invalidateQueries({ queryKey: ["recovery"] });
    },
    onError: (err: any) =>
      toast.error("Scan failed", { description: err?.message ?? "Try again." }),
  });

  const intervene = useMutation({
    mutationFn: (id: string) => api.sendRecoveryIntervention(id),
    onSuccess: () => {
      toast.success("Intervention sent", {
        description: "Reminder queued. It's in the audit trail.",
      });
      queryClient.invalidateQueries({ queryKey: ["recovery"] });
    },
    onError: (err: any) =>
      toast.error("Couldn't send intervention", { description: err?.message ?? "Try again." }),
  });

  const columns: Column<RecoveryCase>[] = [
    {
      key: "case",
      header: "Case",
      primary: true,
      cell: (r) => (
        <div>
          <p className="font-medium">{r.customerName}</p>
          <p className="text-xs text-muted-foreground">
            {kindLabel[r.kind]} · {r.reason}
          </p>
        </div>
      ),
    },
    {
      key: "atRisk",
      header: "At risk",
      align: "right",
      mobileLabel: "At risk",
      cell: (r) => <span className="tabular">{inr(r.atRisk)}</span>,
    },
    {
      key: "recoverable",
      header: "Still open",
      align: "right",
      mobileLabel: "Still open",
      cell: (r) => <span className="tabular text-warning">{inr(r.recoverable)}</span>,
    },
    {
      key: "recovered",
      header: "Recovered",
      align: "right",
      mobileLabel: "Recovered",
      cell: (r) => <span className="tabular text-positive">{inr(r.recovered)}</span>,
    },
    {
      key: "status",
      header: "Status",
      mobileLabel: "Status",
      cell: (r) => (
        <StatusBadge tone={statusTone(r.status)}>{r.status.replace(/_/g, " ")}</StatusBadge>
      ),
    },
    {
      key: "at",
      header: "Detected",
      align: "right",
      mobileLabel: "Detected",
      cell: (r) => <span className="tabular text-xs text-muted-foreground">{shortDate(r.at)}</span>,
    },
    {
      key: "action",
      header: "",
      align: "right",
      mobileLabel: "Action",
      cell: (r) =>
        r.status === "open" ? (
          // DataTable's mobile card view wraps every cell in a <button>, so this
          // must not render a nested <button> — asChild swaps it to a <span>.
          <Button size="sm" variant="outline" className="press" asChild>
            <span
              role="button"
              tabIndex={0}
              aria-disabled={intervene.isPending && intervene.variables === r.id}
              onClick={(e) => {
                e.stopPropagation();
                if (!(intervene.isPending && intervene.variables === r.id)) intervene.mutate(r.id);
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  e.stopPropagation();
                  if (!(intervene.isPending && intervene.variables === r.id))
                    intervene.mutate(r.id);
                }
              }}
            >
              Send reminder
            </span>
          </Button>
        ) : null,
    },
  ];

  return (
    <AppShell>
      <PageHeader
        eyebrow="Revenue"
        title="Revenue recovery"
        description="Sarthi never charges a customer on its own. It detects the failure, sends the retry or reminder your policy allows, and reports what came back."
        actions={
          <Button onClick={() => detect.mutate()} disabled={detect.isPending}>
            {detect.isPending ? "Scanning…" : "Scan for cases"}
          </Button>
        }
      />
      <QueryBoundary
        query={query}
        rows={5}
        isEmpty={(d) => d.length === 0}
        emptyTitle="Nothing to recover"
        emptyDescription='Click "Scan for cases" to check for abandoned carts and failed payments.'
      >
        {(rows) => {
          const atRisk = rows.reduce((s, r) => s + r.atRisk, 0);
          const stillOpen = rows.reduce((s, r) => s + r.recoverable, 0);
          const recovered = rows.reduce((s, r) => s + r.recovered, 0);
          return (
            <>
              <Stagger className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <MetricCard label="Revenue at risk" value={atRisk} format={(v) => inr(v)} />
                <MetricCard
                  label="Still open"
                  value={stillOpen}
                  format={(v) => inr(v)}
                  hint="Potential value minus whatever's already recovered."
                />
                <MetricCard label="Recovered" value={recovered} format={(v) => inr(v)} />
                <MetricCard
                  label="Open cases"
                  value={rows.filter((r) => r.status === "open").length}
                />
              </Stagger>
              <Panel
                title="Recovery cases"
                description="Each case carries the failure reason and the bounded action taken."
              >
                <DataTable caption="Revenue recovery cases" columns={columns} rows={rows} />
              </Panel>
            </>
          );
        }}
      </QueryBoundary>
    </AppShell>
  );
}
