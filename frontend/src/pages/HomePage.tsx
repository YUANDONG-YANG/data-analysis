import { Link } from "react-router-dom";
import { homeContent, tourSteps } from "../content/pipelineContent";
import { useFinalOutputStatus } from "../hooks/useFinalOutputStatus";
import { usePipelineRuntime } from "../hooks/usePipelineRuntime";

export function HomePage() {
  const first = tourSteps[0];
  const { status, loading, starting, error, startRun } = usePipelineRuntime();
  const { status: finalOutputStatus } = useFinalOutputStatus();
  const runtime = status.runtime;
  const recentLogs = status.logs.slice(-8);

  return (
    <article className="mx-auto max-w-2xl">
      <p className="text-[0.65rem] font-semibold uppercase tracking-[0.4em] text-accent">
        Real Estate Analytics
      </p>
      <h1 className="mt-4 text-balance font-sans text-4xl font-semibold tracking-tight text-ink sm:text-5xl">
        {homeContent.title}
      </h1>
      <p className="mt-6 text-lg leading-relaxed text-ink-muted">{homeContent.lead}</p>

      <ul className="mt-12 space-y-4">
        {homeContent.bullets.map((b) => (
          <li
            key={b.title}
            className="rounded-2xl border border-white/[0.06] bg-canvas-elevated/60 p-5 shadow-card backdrop-blur-sm transition hover:border-accent/20"
          >
            <h2 className="font-semibold text-ink">{b.title}</h2>
            <p className="mt-2 text-sm leading-relaxed text-ink-muted">{b.text}</p>
          </li>
        ))}
      </ul>

      <div className="mt-14 grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
        <button
          type="button"
          onClick={() => void startRun()}
          disabled={status.running || starting}
          className="rainbow-glow-button star-hint-button inline-flex min-h-14 w-full items-center justify-center rounded-full border border-amber-400/40 bg-amber-400/10 px-6 py-3 text-center text-sm font-semibold text-amber-100 transition hover:border-amber-300/60 hover:bg-amber-400/15 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {status.running || starting ? "Pipeline running..." : "Start backend pipeline"}
        </button>
        <Link
          to="/live-demo"
          className="star-hint-button inline-flex min-h-14 w-full items-center justify-center rounded-full border border-emerald-500/40 bg-emerald-500/10 px-6 py-3 text-center text-sm font-semibold text-emerald-100 transition hover:border-emerald-400/60 hover:bg-emerald-500/15"
        >
          Pipeline step demo (latest run)
        </Link>
        {finalOutputStatus.available && (
          <Link
            to="/analysis-report"
            className="rainbow-glow-button star-hint-button inline-flex min-h-14 w-full items-center justify-center rounded-full border border-cyan-500/40 bg-cyan-500/10 px-6 py-3 text-center text-sm font-semibold text-cyan-100 transition hover:border-cyan-400/60 hover:bg-cyan-500/15"
          >
            Open output dashboard
          </Link>
        )}
        <Link
          to="/data-mapping"
          className="star-hint-button inline-flex min-h-14 w-full items-center justify-center rounded-full border border-pink-500/40 bg-pink-500/10 px-6 py-3 text-center text-sm font-semibold text-pink-100 transition hover:border-pink-400/60 hover:bg-pink-500/15"
        >
          Data mapping config
        </Link>
        <Link
          to="/integration-capabilities"
          className="inline-flex min-h-14 w-full items-center justify-center rounded-full border border-violet-500/40 bg-violet-500/10 px-6 py-3 text-center text-sm font-semibold text-violet-100 transition hover:border-violet-400/60 hover:bg-violet-500/15"
        >
          Explain modeling and governance
        </Link>
        <Link
          to={first.path}
          className="star-hint-button inline-flex min-h-14 w-full items-center justify-center rounded-full border border-accent/40 bg-accent/15 px-6 py-3 text-center text-sm font-semibold text-accent-glow shadow-glow transition hover:border-accent/60 hover:bg-accent/20"
        >
          Start pipeline tour
        </Link>
        <a
          className="inline-flex min-h-14 w-full items-center justify-center rounded-full border border-white/10 bg-white/[0.03] px-6 py-3 text-center text-sm font-semibold text-ink-muted transition hover:border-accent/30 hover:bg-white/[0.05] hover:text-ink"
          href="https://github.com/YUANDONG-YANG/data-analysis"
          target="_blank"
          rel="noreferrer"
        >
          View on GitHub
        </a>
      </div>

      <section className="mt-10 rounded-3xl border border-white/[0.06] bg-canvas-elevated/50 p-6 shadow-card">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-ink-faint">
              Backend runner
            </p>
            <h2 className="mt-2 text-xl font-semibold text-ink">Run and monitor the pipeline</h2>
            <p className="mt-2 max-w-xl text-sm leading-relaxed text-ink-muted">
              Start the Python pipeline from the browser, watch the current step, and open the live
              demo to inspect each completed stage as results arrive.
            </p>
          </div>
          <span
            className={
              status.running
                ? "rounded-full border border-emerald-500/30 bg-emerald-950/40 px-3 py-1 text-xs text-emerald-200"
                : "rounded-full border border-white/10 bg-canvas px-3 py-1 text-xs text-ink-faint"
            }
          >
            {loading
              ? "Checking status..."
              : status.running
                ? "Running"
                : runtime?.status === "completed"
                  ? "Last run completed"
                  : runtime?.status === "failed"
                    ? "Last run failed"
                    : "Idle"}
          </span>
        </div>

        {runtime?.status === "completed" && !status.running && finalOutputStatus.available && (
          <div className="mt-5 rounded-2xl border border-emerald-500/30 bg-gradient-to-br from-emerald-950/40 to-cyan-950/30 p-5 shadow-lg">
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-emerald-500/20 text-xl">
                ✓
              </div>
              <div className="flex-1">
                <p className="font-semibold text-emerald-100">
                  Pipeline Completed - Gold Layer Data Ready
                </p>
                <p className="mt-1.5 text-sm text-emerald-200/80">
                  All processing steps finished successfully. Final output files are available in <span className="font-mono text-emerald-100">data/gold/</span>
                </p>
                <div className="mt-3 flex flex-wrap gap-2 text-xs">
                  <span className="rounded-md bg-emerald-500/10 px-2 py-1 font-mono text-emerald-200">
                    final_dataframe.csv
                  </span>
                  <span className="rounded-md bg-emerald-500/10 px-2 py-1 font-mono text-emerald-200">
                    pipeline_analysis_report.html
                  </span>
                  <span className="rounded-md bg-emerald-500/10 px-2 py-1 font-mono text-emerald-200">
                    pipeline_steps_report.json
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {(runtime?.current_step || runtime?.current_title) && status.running && (
          <div className="mt-5 rounded-2xl border border-white/[0.06] bg-canvas/60 px-4 py-4">
            <p className="font-mono text-xs text-accent">
              {runtime.current_step ?? "Step"} {runtime.current_title ? `· ${runtime.current_title}` : ""}
            </p>
            <p className="mt-2 text-sm text-ink-muted">
              The pipeline is still running. Completed steps will appear in the live demo as soon as each stage finishes.
            </p>
          </div>
        )}

        {error && (
          <p className="mt-4 rounded-xl border border-red-500/20 bg-red-950/30 px-4 py-3 text-sm text-red-200">
            {error}
          </p>
        )}

        <div className="mt-5 flex flex-wrap gap-3">
          <Link
            to="/live-demo"
            className="inline-flex items-center justify-center rounded-full border border-accent/30 px-5 py-2.5 text-sm font-medium text-accent-glow transition hover:bg-accent/10"
          >
            Open live demo
          </Link>
          {finalOutputStatus.available && (
            <Link
              to="/analysis-report"
              className="rainbow-glow-button inline-flex items-center justify-center rounded-full border border-cyan-500/30 px-5 py-2.5 text-sm font-medium text-cyan-100 transition hover:bg-cyan-500/10"
            >
              Open output dashboard
            </Link>
          )}
        </div>

        <div className="mt-6">
          <div className="mb-3 flex items-center justify-between gap-3">
            <h3 className="text-xs font-semibold uppercase tracking-[0.22em] text-ink-faint">
              Recent runtime logs
            </h3>
            <span className="text-[0.7rem] text-ink-faint">{recentLogs.length} lines</span>
          </div>
          <pre className="max-h-72 overflow-auto rounded-2xl border border-white/[0.06] bg-canvas px-4 py-4 font-mono text-[0.72rem] leading-relaxed text-ink-muted">
            {recentLogs.length
              ? recentLogs.join("\n")
              : "No runtime logs yet. Start the pipeline to stream progress here."}
          </pre>
        </div>
      </section>

      <section className="mt-10 rounded-3xl border border-white/[0.06] bg-canvas-elevated/40 p-6 shadow-card">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-ink-faint">
              Integration summary
            </p>
            <h2 className="mt-2 text-xl font-semibold text-ink">
              What this project can already demonstrate
            </h2>
          </div>
          <Link
            to="/integration-capabilities"
            className="inline-flex items-center justify-center rounded-full border border-violet-500/40 bg-violet-500/10 px-4 py-2 text-sm font-semibold text-violet-100 transition hover:border-violet-400/60 hover:bg-violet-500/15"
          >
            Open detailed explanation
          </Link>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          {[
            ["Data modeling", "Supported"],
            ["Architecture design", "Supported"],
            ["Conflict resolution", "Supported with scope note"],
            ["Data governance", "Supported"],
          ].map(([label, statusText]) => (
            <div
              key={label}
              className="rounded-2xl border border-white/[0.06] bg-canvas/60 px-4 py-4"
            >
              <p className="font-medium text-ink">{label}</p>
              <p className="mt-1 text-sm text-ink-muted">{statusText}</p>
            </div>
          ))}
        </div>
      </section>
    </article>
  );
}
