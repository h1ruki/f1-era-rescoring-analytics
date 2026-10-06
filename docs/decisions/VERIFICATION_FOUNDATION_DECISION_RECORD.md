# Drivers / Original verification foundation

Status: approved foundation, updated with the canonical normal-use trust
implementation under the historical-data trust decision. The initial slice is
preserved below. Milestone 1A/1B methodology remains authoritative.

## Current authority: canonical trust implementation

[HISTORICAL_DATA_TRUST_DECISION_RECORD.md](HISTORICAL_DATA_TRUST_DECISION_RECORD.md)
supersedes the earlier independent-evidence prerequisites for normal project trust
and production promotion. The original foundation design below is preserved as
implementation history and remains the strict supplementary external-audit policy.
Its earlier diagnostic-only and production-boundary statements describe that slice,
not the current service behavior.

Normal-use Drivers / Original trust now follows one generic adapter in
`verification/canonical.py`: approved immutable F1DB snapshot, deterministic
supported reconstruction, integrity/invariant checks, and exact full-population
canonical championship reconciliation. `CanonicalTrustAssessment` reuses the
passed/blocked/stale/error states, comparison outcomes, findings and exact standings
comparator. It separately exposes `canonical_dataset_backed`, `comparison`, derived
`trusted_for_normal_use`, and optional `external_audit`. Snapshot changes are stale;
operational exceptions remain errors. An unsupported or ambiguous result cannot
become trusted merely by matching totals. No per-season trust branches exist.

The service binds reads and calculation to snapshots identified before and after
each request. Integrity checks cover calendar/results population and identities,
supported classification/participation states, source-to-award trace, exact awards,
constructor contributions, countback and margins. Reconciliation checks every
driver's membership, exact points, sporting position and classification, plus
championship-won consistency. Unknown upstream claim-level F1DB lineage is documented
and non-blocking. This is canonical reconciliation, not independent corroboration.

The service/API expose results only when the canonical assessment passes; failures
return unavailable with findings and null champion/runner-up/margin. Operational
source/programming failures remain server errors. Existing capabilities describe
implemented package support, not a promise that every source/request will pass.
The frontend already respects availability and needs no additional evidence gate.
Scoring and source records are unchanged.

2010's completed external audit is preserved as snapshot/package-bound supplementary
summary data in `apps/backend/historical/external_audit_summaries.json`, attributed to the
approved decision record and retaining the provisional-classification qualification.
It is not a fabricated strict evaluator dossier. No audit summary is asserted for
2011-2013. Absence of external audit evidence, including for 2010, does not block
canonical trust. Further primary-source research is exception handling for
reconciliation failures, conflicts, unsupported interpretations or selected edge cases.

The strict `evaluate_verification` and evidence schemas retain provenance,
human-review, ambiguity and fail-closed tests. Their `historically_verified` claim
still means strict independent verification, distinct from normal-use trust and
from the preserved research summary. Synthetic assessments cannot confer historical
trust. No F1DB-derived expectation is labelled independent.

For normal-use trust, the earlier clean-Git/independent-metadata prerequisites are
superseded: the service freshly evaluates actual inputs, identified by dataset/rules
hashes and calculation/policy versions, without requiring a committed checkout.
The diagnostic shares the service path and reports Git identity/dirty state as
information; it does not certify a clean implementation commit. The strict external
evaluator retains its clean-Git requirement. Constructors, counterfactual scoring
and broader historical support remain outside this implementation.

## Original foundation design (preserved)

Original status: approved architecture and product-owner refinements; first
implementation slice only. This foundation did not activate a production gate or
expand coverage. Milestone 1A/1B methodology remained authoritative.

## Authority and verification standard

Implemented, reconstructable, verified and production-supported are distinct.
F1DB's pinned SHA-256 identifies immutable recorded event facts. Ordinary F1DB
rows do not need duplicate external citations. Project evidence establishes
regulations, applicability, completion/event scope, amendments, exceptional
interpretations and independent final standings. Python executes supported rules;
it and the model are not historical authorities. An audit reports conclusions
about a specific context, not new historical truth. The frontend is presentation.

Verified means a complete official final Drivers classification agrees exactly
with the deterministic Original reconstruction: driver population, rational points,
sporting positions and classification states. Correct champions, top-N matches,
or matching F1DB tables alone are insufficient. Relevant rules, completion, event
scope and amendment review must have accepted evidence. Source-integrity and
calculation-invariant checks must pass; unresolved material ambiguity blocks.
Explicit ties/unranked/excluded states must not be replaced with display ordering.

Verification does not universally require proving every event participant absent
from a published championship table. An omission blocks when it materially affects
membership, eligibility, points, classification or sporting order. Nonmaterial
participant diagnostics can remain informational. Optional identity/chassis fields
are outside this verification scope.

## Independent evidence and fail-closed policy

Expectations must not be generated by the scoring implementation or exported from
F1DB and relabelled independent. Expected values and their evidence require human
review. Accepted evidence records preserve document locators, source summaries,
project interpretation, applicability and reviewer identity/date. A syntactically
valid document or declared independence cannot establish real-world truth by itself.
No source downloads, automatic fixture updates or support promotion are provided.

Missing, incomplete, disputed or materially ambiguous evidence blocks verification.
Unknown points are null, never zero; comparisons use Fraction, never tolerance or
display rounding. An exact match still cannot override missing prerequisites.
All simultaneous findings are retained. Errors remain distinct from evidence gaps.
Material source mismatches must be investigated; database rows must never be
changed to obtain agreement.

Synthetic metadata is visibly labelled and assessed only under an explicit
synthetic scope. A synthetic PASSED assessment means the policy test passes;
it can never confer `historically_verified`. Default evaluation is historical.
No real historical evidence is supplied by this slice.

JSON loading and in-memory evaluation share the same metadata validation rules.
Evaluation projects typed metadata to the wire schema and reuses the strict parser;
direct construction or dataclass replacement cannot bypass provenance validation.
Historical scope rejects synthetic sources, and accepted claims require intact
source references. Invalid metadata yields blocking findings and is not compared.
Metadata hashes are derived read-only properties, not independently supplied fields.

## Context and status

Context contains F1DB SHA-256, validated evidence/fixture content hash, relevant
rules content hash, policy/schema version and Git commit identity. Dirty working
trees or unavailable Git identity are non-reproducible and cannot verify. No
elaborate code fingerprinting is attempted. Inputs and context are immutable
during a run; the caller must bind its reconstruction to those inputs.

Hashes identify the authored validated representation: object keys are sorted,
parsed fractions are reduced, and array order is retained. This is not semantic
canonicalization. Harmless reorderings can intentionally cause conservative
staleness. Evaluation compares hashes derived from its validated metadata against
the context; it cannot accept another payload merely because an old hash was supplied.

States are passed, blocked, stale and error. Reconstruction and expected
comparison outcomes are separate. Typed findings describe evidence, data,
capability, ambiguity, exact mismatch and reproducibility issues. Operational error
takes precedence over stale context, which takes precedence over blocked; findings
are retained regardless. A changed previous context requires a fresh evaluation,
not reuse of its old success. No stored state-transition workflow is introduced.
`historically_verified` is derived from historical scope and PASSED state, never
an independently mutable flag. Only an evaluation satisfying the historical
evidence/provenance requirements may yield that combination.

The evaluator trusts typed source/invariant check results supplied by its adapter;
both default to false and require actual booleans. Evaluation checks identity with
True rather than truthiness. `source_checks_not_passed` means that prerequisite
has not passed; `source_data_missing` is reserved for known missing required data.
An unknown expected event scope is missing season evidence, not proof of absent
source data. In a complete population, every TIED row must share its sporting
position with at least one other TIED driver; this imposes no new tie-break rule.
This slice does not implement universal historical source
integrity, countback-trace validation, or missing scoring operations. Those checks
must be supplied and tested before later historical promotion.

## Production boundary and diagnostic

Current service/API capabilities and 2010-2013 availability remain unchanged.
The verification modules are not imported by production services. Their new status
does not retroactively change the meaning of existing PoC support.

The fixed four-season diagnostic uses existing scoring without modifying it,
checks internal award/contribution/margin reconciliation, and reports F1DB
differences separately. It supplies no historical metadata and therefore always
blocks independent verification, even when all F1DB differences are zero. F1DB
reconciliation retains the existing calculator's semantics and is not proof of
external exactness or evidence coverage.

Production promotion requires a separately approved slice: accepted independent
baseline evidence, current-context verification, tested API exposure policy and
then activation of the gate. No grandfathering into independently verified status.
The legacy Streamlit prototype remains untouched. Constructors, counterfactual
scoring, full-history auditing, CI and frontend work are out of scope.

## Canonical trust architecture clarification

Under the superseding historical-data policy, the runtime approval authority is
`apps/backend/historical/canonical_snapshot.json`. Each normal-use assessment binds
source reads and the independent complete championship population to one captured
snapshot image. Matching supplied subsets do not establish completeness.
Supplementary audit summaries enrich an already completed canonical assessment;
missing or invalid summaries cannot change production trust. Completed but rejected
calculations retain diagnostic counts while production result fields stay unavailable.
The strict evidence foundation above remains authoritative for explicit independent
verification claims, not a canonical normal-use production gate.
