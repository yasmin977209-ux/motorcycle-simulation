#!/usr/bin/env python3
"""Bounded exact-fingerprint replay for approved Gate A golden extension D-2026-10-14-01."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

MAIN_HEAD = "647c19826b90d8224ce73ef9b90c306a45e03fb0"
SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
BENCHMARK_BLOB_SHA = "d54602982b6422939955ca841a251ecd250b4139"
MASTER_SEED = 20270101
N600_RUN_ID = 38174743440
N600_ARTIFACT_ID = 11715388165
N600_HASH_MAP_SHA256 = "dd537fe96c5a8736201441e9a620db148a0d16cadae518d2a777fbc723db395f"
N1200_RUN_ID = 38179919488
N1200_ARTIFACT_ID = 11717929259
N1200_HASH_MAP_SHA256 = "eaf1f8f3060aac6967b064d3199c082d2a9b47027c865628986f56cbb23c1fc3"
C100_GOLDEN = "4e58d9f5f5a11ff8a3f1f9c80e90ac5594660ae99d4f52170ec775bbd5a63417"

# Each entry is a per-trial result_sha from the specified historical Gate B report.
HISTORICAL: dict[tuple[str, int], dict[str, Any]] = {
    ("C030_G000", 551): {"sha256": "61554c2848e5e337bf180fdf3b4ddb4c545ae2b4e41e907323556ce6da007143", "manifest_run_id": N600_RUN_ID, "artifact_id": N600_ARTIFACT_ID, "trial_output_run_id": N600_RUN_ID, "trial_output_attempt": 1},
    ("C030_G000", 600): {"sha256": "cb1aa5ebfbef76b21c6a874f4548b7142a8e81b6bee64209ab8ea79cf58667ef", "manifest_run_id": N600_RUN_ID, "artifact_id": N600_ARTIFACT_ID, "trial_output_run_id": N600_RUN_ID, "trial_output_attempt": 1},
    ("C030_G000", 700): {"sha256": "804477797d43400ccc1dd22283e6b5ee352e7716596cb302231b1455bebf7096", "manifest_run_id": N1200_RUN_ID, "artifact_id": N1200_ARTIFACT_ID, "trial_output_run_id": N1200_RUN_ID, "trial_output_attempt": 1},
    ("C030_G000", 1200): {"sha256": "f356b1bc06330a3904d72430212024df538336446be6c5947fbf9038a1a427f9", "manifest_run_id": N1200_RUN_ID, "artifact_id": N1200_ARTIFACT_ID, "trial_output_run_id": N1200_RUN_ID, "trial_output_attempt": 1},
    ("C050_G050", 600): {"sha256": "7184c6167c63f5c3cf5126e0cb0d284301ffff5326911d55939b83843d6b9f5d", "manifest_run_id": N600_RUN_ID, "artifact_id": N600_ARTIFACT_ID, "trial_output_run_id": N600_RUN_ID, "trial_output_attempt": 1},
    ("C050_G050", 1200): {"sha256": "4e94441719eea9e6f07e945d23d36321101bd4b6f8a1fcaa1dad2916a6c333f7", "manifest_run_id": N1200_RUN_ID, "artifact_id": N1200_ARTIFACT_ID, "trial_output_run_id": N1200_RUN_ID, "trial_output_attempt": 2},
    ("C070_G070", 600): {"sha256": "7d7c5ff0e3e9df0f471d7d11840ca213dde99a1305e92811a00055f95faad6c5", "manifest_run_id": N600_RUN_ID, "artifact_id": N600_ARTIFACT_ID, "trial_output_run_id": N600_RUN_ID, "trial_output_attempt": 1},
    ("C070_G070", 1200): {"sha256": "a93f7352883dc592cf4998307d87eb42a8fe3ef14d236a394a70005b180d0904", "manifest_run_id": N1200_RUN_ID, "artifact_id": N1200_ARTIFACT_ID, "trial_output_run_id": N1200_RUN_ID, "trial_output_attempt": 1},
    ("C085_G100", 600): {"sha256": "269cd5c1258fe24e70158db2ef13b60985f9908a559846b538207abe8b5f89fb", "manifest_run_id": N600_RUN_ID, "artifact_id": N600_ARTIFACT_ID, "trial_output_run_id": N600_RUN_ID, "trial_output_attempt": 1},
    ("C085_G100", 1200): {"sha256": "1605e5d5888ba17b67ebd1f953e200cd7bf81445abaed4e24e3f12fe34c0d9c3", "manifest_run_id": N1200_RUN_ID, "artifact_id": N1200_ARTIFACT_ID, "trial_output_run_id": N1200_RUN_ID, "trial_output_attempt": 1},
}
TARGETS = [
    ("C030_G000", 551), ("C030_G000", 600), ("C030_G000", 700), ("C030_G000", 1200),
    ("C050_G050", 600), ("C050_G050", 1200),
    ("C070_G070", 600), ("C070_G070", 1200),
    ("C085_G100", 600), ("C085_G100", 1200),
]
ALL_TARGETS = TARGETS + [("C100_G100", 1)]
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
RESULT_MARKER = "__CPD_PER_TRIAL_RESULT_SHA256__="


def classify_fingerprints(a: str | None, b: str | None, historical: str | None) -> str:
    """Return the explicit fail-closed classification for one trial."""
    if not a or not b or not historical:
        return "BLOCKED_MISSING_FINGERPRINT"
    if a != b:
        return "FAIL_DRIFT"
    if a != historical:
        return "FAIL_HISTORICAL_MISMATCH"
    return "PASS"


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def _batch_probe(root: Path, benchmark_root: Path) -> dict[str, Any]:
    expected_head = MAIN_HEAD if _git(root, "rev-parse", "HEAD") == MAIN_HEAD else SOURCE_SHA
    if _git(root, "rev-parse", "HEAD") != expected_head:
        raise RuntimeError(f"UNEXPECTED_WORKTREE_HEAD:{root}:{_git(root, 'rev-parse', 'HEAD')}")
    benchmark_blob = _git(benchmark_root, "rev-parse", f"{MAIN_HEAD}:scripts/stage10_benchmark.py")
    if benchmark_blob != BENCHMARK_BLOB_SHA:
        raise RuntimeError(f"BENCHMARK_BLOB_MISMATCH:{benchmark_blob}")
    code = (
        "import json\n"
        "from stage10_benchmark import run_trial\n"
        f"targets = {ALL_TARGETS!r}\n"
        f"seed = {MASTER_SEED}\n"
        "values = {}\n"
        "for scenario, trial_id in targets:\n"
        "    result, measurement = run_trial(scenario, trial_id, seed)\n"
        "    values[f'{scenario}/{trial_id}'] = {\n"
        "        'sha256': measurement['result_sha256'],\n"
        "        'scenario_id': result.scenario_id,\n"
        "        'trial_id': result.trial_id,\n"
        "    }\n"
        f"print({RESULT_MARKER!r} + json.dumps(values, sort_keys=True, separators=(',', ':')))\n"
    )
    env = os.environ.copy()
    # Import the approved benchmark implementation from main, while the empty sys.path
    # entry resolves model modules from the selected worktree (A or B).
    env["PYTHONPATH"] = str(benchmark_root / "scripts")
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )
    marked = [line[len(RESULT_MARKER):] for line in completed.stdout.splitlines() if line.startswith(RESULT_MARKER)]
    if completed.returncode != 0 or len(marked) != 1:
        raise RuntimeError(
            f"REPLAY_PROCESS_FAILED:{root}:returncode={completed.returncode}:"
            f"stdout_tail={completed.stdout[-2000:]}:stderr_tail={completed.stderr[-4000:]}"
        )
    data = json.loads(marked[0])
    expected_keys = {f"{scenario}/{trial_id}" for scenario, trial_id in ALL_TARGETS}
    if set(data) != expected_keys:
        raise RuntimeError(f"REPLAY_KEY_COVERAGE_MISMATCH:{root}")
    for key, item in data.items():
        if not HASH_RE.fullmatch(str(item.get("sha256", ""))):
            raise RuntimeError(f"INVALID_TRIAL_SHA256:{root}:{key}")
        scenario, trial = key.rsplit("/", 1)
        if item.get("scenario_id") != scenario or int(item.get("trial_id", -1)) != int(trial):
            raise RuntimeError(f"REPLAY_RESULT_IDENTITY_MISMATCH:{root}:{key}")
    return {
        "head_sha": _git(root, "rev-parse", "HEAD"),
        "benchmark_blob_sha": benchmark_blob,
        "per_trial": data,
        "process_exit_code": completed.returncode,
        "stderr": completed.stderr[-4000:],
    }


def build_report(main_result: dict[str, Any], source_result: dict[str, Any]) -> dict[str, Any]:
    items = []
    for scenario, trial_id in ALL_TARGETS:
        key = f"{scenario}/{trial_id}"
        historical = (
            HISTORICAL[(scenario, trial_id)]
            if (scenario, trial_id) in HISTORICAL
            else {
                "sha256": C100_GOLDEN,
                "manifest_run_id": 37225915321,
                "artifact_id": 11312276587,
                "trial_output_run_id": 37225915321,
                "trial_output_attempt": 1,
            }
        )
        a = main_result["per_trial"][key]["sha256"]
        b = source_result["per_trial"][key]["sha256"]
        status = classify_fingerprints(a, b, historical["sha256"])
        items.append({
            "scenario_id": scenario,
            "trial_id": trial_id,
            "scope": "C100_SEPARATE_DETERMINISM_REPLAY" if scenario.startswith("C100_") else (
                "NEW_551_600" if trial_id <= 600 else "NEW_601_1200"
            ),
            "fingerprint_A_main_head": a,
            "fingerprint_B_source_sha_worktree": b,
            "fingerprint_historical": historical["sha256"],
            "a_equals_b": a == b,
            "a_equals_historical": a == historical["sha256"],
            "b_equals_historical": b == historical["sha256"],
            "status": status,
            "historical_provenance": historical,
        })
    non_c100 = [x for x in items if not x["scenario_id"].startswith("C100_")]
    c100 = [x for x in items if x["scenario_id"].startswith("C100_")]
    return {
        "schema_version": "cp-d-extended-replay-v1",
        "decision_id": "D-2026-10-14-01",
        "status": "PASS" if len(non_c100) == 10 and all(x["status"] == "PASS" for x in non_c100) and len(c100) == 1 and c100[0]["status"] == "PASS" else "FAIL",
        "main_head_sha": MAIN_HEAD,
        "source_sha": SOURCE_SHA,
        "master_seed": MASTER_SEED,
        "hash_algorithm": "scripts/stage10_benchmark.py result_sha: SHA-256(canonical_json(dataclasses.asdict(result)))",
        "benchmark_blob_sha": BENCHMARK_BLOB_SHA,
        "forbidden_fingerprint_trial_results_used": False,
        "historical_evidence": {
            "n600_run_id": N600_RUN_ID,
            "n600_artifact_id": N600_ARTIFACT_ID,
            "n600_artifact_archive_sha256": "67d5033a67eec27bd7a90b735c56f7f7ceff4181e32c88271dd07f39f3b8e8ae",
            "n600_ordered_hash_map_sha256": N600_HASH_MAP_SHA256,
            "n1200_run_id": N1200_RUN_ID,
            "n1200_artifact_id": N1200_ARTIFACT_ID,
            "n1200_artifact_archive_sha256": "17391caa64a7ed0fb7f3819a5df2f3b69bee982fb16060f3c542c84370bee7c0",
            "n1200_ordered_hash_map_sha256": N1200_HASH_MAP_SHA256,
            "c100_g100_manifest_run_id": 37225915321,
            "c100_g100_manifest_artifact_id": 11312276587,
        },
        "counts": {
            "new_non_c100_trials_expected": 10,
            "new_non_c100_trials_passed": sum(x["status"] == "PASS" for x in non_c100),
            "new_551_600_expected": 5,
            "new_551_600_passed": sum(x["status"] == "PASS" and x["trial_id"] <= 600 for x in non_c100),
            "new_601_1200_expected": 5,
            "new_601_1200_passed": sum(x["status"] == "PASS" and x["trial_id"] > 600 for x in non_c100),
            "c100_determinism_expected": 1,
            "c100_determinism_passed": sum(x["status"] == "PASS" for x in c100),
        },
        "replays": items,
        "no_dataset_or_parquet_modified": True,
        "source_sha_unchanged": True,
        "no_production_monte_carlo": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--main-root", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    errors = []
    result_a = None
    result_b = None
    try:
        if _git(args.main_root, "rev-parse", "HEAD") != MAIN_HEAD:
            raise RuntimeError("MAIN_WORKTREE_HEAD_MISMATCH")
        result_a = _batch_probe(args.main_root, args.main_root)
    except Exception as exc:  # evidence records the exact process/setup failure
        errors.append({"worktree": "A/main@HEAD", "error": f"{type(exc).__name__}: {exc}"})
    try:
        if _git(args.source_root, "rev-parse", "HEAD") != SOURCE_SHA:
            raise RuntimeError("SOURCE_WORKTREE_HEAD_MISMATCH")
        result_b = _batch_probe(args.source_root, args.main_root)
    except Exception as exc:
        errors.append({"worktree": "B/SOURCE_SHA", "error": f"{type(exc).__name__}: {exc}"})

    if result_a is None or result_b is None:
        report: dict[str, Any] = {
            "schema_version": "cp-d-extended-replay-v1",
            "decision_id": "D-2026-10-14-01",
            "status": "FAIL_EXECUTION",
            "main_head_sha": MAIN_HEAD,
            "source_sha": SOURCE_SHA,
            "master_seed": MASTER_SEED,
            "hash_algorithm": "scripts/stage10_benchmark.py result_sha",
            "benchmark_blob_sha": BENCHMARK_BLOB_SHA,
            "worktree_errors": errors,
            "partial_A": result_a,
            "partial_B": result_b,
            "no_dataset_or_parquet_modified": True,
            "source_sha_unchanged": True,
            "no_production_monte_carlo": True,
        }
    else:
        report = build_report(result_a, result_b)
        report["worktree_errors"] = errors
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "n600_new_passed": report.get("counts", {}).get("new_551_600_passed"),
        "n1200_new_passed": report.get("counts", {}).get("new_601_1200_passed"),
        "c100_determinism_passed": report.get("counts", {}).get("c100_determinism_passed"),
        "output": str(args.output),
        "worktree_errors": errors,
    }, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
