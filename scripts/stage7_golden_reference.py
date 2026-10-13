from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Mapping

SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
MASTER_SEED = 20270101
EXPECTED_GLOBAL_SHA256 = "7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44"
MODEL_FILES = (
    "constants.py", "dateutils.py", "rng.py", "entities.py", "state_machine.py",
    "daily_engine.py", "accounting.py", "collection.py", "guarantee.py", "friday.py",
    "settlement.py", "closure.py", "partner_equity.py", "monte_carlo.py",
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class GoldenReferenceError(RuntimeError):
    """The historical golden reference or its source identity is not proved."""


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def ordered_trial_map_sha256(rows: list[tuple[str, int, str]]) -> str:
    payload = "".join(
        f"{scenario}|{trial_id}|{digest}\n"
        for scenario, trial_id, digest in sorted(rows, key=lambda x: (x[0], x[1], x[2]))
    )
    return sha256_bytes(payload.encode("utf-8"))


def load_golden_manifest(path: str | Path, *, source_sha: str, master_seed: int) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        raise GoldenReferenceError(f"GOLDEN_MANIFEST_MISSING path={p}")
    try:
        manifest = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GoldenReferenceError(f"GOLDEN_MANIFEST_INVALID path={p}: {exc}") from exc
    if manifest.get("manifest_version") != "stage12-golden-per-trial-v1":
        raise GoldenReferenceError("GOLDEN_MANIFEST_VERSION_MISMATCH")
    if manifest.get("source_sha") != source_sha or source_sha != SOURCE_SHA:
        raise GoldenReferenceError("GOLDEN_MANIFEST_SOURCE_SHA_MISMATCH")
    if int(manifest.get("master_seed", -1)) != master_seed or master_seed != MASTER_SEED:
        raise GoldenReferenceError("GOLDEN_MANIFEST_MASTER_SEED_MISMATCH")
    scenarios = manifest.get("scenarios")
    if not isinstance(scenarios, dict) or len(scenarios) != 25:
        raise GoldenReferenceError("GOLDEN_MANIFEST_SCENARIOS_INVALID")
    rows: list[tuple[str, int, str]] = []
    for scenario, item in sorted(scenarios.items()):
        hashes = item.get("trial_hashes")
        expected_count = 1 if scenario.startswith("C100_") else 550
        if not isinstance(hashes, dict) or len(hashes) != expected_count:
            raise GoldenReferenceError(f"GOLDEN_TRIAL_COVERAGE_INVALID scenario={scenario}")
        if sorted(int(k) for k in hashes) != list(range(1, expected_count + 1)):
            raise GoldenReferenceError(f"GOLDEN_TRIAL_SEQUENCE_INVALID scenario={scenario}")
        for raw_id, digest in hashes.items():
            if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
                raise GoldenReferenceError(f"GOLDEN_HASH_INVALID scenario={scenario} trial_id={raw_id}")
            rows.append((scenario, int(raw_id), digest))
        aggregate = item.get("historical_trial_result_fingerprint_sha256")
        if not isinstance(aggregate, str) or _SHA256_RE.fullmatch(aggregate) is None:
            raise GoldenReferenceError(f"HISTORICAL_AGGREGATE_FINGERPRINT_MISSING scenario={scenario}")
    calculated = ordered_trial_map_sha256(rows)
    if len(rows) != 11005:
        raise GoldenReferenceError(f"GOLDEN_TRIAL_COUNT_INVALID actual={len(rows)}")
    if calculated != EXPECTED_GLOBAL_SHA256:
        raise GoldenReferenceError(
            f"GOLDEN_GLOBAL_FINGERPRINT_MISMATCH expected={EXPECTED_GLOBAL_SHA256} actual={calculated}"
        )
    if manifest.get("global_ordered_trial_hash_map_sha256") != EXPECTED_GLOBAL_SHA256:
        raise GoldenReferenceError("GOLDEN_MANIFEST_GLOBAL_FINGERPRINT_FIELD_MISMATCH")
    if manifest.get("hash_map_sha256_recomputed") != calculated:
        raise GoldenReferenceError("GOLDEN_MANIFEST_RECOMPUTED_FINGERPRINT_FIELD_MISMATCH")
    return manifest


def validate_model_source(
    model_source_root: str | Path,
    *,
    expected_source_sha: str,
    loaded_modules: Mapping[str, Any] | None = None,
) -> str:
    root = Path(model_source_root).resolve()
    if not root.is_dir():
        raise GoldenReferenceError(f"PINNED_MODEL_SOURCE_ROOT_MISSING path={root}")
    if _COMMIT_SHA_RE.fullmatch(expected_source_sha or "") is None:
        raise GoldenReferenceError("EXPECTED_SOURCE_SHA_INVALID")
    head_proc = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=False,
    )
    if head_proc.returncode:
        raise GoldenReferenceError("PINNED_MODEL_SOURCE_GIT_IDENTITY_UNAVAILABLE")
    actual_head = head_proc.stdout.strip()
    if _COMMIT_SHA_RE.fullmatch(actual_head) is None:
        raise GoldenReferenceError("ACTUAL_MODEL_SOURCE_SHA_INVALID")
    if loaded_modules:
        for name in ("constants", "daily_engine", "rng", "monte_carlo"):
            module = loaded_modules.get(name)
            module_path = getattr(module, "__file__", None) if module is not None else None
            if not module_path:
                raise GoldenReferenceError(f"MODEL_MODULE_PATH_UNAVAILABLE module={name}")
            try:
                Path(module_path).resolve().relative_to(root)
            except ValueError as exc:
                raise GoldenReferenceError(
                    f"MODEL_MODULE_NOT_LOADED_FROM_PINNED_SOURCE module={name} path={module_path}"
                ) from exc
    if actual_head == expected_source_sha:
        for relpath in MODEL_FILES:
            path = root / relpath
            if not path.is_file():
                raise GoldenReferenceError(f"PINNED_MODEL_FILE_MISSING path={relpath}")
            expected = subprocess.run(
                ["git", "-C", str(root), "rev-parse", f"{expected_source_sha}:{relpath}"],
                capture_output=True, text=True, check=False,
            )
            actual = subprocess.run(
                ["git", "-C", str(root), "hash-object", str(path)],
                capture_output=True, text=True, check=False,
            )
            if expected.returncode or actual.returncode:
                raise GoldenReferenceError(f"MODEL_SOURCE_BLOB_IDENTITY_UNAVAILABLE path={relpath}")
            if expected.stdout.strip() != actual.stdout.strip():
                raise GoldenReferenceError(f"MODEL_SOURCE_WORKTREE_DRIFT path={relpath}")
    return actual_head


def _as_record(result: Any) -> dict[str, Any]:
    if is_dataclass(result):
        return asdict(result)
    if isinstance(result, Mapping):
        return dict(result)
    raise GoldenReferenceError(f"UNSUPPORTED_TRIAL_RESULT_TYPE type={type(result).__name__}")


def trial_result_sha256(result: Any) -> str:
    record = _as_record(result)
    raw = json.dumps(
        record, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return sha256_bytes(raw)


def compare_known_golden_trials(
    *, scenario: str, results: list[Any], current_n: int, manifest: Mapping[str, Any]
) -> dict[str, Any]:
    scenario_data = manifest.get("scenarios", {}).get(scenario)
    if not isinstance(scenario_data, dict):
        raise GoldenReferenceError(f"GOLDEN_SCENARIO_MISSING scenario={scenario}")
    golden = scenario_data.get("trial_hashes")
    if not isinstance(golden, dict):
        raise GoldenReferenceError(f"GOLDEN_SCENARIO_HASHES_MISSING scenario={scenario}")
    ordered = sorted((_as_record(x) for x in results), key=lambda row: int(row.get("trial_id", -1)))
    if current_n < 1 or len(ordered) < current_n:
        raise GoldenReferenceError(
            f"GATE_A_RESULT_COUNT_INSUFFICIENT scenario={scenario} current_n={current_n} rows={len(ordered)}"
        )
    ids = [int(row.get("trial_id", -1)) for row in ordered]
    if ids != list(range(1, len(ordered) + 1)):
        raise GoldenReferenceError(f"GATE_A_TRIAL_SEQUENCE_INVALID scenario={scenario}")
    if any(row.get("scenario_id") != scenario for row in ordered):
        raise GoldenReferenceError(f"GATE_A_ROW_SCENARIO_MISMATCH scenario={scenario}")
    coverage = min(current_n, len(golden))
    expected_ids = list(range(1, coverage + 1))
    by_id = {int(row["trial_id"]): row for row in ordered}
    expected_rows: list[tuple[str, int, str]] = []
    actual_rows: list[tuple[str, int, str]] = []
    mismatches = []
    for trial_id in expected_ids:
        expected_hash = golden.get(str(trial_id))
        actual_hash = trial_result_sha256(by_id[trial_id])
        if not isinstance(expected_hash, str) or _SHA256_RE.fullmatch(expected_hash) is None:
            raise GoldenReferenceError(f"GATE_A_GOLDEN_HASH_INVALID scenario={scenario} trial_id={trial_id}")
        expected_rows.append((scenario, trial_id, expected_hash))
        actual_rows.append((scenario, trial_id, actual_hash))
        if expected_hash != actual_hash:
            mismatches.append({
                "trial_id": trial_id,
                "expected_sha256": expected_hash,
                "actual_sha256": actual_hash,
            })
    return {
        "expected_golden_fingerprint_sha256": ordered_trial_map_sha256(expected_rows),
        "actual_fingerprint_sha256": ordered_trial_map_sha256(actual_rows),
        "golden_reference_id": f"{manifest['canonical_reference_id']}|{scenario}|known_trial_ids=1..{coverage}",
        "golden_coverage_count": coverage,
        "golden_coverage_current_n": current_n,
        "current_n_without_historical_goldens": max(0, current_n - coverage),
        "historical_mismatch_count": len(mismatches),
        "historical_mismatches": mismatches,
    }


def evaluate_gate_a_for_results(
    *,
    previous_n: int | None,
    previous_metrics: dict[str, dict[str, Any]] | None,
    current_n: int,
    current_metrics: dict[str, dict[str, Any]],
    escalation_multiplier: int,
    relative_epsilon: float,
    absolute_epsilon: float,
    results: list[Any],
    scenario: str,
    source_sha: str,
    master_seed: int = MASTER_SEED,
    model_source_root: str | Path | None,
    manifest_path: str | Path,
    loaded_modules: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    from scripts.stage7_stability import evaluate_gate_a as evaluate_stage7_gate_a

    if model_source_root is None:
        return {
            "previous_n": previous_n,
            "current_n": current_n,
            "expected_current_n": previous_n * escalation_multiplier if previous_n is not None else current_n,
            "metrics": {},
            "checked": False,
            "stable": False,
            "status": "BLOCKED",
            "reason": "pinned model source root is not supplied",
        }
    try:
        manifest = load_golden_manifest(manifest_path, source_sha=source_sha, master_seed=master_seed)
        actual_source_sha = validate_model_source(
            model_source_root, expected_source_sha=source_sha, loaded_modules=loaded_modules
        )
        evidence = compare_known_golden_trials(
            scenario=scenario, results=results, current_n=current_n, manifest=manifest
        )
    except GoldenReferenceError as exc:
        return {
            "previous_n": previous_n,
            "current_n": current_n,
            "expected_current_n": previous_n * escalation_multiplier if previous_n is not None else current_n,
            "metrics": {},
            "checked": False,
            "stable": False,
            "status": "BLOCKED",
            "reason": str(exc),
        }
    if evidence["current_n_without_historical_goldens"] > 0:
        return {
            "previous_n": previous_n,
            "current_n": current_n,
            "expected_current_n": previous_n * escalation_multiplier if previous_n is not None else current_n,
            "metrics": {},
            "checked": False,
            "stable": False,
            "status": "BLOCKED",
            "reason": (
                "approved exact-golden coverage is incomplete for the requested checkpoint: "
                f"N={current_n}, verified_golden_rows={evidence['golden_coverage_count']}, "
                f"rows_without_approved_golden={evidence['current_n_without_historical_goldens']}; "
                "no Gate A PASS is permitted until exact goldens cover the full checkpoint"
            ),
            "golden_coverage_count": evidence["golden_coverage_count"],
            "golden_coverage_current_n": evidence["golden_coverage_current_n"],
            "current_n_without_historical_goldens": evidence["current_n_without_historical_goldens"],
            "historical_mismatch_count": evidence["historical_mismatch_count"],
            "historical_mismatches": evidence["historical_mismatches"],
            "canonical_reference_id": manifest["canonical_reference_id"],
            "source_tree_head_verified": actual_source_sha == source_sha,
        }

    gate_a = evaluate_stage7_gate_a(
        previous_n=previous_n,
        previous_metrics=previous_metrics,
        current_n=current_n,
        current_metrics=current_metrics,
        escalation_multiplier=escalation_multiplier,
        relative_epsilon=relative_epsilon,
        absolute_epsilon=absolute_epsilon,
        expected_golden_fingerprint_sha256=evidence["expected_golden_fingerprint_sha256"],
        actual_fingerprint_sha256=evidence["actual_fingerprint_sha256"],
        golden_reference_id=evidence["golden_reference_id"],
        expected_source_sha=source_sha,
        actual_source_sha=actual_source_sha,
    )
    gate_a.update({
        "golden_coverage_count": evidence["golden_coverage_count"],
        "golden_coverage_current_n": evidence["golden_coverage_current_n"],
        "current_n_without_historical_goldens": evidence["current_n_without_historical_goldens"],
        "historical_mismatch_count": evidence["historical_mismatch_count"],
        "historical_mismatches": evidence["historical_mismatches"],
        "canonical_reference_id": manifest["canonical_reference_id"],
        "source_tree_head_verified": actual_source_sha == source_sha,
    })
    return gate_a


__all__ = [
    "GoldenReferenceError",
    "compare_known_golden_trials",
    "evaluate_gate_a_for_results",
    "load_golden_manifest",
    "ordered_trial_map_sha256",
    "sha256_bytes",
    "trial_result_sha256",
    "validate_model_source",
]
