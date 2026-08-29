import { Link } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { ArrowRight, CircleSlash, ShieldCheck, TriangleAlert } from "lucide-react";
import type { EvidencePoint, Opportunity, PolicyCheck } from "@/lib/types";
import {
  ConfidenceMeter,
  StaggerItem,
  StatusBadge,
  inr,
  num,
  statusTone,
} from "@/components/primitives";
import { Button } from "@/components/ui/button";

export const opportunityTypeLabel: Record<Opportunity["type"], string> = {
  cross_sell: "Cross-sell",
  bundle: "Bundle",
  upsell: "Upsell",
  cart_recovery: "Cart recovery",
  payment_recovery: "Payment recovery",
  inventory_promo: "Inventory promo",
  campaign: "Campaign",
  ranking: "Ranking",
};

export function OpportunityCard({
  opportunity,
  onDecide,
  pending,
}: {
  opportunity: Opportunity;
  onDecide?: (id: string, decision: "approve" | "reject") => void;
  pending?: boolean;
}) {
  const o = opportunity;
  return (
    <StaggerItem>
      <motion.article
        layoutId={`opp-${o.id}`}
        whileHover={{ y: -2 }}
        transition={{ type: "spring", stiffness: 260, damping: 26 }}
        className="group rounded-xl border border-border bg-card p-5 transition-colors hover:border-border-strong"
      >
        <div className="flex flex-wrap items-center gap-2">
          <span className="eyebrow text-primary">{opportunityTypeLabel[o.type]}</span>
          <StatusBadge tone={statusTone(o.status)}>{o.status.replace(/_/g, " ")}</StatusBadge>
        </div>

        <h3 className="mt-3 text-lg font-semibold leading-snug tracking-tight">
          <Link
            to="/opportunities/$id"
            params={{ id: o.id }}
            className="focus-visible:outline-none focus-visible:underline"
          >
            {o.title}
          </Link>
        </h3>
        <p className="mt-2 line-clamp-2 text-sm leading-relaxed text-muted-foreground">
          {o.summary}
        </p>

        <dl className="mt-5 grid grid-cols-2 gap-4 border-t border-border pt-4 sm:grid-cols-4">
          <div>
            <dt className="eyebrow">Expected revenue</dt>
            <dd className="tabular mt-1.5 text-sm font-medium text-positive">
              {inr(o.expectedRevenue)}
            </dd>
          </div>
          <div>
            <dt className="eyebrow">Est. orders</dt>
            <dd className="tabular mt-1.5 text-sm font-medium">{num(o.expectedOrders)}</dd>
          </div>
          <div>
            <dt className="eyebrow">Segment</dt>
            <dd className="mt-1.5 truncate text-sm">{o.segment}</dd>
          </div>
          <div>
            <dt className="eyebrow">Confidence</dt>
            <dd className="mt-1.5">
              <ConfidenceMeter value={o.confidence} />
            </dd>
          </div>
        </dl>

        <p className="mt-4 text-xs text-muted-foreground">
          <span className="text-foreground">Evidence:</span> {o.evidence[0]?.statement}
        </p>

        <div className="mt-5 flex flex-wrap items-center gap-2">
          <Button asChild size="sm" variant="secondary">
            <Link to="/opportunities/$id" params={{ id: o.id }}>
              Review <ArrowRight className="size-3.5" aria-hidden />
            </Link>
          </Button>
          {onDecide && (o.status === "new" || o.status === "under_review") ? (
            <>
              <Button size="sm" disabled={pending} onClick={() => onDecide(o.id, "approve")}>
                Approve
              </Button>
              <Button
                size="sm"
                variant="ghost"
                disabled={pending}
                onClick={() => onDecide(o.id, "reject")}
              >
                Reject
              </Button>
            </>
          ) : null}
        </div>
      </motion.article>
    </StaggerItem>
  );
}

export function EvidenceTimeline({ evidence }: { evidence: EvidencePoint[] }) {
  return (
    <ol className="relative space-y-5 border-l border-border pl-6">
      {evidence.map((e, i) => (
        <motion.li
          key={i}
          initial={{ opacity: 0, x: -8 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ delay: i * 0.07, duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
          className="relative"
        >
          <span
            className={`absolute -left-[27px] top-1.5 size-2.5 rounded-full border-2 ${
              e.kind === "recommendation"
                ? "border-primary bg-primary"
                : "border-info bg-background"
            }`}
            aria-hidden
          />
          <p className="eyebrow">{e.kind === "recommendation" ? "Recommendation" : "Observed"}</p>
          <p className="mt-1.5 text-sm leading-relaxed">{e.statement}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {e.metric ? <span className="tabular mr-2">{e.metric}</span> : null}
            Source: {e.source}
          </p>
        </motion.li>
      ))}
    </ol>
  );
}

export function PolicyChecklist({ checks }: { checks: PolicyCheck[] }) {
  return (
    <ul className="space-y-3">
      {checks.map((c) => {
        const Icon =
          c.result === "pass" ? ShieldCheck : c.result === "block" ? CircleSlash : TriangleAlert;
        const tone =
          c.result === "pass"
            ? "text-positive"
            : c.result === "block"
              ? "text-destructive"
              : "text-warning";
        return (
          <li key={c.policy} className="flex items-start gap-3">
            <Icon className={`mt-0.5 size-4 shrink-0 ${tone}`} aria-hidden />
            <div>
              <p className="text-sm font-medium">{c.policy}</p>
              <p className="text-xs text-muted-foreground">{c.detail}</p>
            </div>
            <span className="ml-auto">
              <StatusBadge tone={statusTone(c.result)}>{c.result.replace(/_/g, " ")}</StatusBadge>
            </span>
          </li>
        );
      })}
    </ul>
  );
}
