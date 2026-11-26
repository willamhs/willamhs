# Operating the public profile

The area cards are native GitHub HTML: selectable titles, descriptions, counters and real project links. The black-to-blue headers and colored vendor logos are small local SVG assets. All eight core disciplines have equal visual treatment. Projects live directly inside their matching area.

## Automatic discovery

`.github/workflows/update-profile.yml` queries **all public repositories owned by willamhs every hour, at minute 17**. It follows every GitHub API pagination link, classifies repositories by topics, and regenerates the area cards and statistics from one snapshot. A newly published repository appears in the next successful refresh. Editing topics moves it to the matching area; deleting, archiving or making it private removes it on the next refresh.

This is periodic discovery, not a real-time listener on every repository. No workflow needs to be installed in future project repositories. The profile repository cannot receive another repository's `push` event directly. GitHub can delay scheduled runs; minute 17 avoids the busiest top-of-hour queue. Manual execution is available under **Actions → Profile checks and hourly refresh → Run workflow**.

The built-in `GITHUB_TOKEN` is enough. Only the refresh job receives `contents: write`; validation has read-only access. No new persistent credentials, personal access token or external service is required for scheduled discovery. The workflow also supports `repository_dispatch` with type `profile-refresh` for an existing authorized integration. That optional caller must already have permission to dispatch events to this profile repository; a different repository's default `GITHUB_TOKEN` does not grant access here.

The schedule requires GitHub Actions to be available for the account and repository. If a job never starts, inspect its annotation for an account restriction, disabled workflow, runner availability or billing issue. Code cannot clear an account restriction. Public scheduled workflows can be disabled after 60 days without repository activity. Branch protection can reject a direct bot push; this implementation does not bypass protection or force-push.

## Classify a project

1. Publish an original public repository under your account.
2. Open its **About** settings and add truthful **Topics** from the table below.
3. Add a factual description and, when available, a real demo URL under **Website**.
4. Wait for the next successful hourly refresh or run the workflow manually.

| Area | Recognized topic examples | Explicit primary topic |
| :--- | :--- | :--- |
| Data Analytics | `data-analytics`, `data-analysis`, `eda` | `portfolio-analytics` |
| Business Intelligence | `business-intelligence`, `power-bi`, `tableau`, `dashboard` | `portfolio-business-intelligence` |
| Data Science | `data-science`, `statistics`, `predictive-analytics` | `portfolio-data-science` |
| Machine Learning & Deep Learning | `machine-learning`, `deep-learning`, `pytorch`, `nlp` | `portfolio-machine-learning` |
| AI Engineering & Generative AI | `ai-engineering`, `generative-ai`, `rag`, `ai-agents` | `portfolio-ai-engineering` |
| Data Engineering | `data-engineering`, `etl`, `dbt`, `apache-spark` | `portfolio-data-engineering` |
| Cloud Computing | `cloud-computing`, `gcp`, `aws`, `azure` | `portfolio-cloud` |
| MLOps & LLMOps | `mlops`, `llmops`, `mlflow`, `terraform` | `portfolio-mlops` |
| Software Engineering | `software-engineering`, `backend`, `rest-api`, `web-development` | `portfolio-software` |
| Other Projects | No recognized topic | `portfolio-other` |

For a RAG application, for example, add `portfolio-ai-engineering`, `rag`, `langchain` and `python` if they describe the actual implementation. That puts the repository in AI Engineering and identifies LangChain and Python from metadata. Do not add a topic merely to claim a skill.

**One explicit primary topic** takes precedence over broad technology topics. Without one, the category with the largest number of matching topics wins; ties follow the configured order. The order resolves classification ties only and does not rank the importance of disciplines. Each project appears once. Repository names and descriptions are never used to guess an area. Unknown topics go to **Other Projects**.

The eight core areas stay visible with an honest empty state until matching projects exist. Software Engineering and Other Projects appear when they contain eligible repositories. All category definitions live in `config/categories.json`. The old `portfolio-cloud-mlops` topic remains an alias for `portfolio-cloud`; use the new explicit Cloud or MLOps topic for precise classification.

## Feature and rank projects

Use full real names in `config/categories.json`:

```json
{
  "featured": ["willamhs/REAL-REPOSITORY-NAME"],
  "priority": {"willamhs/ANOTHER-REAL-REPOSITORY": 10},
  "exclude": [],
  "visible_per_category": 4
}
```

Those names illustrate syntax, not existing projects. Featured order wins first, then larger numeric priority, then latest `updated_at`, then full name as a stable tie breaker. Additional projects remain available under **Explore more projects** within the same area. Every API page is read at up to 100 repositories per page.

Private repositories, forks, archived repositories, this profile and configured exclusions are excluded. Duplicate IDs and names are deduplicated. The public repository total includes public forks, archived repositories and this profile; project counts and stars refer only to eligible repositories.

## Preserved content and reliability

Only these marked sections change during an API refresh:

```html
<!-- PROJECTS:START -->
<!-- PROJECTS:END -->
<!-- STATS:START -->
<!-- STATS:END -->
```

Biography, branding, ASCII portrait and manually maintained text stay intact. `STACK` markers are used only by the manual design build. The workflow stages only `README.md`, `assets/projects/snapshot.json` and `assets/stats/`, committing and pushing when these differ. Identical public metadata creates no commit. Excluded repositories are recorded only by identity and exclusion flags, so bot updates cannot create a self-sustaining commit loop.

The updater retrieves every page and validates metadata before rendering and writing. Network errors, long rate limits, malformed payloads, cyclic pagination and missing markers abort without overwriting existing content. Short transient failures receive bounded retries. Credentials and API response bodies are never logged; pagination stays on `https://api.github.com`, and redirects are refused.

Files are replaced atomically individually, rather than through a multi-file filesystem transaction. A disk error can leave some local assets newer than the README, but a failed workflow does not commit them. A completed Git commit publishes the set together. A repository changing during pagination may be picked up in the following refresh because the API does not provide a transactional account snapshot.

`assets/projects/snapshot.json` is the audit source for both cards and charts. Its Git history records meaningful changes. Missing descriptions and languages are labeled honestly. Technology names come only from primary languages and recognized topics. Language charts count repositories, not code volume or proficiency. Contribution totals are omitted; the native GitHub contribution graph is linked.

## Local commands

Use Python 3.11 or newer:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python scripts/validate_profile.py
python scripts/update_projects.py
python scripts/generate_stats.py
python scripts/preview_profile.py
```

The public API works without a token within its unauthenticated rate limits. For higher local limits, supply `GITHUB_TOKEN` through your normal secure environment workflow. Never paste it into repository files or terminal commands. `--root` supports an isolated fixture or checkout.

Design and optional link checks:

```bash
python scripts/build_assets.py
python scripts/validate_profile.py --check-links
python scripts/generate_ascii.py /path/to/original/perfil.jpg --columns 160 --ink silver
```

`build_assets.py` verifies and vendors upstream icons, generates the per-area gradient headers and rebuilds the technology roadmap. It requires network access; the hourly refresh does not depend on icon or badge services. When adding a new configured area, rebuild its header before publishing. The original photograph stays outside the repository and is not needed by Actions.

HTML tables use GitHub's own styling. Custom CSS and scripts are not supported in a profile README, so gradients live in SVG headers. Normal text wraps in each cell; unusually long unbroken names or topics may require GitHub's native horizontal table scrolling on narrow screens. The two-column table does not become a single-column CSS grid on phones. The local preview uses GitHub's published Markdown stylesheet; GitHub's rendered README is authoritative.

## References

- [GitHub markup pipeline and sanitization](https://github.com/github/markup#github-markup)
- [GitHub REST repositories](https://docs.github.com/en/rest/repos/repos#list-repositories-for-a-user)
- [REST pagination](https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api)
- [API rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
- [Workflow permissions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [Scheduled workflow behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
