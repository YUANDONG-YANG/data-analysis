import { Link } from "react-router-dom";

type Capability = {
  title: string;
  status: "Supported" | "Supported with scope note" | "Foundational only";
  summary: string;
  howItWorks: string[];
  caveat?: string;
};

const capabilities: Capability[] = [
  {
    title: "Data modeling",
    status: "Supported",
    summary:
      "The project clearly demonstrates reporting-oriented data modeling built around a canonical monthly community view.",
    howItWorks: [
      "Different source schemas are normalized into common working fields such as `year_month`, `community_name`, `target_sales`, `builder`, and `create_date`.",
      "Community aliases and path slug parsing map source-specific names into canonical `community_name` values.",
      "The final output model is stable and business-readable: `month`, `community_name`, `builder`, `actual_sales`, `target_sales`, `crm_leads`, `web_traffic`, and derived metrics.",
    ],
  },
  {
    title: "Architecture design",
    status: "Supported",
    summary:
      "The codebase already shows a strong layered architecture suitable for explaining repositories, processors, services, calculators, and orchestration.",
    howItWorks: [
      "Repositories isolate file and API ingestion from transformation logic.",
      "Processors standardize and clean source data before any business aggregation is applied.",
      "Services orchestrate domain steps while `MetricsCalculator` owns the final aggregation logic.",
      "The pipeline entry point and DI container make the architecture easy to explain in terms of responsibilities and boundaries.",
    ],
  },
  {
    title: "Conflict resolution",
    status: "Supported with scope note",
    summary:
      "Conflict handling exists and is demonstrable, but it is implemented as practical data-pipeline rules rather than a full exception-management platform.",
    howItWorks: [
      "During keyed merges, duplicate columns are resolved by keeping the original column and filling gaps from the `_dup` column.",
      "Duplicate rows are removed during cleaning and invalid outliers are filtered from sales data.",
      "Builder consistency checks remove cross-builder leakage from API payloads before enrichment.",
    ],
    caveat:
      "This is strong enough to explain conflict resolution strategy in a demo, but it is not yet a full reconciliation workflow with case handling, approvals, or source-by-source dispute audit trails.",
  },
  {
    title: "Financial-grade data governance",
    status: "Foundational only",
    summary:
      "The project includes governance-oriented controls, but it should be presented as a foundation for governed analytics, not as a completed financial-grade governance platform.",
    howItWorks: [
      "The pipeline writes structured logs, step snapshots, output schema information, checksum metadata, quality summaries, and runtime status JSON.",
      "The front-end can expose step-level lineage, before/after comparisons, and persisted output details.",
      "Source normalization, builder consistency checks, and deterministic output sorting support repeatable reporting behavior.",
    ],
    caveat:
      "To honestly claim financial-grade governance, the project would still need formal lineage storage, policy enforcement, approval workflows, access controls, versioned data contracts, retention rules, and stronger audit evidence across the whole lifecycle.",
  },
];

function StatusBadge({ status }: { status: Capability["status"] }) {
  return (
    <span
      className={
        status === "Supported"
          ? "inline-flex min-h-10 min-w-[11rem] items-center justify-center rounded-full border border-emerald-500/30 bg-emerald-950/30 px-3 py-1 text-center text-xs font-medium leading-tight text-emerald-200"
          : status === "Supported with scope note"
            ? "inline-flex min-h-10 min-w-[11rem] items-center justify-center rounded-full border border-amber-500/30 bg-amber-950/30 px-3 py-1 text-center text-xs font-medium leading-tight text-amber-100"
            : "inline-flex min-h-10 min-w-[11rem] items-center justify-center rounded-full border border-violet-500/30 bg-violet-950/30 px-3 py-1 text-center text-xs font-medium leading-tight text-violet-200"
      }
    >
      {status}
    </span>
  );
}

export function IntegrationCapabilitiesPage() {
  return (
    <article className="mx-auto max-w-4xl">
      <header className="border-b border-white/[0.06] pb-10">
        <p className="text-[0.65rem] font-semibold uppercase tracking-[0.35em] text-accent">
          Modeling, architecture, and governance
        </p>
        <h1 className="mt-2 text-balance font-sans text-4xl font-semibold tracking-tight text-ink sm:text-5xl">
          Can this project showcase data modeling, architecture design, conflict resolution, and financial-grade governance?
        </h1>
        <p className="mt-4 max-w-3xl text-lg leading-relaxed text-ink-muted">
          Yes, but with an important boundary. The current codebase is strong for explaining data
          modeling, pipeline architecture, and practical conflict handling. It also contains useful
          governance controls, but those should be presented as the foundation of governed analytics
          rather than a finished financial-grade operating model.
        </p>
      </header>

      <section className="mt-10 overflow-x-auto rounded-2xl border border-white/[0.06] shadow-card">
        <table className="w-full min-w-[680px] border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-white/[0.06] bg-canvas-subtle/50">
              <th className="px-4 py-3 font-semibold text-ink">Capability</th>
              <th className="w-[13rem] px-4 py-3 text-center font-semibold text-ink">Status</th>
              <th className="px-4 py-3 font-semibold text-ink">What the current project can credibly show</th>
            </tr>
          </thead>
          <tbody>
            {capabilities.map((item) => (
              <tr
                key={item.title}
                className="border-b border-white/[0.04] align-top last:border-0 hover:bg-white/[0.02]"
              >
                <td className="px-4 py-4 font-semibold text-ink">{item.title}</td>
                <td className="w-[13rem] px-4 py-4 text-center">
                  <StatusBadge status={item.status} />
                </td>
                <td className="px-4 py-4 text-ink-muted">{item.summary}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="mt-12 space-y-6">
        {capabilities.map((item) => (
          <div
            key={item.title}
            className="rounded-3xl border border-white/[0.06] bg-canvas-elevated/50 p-6 shadow-card"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="text-xl font-semibold text-ink">{item.title}</h2>
                <p className="mt-2 max-w-3xl text-sm leading-relaxed text-ink-muted">
                  {item.summary}
                </p>
              </div>
              <StatusBadge status={item.status} />
            </div>

            <div className="mt-5">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-ink-faint">
                How the code demonstrates it
              </p>
              <ul className="mt-3 list-inside list-disc space-y-2.5 text-sm leading-relaxed text-ink-muted">
                {item.howItWorks.map((point) => (
                  <li key={point}>{point}</li>
                ))}
              </ul>
            </div>

            {item.caveat && (
              <div className="mt-5 rounded-2xl border border-amber-500/20 bg-amber-950/20 px-4 py-4">
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-amber-200/80">
                  Scope note
                </p>
                <p className="mt-2 text-sm leading-relaxed text-amber-100/85">{item.caveat}</p>
              </div>
            )}
          </div>
        ))}
      </section>

      <section className="mt-12 rounded-3xl border border-white/[0.06] bg-canvas-elevated/40 p-6">
        <h2 className="text-xl font-semibold text-ink">Recommended positioning in demos and assessments</h2>
        <p className="mt-3 text-sm leading-relaxed text-ink-muted">
          Position the project as a strong reporting-oriented integration pipeline with solid modeling
          discipline, clear architecture, visible runtime lineage, and practical governance controls.
          For assessments that ask for financial-grade governance, describe the current implementation
          as evidence of governance readiness and then call out the controls that would be added next
          for a production-grade regulated environment.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link
            to="/live-demo"
            className="inline-flex items-center justify-center rounded-full border border-emerald-500/40 bg-emerald-500/10 px-5 py-2.5 text-sm font-semibold text-emerald-100 transition hover:border-emerald-400/60 hover:bg-emerald-500/15"
          >
            Open live pipeline demo
          </Link>
          <Link
            to="/tour/pipeline-overview"
            className="inline-flex items-center justify-center rounded-full border border-accent/30 px-5 py-2.5 text-sm font-medium text-accent-glow transition hover:bg-accent/10"
          >
            Review pipeline tour
          </Link>
        </div>
      </section>
    </article>
  );
}
