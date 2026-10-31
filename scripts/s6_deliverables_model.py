"""Typed, source-attributed shared model for the S6 T2 interim deliverables."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from decimal import Decimal
from fractions import Fraction
from typing import Any, Mapping


@dataclass(frozen=True)
class SourceRef:
    artifact_id: int | str
    run_id: int | str | None
    archive_sha256: str
    member_path: str
    member_sha256: str | None = None
    row_or_key: str | None = None
    evidence_status: str = "VERIFIED_LOCAL"


@dataclass(frozen=True)
class SourcedValue:
    value: Any
    source: SourceRef
    status: str = "VERIFIED_LOCAL"


@dataclass
class S6SharedModel:
    classification: str
    project_identity: dict[str, SourcedValue] = field(default_factory=dict)
    governing_reference: dict[str, SourcedValue] = field(default_factory=dict)
    historical_execution_identity: dict[str, SourcedValue] = field(default_factory=dict)
    artifact_provenance: dict[str, Any] = field(default_factory=dict)
    scenario_definitions: list[dict[str, SourcedValue]] = field(default_factory=list)
    representative_mapping: list[dict[str, SourcedValue]] = field(default_factory=list)
    unique_keys: list[dict[str, SourcedValue]] = field(default_factory=list)
    daily_data: list[dict[str, Any]] = field(default_factory=list)
    accounting_data: list[dict[str, Any]] = field(default_factory=list)
    partner_data: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    roll_forward_evidence: list[dict[str, Any]] = field(default_factory=list)
    statistical_results: dict[str, Any] = field(default_factory=dict)
    gate_statuses: dict[str, Any] = field(default_factory=dict)
    number_registry_references: list[dict[str, Any]] = field(default_factory=list)
    missing_evidence: list[dict[str, Any]] = field(default_factory=list)
    unresolved_conflicts: list[dict[str, Any]] = field(default_factory=list)
    manifest_reconciliation: list[dict[str, Any]] = field(default_factory=list)
    builder_status: str = "T2_INTERIM / NOT_FINAL_BLOCKED"

    def to_dict(self) -> dict[str, Any]:
        return to_jsonable(asdict(self))


def to_jsonable(value: Any) -> Any:
    """Serialize exact numeric types without converting them to binary float."""
    if isinstance(value, Decimal):
        return {"$decimal": format(value, "f")}
    if isinstance(value, Fraction):
        return {"$fraction": {"numerator": value.numerator, "denominator": value.denominator}}
    if is_dataclass(value):
        return to_jsonable(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, float):
        raise TypeError("FINANCIAL_OR_MODEL_FLOAT_FORBIDDEN")
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise TypeError(f"UNSUPPORTED_MODEL_VALUE:{type(value).__name__}")


def sourced(value: Any, source: SourceRef, status: str = "VERIFIED_LOCAL") -> SourcedValue:
    return SourcedValue(value=value, source=source, status=status)
