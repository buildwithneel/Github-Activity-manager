# Installation Guide

Comprehensive installation instructions for **macOS**, **Linux**, and **Windows**.

---

## Prerequisites

- **Python 3.11 or newer**
- **Git** (`git --version`)
- A GitHub account and Personal Access Token or OAuth App

---

## 🍎 macOS Installation

1. **Install Prerequisites** (via [Homebrew](https://brew.sh/)):
   ```bash
   brew install python git
   ```
2. **Clone the repository**:
   ```bash
   git clone https://github.com/Neel-s-Workspace/Github-Activity-manager.git
   cd Github-Activity-manager
   ```
3. **Create and activate virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
4. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
5. **Run the CLI**:
   ```bash
   python3 main.py
   ```

---

## 🐧 Linux Installation

Supports Ubuntu, Debian, Fedora, Arch Linux, and WSL.

1. **Install Dependencies**:
   - *Ubuntu/Debian*:
     ```bash
     sudo apt update && sudo apt install -y python3 python3-pip python3-venv git libsecret-1-0
     ```
   - *Fedora*:
     ```bash
     sudo dnf install -y python3 python3-pip git libsecret
     ```
   - *Arch*:
     ```bash
     sudo pacman -Syu python python-pip git libsecret
     ```
2. **Clone the repository**:
   ```bash
   git clone https://github.com/Neel-s-Workspace/Github-Activity-manager.git
   cd Github-Activity-manager
   ```
3. **Create and activate virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
4. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
5. **Run the CLI**:
   ```bash
   python3 main.py
   ```

---

## 🪟 Windows Installation

Supports Windows 10 and 11 via PowerShell, CMD, or Git Bash.

1. **Install Prerequisites**:
   - Via winget: `winget install Python.Python.3.12 Git.Git`
   - Or install Python 3.11+ from [python.org](https://www.python.org/) (*make sure to check "Add python.exe to PATH"*).
2. **Clone the repository**:
   ```powershell
   git clone https://github.com/Neel-s-Workspace/Github-Activity-manager.git
   cd Github-Activity-manager
   ```
3. **Create virtual environment**:
   ```powershell
   python -m venv .venv
   ```
4. **Activate virtual environment**:
   - *PowerShell*:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
     *(If blocked by ExecutionPolicy: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`)*
   - *Command Prompt*:
     ```cmd
     .\.venv\Scripts\activate.bat
     ```
   - *Git Bash*:
     ```bash
     source .venv/Scripts/activate
     ```
5. **Install dependencies**:
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
6. **Run the CLI**:
   ```powershell
   python main.py
   ```
