"""Small, dependency-free helpers shared by generators."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def read_config(root: Path = ROOT) -> dict:
    config = json.loads((root / "config/categories.json").read_text(encoding="utf-8"))
    cats = config["categories"]
    ids = [c["id"] for c in cats]
    if len(ids) != len(set(ids)) or ids.count("other") != 1:
        raise ValueError("Categories must have unique IDs and exactly one 'other' category")
    if config["visible_per_category"] < 1:
        raise ValueError("visible_per_category must be positive")
    return config


def replace_section(text: str, name: str, body: str) -> str:
    start, end = f"<!-- {name}:START -->", f"<!-- {name}:END -->"
    if text.count(start) != 1 or text.count(end) != 1 or text.index(start) >= text.index(end):
        raise ValueError(f"Expected one ordered {name} marker pair; refusing to rewrite README")
    before, after = text.split(start)[0], text.split(end)[1]
    return f"{before}{start}\n\n{body.strip()}\n\n{end}{after}"


def atomic_write(path: Path, content: str) -> None:
    """Don't touch unchanged files; replace completed UTF-8 files atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return
    fd, temporary = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as file:
            file.write(content)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def safe_url(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = urlparse(value)
        return value if parsed.scheme in ("https", "http") and parsed.hostname and not parsed.username and not any(ord(c) < 32 for c in value) else None
    except ValueError:
        return None
