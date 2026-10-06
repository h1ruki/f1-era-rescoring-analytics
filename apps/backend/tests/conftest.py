"""Small synthetic source databases; never write to the repository F1DB."""

from pathlib import Path
import sqlite3

import pytest

from f1_eras.data_access.f1db import F1DBRepository


# Independent DDL matching the consumed part of the inspected F1DB schema.
_SCHEMA = """
CREATE TABLE season (year INTEGER NOT NULL PRIMARY KEY);
CREATE TABLE race (
    id INTEGER NOT NULL PRIMARY KEY, year INTEGER NOT NULL,
    round INTEGER NOT NULL, date DATE NOT NULL,
    grand_prix_id VARCHAR(100) NOT NULL, official_name VARCHAR(100) NOT NULL,
    laps INTEGER NOT NULL, distance DECIMAL(6,3) NOT NULL,
    scheduled_laps INTEGER, scheduled_distance DECIMAL(6,3),
    sprint_race_date DATE, sprint_race_laps INTEGER,
    sprint_race_distance DECIMAL(6,3), sprint_race_scheduled_laps INTEGER,
    sprint_race_scheduled_distance DECIMAL(6,3)
);
CREATE TABLE driver (id VARCHAR(100) NOT NULL PRIMARY KEY, name VARCHAR(100) NOT NULL);
CREATE TABLE constructor (id VARCHAR(100) NOT NULL PRIMARY KEY, name VARCHAR(100) NOT NULL);
CREATE TABLE race_data (
    race_id INTEGER NOT NULL, type VARCHAR(50) NOT NULL,
    position_display_order INTEGER NOT NULL, position_number INTEGER,
    position_text VARCHAR(4) NOT NULL, driver_number VARCHAR(3) NOT NULL,
    driver_id VARCHAR(100) NOT NULL, constructor_id VARCHAR(100) NOT NULL,
    engine_manufacturer_id VARCHAR(100) NOT NULL, race_shared_car BOOLEAN,
    race_laps INTEGER, race_reason_retired VARCHAR(100), race_points DECIMAL(8,2),
    race_time_penalty VARCHAR(20), race_time_penalty_millis INTEGER,
    race_fastest_lap BOOLEAN,
    PRIMARY KEY (race_id, type, position_display_order)
);
CREATE TABLE season_driver_standing (
    year INTEGER NOT NULL, position_display_order INTEGER NOT NULL,
    position_number INTEGER, position_text VARCHAR(4) NOT NULL,
    driver_id VARCHAR(100) NOT NULL, points DECIMAL(8,2) NOT NULL,
    championship_won BOOLEAN NOT NULL,
    PRIMARY KEY (year, position_display_order)
);
CREATE TABLE entrant (id TEXT NOT NULL PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE season_entrant_driver (
    year INTEGER NOT NULL, entrant_id TEXT NOT NULL, constructor_id TEXT NOT NULL,
    engine_manufacturer_id TEXT NOT NULL, driver_id TEXT NOT NULL,
    rounds TEXT, rounds_text TEXT, test_driver BOOLEAN NOT NULL,
    PRIMARY KEY (year, entrant_id, constructor_id, engine_manufacturer_id, driver_id)
);
CREATE TABLE season_entrant_constructor (year INTEGER, entrant_id TEXT, constructor_id TEXT);
"""


@pytest.fixture
def source_db(tmp_path: Path) -> Path:
    path = tmp_path / "source # fixture.db"
    connection = sqlite3.connect(path)
    try:
        connection.executescript(_SCHEMA)
        connection.executemany("INSERT INTO season VALUES (?)", [(2012,), (2013,)])
        connection.executemany("INSERT INTO driver VALUES (?, ?)", [
            ("driver-a", "Driver A"), ("driver-b", "Driver B"),
        ])
        connection.executemany("INSERT INTO constructor VALUES (?, ?)", [
            ("constructor-a", "Constructor A"), ("constructor-b", "Constructor B"),
        ])
        connection.executemany("INSERT INTO race VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
            (20, 2012, 2, "2012-03-25", "second", "Second Event", 56,
             "310.408", None, None, "2012-03-24", 10, "55.430", 10, "55.430"),
            (10, 2012, 1, "2012-03-18", "first", "First Event", 69,
             "302.249", 70, "306.630", None, None, None, None, None),
            (30, 2013, 1, "2013-03-17", "other", "Other Season", 58,
             "307.574", None, None, None, None, None, None, None),
        ])
        result_rows = [
            (10, "RACE_RESULT", 1, 1, "1", "007", "driver-a", "constructor-a",
             "engine-a", 1, 69, None, "0.5", None, None, 0),
            (10, "RACE_RESULT", 2, 2, "2", "007", "driver-a", "constructor-b",
             "engine-b", 0, 69, None, 0, "20.000", 20000, 1),
            (10, "RACE_RESULT", 3, None, "DNF", "8", "driver-b", "constructor-b",
             "engine-b", None, 2, "Engine", None, None, None, None),
            (10, "RACE_RESULT", 4, None, "DSQ", "9", "missing-driver", "missing-constructor",
             "unknown-engine", 0, 69, None, None, None, None, 0),
        ]
        for order, status in enumerate(("DNS", "NC", "DNQ", "UNKN"), start=5):
            result_rows.append((10, "RACE_RESULT", order, None, status, "8",
                                "driver-b", "constructor-b", "engine-b",
                                0, None, None, None, None, None, 0))
        for session_type in ("QUALIFYING_RESULT", "SPRINT_RACE_RESULT", "PIT_STOP"):
            result_rows.append((10, session_type, 1, 1, "1", "007",
                                "driver-a", "constructor-a", "engine-a",
                                None, None, None, 25, None, None, None))
        connection.executemany(
            "INSERT INTO race_data VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            result_rows,
        )
        connection.executemany("INSERT INTO season_driver_standing VALUES (?, ?, ?, ?, ?, ?, ?)", [
            (2012, 1, 1, "1", "driver-a", "5.5", 1),
            (2012, 2, None, "DSQ", "missing-driver", 3, 0),
            (2012, 3, 2, "2", "driver-b", 0, 0),
            (2013, 1, 1, "1", "driver-b", 25, 1),
        ])
        connection.executemany("INSERT INTO entrant VALUES (?, ?)", [
            ("entrant-a", "Entrant A"), ("entrant-b", "Entrant B"),
        ])
        connection.executemany("INSERT INTO season_entrant_driver VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
            (2012, "entrant-a", "constructor-a", "engine-a", "driver-a", "1;2", "1-2", 0),
            (2012, "entrant-b", "constructor-b", "engine-b", "driver-a", "1", "1", 0),
        ])
        connection.executemany("INSERT INTO season_entrant_constructor VALUES (?, ?, ?)", [
            (2012, "entrant-a", "constructor-a"), (2012, "entrant-a", "constructor-b"),
            (2012, "entrant-b", "constructor-a"), (2012, "entrant-b", "constructor-b"),
        ])
        connection.commit()
    finally:
        connection.close()
    return path


@pytest.fixture
def repository(source_db: Path) -> F1DBRepository:
    return F1DBRepository(source_db)


@pytest.fixture
def project_source_db() -> Path:
    path = Path(__file__).resolve().parents[3] / "data" / "f1db.db"
    assert path.is_file(), "Tracked F1DB snapshot is required for integration tests"
    return path
