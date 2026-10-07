"""Assignment source facts, schema checks and bound-image provenance."""

from contextlib import closing
import sqlite3

import pytest

from f1_eras.data_access import f1db
from f1_eras.data_access.connection import SourceDatabaseError
from f1_eras.data_access.f1db import F1DBRepository, SourceSchemaError
from f1_eras.domain.models import EntrantDriverAssignmentKey, EntrantIdentity


def test_assignment_reader_preserves_ids_coverage_and_source_key(repository):
    first, second = repository.get_season_entrant_assignments(2012)
    assert first.source_key == EntrantDriverAssignmentKey(
        2012, "entrant-a", "constructor-a", "engine-a", "driver-a",
    )
    assert first.entrant == EntrantIdentity("entrant-a", "Entrant A")
    assert first.driver.name == "Driver A" and first.constructor.name == "Constructor A"
    assert first.rounds == (1, 2)
    assert first.recorded_rounds == "1;2" and first.rounds_text == "1-2"
    assert second.entrant.id == "entrant-b" and second.rounds == (1,)
    assert repository.get_season_entrant_assignments(2050) == ()


@pytest.mark.parametrize("year", ["2012 OR 1=1", True, 2012.0, None])
def test_assignment_reader_rejects_non_integer_year(repository, year):
    with pytest.raises(TypeError, match="year must be an integer"):
        repository.get_season_entrant_assignments(year)


def test_assignment_reader_does_not_invent_missing_identity_or_round_coverage(source_db):
    with closing(sqlite3.connect(source_db)) as connection:
        connection.execute("DELETE FROM entrant WHERE id = 'entrant-a'")
        connection.execute("UPDATE season_entrant_driver SET rounds = NULL WHERE entrant_id = 'entrant-a'")
        connection.execute("UPDATE season_entrant_driver SET rounds = '' WHERE entrant_id = 'entrant-b'")
        connection.commit()
    first, second = F1DBRepository(source_db).get_season_entrant_assignments(2012)
    assert first.entrant.name is None and first.rounds is None
    assert second.rounds == ()


@pytest.mark.parametrize("rounds", ["1-3", "1;bad", "0", "1;1"])
def test_unrecognized_round_coverage_retains_identity_and_source_error(source_db, rounds):
    with closing(sqlite3.connect(source_db)) as connection:
        connection.execute("UPDATE season_entrant_driver SET rounds = ?", (rounds,))
        connection.commit()
    assignments = F1DBRepository(source_db).get_season_entrant_assignments(2012)
    assert len(assignments) == 2
    assert all(item.rounds is None and "assignment rounds" in item.round_coverage_error for item in assignments)
    assert all(item.recorded_rounds == rounds for item in assignments)


@pytest.mark.parametrize(("change", "message"), [
    ("DROP TABLE entrant", "missing table entrant"),
    ("ALTER TABLE season_entrant_driver DROP COLUMN rounds", "missing column season_entrant_driver.rounds"),
])
def test_teammate_source_schema_is_validated(source_db, change, message):
    with closing(sqlite3.connect(source_db)) as connection:
        connection.execute(change)
    with pytest.raises(SourceSchemaError, match=message):
        F1DBRepository(source_db).get_season_entrant_assignments(2012)
    source = F1DBRepository(source_db).read_original_drivers_source(2012)
    assert source.entrant_assignments is None
    assert message in source.teammate_source_error
    assert source.classifications and source.recorded and source.events


def test_assignments_use_captured_assessment_image(source_db, monkeypatch):
    repository = F1DBRepository(source_db)
    original = f1db._BoundF1DBReader.get_season_events

    def replace_entrant_after_calendar(reader, year):
        events = original(reader, year)
        with closing(sqlite3.connect(source_db)) as connection:
            connection.execute("UPDATE entrant SET name = 'Replacement entrant'")
            connection.execute("UPDATE season_entrant_driver SET rounds = '2'")
            connection.commit()
        return events

    monkeypatch.setattr(f1db._BoundF1DBReader, "get_season_events", replace_entrant_after_calendar)
    source = repository.read_original_drivers_source(2012)
    assert source.snapshot != source.current_snapshot
    assert source.entrant_assignments[0].entrant.name == "Entrant A"
    assert source.entrant_assignments[0].rounds == (1, 2)
    assert repository.get_season_entrant_assignments(2012)[0].entrant.name == "Replacement entrant"


@pytest.mark.parametrize("rounds", ["bad-format", b"binary-rounds"])
def test_real_assignment_parse_failure_does_not_block_core_source(source_db, rounds):
    repository = F1DBRepository(source_db)
    healthy = repository.read_original_drivers_source(2012)
    with closing(sqlite3.connect(source_db)) as connection:
        connection.execute("UPDATE season_entrant_driver SET rounds = ?", (rounds,))
        connection.commit()
    source = repository.read_original_drivers_source(2012)
    assert source.entrant_assignments
    assert all(item.rounds is None and "Unrecognized entrant assignment rounds" in item.round_coverage_error
               for item in source.entrant_assignments)
    assert source.events == healthy.events
    assert source.classifications == healthy.classifications
    assert source.recorded == healthy.recorded


def test_optional_assignment_sql_failure_does_not_block_core_source(source_db, monkeypatch):
    repository = F1DBRepository(source_db)

    def fail_optional_query(reader, year):
        raise sqlite3.OperationalError("Injected optional assignment query failure")

    monkeypatch.setattr(f1db._BoundF1DBReader, "get_season_entrant_assignments", fail_optional_query)
    source = repository.read_original_drivers_source(2012)
    assert source.entrant_assignments is None
    assert "optional assignment query failure" in source.teammate_source_error
    assert source.events and source.classifications and source.recorded


def test_huge_numeric_round_token_is_normalized_to_source_error():
    with pytest.raises(SourceDatabaseError, match="Unparseable entrant assignment rounds"):
        f1db._assignment_rounds("9" * 10000)


def test_unused_test_driver_value_does_not_change_assignment_acquisition(source_db):
    repository = F1DBRepository(source_db)
    baseline = repository.get_season_entrant_assignments(2012)
    with closing(sqlite3.connect(source_db)) as connection:
        connection.execute("UPDATE season_entrant_driver SET test_driver = 2")
        connection.commit()
    assert repository.get_season_entrant_assignments(2012) == baseline
    assert repository.read_original_drivers_source(2012).entrant_assignments == baseline


def test_unused_test_driver_column_is_not_required(source_db):
    repository = F1DBRepository(source_db)
    baseline = repository.get_season_entrant_assignments(2012)
    with closing(sqlite3.connect(source_db)) as connection:
        connection.execute("ALTER TABLE season_entrant_driver DROP COLUMN test_driver")
    assert repository.get_season_entrant_assignments(2012) == baseline
    assert repository.read_original_drivers_source(2012).entrant_assignments == baseline
