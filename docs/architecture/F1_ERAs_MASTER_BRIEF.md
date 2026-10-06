# F1 ERAs — Master Engineering Brief

F1 ERAs provides historical Formula 1 dominance analytics. Its central question
is: “How dominant was each F1 champion in their title-winning season?” Compare
every championship season in Formula 1 history by the gap between the champion
and runner-up. Championship margin is an analytical measure, not a complete
measure of driver ability or dominance.

This brief is authoritative for architecture, the visible analytical contract and
presentation direction. The [documentation roadmap and release policy](../README.md#product-versions-and-release-policy)
define the major-version scope: v1 Drivers / Historical Reality, v2 What If,
and v3 Constructors. Requirements below span those versions and do not imply
implemented support or inclusion in v1. Milestones are internal development stages;
the [milestone assessment](../README.md#milestone-status) records partial Milestone 1
completion and [Milestone 2](../decisions/MILESTONE_2_DECISION_RECORD.md) defines the
next integration stage within v1.

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

The implemented calculation/API scope is **2010–2013 Drivers / Original**.
Other seasons, Constructors calculations and counterfactual packages remain
unavailable until their rules and implementation are approved and validated.
Broader historical coverage is a product goal, not a current capability claim.

| Area | Implemented now | Target or remaining work |
| --- | --- | --- |
| Analytics and trust | Four Original Drivers packages, exact standings/margins, complete canonical reconciliation, source approval and integrity gate | Full-history Original rules and exception coverage for v1; transplantation for v2 |
| API and context | Capabilities, summaries/details, constructor contributions and entrant-based champion teammate enrichment | Context presentation, nationality, historical colours and alignment with 1B's approved season teammate set contract |
| Frontend | Chronological lollipop chart, points/% toggle, P1/P2 hover, season list, loading/error/retry and unavailable states | Range/era navigation, pinned detail, historical identity/context and release UX validation |

The current frontend does not consume the API's teammate/trust metadata or detail
route; the backend enforces availability. Generic chart colours are not curated team
colours. A disabled Constructors control is a PoC placeholder, not v1 feature scope.

The initial repository/data audit is complete. Its former audit-only instructions
are retired. The prototype and decision records retain historical context;
subsequent development follows the approved architecture and milestone decisions.

## Product and analytical experience

Product name: **F1 ERAs**. Descriptor: **Historical Formula 1 dominance analytics**.

The v1 headline comparison is the Drivers' champion versus runner-up. Teammate,
team, competition and era context support that comparison. Constructor identity
is required internally where needed for teammate determination, team colours,
tooltips and historical identity; Constructors Championship analysis belongs to v3.
Keep the visible product simple; users need not learn the historical engine before
understanding the question. The following is target presentation direction, except
where the implementation table above explicitly says it exists.

The main experience is one interactive chronological lollipop chart comparing
championship P1 and P2. Drivers and Constructors modes should ultimately share
its interaction model. Each season is an independent observation with a meaningful
zero baseline; connecting markers with a line would imply interpolation.

The v1 target supports hover, pinned selection and a detail drawer, season-range
changes, approved era presets and margin metrics. Scoring-package selection belongs
to v2; Constructors mode belongs to v3. Historical colours support v1 context;
modern-colour mappings remain deferred. Full-history view is the v1 goal;
the current view must respect available calculation scope.

The default product state is Drivers, Championship Margin (%), Original scoring,
All F1 range and historical colours. V1 uses a restrained dark theme, designed
primarily for desktop analytical viewing with reasonable small-screen behaviour.
Avoid excessive gradients, decorative effects and motorsport clichés.

### v1 visible analytical contract

Champion (P1) and runner-up (P2) mean the first and second Drivers in the final
amended championship classification under that season's historical Original rules,
including counted-result limits, sanctions/exclusions and sporting tie-breaks where
applicable. The runner-up is not necessarily the champion's teammate. Reconstructed
results must reconcile with the complete canonical classification before publication;
they remain distinct from the recorded standings used for comparison.

The primary metric is:

`Championship Margin (%) = (P1 points - P2 points) / P1 points * 100`

Raw Points Gap is `P1 points - P2 points`. Percentage margin makes comparisons
less directly dependent on points inflation, but it does not remove differences
in rules, event populations or historical context. Exact calculation values govern
ranking and reconciliation; floats and rounding are display projections only.
An undefined denominator must not yield an invented valid margin.
Equal points resolved by the applicable sporting countback produce a zero points
gap and zero percentage gap, not an invented positive margin; explain the resolution.
Unresolved ranking or unavailable calculation is not a zero gap. Display rounding
never selects the champion or runner-up. Once v1 ships, these visible meanings are
stable under the roadmap's release policy.

Constructor contributions/colours and teammate, nationality, competition and era
context explain this comparison; they are not alternative scoring inputs.
Follow [1B's F1-record nationality principle](../decisions/MILESTONE_1B_DECISION_RECORD.md#driver-country-and-nationality).
Follow [1B's approved season teammate set](../decisions/MILESTONE_1B_DECISION_RECORD.md#teammate-eligibility-and-grouping).
**Teammate battle: Yes** means the championship runner-up belongs to the champion's
season teammate set; otherwise **No**. Any qualifying shared championship event
counts, including partial-season overlap. Unavailable evidence remains explicit.

Hover should give concise season, P1/P2, constructor attribution, points, gap,
active scoring package and relevant historical context. The drawer may expose
countback, event awards, constructor contributions, supported teammate status and
source provenance needed to explain the title result. Other statistics are optional
context only where they materially aid that explanation, not a generic dashboard
commitment. Constructors Championship analytics remains v3. Unsupported contextual
fields remain explicitly unavailable.

A historical average line uses only completed, available seasons in the selected
mode, metric, scoring package and range. Recalculate it when those selections
change. Omit it when no eligible observations exist. Scoring-change annotations
should be subtle and may be deemphasised when a single counterfactual package
replaces Original rules throughout the range.

## Source data, trust and snapshot rotation

F1DB is the canonical historical dataset. Application code treats `data/f1db.db` as
immutable source data and must never alter its records to satisfy a test.

[apps/backend/historical/canonical_snapshot.json](../../apps/backend/historical/canonical_snapshot.json)
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
2011–2013. Optional audit information is attached after canonical assessment;
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
The ignored acceptance-test path `data/f1db_newsnapshot.db` is optional local work,
not a required checkout file. The candidate bytes were verified against the official
`v2026.16.0` SQLite release and approved for canonical use on 2026-10-05;
the canonical copy is `data/f1db.db`. The
2010 audit summary retains its previous `v2026.15.0` binding and is not attached
to current-snapshot results. The historical-data trust record preserves both approvals.

## Architecture

The implemented stack is React, TypeScript, Vite and Plotly.js for presentation;
Python and FastAPI for services and analytics; and SQLite for source data.
Current analytics/data access use the Python standard library, including Fraction
for exact championship mathematics; pandas is not an active dependency.
Tests use pytest, Vitest and React Testing Library. The dependency manifests and
frontend lockfile own tool versions, and SETUP.md owns workstation requirements.

The dependency flow is:

`F1DB → repository → domain models → analytics → application service → FastAPI → React`

The application service invokes canonical verification before publishing results
and attaches optional teammate/external-audit context separately. Verification is
not a frontend responsibility. Source approval and supporting audit metadata live
under `apps/backend/historical/`; tests live alongside each application.

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

V1 covers Drivers / Historical Reality under each season's Original rules.
Alternative scoring systems and counterfactual rescoring belong to v2 — What If.
The retained rescoring methodology and shared analytical foundation support that
future work; a general transplantation engine is not yet implemented in the active
backend. Keep v2 work isolated from the released v1 experience until v2.0.
Custom points-entry forms and arbitrary hybrid rules are outside v1.

Counterfactual rescoring preserves recorded race outcomes. It does not simulate
changed driver behaviour, strategy or incentives. Keep recorded Original standings,
reconstructed Original results and counterfactual outputs distinctly labelled.

Milestone 1A governs result eligibility, dropped results, shared drives, fastest-lap
points, shortened/partial-points events, double-points events, sprints, constructor
rules, exclusions and sanctions. Unsupported provisions must not be approximated.
When a package excludes sprint scoring, disclose that exclusion and test it.

Use each supported season's applicable countback rules. The implemented 2010–2013
packages use wins, then second places, then subsequent finishing positions; this
is not an assertion that every historical package uses an identical rule.
An unresolved sporting tie remains unavailable;
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

The champion's season teammate set retains every driver who shared at least one
championship event with the champion in the same racing operation/team. Establish
pairwise event-level relationships normally from normalized entrant/team identity
and participation/entry evidence, then aggregate all qualifying relationships.
Use canonical historical reconciliation/overrides where raw identifiers do not
capture the operation; exhaustive manual verification is not the default. Raw
entrant equality and shared constructor name alone do not define teammates.
Retain identities, shared events/rounds, overlap context and unresolved states,
including substitutions and seat changes, without selecting or ranking a primary
teammate. Pairwise overlap is not transitive. The runner-up membership indicator
must remain separate from driver identity patterns.

Patterns use a versioned **driver + constructor-episode identity mapping** independent
of championships, wins, points and scoring package. The former provisional
championships → wins → points hierarchy is superseded as a pattern-assignment rule.
Performance may supply later contextual statistics, never the meaning of a pattern.
Exact motifs and collision/rendering policies remain presentation decisions.

Where event-level evidence supports it, primary driver chassis uses the greatest
number of verified GP race appearances; constructor primary chassis uses verified
GP car starts under its original historical participation scope. Ties are co-primary.
Season/entrant chassis associations alone cannot establish event usage or primary
chassis. Usage identity remains stable across scoring packages; scoring-dependent
chassis contribution is a separate analytical result.

Milestone 1B resolves multi-constructor attribution, pattern assignment and the
season teammate set contract. The later entrant-based API's primary/additional
selection and incomplete historical reconciliation remain Milestone 2 implementation
work; current output does not establish full-history methodology coverage.
Comprehensive identity curation, event-level chassis evidence, full colour mappings
and exact presentation remain
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

Develop reviewed slices against the [milestone plan](../README.md#milestone-status).
Preserve existing decision history and carry incomplete foundation dependencies
explicitly into integration work. Changes should describe their
purpose, files, validation and limitations for contributor review. Commits should
be coherent and descriptive, such as `feat(analytics): add championship margin`
or `test(rescoring): cover countback ambiguity`. Source rotation is a distinct
reviewed change with provenance and rollback documentation.

Milestone 2 joins remaining v1 Original coverage, supporting identity/colour context
and presentation/integration work. Validate the historical domain and unavailable
states before presenting broader results. Counterfactual packages belong to v2,
Constructors mode to v3; provisional-season support and update automation remain
deferred rather than prerequisites for the completed-season v1 comparison.
Representative future regression cases include early/shared-drive/dropped-result
eras, 1988, 2007, 2014 and 2021. These are test-planning candidates, not assertions
of completed research or implemented support.

The locked major-version roadmap is v1 Drivers / Historical Reality, v2 What If,
and v3 Constructors, as defined in the documentation roadmap. Earlier exploratory
ideas about career comparisons and trend views are not commitments in this roadmap. Custom
scoring, career rankings, unrelated dashboards and a weighted universal
GOAT/dominance score remain outside V1. Contextual metrics may enrich interpretation
without an arbitrary composite score.

Critical analytics, historical edge cases, exact margins, population completeness,
countback, provenance, integrity failures and unsupported states need meaningful
regressions. Frontend tests cover interaction/state and fail-closed rendering.
Fixtures must be grounded in reviewed policy and validated data, not copied blindly
from calculation output. Source files remain immutable during tests.

Current CI runs backend tests on Python 3.11 and 3.14, with lint and the historical
diagnostic, plus frontend tests/build and Bash syntax validation on Ubuntu with
Node 24. It runs for pushes to `development/v1`/`main` and pull requests targeting
`main`. This is not a browser end-to-end suite or Windows/macOS runtime validation.
See [.github/workflows/ci.yml](../../.github/workflows/ci.yml) for the executable checks.

## Development environment

Use Windows PowerShell, Git, Python 3.11+ and compatible Node.js/npm tooling.
VS Code is an optional editor; no AI tooling or subscription is required.
Use the project's `.venv` and frontend-local dependencies rather than global installs.
The pinned backend and frontend manifests are the dependency authority.
See [Development Setup](../../SETUP.md) for authoritative fresh-machine instructions,
prerequisite installation, environment preparation and troubleshooting.

See [apps/backend/README.md](../../apps/backend/README.md) and [apps/frontend/README.md](../../apps/frontend/README.md)
for current endpoints and development details. `F1_ERAS_DB_PATH` selects an
explicit read-only source for local testing; it does not approve that source.

The project uses AI-assisted engineering with human-led product direction,
historical methodology, architectural decisions and validation. Contributor-facing
documentation should describe implementation and evidence accurately, including
limitations, without implying independent historical audits that did not occur.
