"""Read-only Original Drivers service; no championship mathematics here."""

from dataclasses import asdict, dataclass
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
from f1_eras.data_access.connection import SourceSnapshotChanged
from f1_eras.domain.models import ChampionshipCategory, F1DBSnapshot
from f1_eras.domain.verification import (
    AssessmentState, CanonicalTrustAssessment, ComparisonOutcome, FindingCode,
    ReconstructionOutcome, VerificationFinding,
)
from f1_eras.verification.external_audit import enrich_external_audit
from f1_eras.verification.metadata import content_hash
from f1_eras.verification.canonical import assess_canonical_original


@dataclass(frozen=True, slots=True)
class CalculationDiagnostics:
    driver_count: int
    award_count: int
    event_award_difference_count: int
    standing_difference_count: int


@dataclass(frozen=True, slots=True)
class ChampionshipReport:
    year: int
    category: ChampionshipCategory
    scoring: str
    result: OriginalDriversChampionship | CalculationUnavailable
    rules: OriginalDriversRules | None
    source_snapshot: F1DBSnapshot | None
    trust: CanonicalTrustAssessment | None = None
    calculation_diagnostics: CalculationDiagnostics | None = None


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
        try:
            source = self._repository.read_original_drivers_source(year)
        except SourceSnapshotChanged as error:
            rules = original_drivers_rules(year)
            assert rules is not None
            unavailable = CalculationUnavailable(year, category, str(error), "Retry against a stable standalone snapshot")
            trust = CanonicalTrustAssessment(
                year, rules.package.value, CALCULATION_VERSION, None, content_hash(asdict(rules)),
                AssessmentState.STALE, ReconstructionOutcome.NOT_ATTEMPTED, ComparisonOutcome.NOT_RUN, False,
                (VerificationFinding(FindingCode.CONTEXT_STALE, str(error)),),
            )
            return ChampionshipReport(year, category, "original", unavailable, rules, None, trust)
        result = calculate_original_drivers(year, source.events, source.classifications, source.recorded, category)
        trust = assess_canonical_original(
            year=year, snapshot=source.snapshot, current_snapshot=source.current_snapshot,
            events=source.events, classifications=source.classifications, recorded=source.recorded,
            population=source.population, result=result,
        )
        trust = enrich_external_audit(trust)
        diagnostics = (CalculationDiagnostics(
            len(result.standings), len(result.event_awards), len(result.event_award_differences),
            len(result.standing_differences),
        ) if isinstance(result, OriginalDriversChampionship) else None)
        if isinstance(result, OriginalDriversChampionship) and not trust.trusted_for_normal_use:
            result = CalculationUnavailable(
                year, category, "Canonical Original trust assessment did not pass: "
                + "; ".join(finding.message for finding in trust.findings),
                "Resolve the reported source, reconciliation or reconstruction conflict and reassess",
            )
        return ChampionshipReport(
            year, category, "original", result, original_drivers_rules(year),
            source.snapshot, trust, diagnostics,
        )
