"""Read-only diagnostic using the production canonical trust path."""

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import subprocess

from f1_eras.analytics.original_drivers import (
    CALCULATION_VERSION,
    SUPPORTED_ORIGINAL_DRIVERS_SEASONS, original_drivers_rules,
)
from f1_eras.application.championships import ChampionshipService
from f1_eras.data_access.f1db import F1DBRepository
from f1_eras.domain.verification import (
    AssessmentState, CanonicalTrustAssessment, ComparisonOutcome, FindingCode,
    ReconstructionOutcome, VerificationFinding,
)
from f1_eras.verification.approval import SnapshotApprovalError, load_snapshot_approval
from f1_eras.verification.metadata import content_hash


BASELINE_YEARS = SUPPORTED_ORIGINAL_DRIVERS_SEASONS


@dataclass(frozen=True, slots=True)
class BaselineDiagnostic:
    assessment: CanonicalTrustAssessment
    driver_count: int | None
    award_count: int | None
    f1db_award_difference_count: int | None
    f1db_standing_difference_count: int | None
    implementation_commit: str | None
    working_tree_dirty: bool


def _implementation_identity() -> tuple[str | None, bool]:
    root = Path(__file__).resolve().parents[5]
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                                check=True, capture_output=True, text=True).stdout.strip()
        status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"],
                                cwd=root, check=True, capture_output=True, text=True).stdout
        return commit, bool(status)
    except (OSError, subprocess.CalledProcessError):
        return None, True


def _approved(snapshot) -> bool:
    try:
        return load_snapshot_approval().matches(snapshot)
    except SnapshotApprovalError:
        return False


def diagnose_baseline(db_path: str | Path) -> tuple[BaselineDiagnostic, ...]:
    """Reassess through the service; Git identity is diagnostic information.

    This does not create independent audit evidence or reuse an old success.
    A dirty tree cannot yield strict independent verification, but it does not
    prevent normal-use canonical trust under the superseding product decision.
    """
    repository = F1DBRepository(db_path)
    service = ChampionshipService(repository)
    before = repository.identify_snapshot()
    commit, dirty = _implementation_identity()
    diagnostics = []
    for year in BASELINE_YEARS:
        rules = original_drivers_rules(year)
        assert rules is not None
        driver_count = award_count = None
        award_differences = standing_differences = None
        try:
            report = service.original_drivers(year)
            assessment = report.trust
            assert assessment is not None
            if report.calculation_diagnostics is not None:
                counts = report.calculation_diagnostics
                driver_count, award_count = counts.driver_count, counts.award_count
                award_differences = counts.event_award_difference_count
                standing_differences = counts.standing_difference_count
        except Exception as error:
            # The diagnostic records errors distinctly, never as historical
            # unsupported cases. Its CLI returns nonzero when any error occurs.
            assessment = CanonicalTrustAssessment(
                year, rules.package.value, CALCULATION_VERSION, before.sha256, content_hash(asdict(rules)),
                AssessmentState.ERROR, ReconstructionOutcome.ERROR, ComparisonOutcome.NOT_RUN,
                _approved(before),
                findings=(VerificationFinding(FindingCode.ASSESSMENT_ERROR,
                                              f"{type(error).__name__}: {error}"),),
            )
        diagnostics.append(BaselineDiagnostic(assessment, driver_count, award_count,
                                               award_differences, standing_differences, commit, dirty))
    if repository.identify_snapshot() != before:
        raise RuntimeError("F1DB changed during diagnostic; discard this run")
    if _implementation_identity() != (commit, dirty):
        raise RuntimeError("Implementation identity changed during diagnostic; discard this run")
    return tuple(diagnostics)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path(__file__).resolve().parents[5] / "data" / "f1db.db")
    args = parser.parse_args()
    diagnostics = diagnose_baseline(args.db)
    print(json.dumps([{**asdict(item), "assessment": {
        **asdict(item.assessment), "trusted_for_normal_use": item.assessment.trusted_for_normal_use,
    }} for item in diagnostics], indent=2))
    return int(any(item.assessment.state == AssessmentState.ERROR for item in diagnostics))


if __name__ == "__main__":
    raise SystemExit(main())
