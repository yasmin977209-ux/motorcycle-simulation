"""Acceptance and evidence validators for the v2.3 candidate.

Functions operate on records supplied by callers; they never synthesize production
outputs, rewrite history, or promote a blocked statistical gate.
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import re
from typing import Any, Iterable, Mapping

import constants
import rng


# Canonical alias destinations from v2.3 §16.16; Test 158 is DOC/K_TEST.
ALIAS_TO_CANONICAL = {
    82: 17, 102: 6, 133: 39, 134: 9, 135: 33, 136: 27,
    139: 69, 140: 65, 145: 55, 147: 80, 151: 126, 153: 118,
    155: 115, 162: 88, 163: 95,
}
DOC_TEST_IDS = {158}
DEFERRED_PRODUCTION_TESTS = {
    127: ("S5", "production worker-equivalence manifest has not been generated"),
    159: ("S5", "production trials summary/Parquet has not been generated"),
    160: ("S5", "production selection and representative DAILY files have not been generated"),
    161: ("S5", "production DAILY_DISTRIBUTION Parquet has not been generated"),
    169: ("S4", "a reviewed C100 Golden for this new source/cohort is not yet approved"),
    170: ("S5", "production checksum uniqueness requires the authorized cohort"),
    172: ("S5", "production inference coverage is separate from the pure alpha-spending rule"),
    174: ("S5", "production complete-pass/sharding replay is not generated"),
    175: ("S7", "the two production 185-sheet workbooks have not been generated"),
    176: ("S8", "number_registry has not been reconciled to actual deliverables"),
    179: ("S6", "production run manifest has not been generated"),
    180: ("S7", "production DAILY workbook round-trip requires the generated workbook"),
    181: ("S7", "historical representative daily balances are absent; new-source output needs validation"),
    182: ("S8", "production Excel/report numbers have not been reconciled against number_registry"),
    183: ("S6", "production cohort identity manifest has not been generated"),
    184: ("S5", "production RNG audit records have not been generated for the new cohort"),
    186: ("S8", "the seven production deliverables and eight-member archive have not been generated"),
    191: ("S5", "representative roles must be reselected on the approved production cohort"),
    193: ("S6", "new source/cohort/Golden evidence requires separately approved production work"),
}


def validate_rng_audit_records(
    records: Iterable[Mapping[str, Any]],
    *,
    source_sha: str,
    master_seed: int,
    require_audit_fingerprint: bool = True,
) -> int:
    """Validate checksum/draw-count semantics and duplicate checksums per scenario.

    A checksum of zero is legal when draw_count > 0. Checksums from deterministic
    records with draw_count == 0 are not considered in the uniqueness check.
    """
    seen: dict[tuple[str, int], int] = {}
    count = 0
    for raw in records:
        row = dict(raw)
        required = {
            "scenario_id", "trial_id", "rng_checksum", "rng_draw_count",
        }
        if not required.issubset(row):
            raise RuntimeError("RNG_AUDIT_FIELDS_MISSING")
        checksum = row["rng_checksum"]
        draws = row["rng_draw_count"]
        trial_id = row["trial_id"]
        if isinstance(checksum, bool) or not isinstance(checksum, int):
            raise RuntimeError("RNG_CHECKSUM_MUST_BE_INT")
        if not 0 <= checksum < constants.RNG_CHECKSUM_MODULUS:
            raise RuntimeError("RNG_CHECKSUM_OUT_OF_RANGE")
        if isinstance(draws, bool) or not isinstance(draws, int) or draws < 0:
            raise RuntimeError("RNG_DRAW_COUNT_INVALID")
        if isinstance(trial_id, bool) or not isinstance(trial_id, int) or trial_id < 1:
            raise RuntimeError("RNG_AUDIT_TRIAL_ID_INVALID")
        if draws == 0 and checksum != 0:
            raise RuntimeError("RNG_CHECKSUM_NONZERO_WITHOUT_DRAWS")
        if draws > 0:
            key = (str(row["scenario_id"]), checksum)
            if key in seen:
                raise RuntimeError(
                    "DUPLICATE_RNG_CHECKSUM_DETECTED: "
                    f"scenario={key[0]} trial_ids={seen[key]},{trial_id} checksum={checksum}"
                )
            seen[key] = trial_id
        if require_audit_fingerprint:
            actual = row.get("rng_checksum_fingerprint_sha256")
            expected = rng.rng_audit_fingerprint(
                source_sha=source_sha,
                master_seed=master_seed,
                scenario_id=str(row["scenario_id"]),
                trial_id=trial_id,
                rng_checksum=checksum,
                rng_draw_count=draws,
            )
            if actual != expected:
                raise RuntimeError("RNG_AUDIT_FINGERPRINT_MISMATCH")
        count += 1
    return count


def validate_worker_equivalence_manifest(rows: Any) -> int:
    """Validate the pure logic contract for serial/parallel equality records."""
    if isinstance(rows, Mapping):
        rows = rows.get("trials", rows.get("records"))
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("WORKER_EQUIVALENCE_MANIFEST_INVALID")
    for row in rows:
        if not isinstance(row, Mapping):
            raise RuntimeError("WORKER_EQUIVALENCE_ROW_INVALID")
        if row.get("exact_1_eq_2") is not True or row.get("exact_1_eq_4") is not True:
            raise RuntimeError("WORKER_EQUIVALENCE_MISMATCH")
    return len(rows)


def validate_daily_distribution_dates(
    rows: Iterable[Mapping[str, Any]],
    *,
    expected_start: str | None = None,
    expected_end: str | None = None,
) -> int:
    """Ensure supplied daily rows contain contiguous dates without gaps."""
    items = list(rows)
    if not items:
        raise RuntimeError("DAILY_DISTRIBUTION_EMPTY")
    dates = sorted({date.fromisoformat(str(row["date"])) for row in items})
    if expected_start is not None and dates[0].isoformat() != expected_start:
        raise RuntimeError("DAILY_DISTRIBUTION_START_MISMATCH")
    if expected_end is not None and dates[-1].isoformat() != expected_end:
        raise RuntimeError("DAILY_DISTRIBUTION_END_MISMATCH")
    expected = dates[0]
    for actual in dates:
        if actual != expected:
            raise RuntimeError("DAILY_DISTRIBUTION_DATE_GAP")
        expected += timedelta(days=1)
    return len(dates)


def validate_partner_daily_balances(rows: Iterable[Mapping[str, Any]]) -> int:
    items = list(rows)
    if not items:
        raise RuntimeError("MISSING_EVIDENCE: no daily rows")
    required = {"Partner1_Reinvestment_Balance", "Partner2_Reinvestment_Balance"}
    for row in items:
        if not required.issubset(row):
            raise RuntimeError("MISSING_EVIDENCE: partner daily balances absent; do not derive them")
        for name in required:
            value = row[name]
            if isinstance(value, bool) or not isinstance(value, int):
                raise RuntimeError("PARTNER_DAILY_BALANCE_NOT_INTEGER")
    return len(items)


def validate_cohort_identity(rows: Iterable[Mapping[str, Any]]) -> tuple[str, str, str]:
    items = list(rows)
    if not items:
        raise RuntimeError("COHORT_IDENTITY_MISSING_EVIDENCE")
    keys = ("source_sha", "cohort_id", "schema_version")
    for row in items:
        if any(not row.get(key) for key in keys):
            raise RuntimeError("COHORT_IDENTITY_MISSING_EVIDENCE")
    identities = {tuple(str(row[key]) for key in keys) for row in items}
    if len(identities) != 1:
        raise RuntimeError("COHORT_IDENTITY_MISMATCH")
    return next(iter(identities))


def validate_c100_golden_identity(
    *,
    expected_source_sha: str,
    actual_source_sha: str,
    expected_cohort_id: str,
    actual_cohort_id: str,
    expected_schema_version: str,
    actual_schema_version: str,
    expected_fingerprint_sha256: str,
    actual_fingerprint_sha256: str,
) -> bool:
    if expected_source_sha != actual_source_sha:
        raise RuntimeError("C100_GOLDEN_SOURCE_SHA_MISMATCH")
    if expected_cohort_id != actual_cohort_id:
        raise RuntimeError("C100_GOLDEN_COHORT_ID_MISMATCH")
    if expected_schema_version != actual_schema_version:
        raise RuntimeError("C100_GOLDEN_SCHEMA_VERSION_MISMATCH")
    if expected_fingerprint_sha256 != actual_fingerprint_sha256:
        raise RuntimeError("C100_GOLDEN_FINGERPRINT_MISMATCH")
    return True


def validate_bilingual_numeric_values(
    arabic: Mapping[str, Any],
    english: Mapping[str, Any],
) -> int:
    if set(arabic) != set(english):
        raise RuntimeError("BILINGUAL_NUMBER_KEYS_MISMATCH")
    count = 0
    for key in arabic:
        left, right = arabic[key], english[key]
        if left != right or type(left) is not type(right):
            raise RuntimeError(f"BILINGUAL_NUMBER_MISMATCH: {key}")
        if isinstance(left, bool) or not isinstance(left, (int, Decimal)):
            raise RuntimeError(f"BILINGUAL_VALUE_NOT_EXACT_NUMERIC: {key}")
        count += 1
    return count


def validate_number_registry_coverage(
    used_names: Iterable[str],
    entries: Iterable[Mapping[str, Any]],
) -> int:
    names = set(used_names)
    item_list = list(entries)
    mapped = {str(item.get("name")) for item in item_list}
    missing = names - mapped
    if missing:
        raise RuntimeError(f"NUMBER_REGISTRY_MISSING: {','.join(sorted(missing))}")
    for item in item_list:
        for key in ("exact_numerator", "exact_denominator", "display_value", "source"):
            if key not in item:
                raise RuntimeError(f"NUMBER_REGISTRY_FIELD_MISSING: {key}")
        if not isinstance(item["exact_numerator"], int) or not isinstance(item["exact_denominator"], int):
            raise RuntimeError("NUMBER_REGISTRY_EXACT_VALUE_NOT_INT")
        if item["exact_denominator"] <= 0 or not item["source"]:
            raise RuntimeError("NUMBER_REGISTRY_EXACT_VALUE_INVALID")
    return len(names)


def validate_delivery_manifest(
    files: Mapping[str, bytes],
    manifest: Mapping[str, Any],
) -> int:
    entries = manifest.get("files")
    if not isinstance(entries, list):
        raise RuntimeError("MANIFEST_FILES_INVALID")
    if {entry.get("path") for entry in entries} != set(files):
        raise RuntimeError("MANIFEST_FILE_SET_MISMATCH")
    for entry in entries:
        path = entry["path"]
        payload = files[path]
        if entry.get("sha256") != sha256(payload).hexdigest():
            raise RuntimeError(f"MANIFEST_SHA256_MISMATCH: {path}")
        if entry.get("size_bytes") != len(payload):
            raise RuntimeError(f"MANIFEST_SIZE_MISMATCH: {path}")
        if not entry.get("tested_commit_sha") or not entry.get("command"):
            raise RuntimeError(f"MANIFEST_PROVENANCE_MISSING: {path}")
    return len(entries)


def c100_path_summary(results: Iterable[Any]) -> dict[str, Any]:
    import monte_carlo
    items = list(results)
    if not items:
        raise RuntimeError("C100_RESULTS_EMPTY")
    fingerprints = {monte_carlo.financial_path_fingerprint(item) for item in items}
    unique_paths = len(fingerprints)
    return {
        "N": len(items),
        "N_unique_paths": unique_paths,
        "status": "DEGENERATE_DETERMINISTIC" if unique_paths == 1 else "PATHS_DIFFER",
        "random_confidence_interval": False,
    }


def build_acceptance_registry(root: str | Path | None = None) -> list[dict[str, Any]]:
    """Build the normative 193-row registry from numbered pytest definitions."""
    root_path = Path(root) if root is not None else Path(__file__).resolve().parent
    test_root = root_path / "tests"
    functions: dict[int, tuple[str, str]] = {}
    for path in sorted(test_root.rglob("test_*.py")):
        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for match in re.finditer(r"^def test_(\d{3})_([^(:]+)\(", source, re.MULTILINE):
            test_id = int(match.group(1))
            functions.setdefault(
                test_id,
                (match.group(2), path.relative_to(root_path).as_posix()),
            )
    out: list[dict[str, Any]] = []
    for test_id in range(1, 194):
        function = functions.get(test_id)
        name = function[0] if function else f"DEFINITION_MISSING_{test_id:03d}"
        test_file = function[1] if function else None
        if test_id in DOC_TEST_IDS:
            kind, alias_of = "DOC", None
        elif test_id in ALIAS_TO_CANONICAL:
            kind, alias_of = "ALIAS", ALIAS_TO_CANONICAL[test_id]
        else:
            kind, alias_of = "UNIQUE", None
        deferred = DEFERRED_PRODUCTION_TESTS.get(test_id)
        out.append({
            "id": test_id,
            "name": name,
            "file": test_file,
            "type": kind,
            "alias_of": alias_of,
            "logic_status": "NOT_RUN",
            "production_status": "DEFERRED" if deferred else "NOT_REQUIRED",
            "deferred_stage": deferred[0] if deferred else None,
            "deferred_reason": deferred[1] if deferred else None,
            "source_basis": (
                "v2.3 §§16.16–16.18 and Appendix E; owner-approved checksum memo"
                if test_id >= 164 else "v2.3 §16.0/§16.1–§16.16"
            ),
        })
    return out
