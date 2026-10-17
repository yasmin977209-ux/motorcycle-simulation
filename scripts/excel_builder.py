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
    build_scenario_summary,
    collect_excel_errors,
    ensure_date,
    load_json,
    metric_stats,
    numeric_metrics,
    patch_xlsx_numeric_values,
    py_value,
    save_workbook_preserving_stats_precision,
    sha256_file,
    style_sheet,
    write_acctg_sheet,
    write_assets_sheet,
    write_constants,
    write_daily_sheet,
    write_errors,
    write_final_closure,
    write_generic,
    write_heatmap,
    write_partner_sheet,
    write_readme,
    write_scenario_detail,
    write_scenario_matrix,
    write_stats_sheet,
    write_table,
    write_validation,
    write_sensitivity_sheet as write_sensitivity,
    write_daily_distribution as _write_daily_distribution,
    write_representatives as _write_representatives,
)


def load_rep_payload(dataset_root: Path, scenario: str, label: str) -> dict[str, Any]:
    """Read a named representative JSON, including from the scenario archive."""
    direct = dataset_root / scenario / "representatives" / f"{label}.json"
    if direct.is_file():
        return load_json(direct)
    tar_path = dataset_root / scenario / f"{scenario}.tar.gz"
    if not tar_path.is_file():
        raise FileNotFoundError(f"MISSING_REPRESENTATIVE_PAYLOAD: {scenario}/{label}")
    target = f"representatives/{label}.json"
    with tarfile.open(tar_path, "r:gz") as archive:
        member = next(
            (item for item in archive.getmembers() if item.name.lstrip("./") == target),
            None,
        )
        if member is None:
            raise FileNotFoundError(f"MISSING_REPRESENTATIVE_PAYLOAD: {scenario}/{label}")
        stream = archive.extractfile(member)
        if stream is None:
            raise RuntimeError(f"UNREADABLE_REPRESENTATIVE_PAYLOAD: {scenario}/{label}")
        return json.load(stream)


def load_scenario_trials(dataset_root: Path, scenario: str):
    """Legacy loader retained for callers that expect lists of Parquet rows."""
    path = Path(dataset_root) / scenario / "trial_results.parquet"
    if not path.is_file():
        raise FileNotFoundError(path)
    return pq.read_table(path).to_pylist()


def load_scenario_daily_distribution(dataset_root: Path, scenario: str):
    """Legacy daily-distribution loader retained for existing callers."""
    path = Path(dataset_root) / scenario / "daily_distribution.parquet"
    if not path.is_file():
        raise FileNotFoundError(path)
    return pq.read_table(path).to_pylist()


def representative_rows(rep_path: Path, scenario: str):
    """Legacy representative trial-id reader retained for external scripts."""
    rep = load_json(Path(rep_path))["scenarios"][scenario]
    return {
        label: int(trial_id)
        for label, trial_id in rep.items()
        if label in {"P10", "P50", "P90", "Loss"}
    }


def _root_layout(
    dataset_path: str | Path,
    manifest_path: str | Path | None = None,
):
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
    """Load immutable Parquet/JSON data; worksheet writing is delegated to Stage 13."""
    artifact_root, dataset_root, manifest_file = _root_layout(dataset_path, manifest_path)
    manifest = load_json(manifest_file)

    if representatives_path is not None:
        reps_file = Path(representatives_path)
    else:
        reps_file = next(
            (
                p for p in (
                    artifact_root / "representative_trial_ids.json",
                    dataset_root / "representative_trial_ids.json",
                )
                if p.is_file()
            ),
            None,
        )
    assignments = load_json(reps_file).get("scenarios", {}) if reps_file else {}
    validation_file = next(
        (
            p for p in (
                artifact_root / "validation_163.json",
                dataset_root / "validation_163.json",
            )
            if p.is_file()
        ),
        None,
    )
    validation = (
        load_json(validation_file)
        if validation_file
        else {"status": "not-provided", "tests": []}
    )
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
        for filename, key in (
            ("P10", "P10"),
            ("P50", "P50"),
            ("P90", "P90"),
            ("Loss", "Loss"),
            ("Max Case", "Max Case"),
        ):
            try:
                reps[key] = load_rep_payload(dataset_root, scenario, filename)
            except FileNotFoundError:
                if mode != "demo" and trials[scenario]:
                    raise
        representatives[scenario] = reps
        if scenario not in assignments and reps:
            assignments[scenario] = {
                key: int(reps[key]["summary"]["trial_id"])
                for key in ("P10", "P50", "P90", "Loss", "Max Case")
                if key in reps
            }

    return {
        "manifest": manifest,
        "trials_by_scenario": trials,
        "daily_distributions_by_scenario": distributions,
        "representatives_by_scenario": representatives,
        "representative_trial_ids": assignments,
        "validation": validation,
        "errors": errors,
        "dataset_root": str(dataset_root),
    }


def build_excel(dataset_path, output_path, mode="canonical"):
    """Public API for the approved orchestrator/assembler split."""
    data = load_dataset(dataset_path, mode=mode)
    return assemble_workbook(data, output_path, mode=mode)


def resolve_build_mode(manifest, mode=None):
    """Resolve a declared cohort explicitly; an unknown cohort never becomes demo."""
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


def build_workbook(
    dataset_root,
    output_path,
    manifest_path,
    representatives_path,
    mode=None,
):
    """Legacy orchestration signature retained; assembly is handled by Stage 13."""
    manifest = load_json(Path(manifest_path))
    resolved_mode = resolve_build_mode(manifest, mode)
    data = load_dataset(
        dataset_root,
        mode=resolved_mode,
        manifest_path=manifest_path,
        representatives_path=representatives_path,
    )
    return assemble_workbook(data, output_path, mode=resolved_mode)


def write_daily_distribution(wb, dataset_root):
    """Legacy worksheet helper signature; delegate its data to the Stage 13 writer."""
    daily_by_scenario = {}
    for scenario in EXPECTED_SCENARIOS:
        try:
            daily_by_scenario[scenario] = load_scenario_daily_distribution(
                Path(dataset_root), scenario
            )
        except FileNotFoundError:
            daily_by_scenario[scenario] = []
    return _write_daily_distribution(wb, daily_by_scenario)


def write_representatives(wb, manifest, rep_path):
    """Legacy worksheet helper signature; read named payloads then delegate assembly."""
    dataset_root = Path(manifest.get("_dataset_root", Path(rep_path).parent))
    representatives_by_scenario = {}
    role_files = (
        ("P10", "P10"),
        ("P50", "P50"),
        ("P90", "P90"),
        ("Loss", "Loss"),
        ("Max Case", "Max Case"),
    )
    for scenario in EXPECTED_SCENARIOS:
        reps = {}
        for role, filename in role_files:
            try:
                reps[role] = load_rep_payload(dataset_root, scenario, filename)
            except FileNotFoundError:
                continue
        representatives_by_scenario[scenario] = reps
    return _write_representatives(wb, representatives_by_scenario)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-path")
    parser.add_argument("--dataset-root")
    parser.add_argument("--output-path", required=True)
    parser.add_argument(
        "--mode",
        choices=("canonical", "sample", "demo", "adaptive"),
        default=None,
    )
    parser.add_argument("--manifest")
    parser.add_argument("--representatives")
    args = parser.parse_args()
    dataset = args.dataset_path or args.dataset_root
    if not dataset:
        parser.error("--dataset-path is required (or use legacy --dataset-root)")
    if args.manifest or args.representatives or args.dataset_root:
        result = build_workbook(
            dataset,
            args.output_path,
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
