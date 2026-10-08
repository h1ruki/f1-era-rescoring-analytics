# Changelog

Notable changes to F1 Title Margins are documented here.

## Pre-release

### 8 October 2026

#### Added

- Continuous integration verifies every pull request to `main` and every push to it: the Python
  lint and tests, a rebuild from the pinned F1DB release that must leave `data/seasons.json`
  unchanged, and the frontend tests, type-check and production build on Node 24.
- Reduced-motion support: chart animation is disabled when the visitor's system asks for reduced
  motion.
- A README covering the project, its architecture and data source, local setup, and copyright
  and reuse terms.

#### Fixed

- The chart's accessible description no longer tells users to select a bar for details; bars
  cannot be reached from the keyboard.

#### Changed

- The methodology's source note names F1DB's CC BY 4.0 licence and links to it.

### 7 October 2026

#### Fixed

- Headline extremes (most dominant, closest, largest and smallest points gap) are ranked from
  the underlying championship points rather than a rounded percentage, so genuine ties are told
  apart from margins that merely round to the same figure.
- The methodology now says dropped-score rules applied through 1990, making clear that 1990 is
  included.

#### Changed

- Seasons that genuinely tie for a headline extreme are disclosed beside the named season, for
  example "2007 (tied with 2008)".
- The 1995–1999 view is labelled "1990s 3-Litre Era" to distinguish it from the 1966–1976
  "3-Litre Era".
- The 1997 season note explains why Michael Schumacher was excluded from the championship
  classification.
- The methodology documents how a driver who raced for more than one constructor in a season is
  attributed to one of them.
- Regression tests pin the key historical claims in the methodology and the two-decimal
  precision of championship points that the headline ranking relies on.
- The F1DB source cache keeps at most two immutable, versioned SQLite snapshots: the pinned
  release plus one previous/reference snapshot. Release archives are verified in memory and
  never persisted.

#### Removed

- Archived legacy implementations from the active source tree; they remain recoverable through
  Git history.
- Obsolete colour-review tooling.
