"""Nonhistorical tests of verification policy, independent of the scoring engine."""

from dataclasses import replace
from fractions import Fraction
import json
from pathlib import Path

import pytest

from f1_eras.domain.verification import (
    AssessmentState, ClassificationState, ComparisonOutcome, FindingCode,
    ReconstructionCheck, ReconstructionOutcome, StandingValue,
    VerificationContext, VerificationFinding, VerificationScope,
)
from f1_eras.verification.compare import compare_standings
from f1_eras.verification.evaluate import evaluate_verification
from f1_eras.verification.metadata import load_metadata, parse_metadata


SYNTHETIC_PATH = Path(__file__).parent / "fixtures" / "synthetic" / "drivers_original.json"
# Independently written comparator inputs, not copied/generated from the oracle.
ROWS = (
    StandingValue("synthetic-alpha", Fraction(10), 1, ClassificationState.RANKED),
    StandingValue("synthetic-beta", Fraction(3, 2), 2, ClassificationState.RANKED),
    StandingValue("synthetic-gamma", Fraction(0), 3, ClassificationState.RANKED),
)


@pytest.fixture
def document():
    return json.loads(SYNTHETIC_PATH.read_text(encoding="utf-8"))


def evaluate(document, rows=ROWS, *, scope=VerificationScope.SYNTHETIC,
             reconstruction_changes=None, context_changes=None, previous_context=None):
    metadata = parse_metadata(json.dumps(document)) if document is not None else None
    context = VerificationContext(
        "a" * 64, metadata.content_sha256 if metadata else None,
        metadata.rules_sha256 if metadata else "b" * 64, "c" * 40, False,
    )
    reconstruction = ReconstructionCheck(
        ReconstructionOutcome.COMPLETED, context, 9999, "synthetic-original", "synthetic-calculator-v1",
        rows, (1, 2), True, True,
    )
    if reconstruction_changes:
        reconstruction = replace(reconstruction, **reconstruction_changes)
    if context_changes:
        context = replace(context, **context_changes)
    return evaluate_verification(
        year=9999, package_id="synthetic-original", implementation_id="synthetic-calculator-v1",
        reconstruction=reconstruction, context=context, metadata=metadata,
        scope=scope, previous_context=previous_context,
    )


def codes(assessment):
    return {finding.code for finding in assessment.findings}


def test_valid_synthetic_championship_passes_only_in_synthetic_scope(document):
    result = evaluate(document)
    assert result.state == AssessmentState.PASSED
    assert result.comparison == ComparisonOutcome.MATCH
    assert result.findings == ()
    assert not result.historically_verified
    historical = evaluate(document, scope=VerificationScope.HISTORICAL)
    assert historical.state == AssessmentState.BLOCKED
    assert FindingCode.SYNTHETIC_EVIDENCE in codes(historical)
    assert not historical.historically_verified


def test_historical_scope_is_default_and_never_accepts_synthetic_bundle():
    metadata = load_metadata(SYNTHETIC_PATH)
    context = VerificationContext("a" * 64, metadata.content_sha256, metadata.rules_sha256, "c" * 40, False)
    result = evaluate_verification(
        year=9999, package_id="synthetic-original", implementation_id="synthetic-calculator-v1",
        reconstruction=ReconstructionCheck(
            ReconstructionOutcome.COMPLETED, context, 9999, "synthetic-original", "synthetic-calculator-v1",
            ROWS, (1, 2), True, True,
        ),
        context=context, metadata=metadata,
    )
    assert result.scope == VerificationScope.HISTORICAL
    assert result.state == AssessmentState.BLOCKED


@pytest.mark.parametrize("points", [Fraction(2), Fraction(15000000000000001, 10000000000000000)])
def test_correct_champion_but_wrong_lower_points_blocks_exactly(document, points):
    result = evaluate(document, (ROWS[0], replace(ROWS[1], points=points), ROWS[2]))
    assert result.state == AssessmentState.BLOCKED
    assert result.comparison == ComparisonOutcome.MISMATCH
    difference = next(f for f in result.findings if f.code == FindingCode.POINTS_MISMATCH)
    assert difference.subject == "synthetic-beta"
    assert difference.expected == "3/2" and difference.actual == str(points)


def test_missing_expected_evidence_blocks_even_successful_reconstruction(document):
    document["expected"] = None
    result = evaluate(document)
    assert result.state == AssessmentState.BLOCKED
    assert result.reconstruction == ReconstructionOutcome.COMPLETED
    assert result.comparison == ComparisonOutcome.NOT_RUN
    assert FindingCode.EXPECTED_EVIDENCE_MISSING in codes(result)


def test_missing_classified_zero_point_driver_blocks(document):
    result = evaluate(document, ROWS[:2])
    assert result.state == AssessmentState.BLOCKED
    assert FindingCode.MISSING_DRIVER in codes(result)


def test_unexpected_classified_driver_blocks_complete_population(document):
    result = evaluate(document, ROWS + (
        StandingValue("synthetic-extra", Fraction(0), 4, ClassificationState.RANKED),
    ))
    assert result.state == AssessmentState.BLOCKED
    assert FindingCode.UNEXPECTED_DRIVER in codes(result)


@pytest.mark.parametrize("change,code", [
    ({"position": 3}, FindingCode.POSITION_MISMATCH),
    ({"position": None, "classification": ClassificationState.EXCLUDED}, FindingCode.CLASSIFICATION_MISMATCH),
])
def test_sporting_order_and_classification_mismatches_block(document, change, code):
    result = evaluate(document, (ROWS[0], replace(ROWS[1], **change), ROWS[2]))
    assert result.state == AssessmentState.BLOCKED
    assert code in codes(result)


@pytest.mark.parametrize("field,value", [("points", None), ("position", None), ("classification", "unknown")])
def test_incomplete_expected_values_cannot_match(document, field, value):
    document["expected"]["rows"][1][field] = value
    result = evaluate(document)
    assert result.state == AssessmentState.BLOCKED
    assert FindingCode.EXPECTED_INFORMATION_INCOMPLETE in codes(result)


def test_multiple_blockers_are_preserved(document):
    document["rules"] = None
    document["season"]["material_ambiguities"] = ["SYNTHETIC eligibility dispute"]
    result = evaluate(document, (ROWS[0], replace(ROWS[1], points=Fraction(7))))
    assert result.state == AssessmentState.BLOCKED
    assert {FindingCode.RULE_EVIDENCE_MISSING, FindingCode.HISTORICAL_AMBIGUITY,
            FindingCode.POINTS_MISMATCH, FindingCode.MISSING_DRIVER} <= codes(result)


@pytest.mark.parametrize("field,value", [
    ("f1db_sha256", "d" * 64), ("metadata_sha256", "e" * 64),
    ("rules_sha256", "f" * 64), ("implementation_commit", "d" * 40),
    ("policy_version", "future-policy"), ("schema_version", 2),
])
def test_changed_context_cannot_remain_passed(document, field, value):
    result = evaluate(document, context_changes={field: value})
    assert result.state == AssessmentState.STALE
    assert FindingCode.CONTEXT_STALE in codes(result)
    assert not result.historically_verified


def test_previous_assessment_requires_fresh_evaluation_after_change(document):
    previous = evaluate(document).context
    document["claims"][0]["summary"] += " Revised SYNTHETIC specification."
    stale = evaluate(document, previous_context=previous)
    assert stale.state == AssessmentState.STALE
    assert evaluate(document).state == AssessmentState.PASSED


def test_row_order_does_not_change_comparison(document):
    rows = (ROWS[0], replace(ROWS[1], points=Fraction(7)))
    expected = parse_metadata(json.dumps(document)).expected
    assert expected is not None
    first = compare_standings(rows, expected)
    second = compare_standings(tuple(reversed(rows)), replace(expected, rows=tuple(reversed(expected.rows))))
    assert first == second


def test_partial_population_and_empty_complete_population_never_verify(document):
    document["expected"]["population"] = "partial"
    assert FindingCode.POPULATION_INCOMPLETE in codes(evaluate(document))
    document["expected"]["population"] = "complete"
    document["expected"]["rows"] = []
    assert evaluate(document, ()).state == AssessmentState.BLOCKED


def test_duplicate_reconstructed_driver_is_not_overwritten(document):
    result = evaluate(document, ROWS + (ROWS[1],))
    assert result.state == AssessmentState.BLOCKED
    assert FindingCode.SOURCE_DATA_INCONSISTENT in codes(result)


@pytest.mark.parametrize("independence", ["f1db", "reconstruction", "unknown"])
def test_circular_or_unknown_expected_lineage_blocks(document, independence):
    document["expected"]["independence"] = independence
    assert FindingCode.EXPECTED_NOT_INDEPENDENT in codes(evaluate(document))


@pytest.mark.parametrize("review,code", [
    ("draft", FindingCode.EVIDENCE_NOT_ACCEPTED),
    ("superseded", FindingCode.EVIDENCE_NOT_ACCEPTED),
    ("disputed", FindingCode.EVIDENCE_CONFLICT),
])
def test_unaccepted_and_disputed_claims_block(document, review, code):
    document["claims"][0]["review"] = review
    assert code in codes(evaluate(document))


def test_missing_rule_topic_and_wrong_applicability_block(document):
    document["rules"]["provisions"].pop()
    document["claims"][0]["applicable_years"] = [9998]
    result = evaluate(document)
    assert result.state == AssessmentState.BLOCKED
    assert FindingCode.RULE_EVIDENCE_MISSING in codes(result)


@pytest.mark.parametrize("field,value,code", [
    ("completion", "incomplete", FindingCode.SEASON_NOT_COMPLETE),
    ("completion", "unknown", FindingCode.SEASON_NOT_COMPLETE),
    ("event_ids", [1], FindingCode.SOURCE_DATA_INCONSISTENT),
    ("amendment_evidence", [], FindingCode.SEASON_EVIDENCE_MISSING),
])
def test_completion_event_population_and_amendment_review_are_required(document, field, value, code):
    document["season"][field] = value
    assert code in codes(evaluate(document))


def test_nonmaterial_participant_diagnostic_is_not_automatic_blocker(document):
    finding = VerificationFinding(FindingCode.PARTICIPANT_DIAGNOSTIC,
                                  "SYNTHETIC absent entrant has no material classification impact")
    result = evaluate(document, reconstruction_changes={"findings": (finding,)})
    assert result.state == AssessmentState.PASSED
    assert finding in result.findings
    material = replace(finding, code=FindingCode.HISTORICAL_AMBIGUITY)
    assert evaluate(document, reconstruction_changes={"findings": (material,)}).state == AssessmentState.BLOCKED


@pytest.mark.parametrize("outcome,state", [
    (ReconstructionOutcome.NOT_ATTEMPTED, AssessmentState.BLOCKED),
    (ReconstructionOutcome.UNAVAILABLE, AssessmentState.BLOCKED),
    (ReconstructionOutcome.ERROR, AssessmentState.ERROR),
])
def test_reconstruction_failures_cannot_pass(document, outcome, state):
    result = evaluate(document, reconstruction_changes={"outcome": outcome})
    assert result.state == state
    assert result.comparison == ComparisonOutcome.NOT_RUN


@pytest.mark.parametrize("field", ["source_checks_passed", "invariant_checks_passed"])
def test_unchecked_prerequisites_block(document, field):
    assert evaluate(document, reconstruction_changes={field: False}).state == AssessmentState.BLOCKED


def test_dirty_or_unknown_implementation_is_non_reproducible(document):
    for change in ({"working_tree_dirty": True}, {"implementation_commit": None}):
        result = evaluate(document, context_changes=change)
        assert FindingCode.NON_REPRODUCIBLE in codes(result)
        assert result.state != AssessmentState.PASSED


def test_explicit_ties_and_exclusions_are_compared_without_inventing_order(document):
    for row in document["expected"]["rows"][:2]:
        row.update(position=1, classification="tied", points={"numerator": 10, "denominator": 1})
    document["expected"]["rows"][2].update(position=None, classification="excluded")
    rows = (replace(ROWS[0], classification=ClassificationState.TIED),
            replace(ROWS[1], points=Fraction(10), position=1, classification=ClassificationState.TIED),
            replace(ROWS[2], position=None, classification=ClassificationState.EXCLUDED))
    assert evaluate(document, rows).state == AssessmentState.PASSED


@pytest.mark.parametrize("change", [
    {"year": 9998}, {"package_id": "another-package"}, {"implementation_id": "another-implementation"},
])
def test_reconstruction_is_bound_to_requested_season_and_package(document, change):
    result = evaluate(document, reconstruction_changes=change)
    assert result.state == AssessmentState.BLOCKED
    assert FindingCode.METADATA_INVALID in codes(result)


def test_dirty_context_is_blocked_even_when_all_contexts_match(document):
    clean = evaluate(document).context
    dirty = replace(clean, working_tree_dirty=True)
    result = evaluate(document, reconstruction_changes={"context": dirty},
                      context_changes={"working_tree_dirty": True})
    assert result.state == AssessmentState.BLOCKED
    assert codes(result) == {FindingCode.NON_REPRODUCIBLE}


def test_unimplemented_capability_and_errors_preserve_other_findings(document):
    document["expected"] = None
    result = evaluate(document, reconstruction_changes={"findings": (
        VerificationFinding(FindingCode.CAPABILITY_UNIMPLEMENTED, "SYNTHETIC missing operation"),
        VerificationFinding(FindingCode.ASSESSMENT_ERROR, "SYNTHETIC operational error"),
    )})
    assert result.state == AssessmentState.ERROR
    assert {FindingCode.CAPABILITY_UNIMPLEMENTED, FindingCode.ASSESSMENT_ERROR,
            FindingCode.EXPECTED_EVIDENCE_MISSING} <= codes(result)
