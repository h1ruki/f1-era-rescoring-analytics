# F1 Title Margins

**How dominant was each F1 champion in their title-winning season?**

F1 Title Margins charts the gap between the champion and the runner-up in every completed
Formula 1 Drivers' Championship season from 1950 to 2025.

**Live application: <https://f1-title-margins.pages.dev/>**

## What it shows

- **Percentage margin** is the default: (champion points − runner-up points) ÷ champion points
  × 100. It is the default because it stays comparable across scoring eras.
- **Points gap** is one toggle away. A raw gap is less comparable across eras, because a win has
  been worth 8, 9, 10 and 25 points.
- A year range and curated era views narrow the chart, and the headline figures follow the
  selection. Bars carry the champion's constructor colour; shaded bands mark the finishing-points
  scale in use.

## Architecture

```text
pinned F1DB release
  → deterministic Python pipeline         pipeline/
  → committed data/seasons.json
  → React + TypeScript + ECharts + Vite   src/
  → static deployment
```

v1 has no runtime backend or API. The browser loads a static bundle with the season data compiled
in.

## Data and methodology

- The source is [F1DB](https://github.com/f1db/f1db) v2026.16.0, pinned by version and SHA-256 in
  [`data/f1db-release.json`](data/f1db-release.json).
- Champion and runner-up totals are F1DB's recorded final Drivers' Championship standings. They
  are not reconstructed by summing race results, so historical rules such as dropped scores are
  reflected exactly as recorded.
- The pipeline is deterministic: rebuilding from the same pin reproduces
  [`data/seasons.json`](data/seasons.json) byte for byte.

For the scoring history behind the numbers, open **How this is measured** in the
[app](https://f1-title-margins.pages.dev/).

## Technologies

- **Data:** Python (standard library only: `sqlite3`, `decimal`), tested with pytest and linted
  with Ruff.
- **Frontend:** React, strict TypeScript, ECharts, Vite and Vitest.
- **Delivery:** GitHub Actions for verification; static hosting on Cloudflare Pages.

## Local setup

### Frontend

Node 24, as declared in [`.nvmrc`](.nvmrc). The season data is committed, so the frontend runs
without Python.

```sh
npm ci
npm run dev      # development server
npm test         # unit tests
npm run build    # type-check, then production build into dist/
npm run preview  # serve the production build
```

### Data pipeline

Python 3.14 is the release-verification environment.

```sh
python -m venv .venv             # then activate it
python -m pip install -r requirements-dev.txt
python -m pytest
ruff check .
python pipeline/build_seasons.py
```

The first pipeline run downloads the pinned F1DB snapshot into an ignored local cache and verifies
its digest; later runs reuse it.

## Verification

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) is the canonical release verification
contract. The commands above are conveniences; where they differ from the workflow, the workflow
is authoritative.

## Accessibility

Known limitation: the per-season detail in the chart tooltip (drivers, constructors, points and
exact margin) currently requires a pointer or touch.

## Feedback

Please report calculation bugs, presentation bugs and other defects in this project through
[GitHub Issues](https://github.com/h1ruki/f1-title-margins/issues). A suspected error in the
underlying source figures belongs upstream, with [F1DB](https://github.com/f1db/f1db/issues).

## Project status

This is v1: the historical Drivers' Championship release, covering completed seasons 1950–2025.
Changes are recorded in [CHANGELOG.md](CHANGELOG.md). Any later version would be scoped
separately.

## Copyright and reuse

### Application source code

© 2026 h1ruki. All rights reserved.

The original F1 Title Margins application and source code are not open source. No permission is
granted to reuse, modify, redistribute or commercially use them beyond the rights that
[GitHub's Terms of Service](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service)
provide for public repositories, unless separately authorised by the owner.

### F1DB-derived data

The championship data in this project, including `data/seasons.json`, is adapted from
[F1DB](https://github.com/f1db/f1db) v2026.16.0: it is reduced to each season's champion and
runner-up, with the margins calculated by this project. F1DB is licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The reservation above does not apply to
this F1DB-derived material and does not limit the rights CC BY 4.0 grants in it.

## Unofficial project

F1 Title Margins is unofficial and is not affiliated with or endorsed by Formula 1 or the FIA.
