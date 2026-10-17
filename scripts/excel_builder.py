from __future__ import annotations

import argparse
import json
import tarfile
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from scripts.stage13_assemble import (
    EXPECTED_SCENARIOS,
    assemble_workbook,
    load_json,
    patch_xlsx_numeric_values,  # backward-compatible public export for Stage 9C rebuild path
    save_workbook_preserving_stats_precision,
    write_daily_sheet,
)


def load_rep_payload(dataset_root: Path, scenario: str, label: str) -> dict[str, Any]:
    direct = dataset_root / scenario / "representatives" / f"{label}.json"
    if direct.is_file():
        return load_json(direct)
    tar_path = dataset_root / scenario / f"{scenario}.tar.gz"
    if not tar_path.is_file():
        raise FileNotFoundError(f"MISSING_REPRESENTATIVE_PAYLOAD: {scenario}/{label}")
    target = f"representatives/{label}.json"
    with tarfile.open(tar_path, "r:gz") as archive:
        member = next((item for item in archive.getmembers() if item.name.lstrip("./") == target), None)
        if member is None:
            raise FileNotFoundError(f"MISSING_REPRESENTATIVE_PAYLOAD: {scenario}/{label}")
        stream = archive.extractfile(member)
        if stream is None:
            raise RuntimeError(f"UNREADABLE_REPRESENTATIVE_PAYLOAD: {scenario}/{label}")
        return json.load(stream)


def _root_layout(dataset_path: str | Path, manifest_path: str | Path | None = None):
    given = Path(dataset_path)
    if not given.exists() or not given.is_dir():
        raise FileNotFoundError(f"DATASET_PATH_NOT_FOUND: {given}")
    if manifest_path is not None:
        manifest_file = Path(manifest_path)
        artifact_root, dataset_root = manifest_file.parent, given
    elif (given / "dataset").is_dir() and (given / "manifest.json").is_file():
        artifact_root, dataset_root = given, given / "dataset"
        manifest_file = given / "manifest.json"
    else:
        artifact_root = dataset_root = given
        manifest_file = given / "manifest.json"
    if not manifest_file.is_file():
        raise FileNotFoundError(f"DATASET_MANIFEST_MISSING: {manifest_file}")
    return artifact_root, dataset_root, manifest_file


def load_dataset(
    dataset_path: str | Path,
    mode: str = "canonical",
    *,
    manifest_path: str | Path | None = None,
    representatives_path: str | Path | None = None,
) -> dict[str, Any]:
    """Load immutable Parquet and JSON values before calling the assembler."""
    artifact_root, dataset_root, manifest_file = _root_layout(dataset_path, manifest_path)
    manifest = load_json(manifest_file)
    if representatives_path is not None:
        reps_file = Path(representatives_path)
    else:
        reps_file = next((p for p in (
            artifact_root / "representative_trial_ids.json",
            dataset_root / "representative_trial_ids.json",
        ) if p.is_file()), None)
    assignments = load_json(reps_file).get("scenarios", {}) if reps_file else {}
    validation_file = next((p for p in (
        artifact_root / "validation_163.json", dataset_root / "validation_163.json"
    ) if p.is_file()), None)
    validation = load_json(validation_file) if validation_file else {"status": "not-provided", "tests": []}
    error_file = dataset_root / "error_log.json"
    errors = load_json(error_file) if error_file.is_file() else []
    trials, distributions, representatives = {}, {}, {}
    for scenario in EXPECTED_SCENARIOS:
        folder = dataset_root / scenario
        trial_file = folder / "trial_results.parquet"
        daily_file = folder / "daily_distribution.parquet"
        if trial_file.is_file():
            trials[scenario] = pq.read_table(trial_file).to_pylist()
        elif mode == "demo":
            trials[scenario] = []
        else:
            raise FileNotFoundError(f"SCENARIO_TRIAL_RESULTS_MISSING: {scenario}")
        if daily_file.is_file():
            distributions[scenario] = pq.read_table(daily_file).to_pylist()
        elif mode == "demo":
            distributions[scenario] = []
        else:
            raise FileNotFoundError(f"SCENARIO_DAILY_DISTRIBUTION_MISSING: {scenario}")
        reps = {}
        for filename, key in (("P10", "P10"), ("P50", "P50"), ("P90", "P90"),
                              ("Loss", "Loss"), ("Max Case", "Max Case")):
            try:
                reps[key] = load_rep_payload(dataset_root, scenario, filename)
            except FileNotFoundError:
                if mode != "demo" and trials[scenario]:
                    raise
        representatives[scenario] = reps
        if scenario not in assignments and reps:
            assignments[scenario] = {
                key: int(reps[key]["summary"]["trial_id"])
                for key in ("P10", "P50", "P90", "Loss", "Max Case") if key in reps
            }
    return {
        "manifest": manifest, "trials_by_scenario": trials,
        "daily_distributions_by_scenario": distributions,
        "representatives_by_scenario": representatives,
        "representative_trial_ids": assignments, "validation": validation,
        "errors": errors, "dataset_root": str(dataset_root),
    }


def build_excel(dataset_path, output_path, mode="canonical"):
    """Public API defined by the approved D-2026-10-10-04 architecture."""
    data = load_dataset(dataset_path, mode=mode)
    return assemble_workbook(data, output_path, mode=mode)


def resolve_build_mode(manifest, mode=None):
    """Resolve a declared cohort explicitly; never demote an unknown cohort to demo."""
    supported = {"canonical", "sample", "demo", "adaptive"}
    if mode is not None:
        if mode not in supported:
            raise ValueError(f"UNSUPPORTED_EXCEL_MODE: {mode}")
        return mode
    if manifest.get("cohort_id") == "STAGE13_ADAPTIVE_STABLE_PER_SCENARIO_V1":
        return "adaptive"
    count = manifest.get("total_trials")
    if count == 11005:
        return "canonical"
    if count == 625:
        return "sample"
    raise ValueError(
        "UNRECOGNIZED_COHORT_MODE: specify mode='demo' for fixtures or provide an approved cohort contract"
    )


def build_workbook(dataset_root, output_path, manifest_path, representatives_path, mode=None):
    """Compatibility adapter for old runners; creation of worksheets is delegated."""
    manifest = load_json(Path(manifest_path))
    mode = resolve_build_mode(manifest, mode)
    data = load_dataset(dataset_root, mode=mode, manifest_path=manifest_path,
                        representatives_path=representatives_path)
    return assemble_workbook(data, output_path, mode=mode)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-path")
    parser.add_argument("--dataset-root")
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--mode", choices=("canonical", "sample", "demo", "adaptive"), default=None)
    parser.add_argument("--manifest")
    parser.add_argument("--representatives")
    args = parser.parse_args()
    dataset = args.dataset_path or args.dataset_root
    if not dataset:
        parser.error("--dataset-path is required (or use legacy --dataset-root)")
    if args.manifest or args.representatives or args.dataset_root:
        result = build_workbook(
            dataset, args.output_path,
            args.manifest or str(Path(dataset) / "manifest.json"),
            args.representatives or str(Path(dataset) / "representative_trial_ids.json"),
            mode=args.mode,
        )
    else:
        result = build_excel(dataset, args.output_path, mode=args.mode or "canonical")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    raise SystemExit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
