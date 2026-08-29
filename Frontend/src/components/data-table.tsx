import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface Column<T> {
  key: string;
  header: string;
  align?: "left" | "right";
  className?: string;
  cell: (row: T) => ReactNode;
  /** Shown as the label when the table collapses to cards on mobile. */
  mobileLabel?: string;
  primary?: boolean;
}

export function DataTable<T extends { id: string }>({
  caption,
  columns,
  rows,
  onRowClick,
}: {
  caption: string;
  columns: Column<T>[];
  rows: T[];
  onRowClick?: (row: T) => void;
}) {
  return (
    <>
      {/* Desktop table */}
      <div className="hidden overflow-x-auto md:block">
        <table className="w-full border-collapse text-sm">
          <caption className="sr-only">{caption}</caption>
          <thead>
            <tr className="border-b border-border">
              {columns.map((c) => (
                <th
                  key={c.key}
                  scope="col"
                  className={cn(
                    "whitespace-nowrap px-3 py-2.5 text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground",
                    c.align === "right" ? "text-right" : "text-left",
                  )}
                >
                  {c.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.id}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                tabIndex={onRowClick ? 0 : undefined}
                onKeyDown={
                  onRowClick
                    ? (e) => {
                        if (e.key === "Enter") onRowClick(row);
                      }
                    : undefined
                }
                className={cn(
                  "border-b border-border/60 transition-colors last:border-0",
                  onRowClick &&
                    "cursor-pointer hover:bg-surface-raised focus:bg-surface-raised focus:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                )}
              >
                {columns.map((c) => (
                  <td
                    key={c.key}
                    className={cn(
                      "px-3 py-3 align-middle",
                      c.align === "right" ? "text-right" : "text-left",
                      c.className,
                    )}
                  >
                    {c.cell(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <ul className="space-y-3 md:hidden">
        {rows.map((row) => (
          <li key={row.id}>
            <button
              type="button"
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              className="w-full rounded-lg border border-border bg-surface p-4 text-left"
            >
              <dl className="space-y-2">
                {columns.map((c) => (
                  <div key={c.key} className="flex items-baseline justify-between gap-4">
                    <dt className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
                      {c.mobileLabel ?? c.header}
                    </dt>
                    <dd className={cn("text-sm", c.primary && "font-medium")}>{c.cell(row)}</dd>
                  </div>
                ))}
              </dl>
            </button>
          </li>
        ))}
      </ul>
    </>
  );
}
