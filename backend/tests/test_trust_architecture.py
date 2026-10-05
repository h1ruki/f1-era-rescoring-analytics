"""Repository binding, optional audit failures and snapshot approval regressions."""

from dataclasses import replace
import hashlib
import sqlite3
from contextlib import closing
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from f1_eras.analytics.original_drivers import CalculationUnavailable
from f1_eras.api.http import create_app
from f1_eras.application.championships import ChampionshipService
from f1_eras.data_access import f1db
from f1_eras.data_access.connection import SourceDatabaseError, SourceSnapshotChanged
from f1_eras.data_access.f1db import F1DBRepository
from f1_eras.domain.verification import AssessmentState, ComparisonOutcome, FindingCode, ReconstructionOutcome
from f1_eras.verification import approval, external_audit
from f1_eras.verification.approval import load_snapshot_approval
from f1_eras.verification.diagnostic import diagnose_baseline


YEARS = (2010, 2011, 2012, 2013)


@pytest.mark.integration
@pytest.mark.parametrize("failure", ("missing", "unreadable", "malformed", "shape", "types", "duplicate"))
def test_optional_audit_failure_never_blocks_canonical_api(project_source_db, monkeypatch, failure):
    original = Path.read_text

    def audit_read(path, *args, **kwargs):
        if path != external_audit.AUDIT_PATH:
            return original(path, *args, **kwargs)
        if failure == "missing":
            raise FileNotFoundError(path)
        if failure == "unreadable":
            raise PermissionError(path)
        return {"malformed": "[", "shape": '[{"year":2010}]',
                "types": '[null]', "duplicate": '{"year":2010,"year":2011}'}[failure]

    monkeypatch.setattr(Path, "read_text", audit_read)
    client = TestClient(create_app(ChampionshipService(F1DBRepository(project_source_db))))
    response = client.get("/api/v1/championship-margins")
    assert response.status_code == 200
    for row in response.json()["results"]:
        assert row["availability"] == "available"
        assert row["trust"]["trusted_for_normal_use"]
        assert row["trust"]["external_audit"] is None
        assert row["trust"]["external_audit_status"] == ("unavailable" if failure == "missing" else "invalid")


@pytest.mark.integration
def test_existing_2010_audit_cannot_override_failed_canonical_reconciliation(project_source_db):
    class ConflictingSource(F1DBRepository):
        def read_original_drivers_source(self, year):
            source = super().read_original_drivers_source(year)
            first = source.recorded[0]
            return replace(source, recorded=(replace(first, recorded_points=first.recorded_points + 1),) + source.recorded[1:])

    service = ChampionshipService(ConflictingSource(project_source_db))
    report = service.original_drivers(2010)
    assert report.trust.external_audit is not None
    assert report.trust.comparison == ComparisonOutcome.MISMATCH
    assert not report.trust.trusted_for_normal_use
    assert isinstance(report.result, CalculationUnavailable)
    body = TestClient(create_app(service)).get("/api/v1/championships/2010").json()
    assert body["champion"] is body["runner_up"] is body["margin"] is None
    assert "standings" not in body
    assert report.calculation_diagnostics.driver_count == 27
    assert report.calculation_diagnostics.standing_difference_count > 0


@pytest.mark.integration
@pytest.mark.parametrize("document", (None, "{", "{}", '{"sha256":"a"}',
    '{"upstream_release":"v1.0.0","upstream_release_commit":"bad","sha256":"bad","size_bytes":true}'))
def test_missing_or_invalid_approval_fails_closed(project_source_db, monkeypatch, tmp_path, document):
    path = tmp_path / "approval.json"
    if document is not None:
        path.write_text(document, encoding="utf-8")
    monkeypatch.setattr(approval, "MANIFEST_PATH", path)
    report = ChampionshipService(F1DBRepository(project_source_db)).original_drivers(2010)
    assert report.trust.state == AssessmentState.BLOCKED
    assert not report.trust.trusted_for_normal_use
    assert {FindingCode.METADATA_INVALID, FindingCode.CANONICAL_DATASET_REQUIRED} <= {f.code for f in report.trust.findings}
    assert report.calculation_diagnostics.driver_count == 27


@pytest.mark.integration
def test_population_is_queried_independently_of_comparison_reader(project_source_db, monkeypatch):
    original = f1db._BoundF1DBReader.get_recorded_driver_standings
    monkeypatch.setattr(f1db._BoundF1DBReader, "get_recorded_driver_standings", lambda self, year: original(self, year)[:-1])
    source = F1DBRepository(project_source_db).read_original_drivers_source(2012)
    assert len(source.population.driver_ids) == len(source.recorded) + 1
    report = ChampionshipService(F1DBRepository(project_source_db)).original_drivers(2012)
    assert not report.trust.trusted_for_normal_use


@pytest.mark.integration
def test_source_change_between_reads_is_stale_and_never_published(project_source_db, monkeypatch):
    repository = F1DBRepository(project_source_db)
    original = f1db._BoundF1DBReader.get_season_events
    changed = replace(repository.identify_snapshot(), sha256="a" * 64)

    def during_read(reader, year):
        monkeypatch.setattr(repository, "identify_snapshot", lambda: changed)
        return original(reader, year)

    monkeypatch.setattr(f1db._BoundF1DBReader, "get_season_events", during_read)
    report = ChampionshipService(repository).original_drivers(2012)
    assert report.trust.state == AssessmentState.STALE
    assert report.trust.reconstruction == ReconstructionOutcome.COMPLETED
    assert report.calculation_diagnostics.award_count == 480
    assert not report.trust.trusted_for_normal_use
    assert isinstance(report.result, CalculationUnavailable)


@pytest.mark.integration
def test_operational_integrity_failure_is_error_not_unavailable(project_source_db, monkeypatch):
    repository = F1DBRepository(project_source_db)

    def broken_integrity(connection):
        raise SourceDatabaseError("Injected source integrity failure")

    monkeypatch.setattr(f1db, "validate_required_schema", broken_integrity)
    with pytest.raises(SourceDatabaseError, match="integrity"):
        ChampionshipService(repository).original_drivers(2010)
    client = TestClient(create_app(ChampionshipService(repository)), raise_server_exceptions=False)
    assert client.get("/api/v1/championships/2010").status_code == 500


@pytest.mark.integration
def test_capture_change_is_stale_not_operational_error(project_source_db, monkeypatch):
    repository = F1DBRepository(project_source_db)

    def changed(year):
        raise SourceSnapshotChanged("Injected capture replacement")

    monkeypatch.setattr(repository, "read_original_drivers_source", changed)
    report = ChampionshipService(repository).original_drivers(2010)
    assert report.trust.state == AssessmentState.STALE
    assert report.trust.reconstruction == ReconstructionOutcome.NOT_ATTEMPTED
    assert report.trust.f1db_sha256 is None
    assert report.calculation_diagnostics is None


@pytest.fixture
def candidate_db(project_source_db):
    path = project_source_db.parent / "data" / "f1db_newsnapshot.db"
    if not path.is_file():
        pytest.skip("Optional local candidate snapshot is absent")
    return path


@pytest.mark.integration
def test_candidate_withheld_and_completed_diagnostics_preserved(project_source_db, candidate_db):
    before = hashlib.sha256(candidate_db.read_bytes()).hexdigest()
    candidate = F1DBRepository(candidate_db)
    canonical = F1DBRepository(project_source_db)
    assert not load_snapshot_approval().matches(candidate.identify_snapshot())
    client = TestClient(create_app(ChampionshipService(candidate)))
    for year in YEARS:
        old, new = canonical.read_original_drivers_source(year), candidate.read_original_drivers_source(year)
        assert (old.events, old.classifications, old.recorded) == (new.events, new.classifications, new.recorded)
        body = client.get(f"/api/v1/championships/{year}").json()
        assert body["availability"] == "unavailable"
        assert body["champion"] is body["runner_up"] is body["margin"] is None
        assert body["trust"]["state"] == "blocked"
        assert body["trust"]["comparison"] == "match"
        assert body["trust"]["reconstruction"] == "completed"
        assert not body["trust"]["canonical_dataset_backed"]
    diagnostics = diagnose_baseline(candidate_db)
    assert [(d.driver_count, d.award_count) for d in diagnostics] == [(27, 456), (28, 454), (25, 480), (23, 418)]
    assert all(d.f1db_award_difference_count == d.f1db_standing_difference_count == 0 for d in diagnostics)
    assert hashlib.sha256(candidate_db.read_bytes()).hexdigest() == before


@pytest.mark.integration
def test_aba_provenance_cannot_label_candidate_reads_as_approved(project_source_db, candidate_db, monkeypatch):
    # Initial/final on-disk provenance is A, but capture supplies B. The actual
    # captured bytes, rather than endpoint identity assertions, govern trust.
    original = Path.read_bytes
    image = candidate_db.read_bytes()
    monkeypatch.setattr(Path, "read_bytes", lambda path: image if path == project_source_db else original(path))
    report = ChampionshipService(F1DBRepository(project_source_db)).original_drivers(2012)
    assert report.source_snapshot.sha256 == hashlib.sha256(image).hexdigest()
    assert report.trust.state == AssessmentState.STALE
    assert not report.trust.canonical_dataset_backed
    assert not report.trust.trusted_for_normal_use


def test_all_assessment_queries_use_captured_image_even_if_file_changes(source_db, monkeypatch):
    repository = F1DBRepository(source_db)
    original = f1db._BoundF1DBReader.get_season_events

    def change_file_after_calendar(reader, year):
        events = original(reader, year)
        # This is the disposable synthetic fixture, never either real snapshot.
        with closing(sqlite3.connect(source_db)) as connection:
            connection.execute("UPDATE driver SET name = 'Replacement identity'")
            connection.commit()
        return events

    monkeypatch.setattr(f1db._BoundF1DBReader, "get_season_events", change_file_after_calendar)
    source = repository.read_original_drivers_source(2012)
    assert source.snapshot != source.current_snapshot
    assert source.classifications[0].driver.name == "Driver A"
    assert source.recorded[0].driver.name == "Driver A"
    assert repository.get_recorded_driver_standings(2012)[0].driver.name == "Replacement identity"


def test_corrupt_assessment_image_raises_database_error(source_db, monkeypatch):
    repository = F1DBRepository(source_db)
    image = bytearray(source_db.read_bytes())
    # Break the b-tree page header of the disposable fixture's schema table.
    image[100] = 0
    original = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda path: bytes(image) if path == source_db else original(path))
    with pytest.raises(sqlite3.DatabaseError):
        repository.read_original_drivers_source(2012)
