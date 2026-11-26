# Operating the public profile

The README is a public portfolio, written in English. All project data comes from GitHub's REST API. Nothing in the generator adds topics, edits descriptions or modifies other repositories.

## Daily refresh

`.github/workflows/update-profile.yml` runs at **06:17 Peru time (11:17 UTC)** every day, and supports **Actions → Profile checks and daily refresh → Run workflow**. It validates the project before refreshing. Only the refresh job receives `contents: write`; all other permissions are absent. The built-in `GITHUB_TOKEN` is sufficient; no personal access token or additional secret is needed.

The daily schedule starts after this workflow is merged into the default branch. GitHub may delay scheduled runs and may disable schedules in public repositories after 60 days without activity. A protected branch that requires pull requests can reject the bot's direct push; in that case, adapt delivery to a pull request under the repository's own policy. This implementation never bypasses branch protection or force-pushes.

Only the content inside these pairs is replaced:

```html
<!-- PROJECTS:START -->
<!-- PROJECTS:END -->
<!-- STATS:START -->
<!-- STATS:END -->
```

Manual text, biography, branding, portrait and technology roadmap are preserved. `STACK` markers are used only by the manually invoked design build. The workflow stages only `README.md`, `assets/projects/snapshot.json` and `assets/stats/`. It commits and pushes only when those files differ. No refresh timestamp is injected, so identical metadata produces identical files. Excluded repositories are recorded only by identity and exclusion flags to avoid the profile bot creating its own update loop.

## Classify a project

1. Open a repository you own.
2. Click the gear beside **About**, then add appropriate **Topics**.
3. Add a factual repository description and, if available, a genuine demo URL under **Website**.
4. Wait for the daily run or dispatch the workflow manually.

| Specialty | Example recognized topics | Explicit primary topic |
| :--- | :--- | :--- |
| Data Analytics & Business Intelligence | `data-analytics`, `business-intelligence`, `power-bi`, `tableau` | `portfolio-analytics` |
| Data Science | `data-science`, `statistics`, `eda` | `portfolio-data-science` |
| Machine Learning & Deep Learning | `machine-learning`, `deep-learning`, `pytorch`, `nlp` | `portfolio-machine-learning` |
| AI Engineering & Generative AI | `ai-engineering`, `generative-ai`, `rag`, `ai-agents` | `portfolio-ai-engineering` |
| Data Engineering | `data-engineering`, `etl`, `dbt`, `apache-spark` | `portfolio-data-engineering` |
| Cloud Computing & MLOps | `mlops`, `llmops`, `gcp`, `aws`, `terraform` | `portfolio-cloud-mlops` |
| Software Engineering | `software-engineering`, `backend`, `rest-api`, `web-development` | `portfolio-software` |
| Other Projects | No matching topic | `portfolio-other` |

Add **one explicit primary topic** when a project spans several specialties. It takes precedence. Without one, the category with the most matching topics wins; ties follow the order in `config/categories.json`. Each project appears once. A repository name never determines its category. Empty categories are hidden. No recognized topics means **Other Projects**.

For example, `portfolio-ai-engineering`, `rag`, `langchain` and `python` select AI Engineering and identify LangChain/Python. They must describe the actual repository. Merely adding a topic does not verify a skill. Technologies are identified only from the primary language and recognized topics; no dependency or source-code audit is implied.

## Highlight and rank projects

Edit these fields in `config/categories.json`:

```json
{
  "featured": ["willamhs/REAL-REPOSITORY-NAME"],
  "priority": {"willamhs/ANOTHER-REAL-REPOSITORY": 10},
  "exclude": [],
  "visible_per_category": 4
}
```

The names above illustrate syntax, not existing projects. Use full real repository names. `featured` order wins first, then larger `priority`, then latest `updated_at`, with full name as a stable tie breaker. No project is featured by default because selection requires evaluating its actual content. Repositories beyond the visible count remain available under an expandable **Explore more projects** block. The API itself follows every `Link: rel="next"` pagination link at 100 repositories per page.

Private repositories, forks, archived repositories, this profile and configured exclusions never enter the project portfolio. Duplicate IDs and names are deduplicated. The total public repository count includes public forks, archived repositories and this profile. Project stars count eligible repositories only.

## Reliability and provenance

The updater reads all pages into memory, validates required metadata and renders both project and statistics content before writing. Network timeouts, malformed payloads, API errors, cyclic pagination and missing README markers fail the run. Existing content is preserved for all query, validation and rendering failures. Bounded retries handle transient network errors, server failures and short rate limits. Longer rate limits abort safely. API bodies and credentials are never logged. Pagination is restricted to `https://api.github.com`, and redirects are refused to avoid forwarding the token to another host.

Files are replaced atomically individually; the local filesystem update is not a multi-file transaction. A disk failure could leave some locally generated assets ahead of the README, but the failed workflow will not commit them. Git commits publish the completed set together. A repository changing while API pages are being read can appear on its next run; GitHub's listing endpoint does not provide a transactional account snapshot.

`assets/projects/snapshot.json` is the audit source for both charts and portfolio blocks. Its Git history records refreshes. Missing descriptions and languages are explicitly labeled. Primary-language charts count repositories, not source bytes or proficiency. Private contributions, employment, certifications and impact metrics are never inferred. The native contribution graph is linked rather than reconstructed from an incomplete REST events feed.

## Local commands

Use Python 3.11 or newer, preferably in a virtual environment:

```bash
python -m venv .venv
# Activate the environment using your shell's normal command.
python -m pip install -r requirements-dev.txt
python -m pytest -q
python scripts/validate_profile.py
python scripts/update_projects.py
python scripts/generate_stats.py
```

For higher local rate limits, set `GITHUB_TOKEN` in your environment through your usual secure credential workflow. Do not paste it into files, terminal commands or this repository. An unauthenticated refresh also works within GitHub's public API limits. The updater is independent of the working directory; `--root` supports an isolated fixture/workspace.

Optional checks and design commands:

```bash
python scripts/validate_profile.py --check-links
python scripts/build_assets.py
python scripts/generate_ascii.py /path/to/original/perfil.jpg --columns 160
python scripts/preview_profile.py
```

`build_assets.py` vendors versioned upstream SVGs and rewrites the roadmap; it requires a network connection. Daily refreshes never depend on third-party badge/image services. The original photograph remains outside the Git repository and is never needed by Actions.

The preview is a local approximation using GitHub's published Markdown stylesheet. For authoritative rendering, inspect README on the pull request branch in GitHub. External sites may block automated checks; the validator distinguishes these from confirmed reachability.

## References

- [GitHub REST: repositories](https://docs.github.com/en/rest/repos/repos#list-repositories-for-a-user)
- [GitHub REST: pagination](https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api)
- [GitHub REST: rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
- [GitHub Actions workflow syntax and permissions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [Scheduled workflow behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
