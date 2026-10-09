import argparse
import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

import pyarrow.parquet as pq

EXPECTED_GLOBAL = "7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44"
EXPECTED = {
    f"C{c:03}_G{g:03}": (1 if c == 100 else 550)
    for c in (100, 85, 70, 50, 30)
    for g in (100, 70, 50, 30, 0)
}
SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
MASTER_SEED = 20270101
SCHEMA_VERSION = "stage12-daily-accounting-v1"
RNG_POLICY = (
    "rng.py:SHA-256(seed key master_seed|scenario_id|trial_id|bike_id|date|event_type); "
    "draw=first_8_digest_bytes_big_endian/2^64; probability boundaries are deterministic"
)
SAMPLING_POLICY = (
    "one-based contiguous trial IDs; C100 scenarios use 1..1; non-C100 scenarios use 1..550; "
    "one materialization per scenario/trial; no cross-run inputs or resume"
)
STABILITY_POLICY = (
    "C100 uses one deterministic trial and no CI gate; non-C100 checkpoint N=300 then +50; "
    "95% Student-t CI half-width <1% of absolute mean for Final_Net_Project_Equity, "
    "Partner1_Final_Entitlement, Partner2_Final_Entitlement; CI_ABSOLUTE_EPSILON=1; "
    "three consecutive successful checkpoints; accepted N=550 (checkpoints 450, 500, 550)"
)
TRIAL_ID_POLICY = "one-based contiguous trial IDs from 1 to scenario target; no duplicate IDs"
IDENTITY_KEY = b"stage12.dataset_identity"
EXPECTED_COLUMN_TYPES = {
    "scenario_id": "string", "trial_id": "int64", "date": "string",
    "source_sha": "string", "master_seed": "int64",
    "Opening_Cash": "int64", "cash_inflows": "int64", "cash_outflows": "int64",
    "Closing_Cash": "int64", "Opening_AR": "int64", "ar_accruals": "int64",
    "ar_collections": "int64", "ar_transfers_to_guarantee": "int64",
    "Closing_AR": "int64", "Opening_Gross_Bike_Assets": "int64",
    "capitalized_purchases_and_customs": "int64", "gross_writeoffs_on_ownership": "int64",
    "Closing_Gross_Bike_Assets": "int64", "Opening_Accumulated_Depreciation": "int64",
    "depreciation_expense": "int64", "ad_removed_on_writeoff": "int64",
    "Closing_Accumulated_Depreciation": "int64", "Net_Bike_Assets": "int64",
    "Capital": "int64", "Retained_Earnings": "int64", "Opening_Equity": "int64",
    "Operating_Net_Profit": "int64", "Closing_Equity": "int64",
    "Guarantee_Claim_Receivable": "int64", "Total_Assets": "int64",
    "Liabilities": "int64", "Balance_Difference": "int64",
    "Final_Close_Date": "string", "Simulation_Stopped": "bool",
    "Active_Bikes": "int64", "Owned_Transferred_Bikes": "int64",
    "Pending_Claims": "int64", "result_sha256": "string",
}


def _expected_identity(scenario: str) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION, "scenario": scenario,
        "source_sha": SOURCE_SHA, "master_seed": MASTER_SEED,
        "rng_policy": RNG_POLICY, "sampling_policy": SAMPLING_POLICY,
        "stability_policy": STABILITY_POLICY, "trial_id_policy": TRIAL_ID_POLICY,
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    root = Path(parser.parse_args().root)
    files = sorted(root.rglob("*.parquet"))
    if len(files) != 25:
        raise SystemExit(f"expected 25 parquet files, got {len(files)}")
    if {path.stem for path in files} != set(EXPECTED):
        raise SystemExit("scenario artifact filename coverage mismatch")

    keys, trials, total_rows, sources, seeds = set(), [], 0, set(), set()
    scenario_artifacts = {}
    for path in files:
        scenario = path.stem
        schema = pq.read_schema(path)
        actual_types = {field.name: str(field.type) for field in schema}
        if actual_types != EXPECTED_COLUMN_TYPES:
            raise SystemExit(f"daily schema mismatch: {path.name}")
        if any(field.nullable != (field.name == "Final_Close_Date") for field in schema):
            raise SystemExit(f"daily schema nullability mismatch: {path.name}")

        metadata = schema.metadata or {}
        identity_raw = metadata.get(IDENTITY_KEY)
        if identity_raw is None:
            raise SystemExit(f"dataset identity metadata missing: {path.name}")
        try:
            identity = json.loads(identity_raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SystemExit(f"invalid dataset identity metadata: {path.name}: {exc}")
        if identity != _expected_identity(scenario):
            raise SystemExit(f"dataset identity mismatch: {path.name}")
        scenario_artifacts[scenario] = {"file": path.name, "sha256": _sha256_file(path)}

        rows = pq.read_table(
            path,
            columns=["scenario_id", "trial_id", "date", "source_sha", "master_seed", "result_sha256"],
        ).to_pylist()
        if not rows:
            raise SystemExit(f"empty scenario artifact: {path.name}")
        state = None
        for row in rows:
            total_rows += 1
            sources.add(row["source_sha"])
            seeds.add(int(row["master_seed"]))
            key = (row["scenario_id"], int(row["trial_id"]))
            if row["scenario_id"] != scenario:
                raise SystemExit(f"scenario column/file mismatch: {path.name}")
            if row["source_sha"] != SOURCE_SHA:
                raise SystemExit(f"source SHA row mismatch: {key}")
            if int(row["master_seed"]) != MASTER_SEED:
                raise SystemExit(f"master seed row mismatch: {key}")
            day = date.fromisoformat(row["date"])
            if state is None or key != state[0]:
                if state is not None:
                    if state[3] != (state[2] - state[1]).days + 1:
                        raise SystemExit(f"daily gap/duplicate: {state[0]}")
                    trials.append((state[0][0], state[0][1], state[4]))
                if key in keys:
                    raise SystemExit(f"duplicate trial: {key}")
                keys.add(key)
                state = [key, day, day, 1, row["result_sha256"]]
            else:
                if day != state[2] + timedelta(days=1):
                    raise SystemExit(f"daily gap/duplicate: {key} {day}")
                if row["result_sha256"] != state[4]:
                    raise SystemExit(f"trial fingerprint drift: {key}")
                state[2], state[3] = day, state[3] + 1
        if state is not None:
            if state[3] != (state[2] - state[1]).days + 1:
                raise SystemExit(f"daily gap/duplicate: {state[0]}")
            trials.append((state[0][0], state[0][1], state[4]))

    if sources != {SOURCE_SHA} or seeds != {MASTER_SEED} or len(trials) != 11005:
        raise SystemExit("source, master-seed, or trial-count mismatch")

    counts = {scenario: 0 for scenario in EXPECTED}
    for scenario, trial_id, _ in trials:
        if scenario not in EXPECTED or not 1 <= trial_id <= EXPECTED[scenario]:
            raise SystemExit(f"trial coverage failure: {scenario} {trial_id}")
        counts[scenario] += 1
    if counts != EXPECTED or len(keys) != 11005:
        raise SystemExit("trial coverage failure")

    # Keep the documented canonical bytes unchanged:
    # scenario_id|trial_id|trial_hash + LF, sorted by scenario_id then trial_id.
    payload = "".join(
        f"{scenario}|{trial_id}|{trial_sha}\n"
        for scenario, trial_id, trial_sha in sorted(trials)
    )
    reproduced = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    if reproduced != EXPECTED_GLOBAL:
        raise SystemExit(f"global fingerprint mismatch: {reproduced}")

    output_path = Path("docs/stage12/reproduction_result.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps({
        "created_by_cp": "CP-12-B2", "overall_result": "PASS",
        "original_global_sha256": EXPECTED_GLOBAL,
        "reproduced_global_sha256": reproduced, "match": "YES",
        "source_sha": SOURCE_SHA, "master_seed": MASTER_SEED,
        "rng_policy": RNG_POLICY, "sampling_policy": SAMPLING_POLICY,
        "stability_policy": STABILITY_POLICY, "trial_id_policy": TRIAL_ID_POLICY,
        "schema_version": SCHEMA_VERSION, "total_trials": len(trials),
        "total_daily_rows": total_rows, "parquet_files": len(files),
        "scenarios": 25, "retries": 0,
        "scenario_artifacts": scenario_artifacts,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
