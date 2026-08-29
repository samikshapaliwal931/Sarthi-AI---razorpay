import { useMutation } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";
import { useState } from "react";
import { AppShell } from "@/components/app-shell";
import { ErrorState, PageHeader, Panel, ProcessingRow } from "@/components/primitives";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/services/sarthi";
import type { CopilotAnswer } from "@/lib/types";

export const Route = createFileRoute("/ai-copilot")({
  head: () => ({
    meta: [
      { title: "AI copilot — Sarthi" },
      {
        name: "description",
        content:
          "Ask a revenue question in plain language and get the finding, the numbers behind it and a bounded intervention.",
      },
      { property: "og:title", content: "AI copilot — Sarthi" },
      {
        property: "og:description",
        content: "Analyst answers with evidence and a proposed action, not chat filler.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: CopilotPage,
});

const prompts = [
  "Why did revenue drop yesterday?",
  "Which products should I bundle together?",
  "Where am I losing the most checkout revenue?",
];

function formatDataValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (Array.isArray(value)) return `${value.length} item${value.length === 1 ? "" : "s"}`;
  if (typeof value === "object")
    return `${Object.keys(value).length} field${Object.keys(value).length === 1 ? "" : "s"}`;
  return String(value);
}

function AnswerCard({ answer }: { answer: CopilotAnswer }) {
  const opportunityId =
    typeof answer.data?.["opportunity_id"] === "string"
      ? (answer.data["opportunity_id"] as string)
      : undefined;

  const opportunityList = Array.isArray(answer.data?.["opportunities"])
    ? (answer.data["opportunities"] as Array<Record<string, unknown>>)
    : [];

  const dataEntries = answer.data
    ? Object.entries(answer.data).filter(
        ([key]) => key !== "opportunity_id" && key !== "opportunities",
      )
    : [];

  return (
    <motion.article
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="rounded-xl border border-border bg-card p-6 shadow-elevate"
    >
      <p className="eyebrow text-primary">Sarthi</p>
      <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed">{answer.message}</p>

      {opportunityList.length > 0 ? (
        <div className="mt-5 space-y-2">
          {opportunityList.map((opp) => {
            const id = typeof opp["id"] === "string" ? opp["id"] : undefined;
            return (
              <div
                key={id ?? (opp["title"] as string)}
                className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border bg-surface p-4"
              >
                <div className="min-w-0">
                  <p className="text-xs font-medium uppercase tracking-wide text-primary">
                    {String(opp["type"] ?? "opportunity").replace(/_/g, " ")}
                  </p>
                  <p className="mt-1 truncate text-sm font-medium">
                    {String(opp["title"] ?? "Untitled")}
                  </p>
                  {typeof opp["expected_impact"] === "number" ? (
                    <p className="tabular mt-1 text-xs text-muted-foreground">
                      Expected impact ₹
                      {Math.round(opp["expected_impact"] as number).toLocaleString("en-IN")}
                    </p>
                  ) : null}
                </div>
                {id ? (
                  <Button asChild size="sm" variant="outline" className="press">
                    <Link to="/opportunities/$id" params={{ id }}>
                      Review <ArrowRight className="size-3.5" aria-hidden />
                    </Link>
                  </Button>
                ) : null}
              </div>
            );
          })}
        </div>
      ) : null}

      {dataEntries.length > 0 ? (
        <dl className="mt-5 grid gap-3 sm:grid-cols-3">
          {dataEntries.map(([key, value]) => (
            <div key={key} className="rounded-lg border border-border bg-surface p-4">
              <dt className="eyebrow">{key.replace(/_/g, " ")}</dt>
              <dd className="tabular mt-2 text-lg font-semibold">{formatDataValue(value)}</dd>
            </div>
          ))}
        </dl>
      ) : null}

      {answer.actions.length > 0 ? (
        <div className="mt-5 space-y-2">
          {answer.actions.map((action, i) => (
            <div
              key={i}
              className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-primary/30 bg-primary/5 p-4"
            >
              <p className="max-w-xl text-sm">
                <span className="font-medium">Suggested action · </span>
                {action.label ?? action.type ?? "See details"}
              </p>
              {opportunityId ? (
                <Button asChild size="sm" className="press">
                  <Link to="/opportunities/$id" params={{ id: opportunityId }}>
                    Review opportunity <ArrowRight className="size-3.5" aria-hidden />
                  </Link>
                </Button>
              ) : null}
            </div>
          ))}
        </div>
      ) : opportunityId ? (
        <div className="mt-5 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-primary/30 bg-primary/5 p-4">
          <p className="max-w-xl text-sm">This answer references an opportunity.</p>
          <Button asChild size="sm" className="press">
            <Link to="/opportunities/$id" params={{ id: opportunityId }}>
              Review opportunity <ArrowRight className="size-3.5" aria-hidden />
            </Link>
          </Button>
        </div>
      ) : null}

      <p className="mt-4 text-[11px] text-muted-foreground">
        Correlation ID: {answer.correlationId}
      </p>
    </motion.article>
  );
}

function CopilotPage() {
  const [question, setQuestion] = useState("");
  const ask = useMutation({ mutationFn: (q: string) => api.askCopilot(q) });

  return (
    <AppShell>
      <PageHeader
        eyebrow="Workspace"
        title="AI copilot"
        description="Not a chatbot. Ask a revenue question and Sarthi returns the finding, the evidence and a bounded action you can approve."
      />

      <Panel>
        <form
          className="flex flex-col gap-3 sm:flex-row"
          onSubmit={(e) => {
            e.preventDefault();
            if (question.trim()) ask.mutate(question.trim());
          }}
        >
          <Input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask about revenue, conversion, payments or products"
            aria-label="Ask the copilot a revenue question"
          />
          <Button type="submit" className="press" disabled={ask.isPending || !question.trim()}>
            <Sparkles className="size-4" aria-hidden /> Ask Sarthi
          </Button>
        </form>
        <div className="mt-4 flex flex-wrap gap-2">
          {prompts.map((p) => (
            <button
              key={p}
              type="button"
              className="link-sweep rounded-full border border-border px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
              onClick={() => {
                setQuestion(p);
                ask.mutate(p);
              }}
            >
              {p}
            </button>
          ))}
        </div>
      </Panel>

      {ask.isPending ? (
        <Panel>
          <ProcessingRow label="Reading orders, payments and catalog signals" />
        </Panel>
      ) : null}
      {ask.isError ? (
        <ErrorState
          message="The copilot could not answer that."
          onRetry={() => ask.mutate(question)}
        />
      ) : null}
      {ask.data && !ask.isPending ? <AnswerCard answer={ask.data} /> : null}
    </AppShell>
  );
}
