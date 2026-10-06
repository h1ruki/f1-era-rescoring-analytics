# F1 ERAs

Historical Formula 1 dominance analytics

**How dominant was each F1 champion in their title-winning season?**

Compare every championship season in Formula 1 history by the gap between the
champion and runner-up.

**Active v1 development:** the current supported slice is **Drivers / Original,
2010–2013**. Full historical coverage is the v1 goal; it is not yet implemented.
Milestone 1 is partially complete; [Milestone 2](docs/decisions/MILESTONE_2_DECISION_RECORD.md)
defines the next stage toward a complete v1 comparison. Milestones are internal
development stages, not product versions.

## What you can explore now

- Compare the 2010–2013 title-winning seasons in a chronological interactive chart.
- Switch between Championship Margin (%) and Points Gap; inspect champion and
  runner-up points on hover.
- Explore historical championship reality. Broader coverage and supporting
  teammate/team context are still being integrated into the visible product.

## How the comparison is supported

The backend reads an immutable canonical F1DB SQLite snapshot, reconstructs
supported championships and checks the complete result against recorded standings.
Unsupported or rejected results do not display invented champions or margins.
Championship margin describes the title-winning points gap, not a complete measure
of driver ability. The [engineering brief](docs/architecture/F1_ERAs_MASTER_BRIEF.md)
explains the metrics, architecture and historical safeguards.

## Repository structure

| Path | Purpose |
| --- | --- |
| `README.md` | Project overview and links to deeper documentation |
| `SETUP.md` | Workstation setup, daily development and switching PCs |
| `run_dev.bat` | Portable Windows launcher for the active applications |
| `run_dev.sh` | Bash development launcher for macOS/Linux |
| `apps/` | The two active applications, grouped below |
| `apps/backend/` | Source access, exact analytics, service/API, trust metadata and tests |
| `apps/frontend/` | React application, chart presentation and frontend tests |
| `data/` | Canonical immutable F1DB database at `data/f1db.db` |
| `docs/` | Documentation map, roadmap, engineering brief and decision records |
| `legacy/` | Original Streamlit prototype, retained as historical source |

## Development environment

Follow **[SETUP.md](SETUP.md)** for Codex-assisted or manual setup on Windows,
macOS and Linux, daily development, switching PCs, running the project and verification.

## Documentation

- [Documentation map, roadmap and milestone status](docs/README.md)
- [Master engineering brief](docs/architecture/F1_ERAs_MASTER_BRIEF.md)
- [Historical data trust](docs/decisions/HISTORICAL_DATA_TRUST_DECISION_RECORD.md)
- [Backend API](apps/backend/README.md)
- [Frontend implementation](apps/frontend/README.md)
- [Archived Streamlit prototype](legacy/streamlit-prototype/README.md)

## Roadmap

- **v1 — Drivers / Historical Reality:** champion versus runner-up across the full
  history of the Drivers’ Championship. Teammate, team, competition and era
  context can support this comparison. Constructor identity supports Drivers analysis;
  Constructors Championship analysis is outside v1.
- **v2 — What If:** alternative scoring systems and counterfactual rescoring.
- **v3 — Constructors:** dedicated Constructors Championship analytics.

The [canonical roadmap and release policy](docs/README.md#product-versions-and-release-policy)
define these boundaries and the stable v1 analytical contract after release.

## Development

F1 ERAs is human-directed and AI-assisted. The project owner sets the product
vision, analytical direction and methodology decisions. AI tooling has supported
implementation, code review, testing and repository analysis.
