# F1 ERAs backend — repository and Original Drivers calculation

Task 1 introduced source access beside the existing Streamlit prototype. Task 2
adds pure Original Drivers calculations for 2010–2013:

```text
immutable F1DB → data_access → typed source/domain records
                              → analytics → service/API → frontend (later tasks)
```

The supported Original Drivers package set is **2010, 2011, 2012, 2013**.
Repository readers can inspect any stored year; the analytics layer returns an
explicit unavailable result for unsupported seasons and Constructor calculation.

## Environment and tests

Runtime code uses only the Python standard library (Python 3.11+ syntax/APIs;
the current workstation uses Python 3.14.7). The only Task 1 test dependency is
`pytest==9.1.1`. Installation requires the product owner's approval.

From the repository root, after that approval:

```powershell
& .\.venv\Scripts\python.exe -m pip install "pytest==9.1.1"
& .\.venv\Scripts\python.exe -B -m pytest -c backend/pyproject.toml backend/tests -q -p no:cacheprovider
```

No editable package installation is needed for these tests: pytest's configuration
adds `backend/src` to the import path. `setuptools` in the build configuration is
only needed if the backend is packaged/installed later; the commands above do not
build or install the backend package.

All tests run by default, including read-only integration tests against the tracked
`f1db.db`. To run only synthetic fixtures, append `-m "not integration"`.
Synthetic tests create and modify SQLite files only in pytest's temporary directory.
Write-rejection tests never attempt writes against the tracked source database.

## Using the repository

Supply an explicit path; imports never open a database or start the prototype.
For a standard-library diagnostic from the repository root:

```powershell
@'
from pathlib import Path
import sys
sys.path.insert(0, str(Path("backend/src").resolve()))
from f1_eras.data_access.f1db import F1DBRepository

repository = F1DBRepository(Path("f1db.db"))
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
`name=None`; it does not drop the source row or invent a replacement. Season entrant
associations are not used to determine event constructors, operations or teammates.

Classification text is retained verbatim, including unknown codes. Optional awards,
shared-car flags, laps, retirement reasons, fastest-lap flags and recorded race time
penalties remain source facts. `None`, zero and false are distinct. Recorded
standings, including unranked/excluded records and championship-won flags, are not
reinterpreted as reconstructed results or proof of season completion.

Recorded numeric values are selected as SQLite text and represented with `Decimal`,
without conversion through Python floats. This preserves the database's numeric
representation; it does **not** recover exact historical fractions already rounded
or stored as SQLite REAL values. Exact scoring arithmetic belongs to the later
analytics layer. Scheduled laps/distances may be absent and are never filled from
actual values. Event presence does not establish that a race was held or completed.

## Connection, schema and provenance

`data_access/connection.py` opens an existing standalone snapshot using an escaped
file URI with `mode=ro&immutable=1`, sets `query_only=ON`, and closes the connection
on success or failure. Missing paths fail without creating files. Nonempty WAL or
journal sidecars are rejected because the source and its content hash must describe
one standalone file. The source must remain unchanged throughout repository use;
live updates/concurrent replacement are outside Task 1.

`data_access/f1db.py` contains parameterized reader queries and schema checks.
Required tables, consumed column affinities/non-nullability, and source primary
keys are validated at construction and before each read. Unrelated tables, indexes
and columns are allowed. Schema errors explain the missing or incompatible fields.

`identify_snapshot()` returns SHA-256, byte size and explicitly named SQLite schema
and user-version counters. Neither counter is an F1DB release version.
`upstream_release=None` means release provenance has not been verified. The current
audited snapshot SHA-256 is:

```text
6249c3d8e361b5358981a1dfba6a34218a471af35b5f3ab6d6deb19638ac5a71
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
and resolution condition. This task does not implement counterfactual scoring,
identity presentation, an API, or frontend.

The Milestone 1A/1B records remain authoritative as coverage expands.
