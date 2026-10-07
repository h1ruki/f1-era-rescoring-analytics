"""Deterministic teammate semantics and read-only current-slice integration."""

from dataclasses import replace
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
import pytest

from f1_eras.analytics.original_drivers import calculate_original_drivers, original_drivers_rules
from f1_eras.analytics.teammates import (
    TeammateDerivationAmbiguity,
    derive_teammate_context,
    genuinely_participated,
)
from f1_eras.api.http import create_app
from f1_eras.application.championships import ChampionshipReport, ChampionshipService
from f1_eras.data_access import f1db
from f1_eras.data_access.connection import SourceDatabaseError
from f1_eras.data_access.f1db import F1DBRepository
from f1_eras.domain.models import (
    ChampionshipCategory,
    ConstructorIdentity,
    DriverIdentity,
    DriverStandingKey,
    EntrantDriverAssignmentKey,
    EntrantIdentity,
    GPClassification,
    GPClassificationKey,
    RecordedDriverStanding,
    SeasonEntrantDriverAssignment,
    SeasonEvent,
)
from f1_eras.domain.teammates import PrimaryTeammateSelection


YEAR = 2012
CHAMPION = DriverIdentity("champion", "Champion")
EVENTS = tuple(SeasonEvent(
    race_id=round_, year=YEAR, round=round_, date=date(YEAR, 3, round_),
    grand_prix_id=f"gp-{round_}", official_name=f"Race {round_}",
    laps=50, distance=Decimal(300), scheduled_laps=None, scheduled_distance=None,
    sprint_race_date=None, sprint_race_laps=None, sprint_race_distance=None,
    sprint_race_scheduled_laps=None, sprint_race_scheduled_distance=None,
) for round_ in (1, 2, 3))


def assignment(driver, entrant="entrant-a", rounds=(1, 2, 3), constructor="constructor-a"):
    return SeasonEntrantDriverAssignment(
        EntrantDriverAssignmentKey(YEAR, entrant, constructor, "engine", driver),
        EntrantIdentity(entrant, entrant.title()), ConstructorIdentity(constructor, constructor.title()),
        DriverIdentity(driver, driver.title()), rounds,
        ";".join(map(str, rounds)) if rounds is not None else None, None,
    )


def result(driver, round_=1, status="2", constructor="constructor-a", order=2, laps=50):
    return GPClassification(
        GPClassificationKey(round_, "RACE_RESULT", order), YEAR, round_,
        int(status) if status.isdecimal() else None, status, "1",
        DriverIdentity(driver, driver.title()), ConstructorIdentity(constructor, constructor.title()),
        "engine", False, laps, None, None, None, None, False,
    )


def standing(driver, position=3, points="101.5", order=3):
    return RecordedDriverStanding(
        DriverStandingKey(YEAR, order), position, str(position) if position else "DSQ",
        DriverIdentity(driver, driver.title()), Decimal(points), False,
    )


def derive(assignments=(), rows=(), standings=()):
    return derive_teammate_context(
        YEAR, CHAMPION, EVENTS, (assignment("champion"), *assignments),
        (result("champion", status="1", order=1), *rows), standings,
    )


@pytest.mark.parametrize("constructor", ["constructor-a", "constructor-b"])
def test_shared_entrant_not_constructor_defines_teammates(constructor):
    context = derive((assignment("other", constructor=constructor),),
                     (result("other", constructor=constructor),))
    assert context.primary_teammate.driver.id == "other"
    assert context.primary_teammate.shared_races[0].teammate_assignment.constructor.id == constructor
    assert context.primary_teammate.shared_races[0].champion_assignment.constructor.id == "constructor-a"


def test_constructor_equality_does_not_join_different_entrants():
    context = derive((assignment("other", entrant="entrant-b"),), (result("other"),))
    assert context.primary_selection == PrimaryTeammateSelection.NONE
    assert context.candidates == ()


@pytest.mark.parametrize("rows", [(), (result("other", status="DNS", laps=None),),
                                 (result("champion", round_=2), result("other", round_=3))])
def test_assignment_overlap_without_both_drivers_racing_is_insufficient(rows):
    context = derive((assignment("other"),), rows)
    assert context.primary_teammate is None
    assert context.additional_teammates == ()


def test_participation_outside_assignment_coverage_does_not_count():
    context = derive((assignment("other", rounds=(2, 3)),
                      assignment("other", entrant="entrant-b", rounds=(1,))),
                     (result("other"),))
    assert context.primary_selection == PrimaryTeammateSelection.NONE


def test_champion_non_participation_prevents_shared_race():
    context = derive_teammate_context(
        YEAR, CHAMPION, EVENTS, (assignment("champion"), assignment("other")),
        (result("champion", status="DNS", laps=None), result("other")), (),
    )
    assert context.candidates == ()


@pytest.mark.parametrize(("status", "laps", "expected"), [
    ("2", 50, True), ("DNF", 0, True), ("DNF", None, True), ("NC", 39, True),
    ("DNS", None, False), ("DNQ", None, False), ("DNPQ", None, False), ("DSQ", 58, True),
])
def test_participation_uses_inspected_states_not_completed_laps(status, laps, expected):
    assert genuinely_participated(result("other", status=status, laps=laps)) is expected


@pytest.mark.parametrize(("status", "laps"), [
    ("DSQ", None), ("DSQ", 0), ("EX", None), ("DNP", None), ("UNKN", 50),
])
def test_ambiguous_status_is_not_silently_interpreted(status, laps):
    with pytest.raises(TeammateDerivationAmbiguity, match="ambiguous"):
        derive((assignment("other"),), (result("other", status=status, laps=laps),))


def test_inconsistent_numeric_classification_is_rejected():
    with pytest.raises(TeammateDerivationAmbiguity, match="Inconsistent"):
        genuinely_participated(replace(result("other"), position_text="DSQ"))


def test_distinct_races_not_repeated_shared_drive_rows_determine_primary():
    context = derive(
        (assignment("other"), assignment("second")),
        (replace(result("other"), shared_car=True),
         replace(result("other", order=4), shared_car=True),
         result("second", order=3), result("second", round_=2, order=3),
         result("champion", round_=2, status="1", order=1)),
        (standing("other", position=2), standing("second", position=10, order=10)),
    )
    assert context.primary_teammate.driver.id == "second"
    assert context.primary_teammate.shared_race_count == 2
    other = context.additional_teammates[0]
    assert other.shared_race_count == 1
    assert len(other.shared_races[0].teammate_result_keys) == 2


def test_same_race_across_multiple_constructor_assignments_counts_once():
    context = derive_teammate_context(
        YEAR, CHAMPION, EVENTS,
        (assignment("champion"), assignment("other"),
         assignment("champion", constructor="constructor-b"),
         assignment("other", constructor="constructor-b")),
        (result("champion", status="1", order=1), result("other"),
         result("champion", constructor="constructor-b", order=3),
         result("other", constructor="constructor-b", order=4)), (),
    )
    assert context.primary_teammate.shared_race_count == 1
    assert {race.entrant.id for race in context.primary_teammate.shared_races} == {"entrant-a"}
    assert len(context.primary_teammate.shared_races) == 4


def test_team_switch_coverage_retains_only_actual_shared_environment():
    context = derive(
        (assignment("other", rounds=(1,)), assignment("other", "entrant-b", rounds=(2, 3)),
         assignment("second", rounds=(2, 3))),
        (result("other"), result("other", round_=2), result("second", round_=2, order=3),
         result("champion", round_=2, status="1", order=1)),
    )
    assert {item.driver.id: item.shared_race_count for item in context.candidates} == {"other": 1, "second": 1}


def test_championship_position_breaks_shared_race_tie_without_combining_points():
    context = derive(
        (assignment("other"), assignment("second")),
        (result("other"), result("second", order=3)),
        (standing("other", 5, "101.5", 5), standing("second", 2, "242", 2)),
    )
    assert context.primary_teammate.driver.id == "second"
    assert context.primary_teammate.official_final_points == Decimal(242)
    assert context.additional_teammates[0].official_final_points == Decimal("101.5")
    assert context.additional_teammates[0].official_final_position == 5
    assert sum(item.is_primary for item in context.candidates) == 1


@pytest.mark.parametrize("standings", [
    (standing("other", 3), standing("second", 3, order=4)),
    (standing("other", 3),), (),
    (standing("other", None), standing("second", 3, order=4)),
])
def test_unresolved_primary_tie_keeps_every_candidate_without_arbitrary_winner(standings):
    context = derive((assignment("other"), assignment("second")),
                     (result("other"), result("second", order=3)), standings)
    assert context.primary_selection == PrimaryTeammateSelection.UNRESOLVED_TIE
    assert context.primary_teammate_id is None and context.primary_teammate is None
    assert context.tied_primary_candidate_ids == ("other", "second")
    assert len(context.additional_teammates) == 2
    assert not any(item.is_primary for item in context.candidates)


def test_tie_metadata_contains_only_remaining_leaders():
    context = derive(
        tuple(assignment(driver) for driver in ("other", "second", "third")),
        tuple(result(driver, order=order) for order, driver in enumerate(("other", "second", "third"), 2)),
        (standing("other", 3), standing("second", 3, order=4), standing("third", 5, order=5)),
    )
    assert context.tied_primary_candidate_ids == ("other", "second")
    assert len(context.additional_teammates) == 3


def test_ambiguous_final_classification_does_not_supply_tiebreak():
    context = derive(
        (assignment("other"), assignment("second")),
        (result("other"), result("second", order=3)),
        (replace(standing("other", 2), position_text="EX"), standing("second", 3, order=4)),
    )
    assert context.primary_selection == PrimaryTeammateSelection.UNRESOLVED_TIE
    assert context.primary_teammate is None


def test_repeated_identical_result_rows_do_not_inflate_count_or_evidence():
    row = result("other")
    context = derive((assignment("other"),), (row, row))
    assert context.primary_teammate.shared_race_count == 1
    assert context.primary_teammate.shared_races[0].teammate_result_keys == (row.source_key,)


@pytest.mark.parametrize("standings", [(), (standing("other", None, "0"),)])
def test_missing_standing_differs_from_recorded_unranked_zero_points(standings):
    candidate = derive((assignment("other"),), (result("other"),), standings).primary_teammate
    assert candidate.official_final_position is None
    assert candidate.official_final_points == (Decimal(0) if standings else None)
    assert (candidate.final_standing_source_key is not None) == bool(standings)


def test_unique_highest_overlap_needs_no_standing_or_further_tiebreak():
    context = derive((assignment("other"),), (result("other"),))
    assert context.primary_teammate.is_primary
    assert context.additional_teammates == ()
    assert context.tied_primary_candidate_ids == ()


@pytest.mark.parametrize("assignments", [
    (assignment("other", rounds=None),),
    (assignment("other"), assignment("other", entrant="entrant-b")),
])
def test_unknown_rounds_or_ambiguous_event_entrant_stop_derivation(assignments):
    with pytest.raises(TeammateDerivationAmbiguity):
        derive(assignments, (result("other"),))


def test_same_entrant_different_engine_metadata_remains_eligible():
    different_engine = replace(assignment("other"),
                               source_key=EntrantDriverAssignmentKey(
                                   YEAR, "entrant-a", "constructor-a", "other-engine", "other"))
    context = derive((different_engine,), (result("other"),))
    assert context.primary_teammate.shared_race_count == 1
    assert context.primary_teammate.shared_races[0].teammate_assignment.source_key.engine_manufacturer_id == "other-engine"


@pytest.fixture
def fixture_report():
    # A deterministic championship solely for HTTP projection tests.
    rows = tuple(row for round_ in (1, 2, 3) for row in (
        result("champion", round_, status="1", order=1), result("other", round_),
    ))
    championship = calculate_original_drivers(YEAR, EVENTS, rows, ())
    return ChampionshipReport(YEAR, ChampionshipCategory.DRIVERS, "original", championship,
                              original_drivers_rules(YEAR), None)


@pytest.mark.parametrize("path", ["/api/v1/championships/2012", "/api/v1/championship-margins?seasons=2012"])
@pytest.mark.parametrize("case", ["one", "multiple", "none", "tie", "missing"])
def test_http_stable_shape_preserves_each_driver_and_primary_state(fixture_report, path, case):
    assignments = () if case == "none" else (assignment("other"),)
    rows = () if case == "none" else (result("other"),)
    standings = () if case == "missing" else (standing("other", 3, "242"),)
    if case in {"multiple", "tie"}:
        assignments += (assignment("second"),)
        rows += (result("second", order=3),)
        standings += (standing("second", 3 if case == "tie" else 6, "101.5", 6),)
    context = derive(assignments, rows, standings)

    class FixtureService:
        def original_drivers(self, year, category):
            return replace(fixture_report, teammate_context=context)

    response = TestClient(create_app(FixtureService())).get(path)
    assert response.status_code == 200
    body = response.json()
    if "results" in body:
        body = body["results"][0]
    contract = body["teammate_context"]
    assert set(contract) == {"primary_selection", "primary_teammate", "additional_teammates",
                             "tied_primary_candidate_ids"}
    assert contract["primary_selection"] == context.primary_selection.value
    primary = contract["primary_teammate"]
    additional = contract["additional_teammates"]
    if case in {"none", "tie"}:
        assert primary is None
        assert len(additional) == (2 if case == "tie" else 0)
    else:
        assert primary["id"] == "other"
        assert primary["shared_race_count"] == 1
        assert primary["official_final_position"] == (None if case == "missing" else 3)
        assert primary["official_final_points"] == (
            None if case == "missing" else {"exact": {"numerator": 242, "denominator": 1}, "plot": 242.0}
        )
        assert primary["final_standing_recorded"] == (case != "missing")
        assert len(additional) == (1 if case == "multiple" else 0)
        assert all(item["id"] != primary["id"] for item in additional)
    if case == "multiple":
        assert additional[0]["official_final_points"]["exact"] == {"numerator": 203, "denominator": 2}
        assert additional[0]["official_final_position"] == 6
    if case == "tie":
        assert contract["tied_primary_candidate_ids"] == ["other", "second"]


@pytest.mark.integration
@pytest.mark.parametrize(("year", "points", "position", "shared_races"), [
    (2010, 242, 3, 19), (2011, 258, 3, 19), (2012, 179, 6, 20), (2013, 199, 3, 19),
])
def test_canonical_vettel_webber_and_unchanged_championship(project_source_db, year, points, position, shared_races):
    repository = F1DBRepository(project_source_db)
    before = repository.identify_snapshot()
    source = repository.read_original_drivers_source(year)
    service = ChampionshipService(repository)
    report = service.original_drivers(year)
    assert report.result == calculate_original_drivers(year, source.events, source.classifications, source.recorded)
    context = report.teammate_context
    assert context.champion.id == "sebastian-vettel"
    assert context.primary_selection == PrimaryTeammateSelection.UNIQUE
    assert len(context.candidates) == 1
    assert context.primary_teammate.driver == DriverIdentity("mark-webber", "Mark Webber")
    assert context.primary_teammate.official_final_points == points
    assert context.primary_teammate.official_final_position == position
    assert context.primary_teammate.shared_race_count == shared_races
    assert context.additional_teammates == ()
    api = TestClient(create_app(service))
    detail = api.get(f"/api/v1/championships/{year}").json()
    summary = api.get(f"/api/v1/championship-margins?seasons={year}").json()["results"][0]
    assert detail["teammate_context"] == summary["teammate_context"]
    assert detail["teammate_context"]["additional_teammates"] == []
    assert detail["teammate_context"]["primary_teammate"]["official_final_points"]["exact"] == {
        "numerator": points, "denominator": 1,
    }
    assert repository.identify_snapshot() == before


def test_unavailable_api_context_is_distinct_from_no_teammate(project_source_db):
    api = TestClient(create_app(ChampionshipService(F1DBRepository(project_source_db))))
    context = api.get("/api/v1/championships/2009").json()["teammate_context"]
    assert context == {"primary_selection": "unavailable", "primary_teammate": None,
                       "additional_teammates": [], "tied_primary_candidate_ids": []}


@pytest.mark.integration
@pytest.mark.parametrize("failure", ["unknown_rounds", "missing_champion", "champion_round_gap",
                                    "unknown_champion", "ambiguous_champion", "ambiguous_candidate"])
def test_relevant_entrant_uncertainty_preserves_every_core_http_field(project_source_db, failure):
    repository = F1DBRepository(project_source_db)
    source = repository.read_original_drivers_source(2012)
    healthy_service = ChampionshipService(repository)
    healthy_report = healthy_service.original_drivers(2012)
    healthy_api = TestClient(create_app(healthy_service))
    webber = next(item for item in source.entrant_assignments if item.driver.id == "mark-webber")
    other_assignments = tuple(item for item in source.entrant_assignments if item != webber)
    if failure == "unknown_rounds":
        assignments = (*other_assignments, replace(webber, rounds=None))
    elif failure in {"missing_champion", "champion_round_gap", "unknown_champion"}:
        champion = next(item for item in source.entrant_assignments if item.driver.id == "sebastian-vettel")
        assignments = tuple(item for item in source.entrant_assignments if item != champion)
        if failure != "missing_champion":
            assignments += (replace(champion, rounds=None if failure == "unknown_champion" else champion.rounds[1:]),)
    else:
        driver = webber if failure == "ambiguous_candidate" else next(
            item for item in source.entrant_assignments if item.driver.id == "sebastian-vettel"
        )
        assignments = (*source.entrant_assignments, replace(
            driver, entrant=EntrantIdentity("another-entrant", "Another Entrant"),
            source_key=replace(driver.source_key, entrant_id="another-entrant"),
        ))

    class IncompleteSource:
        def read_original_drivers_source(self, year):
            return replace(source, entrant_assignments=assignments)

    service = ChampionshipService(IncompleteSource())
    report = service.original_drivers(2012)
    assert report.result == healthy_report.result
    assert report.trust == healthy_report.trust
    assert report.calculation_diagnostics == healthy_report.calculation_diagnostics
    assert report.teammate_context is None
    api = TestClient(create_app(service), raise_server_exceptions=False)
    for path in ("/api/v1/championships/2012", "/api/v1/championship-margins?seasons=2012"):
        response = api.get(path)
        assert response.status_code == 200
        body = response.json()
        expected = healthy_api.get(path).json()
        if "results" in body:
            body, expected = body["results"][0], expected["results"][0]
        assert body.pop("teammate_context") == {
            "primary_selection": "unavailable", "primary_teammate": None,
            "additional_teammates": [], "tied_primary_candidate_ids": [],
        }
        expected.pop("teammate_context")
        assert body == expected
        assert body["trust"]["trusted_for_normal_use"]
        assert body["champion"]["points"]["exact"]["numerator"] == 281
        assert body["margin"]["raw_points_gap"]["exact"]["numerator"] == 3


@pytest.mark.integration
@pytest.mark.parametrize("malformed", ["malformed-rounds", "9" * 10000], ids=["text", "huge-numeric"])
def test_assignment_parser_failure_is_optional_and_core_api_remains_equivalent(project_source_db, monkeypatch, malformed):
    repository = F1DBRepository(project_source_db)
    api = TestClient(create_app(ChampionshipService(repository)), raise_server_exceptions=False)
    paths = ("/api/v1/championships/2012", "/api/v1/championship-margins?seasons=2012")
    baseline = {path: api.get(path).json() for path in paths}
    original = f1db._assignment_rounds
    monkeypatch.setattr(f1db, "_assignment_rounds", lambda value: original(malformed))
    source = repository.read_original_drivers_source(2012)
    assert source.entrant_assignments
    assert all(item.rounds is None and item.round_coverage_error for item in source.entrant_assignments)
    for path in paths:
        response = api.get(path)
        assert response.status_code == 200
        body, expected = response.json(), baseline[path]
        if "results" in body:
            body, expected = body["results"][0], expected["results"][0]
        assert body.pop("teammate_context")["primary_selection"] == "unavailable"
        expected.pop("teammate_context")
        assert body == expected


@pytest.mark.integration
def test_unrelated_championship_acquisition_error_is_not_swallowed(project_source_db, monkeypatch):
    repository = F1DBRepository(project_source_db)

    def fail_core_read(reader, year):
        raise SourceDatabaseError("Mandatory GP source failed")

    monkeypatch.setattr(f1db._BoundF1DBReader, "get_gp_classifications", fail_core_read)
    with pytest.raises(SourceDatabaseError, match="Mandatory GP"):
        ChampionshipService(repository).original_drivers(2012)
    api = TestClient(create_app(ChampionshipService(repository)), raise_server_exceptions=False)
    assert api.get("/api/v1/championships/2012").status_code == 500


def test_unknown_shared_coverage_cannot_silently_lower_overlap_and_change_primary():
    assignments = (assignment("champion"), assignment("other"), assignment("second"))
    rows = tuple(result("champion", round_, "1", order=1) for round_ in (1, 2, 3)) + (
        result("other", 1), result("other", 2), result("other", 3),
        result("second", 1, order=3), result("second", 2, order=3),
    )
    standings = (standing("other", 5, order=5), standing("second", 2, order=2))
    healthy = derive_teammate_context(YEAR, CHAMPION, EVENTS, assignments, rows, standings)
    assert healthy.primary_teammate.driver.id == "other"
    assert healthy.primary_teammate.shared_race_count == 3
    incomplete = (assignments[0], replace(assignments[1], rounds=None), assignments[2])
    with pytest.raises(TeammateDerivationAmbiguity, match="unknown round coverage"):
        derive_teammate_context(YEAR, CHAMPION, EVENTS, incomplete, rows, standings)


@pytest.mark.parametrize("constructor", ["constructor-a", "constructor-b"])
def test_participant_outside_champion_entrant_roster_is_irrelevant(constructor):
    context = derive(rows=(result("unassigned", constructor=constructor),))
    assert context.primary_selection == PrimaryTeammateSelection.NONE


def test_known_other_entrant_results_do_not_reduce_trustworthy_teammate_context():
    context = derive(
        (assignment("other", rounds=(1,)), assignment("other", "entrant-b", rounds=(2, 3)),
         assignment("second", rounds=(2, 3))),
        (result("other"), result("other", 2), result("other", 3),
         result("champion", 2, "1", order=1), result("champion", 3, "1", order=1),
         result("second", 2, order=3), result("second", 3, order=3)),
    )
    assert context.primary_selection == PrimaryTeammateSelection.UNIQUE
    assert context.primary_teammate.driver.id == "second"
    assert context.primary_teammate.shared_race_count == 2
    assert context.additional_teammates[0].driver.id == "other"
    assert context.additional_teammates[0].shared_race_count == 1


def test_missing_assignment_for_explicit_nonparticipant_does_not_create_ambiguity():
    context = derive(rows=(result("unassigned", status="DNS", laps=None),))
    assert context.primary_selection == PrimaryTeammateSelection.NONE


def test_nonoverlapping_participation_needs_no_teammate_attribution():
    context = derive(rows=(result("unassigned", round_=2),))
    assert context.primary_selection == PrimaryTeammateSelection.NONE


def test_same_engine_different_entrant_does_not_create_teammate():
    context = derive((assignment("other", "entrant-b", constructor="constructor-b"),),
                     (result("other", constructor="constructor-b"),))
    assert context.primary_selection == PrimaryTeammateSelection.NONE


@pytest.mark.parametrize("metadata", [
    (assignment("unrelated", "entrant-b", rounds=None),),
    (assignment("unrelated", "entrant-b"), assignment("unrelated", "entrant-c")),
])
def test_unrelated_entrant_ambiguity_and_participation_state_are_irrelevant(metadata):
    context = derive((assignment("other"), *metadata),
                     (result("other"), result("unrelated", status="UNKN", order=3)))
    assert context.primary_teammate.driver.id == "other"
    assert context.primary_teammate.shared_race_count == 1


def test_candidate_ambiguity_outside_known_shared_rounds_is_irrelevant():
    context = derive(
        (assignment("other", rounds=(2, 3)), assignment("other", "entrant-b", rounds=None)),
        (result("other", status="UNKN"),),
    )
    assert context.primary_selection == PrimaryTeammateSelection.NONE


def test_candidate_unknown_coverage_without_race_participation_is_irrelevant():
    context = derive((assignment("other", rounds=None),),
                     (result("other", status="DNS", laps=None),))
    assert context.primary_selection == PrimaryTeammateSelection.NONE


def test_equipment_cannot_resolve_relevant_multiple_entrant_assignments():
    competing = replace(assignment("other", "entrant-b", constructor="constructor-b"),
                        source_key=EntrantDriverAssignmentKey(
                            YEAR, "entrant-b", "constructor-b", "other-engine", "other"))
    with pytest.raises(TeammateDerivationAmbiguity, match="multiple entrants"):
        derive((assignment("other"), competing), (result("other"),))


def test_champion_team_switch_uses_actual_entrant_roster_at_each_round():
    context = derive_teammate_context(
        YEAR, CHAMPION, EVENTS,
        (assignment("champion", rounds=(1,)), assignment("champion", "entrant-b", rounds=(2, 3)),
         assignment("other"), assignment("second", "entrant-b")),
        tuple(result("champion", round_, "1", order=1) for round_ in (1, 2, 3))
        + (result("other"), result("other", 2), result("second", 2), result("second", 3)), (),
    )
    assert context.primary_teammate.driver.id == "second"
    assert context.primary_teammate.shared_race_count == 2
    assert context.additional_teammates[0].driver.id == "other"
    assert context.additional_teammates[0].shared_race_count == 1


@pytest.mark.integration
@pytest.mark.parametrize("case", ["constructor", "engine", "unrelated_unknown",
                                 "unrelated_ambiguous", "unrelated_absent"])
def test_irrelevant_or_equipment_metadata_preserves_complete_canonical_api(project_source_db, case):
    repository = F1DBRepository(project_source_db)
    source = repository.read_original_drivers_source(2012)
    driver_id = "mark-webber" if case in {"constructor", "engine"} else "jenson-button"
    target = next(item for item in source.entrant_assignments if item.driver.id == driver_id)
    assignments = tuple(item for item in source.entrant_assignments if item != target)
    if case == "constructor":
        assignments += (replace(target, constructor=ConstructorIdentity("other-constructor", "Other Constructor"),
                                source_key=replace(target.source_key, constructor_id="other-constructor")),)
    elif case == "engine":
        assignments += (replace(target, source_key=replace(target.source_key, engine_manufacturer_id="other-engine")),)
    elif case == "unrelated_unknown":
        assignments += (replace(target, rounds=None),)
    elif case == "unrelated_ambiguous":
        assignments += (target, replace(target, entrant=EntrantIdentity("another-entrant", "Another Entrant"),
                                       source_key=replace(target.source_key, entrant_id="another-entrant")))

    class MetadataSource:
        def read_original_drivers_source(self, year):
            return replace(source, entrant_assignments=assignments)

    baseline = TestClient(create_app(ChampionshipService(repository)))
    api = TestClient(create_app(ChampionshipService(MetadataSource())), raise_server_exceptions=False)
    for path in ("/api/v1/championships/2012", "/api/v1/championship-margins?seasons=2012"):
        response = api.get(path)
        assert response.status_code == 200
        assert response.json() == baseline.get(path).json()


@pytest.mark.integration
@pytest.mark.parametrize("driver_id", ["mark-webber", "jenson-button"], ids=["relevant", "unrelated"])
def test_huge_round_token_is_relevant_only_to_champion_entrant_roster(project_source_db, monkeypatch, driver_id):
    repository = F1DBRepository(project_source_db)
    api = TestClient(create_app(ChampionshipService(repository)), raise_server_exceptions=False)
    path = "/api/v1/championships/2012"
    baseline = api.get(path).json()
    original = f1db._BoundF1DBReader._read

    def malformed_rounds(reader, sql, year, *parameters, **kwargs):
        rows = original(reader, sql, year, *parameters, **kwargs)
        if sql == f1db._ENTRANT_ASSIGNMENTS_SQL:
            return [{**dict(row), "rounds": "9" * 10000} if row["driver_id"] == driver_id else row
                    for row in rows]
        return rows

    monkeypatch.setattr(f1db._BoundF1DBReader, "_read", malformed_rounds)
    source = repository.read_original_drivers_source(2012)
    target = next(item for item in source.entrant_assignments if item.driver.id == driver_id)
    assert target.rounds is None and "Unparseable" in target.round_coverage_error
    response = api.get(path)
    assert response.status_code == 200
    body = response.json()
    if driver_id == "mark-webber":
        assert body.pop("teammate_context") == {
            "primary_selection": "unavailable", "primary_teammate": None,
            "additional_teammates": [], "tied_primary_candidate_ids": [],
        }
        baseline.pop("teammate_context")
    assert body == baseline


@pytest.mark.integration
@pytest.mark.parametrize(("driver_id", "flag"), [
    ("jenson-button", 2), ("mark-webber", 0), ("mark-webber", 1),
    ("mark-webber", 2), ("mark-webber", None), ("mark-webber", "unexpected"),
])
def test_unused_test_driver_metadata_preserves_2012_championship(project_source_db, monkeypatch, driver_id, flag):
    repository = F1DBRepository(project_source_db)
    before = repository.identify_snapshot()
    api = TestClient(create_app(ChampionshipService(repository)), raise_server_exceptions=False)
    paths = ("/api/v1/championships/2012", "/api/v1/championship-margins?seasons=2012")
    baseline = {path: api.get(path).json() for path in paths}
    original = f1db._BoundF1DBReader._read

    def assignment_metadata(reader, sql, year, *parameters, **kwargs):
        rows = original(reader, sql, year, *parameters, **kwargs)
        if sql == f1db._ENTRANT_ASSIGNMENTS_SQL:
            # Add the unused source field to the targeted assignment's row,
            # reproducing the reviewed mapping failure without touching F1DB.
            return [{**dict(row), "test_driver": flag} if row["driver_id"] == driver_id else row
                    for row in rows]
        return rows

    monkeypatch.setattr(f1db._BoundF1DBReader, "_read", assignment_metadata)
    for path in paths:
        response = api.get(path)
        assert response.status_code == 200
        assert response.json() == baseline[path]
        body = response.json()
        if "results" in body:
            body = body["results"][0]
        assert body["champion"]["id"] == "sebastian-vettel"
        context = body["teammate_context"]
        assert context["primary_selection"] == "unique"
        assert context["additional_teammates"] == []
        primary = context["primary_teammate"]
        assert primary["id"] == "mark-webber" and primary["name"] == "Mark Webber"
        assert primary["official_final_points"]["exact"] == {"numerator": 179, "denominator": 1}
        assert primary["official_final_position"] == 6
        assert primary["shared_race_count"] == 20
    assert repository.identify_snapshot() == before
