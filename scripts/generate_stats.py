"""Generate honest, static, theme-aware charts from the portfolio snapshot."""
from __future__ import annotations

import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path

try:
    from .common import ROOT, atomic_write, read_config, replace_section
except ImportError:
    from common import ROOT, atomic_write, read_config, replace_section


def chart_svg(snapshot: dict, config: dict, theme: str, mobile: bool = False) -> str:
    dark = theme == "dark"
    bg, panel, ink, muted, line = ("#0A1425", "#0F172A", "#F8FAFC", "#94A3B8", "#213452") if dark else ("#F8FAFC", "#FFFFFF", "#0F172A", "#475569", "#DCE5F2")
    eligible_names = set(snapshot["portfolio_repositories"])
    repos = [r for r in snapshot["repositories"] if r["full_name"] in eligible_names]
    languages = Counter(r["language"] or "Not reported" for r in repos)
    # Top five + remainder so the visible chart always accounts for all projects.
    entries = languages.most_common()
    if len(entries) > 6:
        entries = entries[:5] + [("Other languages", sum(n for _, n in entries[5:]))]
    cats = [(c["name"], len(snapshot["categories"].get(c["id"], []))) for c in config["categories"] if snapshot["categories"].get(c["id"])]
    height = 250 + 48 * (len(entries) + len(cats))
    stars = sum(r["stargazers_count"] for r in repos)
    total = len(repos)
    if mobile:
        return mobile_chart(snapshot, entries, cats, total, stars, bg, panel, ink, muted, line)
    chunks = [f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="{height}" viewBox="0 0 800 {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Public GitHub portfolio activity</title>',
        f'<desc id="desc">{snapshot["public_repositories"]} public repositories; {total} eligible original active projects; {stars} stars across eligible projects. Language counts measure repositories, not lines of code. Category counts use topics.</desc>',
        f'<rect width="800" height="{height}" rx="20" fill="{bg}"/>',
        '<defs><linearGradient id="bar"><stop stop-color="#2563EB"/><stop offset="1" stop-color="#60A5FA"/></linearGradient></defs>',
        f'<g font-family="Arial,Helvetica,sans-serif" fill="{ink}">']
    for x, value, label in [(28, snapshot["public_repositories"], "PUBLIC REPOSITORIES"), (284, total, "PORTFOLIO PROJECTS"), (540, stars, "PROJECT STARS")]:
        chunks.extend([f'<rect x="{x}" y="24" width="232" height="112" rx="12" fill="{panel}" stroke="{line}"/>',
            f'<text x="{x+18}" y="78" font-size="40" font-weight="700">{value}</text>',
            f'<text x="{x+18}" y="111" font-size="14" fill="{muted}" letter-spacing="1">{label}</text>'])
    y = 178
    for heading, items in [("PRIMARY LANGUAGES", entries), ("PROJECT SPECIALTIES", cats)]:
        chunks.append(f'<text x="28" y="{y}" font-size="16" fill="{muted}" letter-spacing="2">{heading}</text>')
        y += 29
        for label, count in items:
            # Full category names can be long; readable compact chart labels.
            short = label.replace("Data Analytics & Business Intelligence", "Analytics & BI").replace("Machine Learning & Deep Learning", "ML & Deep Learning").replace("AI Engineering & Generative AI", "AI & Generative AI").replace("Cloud Computing & MLOps", "Cloud & MLOps")
            width = 410 * count / max(total, 1)
            chunks.extend([f'<text x="28" y="{y+3}" font-size="18">{escape(short)}</text>',
                f'<rect x="300" y="{y-14}" width="410" height="20" rx="6" fill="{line}"/>',
                f'<rect x="300" y="{y-14}" width="{width:.2f}" height="20" rx="6" fill="url(#bar)"/>',
                f'<text x="767" y="{y+3}" text-anchor="end" font-size="18">{count}</text>'])
            y += 48
        y += 18
    chunks.append(f'<text x="28" y="{height-18}" font-size="13" fill="{muted}">Source: GitHub REST API · Repository counts · No private activity inferred</text></g></svg>\n')
    return "\n".join(chunks)


def mobile_chart(snapshot, languages, categories, total, stars, bg, panel, ink, muted, line):
    height = 250 + 62*(len(languages)+len(categories))
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="{height}" viewBox="0 0 400 {height}" role="img" aria-labelledby="title">',
        '<title id="title">Public GitHub activity, mobile layout</title>',
        f'<rect width="400" height="{height}" rx="16" fill="{bg}"/>',
        f'<g font-family="Arial,Helvetica,sans-serif" fill="{ink}">']
    for x, number, label in [(16,snapshot["public_repositories"],"PUBLIC REPOS"),(142,total,"PROJECTS"),(268,stars,"PROJECT STARS")]:
        parts.extend([f'<rect x="{x}" y="18" width="116" height="98" rx="10" fill="{panel}" stroke="{line}"/>',
            f'<text x="{x+12}" y="65" font-size="32" font-weight="700">{number}</text>',
            f'<text x="{x+12}" y="95" font-size="10" fill="{muted}">{label}</text>'])
    y = 156
    for heading, values in [("PRIMARY LANGUAGES",languages),("PROJECT SPECIALTIES",categories)]:
        parts.append(f'<text x="18" y="{y}" font-size="13" fill="{muted}" letter-spacing="1.5">{heading}</text>')
        y += 32
        for name, number in values:
            short = name.replace("Data Analytics & Business Intelligence","Analytics & BI").replace("Machine Learning & Deep Learning","ML & Deep Learning").replace("AI Engineering & Generative AI","AI & Generative AI").replace("Cloud Computing & MLOps","Cloud & MLOps")
            parts.extend([f'<text x="18" y="{y}" font-size="16">{escape(short)}</text>',
                f'<text x="382" y="{y}" text-anchor="end" font-size="16">{number}</text>',
                f'<rect x="18" y="{y+12}" width="364" height="12" rx="4" fill="{line}"/>',
                f'<rect x="18" y="{y+12}" width="{364*number/max(total,1):.2f}" height="12" rx="4" fill="#3B82F6"/>'])
            y += 62
        y += 16
    parts.append(f'<text x="18" y="{height-20}" font-size="11" fill="{muted}">GitHub REST API · Repository counts</text></g></svg>\n')
    return "\n".join(parts)


def build_stats(snapshot: dict, config: dict) -> tuple[dict, str]:
    assets = {f"assets/stats/activity-{theme}{'-mobile' if mobile else ''}.svg": chart_svg(snapshot, config, theme, mobile) for theme in ("light", "dark") for mobile in (False, True)}
    eligible = set(snapshot["portfolio_repositories"])
    repos = [r for r in snapshot["repositories"] if r["full_name"] in eligible]
    languages = Counter(r["language"] or "Not reported" for r in repos)
    stars = sum(r["stargazers_count"] for r in repos)
    body = ('<picture>\n  <source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="assets/stats/activity-dark-mobile.svg" />\n'
            '  <source media="(max-width: 600px)" srcset="assets/stats/activity-light-mobile.svg" />\n'
            '  <source media="(prefers-color-scheme: dark)" srcset="assets/stats/activity-dark.svg" />\n'
            '  <source media="(prefers-color-scheme: light)" srcset="assets/stats/activity-light.svg" />\n'
            f'  <img src="assets/stats/activity-light.svg" width="100%" alt="{snapshot["public_repositories"]} public repositories, {len(repos)} portfolio projects, {stars} project stars. Details below." />\n</picture>\n\n'
            '<details>\n<summary>Read the numbers and methodology</summary>\n\n'
            f'**{snapshot["public_repositories"]} public repositories** owned by this account, including forks, archived repositories and this profile. '
            f'**{len(repos)} portfolio projects** and **{stars} project stars** after excluding forks, archived repositories, this profile and configured exclusions.\n\n'
            '| Primary language | Projects |\n| :--- | ---: |\n')
    body += "".join(f"| {escape(label)} | {n} |\n" for label, n in languages.most_common())
    body += '\n| Specialty | Projects |\n| :--- | ---: |\n'
    body += "".join(f"| {c['name']} | {len(snapshot['categories'][c['id']])} |\n" for c in config["categories"] if c["id"] in snapshot["categories"])
    body += ('\nLanguages count the primary language of each eligible repository, rather than code volume or proficiency. '
             'Each project belongs to one specialty. An empty language is shown as “Not reported”. '
             'All charts share the [same API snapshot](assets/projects/snapshot.json). '
             'The snapshot changes only when public metadata changes; its Git history records refreshes. '
             'Contribution totals are intentionally omitted: this REST snapshot cannot reliably measure them. '
             '[View GitHub’s native contribution graph](https://github.com/willamhs#year-list-container).\n\n</details>')
    return assets, body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    snapshot = json.loads((args.root / "assets/projects/snapshot.json").read_text(encoding="utf-8"))
    assets, body = build_stats(snapshot, read_config(args.root))
    readme_path = args.root / "README.md"
    readme = replace_section(readme_path.read_text(encoding="utf-8"), "STATS", body)
    for path, content in assets.items():
        atomic_write(args.root / path, content)
    atomic_write(readme_path, readme)


if __name__ == "__main__":
    main()
