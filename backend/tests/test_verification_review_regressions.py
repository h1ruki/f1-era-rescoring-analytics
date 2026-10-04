"""Adversarial regressions from foundation review; all data is synthetic."""

from dataclasses import fields, replace
from fractions import Fraction
from pathlib import Path

import pytest

from f1_eras.domain.verification import (
    AssessmentState, ClassificationState, ComparisonOutcome, FindingCode,
    ReconstructionCheck, ReconstructionOutcome, StandingValue,
    VerificationContext, VerificationScope,
)
from f1_eras.verification.compare import compare_standings
from f1_eras.verification.evaluate import evaluate_verification
from f1_eras.verification.metadata import HistoricalMetadata, MetadataError, load_metadata, validate_metadata


SYNTHETIC_PATH = Path(__file__).parent / "fixtures" / "synthetic" / "drivers_original.json"
ROWS = (
    StandingValue("synthetic-alpha", Fraction(10), 1, ClassificationState.RANKED),
    StandingValue("synthetic-beta", Fraction(3, 2), 2, ClassificationState.RANKED),
    StandingValue("synthetic-gamma", Fraction(0), 3, ClassificationState.RANKED),
)


@pytest.fixture
def metadata():
    return load_metadata(SYNTHETIC_PATH)


def reconstruction(metadata, rows=ROWS):
    context = VerificationContext("a" * 64, metadata.content_sha256, metadata.rules_sha256, "b" * 40, False)
    return ReconstructionCheck(
        ReconstructionOutcome.COMPLETED, context, 9999, "synthetic-original", "synthetic-calculator-v1",
        rows, (1, 2), True, True,
    )


def assess(metadata, check, scope=VerificationScope.SYNTHETIC):
    return evaluate_verification(
        year=9999, package_id="synthetic-original", implementation_id="synthetic-calculator-v1",
        reconstruction=check, context=check.context, metadata=metadata, scope=scope,
    )


def codes(result):
    return {finding.code for finding in result.findings}


def test_replacing_scope_cannot_turn_synthetic_sources_into_historical_trust(metadata):
    check = reconstruction(metadata)
    forged = replace(metadata, scope=VerificationScope.HISTORICAL)
    result = assess(forged, check, VerificationScope.HISTORICAL)
    assert result.state == AssessmentState.BLOCKED
    assert FindingCode.METADATA_INVALID in codes(result)
    assert result.comparison == ComparisonOutcome.NOT_RUN
    assert not result.historically_verified
    with pytest.raises(MetadataError, match="scope must agree"):
        validate_metadata(forged)


@pytest.mark.parametrize("attack", [
    "missing_references", "dangling_source", "missing_reviewer", "dangling_claim",
    "duplicate_source", "duplicate_claim", "duplicate_provision",
])
def test_direct_construction_cannot_bypass_evidence_relationships(metadata, attack):
    values = {field.name: getattr(metadata, field.name) for field in fields(metadata)}
    first = metadata.claims[0]
    if attack == "missing_references":
        values["claims"] = (replace(first, references=()),) + metadata.claims[1:]
    elif attack == "dangling_source":
        values["claims"] = (replace(first, references=(replace(first.references[0], source_id="absent"),)),) + metadata.claims[1:]
    elif attack == "missing_reviewer":
        values["claims"] = (replace(first, reviewed_by=None),) + metadata.claims[1:]
    elif attack == "dangling_claim":
        values["expected"] = replace(metadata.expected, evidence_ids=("absent",))
    elif attack == "duplicate_source":
        values["sources"] += (metadata.sources[0],)
    elif attack == "duplicate_claim":
        values["claims"] += (first,)
    else:
        values["rules"] = replace(metadata.rules, provisions=metadata.rules.provisions + (metadata.rules.provisions[0],))
    forged = HistoricalMetadata(**values)
    with pytest.raises(MetadataError):
        validate_metadata(forged)
    with pytest.raises(MetadataError):
        _ = forged.content_sha256
    result = assess(forged, reconstruction(metadata))
    assert result.state == AssessmentState.BLOCKED
    assert FindingCode.METADATA_INVALID in codes(result)
    assert not result.historically_verified


def test_changed_matching_totals_cannot_retain_original_metadata_binding(metadata):
    check = reconstruction(metadata)
    changed_driver = replace(metadata.expected.rows[1], standing=replace(ROWS[1], points=Fraction(2)))
    changed = replace(metadata, expected=replace(
        metadata.expected, rows=(metadata.expected.rows[0], changed_driver, metadata.expected.rows[2]),
    ))
    assert changed.content_sha256 != metadata.content_sha256
    assert changed.rules_sha256 == metadata.rules_sha256
    check = replace(check, standings=(ROWS[0], replace(ROWS[1], points=Fraction(2)), ROWS[2]))
    result = assess(changed, check)
    assert result.comparison == ComparisonOutcome.MATCH
    assert result.state == AssessmentState.STALE
    assert FindingCode.CONTEXT_STALE in codes(result)
    assert not result.historically_verified


def test_package_body_changes_derive_a_new_rules_hash(metadata):
    changed = replace(metadata, rules=replace(metadata.rules, implementation_id="synthetic-calculator-v2"))
    assert changed.rules_sha256 != metadata.rules_sha256
    assert changed.content_sha256 != metadata.content_sha256
    assert assess(changed, reconstruction(metadata)).state == AssessmentState.STALE


@pytest.mark.parametrize("name", ["content_sha256", "rules_sha256"])
def test_hashes_are_derived_not_constructor_fields(metadata, name):
    assert name not in {field.name for field in fields(HistoricalMetadata)}
    with pytest.raises(TypeError):
        replace(metadata, **{name: "f" * 64})


def test_direct_valid_construction_has_identical_validation_and_hashes(metadata):
    direct = HistoricalMetadata(**{field.name: getattr(metadata, field.name) for field in fields(metadata)})
    assert validate_metadata(direct) == metadata
    assert direct.content_sha256 == metadata.content_sha256
    assert assess(direct, reconstruction(metadata)).state == AssessmentState.PASSED


@pytest.mark.parametrize("field", ["source_checks_passed", "invariant_checks_passed"])
@pytest.mark.parametrize("value", [True, False, "true", "false", 1, 0])
def test_prerequisites_require_actual_booleans(metadata, field, value):
    check = reconstruction(metadata)
    if type(value) is not bool:
        with pytest.raises(ValueError, match="actual boolean"):
            replace(check, **{field: value})
    else:
        result = assess(metadata, replace(check, **{field: value}))
        assert result.state == (AssessmentState.PASSED if value else AssessmentState.BLOCKED)


@pytest.mark.parametrize("field", ["source_checks_passed", "invariant_checks_passed"])
@pytest.mark.parametrize("value", ["true", "false", 1, 0])
def test_evaluator_is_fail_closed_even_if_boolean_model_boundary_is_bypassed(metadata, field, value):
    check = reconstruction(metadata)
    object.__setattr__(check, field, value)  # Deliberate adversarial bypass of frozen dataclass.
    assert assess(metadata, check).state == AssessmentState.BLOCKED


@pytest.mark.parametrize("side", ["expected", "reconstructed", "both"])
def test_singleton_tie_never_passes_complete_population(metadata, side):
    expected = metadata.expected
    rows = ROWS
    if side in ("expected", "both"):
        tied = replace(expected.rows[1], standing=replace(ROWS[1], classification=ClassificationState.TIED))
        expected = replace(expected, rows=(expected.rows[0], tied, expected.rows[2]))
    if side in ("reconstructed", "both"):
        rows = (ROWS[0], replace(ROWS[1], classification=ClassificationState.TIED), ROWS[2])
    comparison = compare_standings(rows, expected)
    assert comparison.outcome != ComparisonOutcome.MATCH
    if side == "both":
        assert comparison.outcome == ComparisonOutcome.INCOMPLETE
        assert {FindingCode.EXPECTED_INFORMATION_INCOMPLETE, FindingCode.SOURCE_DATA_INCONSISTENT} <= {
            finding.code for finding in comparison.findings
        }
    changed = replace(metadata, expected=expected)
    assert assess(changed, reconstruction(changed, rows)).state == AssessmentState.BLOCKED


def test_unpassed_source_checks_do_not_claim_data_is_missing(metadata):
    result = assess(metadata, replace(reconstruction(metadata), source_checks_passed=False))
    assert result.state == AssessmentState.BLOCKED
    assert codes(result) == {FindingCode.SOURCE_CHECKS_NOT_PASSED}


def test_unknown_event_scope_is_missing_evidence_not_known_missing_source_data(metadata):
    unknown = replace(metadata, season=replace(metadata.season, event_ids=()))
    result = assess(unknown, reconstruction(unknown))
    assert result.state == AssessmentState.BLOCKED
    assert FindingCode.SEASON_EVIDENCE_MISSING in codes(result)
    assert FindingCode.SOURCE_DATA_MISSING not in codes(result)


def test_known_missing_required_event_reports_missing_source_data(metadata):
    result = assess(metadata, replace(reconstruction(metadata), event_ids=(1,)))
    assert result.state == AssessmentState.BLOCKED
    assert FindingCode.SOURCE_DATA_MISSING in codes(result)


def test_unattempted_source_read_does_not_prove_missing_data(metadata):
    check = replace(reconstruction(metadata), outcome=ReconstructionOutcome.NOT_ATTEMPTED,
                    event_ids=(), standings=(), source_checks_passed=False, invariant_checks_passed=False)
    result = assess(metadata, check)
    assert result.state == AssessmentState.BLOCKED
    assert FindingCode.SOURCE_CHECKS_NOT_PASSED in codes(result)
    assert FindingCode.SOURCE_DATA_MISSING not in codes(result)
    assert FindingCode.SOURCE_DATA_INCONSISTENT not in codes(result)


def test_success_terminology_and_derived_historical_trust(metadata):
    passed = assess(metadata, reconstruction(metadata))
    assert passed.state == AssessmentState.PASSED
    assert passed.state.value == "passed"
    assert {state.value for state in AssessmentState} == {"passed", "blocked", "stale", "error"}
    assert passed.historically_verified is False
    assert "historically_verified" not in {field.name for field in fields(passed)}
    with pytest.raises(TypeError):
        replace(passed, historically_verified=True)
    historical = assess(metadata, reconstruction(metadata), VerificationScope.HISTORICAL)
    assert historical.state == AssessmentState.BLOCKED
    assert historical.historically_verified is False
