import { useEffect, useMemo, useState } from "react";
import type { OutputPreview } from "../types/pipelineRun";

const DATE_SORT_COLUMN_PRIORITY = [
  "SALE_CONTRACT_DATE",
  "CONTRACT_DATE",
  "SALE_DATE",
  "LEAD_DATE",
  "SESSION_DATE",
  "VISIT_DATE",
  "year_month",
  "YEAR_MONTH",
  "month",
  "MONTH",
  "DATE",
  "date",
  "TIMESTAMP",
  "CREATED_AT",
  "UPDATED_AT",
];

function parseSortableTime(value: unknown): number | null {
  if (value === null || value === undefined) return null;
  if (typeof value === "number" && Number.isFinite(value)) {
    if (value > 1e12) return value;
    if (value > 1e9) return value * 1000;
  }
  const s = String(value).trim();
  if (!s) return null;
  let t = Date.parse(s);
  if (!Number.isNaN(t)) return t;
  if (/^\d{4}-\d{2}$/.test(s)) {
    t = Date.parse(`${s}-01`);
    if (!Number.isNaN(t)) return t;
  }
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) {
    t = Date.parse(s);
    if (!Number.isNaN(t)) return t;
  }
  return null;
}

function pickPrimaryDateColumn(columns: string[]): string | null {
  const byUpper = new Map(columns.map((c) => [c.toUpperCase(), c] as const));
  for (const key of DATE_SORT_COLUMN_PRIORITY) {
    const found = byUpper.get(key.toUpperCase());
    if (found) return found;
  }
  for (const c of columns) {
    const u = c.toUpperCase();
    if (/_DATE$/.test(u) || u.endsWith("_AT") || u.includes("TIMESTAMP")) return c;
    if (u === "DATE" || u === "MONTH" || u === "YEAR_MONTH") return c;
  }
  return null;
}

function sortRowsByPrimaryDateDesc(rows: Record<string, unknown>[], dateCol: string): Record<string, unknown>[] {
  return [...rows].sort((a, b) => {
    const ta = parseSortableTime(a[dateCol]);
    const tb = parseSortableTime(b[dateCol]);
    if (ta != null && tb != null && ta !== tb) return tb - ta;
    if (ta == null && tb == null) return 0;
    if (ta == null) return 1;
    return -1;
  });
}

function cellStr(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "number" && Number.isFinite(v)) {
    return Math.abs(v) >= 1e6 || (Math.abs(v) < 0.001 && v !== 0)
      ? v.toExponential(2)
      : String(v);
  }
  return String(v);
}

export function DataPreviewTable({
  preview,
  title,
  pageSize = 20,
}: {
  preview: OutputPreview;
  title: string;
  pageSize?: number;
}) {
  const { columns, rows, truncated, total_rows, preview_rows } = preview;
  const [page, setPage] = useState(1);

  const dateSortColumn = useMemo(() => pickPrimaryDateColumn(columns), [columns]);
  const displayRows = useMemo(() => {
    if (!dateSortColumn) return rows;
    return sortRowsByPrimaryDateDesc(rows, dateSortColumn);
  }, [rows, dateSortColumn]);

  useEffect(() => {
    setPage(1);
  }, [rows.length, total_rows, pageSize]);

  const totalPages = Math.max(1, Math.ceil(displayRows.length / pageSize));
  const safePage = Math.min(page, totalPages);
  const pagedRows = useMemo(() => {
    const start = (safePage - 1) * pageSize;
    return displayRows.slice(start, start + pageSize);
  }, [pageSize, displayRows, safePage]);

  if (!columns.length) {
    return (
      <p className="rounded-xl border border-white/10 bg-canvas-elevated/50 px-4 py-3 text-sm text-ink-faint">
        {"No rows in this step's output."}
      </p>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-white/[0.06] shadow-card">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/[0.06] bg-canvas-subtle/40 px-4 py-2">
        <span className="text-xs font-medium text-ink">{title}</span>
        <span className="font-mono text-[0.7rem] text-ink-faint">
          {total_rows} row{total_rows === 1 ? "" : "s"} total
          {truncated ? ` · loaded ${preview_rows}` : ""}
          {dateSortColumn ? ` · sort ${dateSortColumn} ↓` : ""}
        </span>
      </div>
      <div className="data-preview-scroll max-h-[32rem] overflow-auto">
        <table className="w-full min-w-[640px] border-collapse text-left text-[0.8rem]">
          <thead>
            <tr className="sticky top-0 z-10 border-b border-white/[0.06] bg-canvas/95 backdrop-blur-sm">
              {columns.map((c) => (
                <th
                  key={c}
                  className="whitespace-nowrap px-3 py-2.5 font-mono text-[0.7rem] font-semibold uppercase tracking-wide text-accent-glow"
                >
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pagedRows.map((row, ri) => (
              <tr
                key={`${safePage}-${ri}`}
                className="border-b border-white/[0.04] last:border-0 hover:bg-white/[0.02]"
              >
                {columns.map((c) => (
                  <td key={c} className="max-w-[14rem] truncate px-3 py-2 font-mono text-ink-muted">
                    {cellStr(row[c])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {displayRows.length > pageSize && (
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-white/[0.06] bg-canvas-subtle/30 px-4 py-3">
          <span className="text-[0.72rem] text-ink-faint">
            Page {safePage} of {totalPages}
            {" · "}
            rows {(safePage - 1) * pageSize + 1}-
            {Math.min(safePage * pageSize, displayRows.length)}
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setPage(1)}
              disabled={safePage === 1}
              className="rounded-full border border-white/10 bg-canvas px-3 py-1.5 text-xs text-ink-muted transition hover:border-accent/30 hover:text-ink disabled:cursor-not-allowed disabled:opacity-40"
            >
              First
            </button>
            <button
              type="button"
              onClick={() => setPage((current) => Math.max(1, current - 1))}
              disabled={safePage === 1}
              className="rounded-full border border-white/10 bg-canvas px-3 py-1.5 text-xs text-ink-muted transition hover:border-accent/30 hover:text-ink disabled:cursor-not-allowed disabled:opacity-40"
            >
              Previous
            </button>
            <button
              type="button"
              onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
              disabled={safePage === totalPages}
              className="rounded-full border border-white/10 bg-canvas px-3 py-1.5 text-xs text-ink-muted transition hover:border-accent/30 hover:text-ink disabled:cursor-not-allowed disabled:opacity-40"
            >
              Next
            </button>
            <button
              type="button"
              onClick={() => setPage(totalPages)}
              disabled={safePage === totalPages}
              className="rounded-full border border-white/10 bg-canvas px-3 py-1.5 text-xs text-ink-muted transition hover:border-accent/30 hover:text-ink disabled:cursor-not-allowed disabled:opacity-40"
            >
              Last
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
