export type DeltaMergeMetrics = {
  rows_inserted?: number;
  rows_updated?: number;
  rows_deleted?: number;
};

export type DeltaTableInfo = {
  name: string;
  path: string;
  merge_keys: string[];
  table_version: number;
  last_operation: string;
  metrics?: DeltaMergeMetrics;
};

export type DeltaVersionHistoryEntry = {
  version: number;
  pipeline_id: string;
  at: string;
};

export type DeltaSnapshotPayload = {
  version: number;
  generated_at: string;
  pipeline_id: string;
  notes?: string;
  tables: DeltaTableInfo[];
  history?: DeltaVersionHistoryEntry[];
};

export function isDeltaSnapshotPayload(x: unknown): x is DeltaSnapshotPayload {
  if (!x || typeof x !== "object") return false;
  const o = x as Record<string, unknown>;
  return (
    typeof o.version === "number" &&
    typeof o.generated_at === "string" &&
    typeof o.pipeline_id === "string" &&
    Array.isArray(o.tables)
  );
}
