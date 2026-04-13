import { Link, useParams } from "react-router-dom";
import { tourById } from "../content/pipelineContent";
import { MermaidDiagram } from "../components/MermaidDiagram";
import { InlineText } from "../components/InlineText";

export function TourPage() {
  const { stepId } = useParams<{ stepId: string }>();
  const step = stepId ? tourById[stepId] : undefined;

  if (!step) {
    return (
      <div className="mx-auto max-w-2xl text-center">
        <h1 className="text-2xl font-semibold text-ink">Not found</h1>
        <Link to="/" className="mt-4 inline-block text-accent hover:underline">
          Back home
        </Link>
      </div>
    );
  }

  const prev = step.prevId ? tourById[step.prevId] : null;
  const next = step.nextId ? tourById[step.nextId] : null;

  return (
    <article className="mx-auto max-w-4xl">
      <header className="border-b border-white/[0.06] pb-10">
        <p className="font-mono text-sm tabular-nums text-accent">{step.number}</p>
        <h1 className="mt-2 text-balance font-sans text-4xl font-semibold tracking-tight text-ink sm:text-5xl">
          {step.title}
        </h1>
        {step.subtitle && (
          <p className="mt-4 max-w-2xl text-lg text-ink-muted">{step.subtitle}</p>
        )}
      </header>

      <div className="mt-12 space-y-14">
        {step.sections.map((sec) => (
          <section key={sec.heading} className="scroll-mt-24">
            <h2 className="text-xs font-semibold uppercase tracking-[0.25em] text-ink-faint">
              {sec.heading}
            </h2>
            {sec.body && (
              <p className="mt-4 text-base leading-relaxed text-ink-muted">
                <InlineText text={sec.body} />
              </p>
            )}
            {sec.list && (
              <ul className="mt-4 list-inside list-decimal space-y-2.5 text-ink-muted marker:text-accent">
                {sec.list.map((item) => (
                  <li key={item} className="pl-1 leading-relaxed">
                    <InlineText text={item} />
                  </li>
                ))}
              </ul>
            )}
            {sec.table && (
              <div className="mt-6 overflow-x-auto rounded-2xl border border-white/[0.06] shadow-card">
                <table className="w-full min-w-[520px] border-collapse text-left text-sm">
                  <thead>
                    <tr className="border-b border-white/[0.06] bg-canvas-subtle/50">
                      {sec.table.headers.map((h) => (
                        <th key={h} className="px-4 py-3 font-semibold text-ink">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {sec.table.rows.map((row, ri) => (
                      <tr
                        key={ri}
                        className="border-b border-white/[0.04] last:border-0 hover:bg-white/[0.02]"
                      >
                        {row.map((cell, ci) => (
                          <td key={ci} className="px-4 py-3 text-ink-muted">
                            {cell}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {sec.mermaid && (
              <div className="mt-6">
                <MermaidDiagram chart={sec.mermaid} />
              </div>
            )}
            {sec.footnote && (
              <p className="mt-4 border-l-2 border-accent/40 pl-4 text-sm leading-relaxed text-ink-faint">
                {sec.footnote}
              </p>
            )}
          </section>
        ))}
      </div>

      <nav className="mt-20 flex flex-col gap-4 border-t border-white/[0.06] pt-10 sm:flex-row sm:justify-between">
        {prev ? (
          <Link
            to={prev.path}
            className="group flex flex-col rounded-2xl border border-white/[0.06] bg-canvas-elevated/40 px-5 py-4 transition hover:border-accent/25"
          >
            <span className="text-[0.65rem] font-semibold uppercase tracking-widest text-ink-faint">
              Previous
            </span>
            <span className="mt-1 font-medium text-ink group-hover:text-accent-glow">
              {prev.number} {prev.title}
            </span>
          </Link>
        ) : (
          <span />
        )}
        {next ? (
          <Link
            to={next.path}
            className="group flex flex-col rounded-2xl border border-white/[0.06] bg-canvas-elevated/40 px-5 py-4 text-right transition hover:border-accent/25 sm:ml-auto"
          >
            <span className="text-[0.65rem] font-semibold uppercase tracking-widest text-ink-faint">
              Next
            </span>
            <span className="mt-1 font-medium text-ink group-hover:text-accent-glow">
              {next.number} {next.title}
            </span>
          </Link>
        ) : (
          <Link
            to="/"
            className="group flex flex-col rounded-2xl border border-accent/20 bg-accent/5 px-5 py-4 text-right transition hover:border-accent/40"
          >
            <span className="text-[0.65rem] font-semibold uppercase tracking-widest text-ink-faint">
              Finish
            </span>
            <span className="mt-1 font-medium text-accent-glow">Back to home</span>
          </Link>
        )}
      </nav>
    </article>
  );
}
