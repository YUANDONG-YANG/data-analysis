# Real Estate Heterogeneous Data Analytics

Pipeline for combining sales, targets, CRM, and web traffic data to generate monthly community-level reports (heterogeneous real-estate sources).

## Data Sources

- Sales data: CSV files with home sales records (two builders)
- Target data: CSV/Excel files with monthly sales targets
- CRM data: Lead data from API
- Web traffic: Website traffic metrics from API

## Output

Monthly community-level reports including:

**Note**: Output includes future target-only months (through 2026-12) for planning. These records have zero actual sales and represent forecast data.

**Required metrics:** actual sales, target sales, variance, CRM lead count, web traffic (sessions).

**Additional metrics:** estimated revenue, achievement rate, estimated average sale price, conversion rate (leads to sales), traffic to sales rate.

## Project Structure

```
real-estate-heterogeneous-analytics/
├── README.md
├── requirements.txt
├── config.yaml
├── data/
│   ├── raw/          # Source data (read-only)
│   ├── processed/    # Inputs used by the pipeline (see config paths)
│   └── output/       # Generated reports
└── src/
    ├── main.py       # Entry point
    ├── core/
    ├── repositories/
    ├── services/
    ├── factories/
    └── di/
```

## Installation

Python 3.8+ required.

```bash
pip install -r requirements.txt
```

## Configuration

Edit `config.yaml`: API endpoints, data paths, logging, and optional `community_names` (aliases and URL path slugs for normalization).

## Quick Start

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the backend pipeline

From the repository root:

```bash
python -m src.main
```

This generates the latest output files under `data/output/`, including:

- `final_dataframe.csv`
- `pipeline_analysis_report.html`
- `pipeline_steps_report.json`
- `pipeline_runtime_status.json`

### 3. Start the front-end UI

The repository also includes a React front-end under `frontend/` for the pipeline tour, the live step-by-step demo, and the integration/governance explanation pages.

```bash
cd frontend
npm install
npm run dev
```

Then open the local URL printed by Vite (typically **`http://127.0.0.1:5173/`**).

### 4. Use the live pipeline demo

To see the latest real pipeline output in **`/live-demo`**, run the backend pipeline first as shown above. The front-end reads:

- `data/output/pipeline_steps_report.json`
- `data/output/pipeline_runtime_status.json`

You can also start the backend pipeline directly from the front-end home page using the **Start backend pipeline** button.

## Running

If you only want to run the backend pipeline without the front-end:

```bash
python src/main.py
```

## Documentation

### MkDocs (recommended: full site + Mermaid)

Install dependencies (includes MkDocs), then build and optionally serve:

```bash
pip install -r requirements.txt
mkdocs build --strict
```

- Static HTML output is written to **`site/`** (open `site/index.html` or use a local static server).
- Live preview: `mkdocs serve` → **http://127.0.0.1:8081/**

Configuration: **`mkdocs.yml`** (and **`mkdocs_hooks.py`**, which lowers mermaid2 plugin log noise during `mkdocs build`). Pipeline chapters and `ARCHITECTURE.md` files (via `docs/reference/`) are in the nav; Mermaid diagrams use **`mkdocs-mermaid2-plugin`**.

### Simple Markdown server (optional)

```bash
python docs_server.py
```

Opens **http://localhost:8081/** with a lightweight index (see `start_docs_server.bat` on Windows). Override port with env `DOCS_SERVER_PORT`.

## Testing

```bash
pytest
pytest --cov=src.services --cov=src.core.calculators --cov=src.core.processors --cov-report=html
```

## Data Quality Processing

- Date format standardization (multiple formats supported)
- Community name normalization (config-driven variants)
- Outlier filtering (removes extreme values)
- Missing value handling

## Output Format

Output CSV: `data/output/final_dataframe.csv`

Columns: `month`, `community_name`, `builder`, `actual_sales`, `target_sales`, `variance`, `crm_leads`, `web_traffic`, `estimated_revenue`, `achievement_rate`, `estimated_avg_sale_price`, `conversion_rate`, `traffic_to_sales_rate`.

Sorted by: month (asc), builder (asc), community_name (asc).
