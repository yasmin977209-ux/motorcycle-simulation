from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re

EXPECTED_TEST192_SHA256 = "f6add77e9e7ff8256b36b661df337897de10cd96d7e00b0d9dfa660dea0e927b"
EXPECTED_C100_GOLDEN_SHA256 = "39950d91c3b40b11bea0997b8504ac932a57bcc0ef8e0c51e12d031342a53327"
EXPECTED_C100_MANIFEST_SHA256 = "2097284d77ead6b00492bf75830d09aeef8dbde4aaa1c15dae6a877dc7e9ff04"
EXPECTED_C100_RUN_ID = 40263424595
REQUIRED_FILES = (
    "results_stage5/worker_equivalence_manifest.json",
    "results_stage5/trials_summary.parquet",
    "results_stage5/selection.parquet",
    "results_stage5/daily_distribution.parquet",
    "results_stage5/opt1_sample_validation.json",
    "results_stage5/number_registry.json",
    "results_stage5/runtime_benchmark.json",
    "results_stage5/s5_acceptance.json",
    "results_stage5/s5_manifest.json",
)


def sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def replace_marked_section(content: str, begin: str, end: str, body: str) -> str:
    if content.count(begin) > 1 or content.count(end) > 1:
        raise RuntimeError(f"COMPUTE_PLAN_MARKERS_NOT_UNIQUE:{begin}")
    if begin in content and end in content:
        left = content.index(begin)
        right = content.index(end, left) + len(end)
        return content[:left] + begin + "\n" + body.rstrip() + "\n" + end + content[right:]
    if begin in content or end in content:
        raise RuntimeError(f"COMPUTE_PLAN_MARKER_PAIR_INCOMPLETE:{begin}")
    return content.rstrip() + "\n\n" + begin + "\n" + body.rstrip() + "\n" + end + "\n"


def parse_pytest_summary(log_text: str) -> dict[str, int | str]:
    lines = [
        line.strip()
        for line in log_text.splitlines()
        if " in " in line and re.search(r"\d+\s+(?:passed|failed|skipped|error)", line)
    ]
    if not lines:
        raise RuntimeError("PYTEST_SUMMARY_NOT_FOUND_IN_EXECUTION_LOG")
    line = lines[-1]
    def count(label: str) -> int:
        match = re.search(rf"(\d+)\s+{label}\b", line)
        return int(match.group(1)) if match else 0
    summary = {"summary_line": line, "passed": count("passed"), "failed": count("failed"), "skipped": count("skipped"), "errors": count("error")}
    if summary["passed"] <= 0 or summary["failed"] != 0 or summary["errors"] != 0:
        raise RuntimeError(f"PYTEST_FULL_SUITE_NOT_PASSING:{line}")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--tested-commit", required=True)
    parser.add_argument("--run-id", required=True, type=int)
    parser.add_argument("--run-attempt", required=True, type=int)
    args = parser.parse_args()
    if len(args.source_sha) != 40 or args.source_sha != args.tested_commit:
        raise RuntimeError("S5C_SOURCE_SHA_MISMATCH")

    pytest_log = Path("s5_evidence/pytest.log")
    if not pytest_log.is_file():
        raise RuntimeError("S5C_PYTEST_LOG_MISSING")
    pytest_summary = parse_pytest_summary(pytest_log.read_text(encoding="utf-8"))

    proof_path = Path("docs/stage7/test192_coverage_proof.json")
    if not proof_path.is_file():
        raise RuntimeError("S5A_REUSED_TEST192_PROOF_MISSING")
    proof_sha = sha256_file(proof_path)
    if proof_sha != EXPECTED_TEST192_SHA256:
        raise RuntimeError(f"S5A_REUSED_TEST192_PROOF_SHA256_MISMATCH:{proof_sha}")

    gate_path = Path("docs/stage7/statistical_execution_gate.json")
    compute_path = Path("docs/COMPUTE_PLAN.md")
    gate = json.loads(gate_path.read_text(encoding="utf-8"))

    golden_path = Path("docs/golden/v2.3/C100_GOLDEN_965281d52441cd0d4b744e211c9f68ee4cdc3753.json")
    c100_manifest_path = Path("docs/audits/S4_C100_GOLDEN_MANIFEST_965281d52441cd0d4b744e211c9f68ee4cdc3753.json")
    if not golden_path.is_file() or sha256_file(golden_path) != EXPECTED_C100_GOLDEN_SHA256:
        raise RuntimeError("S4_C100_GOLDEN_REUSE_SHA256_MISMATCH")
    if not c100_manifest_path.is_file() or sha256_file(c100_manifest_path) != EXPECTED_C100_MANIFEST_SHA256:
        raise RuntimeError("S4_C100_MANIFEST_REUSE_SHA256_MISMATCH")

    acceptance_path = Path("results_stage5/s5_acceptance.json")
    manifest_path = Path("results_stage5/s5_manifest.json")
    opt1_path = Path("results_stage5/opt1_sample_validation.json")
    benchmark_path = Path("results_stage5/runtime_benchmark.json")
    worker_path = Path("results_stage5/worker_equivalence_manifest.json")
    acceptance = json.loads(acceptance_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    opt1 = json.loads(opt1_path.read_text(encoding="utf-8"))
    benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))
    worker = json.loads(worker_path.read_text(encoding="utf-8"))

    if acceptance.get("status") != "PASS_S5_MINI_EVIDENCE":
        raise RuntimeError(f"S5C_ACCEPTANCE_STATUS_INVALID:{acceptance.get('status')}")
    if acceptance.get("tested_commit_sha") != args.tested_commit or manifest.get("tested_commit_sha") != args.tested_commit:
        raise RuntimeError("S5C_ARTIFACT_SOURCE_SHA_MISMATCH")
    if opt1.get("status") != "PASS" or opt1.get("sample_trials_per_stochastic_collection_level", 0) < 50:
        raise RuntimeError("S5C_OPT1_SAMPLE_EVIDENCE_INSUFFICIENT")
    if worker.get("exact_result_and_daily_equivalence") is not True:
        raise RuntimeError("S5C_WORKER_EQUIVALENCE_EVIDENCE_INVALID")
    if worker_path.stat().st_size <= 0:
        raise RuntimeError("S5C_WORKER_MANIFEST_EMPTY")

    file_hashes = {}
    manifest_entries = {entry["path"]: entry for entry in manifest.get("files", [])}
    for relative in REQUIRED_FILES:
        path = Path(relative)
        if not path.is_file() or path.stat().st_size <= 0:
            raise RuntimeError(f"S5C_REQUIRED_FILE_MISSING:{relative}")
        if relative != "results_stage5/s5_manifest.json":
            entry = manifest_entries.get(relative)
            if entry is None:
                raise RuntimeError(f"S5C_REQUIRED_FILE_MISSING_FROM_MANIFEST:{relative}")
            actual_hash = sha256_file(path)
            if actual_hash != entry["sha256"] or path.stat().st_size != entry["size_bytes"]:
                raise RuntimeError(f"S5C_MANIFEST_HASH_MISMATCH:{relative}")
            file_hashes[relative] = actual_hash
        else:
            file_hashes[relative] = sha256_file(path)
    for entry in manifest.get("files", []):
        path = Path(entry["path"])
        if not path.is_file() or sha256_file(path) != entry["sha256"] or path.stat().st_size != entry["size_bytes"]:
            raise RuntimeError(f"S5C_MANIFEST_FILE_VALIDATION_FAILED:{entry['path']}")

    c100_reuse = acceptance.get("c100_reuse", {})
    if c100_reuse.get("run_id") != EXPECTED_C100_RUN_ID or c100_reuse.get("rerun") is not False:
        raise RuntimeError("S5C_C100_RERUN_OR_IDENTITY_MISMATCH")

    level_statuses = opt1.get("level_statuses", [])
    opt1_by_level = {row["collection_scenario"]: row for row in level_statuses}
    required_levels = {"C100", "C085", "C070", "C050", "C030"}
    if not required_levels.issubset(opt1_by_level):
        raise RuntimeError("S5C_OPT1_LEVEL_STATUS_MISSING")
    if opt1_by_level["C100"].get("status") != "OPT1_REUSED_ACCEPTED_C100_S4_EVIDENCE":
        raise RuntimeError("S5C_C100_OPT1_REUSE_STATUS_INVALID")
    for collection in ("C085", "C070", "C050", "C030"):
        if not opt1_by_level[collection].get("full_run_scenarios_verified"):
            raise RuntimeError(f"S5C_FULL_G_RUNS_NOT_VERIFIED:{collection}")

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    s5_evidence = {
        "status": "EXECUTED",
        "overall_s5_b_s5_c": "PASS",
        "executed_at_utc": now,
        "workflow_run_id": args.run_id,
        "workflow_run_attempt": args.run_attempt,
        "tested_source_sha": args.tested_commit,
        "s5_b": {
            "status": "PASS_S5_MINI_EVIDENCE",
            "command": "python scripts/s5_mini_verification.py --source-sha <GITHUB_SHA> --tested-commit <GITHUB_SHA>",
            "exit_code": 0,
            "full_test_suite": {
                "command": "python -m pytest -q tests --junitxml=s5_evidence/junit.xml",
                "exit_code": 0,
                **pytest_summary,
            },
            "c100_reuse": {
                "run_id": EXPECTED_C100_RUN_ID,
                "rerun": False,
                "golden_sha256": EXPECTED_C100_GOLDEN_SHA256,
                "manifest_sha256": EXPECTED_C100_MANIFEST_SHA256,
            },
            "test192_reuse": {
                "run_id": 40397897155,
                "rerun": False,
                "proof_path": str(proof_path),
                "proof_sha256": proof_sha,
            },
            "opt1_status_by_collection_level": level_statuses,
            "results_stage5_manifest_sha256": sha256_file(manifest_path),
            "required_artifact_sha256": file_hashes,
        },
        "s5_c": {
            "status": "COMPLETED_AFTER_S5_B_SUCCESS",
            "gate_path": "docs/stage7/statistical_execution_gate.json",
            "compute_plan_path": "docs/COMPUTE_PLAN.md",
            "formal_gate_conclusion": "S5-B/S5-C execution evidence passed; this does not assert production Gate A/B acceptance or scenario convergence.",
        },
    }
    gate["s5_execution_evidence"] = s5_evidence
    gate["implementation_approval"]["validated_source_head_sha"] = args.tested_commit
    gate["implementation_approval"]["evidence_sha256"] = sha256_file(manifest_path)
    gate["implementation_approval"]["note"] = (
        "Exact source and S5-B/S5-C evidence verified from a completed GitHub Actions run. "
        "This records bounded execution/equivalence evidence only; production statistical acceptance remains separate."
    )
    gate["execution_authorization"]["permitted_next_work"] = (
        "S5-B and S5-C evidence recorded from completed execution. Proceed to the next authorized work-branch stage only with measured artifacts, "
        "preserve the historical failed transition, and reuse accepted C100 evidence read-only without rerunning it."
    )
    gate_path.write_text(json.dumps(gate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    content = compute_path.read_text(encoding="utf-8")
    content = content.replace("with trial IDs 1–5,", "with trial IDs 1–50,")
    content = content.replace("The sample has N=5", "The sample has N=50")
    content = content.replace("from this small N=5 cohort", "from this N=50 validation cohort")
    elapsed = benchmark["elapsed_seconds"]
    throughput = benchmark["throughput_trials_per_second"]
    speedups = benchmark["speedup_vs_sequential"]
    runtime_lines = [
        f"Actual workflow Run: {args.run_id} (attempt {args.run_attempt}); tested source SHA: {args.tested_commit}.",
        f"Measured S5-B workload: {benchmark['sample']['actual_trial_executions']} executions, {benchmark['sample']['unique_trial_paths']} unique stochastic scenario/trial paths, 20 non-C100 scenarios, N={len(benchmark['sample']['trial_ids_per_scenario'])} trials each.",
        f"- Sequential total: {elapsed['sequential_seconds']} s; throughput: {throughput['sequential_seconds']} unique scenario/trial paths/s.",
        f"- Parallel 2 workers total: {elapsed['parallel_2_workers_seconds']} s; throughput: {throughput['parallel_2_workers_seconds']} unique scenario/trial paths/s; speed-up: {speedups['parallel_2_workers']}x.",
        f"- Parallel 4 workers total: {elapsed['parallel_4_workers_seconds']} s; throughput: {throughput['parallel_4_workers_seconds']} unique scenario/trial paths/s; speed-up: {speedups['parallel_4_workers']}x.",
        f"- Total measured script elapsed: {benchmark['end_to_end_script_seconds']} s.",
        f"- Full repository tests: {pytest_summary['passed']} passed, {pytest_summary['skipped']} skipped, {pytest_summary['failed']} failed, {pytest_summary['errors']} errors (command exit code 0).",
        "S6 extrapolations remain unmeasured linear projections from this N=50 validation cohort; no production checkpoint or stability claim is inferred.",
        "C100 was hash-verified and reused read-only from S4 Run 40263424595; neither C100 nor Test 192's coverage simulation was rerun in S5-B.",
    ]
    content = replace_marked_section(content, "<!-- S5_RUNTIME_BEGIN -->", "<!-- S5_RUNTIME_END -->", "\n".join(runtime_lines))

    level_lines = [
        "## S5-C — Owner-approved OPT-1 evidence",
        "",
        f"- Evidence Run: {args.run_id}; tested source SHA: {args.tested_commit}. This section is recorded only after S5-B and the full test inventory passed.",
        f"- Accepted Test 192 proof reused without rerunning its simulation: SHA-256 {proof_sha}; S5-A Run 40397897155.",
        f"- C100: OPT1_REUSED_ACCEPTED_C100_S4_EVIDENCE, S4 Run {EXPECTED_C100_RUN_ID}, Golden SHA-256 {EXPECTED_C100_GOLDEN_SHA256}; no C100 rerun.",
        "",
        "| Collection level | OPT-1 status | Eligible zero-claim trials | Full independent G runs verified |",
        "|---|---|---:|---|",
    ]
    for c in ("C100", "C085", "C070", "C050", "C030"):
        item = opt1_by_level[c]
        eligible = item.get("eligible_zero_claim_trials")
        eligible_text = "reused S4 evidence" if eligible is None else str(eligible)
        full_modes = "No (reused S4)" if c == "C100" else ("Yes: G100/G070/G050/G030/G000" if item.get("full_run_scenarios_verified") else "No")
        level_lines.append(f"| {c} | {item['status']} | {eligible_text} | {full_modes} |")
    level_lines.extend([
        "",
        "For any level with claims_created == 0, the S5-B sample compared the financial trial_fingerprint and each daily row against all four lower-G candidates before marking the trial eligible for DERIVED_FROM=Cxxx_G100. Positive-claim trials remain full-run-only. If no sampled trial is claim-free, the level is recorded as OPT1_INELIGIBLE_FULL_RUN_REQUIRED and all five G scenarios must complete independently; the program does not raise an eligibility RuntimeError.",
        "",
        "### Required S5-B artifact SHA-256",
        "",
    ])
    for relative in (
        "results_stage5/worker_equivalence_manifest.json",
        "results_stage5/trials_summary.parquet",
        "results_stage5/daily_distribution.parquet",
        "results_stage5/opt1_sample_validation.json",
        "results_stage5/s5_manifest.json",
    ):
        level_lines.append(f"- {relative}: {file_hashes[relative]}")
    level_lines.extend([
        "",
        f"- Test inventory: {pytest_summary['summary_line']}",
        "- Scope limitation: this closes only S5-B/S5-C execution/equivalence evidence. It does not declare Gate A or Gate B production acceptance, convergence, or final delivery acceptance.",
    ])
    content = replace_marked_section(content, "<!-- S5_OPT1_BEGIN -->", "<!-- S5_OPT1_END -->", "\n".join(level_lines))
    compute_path.write_text(content.rstrip() + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "S5_C_FINALIZATION_READY_TO_COMMIT",
        "run_id": args.run_id,
        "tested_source_sha": args.tested_commit,
        "test192_reused_sha256": proof_sha,
        "s5_manifest_sha256": sha256_file(manifest_path),
        "required_artifact_sha256": file_hashes,
        "opt1_levels": {c: opt1_by_level[c]["status"] for c in ("C100", "C085", "C070", "C050", "C030")},
        "pytest": pytest_summary,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
