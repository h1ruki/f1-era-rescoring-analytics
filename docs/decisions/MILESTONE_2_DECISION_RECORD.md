# Milestone 2 — Complete the v1 historical Drivers comparison

Status: **Next-stage plan, defined by the 2026-10-06 repository audit; incomplete.**
This record formalises the work justified by the existing product direction and
implementation. It uses the final product-owner-approved teammate contract in
[Milestone 1B](MILESTONE_1B_DECISION_RECORD.md#teammate-eligibility-and-grouping)
and does not mark Milestone 1 complete. The
[roadmap](../README.md#milestone-status) owns overall milestone status.

## Objective and product outcome

Make the answer to **“How dominant was each F1 champion in their title-winning
season?”** usable across completed Formula 1 championship history: compare each
champion with the championship runner-up, understand the points and percentage
gap, and inspect the historical context needed to interpret it.

This is an internal development milestone **within v1 — Drivers / Historical
Reality**, not v2. Its outcome is a complete, reviewable v1 candidate whose visible
analytical meaning can be frozen at release. Milestone completion does not itself
publish a release. Keep the first view simple and reveal analytical depth on demand.

## Why this is a coherent next stage

The repository already connects immutable F1DB input, exact Original reconstruction,
canonical trust, FastAPI and a chronological React chart for 2010–2013. It also
supplies champion teammate enrichment through the API. The remaining work is to
extend that same answer through history and present its supporting context reliably.
It is not a request for a new analytics dashboard or a replacement architecture.

The [master brief](../architecture/F1_ERAs_MASTER_BRIEF.md#v1-visible-analytical-contract)
owns the visible analytical contract. [1A](MILESTONE_1A_DECISION_RECORD.md),
[1B](MILESTONE_1B_DECISION_RECORD.md) and
[historical-data trust](HISTORICAL_DATA_TRUST_DECISION_RECORD.md) remain the
methodology authorities. Their unimplemented v1 requirements are dependencies
carried into this milestone, not evidence that Milestone 1 was finished.

## Scope and dependencies

| Work area | Required outcome |
| --- | --- |
| Historical calculation and coverage | Extend Original Drivers packages across completed championship history. Implement only the season-applicable rules needed for historical reality; preserve exact fractions, counted/dropped results, sanctions, exclusions, shared drives, special event awards and sporting countback where applicable. Unsupported interpretations stay unavailable until resolved. |
| Trust and historical evidence | Every exposed season passes the approved snapshot, integrity and complete-population canonical reconciliation path. Reconcile membership, points, sporting positions and classification, not just P1/P2. Investigate concrete conflicts and unsupported interpretations; preserve the separate, snapshot-bound 2010 external-audit record. |
| Historical/context metadata | Supply champion and runner-up identities, relevant constructor contributions and historical colours, F1-record nationality and complete supported season teammate sets with shared-event overlap/context. Apply 1B's attribution and event-level racing-operation methodology, including historical reconciliation where needed, and retain partial/ambiguous/unavailable states. Context must explain the title comparison; comprehensive chassis/engine history is not a prerequisite. |
| Backend/API | Expose the supported coverage and approved context through the existing service/API. Keep mathematics in Python; separate mandatory trust from optional enrichment. Provide sufficient countback/classification/rule context to explain exceptional title outcomes without a new public scoring mode. |
| Frontend and UX | Present chronological champion-versus-runner-up margins with points/% selection, meaningful zero baseline, season/range navigation, concise hover and inspectable season detail. Integrate constructor/teammate context without changing the headline comparison. Use historical colours with truthful unresolved attribution. Implement era presets only with documented boundaries. |
| Integration and usability | Connect actual backend coverage/context to frontend controls and detail, avoiding hard-coded four-season coverage claims. Preserve loading, empty, unavailable, error and retry handling. Make the comparison and explanations usable with keyboard, accessible text and colour-independent cues, and at smaller viewport sizes. |
| Verification and readiness | Validate expanded rules and representative historical exceptions, full-season reconciliation, optional-context failures, API contracts and frontend interactions. Exercise a complete app smoke check, responsiveness/accessibility and documented setup on the environments claimed as supported. |

Completion requires a reviewed coverage inventory against the approved snapshot:
which completed championship seasons are supported, their rules and verification
status, and any unresolved historical exceptions. Source-year presence alone does
not prove championship completion. A missing or blocked completed season prevents
claiming full-history completion; changing that release promise requires an explicit
product-owner scope decision. Upcoming/in-progress seasons must not masquerade as
final title-winning seasons.

Align implementation with [1B's approved season teammate set](MILESTONE_1B_DECISION_RECORD.md#teammate-eligibility-and-grouping):
aggregate every qualifying event-level shared racing-operation relationship,
normally established from normalized entrant/team identity and participation/entry
evidence, with canonical historical reconciliation for exceptions. Retain all
teammates without primary/additional ranking. Derive **Teammate battle: Yes/No**
from championship runner-up membership, including partial-season overlap, and
integrate this context into v1. The current entrant-derived API and its selection
rule remain implementation drift to resolve in Milestone 2, not a pending semantic
decision or a claim of full-history compliance.

## Completion criteria

- [ ] Every completed championship season in the reviewed release coverage is
  available under its Original rules and passes complete canonical reconciliation;
  all-history wording matches the actual coverage.
- [ ] Champion, runner-up, final counted points, raw gap and championship margin
  agree with the master brief's contract. Equal points resolved by countback remain
  a zero gap with the resolution explained; no display rounding determines ranking.
- [ ] Historical exceptions required by those seasons have supported rules,
  source/interpretation records where needed, and meaningful regressions.
  Unfinished seasons and unresolved calculations never display definitive margins.
- [ ] Complete supported season teammate sets retain every qualifying relationship
  through correct event-level aggregation, with historical reconciliation for
  exceptional identity cases. Champion/runner-up teammate-battle membership is
  derived correctly, including partial-season overlap, and integrated into v1
  without selecting a primary teammate.
- [ ] Constructor attribution, F1-record nationality and colours convey supported
  identity/context; unavailable context cannot erase a valid championship result
  or become a false fact.
- [ ] Users can navigate the historical comparison, change metric/range and inspect
  P1/P2 and necessary title-resolution context without learning the internal engine.
  Era presets, if exposed, use documented boundaries and consistent Custom behavior.
- [ ] Frontend/API integration covers valid, empty, unavailable and failed responses,
  including optional metadata gaps. Keyboard, text alternatives, contrast and
  small-screen behavior are reviewed with the actual chart.
- [ ] Relevant backend/frontend suites, build, expanded historical diagnostic and
  app smoke checks pass on the reviewed candidate; source data remains immutable.
  Setup claims and any remaining platform validation limitations are explicit.
- [ ] README, capabilities, component references and roadmap agree with the delivered
  scope. The owner reviews the stable v1 analytical contract before release.

## Non-goals and deferred work

- **v2:** user-selectable alternative scoring, cross-year rule transplantation,
  What If outcomes, counterfactual explanations/exports and arbitrary scoring forms.
  Reusing historical rules internally does not expose these as v1 controls.
- **v3:** Constructors Championship standings, comparisons and dominance analysis.
  Preserve the constructor identities/contributions that v1 Drivers context needs.
- Universal driver rankings/GOAT scores, career comparisons, generic statistics
  dashboards and weighted composite dominance metrics.
- Exhaustive chassis usage, engine lineage, operational succession or modern-colour
  mappings that do not resolve a required v1 claim. Existing 1B research stays useful.
- Active-season/live/provisional analytics, automated snapshot acquisition/promotion,
  and an independent external dossier for every season.
- Architecture replacement, a new setup system or speculative later product versions.

## Suggested implementation order

1. Inventory completed-season Original coverage, rules and context gaps against the
   approved snapshot, including drift from the approved season teammate set contract.
2. Expand historical packages in reviewable groups, adding reconciliation and
   exception coverage before advertising availability.
3. Integrate approved context, range navigation and detail into the existing chart;
   parallel progress in these areas does not waive their analytical dependencies.
4. Review the complete v1 candidate against the criteria above and the release policy.

Each implementation session should identify which criterion it advances and retain
the remaining gaps. No particular component layout, database redesign, calendar
deadline or release date is prescribed by this record.
