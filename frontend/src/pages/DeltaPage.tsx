import { useMemo } from "react";
import { Link } from "react-router-dom";
import { MermaidDiagram } from "../components/MermaidDiagram";
import { useDeltaSnapshot } from "../hooks/useDeltaSnapshot";
import { usePipelineRuntime } from "../hooks/usePipelineRuntime";
import type { DeltaMergeMetrics, DeltaSnapshotPayload } from "../types/deltaSnapshot";

const DELTA_FLOW = `flowchart LR
  B[Bronze files / APIs]
  S[Silver Delta tables]
  G[Gold Delta metrics]
  V["Transaction log & versions"]
  C[CSV + reports for UI]

  B -->|clean & key| S
  S -->|join & KPIs| G
  G -->|each MERGE commit| V
  G -->|optional export| C

  style G fill:#1e2d2d,stroke:#34d399,color:#6ee7b7
  style S fill:#1e2a3d,stroke:#60a5fa,color:#93c5fd
  style V fill:#1a2f2a,stroke:#2dd4bf,color:#99f6e4
  style C fill:#162236,stroke:#94a3b8,color:#cbd5e1`;

const MERGE_SQL = `MERGE INTO gold_metrics AS t
USING staging AS s
  ON t.month = s.month AND t.builder = s.builder AND t.community_name = s.community_name
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;`;

function MergeMetricsBar({ metrics }: { metrics: DeltaMergeMetrics }) {
  const ins = metrics.rows_inserted ?? 0;
  const upd = metrics.rows_updated ?? 0;
  const del = metrics.rows_deleted ?? 0;
  const total = ins + upd + del;
  if (total <= 0) return null;
  const pIns = (ins / total) * 100;
  const pUpd = (upd / total) * 100;
  const pDel = (del / total) * 100;
  return (
    <div className="mt-3 space-y-2">
      <div className="flex h-2.5 overflow-hidden rounded-full bg-canvas ring-1 ring-white/[0.06]">
        {ins > 0 && (
          <span
            className="bg-emerald-500/80 transition-[width]"
            style={{ width: `${pIns}%` }}
            title={`${ins} inserted`}
          />
        )}
        {upd > 0 && (
          <span
            className="bg-amber-500/80 transition-[width]"
            style={{ width: `${pUpd}%` }}
            title={`${upd} updated`}
          />
        )}
        {del > 0 && (
          <span
            className="bg-rose-500/75 transition-[width]"
            style={{ width: `${pDel}%` }}
            title={`${del} deleted`}
          />
        )}
      </div>
      <p className="text-[0.65rem] leading-relaxed text-ink-faint">
        <span className="text-emerald-300/90">■</span> insert{" "}
        <span className="text-amber-300/90">■</span> update{" "}
        <span className="text-rose-300/90">■</span> delete · {total} row ops
      </p>
    </div>
  );
}

function snapshotSummary(data: DeltaSnapshotPayload) {
  const maxVer = data.tables.reduce((m, t) => Math.max(m, t.table_version), 0);
  const mergeOps = data.tables.reduce((sum, t) => {
    const x = t.metrics;
    if (!x) return sum;
    return sum + (x.rows_inserted ?? 0) + (x.rows_updated ?? 0) + (x.rows_deleted ?? 0);
  }, 0);
  return { tableCount: data.tables.length, maxVer, mergeOps };
}

function SnapshotSkeleton() {
  return (
    <div className="mt-4 grid gap-4 sm:grid-cols-2">
      {[0, 1].map((i) => (
        <div
          key={i}
          className="h-44 animate-pulse rounded-2xl border border-white/[0.06] bg-canvas-elevated/50"
        />
      ))}
    </div>
  );
}

export function DeltaPage() {
  const { data, source, loading, error, reload } = useDeltaSnapshot();
  const runtime = usePipelineRuntime();

  const summary = useMemo(() => (data ? snapshotSummary(data) : null), [data]);

  return (
    <article className="mx-auto max-w-4xl">
      <header className="border-b border-white/[0.06] pb-8">
        <p className="text-[0.65rem] font-semibold uppercase tracking-[0.35em] text-teal-300/90">
          Delta Lake
        </p>
        <h1 className="mt-2 text-balance font-sans text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
          ACID tables, MERGE, and version history
        </h1>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-ink-muted">
          This page demonstrates how Delta fits the medallion pipeline: Silver and Gold can be stored as
          versioned tables with keyed <span className="font-mono text-ink-muted/90">MERGE</span> updates.
          The browser does not read Parquet directly—it shows metadata written to{" "}
          <span className="font-mono text-teal-200/80">delta_snapshot.json</span> (or the bundled sample)
          while charts still use <span className="font-mono text-ink-muted/90">final_dataframe.csv</span>.
        </p>
        <div className="mt-6 flex flex-wrap items-center gap-3 text-xs">
          <button
            type="button"
            onClick={() => void runtime.startRun()}
            disabled={runtime.status.running || runtime.starting}
            className="rounded-full border border-amber-400/40 bg-amber-400/10 px-4 py-1.5 font-semibold text-amber-100 transition hover:border-amber-300/60 hover:bg-amber-400/15 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {runtime.status.running || runtime.starting ? "Pipeline running..." : "Run backend pipeline"}
          </button>
          <Link
            to="/live-demo"
            className="rounded-full border border-emerald-500/40 bg-emerald-500/10 px-4 py-1.5 font-semibold text-emerald-100 transition hover:border-emerald-400/60 hover:bg-emerald-500/15"
          >
            Pipeline step demo
          </Link>
          <button
            type="button"
            onClick={() => void reload()}
            className="rounded-full border border-white/10 px-4 py-1.5 text-ink-muted transition hover:bg-white/[0.04] hover:text-ink"
          >
            Refresh snapshot
          </button>
          {source && (
            <span
              className={
                source === "live"
                  ? "rounded-full border border-teal-500/35 bg-teal-950/40 px-3 py-1 text-teal-100/90"
                  : "rounded-full border border-amber-500/35 bg-amber-950/40 px-3 py-1 text-amber-100/90"
              }
            >
              {source === "live" ? "Live: data/gold/delta_snapshot.json" : "Sample data (offline)"}
            </span>
          )}
        </div>
      </header>

      <section className="mt-10" aria-labelledby="delta-flow-heading">
        <h2 id="delta-flow-heading" className="text-xs font-semibold uppercase tracking-[0.28em] text-ink-faint">
          Flow
        </h2>
        <div className="mt-4">
          <MermaidDiagram chart={DELTA_FLOW} />
        </div>
      </section>

      <section className="mt-10" aria-labelledby="delta-merge-heading">
        <h2 id="delta-merge-heading" className="text-xs font-semibold uppercase tracking-[0.28em] text-ink-faint">
          MERGE semantics
        </h2>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-ink-muted">
          Each pipeline run can upsert into the Gold table by business key: matching rows update, new keys
          insert. The snapshot below shows how many rows were touched in the last operation (illustrative).
        </p>
        <pre className="mt-4 overflow-x-auto rounded-2xl border border-white/[0.06] bg-canvas/80 p-4 font-mono text-[0.72rem] leading-relaxed text-teal-100/90 shadow-inner">
          {MERGE_SQL}
        </pre>
      </section>

      <section className="mt-10" aria-labelledby="delta-snapshot-heading">
        <h2 id="delta-snapshot-heading" className="text-xs font-semibold uppercase tracking-[0.28em] text-ink-faint">
          Snapshot
        </h2>
        {loading && (
          <>
            <p className="mt-4 text-sm text-ink-muted">Loading Delta metadata…</p>
            <SnapshotSkeleton />
          </>
        )}
        {error && !loading && (
          <p className="mt-4 rounded-xl border border-red-500/20 bg-red-950/30 px-4 py-3 text-sm text-red-200">
            {error}
          </p>
        )}
        {data && !loading && (
          <div className="mt-4 space-y-6">
            {summary && summary.tableCount > 0 && (
              <div className="flex flex-wrap gap-2">
                <span className="rounded-xl border border-teal-500/25 bg-teal-950/35 px-4 py-2 text-xs text-teal-100/95">
                  <span className="text-ink-faint">Tables </span>
                  <span className="font-mono font-semibold tabular-nums">{summary.tableCount}</span>
                </span>
                <span className="rounded-xl border border-white/10 bg-canvas-elevated/60 px-4 py-2 text-xs text-ink-muted">
                  <span className="text-ink-faint">Latest table version </span>
                  <span className="font-mono font-semibold tabular-nums text-ink">v{summary.maxVer}</span>
                </span>
                <span className="rounded-xl border border-white/10 bg-canvas-elevated/60 px-4 py-2 text-xs text-ink-muted">
                  <span className="text-ink-faint">Row ops (last MERGE) </span>
                  <span className="font-mono font-semibold tabular-nums text-ink">{summary.mergeOps}</span>
                </span>
              </div>
            )}

            <div className="flex flex-wrap gap-3 text-xs text-ink-muted">
              <span className="rounded-full border border-white/10 px-3 py-1 font-mono">
                pipeline_id: {data.pipeline_id}
              </span>
              <span className="rounded-full border border-white/10 px-3 py-1">
                payload v{data.version} · {data.generated_at}
              </span>
            </div>
            {data.notes && (
              <p className="rounded-xl border border-white/[0.06] bg-canvas/50 px-4 py-3 text-sm text-ink-muted">
                {data.notes}
              </p>
            )}
            {data.tables.length === 0 && (
              <p className="rounded-xl border border-amber-500/20 bg-amber-950/25 px-4 py-3 text-sm text-amber-100/90">
                No tables in this snapshot. Add entries under <span className="font-mono">tables</span> in{" "}
                <span className="font-mono">delta_snapshot.json</span>.
              </p>
            )}
            <div className="grid gap-4 sm:grid-cols-2">
              {data.tables.map((t) => (
                <div
                  key={t.name}
                  className="rounded-2xl border border-teal-500/20 bg-gradient-to-br from-teal-950/30 to-canvas-elevated/60 p-5 shadow-card"
                >
                  <p className="font-mono text-xs text-teal-300/90">{t.name}</p>
                  <p className="mt-1 break-all font-mono text-[0.7rem] text-ink-faint">{t.path}</p>
                  <dl className="mt-4 space-y-2 text-sm">
                    <div className="flex justify-between gap-2">
                      <dt className="text-ink-faint">Table version</dt>
                      <dd className="font-mono text-ink">v{t.table_version}</dd>
                    </div>
                    <div className="flex justify-between gap-2">
                      <dt className="text-ink-faint">Last op</dt>
                      <dd className="font-mono text-ink">{t.last_operation}</dd>
                    </div>
                    <div>
                      <dt className="text-ink-faint">Merge keys</dt>
                      <dd className="mt-1 font-mono text-[0.7rem] text-ink-muted">
                        {t.merge_keys.join(", ")}
                      </dd>
                    </div>
                    {t.metrics && <MergeMetricsBar metrics={t.metrics} />}
                  </dl>
                </div>
              ))}
            </div>
            {data.history && data.history.length > 0 && (
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-[0.22em] text-ink-faint">
                  Recent versions (time travel)
                </h3>
                <ul className="mt-3 divide-y divide-white/[0.06] overflow-hidden rounded-2xl border border-white/[0.06] bg-canvas/40 font-mono text-[0.72rem] text-ink-muted">
                  {data.history.map((h) => (
                    <li
                      key={`${h.version}-${h.at}`}
                      className="grid grid-cols-1 gap-1 px-4 py-3 sm:grid-cols-[minmax(0,4rem)_1fr_minmax(0,8rem)] sm:items-center sm:gap-4"
                    >
                      <span className="font-semibold text-teal-200/90">v{h.version}</span>
                      <span className="text-ink-muted">{h.at}</span>
                      <span className="truncate text-ink-faint sm:text-right">{h.pipeline_id}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </section>

      <section className="mt-12 rounded-2xl border border-white/[0.06] bg-canvas-elevated/40 p-6">
        <h2 className="text-sm font-semibold text-ink">How to get live data</h2>
        <ol className="mt-3 list-inside list-decimal space-y-2 text-sm text-ink-muted">
          <li>Integrate Delta writes in the Python pipeline and emit <span className="font-mono">data/gold/delta_snapshot.json</span>.</li>
          <li>Run <span className="font-mono">python -m src.main</span> from the repo root (or use the button above).</li>
          <li>Click <span className="font-mono text-ink-muted/90">Refresh snapshot</span>—this page will switch from sample to live.</li>
        </ol>
      </section>
    </article>
  );
}
