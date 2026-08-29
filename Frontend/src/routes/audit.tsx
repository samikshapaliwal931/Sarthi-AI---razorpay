import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { AppShell } from "@/components/app-shell";
import {
  PageHeader,
  Panel,
  QueryBoundary,
  StatusBadge,
  shortDate,
  statusTone,
} from "@/components/primitives";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/services/sarthi";

export const Route = createFileRoute("/audit")({
  head: () => ({
    meta: [
      { title: "Audit trail — Sarthi" },
      {
        name: "description",
        content:
          "Immutable record of every agent decision: input, policy result, approval, execution and outcome.",
      },
      { property: "og:title", content: "Audit trail — Sarthi" },
      {
        property: "og:description",
        content: "Input, decision, policy result, approval and execution for every action.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: AuditPage,
});

function AuditPage() {
  const [q, setQ] = useState("");
  const query = useQuery({ queryKey: ["audit"], queryFn: api.listAuditEvents });

  return (
    <AppShell>
      <PageHeader
        eyebrow="Governance"
        title="Audit trail"
        description="Every decision Sarthi makes is written down before it acts: what it saw, what your policies said, who approved, and what actually happened."
        actions={
          <Input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search actions"
            aria-label="Search audit trail"
            className="w-56"
          />
        }
      />
      <QueryBoundary
        query={query}
        rows={5}
        isEmpty={(d) => d.length === 0}
        emptyTitle="Audit trail is empty"
      >
        {(rows) => {
          const filtered = rows.filter((e) =>
            `${e.agent} ${e.action} ${e.result} ${e.correlationId}`
              .toLowerCase()
              .includes(q.toLowerCase()),
          );
          return filtered.length === 0 ? (
            <Panel>
              <p className="py-10 text-center text-sm text-muted-foreground">
                No audit records match “{q}”.
              </p>
            </Panel>
          ) : (
            <div className="space-y-4">
              {filtered.map((e) => (
                <details
                  key={e.id}
                  className="lift group rounded-xl border border-border bg-card p-5 open:shadow-elevate"
                >
                  <summary className="flex cursor-pointer list-none flex-wrap items-center gap-3">
                    <span className="eyebrow text-primary">{e.agent}</span>
                    <StatusBadge tone={statusTone(e.policyResult)}>
                      {e.policyResult.replace(/_/g, " ")}
                    </StatusBadge>
                    <span className="min-w-0 flex-1 truncate text-sm font-medium">{e.action}</span>
                    <span className="tabular text-xs text-muted-foreground">{shortDate(e.at)}</span>
                  </summary>
                  <dl className="mt-5 grid gap-4 border-t border-border pt-4 text-sm md:grid-cols-2">
                    <div>
                      <dt className="eyebrow">Input</dt>
                      <dd className="mt-1.5 text-muted-foreground">{e.input}</dd>
                    </div>
                    <div>
                      <dt className="eyebrow">Decision</dt>
                      <dd className="mt-1.5 text-muted-foreground">{e.decision}</dd>
                    </div>
                    <div>
                      <dt className="eyebrow">Approval</dt>
                      <dd className="mt-1.5 text-muted-foreground">
                        {e.approval.replace(/_/g, " ")}
                      </dd>
                    </div>
                    <div>
                      <dt className="eyebrow">Execution</dt>
                      <dd className="mt-1.5 text-muted-foreground">
                        {e.execution.replace(/_/g, " ")}
                      </dd>
                    </div>
                    <div className="md:col-span-2">
                      <dt className="eyebrow">Result</dt>
                      <dd className="mt-1.5">{e.result}</dd>
                    </div>
                  </dl>
                  <p className="tabular mt-4 text-[11px] text-muted-foreground">
                    {e.correlationId}
                  </p>
                </details>
              ))}
              <div className="flex justify-end">
                <Button variant="outline" size="sm" className="press" onClick={() => setQ("")}>
                  Clear filter
                </Button>
              </div>
            </div>
          );
        }}
      </QueryBoundary>
    </AppShell>
  );
}
