"""Generic canonical-F1DB trust adapter for supported Original Drivers rules.

No external-evidence prerequisites and no season-specific trust branches.
The existing independent evaluator retains its stricter supplementary claim.
"""

from collections import Counter
from dataclasses import asdict
from fractions import Fraction

from f1_eras.analytics.original_drivers import (
    CALCULATION_VERSION, CalculationUnavailable, OriginalDriversChampionship,
    original_drivers_rules,
)
from f1_eras.domain.models import (
    CanonicalDriverPopulation, F1DBSnapshot, GPClassification, RecordedDriverStanding, SeasonEvent,
)
from f1_eras.domain.verification import (
    AssessmentState, CanonicalTrustAssessment, ClassificationState, ComparisonOutcome,
    FindingCode, ReconstructionOutcome, StandingValue,
    VerificationFinding, ordered_findings,
)
from f1_eras.verification.approval import SnapshotApprovalError, load_snapshot_approval
from f1_eras.verification.compare import compare_standings
from f1_eras.verification.metadata import (
    ExpectedDriver, ExpectedStandings, PopulationCoverage, content_hash,
)


def reconstruction_invariants(result: OriginalDriversChampionship) -> bool:
    """Reconcile awards, contribution totals, ranking/countback and margins."""
    standings = result.standings
    if len(standings) < 2 or result.p1 != standings[0] or result.p2 != standings[1]:
        return False
    if len({row.driver.id for row in standings}) != len(standings):
        return False
    max_finish = max((award.final_position or 0 for award in result.event_awards), default=0)
    for index, standing in enumerate(standings, start=1):
        awards = tuple(award for award in result.event_awards if award.driver.id == standing.driver.id)
        counts = Counter(award.final_position for award in awards if award.final_position is not None)
        contributions = Counter()
        for award in awards:
            contributions[award.constructor.id] += award.points
        if (standing.position != index or standing.points != sum((award.points for award in awards), Fraction())
                or standing.finish_counts != tuple(counts[position] for position in range(1, max_finish + 1))
                or len({item.constructor.id for item in standing.constructor_contributions})
                != len(standing.constructor_contributions)
                or dict(contributions) != {item.constructor.id: item.counted_points
                                           for item in standing.constructor_contributions}):
            return False
    if {award.driver.id for award in result.event_awards} != {row.driver.id for row in standings}:
        return False
    keys = tuple((row.points, row.finish_counts) for row in standings)
    if keys != tuple(sorted(keys, reverse=True)) or len(set(keys)) != len(keys):
        return False
    return (result.p1.points > 0 and result.raw_points_gap == result.p1.points - result.p2.points
            and result.percentage_gap == result.raw_points_gap / result.p1.points * 100)


def assess_canonical_original(
    *, year: int, snapshot: F1DBSnapshot, current_snapshot: F1DBSnapshot,
    events: tuple[SeasonEvent, ...], classifications: tuple[GPClassification, ...],
    recorded: tuple[RecordedDriverStanding, ...], population: CanonicalDriverPopulation,
    result: OriginalDriversChampionship | CalculationUnavailable,
) -> CanonicalTrustAssessment:
    """Assess inputs and this result afresh; never promote a cached assessment.

    Repository schema/read-only checks precede this adapter. Pinned immutable
    F1DB supplies historical scope; unknown upstream lineage is non-blocking.
    Null event awards outside the scoring positions are canonical absence of
    an award, not unknown championship points. Championship points stay exact.
    """
    findings: list[VerificationFinding] = []

    def add(code: FindingCode, message: str, subject: str = "season") -> None:
        findings.append(VerificationFinding(code, message, subject))

    rules = original_drivers_rules(year)
    canonical = False
    try:
        canonical = load_snapshot_approval().matches(snapshot)
    except SnapshotApprovalError as error:
        add(FindingCode.METADATA_INVALID, f"Canonical snapshot approval unavailable: {error}")
    if not canonical:
        add(FindingCode.CANONICAL_DATASET_REQUIRED, "Source is not the approved immutable F1DB snapshot")
    population_complete = (
        population.year == year and population.f1db_sha256 == snapshot.sha256
        and bool(population.driver_ids)
        and len(set(population.driver_ids)) == len(population.driver_ids)
        and tuple(row.driver.id for row in recorded) == population.driver_ids
    )
    if not population_complete:
        add(FindingCode.POPULATION_INCOMPLETE, "Comparison does not cover the bound canonical championship population")
    if snapshot != current_snapshot:
        add(FindingCode.CONTEXT_STALE, "Source snapshot changed during reconstruction; discard this attempt")
    if rules is None:
        add(FindingCode.CAPABILITY_UNIMPLEMENTED, "Original source-year package is unsupported")
    if result.year != year:
        add(FindingCode.SOURCE_DATA_INCONSISTENT, "Result year differs from requested source year")

    outcome = ReconstructionOutcome.UNAVAILABLE
    comparison = ComparisonOutcome.NOT_RUN
    if isinstance(result, CalculationUnavailable):
        add(FindingCode.RECONSTRUCTION_UNAVAILABLE, result.reason + "; " + result.resolution)
    else:
        outcome = ReconstructionOutcome.COMPLETED
        if (rules is None or result.package != rules.package
                or result.calculation_version != CALCULATION_VERSION):
            add(FindingCode.CAPABILITY_UNIMPLEMENTED, "Result package or calculation version is unsupported")
        if (not events or any(event.year != year for event in events)
                or len({event.race_id for event in events}) != len(events)
                or sorted(event.round for event in events) != list(range(1, len(events) + 1))):
            add(FindingCode.SOURCE_DATA_INCONSISTENT, "Calendar population/rounds are absent or inconsistent")
        if any(event.laps <= 0 or event.distance <= 0 for event in events):
            add(FindingCode.SEASON_NOT_COMPLETE, "Calendar includes an event without a held GP result")
        if any(any(value is not None for value in (
                event.sprint_race_date, event.sprint_race_laps, event.sprint_race_distance,
                event.sprint_race_scheduled_laps, event.sprint_race_scheduled_distance)) for event in events):
            add(FindingCode.CAPABILITY_UNIMPLEMENTED, "Source-year sprint interpretation is unsupported")
        rounds = {event.race_id: event.round for event in events}
        if ({row.source_key.race_id for row in classifications} != set(rounds)
                or any(row.year != year or row.round != rounds.get(row.source_key.race_id)
                       or row.source_key.session_type != "RACE_RESULT" for row in classifications)
                or len({row.source_key for row in classifications}) != len(classifications)
                or len({(row.source_key.race_id, row.driver.id) for row in classifications}) != len(classifications)):
            add(FindingCode.SOURCE_DATA_INCONSISTENT, "GP population, keys or event/driver identity are inconsistent")
        for row in classifications:
            if row.shared_car is True:
                add(FindingCode.CAPABILITY_UNIMPLEMENTED, "Shared-drive scoring interpretation is unsupported", row.driver.id)
            elif row.shared_car is not False:
                add(FindingCode.HISTORICAL_AMBIGUITY, "Shared-drive participation state is unknown", row.driver.id)
            if ((row.position_number is None and row.position_text not in {"DNF", "DNS", "DSQ", "NC", "DNQ"})
                    or (row.position_number is not None and
                        (row.position_number < 1 or row.position_text != str(row.position_number)))):
                add(FindingCode.HISTORICAL_AMBIGUITY, "GP classification is unknown or inconsistent", row.driver.id)
        for race_id in rounds:
            positions = [row.position_number for row in classifications
                         if row.source_key.race_id == race_id and row.position_number is not None]
            if len(positions) != len(set(positions)):
                add(FindingCode.HISTORICAL_AMBIGUITY, "GP tied positions need an unsupported interpretation", str(race_id))

        # Bind the trace to the supplied source rows and implemented points;
        # reconciliation can never excuse an internally inconsistent trace.
        rows_by_key = {row.source_key: row for row in classifications}
        if (len(result.event_awards) != len(classifications)
                or len({award.source_key for award in result.event_awards}) != len(result.event_awards)):
            add(FindingCode.SOURCE_DATA_INCONSISTENT, "Award trace does not cover unique source classifications")
        for award in result.event_awards:
            source = rows_by_key.get(award.source_key)
            if source is None:
                add(FindingCode.SOURCE_DATA_INCONSISTENT, "Award has no source classification")
                continue
            points = Fraction(rules.points_by_position[source.position_number - 1]) if (
                rules is not None and source.position_number is not None
                and 1 <= source.position_number <= len(rules.points_by_position)) else Fraction()
            recorded_points = Fraction(source.recorded_points) if source.recorded_points is not None else None
            if (award.driver != source.driver or award.constructor != source.constructor
                    or award.final_position != source.position_number or award.final_position_text != source.position_text
                    or award.recorded_points != recorded_points or award.points != points or award.counted is not True):
                add(FindingCode.SOURCE_DATA_INCONSISTENT, "Award trace differs from source/implemented rules", source.driver.id)
            if points != (recorded_points if recorded_points is not None else Fraction()):
                add(FindingCode.POINTS_MISMATCH, "Event award differs from canonical recorded award", source.driver.id)
        if not reconstruction_invariants(result):
            add(FindingCode.INVARIANTS_UNCHECKED, "Award, contribution, countback or margin invariant failed")
        if result.recorded_standings != recorded:
            add(FindingCode.SOURCE_DATA_INCONSISTENT, "Result comparison input differs from canonical standings")
        if any(row.source_key.year != year for row in recorded) or len({row.source_key for row in recorded}) != len(recorded):
            add(FindingCode.SOURCE_DATA_INCONSISTENT, "Recorded standings year or source keys are inconsistent")
        if {row.driver.id for row in result.standings} != set(population.driver_ids):
            add(FindingCode.POPULATION_INCOMPLETE, "Reconstruction does not cover the bound canonical championship population")
        # Unsupported championship classifications are UNKNOWN, never silently
        # converted to a ranking via display order or numeric position alone.
        expected = ExpectedStandings(year, PopulationCoverage.COMPLETE if population_complete else PopulationCoverage.PARTIAL, "f1db", "final_amended", (), tuple(
            ExpectedDriver(StandingValue(row.driver.id, Fraction(row.recorded_points), row.position_number,
                ClassificationState.RANKED if row.position_number is not None
                and row.position_text == str(row.position_number) else ClassificationState.UNKNOWN),
                row.position_text, ()) for row in recorded
        ))
        compared = compare_standings(tuple(StandingValue(row.driver.id, row.points, row.position,
                                    ClassificationState.RANKED) for row in result.standings), expected)
        comparison = compared.outcome
        findings.extend(compared.findings)
        if any(row.championship_won != (row.position_number == 1) for row in recorded):
            add(FindingCode.SOURCE_DATA_INCONSISTENT, "Canonical championship-won flags differ from sporting positions")

    state = AssessmentState.BLOCKED if findings else AssessmentState.PASSED
    if any(item.code == FindingCode.CONTEXT_STALE for item in findings):
        state = AssessmentState.STALE
    package_id = rules.package.value if rules else None
    return CanonicalTrustAssessment(
        year, package_id, CALCULATION_VERSION, snapshot.sha256, content_hash(asdict(rules) if rules else None),
        state, outcome, comparison, canonical, ordered_findings(findings),
    )
