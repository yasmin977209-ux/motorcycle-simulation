from __future__ import annotations

import hashlib
import io
import json
import os
import tarfile
import urllib.request
import zipfile
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq

REPOSITORY = "yasmin977209-ux/motorcycle-simulation"
ARTIFACT_ID = 11497409735
SOURCE_RUN_ID = 37655041728
EXPECTED_ZIP_SHA256 = "9331c726560471f3092b2c61893a7ad87f3bafed363217249b6f4a992c029c07"
EXPECTED_PARQUET_SHA256 = "deaaf22000a56eb674ea4d349235f1e6d9410b838979ae043f41712983924b54"
EXPECTED_SCENARIO = "C030_G030"
EXPECTED_SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
OBSERVED_P16_CELL_VALUE = 13185720.000000002
EXPECTED_TRIAL_COUNT = 450


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fail(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def download_artifact_zip() -> bytes:
    token = os.environ.get("GH_TOKEN")
    fail(bool(token), "GH_TOKEN is required for read-only artifact download")
    url = (
        f"https://api.github.com/repos/{REPOSITORY}/actions/artifacts/"
        f"{ARTIFACT_ID}/zip"
    )
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "motorcycle-simulation-p16-quantile-audit",
        },
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        fail(response.status == 200, f"artifact download status={response.status}")
        return response.read()


def extract_verified_trial_results(artifact_zip: bytes) -> bytes:
    fail(
        sha256(artifact_zip) == EXPECTED_ZIP_SHA256,
        "ARTIFACT_ZIP_SHA256_MISMATCH",
    )
    with zipfile.ZipFile(io.BytesIO(artifact_zip)) as outer:
        archives = [name for name in outer.namelist() if name.endswith(".tar.gz")]
        fail(archives == [f"{EXPECTED_SCENARIO}.tar.gz"], f"unexpected outer members: {archives}")
        tar_bytes = outer.read(archives[0])

    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:gz") as tar:
        members = [
            member
            for member in tar.getmembers()
            if member.isfile() and member.name.rsplit("/", 1)[-1] == "trial_results.parquet"
        ]
        fail(len(members) == 1, f"expected one trial_results.parquet; found {len(members)}")
        stream = tar.extractfile(members[0])
        fail(stream is not None, "TRIAL_RESULTS_MEMBER_UNREADABLE")
        parquet_bytes = stream.read()

    fail(
        sha256(parquet_bytes) == EXPECTED_PARQUET_SHA256,
        "TRIAL_RESULTS_PARQUET_SHA256_MISMATCH",
    )
    return parquet_bytes


def main() -> None:
    artifact_zip = download_artifact_zip()
    parquet_bytes = extract_verified_trial_results(artifact_zip)
    table = pq.read_table(io.BytesIO(parquet_bytes))

    fail(table.num_rows == EXPECTED_TRIAL_COUNT, f"expected 450 rows, got {table.num_rows}")
    fail("final_cash" in table.column_names, f"final_cash missing from schema: {table.column_names}")
    values = table.column("final_cash").to_pylist()
    fail(len(values) == EXPECTED_TRIAL_COUNT, "Final_Cash count mismatch")
    fail(
        all(isinstance(value, int) and not isinstance(value, bool) for value in values),
        "Final_Cash source values are not all integer amounts",
    )

    if "trial_id" in table.column_names:
        ids = table.column("trial_id").to_pylist()
        fail(sorted(ids) == list(range(1, EXPECTED_TRIAL_COUNT + 1)), "trial IDs do not cover 1..450")
    if "scenario_id" in table.column_names:
        scenarios = set(table.column("scenario_id").to_pylist())
        fail(scenarios == {EXPECTED_SCENARIO}, f"scenario identity mismatch: {scenarios}")

    ordered = sorted(values)
    position = Fraction((EXPECTED_TRIAL_COUNT - 1) * 9, 10)
    lower_index = position.numerator // position.denominator
    upper_index = min(lower_index + 1, EXPECTED_TRIAL_COUNT - 1)
    weight = position - lower_index
    lower = ordered[lower_index]
    upper = ordered[upper_index]
    exact = Fraction(lower * (weight.denominator - weight.numerator) + upper * weight.numerator, weight.denominator)

    numpy_p90 = float(np.quantile(np.asarray(values, dtype=np.float64), 0.90, method="linear"))
    float_linear = float(lower) + float(weight) * (float(upper) - float(lower))
    report: dict[str, Any] = {
        "audit_status": "PASS_SCOPED_READ_ONLY",
        "repository": REPOSITORY,
        "artifact_id": ARTIFACT_ID,
        "source_run_id": SOURCE_RUN_ID,
        "scenario": EXPECTED_SCENARIO,
        "source_sha": EXPECTED_SOURCE_SHA,
        "artifact_zip_sha256": sha256(artifact_zip),
        "trial_results_parquet_sha256": sha256(parquet_bytes),
        "trial_count": len(values),
        "field": "final_cash",
        "source_values_are_integer_yer": True,
        "quantile": "P90",
        "method": "numpy.quantile(method=linear)",
        "position_zero_based": f"{position.numerator}/{position.denominator}",
        "lower_index_zero_based": lower_index,
        "upper_index_zero_based": upper_index,
        "lower_order_statistic_yer": lower,
        "upper_order_statistic_yer": upper,
        "interpolation_weight": f"{weight.numerator}/{weight.denominator}",
        "exact_linear_quantile_fraction": f"{exact.numerator}/{exact.denominator}",
        "exact_linear_quantile_decimal": float(exact),
        "exact_linear_quantile_is_integer_yer": exact.denominator == 1,
        "numpy_float64_p90": numpy_p90,
        "manual_float_linear_p90": float_linear,
        "observed_p16_cell": "C030_G030_STATS!L3",
        "observed_p16_cell_value": OBSERVED_P16_CELL_VALUE,
        "numpy_matches_observed_cell": numpy_p90 == OBSERVED_P16_CELL_VALUE,
        "numpy_float_minus_exact_value": numpy_p90 - float(exact),
        "policy_disposition": (
            "EXACT_INTEGER_QUANTILE_FLOAT_TAIL_CANDIDATE"
            if exact.denominator == 1 and numpy_p90 != float(exact)
            else "OWNER_POLICY_REVIEW_REQUIRED"
            if exact.denominator != 1
            else "NO_FLOAT_TAIL_REPRODUCED"
        ),
        "historical_data_modified": False,
        "published_workbook_modified": False,
        "simulation_or_trials_executed": False,
    }

    output = Path("p16_quantile_audit")
    output.mkdir(parents=True, exist_ok=True)
    destination = output / "quantile_boundary_report.json"
    destination.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
