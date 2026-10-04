# Historical verification metadata

No historical evidence or expected standings are populated in this slice.
F1DB standings are not independent verification fixtures.

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

Future reviewed bundles may live here, but adding them and activating production
verification require a separately approved slice. No automatic generation,
expected-output update, source download or promotion facility is provided.
