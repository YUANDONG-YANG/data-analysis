import { useEffect, useState } from "react";
import type { PipelineRunPayload } from "../types/pipelineRun";

export type PipelineDataSource = "live" | "sample" | "none";

function isPayload(v: unknown): v is PipelineRunPayload {
  if (!v || typeof v !== "object") return false;
  const o = v as Record<string, unknown>;
  return Array.isArray(o.steps) && typeof o.pipeline_id === "string";
}

export function usePipelineRun() {
  const [data, setData] = useState<PipelineRunPayload | null>(null);
  const [source, setSource] = useState<PipelineDataSource>("none");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function tryFetch(url: string): Promise<PipelineRunPayload | null> {
      const r = await fetch(url);
      if (!r.ok) return null;
      const j: unknown = await r.json();
      if (j && typeof j === "object" && "ok" in j && (j as { ok?: boolean }).ok === false) {
        return null;
      }
      return isPayload(j) ? j : null;
    }

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const live = await tryFetch("/api/pipeline-steps.json");
        if (!cancelled && live) {
          setData(live);
          setSource("live");
          setLoading(false);
          return;
        }
      } catch {
        /* try sample */
      }
      try {
        const sample = await tryFetch("/pipeline_steps_report.sample.json");
        if (!cancelled && sample) {
          setData(sample);
          setSource("sample");
          setLoading(false);
          return;
        }
      } catch {
        /* noop */
      }
      if (!cancelled) {
        setData(null);
        setSource("none");
        setError(
          "No pipeline data found. Run `python -m src.main` from the repo root, or place `pipeline_steps_report.json` under `frontend/public/`.",
        );
      }
      setLoading(false);
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return { data, source, loading, error };
}
