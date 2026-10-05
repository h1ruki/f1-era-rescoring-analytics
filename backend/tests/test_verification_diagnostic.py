"""Diagnostics and production share canonical trust; audit remains separate."""

from pathlib import Path

import pytest

from f1_eras.data_access.f1db import F1DBRepository
from f1_eras.domain.verification import (
    AssessmentState, ComparisonOutcome, FindingCode, ReconstructionOutcome,
)
from f1_eras.verification.diagnostic import diagnose_baseline
from f1_eras.verification import diagnostic
from f1_eras.application import championships


@pytest.mark.integration
def test_baseline_diagnostic_uses_canonical_trust(project_source_db: Path):
    repository = F1DBRepository(project_source_db)
    before = repository.identify_snapshot()
    diagnostics = diagnose_baseline(project_source_db)
    assert [item.assessment.year for item in diagnostics] == [2010, 2011, 2012, 2013]
    assert [(item.driver_count, item.award_count) for item in diagnostics] == [
        (27, 456), (28, 454), (25, 480), (23, 418),
    ]
    for item in diagnostics:
        assessment = item.assessment
        assert assessment.reconstruction == ReconstructionOutcome.COMPLETED
        assert assessment.comparison == ComparisonOutcome.MATCH
        assert assessment.state == AssessmentState.PASSED
        assert assessment.trusted_for_normal_use
        assert not assessment.findings
        assert (assessment.external_audit is not None) == (assessment.year == 2010)
        assert item.f1db_award_difference_count == item.f1db_standing_difference_count == 0
        assert assessment.f1db_sha256 == before.sha256
    assert repository.identify_snapshot() == before


@pytest.mark.integration
def test_diagnostic_errors_are_not_misreported_as_historical_gaps(project_source_db: Path, monkeypatch):
    def broken_calculation(*args, **kwargs):
        raise RuntimeError("SYNTHETIC injected calculation failure")

    monkeypatch.setattr(championships, "calculate_original_drivers", broken_calculation)
    diagnostics = diagnose_baseline(project_source_db)
    assert len(diagnostics) == 4
    for item in diagnostics:
        assert item.assessment.state == AssessmentState.ERROR
        assert item.assessment.reconstruction == ReconstructionOutcome.ERROR
        assert item.f1db_award_difference_count is None
        assert item.f1db_standing_difference_count is None
        assert FindingCode.ASSESSMENT_ERROR in {f.code for f in item.assessment.findings}


@pytest.mark.integration
def test_diagnostic_cli_emits_json_and_returns_nonzero_for_error(project_source_db: Path, monkeypatch, capsys):
    def broken_calculation(*args, **kwargs):
        raise RuntimeError("SYNTHETIC injected calculation failure")

    monkeypatch.setattr(championships, "calculate_original_drivers", broken_calculation)
    monkeypatch.setattr("sys.argv", ["diagnostic", "--db", str(project_source_db)])
    assert diagnostic.main() == 1
    import json
    output = json.loads(capsys.readouterr().out)
    assert [item["assessment"]["state"] for item in output] == ["error"] * 4
