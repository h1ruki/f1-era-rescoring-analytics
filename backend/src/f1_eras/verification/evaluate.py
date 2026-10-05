"""Strict supplementary independent-audit policy; not the normal-use trust gate."""

from f1_eras.domain.verification import (
    AssessmentState, ComparisonOutcome, FindingCode, POLICY_VERSION,
    ReconstructionCheck, ReconstructionOutcome, SCHEMA_VERSION,
    VerificationAssessment, VerificationContext, VerificationFinding,
    VerificationScope, ordered_findings,
)
from f1_eras.verification.compare import compare_standings
from f1_eras.verification.metadata import (
    HistoricalMetadata, MetadataError, ReviewState, RuleTopic, validate_metadata,
)


def evaluate_verification(
    *, year: int, package_id: str, implementation_id: str,
    reconstruction: ReconstructionCheck, context: VerificationContext,
    metadata: HistoricalMetadata | None,
    scope: VerificationScope = VerificationScope.HISTORICAL,
    previous_context: VerificationContext | None = None,
) -> VerificationAssessment:
    """Assess this attempt; previous assessments are never reused as proof.

    An explicit synthetic scope exercises the same gates but cannot confer
    historical verification. A changed previous context yields STALE; a fresh
    evaluation without that previous context is needed to obtain verification.
    Source/invariant checks belong to the reconstruction adapter, never to the
    expected fixture. The default false check flags fail closed.
    """
    findings = list(reconstruction.findings)

    def add(code: FindingCode, message: str, subject: str = "season") -> None:
        findings.append(VerificationFinding(code, message, subject))

    if type(year) is not int or year < 1 or not package_id or not implementation_id:
        raise ValueError("A positive year, package_id and implementation_id are required")
    if not isinstance(scope, VerificationScope):
        raise ValueError("scope must be VerificationScope")
    if (reconstruction.year != year or reconstruction.package_id != package_id
            or reconstruction.implementation_id != implementation_id):
        add(FindingCode.METADATA_INVALID, "Reconstruction year/package/implementation does not match assessment")
    if (context != reconstruction.context
            or previous_context is not None and context != previous_context
            or context.policy_version != POLICY_VERSION or context.schema_version != SCHEMA_VERSION):
        add(FindingCode.CONTEXT_STALE, "Assessment/reconstruction context or policy does not match current context")
    if context.working_tree_dirty or context.implementation_commit is None:
        add(FindingCode.NON_REPRODUCIBLE, "A clean working tree and known implementation commit are required")
    if reconstruction.outcome == ReconstructionOutcome.ERROR:
        add(FindingCode.ASSESSMENT_ERROR, "Reconstruction encountered an operational or programming error")
    elif reconstruction.outcome != ReconstructionOutcome.COMPLETED:
        add(FindingCode.RECONSTRUCTION_UNAVAILABLE, "Reconstruction has not completed")
    if reconstruction.source_checks_passed is not True:
        add(FindingCode.SOURCE_CHECKS_NOT_PASSED, "Required source-integrity checks have not passed")
    if reconstruction.invariant_checks_passed is not True:
        add(FindingCode.INVARIANTS_UNCHECKED, "Required reconstruction invariants have not passed")

    metadata_invalid = False
    if metadata is not None:
        try:
            metadata = validate_metadata(metadata)
        except MetadataError as error:
            add(FindingCode.METADATA_INVALID, str(error))
            metadata_invalid = True
            metadata = None  # Invalid evidence must not reach comparison or trust checks.

    claims = {claim.id: claim for claim in metadata.claims} if metadata else {}

    def evidence(ids: tuple[str, ...], code: FindingCode, subject: str) -> None:
        if not ids:
            add(code, "Required evidence is absent", subject)
        for claim_id in ids:
            claim = claims.get(claim_id)
            if claim is None:
                add(FindingCode.METADATA_INVALID, "Evidence reference cannot be resolved", claim_id)
                continue
            if claim.review == ReviewState.DISPUTED:
                add(FindingCode.EVIDENCE_CONFLICT, "Evidence claim is disputed", claim_id)
            elif claim.review != ReviewState.ACCEPTED:
                add(FindingCode.EVIDENCE_NOT_ACCEPTED, "Evidence claim has not been accepted", claim_id)
            if year not in claim.applicable_years:
                add(code, "Evidence does not establish applicability to this year", subject)

    if metadata:
        if context.metadata_sha256 != metadata.content_sha256 or context.rules_sha256 != metadata.rules_sha256:
            add(FindingCode.CONTEXT_STALE, "Metadata/package content does not match verification context")
        if metadata.scope != scope:
            add(FindingCode.SYNTHETIC_EVIDENCE, "Synthetic and historical assessment scopes cannot be mixed")
    elif context.metadata_sha256 is not None and not metadata_invalid:
        add(FindingCode.CONTEXT_STALE, "Context identifies metadata that was not supplied")

    rules = metadata.rules if metadata else None
    if rules is None:
        add(FindingCode.RULE_EVIDENCE_MISSING, "No independently evidenced source-year rules package")
    else:
        if rules.id != package_id or rules.source_year != year or rules.implementation_id != implementation_id:
            add(FindingCode.METADATA_INVALID, "Rule package/year/implementation does not match requested reconstruction")
        evidence(rules.applicability_evidence, FindingCode.RULE_EVIDENCE_MISSING, "rules:applicability")
        provisions = {provision.topic: provision for provision in rules.provisions}
        for topic in RuleTopic:
            evidence(provisions[topic].evidence_ids if topic in provisions else (),
                     FindingCode.RULE_EVIDENCE_MISSING, f"rules:{topic.value}")

    season = metadata.season if metadata else None
    if season is None:
        add(FindingCode.SEASON_EVIDENCE_MISSING, "No evidenced completion, event scope or amendment review")
    else:
        if season.year != year:
            add(FindingCode.METADATA_INVALID, "Season context year does not match")
        if season.completion != "complete":
            add(FindingCode.SEASON_NOT_COMPLETE, "Completed season is not established")
        for name, refs in (("completion", season.completion_evidence),
                           ("event_scope", season.event_scope_evidence),
                           ("amendments", season.amendment_evidence)):
            evidence(refs, FindingCode.SEASON_EVIDENCE_MISSING, f"season:{name}")
        if not season.event_ids:
            add(FindingCode.SEASON_EVIDENCE_MISSING, "Expected championship event population is not established")
        if reconstruction.outcome == ReconstructionOutcome.COMPLETED:
            if set(season.event_ids) - set(reconstruction.event_ids):
                add(FindingCode.SOURCE_DATA_MISSING, "Required events from evidenced scope are missing from reconstruction")
            if (len(reconstruction.event_ids) != len(set(reconstruction.event_ids))
                    or set(season.event_ids) != set(reconstruction.event_ids)):
                add(FindingCode.SOURCE_DATA_INCONSISTENT, "Reconstructed event population differs from evidenced event scope")
        for ambiguity in season.material_ambiguities:
            add(FindingCode.HISTORICAL_AMBIGUITY, ambiguity)

    comparison = ComparisonOutcome.NOT_RUN
    expected = metadata.expected if metadata else None
    if expected is None:
        add(FindingCode.EXPECTED_EVIDENCE_MISSING, "Independent final championship standings are absent")
    else:
        if expected.year != year:
            add(FindingCode.METADATA_INVALID, "Expected standings year does not match")
        if expected.independence != "independent":
            add(FindingCode.EXPECTED_NOT_INDEPENDENT, "Expectations must be independent of F1DB and reconstruction")
        if expected.result_basis != "final_amended":
            add(FindingCode.EXPECTED_INFORMATION_INCOMPLETE, "Final amended result basis is not established")
        evidence(expected.evidence_ids, FindingCode.EXPECTED_EVIDENCE_MISSING, "expected:classification")
        for row in expected.rows:
            evidence(row.evidence_ids or expected.evidence_ids,
                     FindingCode.EXPECTED_EVIDENCE_MISSING, row.standing.driver_id)
        if reconstruction.outcome == ReconstructionOutcome.COMPLETED:
            result = compare_standings(reconstruction.standings, expected)
            comparison = result.outcome
            findings.extend(result.findings)

    state = AssessmentState.PASSED
    if any(item.blocking for item in findings):
        state = AssessmentState.BLOCKED
    if any(item.code == FindingCode.CONTEXT_STALE for item in findings):
        state = AssessmentState.STALE
    if any(item.code == FindingCode.ASSESSMENT_ERROR for item in findings):
        state = AssessmentState.ERROR
    return VerificationAssessment(year, package_id, scope, state, reconstruction.outcome,
                                  comparison, context, ordered_findings(findings))
