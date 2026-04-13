import { useCallback, useEffect, useState } from "react";
import type { PipelineRunStatusResponse } from "../types/pipelineRun";

const POLL_MS = 1200;

const EMPTY_STATUS: PipelineRunStatusResponse = {
  ok: true,
  running: false,
  started_at: null,
  finished_at: null,
  exit_code: null,
  logs: [],
  runtime: null,
};

export function usePipelineRuntime() {
  const [status, setStatus] = useState<PipelineRunStatusResponse>(EMPTY_STATUS);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const response = await fetch("/api/pipeline-run/status");
      if (!response.ok) {
        throw new Error("Could not fetch pipeline runtime status.");
      }
      const json = (await response.json()) as PipelineRunStatusResponse;
      setStatus(json);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not fetch pipeline runtime status.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => {
      void refresh();
    }, POLL_MS);
    return () => window.clearInterval(timer);
  }, [refresh]);

  const startRun = useCallback(async () => {
    setStarting(true);
    setError(null);
    try {
      const response = await fetch("/api/pipeline-run/start", {
        method: "POST",
      });
      const payload = (await response.json()) as { ok?: boolean; message?: string };
      if (!response.ok || payload.ok === false) {
        throw new Error(payload.message ?? "Could not start the pipeline.");
      }
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start the pipeline.");
    } finally {
      setStarting(false);
    }
  }, [refresh]);

  return {
    status,
    loading,
    starting,
    error,
    refresh,
    startRun,
  };
}
