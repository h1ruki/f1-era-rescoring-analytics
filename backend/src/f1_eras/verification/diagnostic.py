"""Read-only diagnostic for the existing four-season slice, not a promotion tool."""

import argparse
from dataclasses import asdict, dataclass
from fractions import Fraction
import json
from pathlib import Path
import subprocess

from f1_eras.analytics.original_drivers import (
    CALCULATION_VERSION, OriginalDriversChampionship,
    calculate_original_drivers, original_drivers_rules,
)
from f1_eras.data_access.f1db import F1DBRepository
from f1_eras.domain.verification import (
    AssessmentState, ClassificationState, FindingCode, ReconstructionCheck,
    ReconstructionOutcome, StandingValue, VerificationAssessment,
    VerificationContext, VerificationFinding,
)
from f1_eras.verification.evaluate import evaluate_verification
from f1_eras.verification.metadata import content_hash


BASELINE_YEARS = (2010, 2011, 2012, 2013)


@dataclass(frozen=True, slots=True)
class BaselineDiagnostic:
    assessment: VerificationAssessment
    driver_count: int
    award_count: int
    f1db_award_difference_count: int | None
    f1db_standing_difference_count: int | None


def _implementation_identity() -> tuple[str | None, bool]:
    root = Path(__file__).resolve().parents[4]
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                                check=True, capture_output=True, text=True).stdout.strip()
        status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"],
                                cwd=root, check=True, capture_output=True, text=True).stdout
        return commit, bool(status)
    except (OSError, subprocess.CalledProcessError):
        return None, True


def _invariants(result: OriginalDriversChampionship) -> bool:
    for standing in result.standings:
        awards = sum((award.points for award in result.event_awards
                      if award.driver.id == standing.driver.id), Fraction())
        contributions = sum((item.counted_points for item in standing.constructor_contributions), Fraction())
        if awards != standing.points or contributions != standing.points:
            return False
    return (result.raw_points_gap == result.p1.points - result.p2.points
            and result.p1.points != 0
            and result.percentage_gap == result.raw_points_gap / result.p1.points * 100)


def diagnose_baseline(db_path: str | Path) -> tuple[BaselineDiagnostic, ...]:
    """Use existing calculations unchanged, with no historical metadata supplied.

    Structural source checks here are the existing calculator's checks. They do
    not establish historical completeness; absent season evidence blocks that.
    Reconciliation against F1DB is reported separately and cannot grant PASSED.
    """
    repository = F1DBRepository(db_path)
    before = repository.identify_snapshot()
    commit, dirty = _implementation_identity()
    diagnostics = []
    for year in BASELINE_YEARS:
        rules = original_drivers_rules(year)
        assert rules is not None
        context = VerificationContext(before.sha256, None, content_hash(asdict(rules)), commit, dirty)
        driver_count = award_count = 0
        award_differences = standing_differences = None
        try:
            events = repository.get_season_events(year)
            rows = repository.get_gp_classifications(year)
            result = calculate_original_drivers(
                year, events, rows, repository.get_recorded_driver_standings(year),
            )
            if isinstance(result, OriginalDriversChampionship):
                driver_count, award_count = len(result.standings), len(result.event_awards)
                award_differences = len(result.event_award_differences)
                standing_differences = len(result.standing_differences)
                reconstruction = ReconstructionCheck(
                    ReconstructionOutcome.COMPLETED, context, year, rules.package.value, CALCULATION_VERSION,
                    tuple(StandingValue(row.driver.id, row.points, row.position, ClassificationState.RANKED)
                          for row in result.standings),
                    tuple(event.race_id for event in events),
                    source_checks_passed=True, invariant_checks_passed=_invariants(result),
                )
            else:
                reconstruction = ReconstructionCheck(
                    ReconstructionOutcome.UNAVAILABLE, context, year, rules.package.value, CALCULATION_VERSION,
                    findings=(VerificationFinding(FindingCode.RECONSTRUCTION_UNAVAILABLE,
                                                  result.reason + "; " + result.resolution),),
                )
        except Exception as error:
            # The diagnostic records errors distinctly, never as historical
            # unsupported cases. Its CLI returns nonzero when any error occurs.
            reconstruction = ReconstructionCheck(
                ReconstructionOutcome.ERROR, context, year, rules.package.value, CALCULATION_VERSION,
                findings=(VerificationFinding(FindingCode.ASSESSMENT_ERROR,
                                              f"{type(error).__name__}: {error}"),),
            )
        assessment = evaluate_verification(
            year=year, package_id=rules.package.value, implementation_id=CALCULATION_VERSION,
            reconstruction=reconstruction, context=context, metadata=None,
        )
        diagnostics.append(BaselineDiagnostic(assessment, driver_count, award_count,
                                               award_differences, standing_differences))
    if repository.identify_snapshot() != before:
        raise RuntimeError("F1DB changed during diagnostic; discard this run")
    if _implementation_identity() != (commit, dirty):
        raise RuntimeError("Implementation identity changed during diagnostic; discard this run")
    return tuple(diagnostics)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path(__file__).resolve().parents[4] / "f1db.db")
    args = parser.parse_args()
    diagnostics = diagnose_baseline(args.db)
    print(json.dumps([asdict(item) for item in diagnostics], indent=2))
    return int(any(item.assessment.state == AssessmentState.ERROR for item in diagnostics))


if __name__ == "__main__":
    raise SystemExit(main())
