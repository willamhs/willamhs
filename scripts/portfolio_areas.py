"""Native GitHub HTML portfolio cards with small black-to-blue SVG headers.

The area titles, descriptions, counters, links and projects are real HTML.
Only the decorative gradient and original-color vendor icons are SVG assets.
"""
from __future__ import annotations

from html import escape
from pathlib import Path
import re

try:
    from .common import ROOT, atomic_write
except ImportError:
    from common import ROOT, atomic_write


def area_banner(category: dict, root: Path = ROOT) -> str:
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="480" height="76" viewBox="0 0 480 76" role="img" aria-label="{escape(category["name"], quote=True)} technology icons">',
        '<defs><linearGradient id="night-blue" x2="1" y2=".3"><stop stop-color="#01090E"/><stop offset=".48" stop-color="#061B3D"/><stop offset="1" stop-color="#0757CB"/></linearGradient></defs>',
        '<rect x=".5" y=".5" width="479" height="75" rx="12" fill="url(#night-blue)" stroke="#1F5797"/>',
        '<path d="M260 76c80-50 136-40 220-70M280 76c80-35 136-20 200-53" fill="none" stroke="#27C7FF" stroke-opacity=".18"/>',
        '<path d="m441 31 7 7-7 7m-13-14 7 7-7 7" fill="none" stroke="#60D7FF" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>']
    for index, icon in enumerate(category.get("technologies", [])):
        if not re.fullmatch(r'[a-z0-9-]+',icon):
            raise ValueError(f"Invalid technology icon identifier: {icon}")
        vector = (root / f"assets/icons/tech/{icon}.svg").read_text(encoding="utf-8")
        vector = re.sub(r'<svg\b[^>]*>',lambda m: re.sub(r'\s(?:width|height)="[^"]*"','',m.group())[:-1]+f' x="{18+index*49}" y="18" width="40" height="40">',vector,count=1)
        parts.append(vector)
    return '\n'.join(parts)+'</svg>\n'


def build_area_assets(config: dict, root: Path = ROOT):
    for category in config["categories"]:
        if not re.fullmatch(r'[a-z][a-z0-9-]+',category["id"]):
            raise ValueError("Invalid area identifier")
        atomic_write(root / f'assets/areas/{category["id"]}-header.svg',area_banner(category,root))


def area_card(category, repos, config, render_project):
    name=escape(category["name"])
    bits=[f'<img src="assets/areas/{category["id"]}-header.svg" width="100%" alt="{name}: original-color technology icons on a black-to-blue gradient" />',
        f'<h3>{name}</h3>',f'<p>{escape(category.get("description", ""))}</p>']
    if not repos:
        bits.append('<p><sub>No public projects published in this area yet.</sub></p>')
    else:
        bits.append(f'<p><strong>{len(repos)} public {"project" if len(repos)==1 else "projects"}</strong></p>')
        limit=config["visible_per_category"]
        bits.extend(render_project(repo,config) for repo in repos[:limit])
        if len(repos)>limit:
            bits.append(f'<details><summary>Explore {len(repos)-limit} more projects</summary>')
            bits.extend(render_project(repo,config) for repo in repos[limit:])
            bits.append('</details>')
    return '\n'.join(bits)


def render_areas(groups, config, render_project):
    main=[c for c in config["categories"] if c.get("show_when_empty",False)]
    more=[c for c in config["categories"] if not c.get("show_when_empty",False) and groups[c["id"]]]
    bits=['<table width="100%">']
    for index in range(0,len(main),2):
        bits.append('<tr>')
        pair=main[index:index+2]
        for category in pair:
            bits.append(f'<td width="50%" valign="top">\n{area_card(category,groups[category["id"]],config,render_project)}\n</td>')
        if len(pair)==1:
            bits.append('<td width="50%"></td>')
        bits.append('</tr>')
    bits.append('</table>')
    for category in more:
        bits.append(f'<table width="100%"><tr><td valign="top">\n{area_card(category,groups[category["id"]],config,render_project)}\n</td></tr></table>')
    if not any(groups.values()):
        bits.append('<p>No eligible public repositories are currently available.</p>')
    bits.append('<p><sub>New public repositories are discovered by the hourly refresh. Topics choose the area; unrecognized topics go to Other Projects. <a href="docs/automation.md#classify-a-project">How classification works</a>. Forks, archived repositories and this profile are excluded. Technologies shown in project metadata come from their primary language and recognized topics.</sub></p>')
    return '\n\n'.join(bits)
