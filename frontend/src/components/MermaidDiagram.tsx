import mermaid from "mermaid";
import { useEffect, useId, useRef, useState } from "react";

let mermaidConfigured = false;

function configureMermaid() {
  if (mermaidConfigured) return;
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: "loose",
    theme: "base",
    look: "classic",
    fontFamily: "Instrument Sans, system-ui, sans-serif",
    flowchart: {
      curve: "basis",
      padding: 16,
      htmlLabels: true,
      useMaxWidth: true,
    },
    themeVariables: {
      darkMode: true,
      background: "transparent",
      mainBkg: "#162236",
      secondBkg: "#1d2a44",
      tertiaryColor: "#22304c",
      primaryColor: "#1b2d49",
      primaryTextColor: "#e5eefc",
      primaryBorderColor: "#63a7ff",
      secondaryColor: "#1f2648",
      secondaryTextColor: "#d9e6ff",
      secondaryBorderColor: "#8b7dff",
      tertiaryTextColor: "#d6e2f5",
      lineColor: "#8aa7d1",
      border1: "#6d90c4",
      border2: "#5278b3",
      arrowheadColor: "#8fc0ff",
      clusterBkg: "rgba(30, 41, 59, 0.72)",
      clusterBorder: "#516b95",
      titleColor: "#f3f7ff",
      edgeLabelBackground: "rgba(15, 23, 42, 0.86)",
      textColor: "#edf4ff",
    },
  });
  mermaidConfigured = true;
}

type Props = {
  chart: string;
  className?: string;
};

export function MermaidDiagram({ chart, className = "" }: Props) {
  const id = useId().replace(/:/g, "");
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    configureMermaid();
    const uniqueId = `m-${id}-${Math.random().toString(36).slice(2, 9)}`;
    setError(null);

    let cancelled = false;
    mermaid
      .render(uniqueId, chart)
      .then(({ svg }) => {
        if (!cancelled && el) el.innerHTML = svg;
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message);
      });

    return () => {
      cancelled = true;
    };
  }, [chart, id]);

  if (error) {
    return (
      <div
        className={`rounded-2xl border border-red-400/30 bg-red-950/20 p-4 font-mono text-sm text-red-100 ${className}`}
      >
        Mermaid error: {error}
      </div>
    );
  }

  return (
    <div
      className={`diagram-surface overflow-x-auto rounded-[1.75rem] border border-white/10 bg-[linear-gradient(180deg,rgba(20,29,47,0.82),rgba(17,24,39,0.72))] p-6 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05),0_24px_70px_-24px_rgba(2,6,23,0.9)] backdrop-blur-sm ${className}`}
    >
      <div
        ref={containerRef}
        className="flex min-h-[120px] justify-center text-ink [&_svg]:max-w-full [&_svg]:overflow-visible [&_.edgeLabel]:text-ink-muted [&_.nodeLabel]:text-ink"
      />
    </div>
  );
}
