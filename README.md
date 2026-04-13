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
│   ├── bronze/       # 🥉 Bronze layer: Raw source data (read-only)
│   ├── silver/       # 🥈 Silver layer: Cleaned & standardized data
│   └── gold/         # 🥇 Gold layer: Business-aggregated reports
└── src/
    ├── main.py       # Entry point
    ├── core/
    ├── repositories/
    ├── services/
    ├── factories/
    └── di/
```

## Data Architecture (Medallion Pattern)

This project follows the **Medallion Architecture** with three data quality layers:

### 🥉 Bronze Layer (`data/bronze/`)
- **Purpose**: Raw data ingestion zone
- **Characteristics**: Immutable source files, no transformations
- **Contents**:
  - `sales_builder_a.csv`, `sales_builder_b.csv` - Raw sales records
  - `target_sales_builder_a.xlsx`, `target_sales_builder_b.csv` - Raw target data
- **Used by**: `FileRepository`, `APIRepository`

### 🥈 Silver Layer (`data/silver/`)
- **Purpose**: Cleaned and standardized zone
- **Characteristics**: Deduplicated, outlier-filtered, date/community standardized
- **Contents** (generated after pipeline execution):
  - `sales_processed.csv` - Cleaned sales with standardized dates and communities
  - `targets_processed.csv` - Cleaned targets with normalized communities
  - `crm_processed.csv` - Standardized CRM leads with unified date formats
  - `web_traffic_processed.csv` - Processed web traffic with community mapping
- **Used by**: Intermediate storage for audit, debugging, and downstream analysis

### 🥇 Gold Layer (`data/gold/`)
- **Purpose**: Business-aggregated reporting zone
- **Characteristics**: Final metrics table (month × community × builder)
- **Contents**:
  - `final_dataframe.csv` - Final metrics with KPIs and derived rates
  - `pipeline_analysis_report.html` - Quality report and execution summary
  - `pipeline_steps_report.json` - Detailed step-by-step execution log
  - `pipeline_runtime_status.json` - Real-time pipeline status for frontend
- **Used by**: Analytics dashboards, business intelligence tools, downstream systems

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

This generates the latest output files under `data/gold/`, including:

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
