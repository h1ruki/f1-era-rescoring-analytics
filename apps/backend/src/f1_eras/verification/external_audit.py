"""Optional audit enrichment, isolated from canonical assessment failures."""

from dataclasses import fields, replace
import json
from pathlib import Path
import re

from f1_eras.domain.verification import CanonicalTrustAssessment, ExternalAuditSummary
from f1_eras.verification.approval import unique_object


AUDIT_PATH = Path(__file__).resolve().parents[3] / "historical" / "external_audit_summaries.json"


def enrich_external_audit(assessment: CanonicalTrustAssessment) -> CanonicalTrustAssessment:
    """Invalid/unavailable audit information never changes canonical trust."""
    try:
        items = json.loads(AUDIT_PATH.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
        if type(items) is not list:
            raise ValueError("Audit summaries must be an array")
        summaries = []
        contexts = set()
        for item in items:
            if type(item) is not dict or set(item) != {f.name for f in fields(ExternalAuditSummary)}:
                raise ValueError("Invalid audit summary shape")
            if type(item["year"]) is not int or item["year"] < 1:
                raise ValueError("Invalid audit year")
            if any(type(value) is not str or not value.strip()
                   for key, value in item.items() if key != "year"):
                raise ValueError("Invalid audit summary value")
            if re.fullmatch(r"[0-9a-f]{64}", item["f1db_sha256"]) is None:
                raise ValueError("Invalid audit snapshot hash")
            summary = ExternalAuditSummary(**item)
            context = (summary.year, summary.package_id, summary.f1db_sha256)
            if context in contexts:
                raise ValueError("Duplicate audit context")
            contexts.add(context)
            summaries.append(summary)
    except FileNotFoundError:
        return replace(assessment, external_audit=None, external_audit_status="unavailable")
    except (OSError, UnicodeError, ValueError):
        return replace(assessment, external_audit=None, external_audit_status="invalid")
    summary = next((item for item in summaries if (
        item.year, item.package_id, item.f1db_sha256
    ) == (assessment.year, assessment.package_id, assessment.f1db_sha256)), None)
    return replace(assessment, external_audit=summary,
                   external_audit_status="available" if summary else "unavailable")
