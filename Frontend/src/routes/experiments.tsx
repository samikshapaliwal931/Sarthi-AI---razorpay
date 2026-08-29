import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/app-shell";
import {
  PageHeader,
  Panel,
  QueryBoundary,
  Stagger,
  StaggerItem,
  StatusBadge,
  inr,
  num,
  statusTone,
} from "@/components/primitives";
import { api } from "@/services/sarthi";
import type { ExperimentArm } from "@/lib/types";

export const Route = createFileRoute("/experiments")({
  head: () => ({
    meta: [
      { title: "Experiments — Sarthi" },
      {
        name: "description",
        content:
          "Controlled tests that quantify incremental lift so every future proposal is better calibrated.",
      },
      { property: "og:title", content: "Experiments — Sarthi" },
      {
        property: "og:description",
        content: "Control vs variant results with confidence and incremental revenue.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: ExperimentsPage,
});

function Arm({ arm, highlight }: { arm: ExperimentArm; highlight?: boolean }) {
  return (
    <div
      className={
        highlight
          ? "rounded-lg border border-primary/40 bg-primary/5 p-4"
          : "rounded-lg border border-border p-4"
      }
    >
      <p className="text-sm font-medium">{arm.label}</p>
      <dl className="mt-3 space-y-1.5 text-xs">
        <div className="flex justify-between gap-4">
          <dt className="text-muted-foreground">Sessions</dt>
          <dd className="tabular">{num(arm.sessions)}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-muted-foreground">Conversion</dt>
          <dd className="tabular">{arm.conversion.toFixed(1)}%</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-muted-foreground">Revenue / session</dt>
          <dd className="tabular">₹{arm.revenuePerSession.toFixed(1)}</dd>
        </div>
      </dl>
    </div>
  );
}

function ExperimentsPage() {
  const query = useQuery({ queryKey: ["experiments"], queryFn: api.listExperiments });
  return (
    <AppShell>
      <PageHeader
        eyebrow="Growth"
        title="Experiments"
        description="Sarthi holds back a control group on every intervention, so lift is measured rather than claimed."
      />
      <QueryBoundary
        query={query}
        rows={3}
        isEmpty={(d) => d.length === 0}
        emptyTitle="No experiments running"
      >
        {(rows) => (
          <Stagger className="grid gap-5 xl:grid-cols-2">
            {rows.map((e) => (
              <StaggerItem key={e.id}>
                <article className="lift h-full rounded-xl border border-border bg-card p-5">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <StatusBadge tone={statusTone(e.status)}>{e.status}</StatusBadge>
                    <span className="tabular text-xs text-muted-foreground">
                      {Math.round(e.confidence * 100)}% confidence
                    </span>
                  </div>
                  <h2 className="mt-3 text-lg font-semibold tracking-tight">{e.name}</h2>
                  <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
                    {e.hypothesis}
                  </p>

                  <div className="mt-5 grid gap-3 sm:grid-cols-2">
                    <Arm arm={e.control} />
                    <Arm arm={e.variant} highlight />
                  </div>

                  <div className="mt-5 flex flex-wrap items-end justify-between gap-4 border-t border-border pt-4">
                    <div>
                      <p className="eyebrow">Measured lift</p>
                      <p className="tabular mt-1.5 text-2xl font-semibold text-positive">
                        +{e.lift.toFixed(1)}%
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="eyebrow">Incremental revenue</p>
                      <p className="tabular mt-1.5 text-lg font-semibold">
                        {inr(e.incrementalRevenue)}
                      </p>
                    </div>
                  </div>
                </article>
              </StaggerItem>
            ))}
          </Stagger>
        )}
      </QueryBoundary>
    </AppShell>
  );
}
