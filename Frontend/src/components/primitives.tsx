import { motion, useInView, useReducedMotion } from "framer-motion";
import { AlertTriangle, Inbox, Loader2, RefreshCw, ShieldAlert } from "lucide-react";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

/* ---------- formatting ---------- */

export const inr = (value: number, compact = false) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: compact ? 1 : 0,
    notation: compact ? "compact" : "standard",
  }).format(value);

export const pct = (value: number, digits = 1) => `${(value * 100).toFixed(digits)}%`;
export const num = (value: number) => new Intl.NumberFormat("en-IN").format(value);
export const shortDate = (iso: string) =>
  new Date(iso).toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });

/* ---------- motion ---------- */

export function Reveal({
  children,
  delay = 0,
  className,
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
}) {
  const reduced = useReducedMotion();
  return (
    <motion.div
      className={className}
      initial={reduced ? false : { opacity: 0, y: 14 }}
      whileInView={reduced ? undefined : { opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.55, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}

export function Stagger({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <motion.div
      className={className}
      initial="hidden"
      animate="show"
      variants={{ hidden: {}, show: { transition: { staggerChildren: 0.06 } } }}
    >
      {children}
    </motion.div>
  );
}

export function StaggerItem({ children, className }: { children: ReactNode; className?: string }) {
  const reduced = useReducedMotion();
  return (
    <motion.div
      className={className}
      variants={
        reduced
          ? { hidden: {}, show: {} }
          : {
              hidden: { opacity: 0, y: 12 },
              show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } },
            }
      }
    >
      {children}
    </motion.div>
  );
}

export function Counter({
  value,
  format = (v: number) => num(Math.round(v)),
  className,
}: {
  value: number;
  format?: (v: number) => string;
  className?: string;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true });
  const reduced = useReducedMotion();
  const [display, setDisplay] = useState(reduced ? value : 0);

  useEffect(() => {
    if (reduced) {
      setDisplay(value);
      return;
    }
    if (!inView) return;
    const start = performance.now();
    const duration = 900;
    let frame = 0;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(value * eased);
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [inView, value, reduced]);

  return (
    <span ref={ref} className={cn("tabular", className)}>
      {format(display)}
    </span>
  );
}

/* ---------- layout ---------- */

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <header className="flex flex-col gap-4 border-b border-border pb-6 md:flex-row md:items-end md:justify-between">
      <div className="max-w-2xl">
        {eyebrow ? <p className="eyebrow mb-3">{eyebrow}</p> : null}
        <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">{title}</h1>
        {description ? (
          <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{description}</p>
        ) : null}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
    </header>
  );
}

export function Panel({
  title,
  description,
  actions,
  children,
  className,
}: {
  title?: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={cn("rounded-xl border border-border bg-card shadow-elevate", className)}>
      {title ? (
        <div className="flex flex-wrap items-start justify-between gap-3 border-b border-border px-5 py-4">
          <div>
            <h2 className="text-sm font-semibold tracking-tight">{title}</h2>
            {description ? (
              <p className="mt-1 text-xs text-muted-foreground">{description}</p>
            ) : null}
          </div>
          {actions}
        </div>
      ) : null}
      <div className="p-5">{children}</div>
    </section>
  );
}

/* ---------- status ---------- */

type Tone = "neutral" | "positive" | "warning" | "danger" | "info" | "primary";

const toneClass: Record<Tone, string> = {
  neutral: "border-border-strong text-muted-foreground",
  positive: "border-positive/40 text-positive",
  warning: "border-warning/40 text-warning",
  danger: "border-destructive/45 text-destructive",
  info: "border-info/40 text-info",
  primary: "border-primary/45 text-primary",
};

export function StatusBadge({ tone = "neutral", children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border bg-transparent px-2.5 py-0.5 text-[11px] font-medium tracking-wide",
        toneClass[tone],
      )}
    >
      <span className="size-1.5 rounded-full bg-current" aria-hidden />
      {children}
    </span>
  );
}

export function statusTone(status: string): Tone {
  switch (status) {
    case "approved":
    case "executed":
    case "paid":
    case "fulfilled":
    case "recovered":
    case "pass":
    case "completed":
    case "live":
    case "captured":
    case "in_stock":
      return "positive";
    case "blocked":
    case "failed":
    case "rejected":
    case "lost":
    case "block":
    case "out_of_stock":
      return "danger";
    case "pending":
    case "awaiting_approval":
    case "requires_approval":
    case "under_review":
    case "low_stock":
    case "at_risk":
      return "warning";
    case "new":
    case "running":
    case "executing":
    case "in_progress":
    case "active":
      return "info";
    default:
      return "neutral";
  }
}

export function ConfidenceMeter({ value }: { value: number }) {
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-20 overflow-hidden rounded-full bg-muted" role="presentation">
        <motion.div
          className="h-full rounded-full bg-primary"
          initial={{ width: 0 }}
          whileInView={{ width: `${Math.round(value * 100)}%` }}
          viewport={{ once: true }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
        />
      </div>
      <span className="tabular text-xs text-muted-foreground">
        {Math.round(value * 100)}% confidence
      </span>
    </div>
  );
}

/* ---------- states ---------- */

export function LoadingState({ rows = 4, label = "Loading" }: { rows?: number; label?: string }) {
  return (
    <div className="space-y-3" role="status" aria-live="polite" aria-busy="true">
      <span className="sr-only">{label}</span>
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-16 w-full rounded-lg" />
      ))}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message?: string; onRetry?: () => void }) {
  return (
    <div
      role="alert"
      className="flex flex-col items-start gap-3 rounded-xl border border-destructive/30 bg-destructive/5 p-6"
    >
      <div className="flex items-center gap-2 text-destructive">
        <AlertTriangle className="size-4" aria-hidden />
        <p className="text-sm font-medium">Something went wrong</p>
      </div>
      <p className="text-sm text-muted-foreground">{message ?? "We couldn't load this data."}</p>
      {onRetry ? (
        <Button size="sm" variant="outline" onClick={onRetry}>
          <RefreshCw className="size-3.5" aria-hidden /> Retry
        </Button>
      ) : null}
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-border px-6 py-14 text-center">
      <Inbox className="size-5 text-muted-foreground" aria-hidden />
      <p className="text-sm font-medium">{title}</p>
      <p className="max-w-sm text-sm text-muted-foreground">{description}</p>
      {action}
    </div>
  );
}

export function PermissionDenied({ what }: { what: string }) {
  return (
    <div className="flex items-start gap-3 rounded-xl border border-warning/30 bg-warning/5 p-5">
      <ShieldAlert className="mt-0.5 size-4 text-warning" aria-hidden />
      <div>
        <p className="text-sm font-medium">Permission denied</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Your role can view {what} but cannot change it. Ask a workspace owner for approval rights.
        </p>
      </div>
    </div>
  );
}

export function ProcessingRow({ label }: { label: string }) {
  return (
    <div
      className="flex items-center gap-2 text-xs text-muted-foreground"
      role="status"
      aria-live="polite"
    >
      <Loader2 className="size-3.5 animate-spin" aria-hidden />
      {label}
    </div>
  );
}

/** Standard loading / error / empty wrapper for a React Query result. */
export function QueryBoundary<T>({
  query,
  children,
  emptyTitle = "Nothing here yet",
  emptyDescription = "Data will appear here as soon as Sarthi has something to show.",
  isEmpty,
  rows,
}: {
  query: {
    data: T | undefined;
    isPending: boolean;
    isError: boolean;
    error?: unknown;
    refetch: () => void;
  };
  children: (data: T) => ReactNode;
  emptyTitle?: string;
  emptyDescription?: string;
  isEmpty?: (data: T) => boolean;
  rows?: number;
}) {
  if (query.isPending) return <LoadingState rows={rows} />;
  if (query.isError)
    return (
      <ErrorState
        message={(query.error as Error | undefined)?.message}
        onRetry={() => query.refetch()}
      />
    );
  const data = query.data as T;
  if (isEmpty?.(data)) return <EmptyState title={emptyTitle} description={emptyDescription} />;
  return <>{children(data)}</>;
}
