from dataclasses import FrozenInstanceError
from contextlib import closing
from datetime import date
from decimal import Decimal
import hashlib
from pathlib import Path
import sqlite3

import pytest

from f1_eras.data_access.f1db import F1DBRepository, SourceSchemaError
from f1_eras.domain.models import (
    ChampionshipCategory,
    DriverStandingKey,
    GPClassificationKey,
    POC_CANDIDATE_SEASONS,
)


def test_events_preserve_calendar_and_optional_distance_facts(repository: F1DBRepository) -> None:
    events = repository.get_season_events(2012)
    assert isinstance(events, tuple)
    assert [event.race_id for event in events] == [10, 20]
    first, second = events
    assert first.date == date(2012, 3, 18)
    assert first.laps == 69 and first.scheduled_laps == 70
    assert first.distance == Decimal("302.249")
    assert first.scheduled_distance == Decimal("306.630")
    assert second.scheduled_laps is None and second.scheduled_distance is None
    assert second.sprint_race_date == date(2012, 3, 24)
    assert second.sprint_race_distance == Decimal("55.430")
    # Event 20 deliberately has no results: event presence is not completion.
    assert {row.source_key.race_id for row in repository.get_gp_classifications(2012)} == {10}


def test_gp_population_uses_only_gp_results_and_exact_source_keys(repository: F1DBRepository) -> None:
    rows = repository.get_gp_classifications(2012)
    assert len(rows) == 8
    assert [row.source_key for row in rows] == [
        GPClassificationKey(10, "RACE_RESULT", order) for order in range(1, 9)
    ]


def test_direct_constructor_attribution_preserves_repeated_driver_rows(repository: F1DBRepository) -> None:
    rows = repository.get_gp_classifications(2012)
    driver_rows = [row for row in rows if row.driver.id == "driver-a"]
    assert len(driver_rows) == 2
    assert [row.constructor.id for row in driver_rows] == ["constructor-a", "constructor-b"]
    assert [row.constructor.name for row in driver_rows] == ["Constructor A", "Constructor B"]
    assert [row.engine_manufacturer_id for row in driver_rows] == ["engine-a", "engine-b"]
    assert [row.driver_number for row in driver_rows] == ["007", "007"]


def test_optional_awards_shared_car_and_status_facts_are_not_inferred(repository: F1DBRepository) -> None:
    first, second, retired, excluded, *others = repository.get_gp_classifications(2012)
    assert first.recorded_points == Decimal("0.5") and first.shared_car is True
    assert second.recorded_points == Decimal("0") and second.shared_car is False
    assert retired.recorded_points is None and retired.shared_car is None
    assert retired.position_number is None and retired.position_text == "DNF"
    assert retired.reason_retired == "Engine" and retired.laps == 2
    assert excluded.position_number is None and excluded.position_text == "DSQ"
    assert [row.position_text for row in others] == ["DNS", "NC", "DNQ", "UNKN"]
    assert second.time_penalty == "20.000" and second.time_penalty_millis == 20000
    assert second.fastest_lap is True and retired.fastest_lap is None


def test_missing_identity_names_do_not_drop_source_records(repository: F1DBRepository) -> None:
    excluded = repository.get_gp_classifications(2012)[3]
    assert excluded.driver.id == "missing-driver" and excluded.driver.name is None
    assert excluded.constructor.id == "missing-constructor" and excluded.constructor.name is None


def test_recorded_standings_keep_display_order_exclusion_and_points(repository: F1DBRepository) -> None:
    first, excluded, last = repository.get_recorded_driver_standings(2012)
    assert first.source_key == DriverStandingKey(2012, 1)
    assert first.recorded_points == Decimal("5.5") and first.championship_won is True
    assert excluded.source_key == DriverStandingKey(2012, 2)
    assert excluded.position_number is None and excluded.position_text == "DSQ"
    assert excluded.recorded_points == Decimal("3") and excluded.driver.name is None
    assert last.position_number == 2 and last.recorded_points == Decimal("0")
    assert last.championship_won is False


def test_records_and_nested_identities_are_immutable(repository: F1DBRepository) -> None:
    row = repository.get_gp_classifications(2012)[0]
    with pytest.raises(FrozenInstanceError):
        row.position_text = "Edited"
    with pytest.raises(FrozenInstanceError):
        row.driver.name = "Edited"
    with pytest.raises(FrozenInstanceError):
        row.source_key.position_display_order = 999


@pytest.mark.parametrize("reader", [
    "get_season_events", "get_gp_classifications", "get_recorded_driver_standings",
])
def test_readers_filter_year_and_return_empty_for_absent_year(repository: F1DBRepository, reader: str) -> None:
    read = getattr(repository, reader)
    assert read(2050) == ()
    if reader == "get_gp_classifications":
        assert read(2013) == ()
    else:
        assert read(2013) != ()


@pytest.mark.parametrize("year", ["2012 OR 1=1", True, 2012.0, None])
@pytest.mark.parametrize("reader", [
    "get_season_events", "get_gp_classifications", "get_recorded_driver_standings",
])
def test_non_integer_years_are_rejected(repository: F1DBRepository, reader: str, year: object) -> None:
    with pytest.raises(TypeError, match="year must be an integer"):
        getattr(repository, reader)(year)


@pytest.mark.parametrize(("change", "message"), [
    ("DROP TABLE constructor", "missing table constructor"),
    ("ALTER TABLE race_data RENAME COLUMN race_shared_car TO obsolete_shared_car",
     "missing column race_data.race_shared_car"),
    ("ALTER TABLE driver RENAME TO old_driver; CREATE TABLE driver (id TEXT NOT NULL, name TEXT NOT NULL)",
     "unexpected primary key for driver"),
    ("ALTER TABLE race_data RENAME COLUMN race_points TO old_points; ALTER TABLE race_data ADD COLUMN race_points TEXT",
     "unexpected affinity for race_data.race_points"),
    ("ALTER TABLE driver RENAME TO old_driver; CREATE TABLE driver (id TEXT NOT NULL PRIMARY KEY, name TEXT)",
     "expected NOT NULL for driver.name"),
])
def test_incompatible_schema_fails_clearly(source_db: Path, change: str, message: str) -> None:
    with closing(sqlite3.connect(source_db)) as connection:
        connection.executescript(change)
    with pytest.raises(SourceSchemaError, match=message):
        F1DBRepository(source_db)


def test_snapshot_identifies_file_without_inventing_release(repository: F1DBRepository, source_db: Path) -> None:
    snapshot = repository.identify_snapshot()
    assert snapshot.sha256 == hashlib.sha256(source_db.read_bytes()).hexdigest()
    assert snapshot.size_bytes == source_db.stat().st_size
    assert snapshot.sqlite_schema_version > 0 and snapshot.sqlite_user_version == 0
    assert snapshot.upstream_release is None


def test_categories_and_approved_candidate_set() -> None:
    assert {category.value for category in ChampionshipCategory} == {"drivers", "constructors"}
    assert POC_CANDIDATE_SEASONS == (2010, 2011, 2012, 2013)


@pytest.mark.integration
@pytest.mark.parametrize(("year", "event_count", "classification_count", "standing_count"), [
    (2010, 19, 456, 27), (2011, 19, 454, 28),
    (2012, 20, 480, 25), (2013, 19, 418, 23),
])
def test_curated_source_coverage(project_source_db: Path, year: int, event_count: int,
                                 classification_count: int, standing_count: int) -> None:
    repository = F1DBRepository(project_source_db)
    events = repository.get_season_events(year)
    results = repository.get_gp_classifications(year)
    standings = repository.get_recorded_driver_standings(year)
    assert len(events) == event_count
    assert [event.round for event in events] == list(range(1, event_count + 1))
    assert len(results) == classification_count
    assert len({row.source_key for row in results}) == classification_count
    assert len(standings) == standing_count
    assert len({row.source_key for row in standings}) == standing_count
    assert all(row.driver.name is not None and row.constructor.name is not None for row in results)
    assert {row.source_key.race_id for row in results} == {event.race_id for event in events}


@pytest.mark.integration
def test_project_source_is_identified_and_unchanged(project_source_db: Path) -> None:
    expected_hash = "6249c3d8e361b5358981a1dfba6a34218a471af35b5f3ab6d6deb19638ac5a71"
    repository = F1DBRepository(project_source_db)
    before = repository.identify_snapshot()
    assert before.sha256 == expected_hash
    assert before.upstream_release is None
    for year in POC_CANDIDATE_SEASONS:
        repository.get_season_events(year)
        repository.get_gp_classifications(year)
        repository.get_recorded_driver_standings(year)
    assert repository.identify_snapshot() == before
