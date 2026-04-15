import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import clsx from "clsx";
import { tourSteps } from "../content/pipelineContent";
import { useFinalOutputStatus } from "../hooks/useFinalOutputStatus";

/** Fixed-width slot so nav labels align regardless of glyph width (▶ vs Δ vs ▣). */
const navIconClass =
  "inline-flex h-5 w-5 flex-shrink-0 items-center justify-center font-mono text-[0.7rem] leading-none text-ink-faint";

export function DocLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { status: finalOutputStatus } = useFinalOutputStatus();
  const showOutputDashboard = finalOutputStatus.available;

  return (
    <div className="relative flex min-h-screen">
      <aside className="sidebar-shine fixed left-0 top-0 z-30 hidden h-full w-[min(18rem,100%)] flex-col border-r border-white/[0.06] shadow-glow lg:flex">
        <div className="border-b border-white/[0.06] px-6 py-8">
          <Link to="/" className="block">
            <span className="text-[0.65rem] font-semibold uppercase tracking-[0.35em] text-ink-faint">
              Documentation
            </span>
            <span className="mt-2 block font-sans text-lg font-semibold tracking-tight text-ink">
              Pipeline tour
            </span>
          </Link>
        </div>
        <nav className="flex-1 overflow-y-auto px-3 py-4">
          <p className="mb-2 px-3 text-[0.6rem] font-semibold uppercase tracking-[0.3em] text-ink-faint">
            Configuration
          </p>
          <div className="mb-6 space-y-0.5">
            <Link
              to="/data-mapping"
              className={clsx(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-all duration-200",
                location.pathname === "/data-mapping"
                  ? "bg-pink-500/10 text-pink-200 shadow-[inset_0_0_0_1px_hsl(330_81%_60%_/_0.35)]"
                  : "text-ink-muted hover:bg-white/[0.04] hover:text-ink",
              )}
            >
              <span className={navIconClass} aria-hidden>
                ⚙
              </span>
              <span className="min-w-0 font-medium">Data mapping config</span>
            </Link>
          </div>
          <p className="mb-2 px-3 text-[0.6rem] font-semibold uppercase tracking-[0.3em] text-ink-faint">
            Runtime
          </p>
          <div className="mb-6 space-y-0.5">
            <Link
              to="/live-demo"
              className={clsx(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-all duration-200",
                location.pathname === "/live-demo"
                  ? "bg-emerald-500/10 text-emerald-200 shadow-[inset_0_0_0_1px_hsl(142_76%_36%_/_0.35)]"
                  : "text-ink-muted hover:bg-white/[0.04] hover:text-ink",
              )}
            >
              <span className={navIconClass} aria-hidden>
                ▶
              </span>
              <span className="min-w-0 font-medium">Pipeline step demo</span>
            </Link>
            {showOutputDashboard && (
              <Link
                to="/analysis-report"
                className={clsx(
                  "rainbow-glow-button flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-all duration-200",
                  location.pathname === "/analysis-report"
                    ? "bg-cyan-500/10 text-cyan-200 shadow-[inset_0_0_0_1px_hsl(191_91%_36%_/_0.35)]"
                    : "text-ink-muted hover:bg-white/[0.04] hover:text-ink",
                )}
              >
                <span className={navIconClass} aria-hidden>
                  ▣
                </span>
                <span className="min-w-0 font-medium">Output dashboard</span>
              </Link>
            )}
            <Link
              to="/delta"
              className={clsx(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-all duration-200",
                location.pathname === "/delta"
                  ? "bg-teal-500/10 text-teal-200 shadow-[inset_0_0_0_1px_hsl(173_80%_40%_/_0.35)]"
                  : "text-ink-muted hover:bg-white/[0.04] hover:text-ink",
              )}
            >
              <span className={navIconClass} aria-hidden>
                Δ
              </span>
              <span className="min-w-0 font-medium">Delta Lake</span>
            </Link>
            <Link
              to="/integration-capabilities"
              className={clsx(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-all duration-200",
                location.pathname === "/integration-capabilities"
                  ? "bg-violet-500/10 text-violet-200 shadow-[inset_0_0_0_1px_hsl(262_83%_58%_/_0.35)]"
                  : "text-ink-muted hover:bg-white/[0.04] hover:text-ink",
              )}
            >
              <span className={navIconClass} aria-hidden>
                ◎
              </span>
              <span className="min-w-0 font-medium">Integration capabilities</span>
            </Link>
          </div>
          <p className="mb-2 px-3 text-[0.6rem] font-semibold uppercase tracking-[0.3em] text-ink-faint">
            Pipeline tour
          </p>
          <ol className="space-y-0.5">
            {tourSteps.map((step) => {
              const active = location.pathname === step.path;
              return (
                <li key={step.id}>
                  <Link
                    to={step.path}
                    className={clsx(
                      "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-all duration-200",
                      active
                        ? "bg-accent/10 text-accent-glow shadow-[inset_0_0_0_1px_hsl(199_89%_48%_/_0.25)]"
                        : "text-ink-muted hover:bg-white/[0.04] hover:text-ink",
                    )}
                  >
                    <span
                      className={clsx(
                        "inline-flex min-w-[2.25rem] flex-shrink-0 justify-end font-mono text-[0.7rem] tabular-nums leading-none",
                        active ? "text-accent" : "text-ink-faint group-hover:text-ink-muted",
                      )}
                    >
                      {step.number}
                    </span>
                    <span className="min-w-0 font-medium">{step.title}</span>
                  </Link>
                </li>
              );
            })}
          </ol>
        </nav>
        <div className="border-t border-white/[0.06] px-6 py-4">
          <p className="text-xs leading-relaxed text-ink-faint">Author Robin Yang</p>
        </div>
      </aside>

      {/* Mobile top bar */}
      <header className="sticky top-0 z-20 flex items-center justify-between border-b border-white/[0.06] bg-canvas/90 px-4 py-3 backdrop-blur-md lg:hidden">
        <Link to="/" className="text-sm font-semibold text-ink">
          Pipeline tour
        </Link>
        <select
          className="max-w-[55vw] rounded-lg border border-white/10 bg-canvas-elevated px-2 py-1.5 text-xs text-ink"
          value={
            location.pathname === "/data-mapping"
              ? "/data-mapping"
              : location.pathname === "/live-demo"
                ? "/live-demo"
              : location.pathname === "/delta"
                ? "/delta"
              : showOutputDashboard && location.pathname === "/analysis-report"
                ? "/analysis-report"
              : location.pathname === "/integration-capabilities"
                ? "/integration-capabilities"
              : location.pathname.startsWith("/tour")
                ? location.pathname
                : "/"
          }
          onChange={(e) => navigate(e.target.value)}
        >
          <option value="/">Home</option>
          <option value="/data-mapping">⚙ Data mapping config</option>
          <option value="/live-demo">Pipeline step demo</option>
          <option value="/delta">Delta Lake</option>
          {showOutputDashboard && <option value="/analysis-report">Output dashboard</option>}
          <option value="/integration-capabilities">Integration capabilities</option>
          {tourSteps.map((s) => (
            <option key={s.id} value={s.path}>
              {s.number} {s.title}
            </option>
          ))}
        </select>
      </header>

      <div className="flex min-h-screen flex-1 flex-col lg:pl-72">
        <main className="relative flex-1 px-5 pb-24 pt-10 sm:px-10 lg:px-16 lg:pt-14">
          <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top_right,_hsl(270_50%_40%_/_0.08),_transparent_50%)]" />
          <Outlet />
        </main>
      </div>
    </div>
  );
}
