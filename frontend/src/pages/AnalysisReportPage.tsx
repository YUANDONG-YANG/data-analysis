import { type ReactNode, useCallback, useEffect, useMemo, useState } from "react";
import Papa from "papaparse";
import { Link, Navigate } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { DataPreviewTable } from "../components/DataPreviewTable";
import { useFinalOutputStatus } from "../hooks/useFinalOutputStatus";
import { usePipelineRuntime } from "../hooks/usePipelineRuntime";
import type { OutputPreview } from "../types/pipelineRun";

type FinalDataRow = {
  month: string;
  community_name: string;
  builder: string;
  actual_sales: number;
  target_sales: number;
  variance: number;
  crm_leads: number;
  web_traffic: number;
  estimated_revenue: number;
  achievement_rate: number;
  estimated_avg_sale_price: number;
  conversion_rate: number;
  traffic_to_sales_rate: number;
};

const CHART_COLORS = ["#38bdf8", "#34d399", "#f59e0b", "#a78bfa", "#fb7185", "#22d3ee"];
const COMPACT_FORMATTER = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 1,
});
const DECIMAL_FORMATTER = new Intl.NumberFormat("en-US", {
  maximumFractionDigits: 1,
});

type TooltipKind = "number" | "currency" | "percent";

function asNumber(value: unknown): number {
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function ratePercent(numerator: number, denominator: number): number {
  return denominator > 0 ? (numerator / denominator) * 100 : 0;
}

function currencyCompact(value: number): string {
  return `$${COMPACT_FORMATTER.format(value)}`;
}

function compact(value: number): string {
  return COMPACT_FORMATTER.format(value);
}

function percent(value: number): string {
  return `${DECIMAL_FORMATTER.format(value)}%`;
}

function formatTooltipValue(value: unknown, kind: TooltipKind): string {
  const numeric = asNumber(value);
  if (kind === "currency") return currencyCompact(numeric);
  if (kind === "percent") return percent(numeric);
  return DECIMAL_FORMATTER.format(numeric);
}

function parseRow(row: Record<string, string>): FinalDataRow {
  return {
    month: row.month ?? "",
    community_name: row.community_name ?? "",
    builder: row.builder ?? "",
    actual_sales: asNumber(row.actual_sales),
    target_sales: asNumber(row.target_sales),
    variance: asNumber(row.variance),
    crm_leads: asNumber(row.crm_leads),
    web_traffic: asNumber(row.web_traffic),
    estimated_revenue: asNumber(row.estimated_revenue),
    achievement_rate: asNumber(row.achievement_rate),
    estimated_avg_sale_price: asNumber(row.estimated_avg_sale_price),
    conversion_rate: asNumber(row.conversion_rate),
    traffic_to_sales_rate: asNumber(row.traffic_to_sales_rate),
  };
}

function StatCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint: string;
}) {
  return (
    <div className="rounded-3xl border border-white/[0.06] bg-canvas-elevated/50 p-5 shadow-card">
      <p className="text-[0.7rem] font-semibold uppercase tracking-[0.24em] text-ink-faint">{label}</p>
      <p className="mt-3 text-2xl font-semibold text-ink">{value}</p>
      <p className="mt-2 text-sm leading-relaxed text-ink-muted">{hint}</p>
    </div>
  );
}

function ChartCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-3xl border border-white/[0.06] bg-canvas-elevated/40 p-5 shadow-card">
      <div className="mb-5">
        <h2 className="text-lg font-semibold text-ink">{title}</h2>
        <p className="mt-1 text-sm leading-relaxed text-ink-muted">{subtitle}</p>
      </div>
      {children}
    </section>
  );
}

function ChartTooltip({
  active,
  payload,
  label,
  kind,
}: {
  active?: boolean;
  payload?: Array<{ name?: string; value?: unknown; color?: string }>;
  label?: string;
  kind: TooltipKind;
}) {
  if (!active || !payload?.length) return null;

  return (
    <div className="rounded-2xl border border-white/[0.08] bg-slate-950/95 px-4 py-3 shadow-xl">
      {label && <p className="mb-2 font-mono text-sm text-ink">{label}</p>}
      <div className="space-y-1.5">
        {payload.map((entry) => (
          <div key={entry.name} className="flex items-center gap-2 text-sm">
            <span
              className="h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: entry.color ?? "#94a3b8" }}
            />
            <span className="text-ink-muted">{entry.name}:</span>
            <span className="font-medium text-ink">{formatTooltipValue(entry.value, kind)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function AnalysisReportPage() {
  const [rows, setRows] = useState<FinalDataRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const runtimeState = usePipelineRuntime();
  const { status: finalOutputStatus, loading: finalOutputLoading } = useFinalOutputStatus();

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/final-data.csv");
      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as
          | { hint?: string; message?: string }
          | null;
        throw new Error(
          payload?.hint ??
            payload?.message ??
            "No final output CSV found yet. Run the backend pipeline to generate data/gold/final_dataframe.csv.",
        );
      }

      const text = await response.text();
      const parsed = Papa.parse<Record<string, string>>(text, {
        header: true,
        skipEmptyLines: true,
      });
      const nextRows: FinalDataRow[] = parsed.data
        .map(parseRow)
        .filter((row: FinalDataRow) => row.month && row.community_name)
        .sort((a: FinalDataRow, b: FinalDataRow) =>
          a.month === b.month
            ? a.community_name.localeCompare(b.community_name)
            : b.month.localeCompare(a.month),
        );

      setRows(nextRows);
    } catch (err) {
      setRows([]);
      setError(err instanceof Error ? err.message : "Failed to load the final output CSV.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  useEffect(() => {
    if (runtimeState.status.runtime?.status === "completed") {
      void loadData();
    }
  }, [loadData, runtimeState.status.runtime?.status, runtimeState.status.runtime?.updated_at]);

  const latestActualMonth = useMemo(() => {
    const candidates = rows
      .filter((row) => row.actual_sales > 0)
      .map((row) => row.month)
      .sort((a, b) => a.localeCompare(b));
    return candidates.length ? candidates[candidates.length - 1] : null;
  }, [rows]);

  const currentRows = useMemo(
    () => (latestActualMonth ? rows.filter((row) => row.month <= latestActualMonth) : rows),
    [latestActualMonth, rows],
  );
  const futureRows = useMemo(
    () => (latestActualMonth ? rows.filter((row) => row.month > latestActualMonth) : []),
    [latestActualMonth, rows],
  );

  const summarizeRows = useCallback((items: FinalDataRow[]) => {
    const communities = new Set(items.map((row) => row.community_name));
    const builders = new Set(items.map((row) => row.builder));
    const actualSales = items.reduce((sum, row) => sum + row.actual_sales, 0);
    const targetSales = items.reduce((sum, row) => sum + row.target_sales, 0);
    const revenue = items.reduce((sum, row) => sum + row.estimated_revenue, 0);
    const leads = items.reduce((sum, row) => sum + row.crm_leads, 0);
    const traffic = items.reduce((sum, row) => sum + row.web_traffic, 0);

    return {
      rows: items.length,
      communities: communities.size,
      builders: builders.size,
      actualSales,
      targetSales,
      revenue,
      leads,
      traffic,
      achievementRatePct: ratePercent(actualSales, targetSales),
      conversionRatePct: ratePercent(actualSales, leads),
      trafficToSalesPct: ratePercent(actualSales, traffic),
    };
  }, []);

  const totals = useMemo(() => summarizeRows(rows), [rows, summarizeRows]);
  const currentTotals = useMemo(() => summarizeRows(currentRows), [currentRows, summarizeRows]);
  const futureTotals = useMemo(() => summarizeRows(futureRows), [futureRows, summarizeRows]);

  const buildMonthlySeries = useCallback((items: FinalDataRow[]) => {
    const grouped = new Map<
      string,
      {
        month: string;
        actual_sales: number;
        target_sales: number;
        estimated_revenue: number;
        crm_leads: number;
        web_traffic: number;
      }
    >();

    for (const row of items) {
      const current = grouped.get(row.month) ?? {
        month: row.month,
        actual_sales: 0,
        target_sales: 0,
        estimated_revenue: 0,
        crm_leads: 0,
        web_traffic: 0,
      };
      current.actual_sales += row.actual_sales;
      current.target_sales += row.target_sales;
      current.estimated_revenue += row.estimated_revenue;
      current.crm_leads += row.crm_leads;
      current.web_traffic += row.web_traffic;
      grouped.set(row.month, current);
    }

    return [...grouped.values()]
      .sort((a, b) => a.month.localeCompare(b.month))
      .map((row) => ({
        ...row,
        achievement_rate_percent: ratePercent(row.actual_sales, row.target_sales),
        conversion_rate_percent: ratePercent(row.actual_sales, row.crm_leads),
        traffic_to_sales_rate_percent: ratePercent(row.actual_sales, row.web_traffic),
      }));
  }, []);

  const monthlySeries = useMemo(() => buildMonthlySeries(currentRows), [buildMonthlySeries, currentRows]);
  const forecastMonthlySeries = useMemo(
    () =>
      buildMonthlySeries(futureRows).map((row) => ({
        month: row.month,
        target_sales: row.target_sales,
      })),
    [buildMonthlySeries, futureRows],
  );

  const topCommunities = useMemo(() => {
    const grouped = new Map<
      string,
      { community_name: string; actual_sales: number; target_sales: number; estimated_revenue: number }
    >();

    for (const row of currentRows) {
      const current = grouped.get(row.community_name) ?? {
        community_name: row.community_name,
        actual_sales: 0,
        target_sales: 0,
        estimated_revenue: 0,
      };
      current.actual_sales += row.actual_sales;
      current.target_sales += row.target_sales;
      current.estimated_revenue += row.estimated_revenue;
      grouped.set(row.community_name, current);
    }

    return [...grouped.values()]
      .sort((a, b) => b.actual_sales - a.actual_sales)
      .slice(0, 8);
  }, [currentRows]);

  const builderSeries = useMemo(() => {
    const grouped = new Map<
      string,
      {
        builder: string;
        actual_sales: number;
        target_sales: number;
        estimated_revenue: number;
        crm_leads: number;
        web_traffic: number;
      }
    >();

    for (const row of currentRows) {
      const current = grouped.get(row.builder) ?? {
        builder: row.builder,
        actual_sales: 0,
        target_sales: 0,
        estimated_revenue: 0,
        crm_leads: 0,
        web_traffic: 0,
      };
      current.actual_sales += row.actual_sales;
      current.target_sales += row.target_sales;
      current.estimated_revenue += row.estimated_revenue;
      current.crm_leads += row.crm_leads;
      current.web_traffic += row.web_traffic;
      grouped.set(row.builder, current);
    }

    return [...grouped.values()]
      .sort((a, b) => a.builder.localeCompare(b.builder))
      .map((row) => ({
        ...row,
        achievement_rate_percent: ratePercent(row.actual_sales, row.target_sales),
        conversion_rate_percent: ratePercent(row.actual_sales, row.crm_leads),
      }));
  }, [currentRows]);

  const builderRevenueShare = useMemo(
    () =>
      builderSeries.map((row, idx) => ({
        name: `Builder ${row.builder.toUpperCase()}`,
        value: row.estimated_revenue,
        fill: CHART_COLORS[idx % CHART_COLORS.length],
      })),
    [builderSeries],
  );

  const preview = useMemo<OutputPreview>(
    () => ({
      columns: [
        "month",
        "community_name",
        "builder",
        "actual_sales",
        "target_sales",
        "variance",
        "crm_leads",
        "web_traffic",
        "estimated_revenue",
        "achievement_rate",
        "conversion_rate",
        "traffic_to_sales_rate",
      ],
      rows: rows.map((row) => ({
        month: row.month,
        community_name: row.community_name,
        builder: row.builder,
        actual_sales: row.actual_sales,
        target_sales: row.target_sales,
        variance: row.variance,
        crm_leads: row.crm_leads,
        web_traffic: row.web_traffic,
        estimated_revenue: row.estimated_revenue,
        achievement_rate: percent(ratePercent(row.actual_sales, row.target_sales)),
        conversion_rate: percent(ratePercent(row.actual_sales, row.crm_leads)),
        traffic_to_sales_rate: percent(ratePercent(row.actual_sales, row.web_traffic)),
      })),
      truncated: false,
      total_rows: rows.length,
      preview_rows: rows.length,
    }),
    [rows],
  );

  const qualityAlerts = useMemo(() => {
    const alerts: { title: string; detail: string }[] = [];
    if (!currentRows.length) return alerts;

    const communityMedians = new Map<string, number>();
    for (const [community, items] of Object.entries(
      currentRows.reduce<Record<string, number[]>>((acc, row) => {
        if (row.actual_sales > 0) {
          acc[row.community_name] = acc[row.community_name] ?? [];
          acc[row.community_name].push(row.estimated_avg_sale_price);
        }
        return acc;
      }, {}),
    )) {
      const sorted = [...items].sort((a, b) => a - b);
      communityMedians.set(community, sorted[Math.floor(sorted.length / 2)] ?? 0);
    }

    const maxPriceRow = [...currentRows]
      .filter((row) => row.actual_sales > 0)
      .sort((a, b) => b.estimated_avg_sale_price - a.estimated_avg_sale_price)[0];
    if (maxPriceRow) {
      const median = communityMedians.get(maxPriceRow.community_name) ?? 0;
      if (median > 0 && maxPriceRow.estimated_avg_sale_price > median * 2) {
        alerts.push({
          title: "Revenue outlier needs review",
          detail: `${maxPriceRow.month} ${maxPriceRow.community_name} has avg sale price ${currencyCompact(
            maxPriceRow.estimated_avg_sale_price,
          )}, which is well above that community's normal range.`,
        });
      }
    }

    const salesWithoutTarget = currentRows.filter(
      (row) => row.actual_sales > 0 && row.target_sales === 0,
    ).length;
    if (salesWithoutTarget > 0) {
      alerts.push({
        title: "Target coverage is incomplete",
        detail: `${salesWithoutTarget} current-period rows have actual sales but no target, so achievement should be interpreted within a filtered time window.`,
      });
    }

    const trafficGaps = [...new Set(
      currentRows
        .filter((row) => row.actual_sales > 0 && row.web_traffic === 0)
        .map((row) => row.community_name),
    )];
    if (trafficGaps.length) {
      alerts.push({
        title: "Traffic coverage is missing for some communities",
        detail: `${trafficGaps.join(", ")} currently show sales activity without matching web traffic, which affects funnel-efficiency comparisons.`,
      });
    }

    return alerts;
  }, [currentRows]);

  if (!finalOutputLoading && !finalOutputStatus.available && !runtimeState.status.running) {
    return <Navigate to="/" replace />;
  }

  return (
    <article className="mx-auto max-w-4xl">
      <header className="border-b border-white/[0.06] pb-8">
        <p className="text-[0.65rem] font-semibold uppercase tracking-[0.35em] text-accent">
          Output analysis
        </p>
        <h1 className="mt-2 text-balance font-sans text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
          Final output dashboard
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-ink-muted">
          This page turns <code className="text-ink">final_dataframe.csv</code> into charts so the
          final pipeline output can be presented directly in the front-end.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => void runtimeState.startRun()}
            disabled={runtimeState.status.running || runtimeState.starting}
            className="rounded-full border border-amber-400/40 bg-amber-400/10 px-5 py-2.5 text-sm font-semibold text-amber-100 transition hover:border-amber-300/60 hover:bg-amber-400/15 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {runtimeState.status.running || runtimeState.starting
              ? "Pipeline running..."
              : "Regenerate final output"}
          </button>
          <button
            type="button"
            onClick={() => void loadData()}
            className="rounded-full border border-cyan-500/40 bg-cyan-500/10 px-5 py-2.5 text-sm font-semibold text-cyan-100 transition hover:border-cyan-400/60 hover:bg-cyan-500/15"
          >
            Refresh dashboard
          </button>
          <Link
            to="/live-demo"
            className="inline-flex items-center justify-center rounded-full border border-emerald-500/40 bg-emerald-500/10 px-5 py-2.5 text-sm font-semibold text-emerald-100 transition hover:border-emerald-400/60 hover:bg-emerald-500/15"
          >
            Open live demo
          </Link>
        </div>
      </header>

      {loading && (
        <div className="mt-10 rounded-3xl border border-white/[0.06] bg-canvas-elevated/40 px-6 py-16 text-center text-ink-muted">
          Loading output charts...
        </div>
      )}

      {!loading && error && (
        <section className="mt-10 rounded-3xl border border-amber-500/20 bg-amber-950/20 p-6">
          <h2 className="text-xl font-semibold text-amber-100">Final output not available</h2>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-amber-100/85">{error}</p>
          <p className="mt-4 text-sm text-ink-muted">
            Run the backend once, then refresh this page to generate the chart dashboard from the
            final CSV output.
          </p>
        </section>
      )}

      {!loading && !error && rows.length > 0 && (
        <div className="mt-10 space-y-8">
          <section className="rounded-3xl border border-cyan-500/20 bg-cyan-950/15 p-5 shadow-card">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-200/80">
              Dashboard metric definition
            </p>
            <p className="mt-2 max-w-3xl text-sm leading-relaxed text-cyan-50/90">
              All rate charts below are recomputed from base numerators and denominators and displayed
              as percentages. This avoids mixing CSV fields that use different storage styles, such as
              percentage values for `achievement_rate` / `conversion_rate` and ratio values for
              `traffic_to_sales_rate`.
            </p>
          </section>

          {qualityAlerts.length > 0 && (
            <section className="rounded-3xl border border-amber-500/20 bg-amber-950/15 p-5 shadow-card">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-amber-200/80">
                Data quality alerts
              </p>
              <div className="mt-4 grid gap-3 lg:grid-cols-3">
                {qualityAlerts.map((alert) => (
                  <div
                    key={alert.title}
                    className="rounded-2xl border border-amber-400/15 bg-slate-950/35 px-4 py-4"
                  >
                    <p className="text-sm font-semibold text-amber-100">{alert.title}</p>
                    <p className="mt-2 text-sm leading-relaxed text-amber-50/80">{alert.detail}</p>
                  </div>
                ))}
              </div>
            </section>
          )}

          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              label="Current actual sales"
              value={DECIMAL_FORMATTER.format(currentTotals.actualSales)}
              hint={`Closed-sales period through ${latestActualMonth ?? "latest available month"}.`}
            />
            <StatCard
              label="Current target sales"
              value={DECIMAL_FORMATTER.format(currentTotals.targetSales)}
              hint="Targets in the same operating window as the actual sales shown above."
            />
            <StatCard
              label="Current achievement"
              value={percent(currentTotals.achievementRatePct)}
              hint="Actual sales divided by target sales for the current operating period only."
            />
            <StatCard
              label="Forecast target volume"
              value={DECIMAL_FORMATTER.format(futureTotals.targetSales)}
              hint={`${futureTotals.rows} future planning rows kept separate from current performance.`}
            />
          </section>

          <section className="grid gap-6 lg:grid-cols-2">
            <ChartCard
              title="Current-period sales vs target"
              subtitle="This chart excludes future target-only months so actual performance and target volume share the same time window."
            >
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={monthlySeries}>
                    <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
                    <XAxis
                      dataKey="month"
                      stroke="#94a3b8"
                      tick={{ fontSize: 12 }}
                      angle={-35}
                      textAnchor="end"
                      height={60}
                    />
                    <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
                    <Tooltip
                      content={<ChartTooltip kind="number" />}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="actual_sales"
                      name="Actual sales"
                      stroke="#38bdf8"
                      strokeWidth={2.5}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="target_sales"
                      name="Target sales"
                      stroke="#34d399"
                      strokeWidth={2.5}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </ChartCard>

            <ChartCard
              title="Forecast targets"
              subtitle="Future planning months are shown separately from current operating results to avoid mixing forecast demand with historical sales."
            >
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={forecastMonthlySeries}>
                    <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
                    <XAxis
                      dataKey="month"
                      stroke="#94a3b8"
                      tick={{ fontSize: 12 }}
                      angle={-35}
                      textAnchor="end"
                      height={60}
                    />
                    <YAxis
                      stroke="#94a3b8"
                      tick={{ fontSize: 12 }}
                    />
                    <Tooltip
                      content={<ChartTooltip kind="number" />}
                    />
                    <Legend />
                    <Bar
                      dataKey="target_sales"
                      name="Forecast target sales"
                      fill="#34d399"
                      radius={[6, 6, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </ChartCard>
          </section>

          <section className="grid gap-6 lg:grid-cols-2">
            <ChartCard
              title="Current-period achievement rate"
              subtitle="Target attainment stays on its own chart so it can use a wider percentage scale without compressing funnel-efficiency metrics."
            >
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={monthlySeries}>
                    <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
                    <XAxis
                      dataKey="month"
                      stroke="#94a3b8"
                      tick={{ fontSize: 12 }}
                      angle={-35}
                      textAnchor="end"
                      height={60}
                    />
                    <YAxis
                      stroke="#94a3b8"
                      tick={{ fontSize: 12 }}
                      tickFormatter={(value) => `${value}%`}
                    />
                    <Tooltip content={<ChartTooltip kind="percent" />} />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="achievement_rate_percent"
                      name="Achievement rate"
                      stroke="#f59e0b"
                      strokeWidth={2.5}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </ChartCard>

            <ChartCard
              title="Monthly funnel efficiency"
              subtitle="Lead conversion and traffic-to-sales are both shown as weighted percentage points across the current operating period."
            >
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={monthlySeries}>
                    <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
                    <XAxis
                      dataKey="month"
                      stroke="#94a3b8"
                      tick={{ fontSize: 12 }}
                      angle={-35}
                      textAnchor="end"
                      height={60}
                    />
                    <YAxis
                      stroke="#94a3b8"
                      tick={{ fontSize: 12 }}
                      tickFormatter={(value) => `${value}%`}
                    />
                    <Tooltip
                      content={<ChartTooltip kind="percent" />}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="conversion_rate_percent"
                      name="CRM conversion rate"
                      stroke="#a78bfa"
                      strokeWidth={2.5}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="traffic_to_sales_rate_percent"
                      name="Traffic to sales rate"
                      stroke="#22d3ee"
                      strokeWidth={2.5}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </ChartCard>
          </section>

          <section className="grid gap-6 lg:grid-cols-2">
            <ChartCard
              title="Sales conversion funnel"
              subtitle="Shows conversion efficiency from web traffic → CRM leads → actual sales (current period only)."
            >
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart 
                    data={[
                      { 
                        stage: 'Web Traffic', 
                        count: currentTotals.traffic,
                        rate: 100
                      },
                      { 
                        stage: 'CRM Leads', 
                        count: currentTotals.leads,
                        rate: currentTotals.traffic > 0 ? (currentTotals.leads / currentTotals.traffic) * 100 : 0
                      },
                      { 
                        stage: 'Actual Sales', 
                        count: currentTotals.actualSales,
                        rate: currentTotals.traffic > 0 ? (currentTotals.actualSales / currentTotals.traffic) * 100 : 0
                      }
                    ]}
                    layout="vertical"
                    margin={{ left: 20, right: 40 }}
                  >
                    <CartesianGrid stroke="rgba(255,255,255,0.08)" horizontal={false} />
                    <XAxis 
                      type="number" 
                      stroke="#94a3b8" 
                      tick={{ fontSize: 12 }}
                      tickFormatter={(value) => compact(value)}
                    />
                    <YAxis 
                      type="category" 
                      dataKey="stage" 
                      stroke="#94a3b8" 
                      width={100}
                      tick={{ fontSize: 12 }}
                    />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (!active || !payload || !payload.length) return null;
                        const data = payload[0].payload;
                        return (
                          <div className="rounded-lg border border-white/10 bg-canvas-elevated/95 px-3 py-2 shadow-xl backdrop-blur-sm">
                            <p className="mb-1 text-xs font-medium text-ink">{data.stage}</p>
                            <p className="text-sm font-semibold text-accent-glow">
                              {DECIMAL_FORMATTER.format(data.count)} ({percent(data.rate)})
                            </p>
                          </div>
                        );
                      }}
                    />
                    <Bar dataKey="count" fill="#a78bfa" radius={[0, 6, 6, 0]}>
                      {[0, 1, 2].map((index) => (
                        <Cell key={index} fill={['#22d3ee', '#a78bfa', '#34d399'][index]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </ChartCard>

            <ChartCard
              title="Top communities by actual sales"
              subtitle="Best for showing which communities contribute the most volume in the final integrated output."
            >
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={topCommunities} layout="vertical" margin={{ left: 12, right: 12 }}>
                    <CartesianGrid stroke="rgba(255,255,255,0.08)" horizontal={false} />
                    <XAxis
                      type="number"
                      stroke="#94a3b8"
                      tick={{ fontSize: 12 }}
                      tickFormatter={(value) => compact(value)}
                    />
                    <YAxis
                      type="category"
                      dataKey="community_name"
                      stroke="#94a3b8"
                      width={120}
                      tick={{ fontSize: 12 }}
                    />
                    <Tooltip
                      content={<ChartTooltip kind="number" />}
                    />
                    <Legend />
                    <Bar dataKey="actual_sales" name="Actual sales" fill="#38bdf8" radius={[0, 6, 6, 0]} />
                    <Bar dataKey="target_sales" name="Target sales" fill="#34d399" radius={[0, 6, 6, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </ChartCard>
            <ChartCard
              title="Builder sales and target"
              subtitle="Builder comparison is based on the current operating period only, so future planning targets do not distort the columns."
            >
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={builderSeries}>
                    <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
                    <XAxis dataKey="builder" stroke="#94a3b8" tick={{ fontSize: 12 }} />
                    <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
                    <Tooltip
                      content={<ChartTooltip kind="number" />}
                    />
                    <Legend />
                    <Bar dataKey="actual_sales" name="Actual sales" fill="#38bdf8" radius={[6, 6, 0, 0]} />
                    <Bar dataKey="target_sales" name="Target sales" fill="#34d399" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </ChartCard>

            <ChartCard
              title="Revenue share by builder"
              subtitle="Useful when presenting which builder contributes most of the modeled revenue."
            >
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={builderRevenueShare}
                      dataKey="value"
                      nameKey="name"
                      innerRadius={72}
                      outerRadius={108}
                      paddingAngle={2}
                    >
                      {builderRevenueShare.map((entry, index) => (
                        <Cell key={entry.name} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      content={<ChartTooltip kind="currency" />}
                    />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </ChartCard>
          </section>

          <section className="grid gap-4 sm:grid-cols-3">
            <StatCard
              label="Lead conversion"
              value={percent(currentTotals.conversionRatePct)}
              hint="Weighted from current-period actual sales divided by total CRM leads."
            />
            <StatCard
              label="Traffic to sales"
              value={percent(currentTotals.trafficToSalesPct)}
              hint="Weighted from current-period actual sales divided by total web traffic."
            />
            <StatCard
              label="Coverage"
              value={`${totals.communities} communities / ${totals.builders} builders`}
              hint={`${totals.rows} monthly rows in the full CSV, including current and forecast periods.`}
            />
          </section>

          <section className="rounded-3xl border border-white/[0.06] bg-canvas-elevated/40 p-5 shadow-card">
            <div className="mb-5">
              <h2 className="text-lg font-semibold text-ink">Final output preview</h2>
              <p className="mt-1 text-sm leading-relaxed text-ink-muted">
                A tabular preview from <code className="text-ink">final_dataframe.csv</code>. Rate
                columns are displayed here using the same percentage definition as the dashboard charts.
              </p>
            </div>
            <DataPreviewTable preview={preview} title="Final CSV preview" pageSize={20} />
          </section>
        </div>
      )}
    </article>
  );
}
