import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { IncomingMessage, ServerResponse } from "node:http";
import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import react from "@vitejs/plugin-react";
import type { Plugin } from "vite";
import { defineConfig } from "vite";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, "..");
const finalDataCsv = path.join(repoRoot, "data", "gold", "final_dataframe.csv");
const pipelineStepsJson = path.join(repoRoot, "data", "gold", "pipeline_steps_report.json");
const pipelineRuntimeJson = path.join(repoRoot, "data", "gold", "pipeline_runtime_status.json");

function pipelineStepsApiPlugin(): Plugin {
  let child: ChildProcessWithoutNullStreams | null = null;
  let logs: string[] = [];
  let startedAt: string | null = null;
  let finishedAt: string | null = null;
  let exitCode: number | null = null;

  const appendLog = (chunk: Buffer | string) => {
    const text = chunk.toString();
    const lines = text.split(/\r?\n/).filter(Boolean);
    logs.push(...lines);
    if (logs.length > 500) {
      logs = logs.slice(-500);
    }
  };

  const readJsonFile = (filePath: string) => {
    if (!fs.existsSync(filePath)) return null;
    try {
      return JSON.parse(fs.readFileSync(filePath, "utf-8"));
    } catch {
      return null;
    }
  };

  const respondJson = (res: ServerResponse, statusCode: number, payload: unknown) => {
    res.statusCode = statusCode;
    res.setHeader("Content-Type", "application/json; charset=utf-8");
    res.end(JSON.stringify(payload));
  };

  const serve = (req: IncomingMessage, res: ServerResponse, next: () => void) => {
    const pathname = req.url?.split("?")[0] ?? "";
    if (pathname === "/api/pipeline-steps.json") {
      fs.readFile(pipelineStepsJson, (err, data) => {
        if (err) {
          respondJson(res, 404, {
            ok: false,
            error: "file_not_found",
            hint: "Run: python -m src.main (writes data/gold/pipeline_steps_report.json)",
          });
          return;
        }
        res.setHeader("Content-Type", "application/json; charset=utf-8");
        res.end(data);
      });
      return;
    }

    if (pathname === "/api/pipeline-run/start" && req.method === "POST") {
      if (child && exitCode === null) {
        respondJson(res, 409, {
          ok: false,
          error: "already_running",
          message: "A pipeline run is already in progress.",
        });
        return;
      }

      try {
        fs.rmSync(pipelineRuntimeJson, { force: true });
      } catch {
        /* ignore cleanup issues */
      }

      logs = [];
      startedAt = new Date().toISOString();
      finishedAt = null;
      exitCode = null;
      child = spawn("python", ["-m", "src.main"], {
        cwd: repoRoot,
        env: process.env,
        stdio: ["ignore", "pipe", "pipe"],
      });

      child.stdout.on("data", appendLog);
      child.stderr.on("data", appendLog);
      child.on("error", (err) => {
        appendLog(`Process error: ${err.message}`);
        exitCode = -1;
        finishedAt = new Date().toISOString();
        child = null;
      });
      child.on("close", (code) => {
        exitCode = code ?? null;
        finishedAt = new Date().toISOString();
        child = null;
      });

      respondJson(res, 200, {
        ok: true,
        running: true,
        started_at: startedAt,
      });
      return;
    }

    if (pathname === "/api/pipeline-run/status") {
      const runtime = readJsonFile(pipelineRuntimeJson);
      respondJson(res, 200, {
        ok: true,
        running: Boolean(child && exitCode === null),
        started_at: startedAt,
        finished_at: finishedAt,
        exit_code: exitCode,
        logs: logs.slice(-120),
        runtime,
      });
      return;
    }

    if (pathname === "/api/final-data.csv") {
      fs.readFile(finalDataCsv, (err, data) => {
        if (err) {
          respondJson(res, 404, {
            ok: false,
            error: "file_not_found",
            hint: "Run: python -m src.main (writes data/gold/final_dataframe.csv)",
          });
          return;
        }
        res.statusCode = 200;
        res.setHeader("Content-Type", "text/csv; charset=utf-8");
        res.end(data);
      });
      return;
    }

    if (pathname === "/api/final-data/status") {
      respondJson(res, 200, {
        ok: true,
        available: fs.existsSync(finalDataCsv),
      });
      return;
    }

    next();
  };

  return {
    name: "pipeline-steps-api",
    configureServer(server) {
      server.middlewares.use(serve);
    },
    configurePreviewServer(server) {
      server.middlewares.use(serve);
    },
  };
}

export default defineConfig({
  plugins: [react(), pipelineStepsApiPlugin()],
  server: {
    port: 5173,
    strictPort: false,
  },
});
