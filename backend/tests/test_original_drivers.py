"""Pure scoring checks and four-season read-only reconciliation."""

from dataclasses import replace
from datetime import date
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest

from f1_eras.analytics.original_drivers import (
    CalculationUnavailable,
    OriginalDriversChampionship,
    OriginalPackage,
    calculate_original_drivers,
)
from f1_eras.data_access.f1db import F1DBRepository
from f1_eras.domain.models import (
    ChampionshipCategory,
    ConstructorIdentity,
    DriverIdentity,
    DriverStandingKey,
    GPClassification,
    GPClassificationKey,
    RecordedDriverStanding,
    SeasonEvent,
)


def event(round_number: int, year: int = 2012) -> SeasonEvent:
    return SeasonEvent(
        race_id=round_number, year=year, round=round_number, date=date(year, 3, round_number),
        grand_prix_id=str(round_number), official_name=f"GP {round_number}",
        laps=50, distance=Decimal("300"), scheduled_laps=50,
        scheduled_distance=Decimal("300"), sprint_race_date=None,
        sprint_race_laps=None, sprint_race_distance=None,
        sprint_race_scheduled_laps=None, sprint_race_scheduled_distance=None,
    )


def classification(round_number: int, order: int, driver: str, position: int | None,
                   constructor: str = "team-a", recorded: str | None = None,
                   status: str | None = None) -> GPClassification:
    return GPClassification(
        source_key=GPClassificationKey(round_number, "RACE_RESULT", order),
        year=2012, round=round_number, position_number=position,
        position_text=status or (str(position) if position is not None else "DNF"),
        driver_number="1", driver=DriverIdentity(driver, driver),
        constructor=ConstructorIdentity(constructor, constructor),
        engine_manufacturer_id="engine", shared_car=False, laps=50,
        reason_retired=None, recorded_points=Decimal(recorded) if recorded is not None else None,
        time_penalty=None, time_penalty_millis=None, fastest_lap=False,
    )


def recorded(order: int, driver: str, points: str) -> RecordedDriverStanding:
    return RecordedDriverStanding(
        DriverStandingKey(2012, order), order, str(order), DriverIdentity(driver, driver),
        Decimal(points), order == 1,
    )


def calculated(events: tuple[SeasonEvent, ...], rows: tuple[GPClassification, ...],
               standings: tuple[RecordedDriverStanding, ...] = ()) -> OriginalDriversChampionship:
    result = calculate_original_drivers(2012, events, rows, standings)
    assert isinstance(result, OriginalDriversChampionship), result
    return result


def test_exact_scoring_all_results_contributions_and_p1_p2() -> None:
    events = (event(1), event(2))
    rows = (
        classification(1, 1, "a", 1, "team-a", "25"),
        classification(1, 2, "b", 2, "team-b", "18"),
        classification(1, 3, "c", 11),
        classification(2, 1, "a", 2, "team-c", "18"),
        classification(2, 2, "b", 3, "team-b", "15"),
        classification(2, 3, "c", None),
    )
    result = calculated(events, rows)
    assert (result.p1.driver.id, result.p1.points) == ("a", Fraction(43))
    assert (result.p2.driver.id, result.p2.points) == ("b", Fraction(33))
    assert result.p1.finish_counts[0:2] == (1, 1)
    assert result.raw_points_gap == 10 and result.percentage_gap == Fraction(1000, 43)
    assert [(c.constructor.id, c.counted_points) for c in result.p1.constructor_contributions] == [
        ("team-a", Fraction(25)), ("team-c", Fraction(18)),
    ]
    assert len(result.event_awards) == 6 and all(award.counted for award in result.event_awards)
    assert [award.points for award in result.event_awards] == [25, 18, 0, 18, 15, 0]


def test_full_points_scale_and_exact_zero_gap() -> None:
    rows = tuple(classification(1, place, f"driver-{place}", place)
                 for place in range(1, 12))
    result = calculated((event(1),), rows)
    assert [award.points for award in result.event_awards] == [
        25, 18, 15, 12, 10, 8, 6, 4, 2, 1, 0,
    ]
    tied = calculated((event(1), event(2)), (
        classification(1, 1, "a", 1), classification(1, 2, "b", 3),
        classification(2, 1, "a", 11), classification(2, 2, "b", 5),
    ))
    assert tied.p1.points == tied.p2.points == 25
    assert tied.p1.driver.id == "a"  # Win count breaks the equal points.
    assert tied.raw_points_gap == tied.percentage_gap == 0


def test_countback_across_scoring_and_zero_point_finishes() -> None:
    rows = (
        classification(1, 1, "a", 1), classification(1, 2, "b", 2),
        classification(1, 3, "c", 11), classification(1, 4, "d", 12),
        classification(2, 1, "b", 1), classification(2, 2, "a", 2),
        classification(2, 3, "d", 11), classification(2, 4, "c", 12),
        classification(3, 1, "a", 3), classification(3, 2, "b", 4),
        classification(3, 3, "c", 13), classification(3, 4, "d", 11),
    )
    result = calculated((event(1), event(2), event(3)), rows)
    assert [standing.driver.id for standing in result.standings] == ["a", "b", "d", "c"]
    assert result.p1.points == 58 and result.p2.points == 55
    assert result.raw_points_gap == Fraction(3)
    assert result.percentage_gap == Fraction(150, 29)
    assert result.standings[2].points == result.standings[3].points == 0


def test_recorded_facts_remain_separate_and_amended_classification_is_scored() -> None:
    amended = replace(classification(1, 1, "a", 2, recorded="25"),
                      time_penalty="5.000", time_penalty_millis=5000)
    result = calculated(
        (event(1),), (amended, classification(1, 2, "b", 1, recorded="18")),
        (recorded(1, "a", "25"), recorded(2, "b", "18")),
    )
    assert result.p1.driver.id == "b" and result.p1.points == 25
    assert result.event_awards[0].final_position == 2
    assert result.event_awards[0].points == 18
    assert result.event_awards[0].recorded_points == 25
    assert len(result.event_award_differences) == 2
    assert len(result.standing_differences) == 2
    assert result.recorded_standings[0].driver.id == "a"
    assert result.recorded_standings[0].recorded_points == 25


def test_unavailable_packages_categories_and_incomplete_calendar() -> None:
    rows = (classification(1, 1, "a", 1), classification(1, 2, "b", 2))
    assert isinstance(calculate_original_drivers(2009, (), (), ()), CalculationUnavailable)
    constructor = calculate_original_drivers(
        2012, (event(1),), rows, (), ChampionshipCategory.CONSTRUCTORS,
    )
    assert isinstance(constructor, CalculationUnavailable)
    assert "unimplemented" in constructor.reason
    incomplete = calculate_original_drivers(2012, (event(1), event(2)), rows, ())
    assert isinstance(incomplete, CalculationUnavailable)
    assert "no final GP classification" in incomplete.reason


@pytest.mark.integration
@pytest.mark.parametrize(("year", "package", "p1_points", "p2_id", "p2_points", "gap", "percentage"), [
    (2010, OriginalPackage.YEAR_2010, 256, "fernando-alonso", 252, 4, Fraction(25, 16)),
    (2011, OriginalPackage.YEAR_2011, 392, "jenson-button", 270, 122, Fraction(1525, 49)),
    (2012, OriginalPackage.YEAR_2012, 281, "fernando-alonso", 278, 3, Fraction(300, 281)),
    (2013, OriginalPackage.YEAR_2013, 397, "fernando-alonso", 242, 155, Fraction(15500, 397)),
])
def test_curated_reconciliation_without_source_mutation(
    project_source_db: Path, year: int, package: OriginalPackage,
    p1_points: int, p2_id: str, p2_points: int, gap: int, percentage: Fraction,
) -> None:
    repository = F1DBRepository(project_source_db)
    before = repository.identify_snapshot()
    result = calculate_original_drivers(
        year, repository.get_season_events(year), repository.get_gp_classifications(year),
        repository.get_recorded_driver_standings(year),
    )
    assert isinstance(result, OriginalDriversChampionship), result
    assert result.package == package
    assert (result.p1.driver.id, result.p1.points) == ("sebastian-vettel", p1_points)
    assert (result.p2.driver.id, result.p2.points) == (p2_id, p2_points)
    assert result.raw_points_gap == gap and result.percentage_gap == percentage
    assert result.event_award_differences == ()
    assert result.standing_differences == ()
    assert len(result.event_awards) == len(repository.get_gp_classifications(year))
    assert len(result.standings) == len(result.recorded_standings)
    assert repository.identify_snapshot() == before
