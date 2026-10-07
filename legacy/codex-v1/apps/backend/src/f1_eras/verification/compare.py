"""Full-population comparison, with no scoring, data access or tie-breaking."""

from collections import Counter

from f1_eras.domain.verification import (
    ClassificationState, ComparisonOutcome, FindingCode, StandingComparison,
    StandingValue, VerificationFinding, ordered_findings,
)
from f1_eras.verification.metadata import ExpectedStandings, PopulationCoverage


_MISMATCH_CODES = frozenset({
    FindingCode.MISSING_DRIVER, FindingCode.UNEXPECTED_DRIVER,
    FindingCode.POINTS_MISMATCH, FindingCode.POSITION_MISMATCH,
    FindingCode.CLASSIFICATION_MISMATCH,
})


def compare_standings(
    reconstructed: tuple[StandingValue, ...], expected: ExpectedStandings,
) -> StandingComparison:
    """Compare sporting values by identity; input/display order has no meaning."""
    findings: list[VerificationFinding] = []
    expected_rows = tuple(row.standing for row in expected.rows)
    if expected.population != PopulationCoverage.COMPLETE or not expected_rows:
        findings.append(VerificationFinding(
            FindingCode.POPULATION_INCOMPLETE, "A nonempty complete final classification is required",
        ))
    duplicates = False
    for label, rows in (("expected", expected_rows), ("reconstructed", reconstructed)):
        for driver_id, count in sorted(Counter(row.driver_id for row in rows).items()):
            if count > 1:
                duplicates = True
                findings.append(VerificationFinding(
                    FindingCode.METADATA_INVALID if label == "expected" else FindingCode.SOURCE_DATA_INCONSISTENT,
                    f"Duplicate {label} driver; no row may overwrite another", driver_id,
                ))
        positions: dict[int, list[StandingValue]] = {}
        for row in rows:
            ranked = row.classification in (ClassificationState.RANKED, ClassificationState.TIED)
            if (row.points is None or row.classification == ClassificationState.UNKNOWN
                    or ranked != (row.position is not None)):
                findings.append(VerificationFinding(
                    FindingCode.EXPECTED_INFORMATION_INCOMPLETE if label == "expected"
                    else FindingCode.SOURCE_DATA_INCONSISTENT,
                    f"{label} points, position or classification are incomplete/inconsistent", row.driver_id,
                ))
            if row.position is not None:
                positions.setdefault(row.position, []).append(row)
        for position, group in sorted(positions.items()):
            if (expected.population == PopulationCoverage.COMPLETE and len(group) == 1
                    and group[0].classification == ClassificationState.TIED):
                findings.append(VerificationFinding(
                    FindingCode.EXPECTED_INFORMATION_INCOMPLETE if label == "expected"
                    else FindingCode.SOURCE_DATA_INCONSISTENT,
                    f"{label} tied classification has no counterpart in complete population",
                    f"position:{position}",
                ))
            if len(group) > 1 and any(row.classification != ClassificationState.TIED for row in group):
                findings.append(VerificationFinding(
                    FindingCode.EXPECTED_INFORMATION_INCOMPLETE if label == "expected"
                    else FindingCode.SOURCE_DATA_INCONSISTENT,
                    f"{label} duplicate sporting position lacks explicit tied classification",
                    f"position:{position}",
                ))
    if not duplicates:
        actual_by_id = {row.driver_id: row for row in reconstructed}
        expected_by_id = {row.driver_id: row for row in expected_rows}
        for driver_id in sorted(expected_by_id.keys() - actual_by_id.keys()):
            findings.append(VerificationFinding(
                FindingCode.MISSING_DRIVER, "Expected classified driver is absent from reconstruction", driver_id,
            ))
        if expected.population == PopulationCoverage.COMPLETE:
            for driver_id in sorted(actual_by_id.keys() - expected_by_id.keys()):
                findings.append(VerificationFinding(
                    FindingCode.UNEXPECTED_DRIVER, "Reconstructed classified driver is outside complete expectation",
                    driver_id,
                ))
        for driver_id in sorted(expected_by_id.keys() & actual_by_id.keys()):
            wanted, actual = expected_by_id[driver_id], actual_by_id[driver_id]
            for field, code in (("points", FindingCode.POINTS_MISMATCH),
                                ("position", FindingCode.POSITION_MISMATCH),
                                ("classification", FindingCode.CLASSIFICATION_MISMATCH)):
                left, right = getattr(wanted, field), getattr(actual, field)
                if field == "points" and left is None:
                    continue
                if field == "classification" and left == ClassificationState.UNKNOWN:
                    continue
                if left != right:
                    findings.append(VerificationFinding(
                        code, f"Exact {field} differs", driver_id, field,
                        str(left) if left is not None else None,
                        str(right) if right is not None else None,
                    ))
    outcome = ComparisonOutcome.MATCH
    if any(item.code in _MISMATCH_CODES for item in findings):
        outcome = ComparisonOutcome.MISMATCH
    elif findings:
        outcome = ComparisonOutcome.INCOMPLETE
    return StandingComparison(outcome, ordered_findings(findings))
