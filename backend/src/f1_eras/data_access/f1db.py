"""Parameterized F1DB readers. All queries and schema adaptation live here."""

from datetime import date
from decimal import Decimal
import hashlib
from pathlib import Path
import sqlite3

from f1_eras.data_access.connection import SourceDatabaseError, open_read_only
from f1_eras.domain.models import (
    ConstructorIdentity,
    DriverIdentity,
    DriverStandingKey,
    F1DBSnapshot,
    GPClassification,
    GPClassificationKey,
    RecordedDriverStanding,
    SeasonEvent,
)


class SourceSchemaError(SourceDatabaseError):
    """The source schema is incompatible with the fields these readers consume."""


# Expected SQLite affinities and NOT NULL declarations for consumed columns.
# Unrelated columns, indexes and tables may be added without invalidating access.
_REQUIRED_COLUMNS = {
    "season": {"year": ("INTEGER", True)},
    "race": {
        "id": ("INTEGER", True), "year": ("INTEGER", True),
        "round": ("INTEGER", True), "date": ("NUMERIC", True),
        "grand_prix_id": ("TEXT", True), "official_name": ("TEXT", True),
        "laps": ("INTEGER", True), "distance": ("NUMERIC", True),
        "scheduled_laps": ("INTEGER", False),
        "scheduled_distance": ("NUMERIC", False),
        "sprint_race_date": ("NUMERIC", False),
        "sprint_race_laps": ("INTEGER", False),
        "sprint_race_distance": ("NUMERIC", False),
        "sprint_race_scheduled_laps": ("INTEGER", False),
        "sprint_race_scheduled_distance": ("NUMERIC", False),
    },
    "race_data": {
        "race_id": ("INTEGER", True), "type": ("TEXT", True),
        "position_display_order": ("INTEGER", True),
        "position_number": ("INTEGER", False), "position_text": ("TEXT", True),
        "driver_number": ("TEXT", True), "driver_id": ("TEXT", True),
        "constructor_id": ("TEXT", True), "engine_manufacturer_id": ("TEXT", True),
        "race_shared_car": ("NUMERIC", False), "race_laps": ("INTEGER", False),
        "race_reason_retired": ("TEXT", False), "race_points": ("NUMERIC", False),
        "race_time_penalty": ("TEXT", False),
        "race_time_penalty_millis": ("INTEGER", False),
        "race_fastest_lap": ("NUMERIC", False),
    },
    "driver": {"id": ("TEXT", True), "name": ("TEXT", True)},
    "constructor": {"id": ("TEXT", True), "name": ("TEXT", True)},
    "season_driver_standing": {
        "year": ("INTEGER", True), "position_display_order": ("INTEGER", True),
        "position_number": ("INTEGER", False), "position_text": ("TEXT", True),
        "driver_id": ("TEXT", True), "points": ("NUMERIC", True),
        "championship_won": ("NUMERIC", True),
    },
}
_REQUIRED_KEYS = {
    "season": ("year",), "race": ("id",),
    "race_data": ("race_id", "type", "position_display_order"),
    "driver": ("id",), "constructor": ("id",),
    "season_driver_standing": ("year", "position_display_order"),
}

_EVENTS_SQL = """
SELECT id, year, round, date, grand_prix_id, official_name, laps,
       CAST(distance AS TEXT) AS distance,
       scheduled_laps, CAST(scheduled_distance AS TEXT) AS scheduled_distance,
       sprint_race_date, sprint_race_laps,
       CAST(sprint_race_distance AS TEXT) AS sprint_race_distance,
       sprint_race_scheduled_laps,
       CAST(sprint_race_scheduled_distance AS TEXT) AS sprint_race_scheduled_distance
FROM race WHERE year = ? ORDER BY round, id
"""

_GP_CLASSIFICATIONS_SQL = """
SELECT rd.race_id, rd.type, rd.position_display_order, r.year, r.round,
       rd.position_number, rd.position_text, rd.driver_number,
       rd.driver_id, d.name AS driver_name,
       rd.constructor_id, c.name AS constructor_name, rd.engine_manufacturer_id,
       rd.race_shared_car, rd.race_laps, rd.race_reason_retired,
       CAST(rd.race_points AS TEXT) AS recorded_points,
       rd.race_time_penalty, rd.race_time_penalty_millis, rd.race_fastest_lap
FROM race_data rd
JOIN race r ON r.id = rd.race_id
LEFT JOIN driver d ON d.id = rd.driver_id
LEFT JOIN constructor c ON c.id = rd.constructor_id
WHERE r.year = ? AND rd.type = ?
ORDER BY r.round, r.id, rd.position_display_order
"""

_DRIVER_STANDINGS_SQL = """
SELECT s.year, s.position_display_order, s.position_number, s.position_text,
       s.driver_id, d.name AS driver_name,
       CAST(s.points AS TEXT) AS recorded_points, s.championship_won
FROM season_driver_standing s
LEFT JOIN driver d ON d.id = s.driver_id
WHERE s.year = ? ORDER BY s.position_display_order
"""


def _affinity(declared_type: str) -> str:
    declaration = declared_type.upper()
    if "INT" in declaration:
        return "INTEGER"
    if any(token in declaration for token in ("CHAR", "CLOB", "TEXT")):
        return "TEXT"
    if not declaration or "BLOB" in declaration:
        return "BLOB"
    if any(token in declaration for token in ("REAL", "FLOA", "DOUB")):
        return "REAL"
    return "NUMERIC"


def validate_required_schema(connection: sqlite3.Connection) -> None:
    """Check consumed fields and exact source primary keys, not a version guess."""
    tables = {
        row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    problems: list[str] = []
    for table, requirements in _REQUIRED_COLUMNS.items():
        if table not in tables:
            problems.append(f"missing table {table}")
            continue
        # Identifiers come only from the private fixed schema above, never callers.
        columns = list(connection.execute(f'PRAGMA table_info("{table}")'))
        by_name = {row[1]: row for row in columns}
        for name, (affinity, required_not_null) in requirements.items():
            if name not in by_name:
                problems.append(f"missing column {table}.{name}")
                continue
            column = by_name[name]
            if _affinity(column[2]) != affinity:
                problems.append(f"unexpected affinity for {table}.{name}")
            if required_not_null and not column[3]:
                problems.append(f"expected NOT NULL for {table}.{name}")
        primary_key = tuple(
            row[1] for row in sorted(columns, key=lambda row: row[5]) if row[5]
        )
        if primary_key != _REQUIRED_KEYS[table]:
            problems.append(f"unexpected primary key for {table}: {primary_key}")
    if problems:
        raise SourceSchemaError("Incompatible F1DB schema: " + "; ".join(problems))


def _optional_decimal(value: str | None) -> Decimal | None:
    return None if value is None else Decimal(value)


def _optional_bool(value: int | None, field: str) -> bool | None:
    if value is None:
        return None
    if value not in (0, 1):
        raise SourceDatabaseError(f"Invalid source boolean {field}: {value!r}")
    return bool(value)


class F1DBRepository:
    """Read source facts for any stored year; calculation support is a later gate.

    The caller supplies an explicit path. No prototype imports, writable
    connection fallback, persistent connection, or source mutation is used.
    """

    def __init__(self, db_path: str | Path) -> None:
        self._path = Path(db_path).resolve(strict=True)
        with open_read_only(self._path) as connection:
            validate_required_schema(connection)

    def _read(self, sql: str, year: int, *parameters: object) -> list[sqlite3.Row]:
        if type(year) is not int:
            raise TypeError("year must be an integer")
        with open_read_only(self._path) as connection:
            validate_required_schema(connection)
            return connection.execute(sql, (year, *parameters)).fetchall()

    def get_season_events(self, year: int) -> tuple[SeasonEvent, ...]:
        return tuple(
            SeasonEvent(
                race_id=row["id"], year=row["year"], round=row["round"],
                date=date.fromisoformat(row["date"]),
                grand_prix_id=row["grand_prix_id"], official_name=row["official_name"],
                laps=row["laps"], distance=Decimal(row["distance"]),
                scheduled_laps=row["scheduled_laps"],
                scheduled_distance=_optional_decimal(row["scheduled_distance"]),
                sprint_race_date=(date.fromisoformat(row["sprint_race_date"])
                                  if row["sprint_race_date"] is not None else None),
                sprint_race_laps=row["sprint_race_laps"],
                sprint_race_distance=_optional_decimal(row["sprint_race_distance"]),
                sprint_race_scheduled_laps=row["sprint_race_scheduled_laps"],
                sprint_race_scheduled_distance=_optional_decimal(
                    row["sprint_race_scheduled_distance"]
                ),
            ) for row in self._read(_EVENTS_SQL, year)
        )

    def get_gp_classifications(self, year: int) -> tuple[GPClassification, ...]:
        return tuple(
            GPClassification(
                source_key=GPClassificationKey(
                    row["race_id"], row["type"], row["position_display_order"]
                ),
                year=row["year"], round=row["round"],
                position_number=row["position_number"], position_text=row["position_text"],
                driver_number=row["driver_number"],
                driver=DriverIdentity(row["driver_id"], row["driver_name"]),
                constructor=ConstructorIdentity(row["constructor_id"], row["constructor_name"]),
                engine_manufacturer_id=row["engine_manufacturer_id"],
                shared_car=_optional_bool(row["race_shared_car"], "race_shared_car"),
                laps=row["race_laps"], reason_retired=row["race_reason_retired"],
                recorded_points=_optional_decimal(row["recorded_points"]),
                time_penalty=row["race_time_penalty"],
                time_penalty_millis=row["race_time_penalty_millis"],
                fastest_lap=_optional_bool(row["race_fastest_lap"], "race_fastest_lap"),
            ) for row in self._read(_GP_CLASSIFICATIONS_SQL, year, "RACE_RESULT")
        )

    def get_recorded_driver_standings(self, year: int) -> tuple[RecordedDriverStanding, ...]:
        return tuple(
            RecordedDriverStanding(
                source_key=DriverStandingKey(row["year"], row["position_display_order"]),
                position_number=row["position_number"], position_text=row["position_text"],
                driver=DriverIdentity(row["driver_id"], row["driver_name"]),
                recorded_points=Decimal(row["recorded_points"]),
                championship_won=bool(_optional_bool(row["championship_won"], "championship_won")),
            ) for row in self._read(_DRIVER_STANDINGS_SQL, year)
        )

    def identify_snapshot(self) -> F1DBSnapshot:
        """Identify the standalone file; SQLite schema counters are not releases."""
        before = self._path.stat()
        with open_read_only(self._path) as connection:
            validate_required_schema(connection)
            schema_version = connection.execute("PRAGMA schema_version").fetchone()[0]
            user_version = connection.execute("PRAGMA user_version").fetchone()[0]
            with self._path.open("rb") as source:
                checksum = hashlib.file_digest(source, "sha256").hexdigest()
        after = self._path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise SourceDatabaseError("Source database changed during snapshot identification")
        return F1DBSnapshot(checksum, after.st_size, schema_version, user_version)
