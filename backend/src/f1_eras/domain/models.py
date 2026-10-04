"""Source facts, without championship calculations or inferred identities."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum


class ChampionshipCategory(StrEnum):
    DRIVERS = "drivers"
    CONSTRUCTORS = "constructors"


# Product-owner approved candidates, not a claim of implemented scoring support.
POC_CANDIDATE_SEASONS: tuple[int, ...] = (2010, 2011, 2012, 2013)


@dataclass(frozen=True, slots=True)
class DriverIdentity:
    id: str
    name: str | None  # None when the source identity lookup is missing.


@dataclass(frozen=True, slots=True)
class ConstructorIdentity:
    id: str
    name: str | None


@dataclass(frozen=True, slots=True)
class SeasonEvent:
    race_id: int
    year: int
    round: int
    date: date
    grand_prix_id: str
    official_name: str
    laps: int
    distance: Decimal
    scheduled_laps: int | None
    scheduled_distance: Decimal | None
    sprint_race_date: date | None
    sprint_race_laps: int | None
    sprint_race_distance: Decimal | None
    sprint_race_scheduled_laps: int | None
    sprint_race_scheduled_distance: Decimal | None


@dataclass(frozen=True, slots=True)
class GPClassificationKey:
    race_id: int
    session_type: str
    position_display_order: int


@dataclass(frozen=True, slots=True)
class GPClassification:
    source_key: GPClassificationKey
    year: int
    round: int
    position_number: int | None
    position_text: str
    driver_number: str
    driver: DriverIdentity
    constructor: ConstructorIdentity
    engine_manufacturer_id: str
    shared_car: bool | None
    laps: int | None
    reason_retired: str | None
    recorded_points: Decimal | None
    time_penalty: str | None
    time_penalty_millis: int | None
    fastest_lap: bool | None


@dataclass(frozen=True, slots=True)
class DriverStandingKey:
    year: int
    position_display_order: int


@dataclass(frozen=True, slots=True)
class RecordedDriverStanding:
    source_key: DriverStandingKey
    position_number: int | None
    position_text: str
    driver: DriverIdentity
    recorded_points: Decimal
    championship_won: bool


@dataclass(frozen=True, slots=True)
class F1DBSnapshot:
    sha256: str
    size_bytes: int
    sqlite_schema_version: int
    sqlite_user_version: int
    upstream_release: str | None = None
