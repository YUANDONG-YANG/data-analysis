import { useEffect, useMemo, useState } from "react";
import type { OutputPreview } from "../types/pipelineRun";

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

  useEffect(() => {
    setPage(1);
  }, [rows.length, total_rows, pageSize]);

  const totalPages = Math.max(1, Math.ceil(rows.length / pageSize));
  const safePage = Math.min(page, totalPages);
  const pagedRows = useMemo(() => {
    const start = (safePage - 1) * pageSize;
    return rows.slice(start, start + pageSize);
  }, [pageSize, rows, safePage]);

  if (!columns.length) {
    return (
      <p className="rounded-xl border border-white/10 bg-canvas-elevated/50 px-4 py-3 text-sm text-ink-faint">
        {"No rows in this step's output (empty table)."}
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
      {rows.length > pageSize && (
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-white/[0.06] bg-canvas-subtle/30 px-4 py-3">
          <span className="text-[0.72rem] text-ink-faint">
            Page {safePage} of {totalPages}
            {" · "}
            rows {(safePage - 1) * pageSize + 1}-
            {Math.min(safePage * pageSize, rows.length)}
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
