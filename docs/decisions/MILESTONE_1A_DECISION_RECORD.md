# Milestone 1A — Championship methodology decision record

Status: **Methodology approved by the product owner; partially implemented.**
Milestone 1B was subsequently approved in its own record. See the
[milestone status](../README.md#milestone-status) for the current completion assessment.

## Current role and implementation boundary

This record preserves the original rescoring-oriented analytical groundwork.
Its historical-rule, exactness, ambiguity and classification principles support
v1's champion-versus-runner-up comparison under Original rules. Cross-year rule
transplantation and counterfactual views belong to v2; Constructors Championship
calculations belong to v3. Milestone numbers do not designate product versions.

The implemented 1A slice is 2010–2013 Original Drivers scoring, countback, exact
points/margins, constructor contributions and explicit unavailable states, with
complete canonical reconciliation and regression coverage. Best-N/split-season
execution, general sanctions/exclusions, other historical packages and cross-year
transplantation are not implemented by that slice. Remaining historical Original
requirements are dependencies of [Milestone 2](MILESTONE_2_DECISION_RECORD.md).
This approved methodology is not a claim that those capabilities already exist.

## Historical-rule transplantation

Historical trust clarification: [HISTORICAL_DATA_TRUST_DECISION_RECORD.md](HISTORICAL_DATA_TRUST_DECISION_RECORD.md)
supersedes independent external-evidence prerequisites for normal Original trust.
Canonical immutable F1DB input, supported deterministic rules, passing integrity
checks and exact complete championship reconciliation suffice. The implemented
2010-2013 Drivers / Original packages share one trust path; 2010 alone has
supplementary completed external-audit metadata. Earlier research/golden-case
statements below describe this milestone's original context, not a requirement
for new 2011-2013 dossiers. Unsupported historical interpretations, incomplete
seasons, ambiguity, sanctions/exclusions and exact arithmetic requirements remain
authoritative. Further primary-source research addresses failures, conflicts,
unsupported interpretations or deliberately selected historical edge cases.

Select a complete, source-year championship package. Use recorded race and sprint classifications, DSQs, exclusions, and event outcomes as historical facts. Rescore those facts under the selected package; do not simulate different race outcomes.

- An explicitly fixed best-N limit retains the same N on a target calendar of any length. If fewer than N eligible results exist, count those available.
- A calendar-dependent limit is evaluated from its sourced formula using the target calendar. Do not replace it with the numerical quota observed in the source season.
- A split-season rule uses the target calendar and the source package's actual splitting, rounding, and odd-race conventions. Do not freeze original round numbers unless the regulation makes them material. Keep separate quotas separate.
- Never introduce proportional scaling or a hybrid formula without explicit approval.
- Driver and constructor rules, including result limits and eligibility, are calculated separately. Exact fractions remain exact through calculation.

For the 1979 Drivers' Championship rule, let R be the number of championship Grands Prix **actually held**. The first half has floor(R / 2) races and the second has ceil(R / 2); each half retains ceil(half-size / 2) results. Thus 15 races give 4+4 and 24 races give 6+6. The [FIA January 1979 bulletin, printed pages 8–9](https://historicdb.fia.com/sites/default/files/regulations/1734381234/135-jan-1979.pdf) specifies the split, rounding, and actual-races basis.

For the 1981 Drivers' Championship rule, retain ceil(R / 2) + 2 results. Thus 15 races give 10 and 24 races give 14. The [FIA December 1980 bulletin, printed page 10](https://historicdb.fia.com/sites/default/files/regulations/1734383117/154-dec-1980.pdf) specifies the formula and examples. Sprint sessions do not increase R. A driver's missed races do not reduce R.

## Exceptions, sanctions, and ambiguity

Historical race membership, award eligibility, shared drives, fastest-lap and sprint treatment, shortened-event provisions, constructor scoring, final-event double points, and source-year countback travel with the complete package. An ineligible classification is not promoted or reassigned unless the sourced rule requires it. The 2014 final-event multiplier applies to the target season's actual finale.

Unsupported cross-era combinations are **unavailable**, with a precise reason and condition for resolution. Do not supply an invented shared-drive allocation, fastest-lap tie rule, scoring-car selection, or other convention. Preserve event-level facts and any calculations that are independently supported.

An explicit numerical championship deduction keeps its stated number. A sanction removing a particular event award removes that event's recomputed award. Preserve the sanction's driver/constructor scope and its position in the calculation. Championship exclusion changes ranking eligibility without rewriting recorded race classifications. Preserve every constructor contributing to a driver's counted points. Where counted-contribution attribution is unambiguous, expose those contributions in the domain result; how those contributions determine primary visual identity is a Milestone 1B decision. Equal-score result-limit cutoffs retain all valid counted-result allocations and disclose any ambiguity in constructor contribution or another downstream result; database ordering must not choose one silently.

## Counterfactual explanation and domain contract

Whenever **Original** is not selected, label the view persistently: “Counterfactual view — recorded results rescored under [selected year] championship rules.” The label must accompany standalone charts and exports. A recomputed match with official standings does not turn a counterfactual view into an official one.

The eventual backend must provide structured information sufficient for three consistent explanations:

1. A compact active-rules summary: scoring scales, evaluated result-limit rule, sprint, fastest lap, shortened events, countback, constructor rules, special provisions, and preserved historical facts.
2. “How this is calculated”: ordered steps with rule sources, conditions, formula operands, rounding, and evaluated quotas. For example, a 24-race target under 1979 yields halves of 12+12 and quotas of 6+6.
3. A season trace: event awards and components, gross points before limits, counted and dropped results, sanctions, exclusions, exact final totals, countback stages, and unresolved or ambiguous cases.

The domain response must identify the calculation and selected package versions; input snapshot and source record IDs; rule citations and evidence status; calendar population and split membership; event facts and award components; result-selection decisions; adjustment scope; ranking resolution; and blockers. Each trace step needs its inputs, rule, operation, and output. Distinguish zero, dropped, ineligible, excluded, ambiguous, and unavailable states. Unavailable totals must be null/absent rather than fabricated as zero. Event and season components must reconcile to their displayed totals.

## Unfinished seasons

**Approved Choice 1:** Withhold a definitive formula-based championship calculation until the target calendar is complete or a historically verified interim procedure exists. Event-level rescoring, rule evaluation, diagnostics, and explanation may still be shown. The domain response must state precisely why the championship total is unavailable and what condition would resolve it. Do not use the expected final calendar or races completed so far as an unapproved substitute for the final race population.

## Regression and research gates

The regression suite must separately exercise a verified fixed best-N rule on short and long target calendars; the 1979 formula and split on different calendar lengths; and the 1981 formula on different calendar lengths. It must also test reconciliation, complete-package behaviour, sanctions, exclusions, ambiguity, unavailable states, unfinished seasons, source-linked explanations, and persistent counterfactual identification. The previously proposed historical golden cases remain candidates pending source verification. At this record's original approval no tests had been implemented. The current slice has scoring, reconciliation, trust and unavailable-state tests; it does not yet implement the best-N/split/transplantation regression programme above. Cross-year and counterfactual tests are v2 work; source-year rules required for historical Original results remain v1 work.

Research must still certify original clauses and amendments for early result limits and countback; the 1970s shortened-race transition and boundary wording; exceptional entry eligibility and sanctions; shared-drive participation exceptions and cross-era compatibility; historically tied fastest laps under later packages; historical scoring-car nominations; and event facts needed for shortened-race decisions. Affected calculations remain unavailable until the necessary evidence or an expressly approved rule exists.
