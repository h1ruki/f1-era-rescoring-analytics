# Development Setup

Set up a fresh computer to run F1 ERAs. Windows instructions use PowerShell;
macOS/Linux instructions use Bash. Internet access is needed for cloning and
dependency installation. All application commands run from the repository root.

## Runtime requirements

Python's canonical requirement is declared in
[pyproject.toml](../apps/backend/pyproject.toml): **3.11 is the minimum supported
version**. CI validates **Python 3.11 and 3.14**; **Python 3.14** is recommended
for a fresh setup. There is no exact interpreter pin.

The canonical supported Node.js range is declared in
[package.json](../apps/frontend/package.json) under `engines.node`. Prefer
**Node 24 LTS** for a fresh setup, using a version that satisfies that range.
CI currently validates **Node 24 on Ubuntu**. **Node 26** is also supported;
**Node 26.10.0** is known to work in local development, but Node 26 is not
currently CI-validated. Node.js includes npm; there is no exact npm pin.

## Windows setup

### Install prerequisites with PowerShell

Install Git, Python and Node.js with Windows Package Manager, following the
[runtime requirements](#runtime-requirements):

```powershell
winget install --id Git.Git --exact --source winget
winget install --id Python.Python.3.14 --exact --source winget
winget install --id OpenJS.NodeJS.LTS --exact --source winget
```

These package identifiers were verified against the official winget catalog.
Node.js includes npm. If `winget` is unavailable, install the same required
software through another package manager or installer, then continue below.

Open a **new PowerShell terminal** after installation and verify:

```powershell
git --version
python --version
node --version
npm.cmd --version
```

Use `npm.cmd` in PowerShell to avoid the `npm.ps1`
execution-policy restriction. If a command is unavailable, resolve its PATH
or installation before continuing.

### Clone and install dependencies

```powershell
git clone --branch development/v1 https://github.com/h1ruki/f1-era-rescoring-analytics.git
cd f1-era-rescoring-analytics
```

Run the following commands from this **repository root**. Paths containing
spaces are supported. You should see `README.md`, `run_dev.bat` and `apps/`.

Create the root virtual environment and install both applications' dependencies:

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -e "./apps/backend[test]"
npm.cmd --prefix apps/frontend ci
```

The backend command installs the project and its declared `test` extra from
[pyproject.toml](../apps/backend/pyproject.toml). Calling the environment's Python
directly avoids activating it or changing PowerShell execution policy. Frontend
installation follows the tracked [npm lockfile](../apps/frontend/package-lock.json).

Confirm the database is present:

```powershell
Test-Path .\data\f1db.db
```

This should return `True`. The canonical SQLite database is **tracked with the
repository**. Python's built-in `sqlite3` reads it; no separate database server,
standalone SQLite installation or database setup is required.

### Run the application

Double-click **`run_dev.bat`** after setup, or run:

```powershell
.\run_dev.bat
```

The launcher starts the backend and frontend in separate visible terminals,
then opens your default browser at <http://127.0.0.1:5173/>. Keep both service
terminals open while using the application; close both to stop it. Ports
**8000** and **5173** must be available. The launcher performs no installation.

### Manual startup on Windows

Open two PowerShell terminals at the repository root. In the first:

```powershell
& .\.venv\Scripts\python.exe -B -m uvicorn f1_eras.api.http:create_default_app --factory --app-dir apps/backend/src --host 127.0.0.1 --port 8000
```

In the second:

```powershell
npm.cmd --prefix apps/frontend run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

## macOS / Linux setup

Install **Git, Python, Node.js/npm and Bash** using your normal
system/package-management method, following the
[runtime requirements](#runtime-requirements). Python must include `pip`, `venv`
and `sqlite3`; no separate SQLite installation is needed.
Verify the tools with `git --version`, `python3 --version`, `node --version`,
`npm --version` and `bash --version`.

Clone and prepare the applications:

```bash
git clone --branch development/v1 https://github.com/h1ruki/f1-era-rescoring-analytics.git
cd f1-era-rescoring-analytics
python3 -m venv .venv
.venv/bin/python -m pip install -e "./apps/backend[test]"
npm --prefix apps/frontend ci
test -f data/f1db.db && echo "Canonical database is present."
```

The tracked database is included in the clone; no separate server or database
setup is needed. From the repository root, launch with:

```bash
./run_dev.sh
```

Alternatively, use **`bash run_dev.sh`**, which does not require the executable
bit. The launcher uses the root `.venv/bin/python`, starts both services in the
current terminal and attempts to open the browser. Keep that terminal open;
**Ctrl+C stops both services**. If the browser cannot open automatically, visit
<http://127.0.0.1:5173/> yourself. The script performs no installation. On native
Windows shells such as Git Bash, it directs you to `run_dev.bat`; WSL is treated
as Linux.

The Bash launcher has syntax/static validation; macOS/Linux application runtime
execution remains unverified. Windows launcher runtime validation has passed.

### Manual startup on macOS / Linux

Open two terminals at the repository root. In the first:

```bash
.venv/bin/python -B -m uvicorn f1_eras.api.http:create_default_app --factory --app-dir apps/backend/src --host 127.0.0.1 --port 8000
```

In the second:

```bash
npm --prefix apps/frontend run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

## Local development ports

The backend uses **<http://127.0.0.1:8000/>** and the frontend uses
**<http://127.0.0.1:5173/>**. These are fixed local development ports; an existing
process on either port can prevent startup. Vite proxies `/api` to the backend.
No environment variables or external services are required for normal local
startup.

## Verify the environment

The application should load the four **2010–2013 Drivers / Original** results.
Switching between Championship Margin (%) and Points Gap changes the displayed
metric. See the [frontend README](../apps/frontend/README.md) for implemented scope.

Run the existing health checks from the repository root. In PowerShell:

```powershell
& .\.venv\Scripts\python.exe -m ruff check --no-cache --config apps/backend/pyproject.toml apps/backend/src apps/backend/tests
& .\.venv\Scripts\python.exe -B -m pytest -c apps/backend/pyproject.toml apps/backend/tests -q -p no:cacheprovider
npm.cmd --prefix apps/frontend test
npm.cmd --prefix apps/frontend run build
$env:PYTHONPATH = 'apps/backend/src'
& .\.venv\Scripts\python.exe -B -m f1_eras.verification.diagnostic
```

On macOS/Linux:

```bash
.venv/bin/python -m ruff check --no-cache --config apps/backend/pyproject.toml apps/backend/src apps/backend/tests
.venv/bin/python -B -m pytest -c apps/backend/pyproject.toml apps/backend/tests -q -p no:cacheprovider
npm --prefix apps/frontend test
npm --prefix apps/frontend run build
PYTHONPATH=apps/backend/src .venv/bin/python -B -m f1_eras.verification.diagnostic
```

Ruff is lint-only in the current baseline; formatting is not enforced. The
frontend build includes unused-local and unused-parameter compiler checks through
`tsconfig.json`.

Tests should pass and the frontend build should complete. In the diagnostic,
all four seasons should report `state: passed`, `comparison: match`,
`trusted_for_normal_use: true` and zero award/standing differences. Exit zero
means the diagnostic completed; inspect its assessments too. Build output in
`apps/frontend/dist/` is ignored.

## Common problems

| Problem | Action |
| --- | --- |
| Git, Python, Node.js or npm is unavailable | Install the missing prerequisite, open a new terminal and repeat the version checks. Ensure it is on PATH. |
| Root `.venv` is missing | Create it from the repository root, then run the backend install command above. |
| Backend dependencies are missing | Repeat the backend install with the root `.venv` Python for your platform. |
| Frontend `node_modules` is missing | Repeat the frontend `ci` command for your platform. |
| `data/f1db.db` is missing | Check that the clone contains the tracked file. Do not create an empty database as a substitute. |
| Port 8000 or 5173 is occupied | Stop the existing service using that port, then restart the launcher. |
| Browser opens before startup finishes | Check both terminal logs and refresh once the services are ready. |
