# F1 ERAs documentation and roadmap

F1 ERAs asks: **How dominant was each F1 champion in their title-winning season?**
Compare every championship season in Formula 1 history by the gap between the
champion and runner-up. Keep that visible product simple; historical rules,
identity evidence and verification make the comparison trustworthy underneath.

## Documentation authority

This index owns product-version scope, release policy and milestone status.
It routes detailed requirements to the existing subject authorities below.
An approved methodology is not a claim of implemented or complete coverage.

| Document | Purpose and audience | Authority and status |
| --- | --- | --- |
| [Root README](../README.md) | Product introduction for users and newcomers | Current public overview; summarizes this roadmap |
| [Root SETUP.md](../SETUP.md) | Workstation preparation, daily use and PC handoff for contributors | Sole setup authority; replaces the removed `docs/SETUP.md` |
| [Master engineering brief](architecture/F1_ERAs_MASTER_BRIEF.md) | Architecture, visible analytical contract and presentation direction for implementers | Current technical authority; distinguishes implemented scope from targets |
| [Milestone 1A](decisions/MILESTONE_1A_DECISION_RECORD.md) | Championship rules and historical interpretation for analytics/research | Approved normative methodology with retained rescoring history; partially implemented |
| [Milestone 1B](decisions/MILESTONE_1B_DECISION_RECORD.md) | Identity, attribution and teammate semantics for data/UI work | Approved methodology, including the final season teammate set contract; partially implemented |
| [Milestone 2](decisions/MILESTONE_2_DECISION_RECORD.md) | Complete historical Drivers comparison for the owner and implementation sessions | Formal next-stage plan within v1; not a completion or release claim |
| [Historical data trust](decisions/HISTORICAL_DATA_TRUST_DECISION_RECORD.md) | Normal-use trust and source-rotation policy for maintainers | Current normative policy plus preserved 2010 audit and snapshot-approval provenance |
| [Verification foundation](decisions/VERIFICATION_FOUNDATION_DECISION_RECORD.md) | Verification design and its evolution for maintainers/auditors | Current canonical clarification plus historical foundation; original strict rules still govern independent-audit claims, not normal-use availability |
| [Backend README](../apps/backend/README.md) | Implemented repository, analytics, teammate API and diagnostics for backend contributors | Current implementation reference; not a separate setup guide or product-policy override |
| [Frontend README](../apps/frontend/README.md) | Implemented chart, integration and limitations for frontend contributors | Current implementation reference; not the full target UX or a setup guide |
| [Historical metadata README](../apps/backend/historical/README.md) | Approval/audit metadata formats and evidence population for maintainers | Current schema/operational reference under the trust policy |
| [Legacy prototype README](../legacy/streamlit-prototype/README.md) | Original Streamlit work for historical reference | Historical archive; not maintained as a runnable application or current product contract |

The [snapshot manifest](../apps/backend/historical/canonical_snapshot.json) is the
sole **runtime** snapshot-approval authority. The
[external audit summaries](../apps/backend/historical/external_audit_summaries.json)
are snapshot-bound provenance, not another approval mechanism. Synthetic fixtures
under backend tests are policy examples, never historical evidence.
The [Windows setup script](../scripts/setup-windows.ps1) is setup automation;
SETUP.md records its supported PowerShell runtimes and validation limits.
[Editor recommendations](../.vscode/extensions.json) are optional tooling metadata.

Where records overlap, this roadmap determines version inclusion, the master brief
defines the visible metrics and architecture, 1A/1B define domain methodology, and
historical-data trust supersedes the original independent-audit production gate.
Component READMEs describe actual behavior and must flag conflicts rather than
silently supersede approved methodology. Preserve historical sections and their
source qualifications; they are not competing current roadmaps.

## Product versions and release policy

| Version | Product scope | Boundary |
| --- | --- | --- |
| **v1 — Drivers / Historical Reality** | Champion versus championship runner-up across Formula 1 history, under each season's original rules and final amended classification | Teammate, constructor/team identity, colours, competition, era and championship-resolution context support the comparison; full Constructors analytics and alternative scoring are excluded |
| **v2 — What If** | Alternative scoring systems, counterfactual rescoring and outcomes under alternative rule assumptions | Recorded event facts remain distinct from hypothetical championship outcomes |
| **v3 — Constructors** | Constructors Championship comparison and dominance analytics | Constructor identity needed by v1 is not this feature |

Once v1 is released, v1.x preserves its visible analytical contract and focuses
on maintenance: bug fixes, data corrections, dependency/security fixes,
documentation and small non-disruptive polish. Unfinished next-major functionality
stays isolated from the released experience; v2 becomes user-visible at v2.0,
and the same principle applies to v3. Major user-visible analytical changes arrive
with their corresponding major version.

Once releases begin, `main` represents the stable/released product line, while
next-major development can proceed separately. Active development is currently
`development/v1`. API `/api/v1` and package version strings do not certify that
the v1 product has shipped.

## Milestone status

**Milestones are internal development stages, not product versions.** Several
milestones can contribute to v1; Milestone 2 does not mean v2.

At the 2026-10-06 audit, **Milestone 1 is partially complete and still has active
v1 foundation work**. Its original 1A rescoring/rules and 1B identity methodology
span more than v1. Preserve those useful distinctions without requiring every
future-version capability before delivering historical Drivers dominance.
Milestone 2 is the justified next integration/release-readiness stage, with the
remaining v1 foundation work made explicit as dependencies. It is not yet complete.

| Area | What exists | Remaining work and destination |
| --- | --- | --- |
| 1A analytical foundation | Exact 2010–2013 Original Drivers reconstruction, counted constructor contributions, countback, explicit unavailable states, read-only source access and complete canonical reconciliation | Other historical Original packages and their applicable best-N/split, shared-drive, shortened-event, sprint/fastest-lap, sanction/exclusion and countback rules are v1 foundation dependencies; cross-year transplantation belongs to v2 |
| Trust and verification | Generic approval/integrity/reconciliation gate, snapshot-bound reads, negative regression coverage, strict supplementary evaluator and the preserved 2010 audit summary | Reconcile each newly supported season completely; investigate concrete historical conflicts; no duplicate independent dossier is required for every season |
| 1B supporting identity | Driver/constructor IDs and names, Original constructor contributions, entrant/round-based champion teammate API enrichment with explicit ambiguity | Align implementation with the approved season teammate set below; integrate supported context, F1-record nationality and historical team colours. Broad chassis/engine lineage and exhaustive succession research remain deferred unless needed for a v1 claim |
| First product slice | FastAPI summaries/details; React/Plotly chronological margin chart, points/% toggle, hover, summary list, loading/error/retry and unavailable states | Full-history coverage, context display, season/range navigation, detail interaction and release validation form Milestone 2 |

Evidence: [Original calculator](../apps/backend/src/f1_eras/analytics/original_drivers.py),
[application service](../apps/backend/src/f1_eras/application/championships.py),
[canonical assessment](../apps/backend/src/f1_eras/verification/canonical.py),
[teammate derivation](../apps/backend/src/f1_eras/analytics/teammates.py),
[frontend](../apps/frontend/src/App.tsx), and their backend/frontend regression suites.
Existing tests cover this slice and rejection behavior; they do not implement the
unbuilt 1A transplantation or comprehensive 1B research programme.

Milestone 1 therefore built a working foundation for the dominance question,
not a complete historical engine or a finished v1. The project evolved from
rescoring-oriented work; this assessment does not recast that original intent.

## Next work and approved teammate contract

Follow [Milestone 2](decisions/MILESTONE_2_DECISION_RECORD.md) for completion criteria
and sequencing: align teammate implementation, expand Original coverage with
reconciliation, connect supported context to the chart, then validate the complete
v1 experience. Keep unfinished 1A/1B work visible as dependencies, not completed work.

**Approved v1 teammate meaning:** [Milestone 1B](decisions/MILESTONE_1B_DECISION_RECORD.md#teammate-eligibility-and-grouping)
retains every driver who shared at least one championship event with the champion
in the same racing operation/team. Aggregate the complete season teammate set;
do not choose a primary teammate. Normal determination uses normalized entrant/team
identity and participation/entry evidence, with canonical historical reconciliation
for exceptions; raw entrant or constructor equality is not the definition.
**Teammate battle** is Yes if the championship runner-up belongs to that set, No
otherwise, including partial-season overlap. Unsupported evidence remains explicit.
The current entrant-derived API selection still needs Milestone 2 alignment and
full-history coverage. Exact era-preset boundaries and visual details remain deferred.
