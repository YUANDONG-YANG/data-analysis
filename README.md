# Real Estate Heterogeneous Data Analytics

A data-integration assessment project that **blends file-based sales and targets with API-backed CRM and web-traffic feeds**, then produces **month × community × builder** metrics for reporting and exploration.

---

## Design philosophy

### Medallion-style data layers

The repo organizes data by **quality stage**, not by ad-hoc folders:

| Layer | Role |
|--------|------|
| **Bronze** (`data/bronze/`) | Raw, immutable inputs (CSV/Excel sales and targets). |
| **Silver** (`data/silver/`) | Cleaned, deduplicated, standardized tables written after each processing step—useful for audit and debugging. |
| **Gold** (`data/gold/`) | Final business outputs: metrics CSV, HTML analysis report, JSON step logs, and runtime status consumed by tooling and the UI. |

This keeps **ingestion**, **transformation**, and **consumption** visually and operationally separate: you always know whether you are looking at source files, intermediate quality, or publishable results.

### Application architecture

- **Composition root** (`src/main.py`) loads configuration, builds collaborators, and runs the pipeline—no hidden globals.
- **Dependency injection** (`src/di/`) wires repositories and services so orchestration stays testable and explicit.
- **Factories** (`RepositoryFactory`, `ServiceFactory`) construct object graphs from config without leaking construction details into domain code.
- **Repositories** abstract **where** data comes from (`FileRepository` for bronze files, `APIRepository` for CRM and traffic).
- **Application services** coordinate use cases: `DataService` loads and processes each domain; `MetricsService` computes KPIs; **`PipelineService`** is the façade that runs the fixed **load → metrics → save** workflow and structured logging.

The mental model is: **config-driven wiring**, **clear boundaries** between infrastructure and business steps, and a **single orchestrated pipeline** instead of scattered scripts.

### What the front end is for

The **Vite + React** app under `frontend/` is the primary way to **read the story of the system**: guided pipeline content (aligned with `docs/`), Mermaid-style diagrams in the browser, a **step-by-step live demo**, and charts driven by the gold-layer CSV when present. You do **not** need Python or MkDocs running to use it for exploration—the dev server can serve **sample** pipeline JSON when `data/gold/` has not been generated yet.

---

## Getting started (front end only)

**Prerequisites:** [Node.js](https://nodejs.org/) (LTS recommended) and **npm**.

From the **repository root**:

```bash
cd frontend
npm install
npm run dev
```

Open the URL Vite prints—typically **`http://127.0.0.1:5173`**.

That is all you need to browse the UI. If `data/gold/pipeline_steps_report.json` (and related outputs) exist from a prior backend run, the **live demo** and analysis pages will show **real** run data; otherwise the app falls back to bundled sample JSON under `frontend/public/` so the tour still works offline.

---

## Optional: backend pipeline

To regenerate **Gold** artifacts (CSV, reports, JSON) yourself, use Python 3.8+, install `requirements.txt`, configure `config.yaml`, then from the repo root run `python -m src.main`. The front end reads outputs under **`data/gold/`** (see `frontend/vite.config.ts` for dev proxies). This step is **not** required simply to start and explore the front end.

---

## License & context

This repository is structured as an assessment/demo: heterogeneous real-estate sources (files + APIs) are merged into one analytical surface, with emphasis on clear layering, explicit wiring, and inspectable outputs.
