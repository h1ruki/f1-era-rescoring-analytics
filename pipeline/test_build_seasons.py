import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_seasons import is_completed, margin, pick_team

SEASONS_PATH = Path(__file__).resolve().parent.parent / "data" / "seasons.json"


@pytest.fixture(scope="module")
def seasons() -> dict[int, dict]:
    data = json.loads(SEASONS_PATH.read_text(encoding="utf-8"))
    return {s["year"]: s for s in data}


def test_team_attribution_picks_highest_sum() -> None:
    totals = {"cooper": Decimal(19), "ferrari": Decimal(9)}
    assert pick_team(1966, "john-surtees", totals) == "cooper"


def test_team_attribution_tie_raises() -> None:
    with pytest.raises(ValueError, match="1999 some-driver"):
        pick_team(1999, "some-driver", {"a": Decimal(5), "b": Decimal(5)})


def test_team_attribution_null_points_count_as_zero() -> None:
    # NULL race_points are read as 0 (COALESCE), so the 27-point team wins.
    totals = {"ferrari": Decimal(27), "vanwall": Decimal(0)}
    assert pick_team(1959, "tony-brooks", totals) == "ferrari"


def test_completeness() -> None:
    assert is_completed(1, [3, 1, 2])
    assert not is_completed(1, [3, 0, 2])  # a race lacks results
    assert not is_completed(0, [3, 1])  # no champion flagged
    assert not is_completed(2, [3, 1])


def test_margin_rounding() -> None:
    assert margin(Decimal(90), Decimal(87)) == (Decimal("3.00"), Decimal("3.33"))


def test_margin_equal_points_is_zero() -> None:
    assert margin(Decimal(50), Decimal(50)) == (Decimal(0), Decimal(0))


def test_margin_champion_below_runner_up_raises() -> None:
    with pytest.raises(ValueError):
        margin(Decimal(40), Decimal(41))


def check(
    s: dict,
    role: str,
    driver_id: str,
    points: float | None = None,
    team: str | None = None,
    abbreviation: str | None = None,
) -> None:
    assert s[role]["driverId"] == driver_id
    if abbreviation is not None:
        assert s[role]["abbreviation"] == abbreviation
    if points is not None:
        assert s[role]["points"] == points
    if team is not None:
        assert s[role]["teamId"] == team


def test_1952(seasons: dict[int, dict]) -> None:
    check(seasons[1952], "champion", "alberto-ascari", 36)
    check(seasons[1952], "runnerUp", "nino-farina", 24)
    assert seasons[1952]["gapPercent"] == 33.33


def test_1954(seasons: dict[int, dict]) -> None:
    check(seasons[1954], "champion", "juan-manuel-fangio", 42, "mercedes")
    check(seasons[1954], "runnerUp", "jose-froilan-gonzalez", 25.14, abbreviation="GON")


def test_1957(seasons: dict[int, dict]) -> None:
    check(seasons[1957], "runnerUp", "stirling-moss", team="vanwall")


def test_1958(seasons: dict[int, dict]) -> None:
    check(seasons[1958], "champion", "mike-hawthorn", 42)
    check(seasons[1958], "runnerUp", "stirling-moss", 41, "vanwall")


def test_1959(seasons: dict[int, dict]) -> None:
    check(seasons[1959], "runnerUp", "tony-brooks", team="ferrari")


def test_1964(seasons: dict[int, dict]) -> None:
    check(seasons[1964], "champion", "john-surtees", 40, "ferrari")
    check(seasons[1964], "runnerUp", "graham-hill", 39, "brm")


def test_1966(seasons: dict[int, dict]) -> None:
    check(seasons[1966], "runnerUp", "john-surtees", team="cooper")


def test_1988(seasons: dict[int, dict]) -> None:
    check(seasons[1988], "champion", "ayrton-senna", 90)
    check(seasons[1988], "runnerUp", "alain-prost", 87)
    assert seasons[1988]["gapPercent"] == 3.33


def test_1997(seasons: dict[int, dict]) -> None:
    check(seasons[1997], "runnerUp", "heinz-harald-frentzen")


def test_2001(seasons: dict[int, dict]) -> None:
    check(seasons[2001], "champion", "michael-schumacher", abbreviation="MSC")


def test_2021(seasons: dict[int, dict]) -> None:
    check(seasons[2021], "champion", "max-verstappen", 395.5, abbreviation="VER")
    check(seasons[2021], "runnerUp", "lewis-hamilton", 387.5)


def test_2025(seasons: dict[int, dict]) -> None:
    check(seasons[2025], "champion", "lando-norris", 423)
    check(seasons[2025], "runnerUp", "max-verstappen", 421)
    assert seasons[2025]["gapPercent"] == 0.47


def test_every_champion_and_runner_up_has_an_abbreviation(seasons: dict[int, dict]) -> None:
    for s in seasons.values():
        for role in ("champion", "runnerUp"):
            assert s[role]["abbreviation"], f"{s['year']} {role}"


def test_no_championship_through_2025_finished_level(seasons: dict[int, dict]) -> None:
    # Pins the Methodology's "1950 to 2025" claim only; a later season may finish level on points.
    for year in range(1950, 2026):
        assert seasons[year]["gapPoints"] > 0, year


def test_points_are_whole_hundredths(seasons: dict[int, dict]) -> None:
    # The frontend ranks headline extremes on integer hundredths of a point (src/stats.ts).
    # Finer precision in the data must fail here so that comparator is revisited, not rounded.
    for s in seasons.values():
        for role in ("champion", "runnerUp"):
            hundredths = Decimal(str(s[role]["points"])) * 100
            assert hundredths == hundredths.to_integral_value(), f"{s['year']} {role}"


def test_year_range(seasons: dict[int, dict]) -> None:
    years = sorted(seasons)
    assert years[0] == 1950
    assert 2026 not in seasons
    assert years == list(range(years[0], years[-1] + 1))
