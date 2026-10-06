# F1 ERAs ? Master Engineering Brief

F1 ERAs is an interactive Formula One historical analytics application. Its
central question is how large the gap between championship first and second
place was across seasons, eras and scoring systems. Championship margin is an
analytical measure, not a complete measure of driver ability or dominance.

This specification records product direction, methodology and development
boundaries. Roadmap requirements below do not imply implemented support.

## Authority and current implementation

- [Milestone 1A](../decisions/MILESTONE_1A_DECISION_RECORD.md) governs scoring, eligible
  results, countback, sanctions, exact arithmetic, ambiguity and unavailable states.
- [Milestone 1B](../decisions/MILESTONE_1B_DECISION_RECORD.md) governs historical identity,
  chassis usage, constructor attribution, teammate relationships and driver patterns.
- [Historical data trust](../decisions/HISTORICAL_DATA_TRUST_DECISION_RECORD.md) governs
  canonical trust and supplementary external auditing.
- [Verification foundation](../decisions/VERIFICATION_FOUNDATION_DECISION_RECORD.md)
  preserves the earlier independent-evidence methodology and its supersession
  as a normal-use production gate.

The implemented calculation/API scope is **2010?2013 Drivers / Original**.
Other seasons, Constructors calculations and counterfactual packages remain
unavailable until their rules and implementation are approved and validated.
Broader historical coverage is a product goal, not a current capability claim.

The initial repository/data audit is complete. Its former audit-only instructions
are retired. The prototype and decision records retain historical context;
subsequent development follows the approved architecture and milestone decisions.

## Product and analytical experience

Product name: **F1 ERAs**. Subtitle: **Championship dominance across Formula One history**.

The main experience is one interactive chronological lollipop chart comparing
championship P1 and P2. Drivers and Constructors modes should ultimately share
its interaction model. Each season is an independent observation with a meaningful
zero baseline; connecting markers with a line would imply interpolation.

The chart supports hover, pinned selection and a detail drawer, season-range
changes, era presets, margin metrics, scoring packages and colour modes. Full-history
view is a long-term goal; the current view must respect available calculation scope.

The default product state is Drivers, Championship Margin (%), Original scoring,
All F1 range and historical colours. V1 uses a restrained dark theme, designed
primarily for desktop analytical viewing with reasonable small-screen behaviour.
Avoid excessive gradients, decorative effects and motorsport clich?s.

The primary metric is:

`Championship Margin (%) = (P1 points - P2 points) / P1 points ? 100`

Raw Points Gap is `P1 points - P2 points`. Percentage margin makes comparisons
less directly dependent on points inflation, but it does not remove differences
in rules, event populations or historical context. Exact calculation values govern
ranking and reconciliation; floats and rounding are display projections only.
An undefined denominator must not yield an invented valid margin.

Hover should give concise season, P1/P2, constructor attribution, points, gap,
active scoring package and relevant historical context. The drawer may expose
countback, event awards, all constructor contributions, wins, podiums, poles,
reliability, supported teammate status, constructor championship context and
source provenance. Unsupported contextual fields remain explicitly unavailable.

A historical average line uses only completed, available seasons in the selected
mode, metric, scoring package and range. Recalculate it when those selections
change. Omit it when no eligible observations exist. Scoring-change annotations
should be subtle and may be deemphasised when a single counterfactual package
replaces Original rules throughout the range.

## Source data, trust and snapshot rotation

F1DB is the canonical historical dataset. Application code treats `data/f1db.db` as
immutable source data and must never alter its records to satisfy a test.

[backend/historical/canonical_snapshot.json](../../backend/historical/canonical_snapshot.json)
is the machine-readable runtime approval authority for release, release commit,
database SHA-256 and byte size. SQLite schema/user counters are not release versions.
Unknown claim-level upstream source lineage remains documented and non-blocking.

Normal-use trust requires an approved snapshot, supported deterministic
reconstruction, integrity checks and exact complete championship reconciliation.
The repository binds all assessment reads to one captured SQLite image and
independently queries its unfiltered canonical championship driver population.
Matching truncated reconstruction and comparison inputs cannot prove completeness.
Ranked zero-point drivers and equal-points sporting positions remain significant.

Failed reconciliation, missing population, integrity failure, unresolved ambiguity,
unsupported interpretation, unapproved provenance or source changes withhold valid
production results. Unavailable responses do not present champion, runner-up or
margin as valid. Completed calculations can retain diagnostic counts without
becoming available production results. Operational failures remain errors.

Independent external auditing is supplementary. **2010 alone** has the completed
independent historical audit and deep-validation summary, including its FIA
provisional-classification qualification. No equivalent audit is claimed for
2011?2013. Optional audit information is attached after canonical assessment;
missing, unreadable or invalid audit metadata cannot change normal-use trust.
The strict independent-evidence evaluator remains available for explicit audit
claims and retains its stricter evidence requirements.

The former requirement for independent external evidence before normal-use
production trust is superseded by the historical-data trust decision. Historical
records preserve that earlier policy rather than erasing it. Further historical
research is triggered by reconciliation failures, conflicting records, unsupported
interpretations or deliberately selected edge cases.

Snapshot updates require a separate review: establish release provenance, compare
schema and logical data, validate integrity, reconstruct all supported seasons,
review differences, approve the manifest, then activate the new standalone file
with readers stopped and a known-good rollback available. Ordinary data rotation
must not require historical scoring exceptions. External-audit bindings remain
attached to the snapshot actually audited; they do not transfer automatically.

Future automation may discover and validate releases in GitHub Actions and propose
an update PR. It must not download source data during an application request or
approve a snapshot solely because regression tests pass. Automation is deferred.
The local `data/f1db_newsnapshot.db` remains an ignored acceptance-test copy.
Its bytes were verified against the official `v2026.16.0` SQLite release and
approved for canonical use on 2026-10-05; the canonical copy is `data/f1db.db`. The
2010 audit summary retains its previous `v2026.15.0` binding and is not attached
to current-snapshot results. The historical-data trust record preserves both approvals.

## Architecture

The target stack is React, TypeScript, Vite and Plotly.js for presentation;
Python and FastAPI for services and analytics; and SQLite for source data.
Use pandas where appropriate to analysis, without making it a requirement for
exact championship mathematics. Tests use pytest, Vitest and React Testing Library.

The dependency flow is:

`F1DB ? repository ? domain models ? analytics ? application service ? FastAPI ? React`

SQL and schema adaptation belong in the repository. Analytics consumes typed
source facts without database or presentation concerns. Python is the source of
truth for scoring; the frontend visualises supplied results and manages interaction
state. Preserve the useful prototype and repository history while implementing
incrementally. Prefer simple, typed, domain-oriented code and project-local
pinned dependencies. Infrastructure requires a demonstrated need; SQLite remains
sufficient for the current scope.

Assessment images are temporary in-memory data, not persistent databases or a
versioning subsystem. Their memory cost scales with the source file and concurrent
assessments; deployment capacity must account for it before increasing concurrency.

## Historical scoring and counterfactual analysis

V1's broader goal is to apply recognised historical scoring packages to recorded
results. Original scoring remains available alongside explicitly supported packages.
Custom points-entry forms and arbitrary hybrid rules are outside V1.

Counterfactual rescoring preserves recorded race outcomes. It does not simulate
changed driver behaviour, strategy or incentives. Keep recorded Original standings,
reconstructed Original results and counterfactual outputs distinctly labelled.

Milestone 1A governs result eligibility, dropped results, shared drives, fastest-lap
points, shortened/partial-points events, double-points events, sprints, constructor
rules, exclusions and sanctions. Unsupported provisions must not be approximated.
When a package excludes sprint scoring, disclose that exclusion and test it.

Use the approved countback rules for equal totals: wins, then second places, then
subsequent finishing positions. An unresolved sporting tie remains unavailable;
database order, driver ID and display order are not sporting tie-breakers.

Preserve all constructor contributions to a driver's counted championship points.
Multiple valid counted-result allocations or unallocated adjustments remain explicit.
Historical interpretation and expected outputs require defensible source data;
an implementation disagreement is a reason to investigate rules, queries and
expectations, not to patch the historical database.

## Historical identity and visual attribution

Milestone 1B is authoritative. Constructor make/episode, entrant, championship
entry, racing operation, legal organisation, owner, commercial brand, engine make,
works relationship and chassis specification are separate concepts. Shared names,
constructor IDs, ownership or succession do not automatically establish equivalence.

For a multi-constructor driver-season, preserve every counted contribution. The
stable chart-colour anchor is the greatest **reconstructed Original counted
constructor contribution** for that driver, a project visual convention rather
than an official primary-constructor designation. Tied, ambiguous or unavailable
contributions retain multiple/unresolved attribution. Changing the selected scoring
package does not recolour that historical anchor; expose the package-dependent
contribution leader separately.

Teammates are a pairwise, dated relationship requiring the same racing operation
and verified concurrent GP participation in at least one round. Shared constructor
make alone is insufficient. A same-constructor teammate claim also requires the
same contemporary make during the overlap. Retain overlap extent and unresolved
states; pairwise overlap is not transitive. A P1/P2 teammate-title-battle indication,
possibly an outer ring, must remain separate from driver identity patterns.

Patterns use a versioned **driver + constructor-episode identity mapping** independent
of championships, wins, points and scoring package. The former provisional
championships ? wins ? points hierarchy is superseded as a pattern-assignment rule.
Performance may supply later contextual statistics, never the meaning of a pattern.
Exact motifs and collision/rendering policies remain presentation decisions.

Where event-level evidence supports it, primary driver chassis uses the greatest
number of verified GP race appearances; constructor primary chassis uses verified
GP car starts under its original historical participation scope. Ties are co-primary.
Season/entrant chassis associations alone cannot establish event usage or primary
chassis. Usage identity remains stable across scoring packages; scoring-dependent
chassis contribution is a separate analytical result.

Previously open multi-constructor attribution, teammate eligibility and pattern
assignment questions are resolved by Milestone 1B. Comprehensive identity curation,
event-level chassis evidence, full colour mappings and exact presentation remain
deferred. F1DB limitations must produce partial, ambiguous or unavailable claims.

Historical colours use curated contemporary constructor identity. Modern colours
require an explicitly supported contemporary mapping; organisational succession
must not silently recolour unrelated constructors. Historical colours are the
default, and colour selection never changes analytics.

## Range navigation and season status

Era presets and the season slider are bidirectionally linked. Selecting a preset
sets its bounds; changing a bound away from an exact preset yields Custom; returning
to an exact range restores the preset. Selecting Custom preserves the current range.
All F1 covers available supported history. Technical/popular era candidates include
Classic, Ground Effect, Turbo, Naturally Aspirated, V10, V8, Turbo-Hybrid and later
regulation eras. Exact boundaries require a documented future decision; overlapping
navigation ranges are acceptable.

Model upcoming, in-progress, title-clinched and completed states explicitly where
implemented. Calendar year alone cannot establish season status. In-progress data
uses Championship Leader and Current P2, with the latest completed round and source
version. Title clinched remains distinct from season completed. Counterfactual
rescoring retains provisional status, and active seasons are excluded from
historical averages. A future provisional marker treatment must preserve colour
and driver-pattern meanings. Active-season production support is currently deferred.

## Delivery roadmap and quality

Develop one reviewed milestone at a time. Preserve existing decision history and
complete the current scope before expanding it. Changes should describe their
purpose, files, validation and limitations for contributor review. Commits should
be coherent and descriptive, such as `feat(analytics): add championship margin`
or `test(rescoring): cover countback ambiguity`. Source rotation is a distinct
reviewed change with provenance and rollback documentation.

The next coverage expansion should validate the shared historical domain and
unavailable states before presenting broader results. Subsequent work includes
identity/colour curation, approved scoring packages, Constructors mode, broader
historical coverage, provisional-season handling and controlled update automation.
Representative future regression cases include early/shared-drive/dropped-result
eras, 1988, 2007, 2014 and 2021. These are test-planning candidates, not assertions
of completed research or implemented support.

V2 may add driver or constructor history, pairwise career comparisons, selected-season
comparisons and trend views. Custom scoring, career rankings, unrelated dashboards
and a weighted universal GOAT/dominance score remain outside V1. Contextual metrics
may enrich interpretation without an arbitrary composite score.

Critical analytics, historical edge cases, exact margins, population completeness,
countback, provenance, integrity failures and unsupported states need meaningful
regressions. Frontend tests cover interaction/state and fail-closed rendering.
Fixtures must be grounded in reviewed policy and validated data, not copied blindly
from calculation output. Source files remain immutable during tests.

## Windows development

Use Windows PowerShell, VS Code, Git, Python 3.11+ and Node.js 26.x with npm.
Use the project's `.venv` and frontend-local dependencies rather than global installs.
The pinned backend and frontend manifests are the dependency authority.

From the repository root:

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -e './backend[test]'
npm.cmd --prefix frontend ci
& .\.venv\Scripts\python.exe -m pytest -c backend/pyproject.toml
npm.cmd --prefix frontend test
npm.cmd --prefix frontend run build
$env:PYTHONPATH = 'backend/src'
& .\.venv\Scripts\python.exe -m uvicorn f1_eras.api.http:create_default_app --factory
```

Use `npm.cmd` in PowerShell when execution policy blocks the `npm.ps1` shim.
Run the frontend in a separate terminal with `npm.cmd --prefix frontend run dev`.
See [backend/README.md](../../backend/README.md) and [frontend/README.md](../../frontend/README.md)
for current endpoints, setup and development details. `F1_ERAS_DB_PATH` selects an
explicit read-only source for local testing; it does not approve that source.

The project uses AI-assisted engineering with human-led product direction,
historical methodology, architectural decisions and validation. Contributor-facing
documentation should describe implementation and evidence accurately, including
limitations, without implying independent historical audits that did not occur.
