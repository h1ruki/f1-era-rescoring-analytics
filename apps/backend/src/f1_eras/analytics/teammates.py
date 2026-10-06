"""Entrant-based teammate derivation; no scoring or championship reconstruction."""

from collections import defaultdict
from dataclasses import replace

from f1_eras.domain.models import (
    DriverIdentity,
    GPClassification,
    RecordedDriverStanding,
    SeasonEntrantDriverAssignment,
    SeasonEvent,
)
from f1_eras.domain.teammates import (
    PrimaryTeammateSelection,
    SharedRaceEvidence,
    TeammateCandidate,
    TeammateContext,
)


class TeammateDerivationAmbiguity(ValueError):
    """Relevant source evidence cannot establish a defensible teammate context."""


def genuinely_participated(row: GPClassification) -> bool:
    """Use inspected result states; exclusions need independent race-lap evidence.

    DNF includes first-lap retirements with zero completed laps. DNS/DNQ/DNPQ
    explicitly describe non-participation. Do not assign meanings to EX, DNP or
    unknown values. A DSQ alone does not establish whether the driver raced.
    """
    status = row.position_text
    if status in {"DNS", "DNQ", "DNPQ"}:
        if row.position_number is not None:
            raise TeammateDerivationAmbiguity("Non-participating result has a classified position")
        return False
    if row.position_number is not None:
        if row.position_number > 0 and status == str(row.position_number):
            return True
        raise TeammateDerivationAmbiguity(f"Inconsistent classified result: {status!r}")
    if status in {"DNF", "NC"}:
        return True
    if status == "DSQ" and row.laps is not None and row.laps > 0:
        return True
    raise TeammateDerivationAmbiguity(
        f"Race participation is ambiguous for {row.driver.id} at race "
        f"{row.source_key.race_id}: status={status!r}, laps={row.laps!r}"
    )


def _assignments_at_round(
    assignments: list[SeasonEntrantDriverAssignment], round_: int,
) -> list[SeasonEntrantDriverAssignment]:
    """Resolve a relevant driver's entrant coverage, without equipment matching."""
    active = []
    for assignment in assignments:
        if assignment.rounds is None:
            raise TeammateDerivationAmbiguity(
                assignment.round_coverage_error
                or f"Entrant assignment has unknown round coverage for {assignment.driver.id}"
            )
        if round_ in assignment.rounds:
            active.append(assignment)
    if len({item.entrant.id for item in active}) > 1:
        raise TeammateDerivationAmbiguity("Relevant driver has multiple entrants at the same round")
    return active


def _participating_results(rows: list[GPClassification], event: SeasonEvent) -> list[GPClassification]:
    if any(row.year != event.year or row.round != event.round for row in rows):
        raise TeammateDerivationAmbiguity("Result does not match the teammate event calendar")
    return [row for row in rows if genuinely_participated(row)]


def derive_teammate_context(
    year: int,
    champion: DriverIdentity,
    events: tuple[SeasonEvent, ...],
    assignments: tuple[SeasonEntrantDriverAssignment, ...],
    classifications: tuple[GPClassification, ...],
    recorded_standings: tuple[RecordedDriverStanding, ...],
) -> TeammateContext:
    """Start with the champion's entrant roster, then verify shared participation."""
    calendar = {event.race_id: event.round for event in events}
    if (any(event.year != year for event in events) or len(calendar) != len(events)
            or len(set(calendar.values())) != len(events)):
        raise TeammateDerivationAmbiguity("Inconsistent teammate event calendar")
    by_driver: dict[str, list[SeasonEntrantDriverAssignment]] = defaultdict(list)
    for assignment in assignments:
        if assignment.source_key.year == year:
            by_driver[assignment.driver.id].append(assignment)
    if not by_driver[champion.id]:
        raise TeammateDerivationAmbiguity("Champion has no recorded entrant assignment")
    champion_entrants = {item.entrant.id for item in by_driver[champion.id]}
    roster_ids = {driver_id for driver_id, items in by_driver.items()
                  if any(item.entrant.id in champion_entrants for item in items)}
    results: dict[tuple[int, str], list[GPClassification]] = defaultdict(list)
    for row in classifications:
        if row.source_key.session_type != "RACE_RESULT" or row.driver.id not in roster_ids:
            continue
        results[row.source_key.race_id, row.driver.id].append(row)

    evidence: dict[str, list[SharedRaceEvidence]] = defaultdict(list)
    identities: dict[str, DriverIdentity] = {}
    for event in sorted(events, key=lambda item: (item.round, item.race_id)):
        champion_rows = _participating_results(results[event.race_id, champion.id], event)
        if not champion_rows:
            continue
        champion_assignments = _assignments_at_round(by_driver[champion.id], event.round)
        if not champion_assignments:
            raise TeammateDerivationAmbiguity("Champion participation has no entrant assignment at this round")
        entrant = champion_assignments[0].entrant
        for driver_id in sorted(roster_ids - {champion.id}):
            possible_shared = [item for item in by_driver[driver_id]
                               if item.entrant.id == entrant.id
                               and (item.rounds is None or event.round in item.rounds)]
            if not possible_shared:
                continue
            teammate_rows = _participating_results(results[event.race_id, driver_id], event)
            if not teammate_rows:
                continue
            teammate_assignments = _assignments_at_round(by_driver[driver_id], event.round)
            for champion_assignment in dict.fromkeys(champion_assignments):
                for teammate_assignment in dict.fromkeys(teammate_assignments):
                    evidence[driver_id].append(SharedRaceEvidence(
                        event.race_id, event.round, entrant,
                        champion_assignment, teammate_assignment,
                        tuple(sorted({row.source_key for row in champion_rows},
                                     key=lambda key: key.position_display_order)),
                        tuple(sorted({row.source_key for row in teammate_rows},
                                     key=lambda key: key.position_display_order)),
                    ))
            identities[driver_id] = teammate_rows[0].driver

    standings: dict[str, RecordedDriverStanding] = {}
    for standing in recorded_standings:
        if standing.driver.id not in evidence:
            continue
        if standing.source_key.year != year or standing.driver.id in standings:
            raise TeammateDerivationAmbiguity("Final driver standings are inconsistent or duplicated")
        standings[standing.driver.id] = standing
    candidates = []
    for driver_id, races in sorted(evidence.items()):
        standing = standings.get(driver_id)
        candidates.append(TeammateCandidate(
            identities[driver_id], standing.source_key if standing else None,
            standing.position_number if standing else None,
            standing.position_text if standing else None,
            standing.recorded_points if standing else None,
            len({race.race_id for race in races}), tuple(races), False,
        ))
    if not candidates:
        return TeammateContext(year, champion, (), PrimaryTeammateSelection.NONE, None, ())
    maximum = max(item.shared_race_count for item in candidates)
    leaders = [item for item in candidates if item.shared_race_count == maximum]
    if len(leaders) > 1 and all(
        item.official_final_position is not None and item.official_final_position > 0
        and item.official_final_position_text == str(item.official_final_position)
        for item in leaders
    ):
        best_position = min(item.official_final_position for item in leaders)
        leaders = [item for item in leaders if item.official_final_position == best_position]
    if len(leaders) != 1:
        return TeammateContext(
            year, champion, tuple(candidates), PrimaryTeammateSelection.UNRESOLVED_TIE,
            None, tuple(item.driver.id for item in leaders),
        )
    primary_id = leaders[0].driver.id
    return TeammateContext(
        year, champion, tuple(replace(item, is_primary=item.driver.id == primary_id)
                              for item in candidates),
        PrimaryTeammateSelection.UNIQUE, primary_id, (),
    )
