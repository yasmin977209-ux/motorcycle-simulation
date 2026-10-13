from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only validation of immutable Stage 7/10 historical trial artifacts "
            "against the canonical Stage 12 per-trial golden map."
        )
    )
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--model-source-root", required=True)
    parser.add_argument("--source-sha", default=os.environ.get("SOURCE_SHA", ""))
    parser.add_argument("--master-seed", type=int, default=int(os.environ.get("MASTER_SEED", "20270101")))
    parser.add_argument("--manifest", default="scripts/data/stage12_golden_fingerprints_v1.json")
    parser.add_argument("--blocks-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    workspace_root = Path(__file__).resolve().parent.parent
    model_root = Path(args.model_source_root).resolve()
    sys.path.insert(0, str(workspace_root))
    sys.path.insert(0, str(model_root))

    # These model modules must resolve from the pinned SOURCE_SHA worktree, not main.
    import constants
    import daily_engine
    import monte_carlo
    import rng
    import pyarrow.parquet as pq
    from scripts.stage7_golden_reference import evaluate_gate_a_for_results
    from scripts.stage7_history_restore import restore_historical_results

    if not args.source_sha:
        raise RuntimeError("SOURCE_SHA_REQUIRED")
    token = os.environ.get("GH_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        raise RuntimeError("GITHUB_REPOSITORY_AND_GH_TOKEN_REQUIRED")

    loaded_modules = {
        "constants": constants,
        "daily_engine": daily_engine,
        "rng": rng,
        "monte_carlo": monte_carlo,
    }
    manifest_path = (workspace_root / args.manifest).resolve()
    blocks_dir = Path(args.blocks_dir).resolve()
    if blocks_dir.exists() and any(blocks_dir.iterdir()):
        raise RuntimeError(f"AUDIT_REFUSES_NONEMPTY_BLOCK_DIR path={blocks_dir}")
    restore = restore_historical_results(
        repo=repo,
        token=token,
        scenario=args.scenario,
        source_sha=args.source_sha,
        master_seed=args.master_seed,
        model_source_root=model_root,
        loaded_modules=loaded_modules,
        manifest_path=manifest_path,
        blocks_dir=blocks_dir,
    )
    rows = []
    for path in sorted(blocks_dir.glob("block_*.parquet")):
        rows.extend(pq.read_table(path).to_pylist())
    results = [
        monte_carlo.TrialResult(**row)
        for row in sorted(rows, key=lambda row: int(row["trial_id"]))
    ]
    if len(results) != restore["restored_trial_count"]:
        raise RuntimeError(
            f"AUDIT_RESTORED_ROW_COUNT_MISMATCH expected={restore['restored_trial_count']} actual={len(results)}"
        )

    if args.scenario.startswith("C100_"):
        gate_a = {
            "status": "NOT_APPLICABLE_C100",
            "checked": False,
            "reason": "C100 has a single canonical trial and is handled by its deterministic acceptance gate.",
        }
    else:
        gate_a = evaluate_gate_a_for_results(
            previous_n=None,
            previous_metrics=None,
            current_n=300,
            current_metrics={},
            escalation_multiplier=2,
            relative_epsilon=0.01,
            absolute_epsilon=1,
            results=results[:300],
            scenario=args.scenario,
            source_sha=args.source_sha,
            master_seed=args.master_seed,
            model_source_root=model_root,
            manifest_path=manifest_path,
            loaded_modules=loaded_modules,
        )
        if gate_a.get("status") != "PASS" or gate_a.get("checked") is not True:
            raise RuntimeError(
                f"HISTORICAL_N300_GATE_A_NOT_PASS scenario={args.scenario} "
                f"status={gate_a.get('status')} reason={gate_a.get('reason')}"
            )

    report = {
        **restore,
        "gate_a_n300": gate_a,
        "simulation_or_trial_executed": False,
        "historical_trials_rerun": False,
        "historical_dataset_modified": False,
        "historical_artifacts_modified": False,
        "loaded_model_module_paths": {
            name: str(Path(module.__file__).resolve())
            for name, module in loaded_modules.items()
        },
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "result": "PASS",
        "scenario": args.scenario,
        "restored_trial_count": restore["restored_trial_count"],
        "gate_a_n300": gate_a["status"],
        "historical_trials_rerun": False,
        "source_sha": args.source_sha,
        "global_golden_trial_map_sha256": restore["global_golden_trial_map_sha256"],
        "historical_trial_result_fingerprint_sha256": restore["historical_trial_result_fingerprint_sha256"],
        "report": str(output),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
