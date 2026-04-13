import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { DataPreviewTable } from "../components/DataPreviewTable";
import { usePipelineRun } from "../hooks/usePipelineRun";
import { usePipelineRuntime } from "../hooks/usePipelineRuntime";
import type { PipelineStepEntry } from "../types/pipelineRun";

const AUTO_MS = 2800;

function JsonBlock({ label, value }: { label: string; value: unknown }) {
  const [open, setOpen] = useState(false);
  const text = useMemo(() => JSON.stringify(value, null, 2), [value]);
  return (
    <div className="rounded-xl border border-white/[0.06] bg-canvas-elevated/40">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-2.5 text-left text-xs font-medium uppercase tracking-widest text-ink-faint transition hover:text-ink-muted"
      >
        {label}
        <span className="font-mono text-[0.65rem] text-accent">{open ? "−" : "+"}</span>
      </button>
      {open && (
        <pre className="max-h-64 overflow-auto border-t border-white/[0.06] p-4 font-mono text-[0.7rem] leading-relaxed text-ink-muted">
          {text}
        </pre>
      )}
    </div>
  );
}

export function PipelineDemoPage() {
  const { data, source, loading, error } = usePipelineRun();
  const runtimeState = usePipelineRuntime();
  const [idx, setIdx] = useState(0);
  const [auto, setAuto] = useState(false);

  const runtime = runtimeState.status.runtime;
  const runtimeSteps = runtime?.steps ?? [];
  const steps = runtimeSteps.length ? runtimeSteps : data?.steps ?? [];
  const step: PipelineStepEntry | undefined = steps[idx];

  const go = useCallback(
    (d: number) => {
      setIdx((i) => {
        const n = steps.length;
        if (n === 0) return 0;
        return Math.min(Math.max(i + d, 0), n - 1);
      });
    },
    [steps.length],
  );

  useEffect(() => {
    if (!auto || steps.length === 0) return;
    const t = window.setInterval(() => {
      setIdx((i) => (i + 1 >= steps.length ? 0 : i + 1));
    }, AUTO_MS);
    return () => window.clearInterval(t);
  }, [auto, steps.length]);

  useEffect(() => {
    setIdx(0);
  }, [data?.pipeline_id, runtime?.pipeline_id]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight") go(1);
      if (e.key === "ArrowLeft") go(-1);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [go]);

  if (loading && runtimeState.loading) {
    return (
      <div className="mx-auto max-w-3xl animate-pulse py-20 text-center text-ink-muted">
        Loading pipeline results…
      </div>
    );
  }

  if (error || !data || !step) {
    return (
      <article className="mx-auto max-w-2xl rounded-2xl border border-amber-500/20 bg-amber-950/30 p-8 text-amber-100/90">
        <h1 className="text-xl font-semibold">No run data available</h1>
        <p className="mt-3 text-sm leading-relaxed opacity-90">{runtimeState.error ?? error}</p>
        <p className="mt-6 text-sm text-ink-muted">
          You can still read the narrative tour:{" "}
          <Link to="/tour/pipeline-overview" className="text-accent underline">
            Pipeline tour
          </Link>
        </p>
      </article>
    );
  }

  return (
    <article className="mx-auto max-w-4xl">
      <header className="border-b border-white/[0.06] pb-8">
        <p className="text-[0.65rem] font-semibold uppercase tracking-[0.35em] text-accent">
          {runtimeState.status.running ? "Live run in progress" : "Live run"}
        </p>
        <h1 className="mt-2 text-balance font-sans text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
          Pipeline step-by-step demo
        </h1>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-ink-muted">
          Start the backend pipeline from the browser, then follow each stage as results arrive. The
          page updates automatically and shows a preview of the output table for every completed step.
        </p>
        <div className="mt-6 flex flex-wrap items-center gap-3 text-xs text-ink-faint">
          <button
            type="button"
            onClick={() => void runtimeState.startRun()}
            disabled={runtimeState.status.running || runtimeState.starting}
            className="rounded-full border border-amber-400/40 bg-amber-400/10 px-4 py-1.5 text-xs font-semibold text-amber-100 transition hover:border-amber-300/60 hover:bg-amber-400/15 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {runtimeState.status.running || runtimeState.starting ? "Pipeline running..." : "Start backend pipeline"}
          </button>
          <span className="rounded-full border border-white/10 bg-canvas-elevated px-3 py-1 font-mono">
            pipeline_id: {runtime?.pipeline_id ?? data.pipeline_id}
          </span>
          <span className="rounded-full border border-white/10 px-3 py-1">
            {runtime?.updated_at ?? data.generated_at}
          </span>
          <span className="rounded-full border border-white/10 px-3 py-1">
            {(runtime?.run_mode ?? data.run_mode)} / {(runtime?.environment ?? data.environment)}
          </span>
          {(runtime?.total_seconds ?? data.total_seconds) != null && (
            <span className="rounded-full border border-white/10 px-3 py-1">
              Total {(runtime?.total_seconds ?? data.total_seconds ?? 0).toFixed(2)}s
            </span>
          )}
          <span
            className={
              runtimeState.status.running || source === "live"
                ? "rounded-full border border-emerald-500/30 bg-emerald-950/40 px-3 py-1 text-emerald-200/90"
                : "rounded-full border border-amber-500/30 bg-amber-950/40 px-3 py-1 text-amber-100/90"
            }
          >
            {runtimeState.status.running
              ? "Pipeline is currently running"
              : source === "live"
                ? "Live: data/gold (latest run)"
              : "Sample data (no local output file detected)"}
          </span>
        </div>
        {runtimeState.error && (
          <p className="mt-4 rounded-xl border border-red-500/20 bg-red-950/30 px-4 py-3 text-sm text-red-200">
            {runtimeState.error}
          </p>
        )}
      </header>

      {/* Stepper */}
      <div className="mt-10">
        <div className="flex flex-wrap items-center gap-2">
          {steps.map((s, i) => (
            <button
              key={s.step}
              type="button"
              onClick={() => setIdx(i)}
              className={
                i === idx
                  ? "rounded-full bg-accent px-3 py-1.5 font-mono text-xs font-semibold text-canvas shadow-glow"
                  : "rounded-full border border-white/10 bg-canvas-elevated/50 px-3 py-1.5 font-mono text-xs text-ink-muted transition hover:border-accent/30 hover:text-ink"
              }
            >
              {s.step}
            </button>
          ))}
        </div>
        <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-canvas-subtle">
          <div
            className="h-full rounded-full bg-gradient-to-r from-accent to-accent-glow transition-all duration-500"
            style={{ width: `${((idx + 1) / steps.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Current step */}
      <section className="mt-10 space-y-8">
        {runtimeState.status.running && (
          <div className="rounded-2xl border border-emerald-500/20 bg-emerald-950/25 p-5">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-200/80">
              Current execution
            </p>
            <p className="mt-2 font-mono text-sm text-emerald-100">
              {runtime?.current_step ?? "Step"} {runtime?.current_title ? `· ${runtime.current_title}` : ""}
            </p>
            <p className="mt-2 text-sm text-emerald-100/80">
              Completed steps will appear below as soon as each stage finishes.
            </p>
          </div>
        )}
        <div>
          <h2 className="font-mono text-sm text-accent">{step.step}</h2>
          <p className="mt-1 text-2xl font-semibold text-ink">{step.title}</p>
          {step.duration_sec != null && (
            <p className="mt-2 font-mono text-sm text-ink-muted">
              Step time <span className="text-accent-glow">{step.duration_sec.toFixed(3)}</span>s
              {step.delta_display ? (
                <>
                  {" "}
                  · <span className="text-ink">{step.delta_display}</span>
                </>
              ) : null}
            </p>
          )}
        </div>

        {step.output_preview && (
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-faint">
              Step output (row preview)
            </h3>
            <div className="mt-3">
              <DataPreviewTable preview={step.output_preview} title="Output" />
            </div>
          </div>
        )}

        {step.conversion_stats && Object.keys(step.conversion_stats).length > 0 && (
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-faint">
              Conversion stats (step 5)
            </h3>
            <dl className="mt-3 grid gap-2 sm:grid-cols-2">
              {Object.entries(step.conversion_stats).map(([k, v]) => (
                <div
                  key={k}
                  className="rounded-xl border border-white/[0.06] bg-canvas-elevated/30 px-4 py-3"
                >
                  <dt className="font-mono text-[0.65rem] uppercase text-ink-faint">{k}</dt>
                  <dd className="mt-1 font-mono text-sm text-ink">{String(v)}</dd>
                </div>
              ))}
            </dl>
          </div>
        )}

        <div className="grid gap-3 md:grid-cols-2">
          {step.before != null && <JsonBlock label="Before snapshot" value={step.before} />}
          {step.after != null && <JsonBlock label="After snapshot" value={step.after} />}
        </div>

        {idx === steps.length - 1 && (
          <div className="rounded-2xl border border-emerald-500/20 bg-emerald-950/25 p-6">
            <h3 className="text-sm font-semibold text-emerald-100/95">Persisted output</h3>
            <p className="mt-2 font-mono text-sm text-emerald-100/80">
              {runtime?.output_csv ?? data.output_csv} · MD5 {runtime?.output_checksum_md5 ?? data.output_checksum_md5}
            </p>
          </div>
        )}

        <div>
          <div className="mb-3 flex items-center justify-between gap-3">
            <h3 className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-faint">
              Runtime logs
            </h3>
            <span className="text-[0.7rem] text-ink-faint">{runtimeState.status.logs.length} lines</span>
          </div>
          <pre className="max-h-72 overflow-auto rounded-2xl border border-white/[0.06] bg-canvas px-4 py-4 font-mono text-[0.72rem] leading-relaxed text-ink-muted">
            {runtimeState.status.logs.length
              ? runtimeState.status.logs.join("\n")
              : "No runtime logs yet. Start the pipeline to stream progress here."}
          </pre>
        </div>
      </section>

      {/* Controls */}
      <div className="mt-12 flex flex-col gap-4 border-t border-white/[0.06] pt-8 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => go(-1)}
            disabled={idx <= 0}
            className="rounded-full border border-white/15 bg-canvas-elevated px-5 py-2.5 text-sm font-medium text-ink transition hover:border-accent/40 disabled:opacity-40"
          >
            Previous
          </button>
          <button
            type="button"
            onClick={() => go(1)}
            disabled={idx >= steps.length - 1}
            className="rounded-full border border-white/15 bg-canvas-elevated px-5 py-2.5 text-sm font-medium text-ink transition hover:border-accent/40 disabled:opacity-40"
          >
            Next
          </button>
          <button
            type="button"
            onClick={() => setAuto(!auto)}
            className={
              auto
                ? "rounded-full bg-accent px-5 py-2.5 text-sm font-semibold text-canvas"
                : "rounded-full border border-accent/40 px-5 py-2.5 text-sm font-medium text-accent-glow transition hover:bg-accent/10"
            }
          >
            {auto ? `Auto-play (${AUTO_MS / 1000}s / step)` : "Auto-play"}
          </button>
        </div>
        <p className="text-[0.7rem] text-ink-faint">Shortcuts: arrow keys to change step</p>
      </div>
    </article>
  );
}
