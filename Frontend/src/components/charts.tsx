import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { MetricPoint } from "@/lib/types";

const axis = {
  stroke: "var(--color-muted-foreground)",
  fontSize: 11,
  tickLine: false,
  axisLine: false,
};

const tooltipStyle = {
  background: "var(--color-popover)",
  border: "1px solid var(--color-border-strong)",
  borderRadius: 10,
  fontSize: 12,
  color: "var(--color-popover-foreground)",
};

const compact = (v: number) =>
  new Intl.NumberFormat("en-IN", { notation: "compact", maximumFractionDigits: 1 }).format(v);

export function RevenueAreaChart({ data, height = 280 }: { data: MetricPoint[]; height?: number }) {
  return (
    <div
      style={{ height }}
      role="img"
      aria-label="Total revenue and AI-attributed revenue over time"
    >
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="gRevenue" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--color-chart-3)" stopOpacity={0.45} />
              <stop offset="100%" stopColor="var(--color-chart-3)" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="gAi" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--color-chart-1)" stopOpacity={0.5} />
              <stop offset="100%" stopColor="var(--color-chart-1)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="var(--color-border)" vertical={false} />
          <XAxis dataKey="date" {...axis} />
          <YAxis tickFormatter={compact} width={48} {...axis} />
          <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => compact(v)} />
          <Area
            type="monotone"
            dataKey="revenue"
            name="Revenue"
            stroke="var(--color-chart-3)"
            fill="url(#gRevenue)"
            strokeWidth={2}
          />
          <Area
            type="monotone"
            dataKey="aiRevenue"
            name="AI-attributed"
            stroke="var(--color-chart-1)"
            fill="url(#gAi)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function MiniLineChart({
  data,
  dataKey,
  label,
  height = 160,
}: {
  data: MetricPoint[];
  dataKey: keyof MetricPoint;
  label: string;
  height?: number;
}) {
  return (
    <div style={{ height }} role="img" aria-label={label}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="var(--color-border)" vertical={false} />
          <XAxis dataKey="date" {...axis} />
          <YAxis tickFormatter={compact} width={44} {...axis} />
          <Tooltip contentStyle={tooltipStyle} />
          <Line
            type="monotone"
            dataKey={dataKey as string}
            stroke="var(--color-chart-2)"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function CategoryBarChart({
  data,
  height = 240,
  label,
}: {
  data: { name: string; value: number }[];
  height?: number;
  label: string;
}) {
  const palette = [
    "var(--color-chart-1)",
    "var(--color-chart-2)",
    "var(--color-chart-3)",
    "var(--color-chart-4)",
    "var(--color-chart-5)",
  ];
  return (
    <div style={{ height }} role="img" aria-label={label}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="var(--color-border)" vertical={false} />
          <XAxis dataKey="name" {...axis} interval={0} />
          <YAxis tickFormatter={compact} width={48} {...axis} />
          <Tooltip
            contentStyle={tooltipStyle}
            cursor={{ fill: "var(--color-muted)" }}
            formatter={(v: number) => compact(v)}
          />
          <Bar dataKey="value" radius={[6, 6, 0, 0]}>
            {data.map((_, i) => (
              <Cell key={i} fill={palette[i % palette.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
