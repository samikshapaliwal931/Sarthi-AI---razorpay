import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { AppShell } from "@/components/app-shell";
import {
  PageHeader,
  Panel,
  ProcessingRow,
  QueryBoundary,
  StatusBadge,
  shortDate,
  statusTone,
} from "@/components/primitives";
import { api } from "@/services/sarthi";

export const Route = createFileRoute("/agent-activity")({
  head: () => ({
    meta: [
      { title: "Agent activity — Sarthi" },
      {
        name: "description",
        content:
          "A live feed of what every Sarthi agent did, with correlation IDs linking action to outcome.",
      },
      { property: "og:title", content: "Agent activity — Sarthi" },
      {
        property: "og:description",
        content: "Live agent feed with status, detail and correlation IDs.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: AgentActivityPage,
});

function AgentActivityPage() {
  const query = useQuery({ queryKey: ["agent-activity"], queryFn: api.listAgentActivity });
  return (
    <AppShell>
      <PageHeader
        eyebrow="Governance"
        title="Agent activity"
        description="Every agent step is logged as it happens. Nothing executes without a correlation ID you can trace to an audit record."
      />
      <QueryBoundary
        query={query}
        rows={6}
        isEmpty={(d) => d.length === 0}
        emptyTitle="No agent activity yet"
      >
        {(rows) => (
          <Panel title="Live feed" description={`${rows.length} steps in the current window`}>
            <ol className="relative space-y-0">
              {rows.map((a, i) => (
                <motion.li
                  key={a.id}
                  initial={{ opacity: 0, x: -8 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true, margin: "-40px" }}
                  transition={{
                    duration: 0.4,
                    delay: Math.min(i * 0.03, 0.24),
                    ease: [0.22, 1, 0.36, 1],
                  }}
                  className="row-hover relative flex gap-4 rounded-md border-b border-border/70 px-3 py-4 last:border-0"
                >
                  <span className="mt-1.5 size-2 shrink-0 rounded-full bg-primary" aria-hidden />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="eyebrow text-primary">{a.agent}</span>
                      <StatusBadge tone={statusTone(a.status)}>
                        {a.status.replace(/_/g, " ")}
                      </StatusBadge>
                      <span className="tabular text-xs text-muted-foreground">
                        {shortDate(a.at)}
                      </span>
                    </div>
                    <p className="mt-2 text-sm font-medium">{a.action}</p>
                    <p className="mt-1 text-sm text-muted-foreground">{a.detail}</p>
                    {a.status === "running" ? (
                      <div className="mt-2">
                        <ProcessingRow label="Executing inside policy limits" />
                      </div>
                    ) : null}
                    <p className="tabular mt-2 text-[11px] text-muted-foreground">
                      {a.correlationId}
                    </p>
                  </div>
                </motion.li>
              ))}
            </ol>
          </Panel>
        )}
      </QueryBoundary>
    </AppShell>
  );
}
