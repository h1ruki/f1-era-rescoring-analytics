# F1 ERAs

Historical Formula 1 dominance analytics

**How dominant was each F1 champion in their title-winning season?**

Compare every championship season in Formula 1 history by the gap between the
champion and runner-up.

**Active v1 development:** the current supported slice is **Drivers / Original,
2010–2013**. Full historical coverage is the v1 goal; it is not yet implemented.

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
in [apps/backend/pyproject.toml](apps/backend/pyproject.toml) and
[apps/frontend/package.json](apps/frontend/package.json), with the frontend lockfile tracked.

## Repository structure

| Path | Purpose |
| --- | --- |
| `README.md` | Project overview and links to deeper documentation |
| `run_dev.bat` | Portable Windows launcher for the active applications |
| `run_dev.sh` | Bash development launcher for macOS/Linux |
| `apps/` | The two active applications, grouped below |
| `apps/backend/` | Source access, exact analytics, service/API, trust metadata and tests |
| `apps/frontend/` | React application, chart presentation and frontend tests |
| `data/` | Canonical immutable F1DB database at `data/f1db.db` |
| `docs/` | Setup guide, engineering brief and approved decision records |
| `legacy/` | Original Streamlit prototype, retained as historical source |

## Running locally

Start with the **[Development Setup guide](docs/SETUP.md)** for requirements,
cloning, root `.venv` creation and dependency installation. After setup, launch
from the repository root:

**Windows** — double-click `run_dev.bat`, or use PowerShell:

```powershell
.\run_dev.bat
```

**macOS / Linux** — use Bash:

```bash
./run_dev.sh
```

`bash run_dev.sh` also works without executable permission. The Windows launcher
opens separate service terminals; the Bash launcher keeps both services in the
current terminal and stops them with Ctrl+C. Both attempt to open the frontend at
<http://127.0.0.1:5173/>; the backend uses <http://127.0.0.1:8000/>. These fixed
local development ports must be available. Close both service windows on Windows
to stop. Neither launcher installs dependencies.

The setup guide includes **manual backend/frontend commands** for both platforms
and troubleshooting.

## Validation

Run from the repository root in PowerShell; equivalent macOS/Linux checks are in
[Development Setup](docs/SETUP.md):

```powershell
& .\.venv\Scripts\python.exe -B -m pytest -c apps/backend/pyproject.toml apps/backend/tests -q -p no:cacheprovider
npm.cmd --prefix apps/frontend test
npm.cmd --prefix apps/frontend run build
$env:PYTHONPATH = 'apps/backend/src'
& .\.venv\Scripts\python.exe -B -m f1_eras.verification.diagnostic
```

The backend suite includes synthetic policy tests and read-only integration checks
against the tracked snapshot. The diagnostic reports canonical trust and
reconciliation for 2010–2013; inspect each assessment, as exit code zero means the
diagnostic completed. Frontend validation covers interaction and rendering, while
the build checks TypeScript and produces ignored `apps/frontend/dist/` output.

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

- [Development Setup: fresh-machine instructions](docs/SETUP.md)
- [Master engineering brief](docs/architecture/F1_ERAs_MASTER_BRIEF.md)
- [Milestone 1A: championship methodology](docs/decisions/MILESTONE_1A_DECISION_RECORD.md)
- [Milestone 1B: historical identity](docs/decisions/MILESTONE_1B_DECISION_RECORD.md)
- [Historical data trust](docs/decisions/HISTORICAL_DATA_TRUST_DECISION_RECORD.md)
- [Verification foundation and retained history](docs/decisions/VERIFICATION_FOUNDATION_DECISION_RECORD.md)
- [Backend setup and API](apps/backend/README.md)
- [Frontend setup and validation](apps/frontend/README.md)
- [Archived Streamlit prototype](legacy/streamlit-prototype/README.md)

## Roadmap

- **v1 — Drivers / Historical Reality:** champion versus runner-up across the full
  history of the Drivers’ Championship. Teammate, team, competition and era
  context can support this comparison. Constructor identity supports Drivers analysis;
  Constructors Championship analysis is outside v1.
- **v2 — What If:** alternative scoring systems and counterfactual rescoring.
- **v3 — Constructors:** dedicated Constructors Championship analytics.

### Release philosophy

Once v1 is released, v1.x preserves its visible analytical contract and focuses
on maintenance: bug fixes, data corrections, dependency/security fixes,
documentation and small non-disruptive polish. Unfinished next-major functionality
stays isolated from the released experience; v2 becomes user-visible at v2.0,
and the same principle applies to v3. Major user-visible analytical changes arrive
with their corresponding major version.

Once releases begin, `main` represents the stable/released product line, while
next-major development can proceed separately.

## Development

F1 ERAs is human-directed and AI-assisted. The project owner sets the product
vision, analytical direction and methodology decisions. AI tooling has supported
implementation, code review, testing and repository analysis.
