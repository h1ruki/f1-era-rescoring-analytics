# Development Environment and Workstation Setup

This root `SETUP.md` is the **single authoritative development environment and
workstation setup guide for F1 ERAs**, covering Windows, macOS and Linux.
The currently active development branch is `development/v1`.

| Situation | Workflow |
| --- | --- |
| New PC, rebuilt environment, missing/broken tools, or deliberate toolchain change | [Codex-assisted first-time setup](#codex-assisted-first-time-setup), [manual Windows](#manual-windows-setup), or [manual macOS/Linux](#manual-macoslinux-setup) |
| Returning to a configured machine | [Returning to an already-configured machine](#returning-to-an-already-configured-machine) |
| Moving work from the main workstation to a second PC | [Switching Between Development PCs](#switching-between-development-pcs) |
| Starting services or checking a change | [Running](#running-the-project) and [verifying](#verifying-the-project) |
| A check fails or Git state is unexpected | [Troubleshooting and safe recovery](#troubleshooting-and-safe-recovery) |

First-time setup prepares the machine. Normal daily work opens the existing repo,
updates the confirmed branch and starts the project. **Do not rerun the complete
bootstrap every evening.** Internet access is needed for GitHub updates and installs.

## Returning to an already-configured machine

Open the existing root in VS Code (`code .`). Follow the receiving-PC checks below
to inspect, fetch, confirm the branch and update safely, then [start the project](#running-the-project).
Keep `.venv` and `node_modules`; run checks appropriate to your changes.

After fetching, but before pulling, you can check for incoming dependency changes:

```text
git diff --name-only HEAD '@{upstream}' -- apps/backend/pyproject.toml apps/frontend/package.json apps/frontend/package-lock.json
```

After confirming the upstream, this shows incoming dependency-file changes. If
listed, rerun only the relevant backend install and/or frontend `ci` after pulling,
using your OS commands below. Recheck Python/Node versions if their requirements
changed. A source-only update does not need a full bootstrap.

Keep environments local: sync source through GitHub, not `.venv`, `node_modules`
or build outputs.

## Switching Between Development PCs

The main workstation normally does most development; a second Windows PC may
continue in the evening. GitHub carries committed work; uncommitted files remain
on the original PC.

### Leaving the main workstation (or whichever PC you used last)

1. Finish a coherent piece of work and run the [appropriate checks](#verifying-the-project).
2. Inspect `git status`, `git diff` and `git diff --cached`. Run
   `git branch --show-current` and `git branch -vv`; record the actual working
   branch and confirm its upstream. Active v1 work currently uses `development/v1`.
3. Stage only reviewed files (use `git add -- path/to/reviewed-file`, replacing the
   example path), inspect `git diff --cached`, then commit with a clear message:
   `git commit -m "Describe the completed change"`.
4. Push that confirmed branch with `git push`. If there is no upstream or the push
   is rejected, stop and investigate; never force-push as part of a handoff.
5. Confirm `git status` is clean and the branch is up to date with its upstream.
   Record `git log -1 --oneline` with the branch so the next PC can verify the same
   commit. Any expected local generated files must be understood and must not hide
   unfinished source work. Stop both services before leaving.

### Receiving the work on the second PC (same commands on any OS)

Open the existing local F1 ERAs repository, then run:

```text
git status
git branch --show-current
git remote -v
```

`git status` checks local changes, the branch command shows the current branch,
and `git remote -v` confirms the GitHub repository. **Stop on unexpected local
changes**; never automatically stash, reset, clean or discard them.

Fetch remote branch information without changing working files:

```text
git fetch
git branch -vv
```

Fetch updates remote tracking information without changing working files.
`git branch -vv` shows upstreams. Confirm the intended branch from the outgoing
PC's handoff/session context; stop on ambiguity. Do not infer it from GitHub's
default branch. For a confirmed `development/v1` handoff, if switching is needed:

```text
git switch development/v1
```

If the confirmed branch exists only remotely, use
`git switch --track origin/development/v1`. Never switch over unexpected local changes.

Once on the confirmed branch, verify `git branch --show-current` and
`git branch -vv` again. For `development/v1`, expect upstream
`origin/development/v1`. Then:

```text
git pull --ff-only
git status
git log -1 --oneline
git rev-parse HEAD
git rev-parse '@{upstream}'
```

`git pull --ff-only` updates only without a merge; stop if rejected. Local commits
ahead of GitHub also need investigation: "already up to date" alone does not prove
equality. The final hashes must match, status must be clean/expected, and the
handoff commit must be present. Review any newer GitHub changes before continuing.
No merge, rebase, force push or reinstall is automatic.

### Codex: update this PC and continue

```text
Read SETUP.md and follow "Switching Between Development PCs". This PC is already configured; do not reinstall the environment. Check local changes, fetch, verify the branch I was working on and its upstream, then update with fast-forward-only Git operations. Confirm HEAD matches GitHub and report ready to continue. Stop on unexpected local changes, divergence or branch ambiguity.
```

## Project location and branch

The repository root contains `SETUP.md`, `README.md`, `run_dev.bat`, `apps/`
and `data/`. The backend is `apps/backend`, the frontend is `apps/frontend`,
and the Python environment belongs at the root in `.venv`.
All application commands below run at the **repository root**. Windows examples
use PowerShell; macOS/Linux examples use Bash. Paths with spaces are supported.

On the current workstation the root is `C:\Users\thebi\Documents\f1-eras`:

```powershell
Set-Location 'C:\Users\thebi\Documents\f1-eras'
```

On another computer choose your own location. For a fresh clone, after Git is
installed, run these commands from the parent folder where you want the project:

```powershell
git clone --branch development/v1 https://github.com/h1ruki/f1-eras.git
Set-Location f1-eras
```

On macOS/Linux, clone from your chosen parent directory with:

```bash
git clone --branch development/v1 https://github.com/h1ruki/f1-eras.git
cd f1-eras
```

For an existing clone, use the [receiving-PC checks](#switching-between-development-pcs).
Fresh active-v1 clones use `development/v1`; `main` represents the stable/release
line once releases begin. The Windows setup script requires `development/v1` and
never switches branches or discards changes.

## Required software

| Software | Repository requirement | Version check |
| --- | --- | --- |
| Shell | Windows: PowerShell 5.1 or 7+; macOS/Linux: Bash for these examples/launcher | Windows: `$PSVersionTable.PSVersion`; macOS/Linux: `bash --version` |
| Git | No version pin; a current supported Git for your OS | `git --version` |
| VS Code | Optional editor for manual development; required by the chosen Windows automation. No version pin; its CLI must be on PATH when used | `code --version` |
| Python | `>=3.11` in [pyproject.toml](apps/backend/pyproject.toml); CI covers 3.11 and 3.14 | Windows: `py -3 --version` or `python --version`; macOS/Linux: `python3 --version` |
| Node.js | `^24.15.0 || ^26.0.0` in [package.json](apps/frontend/package.json): stable 24.x >=24.15.0 or stable 26.x | `node --version` |
| npm | Bundled with compatible Node.js; no npm version pin; must support lockfile version 3 and `npm ci` | Windows: `npm.cmd --version`; macOS/Linux: `npm --version` |

Prefer Python 3.14 and Node 24 LTS for fresh installs; keep existing compatible
tools. Python needs `venv`, `pip` and `sqlite3`. Python has no declared upper bound,
but versions beyond CI coverage must pass verification. CI tests Node 24 on Ubuntu;
Node 26 is declared compatible but not in that matrix. Historical workstation
versions are not project pins.

Both manual routes use the editable backend install with the declared `test` extra
(pytest, httpx and Ruff) and pip's isolated build requirements. Frontend `ci` uses
the tracked [lockfile](apps/frontend/package-lock.json) and recreates `node_modules`;
do not keep hand-edited files there. Stop services before installing dependencies.
The tracked `data/f1db.db` needs no import, server or separate SQLite install.

## VS Code extensions

[.vscode/extensions.json](.vscode/extensions.json) uses VS Code's normal
[workspace recommendations](https://code.visualstudio.com/docs/configure/extensions/extension-marketplace).
Open **Extensions**, search `@recommended`, and install the six listed extensions,
or use these commands:

```text
code --install-extension openai.chatgpt
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension charliermarsh.ruff
code --install-extension eamodio.gitlens
code --install-extension github.vscode-pull-request-github
code --list-extensions
```

These are Codex, Microsoft Python, Microsoft Pylance, Ruff, GitLens, and GitHub Pull
Requests and Issues, respectively. IDs were checked with `code --list-extensions`;
required supporting extensions may also install. Manual development works without
using Codex. These are editor recommendations, not requirements for running F1 ERAs.
The Windows script installs them as part of the chosen VS Code environment.
Ruff is lint-only; no automatic formatting settings are added.

Manual development can use another editor and skip VS Code/extension steps below.

## Codex-assisted first-time setup

Windows automation supports PowerShell 5.1 and 7+. See its validation limits below.

1. Install Git and VS Code if missing, then clone/open the root (`code .` or
   **File > Open Folder**) and open `SETUP.md`.
2. Install Codex if needed: **Extensions**, search `@id:openai.chatgpt`.
   Paste the prompt below into Codex with this repository open.
3. Codex inspects/runs the Windows script or follows the macOS/Linux manual route,
   with approval where required. Finish verification and the browser checklist;
   stop on a genuine blocker. Windows automated success is `READY FOR DEVELOPMENT`
   with exit code 0; the browser check follows.

## Codex Quick Setup

```text
Read SETUP.md completely and perform first-time setup for this OS. Inspect scripts/setup-windows.ps1 before using Windows automation. Use the manual route on macOS/Linux. Request approval where required. Do not change application logic, F1 data, dependency versions or lockfiles. Continue through verification and the browser check until ready or genuinely blocked.
```

The **Windows-only** script command, after inspection, is:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-windows.ps1
```

`Bypass` affects only this child process, not saved policy; use the manual route if
organisational policy blocks it. PowerShell 7 can use `pwsh` instead.
For bootstrap/repair, reruns reuse a valid `.venv`, skip installed extensions,
repeat declared installs and verify. The script checks database/manifest/lockfile
hashes and never commits, pushes, creates PRs, updates dependencies or formats code.
The script has been statically reviewed and parsed. Diagnostic-array normalization
and its rejection checks passed with synthetic JSON on Windows PowerShell
5.1.26100.9549; modern `pwsh` was unavailable. The full bootstrap has not been run.
Automated workstation readiness still requires a real setup run.

## Manual Windows setup

Follow the shared [requirements](#required-software) and [project location/branch](#project-location-and-branch).
Install only missing prerequisites using either method below; winget is optional.

### Install missing prerequisites with winget

Check `winget --version`. Run only the commands for software you need:

```powershell
winget install --id Git.Git --exact --source winget
winget install --id Microsoft.VisualStudioCode --exact --source winget
winget install --id Python.Python.3.14 --exact --source winget
winget install --id OpenJS.NodeJS.LTS --version 24.15.0 --exact --source winget
```

Node 24.15.0 is a compatible bootstrap choice, not a project pin; newer stable
24.x works too. If that catalog version is unavailable, use the official fallback.
The script uses these IDs and stops on incompatible existing Node. Installer
prompts may require administrator approval; see the [winget reference](https://learn.microsoft.com/en-us/windows/package-manager/winget/install).

After installation **close and reopen VS Code and PowerShell** so PATH updates
take effect. Repeat all version checks in the table before continuing.

### Official fallback when winget is unavailable

Use these official installers; no third-party mirrors are needed:

- [Git for Windows](https://git-scm.com/install/windows): enable command-line Git on PATH.
- [VS Code for Windows](https://code.visualstudio.com/docs/setup/windows): use the User installer and enable Add to PATH.
- [Python for Windows](https://www.python.org/downloads/windows/): choose stable Python 3.14, include pip and enable the Python launcher/PATH options where offered.
- [Node.js downloads](https://nodejs.org/en/download): choose a Windows installer for stable Node 24.x >=24.15.0 (or stable 26.x), including npm and PATH support.

Winget comes with [App Installer](https://learn.microsoft.com/en-us/windows/package-manager/winget/)
and is optional. If software is installed but unavailable, fix PATH/restart the
terminal before rerunning setup. The script stops when safe installation is unavailable.

Open the root in VS Code with `code .`. Use **Terminal > New Terminal**, select
**PowerShell**, and confirm `Get-Location` shows the root. Install the
[recommended extensions](#vs-code-extensions), then prepare the project:

### Create/use the root Python environment and install the backend

From the repository root, create `.venv` **only if it does not already exist**:

```powershell
py -3.14 -m venv .venv
```

If the launcher is unavailable, use `python -m venv .venv` after verifying that
`python --version` satisfies `>=3.11`. If another compatible interpreter is
installed, select it explicitly, for example `py -3.11 -m venv .venv`.
Check an existing environment before using it; an invalid/incompatible one is a
blocker to resolve deliberately, not something the script deletes or overwrites.

```powershell
& .\.venv\Scripts\python.exe --version
& .\.venv\Scripts\python.exe -c "import sys, sqlite3, venv; assert sys.version_info >= (3, 11); assert sys.version_info.releaselevel == 'final'; assert sys.prefix != sys.base_prefix; print(sys.executable)"
& .\.venv\Scripts\python.exe -m pip --version
& .\.venv\Scripts\python.exe -m pip install -e "./apps/backend[test]"
```

Calling `.venv`'s Python directly avoids activation. In VS Code use
**Python: Select Interpreter** and choose `.venv\Scripts\python.exe`.

### Install frontend dependencies and check the data

```powershell
npm.cmd --prefix apps/frontend ci
Test-Path .\data\f1db.db
```

Use `npm.cmd` to avoid `npm.ps1` execution-policy restrictions. The database check
must return `True`. On install/data errors, stop and use [safe recovery](#troubleshooting-and-safe-recovery).

Continue with [verification](#verifying-the-project), [startup](#running-the-project)
and the [ready checklist](#ready-for-development-checklist).

## Manual macOS/Linux setup

The Windows setup script does not run on these platforms. Prepare the OS-specific
prerequisites below, then follow the shared Bash project commands.

### macOS prerequisites

- Git: if `git --version` is unavailable, install Apple's Command Line Tools with
  `xcode-select --install`, as described by [Git's official macOS guide](https://git-scm.com/install/mac).
- Python: use the [official macOS installer](https://www.python.org/downloads/macos/)
  for stable 3.14, or keep a compatible existing interpreter. Open a new terminal
  and verify `python3 --version`; do not assume an OS-provided Python is compatible.
- Node/npm: use a compatible 24.x macOS `.pkg` from [official Node.js downloads](https://nodejs.org/en/download),
  selecting your architecture. Keep an existing compatible Node 26 if preferred.
- VS Code: follow [Microsoft's macOS installation](https://code.visualstudio.com/docs/setup/mac).
  In its Command Palette run **Shell Command: Install 'code' command in PATH**,
  then restart the terminal. Bash is available for the commands and launcher below.

### Linux prerequisites

For Ubuntu/Debian with Python 3.11+ available in the official distro repositories:

```bash
sudo apt update
sudo apt install git python3 python3-venv python3-pip xz-utils
```

Verify `python3 --version`; stop if the distro supplies an older Python. Use a
supported distribution/interpreter rather than replacing its system Python.
Other distributions need their official packages for Git, Bash, compatible Python,
venv/pip and SQLite support. See [Ubuntu's Python setup guidance](https://ubuntu.com/developers/docs/howto/python-setup/).
Install VS Code using Microsoft's [official Linux package instructions](https://code.visualstudio.com/docs/setup/linux).

For Node/npm, use your distro's official packages only if they satisfy the shared
Node range. Otherwise download a compatible Linux binary from
[official Node.js downloads](https://nodejs.org/en/download). For example, after
downloading `node-v24.15.0-linux-x64.tar.xz` to `~/Downloads`:

```bash
mkdir -p "$HOME/.local/share/nodejs"
tar -xJf "$HOME/Downloads/node-v24.15.0-linux-x64.tar.xz" -C "$HOME/.local/share/nodejs"
export PATH="$HOME/.local/share/nodejs/node-v24.15.0-linux-x64/bin:$PATH"
```

This example is for x64; use the matching archive/directory for your machine
(`uname -m` shows its architecture) and selected compatible version. Add that
`export PATH` line once to the startup file of the shell you use so new terminals
and VS Code inherit it, then restart them. Do not use unofficial mirrors.

### Prepare the project (both macOS and Linux)

Run all [software version checks](#required-software) before creating the environment.

Follow [Project location and branch](#project-location-and-branch) to clone/open
the root and [VS Code extensions](#vs-code-extensions) to install the six recommendations.
Create `.venv` only if it does not exist; select a compatible interpreter explicitly
if `python3` points elsewhere (for example `python3.14 -m venv .venv`):

```bash
python3 -m venv .venv
.venv/bin/python --version
.venv/bin/python -c "import sys, sqlite3, venv; assert sys.version_info >= (3, 11); assert sys.version_info.releaselevel == 'final'; assert sys.prefix != sys.base_prefix; print(sys.executable)"
.venv/bin/python -m pip --version
.venv/bin/python -m pip install -e "./apps/backend[test]"
npm --prefix apps/frontend ci
test -f data/f1db.db
```

The final command must exit successfully; stop on missing data or install errors.
Use **Python: Select Interpreter** in VS Code and choose `.venv/bin/python`.
All commands here call it directly; optional [venv activation](https://docs.python.org/3/library/venv.html)
is `source .venv/bin/activate`, and `deactivate` exits it. Activation affects only
that terminal; neither activation nor global pip installs are required.

Continue with [verification](#verifying-the-project), [startup](#running-the-project)
and the [ready checklist](#ready-for-development-checklist).

## Running the project

Open **two terminals at the repository root**, using the commands for your OS.

### Windows (PowerShell)

In terminal 1, start the backend:

```powershell
& .\.venv\Scripts\python.exe -B -m uvicorn f1_eras.api.http:create_default_app --factory --app-dir apps/backend/src --host 127.0.0.1 --port 8000
```

In terminal 2, start the frontend:

```powershell
npm.cmd --prefix apps/frontend run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

### macOS/Linux (Bash)

In terminal 1:

```bash
.venv/bin/python -B -m uvicorn f1_eras.api.http:create_default_app --factory --app-dir apps/backend/src --host 127.0.0.1 --port 8000
```

In terminal 2:

```bash
npm --prefix apps/frontend run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

### Browser check and launchers (all OSes)

Keep both terminals open. Open <http://127.0.0.1:5173/> and check the four
2010-2013 Drivers / Original results and the Championship Margin (%)/Points Gap
toggle. Backend API documentation is at <http://127.0.0.1:8000/docs>.
Vite proxies `/api` to port 8000. Ports 8000 and 5173 must be free; stop an existing
service deliberately if it occupies them. Ctrl+C in each terminal stops the services.
Normal local startup needs no environment variables or external services.

Alternatively, use the existing launchers from the root:

- Windows: `.\run_dev.bat` (or double-click it). It opens two service windows;
  close both to stop.
- macOS/Linux: `bash run_dev.sh` works without executable permission;
  `./run_dev.sh` also works when executable. It keeps both services in the current
  terminal; Ctrl+C stops both. It uses Bash, including when your usual shell is Zsh.

Neither launcher installs dependencies. Both attempt to open the browser. If it
opens too early, inspect the service logs and refresh once ready; if it cannot open,
visit the frontend URL yourself. On native Windows/Git Bash use `run_dev.bat`;
WSL follows the Linux route. The Bash launcher has static validation, but a fresh
macOS/Linux workstation setup and application runtime have not been verified here.

## Verifying the project

After first-time/rebuilt setup, run every check below. During development, run the
checks relevant to your change; run the full suite when dependencies or toolchains
change or the impact is uncertain. Run commands individually at the root and stop
at the first failure.

### Windows (PowerShell)

```powershell
# Backend lint (no formatting or fixes)
& .\.venv\Scripts\python.exe -m ruff check --no-cache --config apps/backend/pyproject.toml apps/backend/src apps/backend/tests
# Full backend suite, including read-only canonical database integration checks
& .\.venv\Scripts\python.exe -B -m pytest -c apps/backend/pyproject.toml apps/backend/tests -q -p no:cacheprovider
# Frontend tests
npm.cmd --prefix apps/frontend test
# TypeScript verification and production build: package.json runs tsc --noEmit then vite build
npm.cmd --prefix apps/frontend run build
# Read-only historical diagnostic
& .\.venv\Scripts\python.exe -B -m f1_eras.verification.diagnostic
```

### macOS/Linux (Bash)

```bash
.venv/bin/python -m ruff check --no-cache --config apps/backend/pyproject.toml apps/backend/src apps/backend/tests
.venv/bin/python -B -m pytest -c apps/backend/pyproject.toml apps/backend/tests -q -p no:cacheprovider
npm --prefix apps/frontend test
npm --prefix apps/frontend run build
.venv/bin/python -B -m f1_eras.verification.diagnostic
```

### Check results and Git state (all OSes)

```text
git status --short --branch
git diff --check
git diff
```

The editable backend install makes the diagnostic importable without a PYTHONPATH
override. The script clears a session `F1_ERAS_DB_PATH` override for verification
so integration tests use the tracked database, then restores it afterward. For
manual verification use a terminal without that override (`Remove-Item
Env:F1_ERAS_DB_PATH -ErrorAction SilentlyContinue` clears it in PowerShell;
`unset F1_ERAS_DB_PATH` clears it in Bash).

Check `$LASTEXITCODE` in PowerShell or `echo $?` in Bash immediately after a
command; zero means success. The diagnostic is stricter than its exit
code: each of **2010, 2011, 2012 and 2013** must have `state: passed`,
`comparison: match`, `trusted_for_normal_use: true`, and zero award/standing
differences. The script parses and checks these fields before printing READY.
`run build` includes `tsc --noEmit` before Vite; no separate typecheck command is
needed. `dist/` is ignored. Pip can create untracked `apps/backend/src/*.egg-info/`
metadata; review generated files and do not stage them as source changes.

## Ready-for-development checklist

- [ ] Correct repository root and confirmed working branch (currently `development/v1`); existing work is preserved.
- [ ] Git, compatible Python and Node/npm version checks pass; VS Code CLI passes if using the VS Code environment.
- [ ] For the chosen VS Code environment, the six recommended extensions are installed in the profile in use; they are not runtime requirements.
- [ ] Root `.venv` works and is selected in VS Code; backend editable install and frontend lockfile installation succeeded.
- [ ] Ruff, full backend tests, frontend tests, TypeScript/production build and all four diagnostic trust assessments pass.
- [ ] Git diff has no unexpected application, dependency declaration, lockfile or data changes.
- [ ] Both services start and the browser smoke check succeeds.

## Troubleshooting and safe recovery

Read the first failed step and preserve the error and existing files. Stop on
unexpected Git changes, branch/upstream ambiguity, divergence or a rejected
fast-forward. Resolve that state deliberately with the owner; never automatically
stash, reset, discard, merge or force-push. GitHub stores committed work, not local
environments; rebuilding a missing environment does not recover unpushed source.

| Problem | Safe next step |
| --- | --- |
| Tool missing or not on PATH | Use the OS prerequisite instructions and official installers; restart the terminal/VS Code and repeat version checks. Winget is optional. |
| `.venv` missing | Create it at the root and run the backend install for your OS. |
| `.venv` exists but fails its checks | Stop; inspect the interpreter/path before a deliberate rebuild. The script never deletes or overwrites it. |
| Missing Python venv/pip/SQLite support on Linux | Install the matching official distro packages, then retry environment creation. Do not install project dependencies into system Python. |
| Dependencies changed or are missing | Stop dev servers, rerun only the relevant declared backend install or frontend `ci`, then verify. |
| `npm ci` rejects the lockfile or registry access fails | Preserve the error and investigate. Do not substitute `npm update`, upgrade dependencies or regenerate the lockfile. |
| Tracked `data/f1db.db` missing or trust rejected | Check the clone and diagnostic findings. Do not create an empty DB or change historical data to pass setup. |
| Port 8000/5173 occupied | Identify and deliberately stop the existing service, then restart. |
| Browser opens before servers are ready | Inspect both logs and refresh after startup; open the frontend URL manually if needed. |
| PowerShell script blocked by policy | Use the manual Windows route; do not weaken organisational policy. |

Do not fix environment problems by changing application logic, historical F1 data,
dependency versions or lockfiles. Once the blocker is resolved, resume the relevant
manual steps, or rerun Windows automation if a bootstrap repair is needed, and
repeat verification. A clean ordinary daily update does not call for a rebuild.
