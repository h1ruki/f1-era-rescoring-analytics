"""Normal-use trust without dossiers; fail-closed mutations stay in memory."""

from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from f1_eras.analytics.original_drivers import (
    CalculationUnavailable, OriginalDriversChampionship, calculate_original_drivers,
    original_drivers_rules,
)
from f1_eras.api.http import create_app
from f1_eras.application.championships import ChampionshipService
from f1_eras.data_access.f1db import F1DBRepository
from f1_eras.domain.verification import AssessmentState, ComparisonOutcome, FindingCode
from f1_eras.verification import canonical, external_audit
from f1_eras.verification.canonical import assess_canonical_original


@pytest.fixture(params=(2010, 2011, 2012, 2013))
def inputs(project_source_db: Path, request):
    repository = F1DBRepository(project_source_db)
    source = repository.read_original_drivers_source(request.param)
    return {
        "year": request.param, "snapshot": source.snapshot, "current_snapshot": source.current_snapshot,
        "events": source.events, "classifications": source.classifications, "recorded": source.recorded,
        "population": source.population,
    }


def assess(inputs, **changes):
    values = {**inputs, **changes}
    result = values.pop("result", None)
    if result is None:
        result = calculate_original_drivers(values["year"], values["events"], values["classifications"], values["recorded"])
    return assess_canonical_original(**values, result=result)


def codes(assessment):
    return {finding.code for finding in assessment.findings}


@pytest.mark.integration
@pytest.mark.parametrize("year", (2010, 2011, 2012, 2013))
def test_same_service_path_trusts_every_season_without_external_evidence(project_source_db, monkeypatch, year):
    # Even the exemplar's supplementary summary may be absent; no dossier or
    # independent fixture is supplied to the canonical assessment at all.
    monkeypatch.setattr(external_audit, "AUDIT_PATH", project_source_db.parent / "missing-audit.json")
    report = ChampionshipService(F1DBRepository(project_source_db)).original_drivers(year)
    assert isinstance(report.result, OriginalDriversChampionship)
    assert report.trust.canonical_dataset_backed
    assert report.trust.comparison == ComparisonOutcome.MATCH
    assert report.trust.state == AssessmentState.PASSED
    assert report.trust.trusted_for_normal_use
    assert report.trust.external_audit is None
    assert report.trust.findings == ()


@pytest.mark.integration
def test_api_keeps_previous_exemplar_audit_separate_from_current_reconciliation(project_source_db):
    client = TestClient(create_app(ChampionshipService(F1DBRepository(project_source_db))))
    results = client.get("/api/v1/championship-margins").json()["results"]
    assert all(item["trust"]["trusted_for_normal_use"] for item in results)
    # The preserved audit is evidence about the previous snapshot, not an audit
    # automatically extended to the newly approved release.
    exemplar = json.loads(external_audit.AUDIT_PATH.read_text(encoding="utf-8"))[0]
    assert exemplar["year"] == 2010
    assert exemplar["decision_record"] == (
        "docs/decisions/HISTORICAL_DATA_TRUST_DECISION_RECORD.md"
        "#completed-2010-independent-historical-audit"
    )
    assert "provisional classification" in exemplar["qualification"]
    assert "unknown" in exemplar["qualification"]
    assert exemplar["f1db_sha256"] != results[0]["source_snapshot"]["sha256"]
    assert all(item["trust"]["external_audit"] is None for item in results)
    assert all(item["trust"]["external_audit_status"] == "unavailable" for item in results)
    assert "historically_verified" not in results[0]["trust"]


@pytest.mark.integration
@pytest.mark.parametrize("mutation,expected_code", [
    ("points", FindingCode.POINTS_MISMATCH),
    ("position", FindingCode.POSITION_MISMATCH),
    ("population", FindingCode.POPULATION_INCOMPLETE),
    ("duplicate", FindingCode.METADATA_INVALID),
    ("classification", FindingCode.EXPECTED_INFORMATION_INCOMPLETE),
    ("champion", FindingCode.SOURCE_DATA_INCONSISTENT),
    ("source_year", FindingCode.SOURCE_DATA_INCONSISTENT),
])
def test_canonical_full_standing_reconciliation_fails_closed(inputs, mutation, expected_code):
    rows = inputs["recorded"]
    first = rows[0]
    if mutation == "points":
        rows = (replace(first, recorded_points=first.recorded_points + Decimal(1)),) + rows[1:]
    elif mutation == "position":
        rows = (replace(first, position_number=2, position_text="2"),) + rows[1:]
    elif mutation == "population":
        rows = rows[:-1]
    elif mutation == "duplicate":
        rows += (rows[-1],)
    elif mutation == "classification":
        rows = (replace(first, position_number=None, position_text="DSQ"),) + rows[1:]
    elif mutation == "champion":
        rows = (replace(first, championship_won=False),) + rows[1:]
    else:
        rows = (replace(first, source_key=replace(first.source_key, year=inputs["year"] + 1)),) + rows[1:]
    assessment = assess(inputs, recorded=rows)
    assert not assessment.trusted_for_normal_use
    assert assessment.state == AssessmentState.BLOCKED
    assert expected_code in codes(assessment)


@pytest.mark.integration
def test_service_and_api_withhold_mismatched_results(inputs, project_source_db):
    repository = F1DBRepository(project_source_db)

    class MismatchedStandings:
        def read_original_drivers_source(self, year):
            source = repository.read_original_drivers_source(year)
            rows = source.recorded
            return replace(source, recorded=(replace(rows[0], recorded_points=rows[0].recorded_points + Decimal(1)),) + rows[1:])

    service = ChampionshipService(MismatchedStandings())
    report = service.original_drivers(2012)
    assert isinstance(report.result, CalculationUnavailable)
    assert report.trust.canonical_dataset_backed
    assert report.trust.comparison == ComparisonOutcome.MISMATCH
    body = TestClient(create_app(service)).get("/api/v1/championships/2012").json()
    assert body["availability"] == "unavailable"
    assert body["champion"] is body["runner_up"] is body["margin"] is None
    assert not body["trust"]["trusted_for_normal_use"]
    assert "standings" not in body


@pytest.mark.integration
@pytest.mark.parametrize("mutation,expected_code", [
    ("unknown_gp", FindingCode.HISTORICAL_AMBIGUITY),
    ("shared_drive", FindingCode.CAPABILITY_UNIMPLEMENTED),
    ("unknown_shared_drive", FindingCode.HISTORICAL_AMBIGUITY),
    ("sprint", FindingCode.CAPABILITY_UNIMPLEMENTED),
    ("missing_event", FindingCode.RECONSTRUCTION_UNAVAILABLE),
    ("duplicate_event", FindingCode.RECONSTRUCTION_UNAVAILABLE),
    ("event_award", FindingCode.POINTS_MISMATCH),
])
def test_integrity_and_unsupported_interpretations_cannot_be_excused_by_matching_standings(inputs, mutation, expected_code):
    events, rows = inputs["events"], inputs["classifications"]
    if mutation == "unknown_gp":
        index = next(i for i, row in enumerate(rows) if row.position_number is None)
        rows = rows[:index] + (replace(rows[index], position_text="UNKN"),) + rows[index + 1:]
    elif mutation == "shared_drive":
        rows = (replace(rows[0], shared_car=True),) + rows[1:]
    elif mutation == "unknown_shared_drive":
        rows = (replace(rows[0], shared_car=None),) + rows[1:]
    elif mutation == "sprint":
        events = (replace(events[0], sprint_race_date=events[0].date),) + events[1:]
    elif mutation == "missing_event":
        rows = tuple(row for row in rows if row.source_key.race_id != events[-1].race_id)
    elif mutation == "duplicate_event":
        events += (events[-1],)
    else:
        rows = (replace(rows[0], recorded_points=Decimal(24)),) + rows[1:]
    assessment = assess(inputs, events=events, classifications=rows)
    assert assessment.state == AssessmentState.BLOCKED
    assert not assessment.trusted_for_normal_use
    assert expected_code in codes(assessment)


@pytest.mark.integration
def test_unresolved_countback_stays_unavailable(inputs):
    # Two equally scoring drivers with identical finish counts cannot gain an
    # invented sporting ordering from canonical reconciliation.
    rows = inputs["classifications"]
    first, second = rows[:2]
    rows = (replace(first, position_number=None, position_text="DNF", recorded_points=None),
            replace(second, position_number=None, position_text="DNF", recorded_points=None))
    assessment = assess(inputs, events=inputs["events"][:1], classifications=rows)
    assert not assessment.trusted_for_normal_use
    assert FindingCode.RECONSTRUCTION_UNAVAILABLE in codes(assessment)
    assert any("Countback" in finding.message for finding in assessment.findings)


@pytest.mark.integration
@pytest.mark.parametrize("field", ("raw_points_gap", "percentage_gap", "finish_counts", "contributions", "awards"))
def test_internal_invariant_failures_block_even_when_standings_match(inputs, field):
    result = calculate_original_drivers(inputs["year"], inputs["events"], inputs["classifications"], inputs["recorded"])
    assert isinstance(result, OriginalDriversChampionship)
    if field in ("raw_points_gap", "percentage_gap"):
        result = replace(result, **{field: Fraction(999)})
    elif field == "awards":
        result = replace(result, event_awards=result.event_awards[:-1])
    else:
        last = result.standings[-1]
        if field == "finish_counts":
            last = replace(last, finish_counts=(999,) + last.finish_counts[1:])
        else:
            last = replace(last, constructor_contributions=())
        result = replace(result, standings=result.standings[:-1] + (last,))
    assessment = assess(inputs, result=result)
    assert assessment.comparison == ComparisonOutcome.MATCH
    assert assessment.state == AssessmentState.BLOCKED
    expected_code = (FindingCode.SOURCE_DATA_INCONSISTENT if field == "awards"
                     else FindingCode.INVARIANTS_UNCHECKED)
    assert expected_code in codes(assessment)


@pytest.mark.integration
def test_unapproved_or_changed_dataset_cannot_confer_trust(inputs):
    changed = replace(inputs["snapshot"], sha256="a" * 64)
    not_canonical = assess(inputs, snapshot=changed, current_snapshot=changed,
                           population=replace(inputs["population"], f1db_sha256=changed.sha256))
    assert not_canonical.comparison == ComparisonOutcome.MATCH
    assert not_canonical.state == AssessmentState.BLOCKED
    assert FindingCode.CANONICAL_DATASET_REQUIRED in codes(not_canonical)
    assert not not_canonical.trusted_for_normal_use
    stale = assess(inputs, current_snapshot=changed)
    assert stale.state == AssessmentState.STALE
    assert not stale.trusted_for_normal_use


@pytest.mark.integration
def test_generic_adapter_has_no_season_whitelist_or_season_specific_trust_requirements(inputs, monkeypatch):
    # Synthetic in-memory future package registration tests the adapter, without
    # adding production scoring support or claiming new historical coverage.
    result = calculate_original_drivers(inputs["year"], inputs["events"], inputs["classifications"], inputs["recorded"])
    assert isinstance(result, OriginalDriversChampionship)
    year = 2099
    rules = original_drivers_rules(inputs["year"])
    monkeypatch.setattr(canonical, "original_drivers_rules", lambda requested: rules if requested == year else None)
    values = {**inputs, "year": year,
              "events": tuple(replace(row, year=year) for row in inputs["events"]),
              "classifications": tuple(replace(row, year=year) for row in inputs["classifications"]),
              "recorded": tuple(replace(row, source_key=replace(row.source_key, year=year)) for row in inputs["recorded"]),
              "population": replace(inputs["population"], year=year)}
    result = replace(result, year=year, recorded_standings=values["recorded"])
    assessment = assess(values, result=result)
    assert assessment.trusted_for_normal_use
    assert assessment.external_audit is None


@pytest.mark.integration
@pytest.mark.parametrize("truncation", ("both", "reconstructed", "empty_comparison", "partial_comparison"))
def test_population_binding_rejects_matching_truncation_and_partial_comparisons(inputs, truncation):
    # Omit a ranked zero-point driver without hardcoding any season's roster.
    omitted = inputs["recorded"][-1]
    assert omitted.recorded_points == 0 and omitted.position_number is not None
    changes = {}
    if truncation in ("both", "reconstructed"):
        changes["classifications"] = tuple(row for row in inputs["classifications"] if row.driver.id != omitted.driver.id)
    if truncation in ("both", "partial_comparison"):
        changes["recorded"] = inputs["recorded"][:-1]
    if truncation == "empty_comparison":
        changes["recorded"] = ()
    assessment = assess(inputs, **changes)
    assert not assessment.trusted_for_normal_use
    assert FindingCode.POPULATION_INCOMPLETE in codes(assessment)
    if truncation != "reconstructed":
        assert assessment.comparison == ComparisonOutcome.INCOMPLETE


@pytest.mark.integration
def test_equal_points_cannot_replace_sporting_order_with_display_order(inputs):
    rows = inputs["recorded"]
    index = next(i for i in range(len(rows) - 1) if rows[i].recorded_points == rows[i + 1].recorded_points)
    first, second = rows[index:index + 2]
    changed = rows[:index] + (
        replace(first, position_number=second.position_number, position_text=second.position_text),
        replace(second, position_number=first.position_number, position_text=first.position_text),
    ) + rows[index + 2:]
    assessment = assess(inputs, recorded=changed)
    assert assessment.comparison == ComparisonOutcome.MISMATCH
    assert FindingCode.POSITION_MISMATCH in codes(assessment)
    assert not assessment.trusted_for_normal_use
