import math
import re
from datetime import datetime
from urllib.parse import urlparse

REQUIRED_FINDING_FIELDS = [
    "finding_id", "project_id", "domain", "category", "requirement", "observation",
    "evidence_ids", "source_url", "source_document", "source_date", "observation_date",
    "verification_status", "severity", "confidence", "limitations", "reviewer_notes",
]
VALID_STATUSES = {"verified", "partially_verified", "unverified", "not_applicable", "conflicting_evidence"}
VALID_SEVERITIES = {"critical", "high", "medium", "low", "undetermined"}
VALID_DOMAINS = {"civil", "environmental", "electrical", "mechanical", "it", "regulatory"}
REQUIRED_EVIDENCE_FIELDS = ["evidence_id", "title", "issuing_org", "url", "access_date", "is_verifiable", "establishes", "unknowns"]


class ValidationError(ValueError):
    """Raised when audit input violates the documented data contract."""


def validate_iso_date(value, field_name, prefix):
    if not isinstance(value, str):
        raise ValidationError(f"{prefix}: '{field_name}' must be a string")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValidationError(f"{prefix}: Invalid ISO date format for '{field_name}': {value!r}")
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValidationError(f"{prefix}: Invalid calendar date for '{field_name}': {value!r}") from exc


def validate_url(value, field_name, prefix):
    if not isinstance(value, str):
        raise ValidationError(f"{prefix}: '{field_name}' must be a string")
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValidationError(f"{prefix}: Invalid URL structure or disallowed scheme for '{field_name}': {value!r}")
    try:
        _ = parsed.port
    except ValueError as exc:
        raise ValidationError(f"{prefix}: Invalid port in '{field_name}': {value!r}") from exc


def validate_confidence(value, prefix):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{prefix}: 'confidence' must be numeric and not boolean")
    if not math.isfinite(value):
        raise ValidationError(f"{prefix}: 'confidence' cannot be NaN or Infinity")
    if not 0.0 <= value <= 1.0:
        raise ValidationError(f"{prefix}: 'confidence' must be between 0.0 and 1.0")


def build_evidence_registry(evidence_data):
    if not isinstance(evidence_data, list):
        raise ValidationError("Evidence data must be a list")
    registry = {}
    for index, record in enumerate(evidence_data):
        prefix = f"Evidence index {index}"
        if not isinstance(record, dict):
            raise ValidationError(f"{prefix}: Record must be an object")
        for field in REQUIRED_EVIDENCE_FIELDS:
            if field not in record:
                raise ValidationError(f"{prefix}: Missing '{field}'")
        eid = record["evidence_id"]
        if not isinstance(eid, str) or not eid.strip():
            raise ValidationError(f"{prefix}: 'evidence_id' must be a non-empty string")
        if eid in registry:
            raise ValidationError(f"{prefix}: Duplicate evidence_id {eid!r}")
        for field in REQUIRED_EVIDENCE_FIELDS:
            if field == "is_verifiable":
                if not isinstance(record[field], bool):
                    raise ValidationError(f"{prefix}: 'is_verifiable' must be a boolean")
            elif not isinstance(record[field], str):
                raise ValidationError(f"{prefix}: '{field}' must be a string")
            elif field in {"title", "issuing_org", "establishes"} and not record[field].strip():
                raise ValidationError(f"{prefix}: '{field}' cannot be empty")
        validate_url(record["url"], "url", prefix)
        validate_iso_date(record["access_date"], "access_date", prefix)
        registry[eid] = record
    return registry


def validate_finding(record, index, evidence_registry):
    if not isinstance(record, dict):
        raise ValidationError(f"Finding index {index}: Record must be an object, got {type(record).__name__}")
    fid = record.get("finding_id", "N/A")
    prefix = f"Finding index {index} (ID: {fid})"
    for field in REQUIRED_FINDING_FIELDS:
        if field not in record:
            raise ValidationError(f"{prefix}: Missing required field '{field}'")
        value = record[field]
        if value is None and field != "source_date":
            raise ValidationError(f"{prefix}: Field '{field}' cannot be null")
        if isinstance(value, str) and not value.strip() and field not in {"limitations", "reviewer_notes"}:
            raise ValidationError(f"{prefix}: Field '{field}' cannot be empty")
    if not isinstance(record["finding_id"], str) or not record["finding_id"].strip():
        raise ValidationError(f"{prefix}: 'finding_id' must be a non-empty string")
    for field, allowed in (("domain", VALID_DOMAINS), ("verification_status", VALID_STATUSES), ("severity", VALID_SEVERITIES)):
        value = record[field]
        if not isinstance(value, str) or value not in allowed:
            raise ValidationError(f"{prefix}: Invalid {field} type or value {value!r}")
    if not isinstance(record["evidence_ids"], list):
        raise ValidationError(f"{prefix}: 'evidence_ids' must be a list")
    for eid in record["evidence_ids"]:
        if not isinstance(eid, str):
            raise ValidationError(f"{prefix}: 'evidence_ids' must contain only strings")
        if eid not in evidence_registry:
            raise ValidationError(f"{prefix}: Unknown evidence_id {eid!r}")
    validate_confidence(record["confidence"], prefix)
    if record["source_date"] is not None:
        validate_iso_date(record["source_date"], "source_date", prefix)
    validate_iso_date(record["observation_date"], "observation_date", prefix)
    validate_url(record["source_url"], "source_url", prefix)
