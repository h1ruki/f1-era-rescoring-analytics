# Historical verification metadata

## Current canonical trust policy

[HISTORICAL_DATA_TRUST_DECISION_RECORD.md](../../HISTORICAL_DATA_TRUST_DECISION_RECORD.md)
supersedes the earlier requirement to populate independent evidence before normal
project trust or production promotion. Immutable canonical F1DB input, supported
deterministic reconstruction, passing integrity checks and exact full championship
reconciliation now suffice, through one shared service/diagnostic adapter.
F1DB standings are explicitly canonical comparison records, never independent
verification fixtures. Unknown upstream claim-level lineage is non-blocking.

`external_audit_summaries.json` preserves the completed 2010 research outcome from
the approved decision record. Each summary identifies year, package, dataset hash,
decision-record locator, scope and qualification. Lookup is generic and requires
all three context identifiers to match. The FIA provisional-classification heading
is retained. This summary supplies no invented reviewer, retrieval date or official
standings transcription and does not confer a strict evaluator success.
No supplementary audit summary is populated for 2011-2013; its absence does not
block normal-use trust. The 2010 record retains its original `v2026.15.0` hash.
The current `v2026.16.0` approval does not transfer that audit: all four current
season assessments have no matching supplementary audit, without blocking canonical
trust. The previous approval and 2026-10-05 rotation remain documented in the
historical-data trust decision record.

No complete historical evidence/expected-standings bundle is populated. The strict
bundle schema and evaluator below remain useful for supplementary independent audits
and historical exceptions. Missing evidence blocks that stricter claim, not normal
canonical trust. Primary-source research is reserved for reconciliation failures,
conflicting records, unsupported interpretations or selected edge-case research.

## Runtime approval and repository population binding

`canonical_snapshot.json` is the sole machine-readable runtime approval record.
It contains the approved upstream release, release commit, SHA-256 and byte size.
Its loader rejects missing/unreadable files, invalid fields and duplicate keys;
invalid approval cannot grant canonical trust. Historical documentation may retain
prior identities but is not runtime configuration.

All assessment source rows and an independent unfiltered championship driver-ID
population are queried from the same captured, integrity-checked SQLite image.
Population completeness cannot be inferred from two matching supplied subsets.
Ranked zero-point drivers and sporting ordering remain part of reconciliation.

Audit summaries are loaded only by separate post-assessment enrichment. Missing
metadata is `unavailable`; unreadable, malformed or invalid records are `invalid`.
Neither changes canonical trust or production availability. Genuine canonical
errors are not handled by this optional loader. Snapshot-bound audit records keep
their original hashes across source rotations unless a separate reviewed audit
transfer is explicitly recorded; no new audit is implied by matching calculations.

A future snapshot approval follows provenance/schema/integrity review, full supported
historical input and result comparison, negative trust regressions and product-owner
approval. Activate the manifest and source together with readers stopped, retaining
a known-good rollback. Ordinary source updates do not require season-specific logic.

## Original independent-evidence bundle schema (retained)

The standard-library loader in `f1_eras.verification.metadata` reads a strict
JSON bundle for one Drivers / Original season. A bundle contains `schema_version`,
`scope`, `category`, `scoring`, `sources`, `claims`, `rules`, `season`, and `expected`.
Unknown fields, duplicate JSON keys/IDs/references, floating-point numbers,
nonfinite numbers and dangling references are rejected. Optional missing evidence
is represented explicitly by empty reference arrays or null sections and blocks
verification. It is never defaulted to accepted evidence.

`validate_metadata()` is the evaluation boundary for directly constructed/replaced
Python records as well as loaded files. It projects records to this same wire
schema and reuses the strict parser, returning a validated immutable copy. There
is no second set of provenance rules in the evaluator. Invalid metadata blocks
assessment and cannot reach the standings comparison.

`content_sha256` and `rules_sha256` are derived read-only properties, never supplied
constructor fields. They hash the validated representation with sorted object keys
and reduced Fraction values. Arrays retain authored order: this is not semantic
canonicalization, and harmless reordering intentionally causes conservative
staleness. The evaluator checks these derived hashes against the context, so
changed content cannot keep another payload's provenance binding.

Sources record document identity/location, publisher, dates and known lineage.
Claims keep source locators, source summaries, project interpretations,
applicability and review state separately. Accepted claims require source
references, a reviewer and review date. Acceptance is a human-reviewed assertion;
the loader cannot prove a document's authority or a transcription's accuracy.

Rule evidence covers each `RuleTopic`, including provisions that are explicitly
inapplicable, and package applicability. This schema records evidence; it does
not implement a new scoring rule language. Season context records the evidenced
event population, completion, amendment review and material ambiguities. Evidence
claims can describe sanctions/decisions without applying them as executable rules.

Expected standings declare complete/partial/unknown population, independent/F1DB/
reconstruction/unknown lineage, and final-amended/provisional/unknown result basis.
Each row holds a stable driver ID, original source label, points, sporting position,
classification state and optional row evidence references. Row references add to
the required whole-classification evidence. They can document amendments or ID
mapping exceptions without repeating document citations. No champion flag is
required: the complete sporting classification already identifies the winner.

Points use `{"numerator": integer, "denominator": positive_integer}` and become
`Fraction`. Null points mean incomplete evidence, never zero. Ranked and explicitly
tied rows require a positive sporting position; unranked/excluded rows have null
position. Unknown classification is representable but cannot verify. Explicit ties
are compared as recorded; neither row order nor driver ID resolves sporting ties.
For complete populations, a TIED row requires at least one counterpart at the same
sporting position, with every member of that position group explicitly TIED.

The only example bundle lives under `backend/tests/fixtures/synthetic/`. Its scope,
source kind and title label it as synthetic. It must never be moved into historical
coverage or relabelled as evidence. Tests explicitly request synthetic assessment
scope; a synthetic PASSED assessment has `historically_verified == False`. Generic
assessment states are passed/blocked/stale/error. Historical verification remains
derived from historical scope plus PASSED, after all evidence requirements pass.

The original foundation required a separately approved independent-evidence slice
before activating production verification. That production prerequisite is now
superseded by the historical-data trust record; the strict evidence requirements
still apply to an independent-audit claim. Future reviewed bundles may live here.
No automatic generation,
expected-output update, source download or promotion facility is provided.
