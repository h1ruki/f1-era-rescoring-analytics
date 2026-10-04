"""Read-only Original Drivers service; no championship mathematics here."""

from dataclasses import dataclass
from fractions import Fraction
from typing import cast

from f1_eras.analytics.original_drivers import (
    CALCULATION_VERSION,
    SUPPORTED_ORIGINAL_DRIVERS_SEASONS,
    CalculationUnavailable,
    OriginalDriversChampionship,
    OriginalDriversRules,
    calculate_original_drivers,
    original_drivers_rules,
)
from f1_eras.data_access.f1db import F1DBRepository
from f1_eras.domain.models import ChampionshipCategory, F1DBSnapshot


@dataclass(frozen=True, slots=True)
class ChampionshipReport:
    year: int
    category: ChampionshipCategory
    scoring: str
    result: OriginalDriversChampionship | CalculationUnavailable
    rules: OriginalDriversRules | None
    source_snapshot: F1DBSnapshot | None


@dataclass(frozen=True, slots=True)
class ChampionshipCapabilities:
    supported_seasons: tuple[int, ...]
    supported_category: ChampionshipCategory
    unimplemented_category: ChampionshipCategory
    scoring: str
    calculation_version: str
    packages: tuple[OriginalDriversRules, ...]


def project_for_plot(value: Fraction) -> float:
    """Lossy display projection; authoritative arithmetic retains ``value``."""
    return float(value)


class ChampionshipService:
    """Resolve supported requests and join analytics to source provenance."""

    def __init__(self, repository: F1DBRepository) -> None:
        self._repository = repository

    def capabilities(self) -> ChampionshipCapabilities:
        packages = tuple(original_drivers_rules(year) for year in SUPPORTED_ORIGINAL_DRIVERS_SEASONS)
        assert all(package is not None for package in packages)
        return ChampionshipCapabilities(
            SUPPORTED_ORIGINAL_DRIVERS_SEASONS, ChampionshipCategory.DRIVERS,
            ChampionshipCategory.CONSTRUCTORS, "original", CALCULATION_VERSION,
            cast(tuple[OriginalDriversRules, ...], packages),
        )

    def original_drivers(
        self, year: int, category: ChampionshipCategory = ChampionshipCategory.DRIVERS,
    ) -> ChampionshipReport:
        if type(year) is not int:
            raise TypeError("year must be an integer")
        if category != ChampionshipCategory.DRIVERS or year not in SUPPORTED_ORIGINAL_DRIVERS_SEASONS:
            unavailable = calculate_original_drivers(year, (), (), (), category)
            assert isinstance(unavailable, CalculationUnavailable)
            return ChampionshipReport(year, category, "original", unavailable, None, None)
        events = self._repository.get_season_events(year)
        classifications = self._repository.get_gp_classifications(year)
        recorded = self._repository.get_recorded_driver_standings(year)
        result = calculate_original_drivers(year, events, classifications, recorded, category)
        return ChampionshipReport(
            year, category, "original", result, original_drivers_rules(year),
            self._repository.identify_snapshot(),
        )
