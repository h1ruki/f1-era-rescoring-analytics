"""Service and HTTP contracts for the four curated Original Drivers seasons."""

from dataclasses import replace
from fractions import Fraction
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from f1_eras.analytics.original_drivers import CalculationUnavailable, OriginalDriversChampionship
from f1_eras.api.http import create_app, create_default_app
from f1_eras.application.championships import ChampionshipService
from f1_eras.data_access.f1db import F1DBRepository
from f1_eras.domain.models import ChampionshipCategory
from f1_eras.verification.approval import load_snapshot_approval


@pytest.fixture
def api(project_source_db: Path) -> TestClient:
    return TestClient(create_app(ChampionshipService(F1DBRepository(project_source_db))))


@pytest.mark.integration
def test_default_factory_finds_canonical_data_from_another_directory(tmp_path, monkeypatch):
    monkeypatch.delenv("F1_ERAS_DB_PATH", raising=False)
    monkeypatch.chdir(tmp_path)
    client = TestClient(create_default_app())
    response = client.get("/api/v1/championship-margins")
    assert response.status_code == 200
    results = response.json()["results"]
    assert [item["season"] for item in results] == [2010, 2011, 2012, 2013]
    assert all(item["availability"] == "available" for item in results)
    assert all(item["trust"]["trusted_for_normal_use"] for item in results)
    assert all(item["source_snapshot"]["sha256"] == load_snapshot_approval().sha256
               for item in results)


def test_default_factory_does_not_fall_back_when_explicit_source_is_missing(tmp_path, monkeypatch):
    missing = tmp_path / "explicit missing source.db"
    monkeypatch.setenv("F1_ERAS_DB_PATH", str(missing))
    with pytest.raises(FileNotFoundError):
        create_default_app()
    assert not missing.exists()


@pytest.mark.integration
@pytest.mark.parametrize(("year", "p1", "p2", "gap", "percent"), [
    (2010, 256, 252, 4, Fraction(25, 16)),
    (2011, 392, 270, 122, Fraction(1525, 49)),
    (2012, 281, 278, 3, Fraction(300, 281)),
    (2013, 397, 242, 155, Fraction(15500, 397)),
])
def test_service_reuses_analytics_and_keeps_recorded_results_separate(
    project_source_db: Path, year: int, p1: int, p2: int, gap: int, percent: Fraction,
) -> None:
    repository = F1DBRepository(project_source_db)
    before = repository.identify_snapshot()
    report = ChampionshipService(repository).original_drivers(year)
    assert isinstance(report.result, OriginalDriversChampionship)
    assert report.result.p1.points == p1 and report.result.p2.points == p2
    assert report.result.raw_points_gap == gap
    assert report.result.percentage_gap == percent
    assert report.result.recorded_standings[0].recorded_points == p1
    assert report.result.event_award_differences == ()
    assert report.result.standing_differences == ()
    assert report.rules is not None and report.rules.package == report.result.package
    assert report.source_snapshot == before
    assert repository.identify_snapshot() == before


def test_service_unavailable_boundaries_do_not_query_unsupported_source(
    project_source_db: Path,
) -> None:
    repository = F1DBRepository(project_source_db)
    class NoReads:
        def __getattr__(self, name: str):
            raise AssertionError(f"Unsupported request read source via {name}")

    service = ChampionshipService(NoReads())
    for year, category in ((2009, ChampionshipCategory.DRIVERS),
                           (2012, ChampionshipCategory.CONSTRUCTORS)):
        report = service.original_drivers(year, category)
        assert isinstance(report.result, CalculationUnavailable)
        assert report.source_snapshot is None and report.rules is None
    class MissingFinalEvent:
        def read_original_drivers_source(self, year: int):
            source = repository.read_original_drivers_source(year)
            return replace(source, classifications=tuple(row for row in source.classifications if row.round == 1))

    incomplete = ChampionshipService(MissingFinalEvent()).original_drivers(2012)
    assert isinstance(incomplete.result, CalculationUnavailable)
    assert "no final GP classification" in incomplete.result.reason
    assert incomplete.source_snapshot is not None


def test_capabilities_and_default_margin_collection(api: TestClient) -> None:
    capabilities = api.get("/api/v1/capabilities")
    assert capabilities.status_code == 200
    body = capabilities.json()
    assert body["supported_seasons"] == [2010, 2011, 2012, 2013]
    assert body["supported_category"] == "drivers"
    assert body["unimplemented_category"] == "constructors"
    assert [package["package"] for package in body["packages"]] == [
        "original-2010", "original-2011", "original-2012", "original-2013",
    ]
    assert all(package["points_by_position"] == [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
               for package in body["packages"])
    response = api.get("/api/v1/championship-margins")
    assert response.status_code == 200
    assert [item["season"] for item in response.json()["results"]] == [
        2010, 2011, 2012, 2013,
    ]
    assert all(item["availability"] == "available" for item in response.json()["results"])
    selected = api.get("/api/v1/championship-margins?seasons=2012&seasons=2009&seasons=2010")
    assert selected.status_code == 200
    assert [item["season"] for item in selected.json()["results"]] == [2009, 2010, 2012]
    assert [item["availability"] for item in selected.json()["results"]] == [
        "unavailable", "available", "available",
    ]


@pytest.mark.integration
@pytest.mark.parametrize(("year", "p1", "p2", "gap", "numerator", "denominator"), [
    (2010, 256, 252, 4, 25, 16),
    (2012, 281, 278, 3, 300, 281),
])
def test_margin_response_has_exact_values_and_independent_plot_projections(
    api: TestClient, year: int, p1: int, p2: int, gap: int,
    numerator: int, denominator: int,
) -> None:
    response = api.get("/api/v1/championship-margins", params={"seasons": year})
    assert response.status_code == 200
    item = response.json()["results"][0]
    assert item["season"] == year and item["category"] == "drivers"
    assert item["scoring"] == "original"
    assert item["champion"]["id"] == "sebastian-vettel"
    assert item["champion"]["points"] == {
        "exact": {"numerator": p1, "denominator": 1}, "plot": float(p1),
    }
    assert item["runner_up"]["points"] == {
        "exact": {"numerator": p2, "denominator": 1}, "plot": float(p2),
    }
    assert item["margin"]["raw_points_gap"] == {
        "exact": {"numerator": gap, "denominator": 1}, "plot": float(gap),
    }
    percent = item["margin"]["championship_margin_percent"]
    assert percent["exact"] == {"numerator": numerator, "denominator": denominator}
    assert percent["plot"] == pytest.approx(float(Fraction(numerator, denominator)))
    assert item["champion"]["constructor_contributions"][0]["counted_points"]["exact"] == {
        "numerator": p1, "denominator": 1,
    }
    assert item["reconciliation"] == {
        "event_awards_match": True, "recorded_driver_standings_match": True,
        "event_award_difference_count": 0, "standing_difference_count": 0,
    }
    assert item["source_snapshot"]["sha256"] == load_snapshot_approval().sha256
    assert item["rules"]["margin_formula"] == "(P1 - P2) / P1 * 100"


def test_detail_exposes_trace_recorded_standings_and_source_keys(api: TestClient) -> None:
    response = api.get("/api/v1/championships/2012")
    assert response.status_code == 200
    body = response.json()
    assert body["package"] == "original-2012"
    assert body["standings"][0]["points"]["exact"] == {"numerator": 281, "denominator": 1}
    assert body["recorded_standings"][0]["recorded_points"] == {
        "numerator": 281, "denominator": 1,
    }
    assert body["recorded_standings"][0]["source_key"] == {
        "year": 2012, "position_display_order": 1,
    }
    assert len(body["event_awards"]) == 480
    assert body["event_awards"][0]["source_key"]["session_type"] == "RACE_RESULT"
    assert body["event_award_differences"] == [] and body["standing_differences"] == []


@pytest.mark.integration
def test_api_reads_without_mutating_source(api: TestClient, project_source_db: Path) -> None:
    repository = F1DBRepository(project_source_db)
    before = repository.identify_snapshot()
    assert api.get("/api/v1/championship-margins").status_code == 200
    assert api.get("/api/v1/championships/2013").status_code == 200
    assert repository.identify_snapshot() == before


def test_validation_and_unavailable_are_distinct(api: TestClient) -> None:
    for path in (
        "/api/v1/championship-margins?seasons=abc",
        "/api/v1/championship-margins?category=teams",
        "/api/v1/championship-margins?scoring=2012",
        "/api/v1/championship-margins?seasons=0",
        "/api/v1/championships/not-a-year",
        "/api/v1/championships/-1",
    ):
        assert api.get(path).status_code == 422
    unsupported = api.get("/api/v1/championship-margins?seasons=2009").json()["results"][0]
    assert unsupported["availability"] == "unavailable"
    assert unsupported["champion"] is None and unsupported["margin"] is None
    assert "unsupported" in unsupported["reason"]
    constructor = api.get("/api/v1/championships/2012?category=constructors").json()
    assert constructor["availability"] == "unavailable"
    assert constructor["category"] == "constructors" and constructor["margin"] is None
    assert "unimplemented" in constructor["reason"]


def test_internal_failure_is_not_misreported_as_unavailable() -> None:
    class BrokenService:
        def capabilities(self) -> dict[str, object]:
            raise RuntimeError("source failure")

    client = TestClient(create_app(BrokenService()), raise_server_exceptions=False)
    assert client.get("/api/v1/capabilities").status_code == 500
