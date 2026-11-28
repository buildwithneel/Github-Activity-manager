# GitHub Activity Manager

An interactive, local-first Python CLI for retrieving your GitHub contribution history, detecting empty days and weeks, simulating activity plans with strict protection for existing contributions, and performing safe, explicit, current-time Git operations.

---

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
  - [macOS](#-macos)
  - [Linux (Ubuntu / Debian / Fedora / Arch)](#-linux)
  - [Windows](#-windows)
- [Step-by-Step Usage Guide](#step-by-step-usage-guide)
- [Authentication Setup](#authentication-setup)
- [Activity Retrieval & Gap Detection](#activity-retrieval--gap-detection)
- [Activity Configuration, Simulation & Exports](#activity-configuration-simulation--exports)
- [Privacy & Security](#privacy--security)
- [Troubleshooting by OS](#troubleshooting-by-os)
- [Running Tests](#running-tests)
- [License & Attribution](#license--attribution)

---

## Features

- **Interactive Rich CLI**: Guided menus, tables, progress spinners, and graceful `Ctrl+C` handling (`python main.py`).
- **Two Authentication Methods**:
  - **GitHub OAuth Device Flow** (opens browser, no embedded client secret).
  - **Personal Access Token (PAT)** (masked input, stored in OS keyring or `0600` encrypted local store).
- **Multi-Year Contribution Retrieval**: Uses GitHub GraphQL `contributionCalendar` year-by-year, handling leap years, month lengths, and SQLite caching.
- **Mandatory Existing Activity Protection**: Any date with `existing_contributions > 0` (whether 1 or 50) is marked `ACTIVE` and **protected**, never overwritten or assigned planned activity.
- **Gap Analyzer**: Detects empty days, consecutive inactive streaks, **completely empty weeks** (7/7 empty), and **partially active weeks** (preserving eligible days).
- **Smart Distribution Engine**: 9 activity patterns (`consistent`, `random`, `weekday_focused`, `weekend_focused`, `increasing`, `decreasing`, `sprint`, `break_based`, `custom`), deterministic seeds, weekday/weekend exclusions, and impossible-target detection.
- **Simulated Contribution Graph**: Dark-terminal GitHub-style 5-level green calendar preview, completely independent of real Git operations.
- **Safe Repository Management**: Create new GitHub repos or select existing ones, preserve unrelated files, update only the managed section of `activity.txt`, preview diffs, dry-run mode, and confirmation-gated current-time commits/pushes.
- **Exports**: CSV, JSON, plain-text reports, SVG, and PNG contribution graphs.

---

## Prerequisites

Before installing, make sure your system has:

- **Python 3.11+** installed (`python3 --version` or `python --version`)
- **Git** installed and available on your PATH (`git --version`)
- A **GitHub Account** (with either a Personal Access Token or an OAuth App)

---

## Installation & Setup

Choose the instructions for your operating system below:

### 🍎 macOS

#### 1. Install Prerequisites
If you don't already have Python 3.11+ and Git installed, use [Homebrew](https://brew.sh/):
```bash
brew install python git
```
*(Alternatively, install Xcode Command Line Tools by running `xcode-select --install` and download Python from [python.org](https://www.python.org/downloads/mac-osx/)).*

#### 2. Clone the Repository
```bash
git clone https://github.com/Neel-s-Workspace/Github-Activity-manager.git
cd Github-Activity-manager
```

#### 3. Create & Activate Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### 4. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 5. Launch the Application
```bash
python3 main.py
```

> **macOS Note**: Credentials are automatically saved in the macOS Keychain using the system's native Security framework.

---

### 🐧 Linux

Works across Ubuntu, Debian, Fedora, Arch Linux, and WSL (Windows Subsystem for Linux).

#### 1. Install Prerequisites & System Dependencies

- **Debian / Ubuntu / Mint / Pop!_OS**:
  ```bash
  sudo apt update
  sudo apt install -y python3 python3-pip python3-venv git libsecret-1-0
  ```
- **Fedora / RHEL**:
  ```bash
  sudo dnf install -y python3 python3-pip git libsecret
  ```
- **Arch Linux / Manjaro**:
  ```bash
  sudo pacman -Syu python python-pip git libsecret
  ```

#### 2. Clone the Repository
```bash
git clone https://github.com/Neel-s-Workspace/Github-Activity-manager.git
cd Github-Activity-manager
```

#### 3. Create & Activate Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### 4. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 5. Launch the Application
```bash
python3 main.py
```

> **Linux / Headless / SSH Note**: If running in a headless environment without a desktop keyring daemon (GNOME Keyring / KWallet), the application automatically falls back to an encrypted `0600` local file store (`~/.github-activity-manager/`). No manual keyring setup is required!

---

### 🪟 Windows

Works on Windows 10 and Windows 11 with PowerShell, Command Prompt, or Git Bash.

#### 1. Install Prerequisites
If Python and Git are not installed:
- **Using Windows Package Manager (winget)**:
  ```powershell
  winget install Python.Python.3.12 Git.Git
  ```
- **Or manual download**:
  - Download Python 3.11+ from [python.org](https://www.python.org/downloads/windows/). **Check the box "Add python.exe to PATH"** during installation.
  - Download Git from [git-scm.com](https://git-scm.com/download/win).

#### 2. Clone the Repository
Open **PowerShell** or **Command Prompt**:
```powershell
git clone https://github.com/Neel-s-Workspace/Github-Activity-manager.git
cd Github-Activity-manager
```

#### 3. Create Virtual Environment
```powershell
python -m venv .venv
```
*(Or use `py -m venv .venv` if using the Python Launcher).*

#### 4. Activate Virtual Environment

- **In PowerShell**:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
  *(If you get a script execution policy error, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` and retry).*

- **In Command Prompt (`cmd.exe`)**:
  ```cmd
  .\.venv\Scripts\activate.bat
  ```

- **In Git Bash**:
  ```bash
  source .venv/Scripts/activate
  ```

#### 5. Install Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### 6. Launch the Application
```powershell
python main.py
```

> **Windows Note**: Tokens are safely stored using Windows Credential Manager via the `keyring` library. For optimal terminal colors and Unicode display, use [Windows Terminal](https://aka.ms/terminal).

---

## Step-by-Step Usage Guide

Once launched (`python main.py`), follow this workflow:

1. **Authenticate (Menu Options 1 or 2)**
   - Log in using **GitHub OAuth (Device Flow)** or a **Personal Access Token (PAT)**.
   - Verify connection with **3. Check Authentication & User Profile**.

2. **Retrieve Contribution Calendar (Menu Option 4)**
   - Enter a date range or calendar year (e.g., `2024` or `2024-01-01` to `2024-12-31`).
   - The CLI queries GitHub's GraphQL API and caches your real contribution calendar locally.

3. **Analyze Empty Days & Weeks (Menu Options 5 & 6)**
   - View inactive streaks, total blank days, and completely or partially empty weeks.
   - Any day with existing contributions (`count > 0`) is strictly marked **ACTIVE** and protected.

4. **Configure Activity Strategy (Menu Option 7)**
   - Set targets: min/max daily commits, target totals, exclude weekends/weekdays, and choose one of 9 distribution patterns (`consistent`, `random`, `increasing`, etc.).

5. **Generate Activity Plan (Menu Option 8)**
   - The distribution engine generates a conflict-free plan that only populates eligible empty days.

6. **Preview Simulated Graph (Menu Option 9)**
   - Inspect the interactive terminal GitHub calendar preview with 5-level green contribution cells.

7. **Manage Repositories & Sync (Menu Option 10)**
   - Select an existing repository or create a new dedicated activity repo.
   - Run a dry-run or inspect the unified diff of `activity.txt`.
   - Perform safe, current-time Git commit and push operations with explicit confirmation gates.

8. **Export Reports & Graphs (Menu Option 11)**
   - Export your analysis and planned graphs to CSV, JSON, text summary, SVG, or high-res PNG.

---

## Authentication Setup

### 1. GitHub OAuth (Device Flow) — Recommended
1. Create a GitHub OAuth App in **GitHub Settings → Developer settings → OAuth Apps**.
   - Set *Application name* to `GitHub Activity Manager`.
   - Set *Homepage URL* and *Authorization callback URL* to `https://github.com`.
   - Ensure **Device Flow** is enabled.
2. In the CLI menu, choose **1. Login with GitHub OAuth**.
3. Paste your **Client ID** (no client secret needed).
4. The CLI displays a one-time code and opens `https://github.com/login/device`. Enter the code to authorize.

### 2. Personal Access Token (PAT)
1. Go to **GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)**.
2. Generate a token with the following scopes:
   - `read:user` (to query profile and contribution calendar).
   - `repo` (only needed if creating or pushing to repositories).
3. In the CLI menu, choose **2. Login with Personal Access Token** and paste the token (input is masked).

---

## Activity Retrieval & Gap Detection

- **Contribution Retrieval (Menu 4)**: Queries GitHub's GraphQL `contributionCalendar` year-by-year for any custom range, full year, or multi-year span.
- **Empty Days & Weeks (Menu 5 & 6)**:
  - `ACTIVE` (`count > 0`): Protected. Never assigned planned commits.
  - `EMPTY` (`count == 0`): Eligible for planning unless excluded.
  - **Partially Active Weeks** are never discarded; their empty days remain eligible.
- **Known GitHub API Limitation**: A `0` count means GitHub's API returned no qualifying public/private contribution for that date. It does not prove no work occurred.

---

## Activity Configuration, Simulation & Exports

- **Configure (Menu 7)** & **Generate Plan (Menu 8)**: Set min/max commits, exact daily/weekly/monthly/total targets, weekend exclusions, patterns, and deterministic random seeds.
- **Preview Graph (Menu 9)**: View the simulated GitHub-style calendar and inspect individual dates. Simulated counts are always labeled separately from real GitHub contributions.
- **Manage Repositories (Menu 10)**: Create a new repo or select an existing one, update `activity.txt` for genuine current-time work, inspect the unified diff, test with dry-run, and push only after explicit confirmation.
- **Export Reports (Menu 11)**: Export CSVs, JSON, text summaries, SVG, and PNG graphs to `~/.github-activity-manager/exports/`.

---

## Privacy & Security

- All data is stored locally in `~/.github-activity-manager/` (`config.json`, `activity.db`, `logs/`, `exports/`, `cache/`).
- Tokens are stored in your OS keyring (with a `0600` encrypted local fallback if no keyring daemon is available), never in `config.json` or logs.
- No telemetry, no analytics, no centralized backend, and SSL verification is always enabled.
- Never generates fake backdated commits, never force-pushes, and never modifies unrelated repository files.

See [docs/SECURITY.md](docs/SECURITY.md), [docs/FEATURES.md](docs/FEATURES.md), [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md), [docs/INSTALLATION.md](docs/INSTALLATION.md), and [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).

---

## Troubleshooting by OS

### All Platforms
- **Missing dependencies**: Run `pip install -r requirements.txt`.
- **Git not found**: Ensure `git --version` works in your terminal and Git is added to your system `PATH`.
- **401 / Expired Token**: Select **13. Logout** and re-authenticate with OAuth or a fresh PAT.
- **Rate Limit (403)**: Wait until the GitHub API rate-limit reset window, or use cached data in `activity.db`.

### macOS
- **`command not found: python`**: Use `python3` instead of `python`, or add `alias python=python3` to your `~/.zshrc`.
- **Xcode CLI errors**: Run `xcode-select --install` to update command line developer tools.

### Linux
- **No keyring daemon found**: The tool automatically uses its built-in encrypted file fallback (`~/.github-activity-manager/`). If you want system keyring integration, install `gnome-keyring` and `libsecret-1-0`.
- **`python3-venv` missing**: On Ubuntu/Debian run `sudo apt install python3-venv`.

### Windows
- **PowerShell Script Execution Error (`PSSecurityException`)**:
  Run this once in PowerShell:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
- **Unicode/Box Drawing Artifacts in CMD**:
  Switch to [Windows Terminal](https://aka.ms/terminal) or PowerShell 7 for proper UTF-8 and Rich color rendering.
- **`'python' is not recognized`**:
  Reinstall Python and ensure you check **"Add python.exe to PATH"**, or use `py main.py`.

---

## Running Tests

```bash
# Using unittest:
python3 -m unittest discover -s tests -v

# Or on Windows:
python -m unittest discover -s tests -v

# Or using pytest:
pytest
```

---

## License & Attribution

Licensed under the **Apache License, Version 2.0**. See [LICENSE](LICENSE).  
Inspired by [Shpota/github-activity-generator](https://github.com/Shpota/github-activity-generator).
