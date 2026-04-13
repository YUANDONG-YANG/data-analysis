# Pipeline documentation UI (React)

Premium front-end for the **Pipeline tour** (content mirrors `docs/01-*.md` … `07-*.md`).

```bash
cd frontend
npm install
npm run dev
```

Open the printed local URL (default `http://127.0.0.1:5173`). Production build: `npm run build`, static files in `dist/`.

## Step-by-step pipeline demo (`/live-demo`)

1. From the **repository root**, run `python -m src.main` once. This writes `data/gold/pipeline_steps_report.json` (and CSV/HTML reports).
2. Start the Vite dev server (`npm run dev` in `frontend/`). The dev server exposes that JSON at `/api/pipeline-steps.json`, so **Pipeline step demo** (`/live-demo`) shows the **latest real run**.
3. If the API file is missing, the UI falls back to `public/pipeline_steps_report.sample.json` (copy of a real run, for offline/demo).

The MkDocs site (`mkdocs serve`, port 8081) remains available for full **Architecture** pages and search; this app adds the interactive tour plus the live six-step demo.
