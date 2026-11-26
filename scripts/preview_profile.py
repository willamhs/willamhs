"""Build a local Markdown preview. Serve the repository with http.server.

This preview alone uses CSS; README and its assets need no page styles or JS.
"""
from __future__ import annotations

from pathlib import Path
import re

import markdown
import requests

try:
    from .common import ROOT, atomic_write
except ImportError:
    from common import ROOT, atomic_write


def main():
    output = ROOT / "preview"
    output.mkdir(exist_ok=True)
    css = output / "github-markdown.css"
    if not css.exists():
        response = requests.get("https://cdn.jsdelivr.net/npm/github-markdown-css@5.8.1/github-markdown.css",timeout=30)
        response.raise_for_status()
        atomic_write(css,response.text)
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    # Python Markdown needs this preview-only hint to parse Markdown in details.
    text = text.replace("<details>",'<details markdown="1">')
    content = markdown.markdown(text,extensions=["extra","sane_lists"])
    html = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="color-scheme" content="light dark"><base href="../">'
        '<title>Willam | Data &amp; AI — profile preview</title>'
        '<link rel="stylesheet" href="preview/github-markdown.css">'
        '<style>body{margin:0;background:#fff}.markdown-body{box-sizing:border-box;max-width:946px;margin:32px auto;padding:32px;border:1px solid #d1d9e0;border-radius:12px}.markdown-body img{max-width:100%;height:auto}.markdown-body p a img{margin:3px 1px}.markdown-body details{margin:16px 0}.markdown-body h4{margin-bottom:8px}.markdown-body h4+p{margin-bottom:8px}@media(prefers-color-scheme:dark){body{background:#0d1117}.markdown-body{border-color:#30363d}}@media(max-width:600px){.markdown-body{margin:0;border:0;border-radius:0;padding:20px 16px}}</style>'
        '</head><body><article class="markdown-body">' + content + '</article></body></html>')
    atomic_write(output / "index.html",html)
    for theme in ("light", "dark"):
        theme_css = output / f"github-markdown-{theme}.css"
        if not theme_css.exists():
            response = requests.get(f"https://cdn.jsdelivr.net/npm/github-markdown-css@5.8.1/github-markdown-{theme}.css",timeout=30)
            response.raise_for_status()
            atomic_write(theme_css,response.text)
        themed = html.replace("preview/github-markdown.css",f"preview/github-markdown-{theme}.css")
        def source(match):
            tag = match.group()
            selected = "dark" if "dark" in tag else "light"
            if selected != theme:
                return ""
            tag = re.sub(r'\s+and\s+\(prefers-color-scheme: [^)]+\)', '', tag)
            return re.sub(r' media="\(prefers-color-scheme: [^)]+\)"', '', tag)
        themed = re.sub(r'<source\b[^>]*>',source,themed)
        background = "#0d1117" if theme == "dark" else "#ffffff"
        themed = themed.replace('</head>',f'<style>body{{background:{background}}}.markdown-body{{background:{background}}}</style></head>')
        atomic_write(output / f"{theme}.html",themed)
    atomic_write(output / "mobile.html", '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Willam — mobile theme review</title><style>body{margin:20px;background:#cbd5e1;font:16px Arial}iframe{width:390px;height:1100px;border:0;border-radius:12px;margin-bottom:24px;display:block;max-width:100%}</style><h1>Mobile review · 390 px</h1><h2>Light</h2><iframe title="Mobile light theme" src="light.html"></iframe><h2>Dark</h2><iframe title="Mobile dark theme" src="dark.html"></iframe></html>')
    print(f"Preview: {output / 'index.html'}")
    print("Serve: python -m http.server 8765 --bind 127.0.0.1")


if __name__ == "__main__":
    main()
