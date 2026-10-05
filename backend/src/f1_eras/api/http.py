"""Minimal FastAPI projection of the Original Drivers application service."""

from dataclasses import asdict
from fractions import Fraction
import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query

from f1_eras.analytics.original_drivers import (
    CalculationUnavailable,
    OriginalDriversChampionship,
    OriginalDriversRules,
    ReconstructedDriverStanding,
)
from f1_eras.application.championships import (
    ChampionshipReport, ChampionshipService, project_for_plot,
)
from f1_eras.data_access.f1db import F1DBRepository
from f1_eras.domain.models import ChampionshipCategory, F1DBSnapshot


def _exact(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def _value(value: Fraction) -> dict[str, object]:
    return {"exact": _exact(value), "plot": project_for_plot(value)}


def _rules(rules: OriginalDriversRules | None) -> dict[str, object] | None:
    if rules is None:
        return None
    return {
        "package": rules.package.value,
        "points_by_position": list(rules.points_by_position),
        "results_counted": rules.results_counted,
        "countback": rules.countback,
        "sprint_points": rules.sprint_points,
        "fastest_lap_points": rules.fastest_lap_points,
        "classification_basis": rules.classification_basis,
        "margin_formula": "(P1 - P2) / P1 * 100",
    }


def _snapshot(snapshot: F1DBSnapshot | None) -> dict[str, object] | None:
    if snapshot is None:
        return None
    return {
        "sha256": snapshot.sha256,
        "size_bytes": snapshot.size_bytes,
        "sqlite_schema_version": snapshot.sqlite_schema_version,
        "sqlite_user_version": snapshot.sqlite_user_version,
        "upstream_release": snapshot.upstream_release,
    }


def _driver(standing: ReconstructedDriverStanding) -> dict[str, object]:
    return {
        "id": standing.driver.id,
        "name": standing.driver.name,
        "position": standing.position,
        "points": _value(standing.points),
        "constructor_contributions": [
            {"constructor_id": item.constructor.id, "constructor_name": item.constructor.name,
             "counted_points": _value(item.counted_points)}
            for item in standing.constructor_contributions
        ],
    }


def _summary(report: ChampionshipReport) -> dict[str, object]:
    base: dict[str, object] = {
        "season": report.year,
        "category": report.category.value,
        "scoring": report.scoring,
        "rules": _rules(report.rules),
        "source_snapshot": _snapshot(report.source_snapshot),
        "trust": ({**asdict(report.trust),
                   "trusted_for_normal_use": report.trust.trusted_for_normal_use}
                  if report.trust is not None else None),
    }
    result = report.result
    if isinstance(result, CalculationUnavailable):
        return {
            **base, "availability": "unavailable", "package": None,
            "calculation_version": None,
            "reason": result.reason, "resolution": result.resolution,
            "champion": None, "runner_up": None, "margin": None,
            "reconciliation": None,
        }
    return {
        **base, "availability": "available", "package": result.package.value,
        "calculation_version": result.calculation_version,
        "champion": _driver(result.p1), "runner_up": _driver(result.p2),
        "margin": {
            "raw_points_gap": _value(result.raw_points_gap),
            "championship_margin_percent": _value(result.percentage_gap),
        },
        "reconciliation": {
            "event_awards_match": not result.event_award_differences,
            "recorded_driver_standings_match": not result.standing_differences,
            "event_award_difference_count": len(result.event_award_differences),
            "standing_difference_count": len(result.standing_differences),
        },
    }


def _detail(report: ChampionshipReport) -> dict[str, object]:
    summary = _summary(report)
    result = report.result
    if isinstance(result, CalculationUnavailable):
        return summary
    assert isinstance(result, OriginalDriversChampionship)
    return {
        **summary,
        "standings": [
            {**_driver(standing), "finish_counts": list(standing.finish_counts)}
            for standing in result.standings
        ],
        "recorded_standings": [
            {
                "source_key": {"year": standing.source_key.year,
                               "position_display_order": standing.source_key.position_display_order},
                "driver_id": standing.driver.id, "driver_name": standing.driver.name,
                "recorded_position": standing.position_number,
                "recorded_position_text": standing.position_text,
                "recorded_points": _exact(Fraction(standing.recorded_points)),
                "championship_won": standing.championship_won,
            } for standing in result.recorded_standings
        ],
        "event_awards": [
            {
                "source_key": {"race_id": award.source_key.race_id,
                               "session_type": award.source_key.session_type,
                               "position_display_order": award.source_key.position_display_order},
                "driver_id": award.driver.id, "constructor_id": award.constructor.id,
                "final_position": award.final_position,
                "final_position_text": award.final_position_text,
                "counted": award.counted, "points": _exact(award.points),
                "recorded_points": _exact(award.recorded_points)
                if award.recorded_points is not None else None,
            } for award in result.event_awards
        ],
        "event_award_differences": [
            {"source_key": {"race_id": difference.source_key.race_id,
                            "session_type": difference.source_key.session_type,
                            "position_display_order": difference.source_key.position_display_order},
             "calculated_points": _exact(difference.calculated_points),
             "recorded_points": _exact(difference.recorded_points)
             if difference.recorded_points is not None else None}
            for difference in result.event_award_differences
        ],
        "standing_differences": [
            {"driver_id": difference.driver_id,
             "calculated_position": difference.calculated_position,
             "recorded_position": difference.recorded_position,
             "calculated_points": _exact(difference.calculated_points)
             if difference.calculated_points is not None else None,
             "recorded_points": _exact(difference.recorded_points)
             if difference.recorded_points is not None else None,
             "calculated_champion": difference.calculated_champion,
             "recorded_champion": difference.recorded_champion}
            for difference in result.standing_differences
        ],
    }


def create_app(service: ChampionshipService) -> FastAPI:
    """Construct the API from an injected service; imports do not open F1DB."""
    app = FastAPI(title="F1 ERAs", version="1.0.0")

    @app.get("/api/v1/capabilities")
    def capabilities() -> dict[str, object]:
        available = service.capabilities()
        return {
            "supported_seasons": list(available.supported_seasons),
            "supported_category": available.supported_category.value,
            "unimplemented_category": available.unimplemented_category.value,
            "scoring": available.scoring,
            "calculation_version": available.calculation_version,
            "packages": [_rules(rules) for rules in available.packages],
        }

    @app.get("/api/v1/championship-margins")
    def championship_margins(
        seasons: list[int] | None = Query(default=None),
        category: Literal["drivers", "constructors"] = "drivers",
        scoring: Literal["original"] = "original",
    ) -> dict[str, object]:
        requested = sorted(set(seasons)) if seasons is not None else list(
            service.capabilities().supported_seasons
        )
        if any(year < 1 for year in requested):
            raise HTTPException(status_code=422, detail="Season must be a positive calendar year")
        return {"category": category, "scoring": scoring, "results": [
            _summary(service.original_drivers(year, ChampionshipCategory(category)))
            for year in requested
        ]}

    @app.get("/api/v1/championships/{season}")
    def championship_detail(
        season: int, category: Literal["drivers", "constructors"] = "drivers",
        scoring: Literal["original"] = "original",
    ) -> dict[str, object]:
        if season < 1:
            raise HTTPException(status_code=422, detail="Season must be a positive calendar year")
        return _detail(service.original_drivers(season, ChampionshipCategory(category)))

    return app


def create_default_app() -> FastAPI:
    """Uvicorn factory: F1_ERAS_DB_PATH may override the local PoC snapshot."""
    db_path = Path(os.environ.get(
        "F1_ERAS_DB_PATH", str(Path(__file__).resolve().parents[4] / "f1db.db")
    ))
    return create_app(ChampionshipService(F1DBRepository(db_path)))
