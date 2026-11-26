"""Fetch a complete public snapshot, then update projects and statistics together.

Run from anywhere: python scripts/update_projects.py
An API failure (including a later pagination page) never reaches the write phase.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import time
from pathlib import Path
from urllib.parse import quote, urlparse
from html import escape

import requests

try:
    from .common import ROOT, atomic_write, read_config, replace_section, safe_url
    from .generate_stats import build_stats
    from .portfolio_areas import render_areas
except ImportError:
    from common import ROOT, atomic_write, read_config, replace_section, safe_url
    from generate_stats import build_stats
    from portfolio_areas import render_areas

API = "https://api.github.com"
LOG = logging.getLogger(__name__)


class GitHubError(RuntimeError):
    """A complete trustworthy snapshot could not be retrieved."""


class GitHubClient:
    def __init__(self, token: str | None = None, session=None, sleep=time.sleep):
        self.session = session or requests.Session()
        self.sleep = sleep
        self.session.headers.update({"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "willamhs-profile/1.0"})
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def get(self, url: str):
        # Never forward the token to a pagination URL outside GitHub's API.
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != "api.github.com":
            raise GitHubError("Refused an untrusted API URL")
        for attempt in range(3):
            try:
                response = self.session.get(url, timeout=(10, 35), allow_redirects=False)
            except requests.RequestException:
                if attempt == 2:
                    raise GitHubError("GitHub network request failed; existing profile preserved") from None
                self.sleep(2 ** attempt)
                continue
            if response.status_code == 200:
                try:
                    return response.json(), response.links.get("next", {}).get("url")
                except ValueError:
                    raise GitHubError("GitHub returned malformed JSON") from None
            if response.status_code in (403, 429):
                # A long rate-limit wait should fail safely, not consume runner minutes.
                retry = response.headers.get("Retry-After", "")
                if retry.isdigit():
                    delay = int(retry)
                elif response.headers.get("X-RateLimit-Remaining") == "0":
                    delay = max(1, int(response.headers.get("X-RateLimit-Reset", "0")) - int(time.time()) + 1)
                else:
                    delay = 2 ** (attempt + 1)
                if attempt < 2 and delay <= 30:
                    self.sleep(delay)
                    continue
                raise GitHubError(f"GitHub access/rate limit (HTTP {response.status_code}); existing profile preserved")
            if response.status_code >= 500 and attempt < 2:
                self.sleep(2 ** attempt)
                continue
            raise GitHubError(f"GitHub API HTTP {response.status_code}; existing profile preserved")
        raise GitHubError("GitHub request attempts exhausted")

    def repositories(self, username: str) -> list[dict]:
        url = f"{API}/users/{quote(username, safe='')}/repos?type=owner&sort=full_name&per_page=100&page=1"
        result, seen_pages, seen_ids = [], set(), set()
        while url:
            if url in seen_pages or len(seen_pages) >= 1000:
                raise GitHubError("Invalid/cyclic pagination; existing profile preserved")
            seen_pages.add(url)
            page, url = self.get(url)
            if not isinstance(page, list):
                raise GitHubError("Expected a repository list")
            for repo in page:
                validate_repository(repo, username)
                if repo["id"] not in seen_ids:
                    result.append(repo)
                    seen_ids.add(repo["id"])
        return result


def validate_repository(repo: dict, username: str) -> None:
    required = {"id", "name", "full_name", "owner", "private", "fork", "archived", "html_url", "description", "language", "topics", "stargazers_count", "updated_at", "homepage"}
    if not isinstance(repo, dict) or not required <= repo.keys():
        raise GitHubError("Incomplete repository metadata; existing profile preserved")
    if not isinstance(repo["owner"], dict) or repo["owner"].get("login", "").lower() != username.lower():
        raise GitHubError("Unexpected repository owner")
    if not isinstance(repo["topics"], list) or not all(isinstance(t, str) for t in repo["topics"]):
        raise GitHubError("Malformed topics")
    if not isinstance(repo["id"], int) or not isinstance(repo["stargazers_count"], int) or repo["stargazers_count"] < 0:
        raise GitHubError("Malformed repository counters")
    if not isinstance(repo["updated_at"], str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", repo["updated_at"]):
        raise GitHubError("Malformed repository timestamp")
    for flag in ("private", "fork", "archived"):
        if not isinstance(repo[flag], bool):
            raise GitHubError("Malformed repository visibility")
    expected = f"https://github.com/{repo['full_name']}"
    if repo["html_url"] != expected or repo["full_name"].lower() != f"{username}/{repo['name']}".lower():
        raise GitHubError("Unexpected repository URL")


def eligible_repositories(repos: list[dict], config: dict) -> list[dict]:
    excluded = {x.lower() for x in config.get("exclude", [])} | {config["profile_repository"].lower()}
    seen, selected = set(), []
    for repo in repos:
        key = repo["full_name"].lower()
        if repo["private"] or repo["fork"] or repo["archived"] or key in excluded or key in seen:
            continue
        selected.append(repo)
        seen.add(key)
    return selected


def classify(repo: dict, config: dict) -> str:
    topics = set(t.lower() for t in repo["topics"])
    # Explicit primary topic wins over all broad technology topics.
    for category in config["categories"]:
        if f"portfolio-{category['id']}" in topics:
            return category["id"]
    for alias, category in config.get("primary_topic_aliases", {}).items():
        if f"portfolio-{alias}" in topics:
            return category
    matches = [(len(topics & set(c["topics"])), -i, c["id"]) for i, c in enumerate(config["categories"]) if c["id"] != "other"]
    best = max(matches, default=(0, 0, "other"))
    return best[2] if best[0] else "other"


def grouped_repositories(repos: list[dict], config: dict) -> dict[str, list[dict]]:
    groups = {c["id"]: [] for c in config["categories"]}
    featured = [r.lower() for r in config.get("featured", [])]
    priorities = {k.lower(): v for k, v in config.get("priority", {}).items()}
    def rank(repo):
        key = repo["full_name"].lower()
        return (featured.index(key) if key in featured else len(featured), -priorities.get(key, 0))
    # Stable sorts give relevance > most recently updated > full name.
    ordered = sorted(repos, key=lambda r: r["full_name"].lower())
    ordered.sort(key=lambda r: r["updated_at"], reverse=True)
    ordered.sort(key=rank)
    for repo in ordered:
        groups[classify(repo, config)].append(repo)
    return groups


def project_block(repo: dict, config: dict) -> str:
    name = '<wbr />'.join(escape(repo["name"][i:i+12]) for i in range(0,len(repo["name"]),12))
    url = escape(repo["html_url"], quote=True)
    featured = repo["full_name"].lower() in {x.lower() for x in config.get("featured", [])}
    label = " &nbsp; <sub>FEATURED</sub>" if featured else ""
    language = repo["language"]
    icon = config["language_icons"].get(language)
    lang = f'<img src="assets/icons/tech/{icon}.svg" width="18" height="18" alt="" /> ' if icon else ""
    lang += escape(language or "Language not reported")
    desc = escape(repo["description"]) if repo["description"] else "<em>No repository description provided.</em>"
    tech = sorted({config["topic_technologies"][t] for t in repo["topics"] if t in config["topic_technologies"]} | ({language} if language else set()))
    technologies = escape(" · ".join(tech)) if tech else "Not identified in public metadata"
    topics = " ".join('<code>'+'<wbr />'.join(escape(t[i:i+12]) for i in range(0,len(t),12))+'</code>' for t in sorted(repo["topics"])) or "Not set"
    demo = safe_url(repo.get("homepage"))
    demo_link = f' &nbsp; · &nbsp; <a href="{escape(demo, quote=True)}">Live demo ↗</a>' if demo else ""
    return (f'<h4><a href="{url}">{name}</a>{label}</h4>\n'
            f'<p>{desc}</p>\n'
            f'<p>{lang} &nbsp; · &nbsp; {repo["stargazers_count"]} stars &nbsp; · &nbsp; Updated {repo["updated_at"][:10]}{demo_link}<br />\n'
            f'<sub><strong>Technologies:</strong> {technologies}<br /><strong>Topics:</strong> {topics}</sub></p>\n')


def render_projects(groups: dict, config: dict) -> str:
    return render_areas(groups,config,project_block)


def refresh(root: Path = ROOT, client=None) -> dict:
    config = read_config(root)
    original = (root / "README.md").read_text(encoding="utf-8")
    # Check both marker pairs BEFORE making requests or writing anything.
    replace_section(original, "PROJECTS", "")
    replace_section(original, "STATS", "")
    repos = (client or GitHubClient(os.getenv("GITHUB_TOKEN"))).repositories(config["username"])
    public = [r for r in repos if not r["private"]]
    eligible = eligible_repositories(public, config)
    groups = grouped_repositories(eligible, config)
    snapshot = {
        "schema_version": 2, "username": config["username"],
        "source": f"{API}/users/{config['username']}/repos",
        "public_repositories": len(public),
        # Excluded repositories only contribute to the public count. In particular,
        # recording this profile's updated_at would make bot commits trigger forever.
        "repositories": [{k: r.get(k) for k in (("id", "name", "full_name", "html_url", "description", "language", "topics", "stargazers_count", "updated_at", "homepage", "fork", "archived") if r in eligible else ("id", "full_name", "fork", "archived"))} for r in sorted(public, key=lambda x: x["full_name"].lower())],
        "portfolio_repositories": [r["full_name"] for r in eligible],
        "categories": {key: [r["full_name"] for r in values] for key, values in groups.items() if values},
    }
    # Build everything in memory first. Failures in fetch/validation/render preserve all previous assets.
    assets, stats_body = build_stats(snapshot, config)
    readme = replace_section(original, "PROJECTS", render_projects(groups, config))
    readme = replace_section(readme, "STATS", stats_body)
    assets["assets/projects/snapshot.json"] = json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"
    for path, content in assets.items():
        atomic_write(root / path, content)
    atomic_write(root / "README.md", readme)
    LOG.info("Updated profile: %d public / %d eligible repositories", len(public), len(eligible))
    return snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        refresh(args.root)
    except (GitHubError, ValueError, KeyError, TypeError, OSError) as exc:
        LOG.error("Profile update aborted: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
