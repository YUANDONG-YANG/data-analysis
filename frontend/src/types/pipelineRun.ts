export type OutputPreview = {
  columns: string[];
  rows: Record<string, unknown>[];
  truncated: boolean;
  total_rows: number;
  preview_rows: number;
};

export type PipelineStepEntry = {
  step: string;
  title: string;
  before?: unknown;
  after?: unknown;
  duration_sec?: number;
  delta_display?: string;
  output_preview?: OutputPreview;
  conversion_stats?: Record<string, unknown>;
};

export type PipelineRunPayload = {
  version: number;
  generated_at: string;
  pipeline_id: string;
  run_mode: string;
  environment: string;
  total_seconds: number | null;
  output_csv: string;
  output_checksum_md5: string;
  steps: PipelineStepEntry[];
  quality_report?: unknown;
};

export type PipelineRuntimePayload = {
  version: number;
  updated_at: string;
  pipeline_id: string;
  run_mode: string;
  environment: string;
  status: "starting" | "running" | "completed" | "failed";
  started_at: string;
  current_step?: string | null;
  current_title?: string | null;
  total_seconds: number | null;
  finished_at?: string;
  output_csv?: string;
  output_checksum_md5?: string;
  steps: PipelineStepEntry[];
  quality_report?: unknown;
  error?: Record<string, unknown>;
};

export type PipelineRunStatusResponse = {
  ok: boolean;
  running: boolean;
  started_at: string | null;
  finished_at: string | null;
  exit_code: number | null;
  logs: string[];
  runtime: PipelineRuntimePayload | null;
};
