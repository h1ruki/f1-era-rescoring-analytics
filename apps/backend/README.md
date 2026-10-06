# F1 ERAs backend — repository and Original Drivers calculation

The active backend provides source access, pure Original Drivers reconstruction
for 2010–2013, and a read-only service with a versioned FastAPI interface.
The React frontend renders its results; the original Streamlit code is archived.
This is the implemented foundation for v1's historical champion-versus-runner-up
comparison. The [roadmap](../../docs/README.md) owns product scope and milestone status;
the [master brief](../../docs/architecture/F1_ERAs_MASTER_BRIEF.md#v1-visible-analytical-contract)
owns the visible analytical contract.

```text
immutable F1DB → data_access → typed source/domain records
                              → analytics → service/API → React frontend
```

The supported Original Drivers package set is **2010, 2011, 2012, 2013**.
Repository readers can inspect any stored year; the analytics layer returns an
explicit unavailable result for unsupported seasons and Constructor calculation.

## Environment and tests

Follow [Development Setup](../../SETUP.md) for prerequisites, installation, startup
and verification on each OS. The component commands below assume that setup is complete.

Analytics and data access use the Python standard library. The API uses FastAPI
and Uvicorn; tests use pytest and httpx, with Ruff for lint. Python requirements and
direct dependency versions are declared in [pyproject.toml](pyproject.toml).

From the repository root:

```powershell
& .\.venv\Scripts\python.exe -B -m pytest -c apps/backend/pyproject.toml apps/backend/tests -q -p no:cacheprovider
```

Pytest adds `apps/backend/src` to its import path.

All tests run by default, including read-only integration tests against the tracked
`data/f1db.db`. To run only synthetic fixtures, append `-m "not integration"`.
Synthetic tests create and modify SQLite files only in pytest's temporary directory.
Write-rejection tests never attempt writes against the tracked source database.

## Champion teammate context

This section describes current entrant-based implementation behavior, including
its primary/additional selection; that ranking is not normative v1 methodology.
[Milestone 1B's final contract](../../docs/decisions/MILESTONE_1B_DECISION_RECORD.md#teammate-eligibility-and-grouping)
retains all drivers who shared a championship event with the champion in the same
racing operation/team, using normalized identity and participation/entry evidence
with canonical reconciliation for historical exceptions. **Teammate battle** means
runner-up membership in that season set, including partial-season overlap.
[Milestone 2](../../docs/decisions/MILESTONE_2_DECISION_RECORD.md) must align the API
with that contract and complete historical coverage; the current enrichment does
not establish compliance. Teammate context never replaces the championship runner-up
or changes points/margins, and the frontend does not yet render it.

Drivers / Original remains limited to 2010–2013. Both championship detail and
margin summaries now include a stable `teammate_context` object:

```json
{
  "primary_selection": "unique",
  "primary_teammate": {
    "id": "mark-webber",
    "name": "Mark Webber",
    "official_final_position": 6,
    "official_final_points": {
      "exact": {"numerator": 179, "denominator": 1},
      "plot": 179.0
    },
    "final_standing_recorded": true,
    "shared_race_count": 20,
    "entrants": [{"id": "red-bull-racing", "name": "Red Bull Racing"}]
  },
  "additional_teammates": [],
  "tied_primary_candidate_ids": []
}
```

`primary_selection` is `unique`, `none`, or `unresolved_tie`. Unavailable
championships or unavailable teammate evidence use `unavailable`, not `none`.
A unique primary appears only in
`primary_teammate`; all other valid candidates appear individually in
`additional_teammates`. For unresolved ties, `primary_teammate` is null and all
candidates remain in `additional_teammates`; `tied_primary_candidate_ids`
identifies the remaining contenders without duplicating their records. Empty
lists are always included. Missing final standings produce null official points
and position plus `final_standing_recorded=false`. A recorded unranked standing
can retain its points and has `final_standing_recorded=true`.

`domain/models.py` preserves entrant assignments and their composite source keys,
raw and parsed round coverage, entrant/driver/constructor identities, and engine ID.
The unused `test_driver` field is neither read, validated nor included in these
models; no value is interpreted as teammate eligibility or race participation.
Assignment reads use the same captured read-only SQLite
image as the calendar, results and final standings. `domain/teammates.py` retains
all candidates, official standing source keys/classification text, explicit
primary selection, and per-race entrant, assignment and result-key evidence.
HTTP omits the detailed race evidence.

Teammate acquisition is optional: entrant-specific schema validation and SQL reads
have a separate failure boundary after mandatory source reads. Acquisition errors
set `entrant_assignments=null` and retain an internal `teammate_source_error`.
Round parsing errors are retained on individual assignments as
`round_coverage_error`, with unknown parsed coverage and the raw metadata preserved.
This allows unrelated entrants' malformed round data to remain irrelevant.
Integer-conversion failures, including oversized ASCII numeric tokens, are
normalized to source errors without application-defined numeric limits.
Mandatory schema, source integrity, calendar/results/standings and snapshot checks
retain their existing behavior.
The service catches only `TeammateDerivationAmbiguity` from teammate derivation.
These enrichment failures produce `primary_selection="unavailable"`, null primary
and empty additional/tie lists while the valid championship, trust and
reconciliation survive. Unexpected programming errors are not swallowed.

`analytics/teammates.py` starts with the champion's recorded entrant assignments
by round, finds other drivers assigned to the same entrant at overlapping rounds,
then checks both drivers' `RACE_RESULT` participation. The entrant roster defines
the possible teammate population; unrelated participants are not attributed or
validated. Constructor and engine IDs are retained as equipment evidence only:
same-entrant teammates may have different equipment, and equipment equality never
creates teammate identity.

Only relevant uncertainty makes enrichment unavailable: missing/unknown champion
coverage at a race they participated in, unknown candidate coverage that could
overlap that entrant, unknown participation during possible overlap, or competing
entrant assignments for that relevant driver/round. Known assignments outside
shared rounds remain excluded, as do results under another established entrant.
Drivers entirely outside the champion's entrant roster, their coverage errors and
their multiple entrant assignments do not invalidate context. Non-participating
results and events without champion participation create no overlap.

The source primary key permits one driver to have multiple entrant assignments
for the same round; read-only inspection found 53 historical driver/round cases
and none in 2010–2013. Race results have no direct entrant ID. Relevant simultaneous
assignments to different entrants therefore remain ambiguous; equipment matching
is not used to invent an entrant winner. Multiple assignments to the same entrant
retain contextual evidence without multiplying races. Shared races count distinct
race IDs, including repeated/shared-drive rows. Primary
selection uses greatest shared-race count, then better official final championship
position. Missing/ambiguous classifications or identical best positions retain
an unresolved tie. Driver IDs only order output; they never break selection ties.
Points always come from official season standings, never the shared-race subset.

Before implementation the canonical result states and assignment format were
inspected through read-only SQL. The 2010–2013 result states are numeric finishes,
DNF, NC, DNS, DNQ and DSQ. Numeric finishes consistent with the recorded position,
DNF and NC establish participation. Zero-lap DNFs include first-lap collisions
and still count. DNS/DNQ/DNPQ do not count. DSQ requires positive recorded race
laps to establish participation independently of the exclusion; both current-slice
DSQ rows have 58 laps. DSQ without that evidence, EX, DNP and unknown states are
left uninterpreted and raise `TeammateDerivationAmbiguity` when relevant. Unknown
round coverage or multiple possible entrants for a result likewise raise a
derivation error, converted by the service to unavailable enrichment.
No withdrawal-specific state occurs in the inspected database;
unrecognized future states require review rather than an inferred meaning.
Round IDs are the inspected semicolon-delimited `rounds` field, not parsed display
ranges. Null coverage remains unknown; empty coverage remains empty.

The current slice yields only Mark Webber: 242/258/179/199 official points,
positions 3/3/6/3, and 19/19/20/19 shared races for 2010/2011/2012/2013. Fixture
tests cover additional candidates, ties, team switches, multiple entrants and
constructors, repeated results, and missing standings without adding production
seasons. Shared-drive championship scoring remains unsupported by the existing
reconstruction/trust gates. Championship calculations and trust policy are unchanged.

## Using the repository

Supply an explicit path; imports never open a database or start the prototype.
For a standard-library diagnostic from the repository root:

```powershell
@'
from pathlib import Path
import sys
sys.path.insert(0, str(Path("apps/backend/src").resolve()))
from f1_eras.data_access.f1db import F1DBRepository

repository = F1DBRepository(Path("data/f1db.db"))
print(repository.identify_snapshot())
print(len(repository.get_season_events(2012)))
print(len(repository.get_gp_classifications(2012)))
print(len(repository.get_recorded_driver_standings(2012)))
'@ | & .\.venv\Scripts\python.exe -B -
```

Readers return tuples of frozen dataclasses, including frozen nested identities
and composite source keys. Events retain `race.id`; GP classifications retain
`(race_id, type, position_display_order)`; driver standings retain
`(year, position_display_order)`. Display order is a source key/order, not a
calculated championship ranking. Multiple records for one event/driver are retained.

GP classifications explicitly select `RACE_RESULT` and enrich names through direct
driver/constructor ID joins. A missing identity lookup preserves its ID and returns
`name=None`; it does not drop the source row or invent a replacement. Event
constructors remain direct result facts; season entrant assignments independently
supply the roster and round coverage for teammate derivation.

Classification text is retained verbatim, including unknown codes. Optional awards,
shared-car flags, laps, retirement reasons, fastest-lap flags and recorded race time
penalties remain source facts. `None`, zero and false are distinct. Recorded
standings, including unranked/excluded records and championship-won flags, are not
reinterpreted as reconstructed results or proof of season completion.

Recorded numeric values are selected as SQLite text and represented with `Decimal`,
without conversion through Python floats. This preserves the database's numeric
representation; it does **not** recover exact historical fractions already rounded
or stored as SQLite REAL values. Exact scoring arithmetic belongs to the
analytics layer. Scheduled laps/distances may be absent and are never filled from
actual values. Event presence does not establish that a race was held or completed.

## Connection, schema and provenance

`data_access/connection.py` opens an existing standalone snapshot using an escaped
file URI with `mode=ro&immutable=1`, sets `query_only=ON`, and closes the connection
on success or failure. Missing paths fail without creating files. Nonempty WAL or
journal sidecars are rejected because the source and its content hash must describe
one standalone file. The source must remain unchanged throughout repository use;
source snapshots are standalone files; assessment reads use a bound image.

`data_access/f1db.py` contains parameterized reader queries and schema checks.
Required tables, consumed column affinities/non-nullability, and source primary
keys for mandatory championship inputs are validated at construction and before
each read; teammate-specific schema is validated when assignments are read.
Unrelated tables, indexes
and columns are allowed. Schema errors explain the missing or incompatible fields.

`identify_snapshot()` returns SHA-256, byte size and explicitly named SQLite schema
and user-version counters. Neither counter is an F1DB release version.
The reader's `upstream_release=None` means it does not infer an F1DB release from
SQLite counters. The authoritative approval manifest identifies the current
snapshot as upstream `v2026.16.0`, release commit
`2ba943cf908ace7d6b606e12b72472f54d442a12`, published 2026-10-04 at 12:21:35 UTC.
Its SHA-256 is:

```text
28707a41bc45d9d4b787d655ef7e135644bdc9cb3307a947258647d83ecba642
```

Integration tests intentionally check this snapshot and audited source row counts.
These are source-access checks, not golden championship outputs. Any later dataset
update needs its own approved validation and provenance review.

## Original Drivers calculation

`f1_eras.analytics.original_drivers.calculate_original_drivers` accepts the
repository's immutable event, final GP classification, and recorded standing
tuples. It has no database access. Each source year retains its own package
identity. These four packages use 25–18–15–12–10–8–6–4–2–1 points, count all
held GP results, and rank equal totals by counts of 1st places, then 2nd places,
and so on through all classified finishing positions. No sprint or fastest-lap
points apply. The source's final amended classification is scored directly;
recorded penalties are not reapplied.

Award, total, constructor-contribution, raw-gap, and percentage-gap arithmetic
uses `fractions.Fraction`. Constructor contribution is each driver's counted
Original points grouped by the constructor on the GP classification, not a
calculated Constructors' Championship. Recorded event awards and final Driver
standings remain separate comparison records. The result exposes differences
from both sources; all four curated seasons currently reconcile with no
differences. Unresolved countback, missing final GP classifications, unsupported
years, and Constructor category return `CalculationUnavailable` with a reason
and resolution condition. Counterfactual scoring, general historical rule packages
and historical identity presentation remain unimplemented; supporting constructor
contributions and teammate API context do exist. The active frontend lives in `apps/frontend/`.

## Read-only service and API

`ChampionshipService` invokes the repository and existing pure analytics. It
returns a typed report with the result or explicit unavailable reason, package
rules, source snapshot identity, and canonical trust assessment. The same generic
trust gate serves every supported season: pinned immutable F1DB, passing integrity
checks, and exact full championship reconciliation. Failed trust withholds results
as unavailable with null champion/runner-up/margin; operational failures remain
server errors. Snapshot identity is checked before reads and after reconstruction.
Unsupported seasons and the unimplemented
Constructor category do not invoke source readers. API imports do not open the
database; the Uvicorn factory constructs the repository from the local `data/f1db.db`
or the explicit `F1_ERAS_DB_PATH` environment variable.

Use the startup commands in [SETUP.md](../../SETUP.md#running-the-project).

The versioned GET endpoints are:

- `/api/v1/capabilities`: curated seasons, supported category, package identities,
  calculation version and implemented rule summaries.
- `/api/v1/championship-margins`: defaults to all four seasons; repeat the
  `seasons` query parameter to select years, e.g.
  `?seasons=2010&seasons=2012`. Results are chronological.
- `/api/v1/championships/{season}`: the same P1/P2 summary plus calculated
  standings, separate recorded standings, event awards, source record keys, and
  reconciliation differences.

Both championship routes accept `category=drivers|constructors` and only
`scoring=original`. Invalid parameters receive HTTP 422. Valid unsupported years
and the Constructor category receive HTTP 200 with `availability=unavailable`,
reason and resolution; their champion and margin are null. Source failures remain
server errors.

Authoritative numeric fields use `{ "exact": { "numerator": n, "denominator": d },
"plot": number }`. The `plot` value is a floating-point projection for charts;
calculation and reconciliation use exact fractions. The response supplies P1/P2
totals, raw gap, and Championship Margin (%) directly, so a frontend does not
need to calculate them. The rules include the margin formula. Provenance includes
the F1DB snapshot SHA-256 and source record keys in detail responses. Regulatory
source citations are not yet part of these four package records.

The Milestone 1A/1B records remain authoritative as coverage expands.

## Canonical trust and supplementary external verification

The approved [verification decision record](../../docs/decisions/VERIFICATION_FOUNDATION_DECISION_RECORD.md)
preserves the original foundation and records its supersession by
[historical-data trust policy](../../docs/decisions/HISTORICAL_DATA_TRUST_DECISION_RECORD.md).
`domain/verification.py` contains typed assessments and context;
`verification/metadata.py` strictly loads JSON evidence;
`verification/compare.py` compares complete standings with exact fractions;
`verification/evaluate.py` retains strict independent-audit evaluation.
`verification/canonical.py` supplies the generic normal-use trust adapter used by
the service/API and diagnostic, reusing exact comparison and typed findings.
Integrity checks bind the award trace to source rows and supported rules, validate
calendar/results keys and populations, reject unknown/unsupported classification
and participation states, and reconcile contributions, countback and margins.
Canonical standings are compared across the full driver population, exact points,
sporting positions/classifications and championship-won consistency.

The API's `trust` object separately reports `canonical_dataset_backed`,
`comparison`, `state`, `findings`, derived `trusted_for_normal_use`, dataset/rules
hashes, calculation/policy versions, and nullable `external_audit`. Unsupported
requests without a reconstruction have `trust=null`. Independent evidence absence
is not a gate. Normal-use trust requires `passed`, a completed reconstruction and
canonical comparison `match`; changed snapshots are `stale`. Strict external
verification remains a distinct `historically_verified` claim from the original
evaluator. Synthetic success cannot grant historical trust.

2010 has supplementary completed-audit summary metadata attributed to the approved
decision record, including the FIA provisional-classification qualification.
That summary retains its `v2026.15.0` snapshot binding. After rotation to
`v2026.16.0`, current responses have no matching external audit, including 2010;
normal canonical trust remains available for all four seasons.
2011-2013 have no external-audit metadata; all four use identical trust logic.
No complete machine-verification historical dossier has been populated; the summary
does not claim a new strict evaluator pass. Unknown claim-level upstream F1DB
lineage is non-blocking. [Metadata documentation](historical/README.md) describes
both representations. New primary-source research is exception handling only.

Run the fixed 2010-2013 diagnostic from the repository root:

```powershell
& .\.venv\Scripts\python.exe -B -m f1_eras.verification.diagnostic
```

It prints JSON with the same canonical trust assessment as production, reconstruction
outcome, findings, supplementary audit summary, F1DB difference counts, and Git
identity/dirty status. All four pinned-snapshot seasons should pass normal-use
trust. Dirty Git state is information for this path; the strict independent evaluator
still requires a clean known commit. Exit 0 means the diagnostic completed, so
inspect each assessment for trust; operational errors exit nonzero.
`--db PATH` selects another read-only snapshot without changing the fixed year set.

The complete backend pytest command above includes the synthetic policy,
schema and comparator tests and the four-season diagnostic integration test.
The only example fixture is explicitly synthetic under `tests/fixtures/synthetic`.

## Bound assessment and snapshot approval

`historical/canonical_snapshot.json` is the machine-readable runtime approval
source of truth (upstream release/commit, SHA-256 and size). Documentation records
provenance but cannot grant runtime approval. Missing, unreadable or invalid
approval fails closed; tests load the same approval mechanism.

`read_original_drivers_source(year)` captures database bytes once, hashes those
exact bytes, validates schema and SQLite integrity, and queries a temporary
in-memory SQLite image. Calendar, GP classifications, comparison standings and an
independently queried unfiltered championship driver population use that image.
The adapter requires full population coverage, including ranked zero-point drivers,
plus exact points and sporting ordering. Matching truncated inputs cannot pass.
Source changes detected at capture or final identification are stale. Database or
operational failures remain errors. Captured images prevent A/B/A path replacements
from silently labelling B's input as approved A; no source file is rewritten.
The request-local image costs roughly one database's size plus capture overhead;
concurrent deployment capacity must account for that memory use.

Canonical assessment does not read `external_audit_summaries.json`. Separate
post-assessment enrichment attaches context-matching audit information and
`external_audit_status` (`available`, `unavailable`, `invalid`). Missing, unreadable,
malformed or invalid supplementary metadata cannot withhold valid canonical results
or promote rejected ones. This isolation does not catch canonical source errors.

The service preserves calculation counts separately from production availability.
Diagnostics retain driver/award counts and known reconciliation difference counts
for completed-but-rejected calculations; counts are null when calculation did not
complete. Rejected API results still have null champion, runner-up and margin.

For rotation: validate a separate candidate's provenance, schema, integrity and
full supported historical inputs/results; review differences; formally approve the
manifest; activate the standalone database with readers stopped and retain rollback.
Update approval-dependent tests and documentation without altering historical
scoring logic. Preserve historical audit bindings; they never transfer automatically.
`v2026.16.0` was approved on 2026-10-05 after official-asset byte comparison and
unchanged 2010-2013 input/reconciliation checks. The previous `v2026.15.0` snapshot
is retained in Git history. `data/f1db_newsnapshot.db` is an ignored path for an
optional local acceptance-test copy, not a required file in a fresh checkout.
