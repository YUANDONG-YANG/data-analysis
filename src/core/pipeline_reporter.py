"""
Pipeline step snapshots, before/after comparison logging, and HTML analysis report.
"""
from __future__ import annotations

import html
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


def dataframe_snapshot(df: pd.DataFrame, label: str) -> Dict[str, Any]:
    """Build a JSON-serializable summary of a DataFrame for logs and HTML."""
    if df is None:
        return {"label": label, "rows": 0, "cols": 0, "columns": [], "memory_bytes": 0, "null_cells": 0, "duplicate_rows": 0}
    rows = len(df)
    cols = len(df.columns)
    null_cells = int(df.isna().sum().sum()) if rows and cols else 0
    dup = int(df.duplicated().sum()) if rows else 0
    mem = int(df.memory_usage(deep=True).sum()) if rows else 0
    return {
        "label": label,
        "rows": rows,
        "cols": cols,
        "columns": [str(c) for c in df.columns.tolist()],
        "memory_bytes": mem,
        "null_cells": null_cells,
        "duplicate_rows": dup,
    }


def snapshot_delta(before: Optional[Dict[str, Any]], after: Dict[str, Any]) -> Dict[str, Any]:
    """Numeric deltas for logging (rows, memory)."""
    if not before:
        return {"rows_delta": after.get("rows", 0), "cols_delta": after.get("cols", 0), "memory_delta_bytes": after.get("memory_bytes", 0)}
    return {
        "rows_delta": after.get("rows", 0) - before.get("rows", 0),
        "cols_delta": after.get("cols", 0) - before.get("cols", 0),
        "memory_delta_bytes": after.get("memory_bytes", 0) - before.get("memory_bytes", 0),
    }


def input_bundle_snapshot(
    sales: pd.DataFrame,
    targets: pd.DataFrame,
    crm: pd.DataFrame,
    web: pd.DataFrame,
) -> Dict[str, Any]:
    """Single 'before' snapshot for the metrics step (four inputs)."""
    parts = [
        dataframe_snapshot(sales, "sales"),
        dataframe_snapshot(targets, "targets"),
        dataframe_snapshot(crm, "crm"),
        dataframe_snapshot(web, "web_traffic"),
    ]
    return {
        "label": "inputs_before_metrics",
        "type": "bundle",
        "parts": parts,
        "sum_rows": sum(p["rows"] for p in parts),
    }


def _before_rows_for_log(before: Optional[Dict[str, Any]]) -> Any:
    if not before:
        return "N/A"
    if before.get("type") == "bundle":
        return before.get("sum_rows")
    return before.get("rows")


def log_step_compare(
    logger: logging.Logger,
    pipeline_id: str,
    step: str,
    title: str,
    before: Optional[Dict[str, Any]],
    after: Dict[str, Any],
    duration_sec: Optional[float] = None,
) -> None:
    """Emit one structured INFO log with before/after and delta."""
    delta = snapshot_delta(before, after)
    extra: Dict[str, Any] = {
        "context": {
            "pipeline_id": pipeline_id,
            "step": step,
            "step_title": title,
            "before": before,
            "after": after,
            "delta": delta,
        }
    }
    if duration_sec is not None:
        extra["performance"] = {"step_seconds": round(duration_sec, 4)}
    logger.info(
        f"[{step}] {title} | before_rows={_before_rows_for_log(before)} "
        f"after_rows={after.get('rows')} delta_rows={delta.get('rows_delta')}",
        extra=extra,
    )


def log_internal_transition(
    logger: logging.Logger,
    domain: str,
    operation: str,
    before_snap: Dict[str, Any],
    after_snap: Dict[str, Any],
) -> None:
    """Log merge→clean→process style transitions inside DataService."""
    d = snapshot_delta(before_snap, after_snap)
    logger.info(
        f"[{domain}] {operation}: rows {before_snap.get('rows')} → {after_snap.get('rows')} "
        f"(Δ {d.get('rows_delta')})",
        extra={
            "context": {
                "domain": domain,
                "operation": operation,
                "before": before_snap,
                "after": after_snap,
                "delta": d,
            }
        },
    )


def dataframe_to_preview_dict(df: pd.DataFrame, max_rows: int = 15) -> Dict[str, Any]:
    """
    Serialize the first ``max_rows`` of a DataFrame to JSON-friendly columns + rows.
    Used by the React pipeline demo and ``pipeline_steps_report.json``.
    """
    if df is None:
        return {"columns": [], "rows": [], "truncated": False, "total_rows": 0, "preview_rows": 0}
    total_rows = len(df)
    if total_rows == 0:
        return {
            "columns": [str(c) for c in df.columns],
            "rows": [],
            "truncated": False,
            "total_rows": 0,
            "preview_rows": 0,
        }
    sub = df.head(max_rows)
    raw_json = sub.to_json(orient="records", date_format="iso", double_precision=15)
    rows = json.loads(raw_json)
    return {
        "columns": [str(c) for c in sub.columns],
        "rows": rows,
        "truncated": total_rows > max_rows,
        "total_rows": int(total_rows),
        "preview_rows": len(rows),
    }


def write_pipeline_steps_json(
    output_path: Path,
    pipeline_id: str,
    run_mode: str,
    environment: str,
    total_seconds: Optional[float],
    step_entries: List[Dict[str, Any]],
    csv_filename: str,
    csv_checksum: str,
    quality_report: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Write machine-readable pipeline run for the React step-by-step demo.

    File name: ``pipeline_steps_report.json`` next to CSV/HTML output.
    """
    output_path = Path(output_path)
    report_path = output_path / "pipeline_steps_report.json"
    payload: Dict[str, Any] = {
        "version": 1,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "pipeline_id": pipeline_id,
        "run_mode": run_mode,
        "environment": environment,
        "total_seconds": round(total_seconds, 4) if total_seconds is not None else None,
        "output_csv": csv_filename,
        "output_checksum_md5": csv_checksum,
        "steps": step_entries,
    }
    if quality_report is not None:
        payload["quality_report"] = json.loads(json.dumps(quality_report, default=str))

    report_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return report_path


def write_pipeline_runtime_status_json(
    output_path: Path,
    pipeline_id: str,
    run_mode: str,
    environment: str,
    status: str,
    started_at: str,
    step_entries: List[Dict[str, Any]],
    current_step: Optional[str] = None,
    current_title: Optional[str] = None,
    total_seconds: Optional[float] = None,
    finished_at: Optional[str] = None,
    output_csv: Optional[str] = None,
    output_checksum_md5: Optional[str] = None,
    quality_report: Optional[Dict[str, Any]] = None,
    error: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Write incremental runtime status for the live front-end monitor.

    File name: ``pipeline_runtime_status.json`` next to other output artifacts.
    """
    output_path = Path(output_path)
    report_path = output_path / "pipeline_runtime_status.json"
    payload: Dict[str, Any] = {
        "version": 1,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "pipeline_id": pipeline_id,
        "run_mode": run_mode,
        "environment": environment,
        "status": status,
        "started_at": started_at,
        "current_step": current_step,
        "current_title": current_title,
        "total_seconds": round(total_seconds, 4) if total_seconds is not None else None,
        "steps": step_entries,
    }
    if finished_at is not None:
        payload["finished_at"] = finished_at
    if output_csv is not None:
        payload["output_csv"] = output_csv
    if output_checksum_md5 is not None:
        payload["output_checksum_md5"] = output_checksum_md5
    if quality_report is not None:
        payload["quality_report"] = json.loads(json.dumps(quality_report, default=str))
    if error is not None:
        payload["error"] = json.loads(json.dumps(error, default=str))

    report_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return report_path


def _fmt_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.2f} MB"


def write_pipeline_analysis_html(
    output_path: Path,
    pipeline_id: str,
    run_mode: str,
    environment: str,
    step_entries: List[Dict[str, Any]],
    metrics_df: pd.DataFrame,
    csv_filename: str,
    csv_checksum: str,
    quality_report: Optional[Dict[str, Any]] = None,
    total_seconds: Optional[float] = None,
    preview_rows: int = 40,
) -> Path:
    """
    Write a standalone HTML report for visual before/after analysis and output preview.

    Returns path to the written file.
    """
    output_path = Path(output_path)
    report_path = output_path / "pipeline_analysis_report.html"
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rows_html = ""
    for entry in step_entries:
        bid = html.escape(str(entry.get("step", "")))
        title = html.escape(str(entry.get("title", "")))
        dur = entry.get("duration_sec")
        dur_s = f"{dur:.3f}s" if dur is not None else "—"
        before = entry.get("before")
        after = entry.get("after")
        drows_disp = entry.get("delta_display")
        if drows_disp is None and after:
            drows_disp = str(snapshot_delta(before, after).get("rows_delta"))
        before_j = html.escape(json.dumps(before, indent=2, ensure_ascii=False) if before else "null")
        after_j = html.escape(json.dumps(after, indent=2, ensure_ascii=False) if after else "null")
        rows_html += f"""
        <tr>
          <td><strong>{bid}</strong><br/><span class="muted">{title}</span></td>
          <td>{dur_s}</td>
          <td><pre>{before_j}</pre></td>
          <td><pre>{after_j}</pre></td>
          <td class="num">{html.escape(str(drows_disp))}</td>
        </tr>"""

    # Preview table
    preview = metrics_df.head(preview_rows) if not metrics_df.empty else pd.DataFrame()
    thead = ""
    if not preview.empty:
        thead = "<tr>" + "".join(f"<th>{html.escape(str(c))}</th>" for c in preview.columns) + "</tr>"
    tbody = ""
    for _, row in preview.iterrows():
        tbody += "<tr>"
        for v in row:
            s = "" if pd.isna(v) else str(v)
            tbody += f"<td>{html.escape(s)}</td>"
        tbody += "</tr>"

    numeric_summary = ""
    if not metrics_df.empty:
        num_cols = metrics_df.select_dtypes(include=["number"]).columns.tolist()
        if num_cols:
            desc = metrics_df[num_cols].describe().transpose()
            numeric_summary = "<h3>Numeric columns (describe)</h3><table class='grid'><thead><tr>"
            numeric_summary += "<th>column</th><th>count</th><th>mean</th><th>std</th><th>min</th><th>max</th></tr></thead><tbody>"
            for col in num_cols:
                if col in desc.index:
                    r = desc.loc[col]
                    mean_v = r.get("mean", 0)
                    std_v = r.get("std", 0)
                    mean_s = str(round(float(mean_v), 4)) if pd.notna(mean_v) else ""
                    std_s = str(round(float(std_v), 4)) if pd.notna(std_v) else ""
                    numeric_summary += (
                        "<tr>"
                        f"<td>{html.escape(str(col))}</td>"
                        f"<td class='num'>{html.escape(str(r.get('count', '')))}</td>"
                        f"<td class='num'>{html.escape(mean_s)}</td>"
                        f"<td class='num'>{html.escape(std_s)}</td>"
                        f"<td class='num'>{html.escape(str(r.get('min', '')))}</td>"
                        f"<td class='num'>{html.escape(str(r.get('max', '')))}</td>"
                        "</tr>"
                    )
            numeric_summary += "</tbody></table>"

    q_html = ""
    if quality_report:
        q_html = (
            "<h3>Quality summary</h3><pre class='box'>"
            f"{html.escape(json.dumps(quality_report, indent=2, ensure_ascii=False, default=str))}"
            "</pre>"
        )

    total_line = f"<p><strong>Total pipeline time:</strong> {total_seconds:.3f}s</p>" if total_seconds else ""

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Pipeline analysis — {html.escape(pipeline_id)}</title>
  <style>
    body {{ font-family: Segoe UI, system-ui, sans-serif; margin: 24px; background: #f6f8fa; color: #24292e; }}
    h1 {{ font-size: 1.35rem; }}
    .meta {{ color: #57606a; margin-bottom: 20px; }}
    table.grid {{ border-collapse: collapse; width: 100%; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
    table.grid th, table.grid td {{ border: 1px solid #d0d7de; padding: 8px 10px; vertical-align: top; }}
    table.grid th {{ background: #f6f8fa; text-align: left; }}
    pre {{ margin: 0; font-size: 11px; max-height: 220px; overflow: auto; background: #f6f8fa; padding: 8px; }}
    .num {{ text-align: right; font-variant-numeric: tabular-nums; }}
    .muted {{ color: #57606a; font-size: 0.9em; }}
    .box {{ background: #fff; padding: 12px; border: 1px solid #d0d7de; overflow: auto; }}
    h2 {{ margin-top: 28px; font-size: 1.1rem; border-bottom: 1px solid #d0d7de; padding-bottom: 6px; }}
    h3 {{ font-size: 1rem; margin-top: 16px; }}
  </style>
</head>
<body>
  <h1>Pipeline before / after analysis</h1>
  <div class="meta">
    <div><strong>Pipeline ID:</strong> {html.escape(pipeline_id)}</div>
    <div><strong>Generated:</strong> {html.escape(ts)}</div>
    <div><strong>Mode:</strong> {html.escape(run_mode)} &nbsp;|&nbsp; <strong>Environment:</strong> {html.escape(environment)}</div>
    <div><strong>Output CSV:</strong> {html.escape(csv_filename)} &nbsp;|&nbsp; <strong>MD5:</strong> <code>{html.escape(csv_checksum)}</code></div>
    <div><strong>Output rows × columns:</strong> {len(metrics_df)} × {len(metrics_df.columns)} &nbsp;|&nbsp; Memory ~ {_fmt_bytes(int(metrics_df.memory_usage(deep=True).sum()) if not metrics_df.empty else 0)}</div>
    {total_line}
  </div>

  <h2>Step-by-step snapshots (before → after)</h2>
  <p class="muted">Each step stores JSON snapshots: rows, cols, columns, memory, nulls, duplicates. Delta rows = after.rows − before.rows (bundle steps use synthetic before).</p>
  <table class="grid">
    <thead>
      <tr>
        <th>Step</th>
        <th>Duration</th>
        <th>Before</th>
        <th>After</th>
        <th>Δ rows</th>
      </tr>
    </thead>
    <tbody>
    {rows_html}
    </tbody>
  </table>

  {q_html}

  <h2>Output data preview (first {preview_rows} rows)</h2>
  <div style="overflow:auto">
    <table class="grid">
      <thead>{thead}</thead>
      <tbody>{tbody}</tbody>
    </table>
  </div>

  {numeric_summary}

  <p class="muted" style="margin-top:32px">Open <code>final_dataframe.csv</code> in the same folder for full data. Regenerate this report by running the pipeline.</p>
</body>
</html>"""
    report_path.write_text(html_doc, encoding="utf-8")
    return report_path
