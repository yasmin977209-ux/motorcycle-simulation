"""Typed, provenance-carrying data model for the read-only S6 delivery pipeline."""
from __future__ import annotations
from dataclasses import dataclass, asdict, is_dataclass
from fractions import Fraction
from decimal import Decimal
from typing import Any

class ModelValidationError(ValueError):
    pass

@dataclass(frozen=True)
class SourceRef:
    artifact_id: int
    run_id: int
    member: str
    sha256: str | None = None
    cohort_id: str | None = None
    source_sha: str | None = None
    trial_id: int | None = None

@dataclass(frozen=True)
class SourcedValue:
    value: Any
    source: SourceRef
    evidence_status: str = "VERIFIED_LOCAL"

@dataclass
class S6SharedModel:
    schema_version: str
    governing_decision_id: str
    governing_reference_sha256: str
    historical_execution_reference_sha256: str
    source_identities: dict[str, dict[str, Any]]
    representative_mapping: list[dict[str, Any]]
    unique_keys: list[dict[str, Any]]
    trial_records: list[dict[str, Any]]
    manifest_reconciliation: list[dict[str, Any]]
    limitations: list[str]
    classification: str = "T2_INTERIM / NOT_FINAL_BLOCKED"

def to_jsonable(value: Any) -> Any:
    if isinstance(value, float):
        raise ModelValidationError("FLOAT_NOT_ALLOWED")
    if isinstance(value, Fraction):
        return {"numerator": value.numerator, "denominator": value.denominator}
    if isinstance(value, Decimal):
        return format(value, "f")
    if is_dataclass(value):
        return to_jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise ModelValidationError(f"UNSUPPORTED_JSON_TYPE:{type(value).__name__}")

def sourced(value: Any, source: SourceRef, evidence_status: str = "VERIFIED_LOCAL") -> dict[str, Any]:
    return to_jsonable(SourcedValue(value, source, evidence_status))
