"""Strict evidence loading; no historical claims in these tests."""

from fractions import Fraction
import json
from pathlib import Path

import pytest

from f1_eras.domain.verification import ClassificationState, StandingValue
from f1_eras.verification.metadata import MetadataError, load_metadata, parse_metadata


SYNTHETIC_PATH = Path(__file__).parent / "fixtures" / "synthetic" / "drivers_original.json"


@pytest.fixture
def document():
    return json.loads(SYNTHETIC_PATH.read_text(encoding="utf-8"))


def test_exact_rational_loading_and_validated_representation_hashes(document):
    loaded = load_metadata(SYNTHETIC_PATH)
    assert loaded.expected.rows[1].standing.points == Fraction(3, 2)
    assert parse_metadata(json.dumps(document, sort_keys=True)).content_sha256 == loaded.content_sha256
    document["expected"]["rows"][1]["points"] = {"numerator": 6, "denominator": 4}
    revised = parse_metadata(json.dumps(document))
    assert revised.expected.rows[1].standing.points == Fraction(3, 2)
    # Hashes now derive from typed, validated content, including reduced Fraction.
    assert revised.content_sha256 == loaded.content_sha256
    assert revised.rules_sha256 == loaded.rules_sha256


def test_array_reordering_intentionally_changes_representation_hash(document):
    loaded = parse_metadata(json.dumps(document))
    document["expected"]["rows"].reverse()
    reordered = parse_metadata(json.dumps(document))
    assert reordered.content_sha256 != loaded.content_sha256
    assert reordered.rules_sha256 == loaded.rules_sha256


@pytest.mark.parametrize("points", [
    1.5, {"numerator": 1.5, "denominator": 1},
    {"numerator": True, "denominator": 2}, {"numerator": 1, "denominator": False},
    {"numerator": 1, "denominator": 0}, {"numerator": 1, "denominator": -2},
    {"numerator": "1", "denominator": 2}, {"numerator": 1, "denominator": 2, "approx": "0.5"},
])
def test_invalid_or_lossy_rationals_rejected(document, points):
    document["expected"]["rows"][1]["points"] = points
    with pytest.raises(MetadataError):
        parse_metadata(json.dumps(document))


@pytest.mark.parametrize("text", ['{"schema_version":1,"schema_version":1}', 'NaN', 'Infinity', '1.0', '{'])
def test_duplicate_json_keys_nonfinite_floats_and_bad_json_rejected(text):
    with pytest.raises(MetadataError):
        parse_metadata(text)


@pytest.mark.parametrize("change", [
    lambda d: d.update(unknown_field=True),
    lambda d: d.update(schema_version=True),
    lambda d: d.update(schema_version=2),
    lambda d: d.update(category="constructors"),
    lambda d: d.update(scoring="counterfactual"),
    lambda d: d["expected"]["rows"].append(d["expected"]["rows"][0]),
    lambda d: d["sources"].append(d["sources"][0]),
    lambda d: d["claims"].append(d["claims"][0]),
    lambda d: d["rules"]["provisions"].append(d["rules"]["provisions"][0]),
    lambda d: d["season"].update(event_ids=[1, 1]),
    lambda d: d["claims"][0]["references"][0].update(source_id="absent"),
    lambda d: d["expected"].update(evidence_ids=["absent"]),
    lambda d: d["claims"][0].update(reviewed_by=None),
    lambda d: d["claims"][0].update(reviewed_on="2000-02-30"),
    lambda d: d["claims"][0].update(references=[]),
    lambda d: d["sources"][0].update(title="Unlabelled fiction"),
    lambda d: d.update(scope="historical"),
    lambda d: d["sources"][0].update(kind="official_result"),
])
def test_strict_schema_and_synthetic_labelling(document, change):
    change(document)
    with pytest.raises(MetadataError):
        parse_metadata(json.dumps(document))


def test_incomplete_bundle_is_representable_but_not_invented(document):
    document.update(sources=[], claims=[], rules=None, season=None, expected=None)
    loaded = parse_metadata(json.dumps(document))
    assert loaded.rules is loaded.season is loaded.expected is None


@pytest.mark.parametrize("points", [1.5, 1, "3/2"])
def test_comparator_domain_rejects_non_fraction_points(points):
    with pytest.raises(ValueError, match="Fraction"):
        StandingValue("synthetic-driver", points, 1, ClassificationState.RANKED)
