"""Teammate context, retaining source evidence independently of HTTP presentation."""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from f1_eras.domain.models import (
    DriverIdentity,
    DriverStandingKey,
    EntrantIdentity,
    GPClassificationKey,
    SeasonEntrantDriverAssignment,
)


class PrimaryTeammateSelection(StrEnum):
    UNIQUE = "unique"
    NONE = "none"
    UNRESOLVED_TIE = "unresolved_tie"


@dataclass(frozen=True, slots=True)
class SharedRaceEvidence:
    race_id: int
    round: int
    entrant: EntrantIdentity
    champion_assignment: SeasonEntrantDriverAssignment
    teammate_assignment: SeasonEntrantDriverAssignment
    champion_result_keys: tuple[GPClassificationKey, ...]
    teammate_result_keys: tuple[GPClassificationKey, ...]


@dataclass(frozen=True, slots=True)
class TeammateCandidate:
    driver: DriverIdentity
    final_standing_source_key: DriverStandingKey | None
    official_final_position: int | None
    official_final_position_text: str | None
    official_final_points: Decimal | None
    shared_race_count: int
    shared_races: tuple[SharedRaceEvidence, ...]
    is_primary: bool


@dataclass(frozen=True, slots=True)
class TeammateContext:
    year: int
    champion: DriverIdentity
    candidates: tuple[TeammateCandidate, ...]
    primary_selection: PrimaryTeammateSelection
    primary_teammate_id: str | None
    tied_primary_candidate_ids: tuple[str, ...]

    @property
    def primary_teammate(self) -> TeammateCandidate | None:
        return next((item for item in self.candidates if item.is_primary), None)

    @property
    def additional_teammates(self) -> tuple[TeammateCandidate, ...]:
        # With no selected primary, preserve every candidate here, including ties.
        return tuple(item for item in self.candidates if not item.is_primary)
