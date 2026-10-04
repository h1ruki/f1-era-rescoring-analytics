"""Strict, standard-library JSON schemas for reviewed evidence and expectations.

A bundle contains one Drivers / Original season. It can be incomplete, but
unknown fields, lossy numbers, duplicate identities and dangling references are
invalid. Valid syntax never implies accepted historical evidence.
"""

from dataclasses import asdict, dataclass
from datetime import date
from enum import StrEnum
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from typing import Any, TypeVar

from f1_eras.domain.verification import (
    ClassificationState, SCHEMA_VERSION, StandingValue, VerificationScope,
)


class MetadataError(ValueError):
    """A historical metadata document does not satisfy the schema."""


class ReviewState(StrEnum):
    DRAFT = "draft"
    ACCEPTED = "accepted"
    DISPUTED = "disputed"
    SUPERSEDED = "superseded"


class PopulationCoverage(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class RuleTopic(StrEnum):
    AWARDS = "awards"
    ELIGIBILITY = "eligibility"
    RESULT_LIMITS = "result_limits"
    COUNTBACK = "countback"
    SPRINT = "sprint"
    FASTEST_LAP = "fastest_lap"
    SHORTENED_EVENTS = "shortened_events"
    SHARED_PARTICIPATION = "shared_participation"
    MULTIPLIERS = "multipliers"
    SANCTIONS = "sanctions"
    EXCLUSIONS = "exclusions"


@dataclass(frozen=True, slots=True)
class SourceRecord:
    id: str
    kind: str
    publisher: str
    title: str
    location: str
    published_on: str | None
    retrieved_on: str | None
    lineage: str


@dataclass(frozen=True, slots=True)
class SourceReference:
    source_id: str
    locator: str


@dataclass(frozen=True, slots=True)
class EvidenceClaim:
    id: str
    references: tuple[SourceReference, ...]
    summary: str
    interpretation: str
    applicable_years: tuple[int, ...]
    review: ReviewState
    reviewed_by: str | None
    reviewed_on: str | None


@dataclass(frozen=True, slots=True)
class RuleProvision:
    topic: RuleTopic
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RulePackageEvidence:
    id: str
    source_year: int
    implementation_id: str
    applicability_evidence: tuple[str, ...]
    provisions: tuple[RuleProvision, ...]


@dataclass(frozen=True, slots=True)
class SeasonContext:
    year: int
    completion: str
    event_ids: tuple[int, ...]
    completion_evidence: tuple[str, ...]
    event_scope_evidence: tuple[str, ...]
    amendment_evidence: tuple[str, ...]
    material_ambiguities: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExpectedDriver:
    standing: StandingValue
    source_label: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExpectedStandings:
    year: int
    population: PopulationCoverage
    independence: str
    result_basis: str
    evidence_ids: tuple[str, ...]
    rows: tuple[ExpectedDriver, ...]


@dataclass(frozen=True, slots=True)
class HistoricalMetadata:
    scope: VerificationScope
    sources: tuple[SourceRecord, ...]
    claims: tuple[EvidenceClaim, ...]
    rules: RulePackageEvidence | None
    season: SeasonContext | None
    expected: ExpectedStandings | None
    @property
    def content_sha256(self) -> str:
        return content_hash(_validated_document(self))

    @property
    def rules_sha256(self) -> str:
        return content_hash(_validated_document(self)["rules"])


def content_hash(value: Any) -> str:
    """Hash a JSON representation: sorted object keys, order-sensitive arrays.

    This is not semantic canonicalization. Harmless array reordering may cause
    conservative staleness. Parsed rational points use Fraction's reduced form.
    """
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")).hexdigest()


def _object(value: Any, fields: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != set(fields.split()):
        raise MetadataError(f"Expected exactly these object fields: {fields}")
    return value


def _text(value: Any) -> str:
    if type(value) is not str or not value.strip():
        raise MetadataError("Expected nonempty text")
    return value


def _integer(value: Any) -> int:
    if type(value) is not int or value < 1:
        raise MetadataError("Expected positive integer (not boolean)")
    return value


def _list(value: Any) -> list[Any]:
    if type(value) is not list:
        raise MetadataError("Expected JSON array")
    return value


def _texts(value: Any) -> tuple[str, ...]:
    result = tuple(_text(item) for item in _list(value))
    _unique(result)
    return result


def _integers(value: Any) -> tuple[int, ...]:
    result = tuple(_integer(item) for item in _list(value))
    _unique(result)
    return result


def _unique(values: tuple[Any, ...]) -> None:
    if len(values) != len(set(values)):
        raise MetadataError("Duplicate IDs, references or values")


def _date(value: Any) -> str | None:
    if value is None:
        return None
    text = _text(value)
    try:
        if date.fromisoformat(text).isoformat() != text:
            raise ValueError()
    except ValueError as error:
        raise MetadataError("Expected ISO calendar date YYYY-MM-DD") from error
    return text


E = TypeVar("E", bound=StrEnum)


def _enum(enum: type[E], value: Any) -> E:
    try:
        return enum(_text(value))
    except ValueError as error:
        raise MetadataError(f"Invalid {enum.__name__}: {value!r}") from error


def _choice(value: Any, choices: str) -> str:
    text = _text(value)
    if text not in choices.split():
        raise MetadataError(f"Expected one of: {choices}")
    return text


def _fraction(value: Any) -> Fraction | None:
    if value is None:
        return None  # Represent incomplete evidence, never inferred zero.
    item = _object(value, "numerator denominator")
    if type(item["numerator"]) is not int:
        raise MetadataError("Rational numerator must be an integer")
    return Fraction(item["numerator"], _integer(item["denominator"]))


def _source(value: Any) -> SourceRecord:
    item = _object(value, "id kind publisher title location published_on retrieved_on lineage")
    return SourceRecord(
        _text(item["id"]),
        _choice(item["kind"], "regulation official_result decision archive secondary synthetic"),
        _text(item["publisher"]), _text(item["title"]), _text(item["location"]),
        _date(item["published_on"]), _date(item["retrieved_on"]), _text(item["lineage"]),
    )


def _claim(value: Any) -> EvidenceClaim:
    item = _object(value, "id references summary interpretation applicable_years review reviewed_by reviewed_on")
    references = []
    for value in _list(item["references"]):
        reference = _object(value, "source_id locator")
        references.append(SourceReference(_text(reference["source_id"]), _text(reference["locator"])))
    _unique(tuple(references))
    review = _enum(ReviewState, item["review"])
    reviewer = None if item["reviewed_by"] is None else _text(item["reviewed_by"])
    reviewed_on = _date(item["reviewed_on"])
    if review == ReviewState.ACCEPTED and (not reviewer or not reviewed_on or not references):
        raise MetadataError("Accepted claims require references, reviewer and review date")
    return EvidenceClaim(
        _text(item["id"]), tuple(references), _text(item["summary"]),
        _text(item["interpretation"]), _integers(item["applicable_years"]),
        review, reviewer, reviewed_on,
    )


def _rules(value: Any) -> RulePackageEvidence | None:
    if value is None:
        return None
    item = _object(value, "id source_year implementation_id applicability_evidence provisions")
    provisions = []
    for value in _list(item["provisions"]):
        provision = _object(value, "topic evidence_ids")
        provisions.append(RuleProvision(
            _enum(RuleTopic, provision["topic"]), _texts(provision["evidence_ids"]),
        ))
    _unique(tuple(provision.topic for provision in provisions))
    return RulePackageEvidence(
        _text(item["id"]), _integer(item["source_year"]), _text(item["implementation_id"]),
        _texts(item["applicability_evidence"]), tuple(provisions),
    )


def _season(value: Any) -> SeasonContext | None:
    if value is None:
        return None
    item = _object(value, "year completion event_ids completion_evidence event_scope_evidence amendment_evidence material_ambiguities")
    return SeasonContext(
        _integer(item["year"]), _choice(item["completion"], "complete incomplete unknown"),
        _integers(item["event_ids"]), _texts(item["completion_evidence"]),
        _texts(item["event_scope_evidence"]), _texts(item["amendment_evidence"]),
        _texts(item["material_ambiguities"]),
    )


def _expected(value: Any) -> ExpectedStandings | None:
    if value is None:
        return None
    item = _object(value, "year population independence result_basis evidence_ids rows")
    rows = []
    for value in _list(item["rows"]):
        row = _object(value, "driver_id source_label points position classification evidence_ids")
        standing = StandingValue(
            _text(row["driver_id"]), _fraction(row["points"]),
            None if row["position"] is None else _integer(row["position"]),
            _enum(ClassificationState, row["classification"]),
        )
        rows.append(ExpectedDriver(standing, _text(row["source_label"]), _texts(row["evidence_ids"])))
    _unique(tuple(row.standing.driver_id for row in rows))
    return ExpectedStandings(
        _integer(item["year"]), _enum(PopulationCoverage, item["population"]),
        _choice(item["independence"], "independent f1db reconstruction unknown"),
        _choice(item["result_basis"], "final_amended provisional unknown"),
        _texts(item["evidence_ids"]), tuple(rows),
    )


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise MetadataError(f"Duplicate JSON object key: {key}")
        result[key] = value
    return result


def _no_float(value: str) -> None:
    raise MetadataError(f"Floating-point/nonfinite JSON numbers are forbidden: {value}")


def parse_metadata(text: str) -> HistoricalMetadata:
    try:
        item = _object(json.loads(text, object_pairs_hook=_pairs, parse_float=_no_float,
                                  parse_constant=_no_float),
                       "schema_version scope category scoring sources claims rules season expected")
    except json.JSONDecodeError as error:
        raise MetadataError(str(error)) from error
    if type(item["schema_version"]) is not int or item["schema_version"] != SCHEMA_VERSION:
        raise MetadataError("Unsupported metadata schema version")
    if item["category"] != "drivers" or item["scoring"] != "original":
        raise MetadataError("Only Drivers / Original metadata is supported")
    scope = _enum(VerificationScope, item["scope"])
    sources = tuple(_source(value) for value in _list(item["sources"]))
    claims = tuple(_claim(value) for value in _list(item["claims"]))
    _unique(tuple(source.id for source in sources))
    _unique(tuple(claim.id for claim in claims))
    for source in sources:
        if (source.kind == "synthetic") != (scope == VerificationScope.SYNTHETIC):
            raise MetadataError("Synthetic sources and bundle scope must agree")
        if scope == VerificationScope.SYNTHETIC and "SYNTHETIC" not in source.title:
            raise MetadataError("Synthetic source titles must visibly say SYNTHETIC")
    rules, season, expected = _rules(item["rules"]), _season(item["season"]), _expected(item["expected"])
    source_ids = {source.id for source in sources}
    for claim in claims:
        if any(reference.source_id not in source_ids for reference in claim.references):
            raise MetadataError(f"Dangling source reference in {claim.id}")
    references: list[str] = []
    if rules:
        references.extend(rules.applicability_evidence)
        for provision in rules.provisions:
            references.extend(provision.evidence_ids)
    if season:
        references.extend(season.completion_evidence + season.event_scope_evidence + season.amendment_evidence)
    if expected:
        references.extend(expected.evidence_ids)
        for row in expected.rows:
            references.extend(row.evidence_ids)
    if set(references) - {claim.id for claim in claims}:
        raise MetadataError("Dangling evidence claim reference")
    return HistoricalMetadata(scope, sources, claims, rules, season, expected)


def _metadata_json(metadata: HistoricalMetadata) -> str:
    """Project typed records back to the existing wire schema, without hashes."""
    if type(metadata) is not HistoricalMetadata:
        raise MetadataError("Expected HistoricalMetadata")
    item = asdict(metadata)
    item.update(schema_version=SCHEMA_VERSION, category="drivers", scoring="original")
    if item["expected"] is not None:
        for row in item["expected"]["rows"]:
            row.update(row.pop("standing"))

    def rational(value: Any) -> dict[str, int]:
        if type(value) is not Fraction:
            raise MetadataError(f"Unsupported metadata value type: {type(value).__name__}")
        return {"numerator": value.numerator, "denominator": value.denominator}

    return json.dumps(item, default=rational, allow_nan=False)


def validate_metadata(metadata: HistoricalMetadata) -> HistoricalMetadata:
    """The evaluation boundary for JSON-loaded AND directly constructed records.

    Reuse the parser's complete structural/provenance checks; never trust a
    dataclass's annotations or its construction history. Return a validated,
    immutable copy so comparison and hashing use the same representation.
    """
    try:
        return parse_metadata(_metadata_json(metadata))
    except (TypeError, ValueError, AttributeError, KeyError) as error:
        raise MetadataError(f"Invalid metadata: {error}") from error


def _validated_document(metadata: HistoricalMetadata) -> dict[str, Any]:
    return json.loads(_metadata_json(validate_metadata(metadata)))


def load_metadata(path: str | Path) -> HistoricalMetadata:
    return parse_metadata(Path(path).read_text(encoding="utf-8"))
