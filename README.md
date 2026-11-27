# GitHub Activity Manager

An interactive, local-first Python CLI for retrieving your GitHub contribution history, detecting empty days and weeks, simulating activity plans with strict protection for existing contributions, and performing safe, explicit, current-time Git operations.

> **Attribution & Inspiration:** Inspired by [Shpota/github-activity-generator](https://github.com/Shpota/github-activity-generator) (Apache-2.0). This project expands the original single-file concept into a modular, privacy-focused analysis, simulation, and safe repository workflow tool.

---

## Features

- **Interactive Rich CLI**: Guided menus, tables, progress spinners, and graceful `Ctrl+C` handling (`python main.py`).
- **Two Authentication Methods**:
  - **GitHub OAuth Device Flow** (opens browser, no embedded client secret).
  - **Personal Access Token (PAT)** (masked input, stored in OS keyring or `0600` encrypted local store).
- **Multi-Year Contribution Retrieval**: Uses GitHub GraphQL `contributionCalendar` year-by-year, handling leap years, month lengths, and SQLite caching.
- **Mandatory Existing Activity Protection**: Any date with `existing_contributions > 0` (whether 1 or 50) is marked `ACTIVE` and **protected**—never overwritten or assigned planned activity.
- **Gap Analyzer**: Detects empty days, consecutive inactive streaks, **completely empty weeks** (7/7 empty), and **partially active weeks** (preserving eligible days).
- **Smart Distribution Engine**: 9 activity patterns (`consistent`, `random`, `weekday_focused`, `weekend_focused`, `increasing`, `decreasing`, `sprint`, `break_based`, `custom`), deterministic seeds, weekday/weekend exclusions, and impossible-target detection.
- **Simulated Contribution Graph**: Dark-terminal GitHub-style 5-level green calendar preview, completely independent of real Git operations.
- **Safe Repository Management**: Create new GitHub repos or select existing ones, preserve unrelated files, update only the managed section of `activity.txt`, preview diffs, dry-run mode, and confirmation-gated current-time commits/pushes.
- **Exports**: CSV, JSON, plain-text reports, SVG, and PNG contribution graphs.

---

## Requirements

- Python **3.11+**
- `git` installed and available on `PATH`
- Dependencies in `requirements.txt` (`rich`, `requests`, `keyring`, `questionary`, `Pillow`)

---

## Installation & One-Command Execution

```bash
git clone https://github.com/<your-username>/GitHub-Activity-Generator.git
cd GitHub-Activity-Generator
pip install -r requirements.txt
python main.py
```

---

## Authentication Setup

### 1. GitHub OAuth (Device Flow)
1. Create a GitHub OAuth App (with Device Flow enabled) in **GitHub Settings → Developer settings → OAuth Apps**.
2. Launch `python main.py` and choose **1. Login with GitHub OAuth**.
3. Enter your OAuth App **Client ID** (no client secret is ever needed or stored), open the verification URL in your browser, and enter the displayed code.

### 2. Personal Access Token (PAT)
1. Generate a token in **GitHub Settings → Developer settings → Personal access tokens**.
2. Minimum recommended scopes:
   - `read:user` — read profile and contribution calendar.
   - `repo` — only needed if creating or pushing to repositories.
3. Choose **2. Login with Personal Access Token** and paste your token (input is hidden).

---

## Activity Retrieval & Gap Detection

- **Contribution Retrieval (Menu 4)**: Queries GitHub's GraphQL `contributionCalendar` year-by-year for any custom range, full year, or multi-year span.
- **Empty Days & Weeks (Menu 5 & 6)**:
  - `ACTIVE` (`count > 0`): Protected. Never assigned planned commits.
  - `EMPTY` (`count == 0`): Eligible for planning unless excluded.
  - **Partially Active Weeks** are never discarded—their empty days remain eligible.
- **Known GitHub API Limitation**: A `0` count means GitHub's API returned no qualifying public/private contribution for that date; it does not prove no work occurred.

---

## Activity Configuration, Simulation & Exports

- **Configure (Menu 7)** & **Generate Plan (Menu 8)**: Set min/max commits, exact daily/weekly/monthly/total targets, weekend exclusions, patterns, and deterministic random seeds.
- **Preview Graph (Menu 9)**: View the simulated GitHub-style calendar and inspect individual dates. Simulated counts are always labeled separately from real GitHub contributions.
- **Manage Repositories (Menu 10)**: Create a new repo or select an existing one, update `activity.txt` for genuine current-time work, inspect the unified diff, test with dry-run, and push only after explicit confirmation.
- **Export Reports (Menu 11)**: Export CSVs, JSON, text summaries, SVG, and PNG graphs to `~/.github-activity-generator/exports/`.

---

## Privacy & Security

- All data is stored locally in `~/.github-activity-generator/` (`config.json`, `activity.db`, `logs/`, `exports/`, `cache/`).
- Tokens are stored in your OS keyring (with a `0600` encrypted local fallback if no keyring daemon is available), never in `config.json` or logs.
- No telemetry, no analytics, no centralized backend, and SSL verification is always enabled.
- Never generates fake backdated commits, never force-pushes, and never modifies unrelated repository files.

See [docs/SECURITY.md](docs/SECURITY.md), [docs/FEATURES.md](docs/FEATURES.md), [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md), [docs/INSTALLATION.md](docs/INSTALLATION.md), and [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).

---

## Troubleshooting

- **Missing dependencies**: Run `pip install -r requirements.txt`.
- **Git not found**: Install Git and ensure `git --version` works in your terminal.
- **401 / Expired Token**: Run **13. Logout** and re-authenticate with OAuth or a fresh PAT.
- **Rate Limit (403)**: Wait until the GitHub API rate-limit reset window, or use cached data in `activity.db`.

---

## Running Tests

```bash
python3 -m unittest discover -s tests -v
# or with pytest:
pytest
```

---

## License & Attribution

Licensed under the **Apache License, Version 2.0**. See [LICENSE](LICENSE).  
Inspired by [Shpota/github-activity-generator](https://github.com/Shpota/github-activity-generator).
