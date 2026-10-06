# F1 ERAs

**Who were the most dominant F1 champions ever, accounting for teammate,
competition and era?**

F1 ERAs explores Formula One championship margins across seasons and scoring
contexts. Its starting measure is the gap between championship first and second
place: raw points or `(P1 points - P2 points) / P1 points × 100`.
Championship margin is an analytical lens, not a complete measure of driver ability.

The ambition is historically grounded comparison across eras, with teammate and
competition context. The current application implements a deliberately limited,
validated slice; broader coverage and contextual analysis remain roadmap work.

## Current implementation

- **2010–2013 Drivers / Original:** deterministic reconstruction under each
  supported season's original championship rules, using exact rational arithmetic.
- **Read-only API:** capabilities, championship margins, standings, event awards,
  reconciliation differences, source identity and trust assessments through FastAPI.
- **Interactive frontend:** a chronological Plotly lollipop chart with hover details,
  a percentage/points-gap toggle and a season summary list.
- **Explicit boundaries:** other seasons, Constructors calculations and
  counterfactual scoring are unavailable; unsupported or rejected results do not
  display invented champion or margin values.

## Engineering overview

The backend reads an immutable canonical F1DB SQLite snapshot, reconstructs
supported championships and checks the complete result against recorded standings.
One shared trust path checks snapshot approval, source integrity, population
completeness, exact points and sporting order before making results available.

Python owns championship mathematics. The frontend renders API-supplied values
and manages interactions; it does not recalculate scoring or championship margins.

**Stack:** Python 3.11+, FastAPI, Uvicorn and SQLite; React, TypeScript, Vite and
Plotly.js; pytest, Vitest and React Testing Library. Dependency versions are defined
in [backend/pyproject.toml](backend/pyproject.toml) and
[frontend/package.json](frontend/package.json), with the frontend lockfile tracked.

## Repository structure

| Path | Purpose |
| --- | --- |
| `backend/` | Source access, exact analytics, service/API, trust metadata and tests |
| `frontend/` | React application, chart presentation and frontend tests |
| `docs/` | Engineering brief and approved methodology/decision records |
| `legacy/` | Original Streamlit prototype, retained as historical source |
| `f1db.db` | Canonical database; deliberately retained at root for now |
| `run_dev.bat` | Portable Windows launcher for the active backend/frontend |

The local `data/f1db_newsnapshot.db` is an ignored temporary acceptance-test copy,
not a second runtime source or a tracked repository asset.

## Running locally

Use Windows PowerShell, Python 3.11+ and Node.js 26.x with npm, following the
project's documented development environment. From the repository root, perform
the one-time dependency setup:

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install "fastapi==0.142.2" "uvicorn==0.54.0" "httpx==0.28.1" "pytest==9.1.1"
npm.cmd --prefix frontend ci
```

Then launch the current application:

```powershell
.\run_dev.bat
```

The launcher checks the local environment, opens separate backend/frontend log
windows and opens <http://127.0.0.1:5173/> in your default browser after a short
startup delay. Ports **8000** and **5173** must be available. Close both service
windows to stop development. The launcher does not install dependencies or change
the database; Vite may create its normal ignored development cache.

Alternatively, start the backend from the repository root in one terminal:

```powershell
& .\.venv\Scripts\python.exe -B -m uvicorn f1_eras.api.http:create_default_app --factory --app-dir backend/src --host 127.0.0.1 --port 8000
```

In another terminal, also from the repository root:

```powershell
npm.cmd --prefix frontend run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Vite proxies `/api` to the backend at `http://127.0.0.1:8000`. See the component
READMEs below for endpoint and development details. `npm.cmd` avoids PowerShell's
`npm.ps1` execution-policy restriction.

## Validation

Run from the repository root:

```powershell
& .\.venv\Scripts\python.exe -B -m pytest -c backend/pyproject.toml backend/tests -q -p no:cacheprovider
npm.cmd --prefix frontend test
npm.cmd --prefix frontend run build
$env:PYTHONPATH = 'backend/src'
& .\.venv\Scripts\python.exe -B -m f1_eras.verification.diagnostic
```

The backend suite includes synthetic policy tests and read-only integration checks
against the tracked snapshot. The diagnostic reports canonical trust and
reconciliation for 2010–2013; inspect each assessment, as exit code zero means the
diagnostic completed. Frontend validation covers interaction and rendering, while
the build checks TypeScript and produces ignored `frontend/dist/` output.

## Data and trust

F1DB is the canonical historical dataset. An approved snapshot, supported rules,
passing integrity checks and exact reconciliation across the recorded championship
population establish trust for normal project use. Unsupported, ambiguous or
mismatching results fail closed; source/operational errors remain explicit errors.

Independent historical auditing is supplementary. **2010 is the deep-validation
exemplar**, not evidence of equivalent independent audits for 2011–2013. Its
preserved audit summary belongs to the earlier snapshot actually audited and does
not automatically transfer to the current approved snapshot.

## Documentation

- [Master engineering brief](docs/architecture/F1_ERAs_MASTER_BRIEF.md)
- [Milestone 1A: championship methodology](docs/decisions/MILESTONE_1A_DECISION_RECORD.md)
- [Milestone 1B: historical identity](docs/decisions/MILESTONE_1B_DECISION_RECORD.md)
- [Historical data trust](docs/decisions/HISTORICAL_DATA_TRUST_DECISION_RECORD.md)
- [Verification foundation and retained history](docs/decisions/VERIFICATION_FOUNDATION_DECISION_RECORD.md)
- [Backend setup and API](backend/README.md)
- [Frontend setup and validation](frontend/README.md)
- [Archived Streamlit prototype](legacy/streamlit-prototype/README.md)

## Roadmap

Approved direction includes broader historical coverage, supported counterfactual
scoring packages, Constructors mode, curated historical identity/colour and
teammate context, and controlled dataset-update automation. Each requires its own
implementation and validation; the brief records the boundaries and deferred work.

## Development

F1 ERAs is human-directed and AI-assisted. The project owner sets the product
vision, analytical direction and methodology decisions. AI tooling has supported
implementation, code review, testing and repository analysis.
