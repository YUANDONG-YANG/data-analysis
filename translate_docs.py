"""
Optional phrase replacement for Markdown files.
Provide a JSON map of source phrase -> English (e.g. legacy zh -> en) as `translation_map.json`
next to this script if you need batch replacements. Empty or missing file means no replacements.
"""
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_MAP = SCRIPT_DIR / "translation_map.json"


def load_translations(path: Path = DEFAULT_MAP) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def translate_file(input_path: Path, output_path: Path, translations: dict) -> None:
    """Apply simple string replacements from ``translations`` and write ``output_path``."""
    content = input_path.read_text(encoding="utf-8")
    for source, target in translations.items():
        content = content.replace(source, target)
    output_path.write_text(content, encoding="utf-8")
    print(f"Wrote: {output_path}")


if __name__ == "__main__":
    print("Load phrases from translation_map.json (optional). See script docstring.")
