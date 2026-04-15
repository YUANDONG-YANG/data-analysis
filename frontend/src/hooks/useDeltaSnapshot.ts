import { useCallback, useEffect, useState } from "react";
import { isDeltaSnapshotPayload, type DeltaSnapshotPayload } from "../types/deltaSnapshot";

export type DeltaSnapshotSource = "live" | "sample";

export function useDeltaSnapshot() {
  const [data, setData] = useState<DeltaSnapshotPayload | null>(null);
  const [source, setSource] = useState<DeltaSnapshotSource | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const liveRes = await fetch("/api/delta-snapshot.json", { cache: "no-store" });
      if (liveRes.ok) {
        const json: unknown = await liveRes.json();
        if (isDeltaSnapshotPayload(json)) {
          setData(json);
          setSource("live");
          return;
        }
        setError("Invalid delta snapshot shape from server.");
        setData(null);
        setSource(null);
        return;
      }
      const sampleRes = await fetch("/delta_snapshot.sample.json", { cache: "no-store" });
      if (!sampleRes.ok) {
        setError("Could not load Delta snapshot (live or sample).");
        setData(null);
        setSource(null);
        return;
      }
      const json: unknown = await sampleRes.json();
      if (isDeltaSnapshotPayload(json)) {
        setData(json);
        setSource("sample");
        return;
      }
      setError("Invalid bundled Delta sample.");
      setData(null);
      setSource(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load Delta snapshot.");
      setData(null);
      setSource(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return { data, source, loading, error, reload: load };
}
