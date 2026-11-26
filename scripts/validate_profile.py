"""Offline validation of README references, themes, ASCII integrity and SVG safety.

Optional --check-links writes a network check report to preview/link-check.json.
HTTP 403/429 and social-site bot challenges are reported as unverified, never
silently claimed to be working pages. This option is not part of daily CI.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import json
import re
import xml.etree.ElementTree as ET
from urllib.parse import unquote, urlparse

try:
    from .common import ROOT, replace_section
except ImportError:
    from common import ROOT, replace_section


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ("href", "src", "srcset") and value:
                self.references.append(value)


def references(text):
    parser = References()
    parser.feed(text)
    return parser.references + re.findall(r'(?<!!)\[[^\]]+\]\(([^\s)]+)\)', text)


def validate(root=ROOT):
    readme = (root / "README.md").read_text(encoding="utf-8")
    for name in ("PROJECTS", "STATS", "STACK"):
        replace_section(readme, name, "")
    for ref in references(readme):
        parsed = urlparse(ref)
        if parsed.scheme or ref.startswith("#"):
            continue
        local = root / unquote(parsed.path)
        if not local.exists():
            raise ValueError(f"Missing local README target: {ref}")
    count = 0
    for path in (root / "assets").rglob("*.svg"):
        svg = ET.parse(path).getroot()
        if svg.tag.split("}")[-1] != "svg":
            raise ValueError(f"Invalid SVG: {path}")
        for element in svg.iter():
            tag = element.tag.split("}")[-1]
            if tag in ("script", "foreignObject", "image", "animate", "animateTransform", "set"):
                raise ValueError(f"Active content or raster in {path}")
            for key, value in element.attrib.items():
                if key.lower().startswith("on") or (key.split("}")[-1] == "href" and not value.startswith("#")):
                    raise ValueError(f"External or active SVG reference in {path}")
        if path.parent.name == "ascii":
            for element in svg.iter():
                tag = element.tag.split("}")[-1]
                if tag not in {"svg", "title", "desc", "rect", "g", "text"}:
                    raise ValueError(f"Portrait contains non-ASCII graphics: {path}")
                if tag == "text" and not all(32 <= ord(c) <= 126 for c in (element.text or "")):
                    raise ValueError(f"Portrait contains non-ASCII characters: {path}")
        count += 1
    for theme in ("light", "dark"):
        for path in (f"assets/banners/header-{theme}.svg", f"assets/ascii/portrait-{theme}.svg", f"assets/stats/activity-{theme}.svg"):
            if not (root / path).exists():
                raise ValueError(f"Missing themed asset: {path}")
    rows = (root / "assets/ascii/portrait.txt").read_text(encoding="ascii").splitlines()
    if not rows or len({len(row) for row in rows}) != 1 or not all(32 <= ord(c) <= 126 for row in rows for c in row):
        raise ValueError("ASCII text has inconsistent dimensions or nonprintable glyphs")
    print(f"Validated {count} self-contained SVGs, theme assets, printable ASCII and all local README targets")


def check_links():
    import requests
    urls = sorted({r for r in references((ROOT / "README.md").read_text(encoding="utf-8")) if r.startswith("https://")})
    def check(url):
        try:
            response = requests.get(url, timeout=25, headers={"User-Agent":"Mozilla/5.0 (compatible; profile-link-validator/1.0)"}, stream=True)
            status = response.status_code
            final = response.url
            response.close()
            state = "reachable" if 200 <= status < 400 else "unverified" if status in (401,403,405,429,999) else "failed"
            return {"url":url, "status":status, "result":state, "final_url":final}
        except requests.RequestException:
            return {"url":url, "result":"unverified", "reason":"network error or timeout"}
    with ThreadPoolExecutor(max_workers=5) as pool:
        result = list(pool.map(check,urls))
    output = ROOT / "preview/link-check.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    for item in result:
        print(f"{item['result']}: {item['url']} ({item.get('status','network')})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-links", action="store_true")
    args = parser.parse_args()
    validate()
    if args.check_links:
        check_links()
