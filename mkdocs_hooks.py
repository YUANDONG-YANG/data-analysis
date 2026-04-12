"""MkDocs hooks: reduce verbose INFO lines from mkdocs-mermaid2-plugin during build/serve."""
import logging


def on_startup(*, command, dirty) -> None:
    logging.getLogger("mkdocs.plugins.mermaid2.util").setLevel(logging.WARNING)
