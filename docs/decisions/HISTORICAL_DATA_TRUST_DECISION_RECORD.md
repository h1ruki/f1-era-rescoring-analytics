# Historical data trust â€” methodology decision record

Status: **Approved by the product owner.** This record preserves the
completed 2010 research outcome and records the product-owner methodology
decision. It does not change verification behaviour or production support.

## Scope and relationship to existing decisions

2010 Drivers / Original is the project's independent historical audit and
deep-validation exemplar.

On approval, this record supersedes the independent-external-evidence
requirements in VERIFICATION_FOUNDATION_DECISION_RECORD.md insofar as they
make external historical auditing a prerequisite for normal project trust
or production promotion. Implementing that policy is separate work.

Milestone 1A/1B scoring, historical interpretation, identity, ambiguity and
unavailable-state requirements remain authoritative.

## Established F1DB snapshot provenance (initial approval)

At initial policy approval, the checked-in `f1db.db` snapshot had the following
established provenance. The later rotation below preserves this original record:

- Upstream release: `v2026.15.0`
- Release commit: `45c6c50fb3d87ef39a0631c7472ea3e597699b4a`
- Checked-in database SHA-256:
  `6249c3d8e361b5358981a1dfba6a34218a471af35b5f3ab6d6deb19638ac5a71`

Snapshot provenance identifies the dataset; it does not establish exact
claim-level historical source lineage inside F1DB. That lineage remains
unknown.

## Completed 2010 independent historical audit

Independent research recovered and inspected the applicable February 2010
FIA Sporting Regulations and corroborated the relevant scoring,
all-results, partial-points and championship-countback provisions.

The completed 19-event season population and complete 27-driver
championship ordering and points were externally checked.

FIA post-season material externally corroborated the complete standings
outside the local reconstruction while retaining a "provisional
classification" heading. That heading is
preserved as a source qualification; the material is not described as an
unqualified final classification.

Championship-affecting race-result amendments were investigated and
confirmed to be reflected in the historical final state used for the audit.

These statements preserve the completed research outcome. They do not
assert additional historical findings or equivalent external audit
coverage for other seasons.

## Product-owner methodology decision

- F1DB is the canonical historical dataset for F1 ERAs.
- Historical source data is treated as trusted project input unless a
  concrete inconsistency is identified.
- Original reconstruction becomes trusted for normal project use when
  the deterministic reconstruction reconciles against the canonical F1DB
  championship data and integrity checks pass.
- Independent external historical auditing is supplementary, not a
  production gate.
- 2010 is retained as the deep-validation exemplar.
- Further primary-source historical research is triggered only by
  reconciliation failures, conflicting records, unsupported rule
  interpretation, or deliberately selected historical edge cases.
- Unknown upstream lineage is documented but does not by itself make an
  externally retrieved oracle circular.
- An oracle copied directly from the same reconstruction input does not
  count as independent corroboration.

Canonical reconciliation and independent external corroboration remain
distinct claims. Trust for normal project use does not imply that every
season has received an independent historical audit.

## Implementation boundary

This record does not modify `f1db.db`, scoring, verification evaluation,
metadata schemas, diagnostic outcomes, API availability or support status.

The trust-model implementation and corresponding documentation updates
require a separate reviewed change. Existing behaviour remains unchanged
until that work is approved and implemented.

## Implementation reference

The approved methodology above is unchanged. The corresponding implementation uses
`backend/historical/canonical_snapshot.json` as its machine-readable runtime snapshot
approval authority. The initial approved identity above is preserved; the current
identity is recorded in that manifest and the rotation entry below.
An invalid or absent approval record fails closed.

The current canonical file is `data/f1db.db`, relative to the repository root.
Its relocation from root `f1db.db` preserves the approved bytes and snapshot
identity. The provenance and rotation entries retain their historical filenames.

Complete reconciliation includes the unfiltered championship driver population
queried independently of supplied comparison inputs in the same bound source image.
Optional external-audit metadata is attached after canonical assessment and cannot
change trust. Source rotation requires its own provenance, schema, integrity and
supported-history validation review and explicit approval; existing external-audit
snapshot bindings are preserved rather than automatically transferred.

The earlier implementation-boundary section records this policy document's original
scope; it is not a claim that a subsequent reviewed implementation must retain the
superseded production gate.

## Approved snapshot rotation (2026-10-05)

Following the product-owner rotation instruction and successful provenance/safety
checks, the canonical snapshot is now [F1DB v2026.16.0](https://github.com/f1db/f1db/releases/tag/v2026.16.0),
published **2026-10-04 12:21:35 UTC**, release commit
`2ba943cf908ace7d6b606e12b72472f54d442a12`.

The official `f1db-sqlite.zip` asset has SHA-256
`efd54b0fb99115024bc56c38871c8b03fead428051f895e0f44ff9a20d6acbab`.
Its checksum was checked against both GitHub's asset digest and the released
`checksums_sha256.txt`. The contained `f1db.db` was compared byte-for-byte with
the local candidate: **73,777,152 bytes**, database SHA-256
`28707a41bc45d9d4b787d655ef7e135644bdc9cb3307a947258647d83ecba642`.

Schema and integrity checks passed. All consumed 2010-2013 historical inputs were
identical to the previous snapshot and complete reconstruction reconciled without
scoring or historical expectation changes. The approval manifest was updated and
the canonical database replaced with those verified bytes.

The previous `v2026.15.0` snapshot remains recoverable from Git history. The 2010
external-audit summary keeps its original snapshot hash; it was not transferred
to `v2026.16.0`. Current responses therefore have no matching external-audit summary,
while all four seasons remain eligible for canonical normal-use trust. No new
independent historical audit is claimed.
