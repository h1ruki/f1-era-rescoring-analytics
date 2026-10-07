"""The reviewed snapshot manifest is the only runtime approval authority."""

from dataclasses import dataclass
import json
from pathlib import Path
import re

from f1_eras.domain.models import F1DBSnapshot


MANIFEST_PATH = Path(__file__).resolve().parents[3] / "historical" / "canonical_snapshot.json"


class SnapshotApprovalError(ValueError):
    """Approval is missing, unreadable or invalid; it cannot confer trust."""


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate metadata key: {key}")
        result[key] = value
    return result


@dataclass(frozen=True, slots=True)
class SnapshotApproval:
    upstream_release: str
    upstream_release_commit: str
    sha256: str
    size_bytes: int

    def matches(self, snapshot: F1DBSnapshot) -> bool:
        return snapshot.sha256 == self.sha256 and snapshot.size_bytes == self.size_bytes


def load_snapshot_approval() -> SnapshotApproval:
    """Load afresh so invalid or removed approval never falls back to a cache."""
    try:
        value = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
        if type(value) is not dict or set(value) != {
            "upstream_release", "upstream_release_commit", "sha256", "size_bytes",
        }:
            raise ValueError("Unexpected approval record shape")
        for field, pattern in (("upstream_release", r"v\d+\.\d+\.\d+"),
                               ("upstream_release_commit", r"[0-9a-f]{40}"),
                               ("sha256", r"[0-9a-f]{64}")):
            if type(value[field]) is not str or re.fullmatch(pattern, value[field]) is None:
                raise ValueError(f"Invalid {field}")
        if type(value["size_bytes"]) is not int or value["size_bytes"] <= 0:
            raise ValueError("Invalid size_bytes")
        return SnapshotApproval(**value)
    except (OSError, UnicodeError, ValueError) as error:
        raise SnapshotApprovalError(str(error)) from error
