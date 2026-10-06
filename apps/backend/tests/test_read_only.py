import hashlib
from pathlib import Path
import sqlite3

import pytest

from f1_eras.data_access.connection import SourceDatabaseError, open_read_only
from f1_eras.data_access.f1db import F1DBRepository


@pytest.mark.parametrize("statement", [
    "CREATE TABLE forbidden (value INTEGER)",
    "UPDATE driver SET name = 'Changed'",
    "PRAGMA user_version = 99",
])
def test_writes_rejected_without_changing_source(source_db: Path, statement: str) -> None:
    before = hashlib.sha256(source_db.read_bytes()).hexdigest()
    with open_read_only(source_db) as connection:
        assert connection.execute("PRAGMA query_only").fetchone()[0] == 1
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            connection.execute(statement)
    assert hashlib.sha256(source_db.read_bytes()).hexdigest() == before


def test_uri_read_only_survives_disabling_query_only(source_db: Path) -> None:
    before = source_db.read_bytes()
    with open_read_only(source_db) as connection:
        connection.execute("PRAGMA query_only = OFF")
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            connection.execute("UPDATE driver SET name = 'Changed'")
    assert source_db.read_bytes() == before


def test_missing_path_is_not_created(tmp_path: Path) -> None:
    missing = tmp_path / "missing.db"
    with pytest.raises(FileNotFoundError):
        with open_read_only(missing):
            pytest.fail("A missing source must not open")
    with pytest.raises(FileNotFoundError):
        F1DBRepository(missing)
    assert not missing.exists()


def test_directory_is_not_accepted(tmp_path: Path) -> None:
    with pytest.raises(SourceDatabaseError, match="not a file"):
        with open_read_only(tmp_path):
            pytest.fail("A directory must not open")


@pytest.mark.parametrize("suffix", ["-wal", "-journal"])
def test_active_sidecars_are_rejected(source_db: Path, suffix: str) -> None:
    Path(str(source_db) + suffix).write_bytes(b"not a standalone snapshot")
    with pytest.raises(SourceDatabaseError, match="standalone immutable snapshot"):
        with open_read_only(source_db):
            pytest.fail("An active sidecar must not be ignored")


def test_connection_closes_after_success(source_db: Path) -> None:
    with open_read_only(source_db) as connection:
        assert connection.execute("SELECT COUNT(*) FROM driver").fetchone()[0] == 2
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        connection.execute("SELECT 1")


def test_connection_closes_after_error(source_db: Path) -> None:
    with pytest.raises(ValueError, match="synthetic failure"):
        with open_read_only(source_db) as connection:
            raise ValueError("synthetic failure")
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        connection.execute("SELECT 1")
