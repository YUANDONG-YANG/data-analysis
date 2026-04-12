"""
Local Markdown documentation server: pipeline tour + per-package ARCHITECTURE.md.

Run: python docs_server.py
Open: http://localhost:8081/ (override with env DOCS_SERVER_PORT)
"""
import http.server
import os
import re
import socket
import socketserver
import sys
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import unquote, urlparse

import markdown

PROJECT_ROOT = Path(__file__).resolve().parent
DOCS_DIR = PROJECT_ROOT / "docs"

# Recommended reading order (home page)
PIPELINE_TOUR: List[Tuple[str, str]] = [
    ("01-pipeline-overview.md", "01 Pipeline overview & layer map"),
    ("02-startup-and-config.md", "02 Startup and configuration"),
    ("03-data-ingestion.md", "03 Data ingestion (repositories & API)"),
    ("04-cleaning-and-transformation.md", "04 Cleaning & transformation (DataProcessor)"),
    ("05-metrics.md", "05 Metrics (MetricsCalculator)"),
    ("06-orchestration-and-output.md", "06 Orchestration & output (PipelineService)"),
    ("07-di-and-factories.md", "07 DI & factories"),
]


def _is_under(parent: Path, child: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def resolve_markdown(project_root: Path, docs_dir: Path, rel_url: str) -> Optional[Path]:
    """Resolve URL path to a local .md file, or None if invalid or not allowed."""
    rel = unquote(rel_url).lstrip("/").replace("\\", "/")
    if not rel.endswith(".md"):
        return None
    parts = Path(rel).parts
    if ".." in parts:
        return None

    candidate = (docs_dir / rel).resolve()
    if candidate.is_file() and _is_under(docs_dir, candidate):
        return candidate

    candidate = (project_root / rel).resolve()
    if not candidate.is_file() or not _is_under(project_root, candidate):
        return None

    if candidate.name == "ARCHITECTURE.md":
        return candidate
    if candidate.name == "README.md" and candidate.parent == project_root:
        return candidate
    return None


def collect_architecture_pages(project_root: Path) -> List[Tuple[str, str]]:
    """Return (url, label) pairs for the architecture section on the index page."""
    items: List[Tuple[str, str]] = []
    for path in sorted(project_root.rglob("ARCHITECTURE.md")):
        if not _is_under(project_root, path):
            continue
        try:
            rel = path.relative_to(project_root).as_posix()
        except ValueError:
            continue
        label = path.parent.relative_to(project_root).as_posix()
        if label == ".":
            label = "repository root"
        items.append((rel, f"Architecture · {label}"))
    return items


class MarkdownHandler(http.server.SimpleHTTPRequestHandler):
    """Render allowed Markdown as HTML; index lists the pipeline tour."""

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path.startswith("/"):
            path = path[1:]

        if path in ("", "/"):
            self._send_index_page()
            return

        if path.endswith(".md"):
            self._send_markdown_page(path)
            return

        self.send_error(404, "Only markdown documentation is served. Open / for index.")

    def _send_index_page(self) -> None:
        css = self._get_css()

        tour_items = ""
        for fname, title in PIPELINE_TOUR:
            fpath = DOCS_DIR / fname
            if fpath.is_file():
                tour_items += f'                <li><a href="/{fname}"><strong>{title}</strong></a></li>\n'

        arch_items = ""
        for rel, title in collect_architecture_pages(PROJECT_ROOT):
            arch_items += f'                <li><a href="/{rel}">{title}</a> <code>{rel}</code></li>\n'

        readme_url = ""
        readme_path = PROJECT_ROOT / "README.md"
        if readme_path.is_file():
            readme_url = (
                f'<div class="index-section"><h2>Project readme</h2><ul class="doc-list">'
                f'<li><a href="/README.md">README.md</a> (repository root)</li></ul></div>'
            )

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Documentation — Real Estate Heterogeneous Data Analytics</title>
    <style>{css}</style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Documentation</h1>
            <p class="subtitle">Follow the pipeline tour, then open each package <code>ARCHITECTURE.md</code> for design detail.</p>
        </header>

        <div class="index-section">
            <h2>Data pipeline (recommended order)</h2>
            <p class="hint">From overview to persistence, aligned with <code>PipelineService.execute()</code>.</p>
            <ol class="doc-list ordered">
{tour_items}
            </ol>
        </div>

        <div class="index-section">
            <h2>Architecture deep dives</h2>
            <p class="hint">One file per source folder; Mermaid diagrams render in the browser.</p>
            <ul class="doc-list">
{arch_items}
            </ul>
        </div>

 {readme_url}

        <footer>
            <p>Run <code>python docs_server.py</code> · Stop with <kbd>Ctrl+C</kbd></p>
        </footer>
    </div>
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _send_markdown_page(self, url_path: str) -> None:
        file_path = resolve_markdown(PROJECT_ROOT, DOCS_DIR, url_path)
        if file_path is None:
            self.send_error(404, "File not found or not allowed")
            return

        try:
            md_content = file_path.read_text(encoding="utf-8")
        except OSError as e:
            self.send_error(500, str(e))
            return

        try:
            md = markdown.Markdown(
                extensions=[
                    "codehilite",
                    "fenced_code",
                    "tables",
                    "toc",
                    "nl2br",
                    "sane_lists",
                ],
                extension_configs={
                    "codehilite": {"css_class": "highlight", "use_pygments": False},
                    "toc": {"permalink": True},
                },
            )
        except Exception:
            md = markdown.Markdown(extensions=["fenced_code", "tables", "nl2br"])

        try:
            html_body = md.convert(md_content)
        except Exception as e:
            self._send_md_error(url_path, e)
            return

        title_match = re.search(r"^#\s+(.+)$", md_content, re.MULTILINE)
        title = title_match.group(1) if title_match else file_path.stem
        title_esc = (
            title.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

        try:
            rel_from_root = file_path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
        except ValueError:
            rel_from_root = file_path.name

        mermaid_init = """
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
  mermaid.initialize({ startOnLoad: false, theme: 'neutral', securityLevel: 'loose' });
  document.querySelectorAll('pre code.language-mermaid').forEach(function(code) {
    var pre = code.parentElement;
    var div = document.createElement('div');
    div.className = 'mermaid';
    div.textContent = code.textContent;
    pre.replaceWith(div);
  });
  mermaid.run().catch(function(e) { console.warn('Mermaid:', e); });
});
</script>
"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title_esc}</title>
    <style>{self._get_css()}</style>
</head>
<body>
    <div class="container">
        <nav class="breadcrumb">
            <a href="/">Documentation</a>
            <span> / </span>
            <span>{title_esc}</span>
            <span class="path-hint"><code>{rel_from_root}</code></span>
        </nav>
        <article class="markdown-body">
{html_body}
        </article>
        <footer>
            <a href="/" class="back-link">Back to documentation index</a>
        </footer>
    </div>
{mermaid_init}
</body>
</html>"""

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _send_md_error(self, url_path: str, err: Exception) -> None:
        import traceback

        detail = traceback.format_exc()
        print(f"\n[ERROR] Markdown: {url_path}\n{detail}\n")
        body = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Error</title></head>
<body><h1>Render failed</h1><p>{err}</p><pre>{detail}</pre><p><a href="/">Back</a></p></body></html>"""
        self.send_response(500)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def log_message(self, format: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))

    def _get_css(self) -> str:
        return """
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #24292e;
            background-color: #f6f8fa;
            padding: 20px;
        }
        .container {
            max-width: 980px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
            border-radius: 6px;
        }
        header { border-bottom: 1px solid #eaecef; padding-bottom: 20px; margin-bottom: 30px; }
        h1 { font-size: 2em; margin-bottom: 10px; color: #0366d6; }
        .subtitle { color: #586069; font-size: 1.05em; }
        .hint { color: #586069; font-size: 0.95em; margin-bottom: 12px; }
        .breadcrumb {
            margin-bottom: 20px;
            padding: 10px 0;
            border-bottom: 1px solid #eaecef;
            font-size: 14px;
        }
        .breadcrumb a { color: #0366d6; text-decoration: none; }
        .breadcrumb a:hover { text-decoration: underline; }
        .path-hint { float: right; color: #6a737d; font-size: 12px; }
        .index-section { margin-bottom: 36px; }
        .index-section h2 {
            font-size: 1.45em;
            margin-bottom: 12px;
            color: #24292e;
            border-bottom: 2px solid #eaecef;
            padding-bottom: 8px;
        }
        .doc-list { list-style: none; padding-left: 0; }
        .doc-list.ordered { list-style: decimal; padding-left: 1.5em; }
        .doc-list li {
            margin: 10px 0;
            padding: 10px;
            background: #f6f8fa;
            border-radius: 4px;
        }
        .doc-list a { color: #0366d6; text-decoration: none; font-size: 1.05em; }
        .doc-list a:hover { text-decoration: underline; }
        .markdown-body { font-size: 16px; line-height: 1.6; word-wrap: break-word; }
        .markdown-body h1, .markdown-body h2 {
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            border-bottom: 1px solid #eaecef;
            padding-bottom: 0.3em;
        }
        .markdown-body h1 { font-size: 2em; }
        .markdown-body h2 { font-size: 1.5em; }
        .markdown-body p { margin-bottom: 16px; }
        .markdown-body ul, .markdown-body ol { margin-bottom: 16px; padding-left: 2em; }
        .markdown-body code {
            padding: 0.2em 0.4em;
            font-size: 85%;
            background-color: rgba(27,31,35,0.05);
            border-radius: 3px;
            font-family: Consolas, monospace;
        }
        .markdown-body pre {
            padding: 16px;
            overflow: auto;
            font-size: 85%;
            background-color: #f6f8fa;
            border-radius: 6px;
            margin-bottom: 16px;
        }
        .markdown-body table { border-collapse: collapse; width: 100%; margin-bottom: 16px; }
        .markdown-body th, .markdown-body td { padding: 6px 13px; border: 1px solid #dfe2e5; }
        .markdown-body th { background-color: #f6f8fa; }
        .mermaid { margin: 20px 0; text-align: center; }
        footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eaecef;
            text-align: center;
            color: #586069;
            font-size: 14px;
        }
        .back-link { color: #0366d6; font-weight: 500; }
        """


def main() -> None:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            os.environ["PYTHONIOENCODING"] = "utf-8"

    default_port = int(os.environ.get("DOCS_SERVER_PORT", "8081"))
    port = default_port
    for _ in range(32):
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            in_use = probe.connect_ex(("127.0.0.1", port)) == 0
        finally:
            probe.close()
        if not in_use:
            break
        port += 1

    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    with socketserver.TCPServer(("", port), MarkdownHandler) as httpd:
        print("=" * 60)
        print("Documentation server (Markdown)")
        print("=" * 60)
        print(f"Project root: {PROJECT_ROOT}")
        print(f"Pipeline docs: {DOCS_DIR.resolve()}")
        print(f"Open: http://localhost:{port}/")
        print("=" * 60)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped")
            httpd.shutdown()


if __name__ == "__main__":
    main()
