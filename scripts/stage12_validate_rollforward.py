from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

SOURCE_RUN_ID = 37964656154
SOURCE_RUN_SHA = "0156c5f4272eb0ca7e32442657d0df9eaf4973d3"
SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
MASTER_SEED = 20270101
EXPECTED_GLOBAL_SHA256 = "7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44"
EXPECTED_DAILY_ROWS = 22546465
SCHEMA_VERSION = "stage12-daily-accounting-v1"
IDENTITY_KEY = b"stage12.dataset_identity"
START_DATE = np.datetime64("2027-01-01", "D")
TRIAL_COUNTS = {
    f"C{c:03d}_G{g:03d}": (1 if c == 100 else 550)
    for c in (100, 85, 70, 50, 30)
    for g in (100, 70, 50, 30, 0)
}
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
EXPECTED_PARQUET_SHA256 = {
    "C030_G000": "b89d0fffcd98465aa9891e76c84559c466706643cbece02967b12bae2d96e85d",
    "C030_G030": "2b95f26624abb6c4f3a7145e457c3f2f8764a9d037e2de326a9dd768d42d40c9",
    "C030_G050": "aec638c6313f602148bf5fefaaa9885f5a9b9abd46ad0467f83292b6680d99c4",
    "C030_G070": "77be80edb5d5ab71dbe8faeab52b3ffb88098f25176aff6f4112f2f5d19f1a0c",
    "C030_G100": "a2e01d1db937216f2121e5dbf554c8371af23754cc60e22848b20c4ad700b702",
    "C050_G000": "6beecb837a3c6b71f34aedbeb958e8dd176cce3d60b2dfa1b95ee9bd57e6a380",
    "C050_G030": "defeb970853ee9ebcd7af349cc902404996ecff250a23bb5c7e1f3686849c983",
    "C050_G050": "f4531eebeb1f30e0160b47229d50d1177a9a2f72007f5b8cd3d0234a46e112c6",
    "C050_G070": "08659990ead7a7da5a275d4496479bfc81badad820652dc6ba0a0765b42a7c82",
    "C050_G100": "81b6e72e588964d54b33f9951f25c8a5c8ec9e458b1c7287c0f130efca7b460c",
    "C070_G000": "3f6543a6f4cc2ed97274ab41164c87077305f53060a53a99b3eb73654ead3644",
    "C070_G030": "3c499fbfbc1f6caa28e6617134d2b09e956813422f51ae7908e22c6aa8eed4a6",
    "C070_G050": "b4463fbf1885dd04b26453e0842a1c6ad433043c05f61c206561f9eb171a5213",
    "C070_G070": "51a39d399667b69691f574f6fe56ddebba9c86d556c2835c192873fe40be5cf5",
    "C070_G100": "90fd4f7102a7741d361f29726700ee87516cfa7e05543d5f3537d0cbfa41b238",
    "C085_G000": "f77beafdcfe43132faa00abab80141f8bf6153fbf35efacfe282d38f0c6ddf38",
    "C085_G030": "e5b8a3efe0cf78b8d98896507c4cd97db3f2910f332f73a97f16df4e996d7c54",
    "C085_G050": "104687ab9d841da2b4360477e390839a414733829f4513cbf98db69655674772",
    "C085_G070": "61d7a844865d47545d23f84fa71e51491c658e5293be490a5c97992374d3fc93",
    "C085_G100": "200645be63674cb2c65bff0bfb89ddc00bdfab9a3cda5e5e5b8d93ba7e23e43a",
    "C100_G000": "df1797e95324433c0db4d450056ca1e5f7e16f1acf6279b8fd83dae275669e52",
    "C100_G030": "51533c10feaddd6124796dee76280662f0c4e79a2bc3cbb7c14acf27436e1c96",
    "C100_G050": "848ea1bc628c286be4f57d6dc807e2c398ab5d45fada7e5cfdf86db9652d3db1",
    "C100_G070": "cfb67a65f99a548d0175f15290d0f446c79c07008ffaa6fd3ab931e63aa8cbaa",
    "C100_G100": "b2965dd4e2426631dcb503012817c63fe206c61e9f054d95c49716e1e3c448ae",
}

NUMERIC_FIELDS = [
    "trial_id", "master_seed",
    "Opening_Cash", "cash_inflows", "cash_outflows", "Closing_Cash",
    "Opening_AR", "ar_accruals", "ar_collections", "ar_transfers_to_guarantee",
    "Closing_AR", "Opening_Gross_Bike_Assets", "capitalized_purchases_and_customs",
    "gross_writeoffs_on_ownership", "Closing_Gross_Bike_Assets",
    "Opening_Accumulated_Depreciation", "depreciation_expense",
    "ad_removed_on_writeoff", "Closing_Accumulated_Depreciation", "Net_Bike_Assets",
    "Capital", "Retained_Earnings", "Opening_Equity", "Operating_Net_Profit",
    "Closing_Equity", "Guarantee_Claim_Receivable", "Total_Assets", "Liabilities",
    "Balance_Difference",
]
IDENTITY_FIELDS = ["scenario_id", "source_sha", "trial_id", "date", "result_sha256"]


def invariant_masks(c: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Return a boolean mask per authoritative daily accounting identity."""
    return {
        "cash_rollforward": (
            c["Opening_Cash"] + c["cash_inflows"] - c["cash_outflows"] == c["Closing_Cash"]
        ),
        "accounts_receivable_rollforward": (
            c["Opening_AR"] + c["ar_accruals"] - c["ar_collections"]
            - c["ar_transfers_to_guarantee"] == c["Closing_AR"]
        ),
        "gross_bike_assets_rollforward": (
            c["Opening_Gross_Bike_Assets"] + c["capitalized_purchases_and_customs"]
            - c["gross_writeoffs_on_ownership"] == c["Closing_Gross_Bike_Assets"]
        ),
        "accumulated_depreciation_rollforward": (
            c["Opening_Accumulated_Depreciation"] + c["depreciation_expense"]
            - c["ad_removed_on_writeoff"] == c["Closing_Accumulated_Depreciation"]
        ),
        "net_bike_assets_derived": (
            c["Net_Bike_Assets"]
            == c["Closing_Gross_Bike_Assets"] - c["Closing_Accumulated_Depreciation"]
        ),
        "equity_rollforward": (
            c["Opening_Equity"] + c["Operating_Net_Profit"] == c["Closing_Equity"]
        ),
        "equity_equals_capital_plus_retained_earnings": (
            c["Closing_Equity"] == c["Capital"] + c["Retained_Earnings"]
        ),
        "total_assets_components": (
            c["Total_Assets"] == c["Closing_Cash"] + c["Closing_AR"]
            + c["Guarantee_Claim_Receivable"] + c["Net_Bike_Assets"]
        ),
        "liabilities_zero": c["Liabilities"] == 0,
        "balance_difference_matches": (
            c["Balance_Difference"] == c["Total_Assets"] - c["Closing_Equity"]
        ),
        "balance_difference_zero": c["Balance_Difference"] == 0,
    }


def _expected_identity(scenario: str) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION, "scenario": scenario,
        "source_sha": SOURCE_SHA, "master_seed": MASTER_SEED,
        "rng_policy": RNG_POLICY, "sampling_policy": SAMPLING_POLICY,
        "stability_policy": STABILITY_POLICY, "trial_id_policy": TRIAL_ID_POLICY,
    }


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _check_entry():
    return {"rows_checked": 0, "violations": 0, "examples": []}


def _record(
    report: dict, name: str, mask: np.ndarray, scenario: str,
    trial_ids, dates, row_offset: int = 0,
):
    entry = report["checks"][name]
    mask = np.asarray(mask, dtype=bool)
    entry["rows_checked"] += int(mask.size)
    failed = np.flatnonzero(~mask)
    entry["violations"] += int(failed.size)
    for i in failed[: max(0, 5 - len(entry["examples"]))]:
        entry["examples"].append({
            "scenario": scenario,
            "trial_id": int(trial_ids[i]),
            "date": str(dates[i]),
            "batch_row": int(row_offset + i),
        })


def _validate_file(path: Path, report: dict) -> dict:
    scenario = path.stem
    target_trials = TRIAL_COUNTS[scenario]
    actual_sha = _file_sha256(path)
    expected_sha = EXPECTED_PARQUET_SHA256[scenario]
    if actual_sha != expected_sha:
        raise ValueError(f"content SHA mismatch for {path.name}: {actual_sha}")

    parquet = pq.ParquetFile(path)
    schema = parquet.schema_arrow
    if {field.name: str(field.type) for field in schema} != EXPECTED_COLUMN_TYPES:
        raise ValueError(f"schema/type mismatch: {path.name}")
    if any(field.nullable != (field.name == "Final_Close_Date") for field in schema):
        raise ValueError(f"schema nullability mismatch: {path.name}")
    metadata = schema.metadata or {}
    raw_identity = metadata.get(IDENTITY_KEY)
    if raw_identity is None or json.loads(raw_identity.decode("utf-8")) != _expected_identity(scenario):
        raise ValueError(f"dataset identity metadata mismatch: {path.name}")

    for name in invariant_masks({field: np.array([], dtype=np.int64) for field in NUMERIC_FIELDS}):
        report["checks"].setdefault(name, _check_entry())
    for name in (
        "row_source_identity", "row_scenario_identity", "row_seed_identity",
        "trial_id_sequence", "date_continuity", "daily_opening_continuity",
        "trial_result_fingerprint_constant",
    ):
        report["checks"].setdefault(name, _check_entry())

    needed = NUMERIC_FIELDS + ["scenario_id", "source_sha", "date", "result_sha256"]
    trial_ids_seen: set[int] = set()
    rows = 0
    first_trial = last_trial = None
    first_date = last_date = None
    previous_trial = None
    previous_date = None
    previous_closings = None
    previous_fingerprint = None
    row_offset = 0
    continuity_fields = [
        ("Opening_Cash", "Closing_Cash"),
        ("Opening_AR", "Closing_AR"),
        ("Opening_Gross_Bike_Assets", "Closing_Gross_Bike_Assets"),
        ("Opening_Accumulated_Depreciation", "Closing_Accumulated_Depreciation"),
        ("Opening_Equity", "Closing_Equity"),
    ]

    for batch in parquet.iter_batches(batch_size=100_000, columns=needed):
        if not batch.num_rows:
            continue
        arrays = {
            field: np.asarray(
                batch.column(batch.schema.get_field_index(field)).to_numpy(zero_copy_only=False)
            )
            for field in NUMERIC_FIELDS
        }
        raw_dates = batch.column(batch.schema.get_field_index("date")).to_pylist()
        dates = np.asarray(raw_dates, dtype="datetime64[D]")
        ids = arrays["trial_id"]
        scenario_values = batch.column(batch.schema.get_field_index("scenario_id")).to_pylist()
        source_values = batch.column(batch.schema.get_field_index("source_sha")).to_pylist()
        fingerprints = batch.column(batch.schema.get_field_index("result_sha256")).to_pylist()
        n = len(ids)

        for name, mask in invariant_masks(arrays).items():
            _record(report, name, mask, scenario, ids, raw_dates, row_offset)
        _record(
            report, "row_source_identity",
            np.asarray([v == SOURCE_SHA for v in source_values]),
            scenario, ids, raw_dates, row_offset,
        )
        _record(
            report, "row_scenario_identity",
            np.asarray([v == scenario for v in scenario_values]),
            scenario, ids, raw_dates, row_offset,
        )
        _record(
            report, "row_seed_identity",
            arrays["master_seed"] == MASTER_SEED,
            scenario, ids, raw_dates, row_offset,
        )

        trial_ids_seen.update(int(value) for value in np.unique(ids))
        if first_trial is None:
            first_trial, first_date = int(ids[0]), raw_dates[0]
        last_trial, last_date = int(ids[-1]), raw_dates[-1]

        if n > 1:
            same_trial = ids[1:] == ids[:-1]
            date_ok = (~same_trial) | (dates[1:] == dates[:-1] + np.timedelta64(1, "D"))
            _record(
                report, "date_continuity", date_ok, scenario, ids[1:],
                raw_dates[1:], row_offset + 1,
            )
            opening_ok = np.ones(n - 1, dtype=bool)
            for opening, closing in continuity_fields:
                opening_ok &= (~same_trial) | (arrays[opening][1:] == arrays[closing][:-1])
            _record(
                report, "daily_opening_continuity", opening_ok, scenario, ids[1:],
                raw_dates[1:], row_offset + 1,
            )
            changes = np.flatnonzero(~same_trial) + 1
            if len(changes):
                sequence_ok = (
                    (ids[changes] == ids[changes - 1] + 1)
                    & (dates[changes] == START_DATE)
                )
                _record(
                    report, "trial_id_sequence", sequence_ok, scenario,
                    ids[changes], [raw_dates[i] for i in changes], row_offset,
                )
            fingerprint_ok = (~same_trial) | (
                np.asarray(fingerprints[1:], dtype=object)
                == np.asarray(fingerprints[:-1], dtype=object)
            )
            _record(
                report, "trial_result_fingerprint_constant", fingerprint_ok,
                scenario, ids[1:], raw_dates[1:], row_offset + 1,
            )

        if previous_trial is not None:
            if int(ids[0]) == previous_trial:
                cross_checks = {
                    "date_continuity": bool(dates[0] == previous_date + np.timedelta64(1, "D")),
                    "daily_opening_continuity": all(
                        int(arrays[opening][0]) == previous_closings[closing]
                        for opening, closing in continuity_fields
                    ),
                    "trial_result_fingerprint_constant": fingerprints[0] == previous_fingerprint,
                }
                for name, passed in cross_checks.items():
                    _record(report, name, np.asarray([passed]), scenario, [int(ids[0])], [raw_dates[0]], row_offset)
            else:
                passed = int(ids[0]) == previous_trial + 1 and dates[0] == START_DATE
                _record(report, "trial_id_sequence", np.asarray([passed]), scenario, [int(ids[0])], [raw_dates[0]], row_offset)

        previous_trial = int(ids[-1])
        previous_date = dates[-1]
        previous_closings = {closing: int(arrays[closing][-1]) for _, closing in continuity_fields}
        previous_fingerprint = fingerprints[-1]
        rows += n
        row_offset += n

    expected_ids = set(range(1, target_trials + 1))
    if trial_ids_seen != expected_ids:
        raise ValueError(
            f"trial coverage mismatch in {path.name}: expected {target_trials} IDs from 1, "
            f"got {len(trial_ids_seen)}"
        )
    if rows == 0 or first_trial != 1 or last_trial != target_trials or first_date != "2027-01-01":
        raise ValueError(
            f"trial/date boundary mismatch in {path.name}: first={first_trial}/{first_date}, "
            f"last={last_trial}, rows={rows}"
        )
    return {
        "file": path.name, "content_sha256": actual_sha,
        "content_sha256_matches_cp12b_manifest": True,
        "trials": len(trial_ids_seen), "daily_rows": rows,
        "first_trial_id": first_trial, "last_trial_id": last_trial,
        "first_date": first_date, "last_date": last_date,
    }


def validate(root: Path) -> dict:
    report = {
        "created_by_cp": "CP-12-C", "source_cp": "CP-12-B",
        "source_run_id": str(SOURCE_RUN_ID), "source_run_head_sha": SOURCE_RUN_SHA,
        "source_sha": SOURCE_SHA, "master_seed": MASTER_SEED,
        "schema_version": SCHEMA_VERSION,
        "expected_global_sha256_from_cp12b": EXPECTED_GLOBAL_SHA256,
        "expected_daily_rows_from_cp12b": EXPECTED_DAILY_ROWS,
        "overall_result": "FAIL", "scenario_count": 0,
        "total_trials": 0, "total_daily_rows": 0, "checks": {}, "scenarios": {},
    }
    files = sorted(root.rglob("*.parquet"))
    if len(files) != 25 or {f.stem for f in files} != set(TRIAL_COUNTS):
        raise ValueError(f"expected the exact 25 CP-12-B Parquet scenario files, found {len(files)}")
    total_trials = total_rows = 0
    for path in files:
        result = _validate_file(path, report)
        report["scenarios"][path.stem] = result
        total_trials += result["trials"]
        total_rows += result["daily_rows"]
    report["scenario_count"] = len(files)
    report["total_trials"] = total_trials
    report["total_daily_rows"] = total_rows
    if total_trials != 11005:
        raise ValueError(f"expected 11005 trials, got {total_trials}")
    if total_rows != EXPECTED_DAILY_ROWS:
        raise ValueError(f"daily rows expected {EXPECTED_DAILY_ROWS}, got {total_rows}")
    violations = {key: entry["violations"] for key, entry in report["checks"].items() if entry["violations"]}
    if violations:
        report["failure"] = {"invariant_violations": violations}
        return report
    report["overall_result"] = "PASS"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit every CP-12-B daily row against the authoritative accounting identities.")
    parser.add_argument("--root", required=True, help="directory containing pinned CP-12-B Parquet artifacts")
    parser.add_argument("--output", required=True, help="JSON path for the audit result")
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        report = validate(Path(args.root))
    except Exception as exc:
        report = {
            "created_by_cp": "CP-12-C", "source_cp": "CP-12-B",
            "source_run_id": str(SOURCE_RUN_ID), "source_run_head_sha": SOURCE_RUN_SHA,
            "source_sha": SOURCE_SHA, "master_seed": MASTER_SEED,
            "overall_result": "FAIL",
            "failure": {"type": type(exc).__name__, "message": str(exc)},
        }
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report.get("overall_result") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
