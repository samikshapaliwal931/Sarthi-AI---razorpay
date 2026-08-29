import { ArrowDownRight, ArrowUpRight, Info } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { Counter, StaggerItem } from "@/components/primitives";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

export function MetricCard({
  label,
  value,
  format,
  delta,
  suffix,
  hint,
}: {
  label: string;
  value: number;
  format?: (v: number) => string;
  delta?: number;
  suffix?: string;
  hint?: string;
}) {
  const positive = (delta ?? 0) >= 0;
  return (
    <StaggerItem className="group relative rounded-xl border border-border bg-card p-5 transition-colors hover:border-border-strong">
      <div className="flex items-center gap-1.5">
        <p className="eyebrow">{label}</p>
        {hint ? (
          <Tooltip>
            <TooltipTrigger
              aria-label={`About ${label}`}
              className="text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring"
            >
              <Info className="size-3" aria-hidden />
            </TooltipTrigger>
            <TooltipContent className="max-w-xs text-xs leading-relaxed">{hint}</TooltipContent>
          </Tooltip>
        ) : null}
      </div>
      <p className="mt-4 text-2xl font-semibold tracking-tight md:text-[1.75rem]">
        <Counter value={value} format={format} />
        {suffix}
      </p>
      {delta !== undefined ? (
        <p
          className={cn(
            "mt-2 inline-flex items-center gap-1 text-xs",
            positive ? "text-positive" : "text-destructive",
          )}
        >
          {positive ? (
            <ArrowUpRight className="size-3.5" aria-hidden />
          ) : (
            <ArrowDownRight className="size-3.5" aria-hidden />
          )}
          <span className="tabular">{Math.abs(delta).toFixed(1)}%</span>
          <span className="text-muted-foreground">vs prior period</span>
        </p>
      ) : null}
    </StaggerItem>
  );
}

export function StatLine({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-6 border-b border-border/60 py-2.5 last:border-0">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="text-sm font-medium">{value}</dd>
    </div>
  );
}
