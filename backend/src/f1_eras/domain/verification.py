"""Verification contracts, separate from calculation and production availability."""

from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction


POLICY_VERSION = "drivers-original-verification-v1"
SCHEMA_VERSION = 1


class VerificationScope(StrEnum):
    HISTORICAL = "historical"
    SYNTHETIC = "synthetic"


class AssessmentState(StrEnum):
    PASSED = "passed"
    BLOCKED = "blocked"
    STALE = "stale"
    ERROR = "error"


class ReconstructionOutcome(StrEnum):
    NOT_ATTEMPTED = "not_attempted"
    COMPLETED = "completed"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class ComparisonOutcome(StrEnum):
    NOT_RUN = "not_run"
    MATCH = "match"
    MISMATCH = "mismatch"
    INCOMPLETE = "incomplete"


class ClassificationState(StrEnum):
    RANKED = "ranked"
    TIED = "tied"
    UNRANKED = "unranked"
    EXCLUDED = "excluded"
    UNKNOWN = "unknown"


class FindingCode(StrEnum):
    RULE_EVIDENCE_MISSING = "rule_evidence_missing"
    EXPECTED_EVIDENCE_MISSING = "expected_evidence_missing"
    SEASON_EVIDENCE_MISSING = "season_evidence_missing"
    EVIDENCE_NOT_ACCEPTED = "evidence_not_accepted"
    EVIDENCE_CONFLICT = "evidence_conflict"
    EXPECTED_NOT_INDEPENDENT = "expected_not_independent"
    SYNTHETIC_EVIDENCE = "synthetic_evidence"
    METADATA_INVALID = "metadata_invalid"
    SOURCE_DATA_MISSING = "source_data_missing"
    SOURCE_CHECKS_NOT_PASSED = "source_checks_not_passed"
    SOURCE_DATA_INCONSISTENT = "source_data_inconsistent"
    CAPABILITY_UNIMPLEMENTED = "capability_unimplemented"
    HISTORICAL_AMBIGUITY = "historical_ambiguity"
    SEASON_NOT_COMPLETE = "season_not_complete"
    POPULATION_INCOMPLETE = "population_incomplete"
    EXPECTED_INFORMATION_INCOMPLETE = "expected_information_incomplete"
    MISSING_DRIVER = "missing_driver"
    UNEXPECTED_DRIVER = "unexpected_driver"
    POINTS_MISMATCH = "points_mismatch"
    POSITION_MISMATCH = "position_mismatch"
    CLASSIFICATION_MISMATCH = "classification_mismatch"
    RECONSTRUCTION_UNAVAILABLE = "reconstruction_unavailable"
    INVARIANTS_UNCHECKED = "invariants_unchecked"
    CONTEXT_STALE = "context_stale"
    NON_REPRODUCIBLE = "non_reproducible"
    ASSESSMENT_ERROR = "assessment_error"
    PARTICIPANT_DIAGNOSTIC = "participant_diagnostic"


@dataclass(frozen=True, slots=True)
class VerificationFinding:
    code: FindingCode
    message: str
    subject: str = "season"
    field: str | None = None
    expected: str | None = None
    actual: str | None = None

    @property
    def blocking(self) -> bool:
        # Only nonmaterial participant diagnostics are informational. There is
        # deliberately no general-purpose flag to waive a failed requirement.
        return self.code != FindingCode.PARTICIPANT_DIAGNOSTIC


def ordered_findings(findings: list[VerificationFinding]) -> tuple[VerificationFinding, ...]:
    return tuple(sorted(set(findings), key=lambda item: (
        item.code.value, item.subject, item.field or "", item.expected or "",
        item.actual or "", item.message,
    )))


@dataclass(frozen=True, slots=True)
class StandingValue:
    driver_id: str
    points: Fraction | None
    position: int | None
    classification: ClassificationState

    def __post_init__(self) -> None:
        if not isinstance(self.driver_id, str) or not self.driver_id.strip():
            raise ValueError("driver_id must be nonempty")
        if self.points is not None and not isinstance(self.points, Fraction):
            raise ValueError("points must be Fraction or None, never float")
        if self.position is not None and (type(self.position) is not int or self.position < 1):
            raise ValueError("position must be a positive integer or None")
        if not isinstance(self.classification, ClassificationState):
            raise ValueError("classification must be ClassificationState")


@dataclass(frozen=True, slots=True)
class VerificationContext:
    f1db_sha256: str
    metadata_sha256: str | None
    rules_sha256: str
    implementation_commit: str | None
    working_tree_dirty: bool
    policy_version: str = POLICY_VERSION
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for value in (self.f1db_sha256, self.metadata_sha256, self.rules_sha256):
            if value is not None and (type(value) is not str or len(value) != 64
                                      or any(c not in "0123456789abcdef" for c in value)):
                raise ValueError("context hashes must be lowercase SHA-256 values")
        if self.f1db_sha256 is None or self.rules_sha256 is None:
            raise ValueError("source and rules context hashes are required")
        if self.implementation_commit is not None and (
            type(self.implementation_commit) is not str or len(self.implementation_commit) != 40
            or any(c not in "0123456789abcdef" for c in self.implementation_commit)
        ):
            raise ValueError("implementation_commit must be a full Git SHA or None")
        if type(self.working_tree_dirty) is not bool:
            raise ValueError("working_tree_dirty must be boolean")
        if type(self.schema_version) is not int or self.schema_version < 1:
            raise ValueError("schema_version must be a positive integer")
        if type(self.policy_version) is not str or not self.policy_version.strip():
            raise ValueError("policy_version must be nonempty")


@dataclass(frozen=True, slots=True)
class ReconstructionCheck:
    outcome: ReconstructionOutcome
    context: VerificationContext
    year: int
    package_id: str
    implementation_id: str
    standings: tuple[StandingValue, ...] = ()
    event_ids: tuple[int, ...] = ()
    source_checks_passed: bool = False
    invariant_checks_passed: bool = False
    findings: tuple[VerificationFinding, ...] = ()

    def __post_init__(self) -> None:
        for field in ("source_checks_passed", "invariant_checks_passed"):
            if type(getattr(self, field)) is not bool:
                raise ValueError(f"{field} must be an actual boolean")


@dataclass(frozen=True, slots=True)
class StandingComparison:
    outcome: ComparisonOutcome
    findings: tuple[VerificationFinding, ...]


@dataclass(frozen=True, slots=True)
class VerificationAssessment:
    year: int
    package_id: str
    scope: VerificationScope
    state: AssessmentState
    reconstruction: ReconstructionOutcome
    comparison: ComparisonOutcome
    context: VerificationContext
    findings: tuple[VerificationFinding, ...]

    @property
    def historically_verified(self) -> bool:
        return self.scope == VerificationScope.HISTORICAL and self.state == AssessmentState.PASSED
