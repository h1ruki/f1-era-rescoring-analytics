"""Original Drivers championships for the four approved PoC source years.

The final F1DB GP classification is the historical fact. Recorded event awards
and standings are comparison inputs only; neither determines a calculated total.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction

from f1_eras.domain.models import (
    ChampionshipCategory,
    ConstructorIdentity,
    DriverIdentity,
    GPClassification,
    GPClassificationKey,
    RecordedDriverStanding,
    SeasonEvent,
)


class OriginalPackage(StrEnum):
    YEAR_2010 = "original-2010"
    YEAR_2011 = "original-2011"
    YEAR_2012 = "original-2012"
    YEAR_2013 = "original-2013"


_PACKAGES = {2010: OriginalPackage.YEAR_2010, 2011: OriginalPackage.YEAR_2011,
             2012: OriginalPackage.YEAR_2012, 2013: OriginalPackage.YEAR_2013}
_POINTS = (25, 18, 15, 12, 10, 8, 6, 4, 2, 1)
CALCULATION_VERSION = "original-drivers-2010-2013-v1"
SUPPORTED_ORIGINAL_DRIVERS_SEASONS = tuple(_PACKAGES)


@dataclass(frozen=True, slots=True)
class OriginalDriversRules:
    package: OriginalPackage
    points_by_position: tuple[int, ...]
    results_counted: str
    countback: str
    sprint_points: str
    fastest_lap_points: str
    classification_basis: str


def original_drivers_rules(year: int) -> OriginalDriversRules | None:
    """Expose the implemented package facts without duplicating scoring rules."""
    package = _PACKAGES.get(year)
    if package is None:
        return None
    return OriginalDriversRules(
        package=package,
        points_by_position=_POINTS,
        results_counted="All results from Grands Prix actually held",
        countback="Most first places, then second places, through classified finishes",
        sprint_points="None",
        fastest_lap_points="None",
        classification_basis="Final recorded amended GP classification",
    )


@dataclass(frozen=True, slots=True)
class CalculationUnavailable:
    year: int
    category: ChampionshipCategory
    reason: str
    resolution: str


@dataclass(frozen=True, slots=True)
class ReconstructedEventAward:
    source_key: GPClassificationKey
    driver: DriverIdentity
    constructor: ConstructorIdentity
    final_position: int | None
    final_position_text: str
    points: Fraction
    recorded_points: Fraction | None
    counted: bool  # Every held GP result counts in these four packages.


@dataclass(frozen=True, slots=True)
class ConstructorContribution:
    constructor: ConstructorIdentity
    counted_points: Fraction


@dataclass(frozen=True, slots=True)
class ReconstructedDriverStanding:
    position: int
    driver: DriverIdentity
    points: Fraction
    finish_counts: tuple[int, ...]  # 1st, 2nd, ... through the largest classified place.
    constructor_contributions: tuple[ConstructorContribution, ...]


@dataclass(frozen=True, slots=True)
class EventAwardDifference:
    source_key: GPClassificationKey
    calculated_points: Fraction
    recorded_points: Fraction | None


@dataclass(frozen=True, slots=True)
class StandingDifference:
    driver_id: str
    calculated_position: int | None
    recorded_position: int | None
    calculated_points: Fraction | None
    recorded_points: Fraction | None
    calculated_champion: bool | None
    recorded_champion: bool | None


@dataclass(frozen=True, slots=True)
class OriginalDriversChampionship:
    year: int
    package: OriginalPackage
    calculation_version: str
    event_awards: tuple[ReconstructedEventAward, ...]
    standings: tuple[ReconstructedDriverStanding, ...]
    recorded_standings: tuple[RecordedDriverStanding, ...]
    event_award_differences: tuple[EventAwardDifference, ...]
    standing_differences: tuple[StandingDifference, ...]
    p1: ReconstructedDriverStanding
    p2: ReconstructedDriverStanding
    raw_points_gap: Fraction
    percentage_gap: Fraction


def calculate_original_drivers(
    year: int,
    events: tuple[SeasonEvent, ...],
    classifications: tuple[GPClassification, ...],
    recorded_standings: tuple[RecordedDriverStanding, ...],
    category: ChampionshipCategory = ChampionshipCategory.DRIVERS,
) -> OriginalDriversChampionship | CalculationUnavailable:
    """Calculate from source facts only, with no data access or source mutation."""
    if type(year) is not int:
        raise TypeError("year must be an integer")
    if category != ChampionshipCategory.DRIVERS:
        return CalculationUnavailable(year, category, "Constructor championship is unimplemented",
                                      "Implement and verify Constructor rules separately")
    if year not in _PACKAGES:
        return CalculationUnavailable(year, category, "Original source-year package is unsupported",
                                      "Add a sourced and verified package for this year")
    if not events or any(event.year != year for event in events):
        return CalculationUnavailable(year, category, "Target calendar is absent or inconsistent",
                                      "Provide the complete source-year event calendar")
    event_ids = {event.race_id for event in events}
    rounds_by_event = {event.race_id: event.round for event in events}
    if len(event_ids) != len(events) or len({event.round for event in events}) != len(events):
        return CalculationUnavailable(year, category, "Target calendar has duplicate events or rounds",
                                      "Correct the source calendar")
    rows_by_event: dict[int, list[GPClassification]] = defaultdict(list)
    seen_keys: set[GPClassificationKey] = set()
    seen_driver_events: set[tuple[int, str]] = set()
    for row in classifications:
        key = row.source_key
        if (row.year != year or key.race_id not in event_ids
                or key.session_type != "RACE_RESULT" or key in seen_keys
                or (key.race_id, row.driver.id) in seen_driver_events):
            return CalculationUnavailable(year, category, "GP classifications are inconsistent",
                                          "Provide unique final GP results for the source calendar")
        seen_keys.add(key)
        seen_driver_events.add((key.race_id, row.driver.id))
        rows_by_event[key.race_id].append(row)
    if any(not rows_by_event[event.race_id] for event in events):
        return CalculationUnavailable(year, category, "A calendar event has no final GP classification",
                                      "Provide final classifications for all held events")
    if any(row.round != rounds_by_event[row.source_key.race_id]
           or (row.position_number is not None and row.position_number < 1)
           for row in classifications):
        return CalculationUnavailable(year, category, "GP position or round is inconsistent",
                                      "Correct the final source classifications")

    awards: list[ReconstructedEventAward] = []
    award_differences: list[EventAwardDifference] = []
    totals: dict[str, Fraction] = defaultdict(Fraction)
    finishes: dict[str, Counter[int]] = defaultdict(Counter)
    identities: dict[str, DriverIdentity] = {}
    contributions: dict[str, dict[str, Fraction]] = defaultdict(lambda: defaultdict(Fraction))
    constructors: dict[str, ConstructorIdentity] = {}
    for event in sorted(events, key=lambda item: item.round):
        for row in sorted(rows_by_event[event.race_id],
                          key=lambda item: item.source_key.position_display_order):
            points = Fraction(_POINTS[row.position_number - 1]) if (
                row.position_number is not None and row.position_number <= len(_POINTS)
            ) else Fraction(0)
            recorded = Fraction(row.recorded_points) if row.recorded_points is not None else None
            awards.append(ReconstructedEventAward(
                row.source_key, row.driver, row.constructor, row.position_number,
                row.position_text, points, recorded, True,
            ))
            if points != (recorded if recorded is not None else 0):
                award_differences.append(EventAwardDifference(row.source_key, points, recorded))
            totals[row.driver.id] += points
            identities[row.driver.id] = row.driver
            constructors[row.constructor.id] = row.constructor
            contributions[row.driver.id][row.constructor.id] += points
            if row.position_number is not None:
                finishes[row.driver.id][row.position_number] += 1

    max_finish = max((position for counts in finishes.values() for position in counts), default=0)
    ordered_ids = sorted(totals, key=lambda driver_id: (
        -totals[driver_id],
        *(-finishes[driver_id][position] for position in range(1, max_finish + 1)),
    ))
    for first, second in zip(ordered_ids, ordered_ids[1:]):
        if (totals[first] == totals[second]
                and finishes[first] == finishes[second]):
            return CalculationUnavailable(year, category, "Countback cannot resolve a tied ranking",
                                          "Verify the applicable further tie-break rule")
    standings = tuple(ReconstructedDriverStanding(
        position=index,
        driver=identities[driver_id],
        points=totals[driver_id],
        finish_counts=tuple(finishes[driver_id][place] for place in range(1, max_finish + 1)),
        constructor_contributions=tuple(ConstructorContribution(
            constructors[constructor_id], points,
        ) for constructor_id, points in sorted(contributions[driver_id].items())),
    ) for index, driver_id in enumerate(ordered_ids, start=1))
    if len(standings) < 2:
        return CalculationUnavailable(year, category, "Fewer than two classified drivers",
                                      "Provide the complete final GP classifications")

    calculated_by_id = {standing.driver.id: standing for standing in standings}
    recorded_by_id = {standing.driver.id: standing for standing in recorded_standings}
    standing_differences: list[StandingDifference] = []
    for driver_id in sorted(calculated_by_id.keys() | recorded_by_id.keys()):
        calculated = calculated_by_id.get(driver_id)
        recorded = recorded_by_id.get(driver_id)
        recorded_position = recorded.position_number if recorded is not None else None
        recorded_points = Fraction(recorded.recorded_points) if recorded is not None else None
        if (calculated is None or recorded is None or calculated.position != recorded_position
                or calculated.points != recorded_points
                or (calculated.position == 1) != recorded.championship_won):
            standing_differences.append(StandingDifference(
                driver_id, calculated.position if calculated else None, recorded_position,
                calculated.points if calculated else None, recorded_points,
                calculated.position == 1 if calculated else None,
                recorded.championship_won if recorded else None,
            ))
    p1, p2 = standings[:2]
    if p1.points == 0:
        return CalculationUnavailable(year, category, "P1 has zero points; percentage gap is undefined",
                                      "Define an approved zero-denominator presentation rule")
    gap = p1.points - p2.points
    return OriginalDriversChampionship(
        year, _PACKAGES[year], CALCULATION_VERSION, tuple(awards), standings,
        recorded_standings, tuple(award_differences), tuple(standing_differences),
        p1, p2, gap, gap / p1.points * 100,
    )
