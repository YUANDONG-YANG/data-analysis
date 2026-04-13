import { useCallback, useEffect, useState } from "react";

const POLL_MS = 1500;

type FinalOutputStatus = {
  ok: boolean;
  available: boolean;
};

const EMPTY_STATUS: FinalOutputStatus = {
  ok: true,
  available: false,
};

export function useFinalOutputStatus() {
  const [status, setStatus] = useState<FinalOutputStatus>(EMPTY_STATUS);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const response = await fetch("/api/final-data/status");
      if (!response.ok) {
        throw new Error("Could not fetch final output status.");
      }
      const payload = (await response.json()) as FinalOutputStatus;
      setStatus(payload);
    } catch {
      setStatus(EMPTY_STATUS);
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

  return {
    status,
    loading,
    refresh,
  };
}
