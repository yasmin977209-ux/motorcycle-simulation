from __future__ import annotations

import hashlib
import json
import mmap
import os
import shutil
import tempfile
import tarfile
import traceback
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from scripts import stage13_gatea_fingerprint_bridge as gatea

REPO = "yasmin977209-ux/motorcycle-simulation"
STAGE7_RUN = 37225915321
STAGE7_HEAD = "e0b2fab6710833774937d778097363d7a8ee8e59"
STAGE10_RUN = 37709936740
STAGE10_HEAD = "ca73f2df37baacebbcad965fc5f433f129675820"
STAGE12_RUN = 37964656154
STAGE12_HEAD = "0156c5f4272eb0ca7e32442657d0df9eaf4973d3"
SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
MASTER_SEED = 20270101
REFERENCE_SHA256 = "ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479"
SCENARIOS = [f"C{c:03d}_G{g:03d}" for c in (100, 85, 70, 50, 30) for g in (100, 70, 50, 30, 0)]
BASE_BLOCKS = ((1, 300), (301, 350), (351, 400), (401, 450))
C100_ENRICHMENT_RUN = 37655041728
C100_ENRICHMENT_HEAD = "b4a88a117fa7d7fcdc7718d6a475699e3e8ac47e"
# Approved historical CP-F delivery-detail replay; this audit only reuses its artifact.
CP_F_REPLAY_RUN = 38619859394
CP_F_REPLAY_HEAD = "f7096bcc9f910df54a60d5a4329a7ebbcd2a43ae"
CP_F_REPLAY_BRANCH = "tmp/cp-f-delivery-20261014"
CP_F_REPLAY_SCHEMA = "stage12-daily-accounting-v1"
C100_ENRICHED_ARTIFACTS = {
    "C100_G000": (11496939782, "fc888978f92ed963c35774cb471dedd93d71ecc335c6fe1b765d897468821c16"),
    "C100_G030": (11497898524, "66aee1cdd7829c25c8b5800b74a69a241eeddee6b90e657c23e0ccd68049ec12"),
    "C100_G050": (11497164787, "61a90c9b0ca28ad7dc2943412822f3df99f4f5797bbb460343194cf5e28aadd8"),
    "C100_G070": (11497369182, "3e6fccb33b4892f2b1f46b91d3781e4723d3914e9273f6e71bd605fc3895db3f"),
    "C100_G100": (11498636066, "05a2c44bcd2f4af5ef613ba2f97ba7d7f6fa289404552394df6952f0a65f680d"),
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: str) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_ROOT_NOT_OBJECT: {path}")
    return value


def expected_collection_probability(scenario: str) -> float:
    return int(scenario[1:4]) / 100.0


def expected_recovery_rate(scenario: str) -> int:
    return int(scenario[6:9])


def rows_from_zip(scenario: str, archive_path: Path, manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[int, str]]:
    rows: list[dict[str, Any]] = []
    block_evidence: list[dict[str, Any]] = []
    trial_hashes: dict[int, str] = {}
    with zipfile.ZipFile(archive_path, "r") as zf:
        if scenario.startswith("C100_"):
            meta_raw = gatea.member(zf, "block_1_1_metadata.json")
            parquet_raw = gatea.member(zf, "block_1_1.parquet")
            hashes, evidence = gatea.validate_block(
                scenario, 1, 1, meta_raw, parquet_raw, manifest, STAGE7_RUN
            )
            block_rows = pq.read_table(BytesIO(parquet_raw)).to_pylist()
            if list(hashes) != [1] or len(block_rows) != 1:
                raise RuntimeError(f"C100_TRIAL_COVERAGE_MISMATCH: {scenario}")
            rows.extend(block_rows)
            trial_hashes.update(hashes)
            block_evidence.append(evidence)
        else:
            expected_ids: list[int] = []
            for start, end in BASE_BLOCKS + ((451, 550),):
                name = f"block_{start}_{end}"
                meta_raw = gatea.member(zf, name + "_metadata.json")
                parquet_raw = gatea.member(zf, name + ".parquet")
                source_run = STAGE10_RUN if start == 451 else STAGE7_RUN
                hashes, evidence = gatea.validate_block(
                    scenario,
                    start,
                    end,
                    meta_raw,
                    parquet_raw,
                    manifest,
                    source_run,
                    allow_bad_suffix=(start == 451),
                )
                block_rows = pq.read_table(BytesIO(parquet_raw)).to_pylist()
                block_ids = [int(row.get("trial_id", -1)) for row in block_rows]
                wanted_ids = list(range(start, end + 1))
                if block_ids != wanted_ids or list(hashes) != wanted_ids:
                    raise RuntimeError(f"TRIAL_ID_SEQUENCE_MISMATCH: {scenario}/{name}")
                rows.extend(block_rows)
                trial_hashes.update(hashes)
                expected_ids.extend(wanted_ids)
                block_evidence.append(evidence)
            if [int(row.get("trial_id", -1)) for row in rows] != list(range(1, 551)):
                raise RuntimeError(f"CANONICAL_TRIAL_COVERAGE_MISMATCH: {scenario}")
    expected_count = 1 if scenario.startswith("C100_") else 550
    if len(rows) != expected_count:
        raise RuntimeError(f"TRIAL_COUNT_MISMATCH: {scenario}: {len(rows)} != {expected_count}")
    for row in rows:
        if row.get("scenario_id") != scenario:
            raise RuntimeError(f"SCENARIO_ID_MISMATCH: {scenario}/{row.get('trial_id')}")
        if row.get("collection_probability") != expected_collection_probability(scenario):
            raise RuntimeError(f"COLLECTION_PROBABILITY_MISMATCH: {scenario}/{row.get('trial_id')}")
        if row.get("recovery_rate_pct") != expected_recovery_rate(scenario):
            raise RuntimeError(f"RECOVERY_RATE_MISMATCH: {scenario}/{row.get('trial_id')}")
        if type(row.get("final_net_project_equity")) is not int:
            raise RuntimeError(f"FINAL_EQUITY_NOT_INTEGER: {scenario}/{row.get('trial_id')}")
    return rows, block_evidence, trial_hashes


def inventory_identity_mismatches(
    manifest: dict[str, Any], inventory: dict[str, Any]
) -> list[dict[str, Any]]:
    artifact_map = manifest.get("artifact_manifest", {}).get("enriched_artifacts", {})
    run_map = manifest.get("artifact_manifest", {}).get("enrichment_run_ids", {})
    mismatches: list[dict[str, Any]] = []
    for item in inventory.get("artifacts", []):
        scenario = item.get("scenario")
        manifest_artifact_id = artifact_map.get(scenario)
        manifest_run_id = run_map.get(scenario)
        if manifest_artifact_id != item.get("artifact_id") or manifest_run_id != item.get("run_id"):
            mismatches.append({
                "scenario": scenario,
                "manifest_artifact_id": manifest_artifact_id,
                "inventory_artifact_id": item.get("artifact_id"),
                "manifest_run_id": manifest_run_id,
                "inventory_run_id": item.get("run_id"),
            })
    return mismatches


def select_maxcase(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    positive = [
        row for row in rows
        if type(row.get("final_net_project_equity")) is int
        and row["final_net_project_equity"] > 0
    ]
    if not positive:
        return None
    highest = max(row["final_net_project_equity"] for row in positive)
    return min(
        (row for row in positive if row["final_net_project_equity"] == highest),
        key=lambda row: int(row["trial_id"]),
    )



def _iso_date(value: Any) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else str(value)




def _read_representative_summary_daily(stream) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Read top-level summary/daily from compact or pretty representative JSON.

    A representative can exceed 250 MB due to event/asset sections. This scans the
    top-level structure with mmap and decodes only summary and daily values. Nested
    keys with the same names are ignored.
    """
    with tempfile.TemporaryFile(mode="w+b") as temp_file:
        shutil.copyfileobj(stream, temp_file, length=1024 * 1024)
        temp_file.flush()
        size = os.fstat(temp_file.fileno()).st_size
        if size <= 0:
            raise RuntimeError("REPRESENTATIVE_JSON_EMPTY")
        with mmap.mmap(temp_file.fileno(), length=0, access=mmap.ACCESS_READ) as mapped:
            def skip_ws(cursor: int) -> int:
                while cursor < size and mapped[cursor] in (32, 9, 10, 13):
                    cursor += 1
                return cursor

            def scan_string(cursor: int) -> int:
                if cursor >= size or mapped[cursor] != 34:
                    raise RuntimeError("REPRESENTATIVE_JSON_STRING_EXPECTED")
                cursor += 1
                escaped = False
                while cursor < size:
                    char = mapped[cursor]
                    if escaped:
                        escaped = False
                    elif char == 92:
                        escaped = True
                    elif char == 34:
                        return cursor + 1
                    cursor += 1
                raise RuntimeError("REPRESENTATIVE_JSON_STRING_UNTERMINATED")

            def scan_value(cursor: int, name: str) -> int:
                cursor = skip_ws(cursor)
                if cursor >= size:
                    raise RuntimeError(f"REPRESENTATIVE_JSON_VALUE_EMPTY:{name}")
                first = mapped[cursor]
                if first in (123, 91):
                    stack = [125 if first == 123 else 93]
                    cursor += 1
                    in_string = False
                    escaped = False
                    while cursor < size and stack:
                        char = mapped[cursor]
                        if in_string:
                            if escaped:
                                escaped = False
                            elif char == 92:
                                escaped = True
                            elif char == 34:
                                in_string = False
                        else:
                            if char == 34:
                                in_string = True
                            elif char == 123:
                                stack.append(125)
                            elif char == 91:
                                stack.append(93)
                            elif char in (125, 93):
                                if char != stack[-1]:
                                    raise RuntimeError(
                                        f"REPRESENTATIVE_JSON_DELIMITER_MISMATCH:{name}"
                                    )
                                stack.pop()
                        cursor += 1
                    if stack:
                        raise RuntimeError(f"REPRESENTATIVE_JSON_VALUE_UNTERMINATED:{name}")
                    return cursor
                if first == 34:
                    return scan_string(cursor)
                while cursor < size and mapped[cursor] not in (44, 125, 93, 32, 9, 10, 13):
                    cursor += 1
                return cursor

            cursor = skip_ws(0)
            if cursor >= size or mapped[cursor] != 123:
                raise RuntimeError("REPRESENTATIVE_JSON_ROOT_NOT_OBJECT")
            cursor += 1
            selected: dict[str, Any] = {}
            wanted = {"summary", "daily"}
            while cursor < size:
                cursor = skip_ws(cursor)
                if cursor < size and mapped[cursor] == 44:
                    cursor = skip_ws(cursor + 1)
                if cursor < size and mapped[cursor] == 125:
                    cursor += 1
                    break
                key_start = cursor
                key_end = scan_string(cursor)
                try:
                    key = json.loads(mapped[key_start:key_end])
                except Exception as exc:
                    raise RuntimeError("REPRESENTATIVE_JSON_TOP_LEVEL_KEY_INVALID") from exc
                cursor = skip_ws(key_end)
                if cursor >= size or mapped[cursor] != 58:
                    raise RuntimeError("REPRESENTATIVE_JSON_COLON_MISSING")
                value_start = skip_ws(cursor + 1)
                value_end = scan_value(value_start, str(key))
                if key in wanted:
                    try:
                        selected[str(key)] = json.loads(mapped[value_start:value_end])
                    except Exception as exc:
                        raise RuntimeError(f"REPRESENTATIVE_JSON_MEMBER_PARSE_FAILED:{key}") from exc
                cursor = skip_ws(value_end)
                if cursor < size and mapped[cursor] == 44:
                    cursor += 1
                elif cursor < size and mapped[cursor] == 125:
                    cursor += 1
                    break
                else:
                    raise RuntimeError("REPRESENTATIVE_JSON_TOP_LEVEL_SEPARATOR_INVALID")
            if set(selected) != wanted:
                raise RuntimeError(
                    f"REPRESENTATIVE_JSON_REQUIRED_MEMBERS_MISSING:{sorted(wanted-set(selected))}"
                )
            summary, daily = selected["summary"], selected["daily"]
            if not isinstance(summary, dict) or not isinstance(daily, list):
                raise RuntimeError("REPRESENTATIVE_SUMMARY_OR_DAILY_SCHEMA_INVALID")
            return summary, daily


def reconcile_enriched_c100_daily_rows(
    scenario: str,
    enriched_rows: list[dict[str, Any]],
    stage12_rows: list[dict[str, Any]],
    *,
    trial_id: int,
    expected_trial_sha256: str,
    source_sha: str,
    master_seed: int,
    final_close_date: str,
    final_cash: int,
    final_equity: int,
    cumulative_project_profit: int,
) -> list[dict[str, Any]]:
    """Reuse manifest-pinned C100 daily rows only when trial identity and ledger values reconcile."""
    if scenario not in C100_ENRICHED_ARTIFACTS or trial_id != 1:
        raise RuntimeError(f"C100_ENRICHED_ROLE_OUT_OF_SCOPE:{scenario}/{trial_id}")
    if not enriched_rows or len(enriched_rows) != len(stage12_rows):
        raise RuntimeError(f"C100_ENRICHED_DAILY_ROW_COUNT_MISMATCH:{scenario}")
    required = {
        "date", "Cash", "Net_Equity", "Cumulative_Project_Profit",
        "Active_Bikes", "Owned_Transferred_Bikes", "Pending_Claims",
        "Partner1_Reinvestment_Balance", "Partner2_Reinvestment_Balance",
    }
    for row in enriched_rows:
        missing = sorted(required - set(row))
        if missing:
            raise RuntimeError(f"C100_ENRICHED_DAILY_FIELDS_MISSING:{scenario}:{missing}")
        for key in ("Partner1_Reinvestment_Balance", "Partner2_Reinvestment_Balance"):
            if type(row[key]) is not int:
                raise RuntimeError(f"C100_ENRICHED_MEMO_BALANCE_NOT_INTEGER:{scenario}:{key}")
        if "scenario_id" in row and row["scenario_id"] != scenario:
            raise RuntimeError(f"C100_ENRICHED_SCENARIO_MISMATCH:{scenario}")
        if "trial_id" in row and int(row["trial_id"]) != trial_id:
            raise RuntimeError(f"C100_ENRICHED_TRIAL_ID_MISMATCH:{scenario}")
        if "source_sha" in row and row["source_sha"] != source_sha:
            raise RuntimeError(f"C100_ENRICHED_SOURCE_SHA_MISMATCH:{scenario}")
        if "master_seed" in row and int(row["master_seed"]) != master_seed:
            raise RuntimeError(f"C100_ENRICHED_MASTER_SEED_MISMATCH:{scenario}")
        if "result_sha256" in row and row["result_sha256"] != expected_trial_sha256:
            raise RuntimeError(f"C100_ENRICHED_TRIAL_SHA_MISMATCH:{scenario}")
        if "Final_Close_Date" in row and row["Final_Close_Date"] != final_close_date:
            raise RuntimeError(f"C100_ENRICHED_FINAL_CLOSE_DATE_MISMATCH:{scenario}")

    enriched_sorted = sorted(enriched_rows, key=lambda row: _iso_date(row["date"]))
    stage12_sorted = sorted(stage12_rows, key=lambda row: _iso_date(row["date"]))
    enriched_dates = [_iso_date(row["date"]) for row in enriched_sorted]
    stage12_dates = [_iso_date(row["date"]) for row in stage12_sorted]
    if enriched_dates != stage12_dates or len(set(enriched_dates)) != len(enriched_dates):
        raise RuntimeError(f"C100_ENRICHED_DAILY_DATE_ALIGNMENT_MISMATCH:{scenario}")
    compare_pairs = (
        ("Cash", "Closing_Cash"),
        ("Net_Equity", "Closing_Equity"),
        ("Cumulative_Project_Profit", "Retained_Earnings"),
        ("Active_Bikes", "Active_Bikes"),
        ("Owned_Transferred_Bikes", "Owned_Transferred_Bikes"),
        ("Pending_Claims", "Pending_Claims"),
    )
    payload: list[dict[str, Any]] = []
    for enriched, stage12 in zip(enriched_sorted, stage12_sorted):
        for source_key, ledger_key in compare_pairs:
            if int(enriched[source_key]) != int(stage12[ledger_key]):
                raise RuntimeError(
                    f"C100_ENRICHED_STAGE12_LEDGER_MISMATCH:{scenario}:"
                    f"{_iso_date(enriched['date'])}:{source_key}"
                )
        payload.append({
            "date": _iso_date(enriched["date"]),
            "Final_Close_Date": str(enriched.get("Final_Close_Date", final_close_date)),
            "Cash": int(enriched["Cash"]),
            "Net_Equity": int(enriched["Net_Equity"]),
            "Cumulative_Project_Profit": int(enriched["Cumulative_Project_Profit"]),
            "Active_Bikes": int(enriched["Active_Bikes"]),
            "Owned_Transferred_Bikes": int(enriched["Owned_Transferred_Bikes"]),
            "Pending_Claims": int(enriched["Pending_Claims"]),
            "Partner1_Reinvestment_Balance": int(enriched["Partner1_Reinvestment_Balance"]),
            "Partner2_Reinvestment_Balance": int(enriched["Partner2_Reinvestment_Balance"]),
            "trial_id": trial_id,
            "source_sha": source_sha,
            "master_seed": master_seed,
            "result_sha256": expected_trial_sha256,
        })
    if enriched_dates[0] != "2027-01-01" or enriched_dates[-1] != final_close_date:
        raise RuntimeError(f"C100_ENRICHED_DAILY_TERMINAL_DATE_MISMATCH:{scenario}")
    if (
        payload[-1]["Cash"] != final_cash
        or payload[-1]["Net_Equity"] != final_equity
        or payload[-1]["Cumulative_Project_Profit"] != cumulative_project_profit
    ):
        raise RuntimeError(f"C100_ENRICHED_DAILY_TERMINAL_VALUE_MISMATCH:{scenario}")
    return payload




def _non_c100_daily_rows_from_enriched_role_artifact(
    scenario: str,
    role: str,
    artifact: dict[str, Any],
    artifact_zip: Path,
    expected_trial_sha256: str,
    selected_trial: dict[str, Any],
    stage12_rows: list[dict[str, Any]],
    manifest: dict[str, Any],
    inventory_item: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Reuse a Stage 9A representative only when the selected MaxCase is the exact role Trial."""
    if scenario.startswith("C100_") or role not in ("P10", "P50", "P90", "Loss"):
        raise RuntimeError(f"STAGE9A_ROLE_REUSE_OUT_OF_SCOPE:{scenario}:{role}")
    selected_id = int(selected_trial["trial_id"])
    role_ids = manifest.get("representative_trials", {}).get(scenario, {})
    inventory_roles = inventory_item.get("roles", {})
    if int(role_ids.get(role, -1)) != selected_id:
        raise RuntimeError(f"STAGE9A_ROLE_TRIAL_ID_MISMATCH:{scenario}:{role}:{selected_id}")
    if int(inventory_roles.get(role, {}).get("trial_id", -1)) != selected_id:
        raise RuntimeError(f"STAGE9A_INVENTORY_ROLE_TRIAL_ID_MISMATCH:{scenario}:{role}:{selected_id}")

    expected_artifact_id = int(manifest.get("artifact_manifest", {}).get("enriched_artifacts", {}).get(scenario, -1))
    expected_run_id = int(manifest.get("artifact_manifest", {}).get("enrichment_run_ids", {}).get(scenario, -1))
    inventory_artifact_id = int(inventory_item.get("artifact_id", -1))
    inventory_run_id = int(inventory_item.get("run_id", -1))
    actual_artifact_id = int(artifact.get("id", -1))
    expected_zip_sha = str(inventory_item.get("zip_sha256", "")).removeprefix("sha256:")
    actual_api_digest = str(artifact.get("digest", "")).removeprefix("sha256:")
    actual_zip_sha = gatea.sha_file(artifact_zip)
    if (
        expected_artifact_id != inventory_artifact_id
        or expected_artifact_id != actual_artifact_id
        or expected_run_id != inventory_run_id
        or expected_run_id != C100_ENRICHMENT_RUN
    ):
        raise RuntimeError(f"STAGE9A_ROLE_ARTIFACT_IDENTITY_MISMATCH:{scenario}")
    if not expected_zip_sha or actual_zip_sha != expected_zip_sha or actual_api_digest != expected_zip_sha:
        raise RuntimeError(f"STAGE9A_ROLE_ARTIFACT_SHA256_MISMATCH:{scenario}")

    with zipfile.ZipFile(artifact_zip, "r") as outer:
        names = outer.namelist()
        if len(names) != 1 or not names[0].endswith(".tar.gz"):
            raise RuntimeError(f"STAGE9A_ROLE_OUTER_ARCHIVE_LAYOUT_INVALID:{scenario}")
        with tarfile.open(fileobj=BytesIO(outer.read(names[0])), mode="r:gz") as archive:
            members = {m.name.removeprefix("./"): m for m in archive.getmembers() if m.isfile()}
            representative_name = f"representatives/{role}.json"
            required = {"scenario_metadata.json", "trial_fingerprints.json", "trial_results.parquet", representative_name}
            if not required.issubset(members):
                raise RuntimeError(f"STAGE9A_ROLE_REQUIRED_MEMBER_MISSING:{scenario}:{sorted(required-set(members))}")

            def read_member(name: str) -> bytes:
                stream = archive.extractfile(members[name])
                if stream is None:
                    raise RuntimeError(f"STAGE9A_ROLE_MEMBER_UNREADABLE:{scenario}:{name}")
                return stream.read()

            metadata = json.loads(read_member("scenario_metadata.json"))
            fingerprints = json.loads(read_member("trial_fingerprints.json"))
            if (
                metadata.get("scenario") != scenario
                or metadata.get("source_sha") != SOURCE_SHA
                or str(metadata.get("run_id")) != str(STAGE7_RUN)
                or int(metadata.get("trial_count", -1)) != 450
                or int(metadata.get("master_seed", MASTER_SEED)) != MASTER_SEED
                or int(metadata.get("recovery_rate_pct", -1)) != expected_recovery_rate(scenario)
                or float(metadata.get("collection_probability", -1)) != expected_collection_probability(scenario)
            ):
                raise RuntimeError(f"STAGE9A_ROLE_METADATA_IDENTITY_MISMATCH:{scenario}:{role}")
            fingerprint_map = fingerprints.get("fingerprints", {})
            if (
                fingerprints.get("scenario") != scenario
                or fingerprints.get("source_sha") != SOURCE_SHA
                or str(fingerprints.get("run_id")) != str(STAGE7_RUN)
                or int(fingerprints.get("trial_count", -1)) != 450
                or fingerprint_map.get(str(selected_id)) != expected_trial_sha256
            ):
                raise RuntimeError(f"STAGE9A_ROLE_TRIAL_FINGERPRINT_MISMATCH:{scenario}:{role}:{selected_id}")

            trial_rows = pq.read_table(BytesIO(read_member("trial_results.parquet"))).to_pylist()
            if len(trial_rows) != 450:
                raise RuntimeError(f"STAGE9A_ROLE_TRIAL_RESULT_COUNT_MISMATCH:{scenario}")
            selected_rows = [row for row in trial_rows if int(row.get("trial_id", -1)) == selected_id]
            if len(selected_rows) != 1:
                raise RuntimeError(f"STAGE9A_ROLE_SELECTED_TRIAL_NOT_UNIQUE:{scenario}:{role}:{selected_id}")
            selected_record = selected_rows[0]
            if (
                selected_record.get("scenario_id") != scenario
                or gatea.row_sha(selected_record) != expected_trial_sha256
            ):
                raise RuntimeError(f"STAGE9A_ROLE_SELECTED_TRIAL_HASH_MISMATCH:{scenario}:{role}:{selected_id}")

            with archive.extractfile(members[representative_name]) as stream:
                summary, daily_rows = _read_representative_summary_daily(stream)
            if (
                summary.get("scenario_id") != scenario
                or int(summary.get("trial_id", -1)) != selected_id
                or gatea.row_sha(summary) != expected_trial_sha256
            ):
                raise RuntimeError(f"STAGE9A_ROLE_SUMMARY_FINGERPRINT_MISMATCH:{scenario}:{role}:{selected_id}")
            summary_keys = (
                "scenario_id", "collection_probability", "recovery_rate_pct", "trial_id",
                "final_close_date", "final_net_project_equity", "final_cash",
                "cumulative_project_profit", "operating_net_profit", "termination_count",
                "secondary_cycle_count", "owned_bikes", "held_assets",
                "total_operating_revenue", "bad_debt", "guarantee_recovered",
                "partner1_final_entitlement", "partner2_final_entitlement",
            )
            for key in summary_keys:
                if key not in selected_trial or summary.get(key) != selected_trial.get(key):
                    raise RuntimeError(f"STAGE9A_ROLE_SUMMARY_MISMATCH:{scenario}:{role}:{selected_id}:{key}")
            expected_daily_count = int(inventory_roles.get(role, {}).get("daily_rows", -1))
            if not daily_rows or len(daily_rows) != expected_daily_count or len(daily_rows) != len(stage12_rows):
                raise RuntimeError(f"STAGE9A_ROLE_DAILY_ROW_COUNT_MISMATCH:{scenario}:{role}:{selected_id}")
            daily_rows = sorted(daily_rows, key=lambda row: _iso_date(row.get("date")))
            stage12_sorted = sorted(stage12_rows, key=lambda row: _iso_date(row.get("date")))
            daily_dates = [_iso_date(row.get("date")) for row in daily_rows]
            if (
                not daily_dates
                or len(set(daily_dates)) != len(daily_dates)
                or daily_dates != [_iso_date(row.get("date")) for row in stage12_sorted]
                or daily_dates[0] != "2027-01-01"
                or daily_dates[-1] != str(selected_trial["final_close_date"])
            ):
                raise RuntimeError(f"STAGE9A_ROLE_DAILY_DATE_ALIGNMENT_MISMATCH:{scenario}:{role}:{selected_id}")
            from datetime import date, timedelta
            for index in range(1, len(daily_dates)):
                if date.fromisoformat(daily_dates[index]) != date.fromisoformat(daily_dates[index-1]) + timedelta(days=1):
                    raise RuntimeError(f"STAGE9A_ROLE_DAILY_DATE_GAP:{scenario}:{role}:{daily_dates[index]}")
            required_fields = {
                "date", "Final_Close_Date", "Cash", "Net_Equity", "Cumulative_Project_Profit",
                "Active_Bikes", "Owned_Transferred_Bikes", "Pending_Claims",
                "Partner1_Reinvestment_Balance", "Partner2_Reinvestment_Balance", "trial_id",
            }
            compare_pairs = (
                ("Cash", "Closing_Cash"),
                ("Net_Equity", "Closing_Equity"),
                ("Cumulative_Project_Profit", "Retained_Earnings"),
                ("Active_Bikes", "Active_Bikes"),
                ("Owned_Transferred_Bikes", "Owned_Transferred_Bikes"),
                ("Pending_Claims", "Pending_Claims"),
                ("Accounts_Receivable", "Closing_AR"),
                ("Gross_Bike_Assets", "Closing_Gross_Bike_Assets"),
                ("Accumulated_Depreciation", "Closing_Accumulated_Depreciation"),
                ("Capital", "Capital"),
                ("Guarantee_Claim_Receivable", "Guarantee_Claim_Receivable"),
            )
            for index, (row, stage12) in enumerate(zip(daily_rows, stage12_sorted)):
                missing = sorted(required_fields - set(row))
                if missing:
                    raise RuntimeError(f"STAGE9A_ROLE_DAILY_FIELDS_MISSING:{scenario}:{role}:{missing}")
                if type(row.get("trial_id")) is not int or row["trial_id"] != selected_id:
                    raise RuntimeError(f"STAGE9A_ROLE_DAILY_TRIAL_ID_MISMATCH:{scenario}:{role}:{index}")
                if row.get("Final_Close_Date") != selected_trial.get("final_close_date"):
                    raise RuntimeError(f"STAGE9A_ROLE_DAILY_CLOSE_DATE_MISMATCH:{scenario}:{role}:{index}")
                for field in ("Partner1_Reinvestment_Balance", "Partner2_Reinvestment_Balance"):
                    if type(row[field]) is not int:
                        raise RuntimeError(f"STAGE9A_ROLE_MEMO_BALANCE_NOT_INTEGER:{scenario}:{role}:{index}:{field}")
                for source_key, ledger_key in compare_pairs:
                    if source_key in row and ledger_key in stage12:
                        if type(row[source_key]) is not int or type(stage12[ledger_key]) is not int or row[source_key] != stage12[ledger_key]:
                            raise RuntimeError(f"STAGE9A_ROLE_STAGE12_LEDGER_MISMATCH:{scenario}:{role}:{daily_dates[index]}:{source_key}")
            last = daily_rows[-1]
            if (
                int(last["Cash"]) != int(selected_trial["final_cash"])
                or int(last["Net_Equity"]) != int(selected_trial["final_net_project_equity"])
                or int(last["Cumulative_Project_Profit"]) != int(selected_trial["cumulative_project_profit"])
            ):
                raise RuntimeError(f"STAGE9A_ROLE_TERMINAL_VALUE_MISMATCH:{scenario}:{role}:{selected_id}")

            payload = [
                {
                    **row,
                    "date": _iso_date(row["date"]),
                    "Final_Close_Date": str(row["Final_Close_Date"]),
                    "trial_id": selected_id,
                    "source_sha": SOURCE_SHA,
                    "master_seed": MASTER_SEED,
                    "result_sha256": expected_trial_sha256,
                }
                for row in daily_rows
            ]
            info = members[representative_name]
            evidence = {
                "run_id": C100_ENRICHMENT_RUN,
                "source_stage7_run_id": STAGE7_RUN,
                "source_sha": SOURCE_SHA,
                "master_seed": MASTER_SEED,
                "artifact_id": actual_artifact_id,
                "artifact_name": artifact.get("name"),
                "artifact_api_digest": artifact.get("digest"),
                "artifact_zip_sha256": actual_zip_sha,
                "scenario_metadata_sha256": gatea.sha_bytes(read_member("scenario_metadata.json")),
                "trial_fingerprints_sha256": gatea.sha_bytes(read_member("trial_fingerprints.json")),
                "representative_payload_member": representative_name,
                "representative_payload_member_size_bytes": int(info.size),
                "representative_payload_member_crc32": f"{int(info.chksum):08x}",
                "role": role,
                "trial_id": selected_id,
                "trial_result_sha256": expected_trial_sha256,
                "daily_row_count": len(payload),
                "partner_memo_fields_status": "VERIFIED_REUSED_SOURCE_ARTIFACT",
                "day_by_day_stage12_reconciliation": True,
                "historical_dataset_modified": False,
                "production_monte_carlo_run": False,
            }
            return payload, evidence


def _cpf_artifact_maxcase_trial_id(artifact_zip: Path, scenario: str) -> int:
    """Read CP-F role identity so a different Trial is never presented as this scenario's MaxCase."""
    with zipfile.ZipFile(artifact_zip, "r") as outer:
        names = outer.namelist()
        if len(names) != 8 or len(names) != len(set(names)) or "scenario_manifest.json" not in names:
            raise RuntimeError(f"CP_F_OUTER_ARCHIVE_LAYOUT_INVALID:{scenario}")
        manifest = json.loads(gatea.member(outer, "scenario_manifest.json"))
    if (
        not isinstance(manifest, dict)
        or manifest.get("scenario") != scenario
        or manifest.get("status") != "PASS"
        or manifest.get("source_sha") != SOURCE_SHA
        or int(manifest.get("master_seed", -1)) != MASTER_SEED
        or manifest.get("schema_version") != CP_F_REPLAY_SCHEMA
        or manifest.get("extension_trial_ids") != list(range(551, 1201))
    ):
        raise RuntimeError(f"CP_F_MANIFEST_IDENTITY_MISMATCH:{scenario}")
    return int(manifest.get("representative_trial_ids", {}).get("MaxCase", -1))


def _pending_maxcase_memo_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Preserve known ledger values while marking unavailable partner memo balances explicitly."""
    return [
        {
            **row,
            "Partner1_Reinvestment_Balance": "PENDING_DATA_SOURCE",
            "Partner2_Reinvestment_Balance": "PENDING_DATA_SOURCE",
        }
        for row in rows
    ]


def _non_c100_daily_rows_from_cpf_artifact(
    scenario: str,
    artifact: dict[str, Any],
    artifact_zip: Path,
    expected_trial_sha256: str,
    selected_trial: dict[str, Any],
    stage12_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Reuse a CP-F MaxCase ledger only after exact identity and ledger reconciliation."""
    if scenario.startswith("C100_"):
        raise RuntimeError(f"CP_F_ROLE_REUSE_C100_NOT_ALLOWED:{scenario}")
    expected_trial_sha256 = gatea.valid_sha(expected_trial_sha256, f"{scenario}/selected")
    with zipfile.ZipFile(artifact_zip, "r") as outer:
        names = outer.namelist()
        if len(names) != 8 or len(names) != len(set(names)):
            raise RuntimeError(f"CP_F_OUTER_ARCHIVE_LAYOUT_INVALID:{scenario}")
        if not {"scenario_manifest.json", "representatives/Max Case.json"}.issubset(set(names)):
            raise RuntimeError(f"CP_F_REQUIRED_MEMBER_MISSING:{scenario}")
        manifest_raw = gatea.member(outer, "scenario_manifest.json")
        manifest = json.loads(manifest_raw)
        if not isinstance(manifest, dict):
            raise RuntimeError(f"CP_F_MANIFEST_SCHEMA_INVALID:{scenario}")
        if artifact.get("name") != f"cp-f-replay-{scenario}":
            raise RuntimeError(f"CP_F_ARTIFACT_NAME_MISMATCH:{scenario}")
        expected_identity = {
            "scenario": scenario,
            "status": "PASS",
            "source_sha": SOURCE_SHA,
            "master_seed": MASTER_SEED,
            "schema_version": CP_F_REPLAY_SCHEMA,
            "historical_daily_trials": 550,
            "extension_trial_count": 650,
            "non_c100_gate_a_fingerprints_verified": True,
            "production_monte_carlo_run": False,
            "historical_dataset_modified": False,
            "historical_parquet_modified": False,
            "main_modified": False,
            "release_created": False,
            "source_sha_bumped": False,
        }
        for key, expected in expected_identity.items():
            if manifest.get(key) != expected:
                raise RuntimeError(
                    f"CP_F_MANIFEST_IDENTITY_MISMATCH:{scenario}:{key}:"
                    f"expected={expected!r}:actual={manifest.get(key)!r}"
                )
        if manifest.get("extension_trial_ids") != list(range(551, 1201)):
            raise RuntimeError(f"CP_F_EXTENSION_COVERAGE_INVALID:{scenario}")
        trial_id = int(selected_trial["trial_id"])
        if (
            trial_id not in manifest.get("detail_replay_trial_ids", [])
            or trial_id not in manifest.get("representative_payload_trial_ids", [])
            or trial_id != int(manifest.get("representative_trial_ids", {}).get("MaxCase", -1))
        ):
            raise RuntimeError(f"CP_F_MAXCASE_ROLE_IDENTITY_MISMATCH:{scenario}:{trial_id}")
        fingerprint_map = manifest.get("trial_fingerprints", {})
        if not isinstance(fingerprint_map, dict):
            raise RuntimeError(f"CP_F_TRIAL_FINGERPRINT_MAP_INVALID:{scenario}")
        manifest_trial_sha = gatea.valid_sha(
            fingerprint_map.get(str(trial_id)), f"{scenario}/CP_F/{trial_id}"
        )
        if manifest_trial_sha != expected_trial_sha256:
            raise RuntimeError(f"CP_F_TRIAL_FINGERPRINT_MISMATCH:{scenario}:{trial_id}")

        with outer.open("representatives/Max Case.json", "r") as representative_stream:
            summary, daily_rows = _read_representative_summary_daily(representative_stream)
        summary_keys = (
            "scenario_id", "collection_probability", "recovery_rate_pct", "trial_id",
            "final_close_date", "final_net_project_equity", "final_cash",
            "cumulative_project_profit", "operating_net_profit", "termination_count",
            "secondary_cycle_count", "owned_bikes", "held_assets",
            "total_operating_revenue", "bad_debt", "guarantee_recovered",
            "partner1_final_entitlement", "partner2_final_entitlement",
        )
        for key in summary_keys:
            if key not in selected_trial or summary.get(key) != selected_trial.get(key):
                raise RuntimeError(
                    f"CP_F_MAXCASE_SUMMARY_MISMATCH:{scenario}:{trial_id}:{key}:"
                    f"summary={summary.get(key)!r}:selected={selected_trial.get(key)!r}"
                )
        if len(daily_rows) != len(stage12_rows):
            raise RuntimeError(f"CP_F_MAXCASE_DAILY_ROW_COUNT_MISMATCH:{scenario}:{trial_id}")
        daily_rows = sorted(daily_rows, key=lambda row: _iso_date(row.get("date")))
        stage12_sorted = sorted(stage12_rows, key=lambda row: _iso_date(row.get("date")))
        daily_dates = [_iso_date(row.get("date")) for row in daily_rows]
        if not daily_dates or len(set(daily_dates)) != len(daily_dates):
            raise RuntimeError(f"CP_F_MAXCASE_DAILY_DATES_DUPLICATE_OR_EMPTY:{scenario}")
        if daily_dates[0] != "2027-01-01" or daily_dates[-1] != str(selected_trial["final_close_date"]):
            raise RuntimeError(f"CP_F_MAXCASE_DAILY_TERMINAL_DATE_MISMATCH:{scenario}")
        from datetime import date, timedelta
        for index in range(1, len(daily_dates)):
            previous = date.fromisoformat(daily_dates[index-1])
            current = date.fromisoformat(daily_dates[index])
            if current != previous + timedelta(days=1):
                raise RuntimeError(f"CP_F_MAXCASE_DAILY_DATE_GAP:{scenario}:{daily_dates[index]}")
        required_fields = {
            "date", "Final_Close_Date", "Cash", "Net_Equity",
            "Cumulative_Project_Profit", "Retained_Earnings", "Active_Bikes",
            "Owned_Transferred_Bikes", "Pending_Claims",
            "Partner1_Reinvestment_Balance", "Partner2_Reinvestment_Balance", "trial_id",
        }
        compare_pairs = (
            ("Cash", "Closing_Cash"),
            ("Net_Equity", "Closing_Equity"),
            ("Cumulative_Project_Profit", "Retained_Earnings"),
            ("Retained_Earnings", "Retained_Earnings"),
            ("Active_Bikes", "Active_Bikes"),
            ("Owned_Transferred_Bikes", "Owned_Transferred_Bikes"),
            ("Pending_Claims", "Pending_Claims"),
            ("Accounts_Receivable", "Closing_AR"),
            ("Gross_Bike_Assets", "Closing_Gross_Bike_Assets"),
            ("Accumulated_Depreciation", "Closing_Accumulated_Depreciation"),
            ("Capital", "Capital"),
            ("Guarantee_Claim_Receivable", "Guarantee_Claim_Receivable"),
        )
        for index, (row, stage12) in enumerate(zip(daily_rows, stage12_sorted)):
            missing = sorted(required_fields - set(row))
            if missing:
                raise RuntimeError(f"CP_F_MAXCASE_DAILY_FIELDS_MISSING:{scenario}:{missing}")
            if type(row.get("trial_id")) is not int or row["trial_id"] != trial_id:
                raise RuntimeError(f"CP_F_MAXCASE_TRIAL_ID_MISMATCH:{scenario}:{index}")
            if _iso_date(row.get("date")) != _iso_date(stage12.get("date")):
                raise RuntimeError(f"CP_F_MAXCASE_STAGE12_DATE_MISMATCH:{scenario}:{index}")
            if row.get("Final_Close_Date") != selected_trial.get("final_close_date"):
                raise RuntimeError(f"CP_F_MAXCASE_FINAL_CLOSE_DATE_MISMATCH:{scenario}:{index}")
            for key in ("Partner1_Reinvestment_Balance", "Partner2_Reinvestment_Balance"):
                if type(row.get(key)) is not int:
                    raise RuntimeError(f"CP_F_MAXCASE_MEMO_BALANCE_NOT_INTEGER:{scenario}:{trial_id}:{index}:{key}")
            for source_key, stage12_key in compare_pairs:
                if source_key in row and stage12_key in stage12:
                    if type(row[source_key]) is not int or type(stage12[stage12_key]) is not int:
                        raise RuntimeError(f"CP_F_MAXCASE_RECONCILIATION_NONINTEGER:{scenario}:{index}:{source_key}")
                    if row[source_key] != stage12[stage12_key]:
                        raise RuntimeError(f"CP_F_MAXCASE_STAGE12_LEDGER_MISMATCH:{scenario}:{daily_dates[index]}:{source_key}")
        last = daily_rows[-1]
        if (
            last["Cash"] != int(selected_trial["final_cash"])
            or last["Net_Equity"] != int(selected_trial["final_net_project_equity"])
            or last["Cumulative_Project_Profit"] != int(selected_trial["cumulative_project_profit"])
        ):
            raise RuntimeError(f"CP_F_MAXCASE_DAILY_FINAL_VALUES_MISMATCH:{scenario}")
        wrapped_rows = [
            {
                **row,
                "date": _iso_date(row["date"]),
                "Final_Close_Date": str(row["Final_Close_Date"]),
                "trial_id": trial_id,
                "source_sha": SOURCE_SHA,
                "master_seed": MASTER_SEED,
                "result_sha256": expected_trial_sha256,
            }
            for row in daily_rows
        ]
        info = outer.getinfo("representatives/Max Case.json")
        return wrapped_rows, {
            "run_id": CP_F_REPLAY_RUN,
            "run_head_sha": CP_F_REPLAY_HEAD,
            "run_branch": CP_F_REPLAY_BRANCH,
            "run_conclusion": "success",
            "artifact_id": int(artifact["id"]),
            "artifact_name": artifact.get("name"),
            "artifact_api_digest": artifact.get("digest"),
            "artifact_zip_sha256": gatea.sha_file(artifact_zip),
            "scenario_manifest_sha256": gatea.sha_bytes(manifest_raw),
            "representative_payload_member": "representatives/Max Case.json",
            "representative_payload_member_size_bytes": int(info.file_size),
            "representative_payload_member_crc32": f"{int(info.CRC):08x}",
            "trial_id": trial_id,
            "trial_result_sha256": expected_trial_sha256,
            "daily_row_count": len(wrapped_rows),
            "partner_memo_fields_status": "VERIFIED_REUSED_SOURCE_ARTIFACT",
            "manifest_non_c100_gate_a_fingerprints_verified": True,
            "historical_dataset_modified": False,
            "historical_parquet_modified": False,
            "production_monte_carlo_run": False,
            "day_by_day_stage12_reconciliation": True,
        }



def _c100_daily_rows_from_artifact(
    scenario: str,
    artifact: dict[str, Any],
    artifact_zip: Path,
    expected_trial_sha256: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    with zipfile.ZipFile(artifact_zip, "r") as outer:
        tar_names = [name for name in outer.namelist() if name.endswith(".tar.gz")]
        if len(tar_names) != 1 or len(outer.namelist()) != 1:
            raise RuntimeError(f"C100_ENRICHED_OUTER_ARCHIVE_LAYOUT_INVALID:{scenario}")
        tar_bytes = outer.read(tar_names[0])
    with tarfile.open(fileobj=BytesIO(tar_bytes), mode="r:gz") as archive:
        members = [member for member in archive.getmembers() if member.isfile()]
        normalized = {member.name.removeprefix("./"): member for member in members}
        for required in (
            "scenario_metadata.json",
            "trial_fingerprints.json",
            "trial_results.parquet",
            "representatives/P50.json",
        ):
            if required not in normalized:
                raise RuntimeError(f"C100_ENRICHED_MEMBER_MISSING:{scenario}:{required}")
        def read_member(name: str) -> bytes:
            stream = archive.extractfile(normalized[name])
            if stream is None:
                raise RuntimeError(f"C100_ENRICHED_MEMBER_UNREADABLE:{scenario}:{name}")
            return stream.read()
        metadata_bytes = read_member("scenario_metadata.json")
        fingerprints_bytes = read_member("trial_fingerprints.json")
        metadata = json.loads(metadata_bytes)
        fingerprints = json.loads(fingerprints_bytes)
        expected_artifact_id, expected_zip_sha = C100_ENRICHED_ARTIFACTS[scenario]
        actual_artifact_id = int(artifact.get("id", -1))
        actual_digest = str(artifact.get("digest", "")).removeprefix("sha256:")
        if actual_artifact_id != expected_artifact_id or actual_digest != expected_zip_sha:
            raise RuntimeError(f"C100_ENRICHED_ARTIFACT_PIN_MISMATCH:{scenario}")
        if (
            metadata.get("scenario") != scenario
            or metadata.get("source_sha") != SOURCE_SHA
            or str(metadata.get("run_id")) != str(STAGE7_RUN)
            or int(metadata.get("trial_count", -1)) != 1
            or int(metadata.get("daily_row_count", -1)) != 2198
            or int(metadata.get("recovery_rate_pct", -1)) != expected_recovery_rate(scenario)
            or float(metadata.get("collection_probability", -1)) != expected_collection_probability(scenario)
        ):
            raise RuntimeError(f"C100_ENRICHED_METADATA_IDENTITY_MISMATCH:{scenario}")
        fingerprint_map = fingerprints.get("fingerprints", {})
        if (
            fingerprints.get("scenario") != scenario
            or fingerprints.get("source_sha") != SOURCE_SHA
            or str(fingerprints.get("run_id")) != str(STAGE7_RUN)
            or int(fingerprints.get("trial_count", -1)) != 1
            or fingerprint_map.get("1") != expected_trial_sha256
        ):
            raise RuntimeError(f"C100_ENRICHED_TRIAL_FINGERPRINT_MISMATCH:{scenario}")
        trial_rows = pq.read_table(BytesIO(read_member("trial_results.parquet"))).to_pylist()
        if len(trial_rows) != 1:
            raise RuntimeError(f"C100_ENRICHED_TRIAL_RESULT_COUNT_MISMATCH:{scenario}")
        trial = trial_rows[0]
        for key, expected in (
            ("scenario_id", scenario),
            ("trial_id", 1),
            ("final_net_project_equity", None),
            ("final_cash", None),
            ("cumulative_project_profit", None),
            ("final_close_date", None),
        ):
            if key not in trial or (expected is not None and trial[key] != expected):
                raise RuntimeError(f"C100_ENRICHED_TRIAL_RESULT_IDENTITY_MISMATCH:{scenario}:{key}")
        if gatea.row_sha(trial) != expected_trial_sha256:
            raise RuntimeError(f"C100_ENRICHED_TRIAL_RESULT_HASH_MISMATCH:{scenario}")
        p50_stream = archive.extractfile(normalized["representatives/P50.json"])
        if p50_stream is None:
            raise RuntimeError(f"C100_ENRICHED_REPRESENTATIVE_P50_UNREADABLE:{scenario}")
        with p50_stream:
            representative_summary, daily_rows = _read_representative_summary_daily(p50_stream)
        if (
            len(daily_rows) != int(metadata["daily_row_count"])
            or len(daily_rows) != 2198
            or int(representative_summary.get("trial_id", -1)) != 1
            or representative_summary.get("scenario_id") != scenario
            or gatea.row_sha(representative_summary) != expected_trial_sha256
        ):
            raise RuntimeError(f"C100_ENRICHED_REPRESENTATIVE_P50_IDENTITY_MISMATCH:{scenario}")
        for key, expected in (
            ("collection_probability", expected_collection_probability(scenario)),
            ("recovery_rate_pct", expected_recovery_rate(scenario)),
            ("final_close_date", daily_rows[-1].get("Final_Close_Date")),
            ("final_net_project_equity", daily_rows[-1].get("Net_Equity")),
            ("final_cash", daily_rows[-1].get("Cash")),
            ("cumulative_project_profit", daily_rows[-1].get("Cumulative_Project_Profit")),
        ):
            if representative_summary.get(key) != expected:
                raise RuntimeError(
                    f"C100_ENRICHED_REPRESENTATIVE_P50_SUMMARY_MISMATCH:{scenario}:{key}"
                )
        return daily_rows, {
            "run_id": C100_ENRICHMENT_RUN,
            "run_head_sha": C100_ENRICHMENT_HEAD,
            "run_conclusion": "failure (artifact validated individually; run-level success is not claimed)",
            "artifact_id": actual_artifact_id,
            "artifact_name": artifact.get("name"),
            "artifact_api_digest": artifact.get("digest"),
            "artifact_zip_sha256": sha256_bytes(artifact_zip.read_bytes()),
            "metadata_sha256": sha256_bytes(metadata_bytes),
            "trial_fingerprints_sha256": sha256_bytes(fingerprints_bytes),
            "daily_row_count": len(daily_rows),
            "trial_id": 1,
            "trial_result_sha256": expected_trial_sha256,
            "manifest_authorized_source": True,
        }



def run_audit() -> dict[str, Any]:
    manifest = read_json("docs/stage9a/dataset_manifest.json")
    payload_inventory = read_json("docs/audits/stage9a_payload_inventory_20261020.json")
    accounting_contract = read_json("docs/stage12/accounting_data_contract.json")
    roll_forward = read_json("docs/stage12/roll_forward_validation.json")
    closure_report = read_json("docs/stage12/closure_settlement_validation.json")
    existing = {item["scenario"]: item for item in payload_inventory["artifacts"]}
    if set(existing) != set(SCENARIOS):
        raise RuntimeError("REPRESENTATIVE_INVENTORY_SCENARIO_SET_MISMATCH")
    inventory_mismatches = inventory_identity_mismatches(manifest, payload_inventory)
    inventory_mismatch_scenarios = {item["scenario"] for item in inventory_mismatches}
    if manifest.get("source_sha") != SOURCE_SHA or manifest.get("master_seed") != MASTER_SEED:
        raise RuntimeError("STAGE9A_MANIFEST_IDENTITY_MISMATCH")

    stage7_run = gatea.validate_run(STAGE7_RUN, STAGE7_HEAD, "success")
    stage10_run = gatea.validate_run(STAGE10_RUN, STAGE10_HEAD, None)
    stage12_run = gatea.validate_run(STAGE12_RUN, STAGE12_HEAD, "success")
    stage7_artifacts, _ = gatea.artifact_index(STAGE7_RUN)
    stage10_artifacts, _ = gatea.artifact_index(STAGE10_RUN)
    stage12_artifacts, _ = gatea.artifact_index(STAGE12_RUN)
    cp_f_replay_run = gatea.validate_run(
        CP_F_REPLAY_RUN, CP_F_REPLAY_HEAD, "success"
    )
    if cp_f_replay_run.get("head_branch") != CP_F_REPLAY_BRANCH:
        raise RuntimeError("CP_F_REPLAY_BRANCH_IDENTITY_MISMATCH")
    cp_f_replay_artifacts, _ = gatea.artifact_index(CP_F_REPLAY_RUN)
    c100_enrichment_run = gatea.validate_run(
        C100_ENRICHMENT_RUN, C100_ENRICHMENT_HEAD, None
    )
    c100_enrichment_artifacts, _ = gatea.artifact_index(C100_ENRICHMENT_RUN)
    stage10_jobs_response = gatea.gh_json(
        f"repos/{REPO}/actions/runs/{STAGE10_RUN}/jobs?per_page=100"
    )
    stage10_jobs = stage10_jobs_response.get("jobs", [])
    if int(stage10_jobs_response.get("total_count", -1)) != len(stage10_jobs):
        raise RuntimeError("STAGE10_JOB_LIST_INCOMPLETE")
    successful_stage10_benchmark_jobs = sum(
        1 for job in stage10_jobs
        if str(job.get("name", "")).startswith("bench-") and job.get("conclusion") == "success"
    )

    workbook_daily_fields = [
        "Closing_Cash", "Closing_Equity", "Retained_Earnings",
        "Active_Bikes", "Owned_Transferred_Bikes", "Pending_Claims",
        "Partner1_Reinvestment_Balance", "Partner2_Reinvestment_Balance",
    ]
    stage12_required_fields = set(accounting_contract.get("schema", {}).get("required_fields", []))
    stage12_contract_has = {
        field: field in stage12_required_fields for field in workbook_daily_fields
    }
    missing_from_stage12_contract = [
        field for field, present in stage12_contract_has.items() if not present
    ]

    report: dict[str, Any] = {
        "schema_version": "stage13-maxcase-source-audit-v1",
        "stage10_run_level_disposition": (
            {
                "status": "FAIL",
                "classification": "WORKFLOW_DEFECT",
                "run_conclusion": stage10_run.get("conclusion"),
                "failed_job_id": 113098100249,
                "exact_error": "SyntaxError: unterminated string literal at scripts/stage10_aggregate.py line 59",
                "disposition": "Do not call the Stage 10 run successful; validate each existing artifact and row fingerprint independently.",
            }
            if stage10_run.get("conclusion") != "success"
            else {"status": "PASS", "run_conclusion": "success"}
        ),
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "repository": REPO,
        "tested_head_sha": os.environ.get("GITHUB_SHA"),
        "tested_branch": os.environ.get("GITHUB_REF_NAME"),
        "scope": "READ_ONLY_STAGE7_STAGE10_TRIALRESULTS_AND_STAGE12_DAILY_PARQUET_EXTRACTION; NO_SIMULATION; NO_HISTORICAL_ARTIFACT_MUTATION; NO_WORKBOOK",
        "source_identity": {
            "source_sha": SOURCE_SHA,
            "master_seed": MASTER_SEED,
            "reference_sha256": REFERENCE_SHA256,
            "stage9a_manifest_git_blob": __import__("subprocess").check_output(
                ["git", "hash-object", "docs/stage9a/dataset_manifest.json"], text=True
            ).strip(),
            "stage9a_global_manifest_sha256": manifest.get("global_manifest_sha256"),
        },
        "runs": {
            "stage7": stage7_run,
            "stage10": stage10_run,
            "stage12": stage12_run,
            "cp_f_delivery_detail_replay": cp_f_replay_run,
            "stage10_successful_benchmark_job_count": successful_stage10_benchmark_jobs,
            "stage10_aggregate_job_conclusion": next(
                (job.get("conclusion") for job in stage10_jobs if job.get("name") == "aggregate-stage10"),
                None,
            ),
        },
        "representative_inventory_provenance": {
            "status": "CONFLICTED" if inventory_mismatches else "PASS_SCOPED",
            "mismatch_count": len(inventory_mismatches),
            "mismatches": inventory_mismatches,
            "reuse_allowed_only_for_identity_matched_scenarios": True,
        },
        "daily_contract": {
            "contract_version": accounting_contract.get("contract_version"),
            "schema_version": accounting_contract.get("schema", {}).get("schema_version"),
            "workbook_daily_fields_checked": stage12_contract_has,
            "fields_absent_from_stage12_contract": missing_from_stage12_contract,
        },
        "scenarios": [],
        "stage12_daily_validation": {"scenarios_validated": 0, "daily_rows_validated": 0, "trial_result_fingerprint_mismatches": 0},
        "integrity_status": "NOT_STARTED",
        "payload_status": "NOT_STARTED",
        "selected_payload_source_attempts": [],
        "historical_artifacts_modified": False,
        "historical_dataset_modified": False,
        "simulation_or_trial_executed": False,
        "workbook_built": False,
    }

    extracted_payloads: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="stage13-maxcase-source-") as tmp:
        root = Path(tmp)
        for scenario in SCENARIOS:
            is_c100 = scenario.startswith("C100_")
            run_id = STAGE7_RUN if is_c100 else STAGE10_RUN
            index = stage7_artifacts if is_c100 else stage10_artifacts
            artifact_name = (
                f"stage7-blocks-{scenario}-1" if is_c100
                else f"stage10-bench-{scenario}-1"
            )
            artifact = gatea.find_artifact(index, artifact_name, run_id)
            stage10_scenario_job = None
            if not is_c100:
                matching_jobs = [
                    job for job in stage10_jobs
                    if job.get("name") == f"bench-{scenario}-1"
                ]
                if len(matching_jobs) != 1 or matching_jobs[0].get("conclusion") != "success":
                    raise RuntimeError(
                        f"STAGE10_SCENARIO_JOB_NOT_SUCCESS: {scenario}: "
                        f"{[(job.get('name'), job.get('conclusion')) for job in matching_jobs]}"
                    )
                stage10_scenario_job = {
                    "job_id": int(matching_jobs[0]["id"]),
                    "name": matching_jobs[0]["name"],
                    "conclusion": matching_jobs[0]["conclusion"],
                }
            expected_head = STAGE7_HEAD if is_c100 else STAGE10_HEAD
            artifact_run = artifact.get("workflow_run") or {}
            if artifact_run and (
                int(artifact_run.get("id", -1)) != run_id
                or artifact_run.get("head_sha") != expected_head
            ):
                raise RuntimeError(f"ARTIFACT_RUN_HEAD_MISMATCH: {scenario}/{artifact_name}")
            zip_path = root / f"{scenario}.zip"
            download_evidence = gatea.download_artifact(artifact, zip_path)
            rows, blocks, trial_hashes = rows_from_zip(scenario, zip_path, manifest)
            selected = select_maxcase(rows)
            canonical_roles = manifest["representative_trials"][scenario]
            role_matches: list[str] = []
            inventory_identity_matches = scenario not in inventory_mismatch_scenarios
            if selected is not None and inventory_identity_matches:
                role_matches = [
                    role for role in ("P10", "P50", "P90", "Loss")
                    if int(canonical_roles[role]) == int(selected["trial_id"])
                ]
            if selected is None:
                selection_status = "UNDEFINED_BUSINESS_RULE"
                payload_reuse = False
            else:
                selection_status = "PASS"
                payload_reuse = bool(role_matches)
            stage12_name = f"stage12-daily-{scenario}"
            stage12_artifact = gatea.find_artifact(stage12_artifacts, stage12_name, STAGE12_RUN)
            stage12_artifact_run = stage12_artifact.get("workflow_run") or {}
            if (
                int(stage12_artifact_run.get("id", -1)) != STAGE12_RUN
                or stage12_artifact_run.get("head_sha") != STAGE12_HEAD
            ):
                raise RuntimeError(f"STAGE12_ARTIFACT_RUN_HEAD_MISMATCH: {scenario}/{stage12_name}")
            stage12_zip = root / f"{scenario}-stage12.zip"
            stage12_download = gatea.download_artifact(stage12_artifact, stage12_zip)
            if stage12_zip.stat().st_size != int(stage12_artifact["size_in_bytes"]):
                raise RuntimeError(f"STAGE12_ARTIFACT_SIZE_MISMATCH: {scenario}")
            parquet_path = root / f"{scenario}.parquet"
            with zipfile.ZipFile(stage12_zip, "r") as zf:
                expected_member = f"{scenario}.parquet"
                if zf.namelist() != [expected_member]:
                    raise RuntimeError(f"STAGE12_ZIP_MEMBER_MISMATCH: {scenario}: {zf.namelist()}")
                with zf.open(expected_member, "r") as source_stream, parquet_path.open("wb") as target_stream:
                    shutil.copyfileobj(source_stream, target_stream)
            trial_checks, stage12_daily_evidence = gatea.validate_stage12(
                scenario, parquet_path, roll_forward, closure_report, trial_hashes
            )
            if any(not item["exact_match"] for item in trial_checks):
                raise RuntimeError(f"STAGE12_TRIAL_RESULT_FINGERPRINT_MISMATCH: {scenario}")
            selected_check = next(
                (item for item in trial_checks if int(item["trial_id"]) == int(selected["trial_id"])),
                None,
            ) if selected is not None else None
            selected_daily_payload = None
            selected_daily_payload_source = None
            selected_daily_payload_source_rejection = None
            if selected is not None:
                if selected_check is None or not selected_check["exact_match"]:
                    raise RuntimeError(f"STAGE12_MAXCASE_TRIAL_NOT_VERIFIED: {scenario}/{selected['trial_id']}")
                daily_rows = pq.read_table(
                    parquet_path, filters=[("trial_id", "=", int(selected["trial_id"]))]
                ).to_pylist()
                daily_rows.sort(key=lambda row: row["date"])
                if len(daily_rows) != int(selected_check["daily_rows"]) or not daily_rows:
                    raise RuntimeError(f"STAGE12_MAXCASE_DAILY_ROW_COUNT_MISMATCH: {scenario}/{selected['trial_id']}")
                if daily_rows[0]["date"] != "2027-01-01" or daily_rows[-1]["date"] != selected["final_close_date"]:
                    raise RuntimeError(f"STAGE12_MAXCASE_FINAL_DATE_MISMATCH: {scenario}/{selected['trial_id']}")
                expected_hash = trial_hashes[int(selected["trial_id"])]
                if any(row.get("result_sha256") != expected_hash for row in daily_rows):
                    raise RuntimeError(f"STAGE12_MAXCASE_RESULT_SHA_MISMATCH: {scenario}/{selected['trial_id']}")
                if any(
                    row.get("scenario_id") != scenario
                    or int(row.get("trial_id", -1)) != int(selected["trial_id"])
                    or row.get("source_sha") != SOURCE_SHA
                    or int(row.get("master_seed", -1)) != MASTER_SEED
                    or row.get("Final_Close_Date") != selected.get("final_close_date")
                    for row in daily_rows
                ):
                    raise RuntimeError(f"STAGE12_MAXCASE_DAILY_IDENTITY_OR_CLOSE_DATE_MISMATCH: {scenario}/{selected['trial_id']}")
                final_daily = daily_rows[-1]
                if (
                    int(final_daily["Closing_Cash"]) != int(selected["final_cash"])
                    or int(final_daily["Closing_Equity"]) != int(selected["final_net_project_equity"])
                    or int(final_daily["Retained_Earnings"]) != int(selected["cumulative_project_profit"])
                ):
                    raise RuntimeError(f"STAGE12_MAXCASE_FINAL_VALUE_MISMATCH: {scenario}/{selected['trial_id']}")
                selected_daily_payload = [
                    {
                        "date": row["date"],
                        "Final_Close_Date": row["Final_Close_Date"],
                        "Cash": int(row["Closing_Cash"]),
                        "Net_Equity": int(row["Closing_Equity"]),
                        "Cumulative_Project_Profit": int(row["Retained_Earnings"]),
                        "Active_Bikes": int(row["Active_Bikes"]),
                        "Owned_Transferred_Bikes": int(row["Owned_Transferred_Bikes"]),
                        "Pending_Claims": int(row["Pending_Claims"]),
                        "trial_id": int(row["trial_id"]),
                        "source_sha": row["source_sha"],
                        "master_seed": int(row["master_seed"]),
                        "result_sha256": row["result_sha256"],
                    }
                    for row in daily_rows
                ]

                if is_c100:
                    expected_enriched_id, expected_enriched_sha = C100_ENRICHED_ARTIFACTS[scenario]
                    manifest_enriched_id = int(
                        manifest.get("artifact_manifest", {}).get("enriched_artifacts", {}).get(scenario, -1)
                    )
                    manifest_enrichment_run = int(
                        manifest.get("artifact_manifest", {}).get("enrichment_run_ids", {}).get(scenario, -1)
                    )
                    inventory_item = existing[scenario]
                    if (
                        manifest_enriched_id != expected_enriched_id
                        or manifest_enrichment_run != C100_ENRICHMENT_RUN
                        or int(inventory_item.get("artifact_id", -1)) != expected_enriched_id
                        or int(inventory_item.get("run_id", -1)) != C100_ENRICHMENT_RUN
                    ):
                        raise RuntimeError(f"C100_ENRICHED_MANIFEST_OR_INVENTORY_IDENTITY_MISMATCH:{scenario}")
                    enriched_artifact = gatea.find_artifact(
                        c100_enrichment_artifacts,
                        f"stage9a06-enriched-{scenario}",
                        C100_ENRICHMENT_RUN,
                    )
                    if int(enriched_artifact.get("id", -1)) != expected_enriched_id:
                        raise RuntimeError(f"C100_ENRICHED_ARTIFACT_ID_MISMATCH:{scenario}")
                    enriched_zip = root / f"{scenario}-enriched-role.zip"
                    enriched_download = gatea.download_artifact(enriched_artifact, enriched_zip)
                    if enriched_download["artifact_zip_sha256"] != expected_enriched_sha:
                        raise RuntimeError(f"C100_ENRICHED_ARTIFACT_SHA256_MISMATCH:{scenario}")
                    enriched_daily_rows, enriched_evidence = _c100_daily_rows_from_artifact(
                        scenario, enriched_artifact, enriched_zip, trial_hashes[int(selected["trial_id"])]
                    )
                    selected_daily_payload = reconcile_enriched_c100_daily_rows(
                        scenario,
                        enriched_daily_rows,
                        daily_rows,
                        trial_id=int(selected["trial_id"]),
                        expected_trial_sha256=trial_hashes[int(selected["trial_id"])],
                        source_sha=SOURCE_SHA,
                        master_seed=MASTER_SEED,
                        final_close_date=str(selected["final_close_date"]),
                        final_cash=int(selected["final_cash"]),
                        final_equity=int(selected["final_net_project_equity"]),
                        cumulative_project_profit=int(selected["cumulative_project_profit"]),
                    )
                    selected_daily_payload_source = {**enriched_evidence, **enriched_download}
                elif role_matches and inventory_identity_matches:
                    role = role_matches[0]
                    inventory_item = existing[scenario]
                    role_zip = root / f"{scenario}-stage9a-{role.lower()}-role.zip"
                    try:
                        role_artifact = gatea.find_artifact(
                            c100_enrichment_artifacts,
                            f"stage9a06-enriched-{scenario}",
                            C100_ENRICHMENT_RUN,
                        )
                        role_download = gatea.download_artifact(role_artifact, role_zip)
                        selected_daily_payload, selected_daily_payload_source = (
                            _non_c100_daily_rows_from_enriched_role_artifact(
                                scenario, role, role_artifact, role_zip,
                                trial_hashes[int(selected["trial_id"])], selected, daily_rows,
                                manifest, inventory_item,
                            )
                        )
                        selected_daily_payload_source.update(role_download)
                    except Exception as exc:
                        selected_daily_payload = _pending_maxcase_memo_rows(selected_daily_payload)
                        report.setdefault("selected_payload_source_attempts", []).append({
                            "scenario": scenario,
                            "source": "STAGE9A_EXACT_ROLE",
                            "status": "REJECTED_SOURCE_CANDIDATE",
                            "role": role,
                            "trial_id": int(selected["trial_id"]),
                            "error": str(exc),
                            "fallback_attempted": True,
                        })
                    finally:
                        role_zip.unlink(missing_ok=True)
                if not is_c100 and selected_daily_payload_source is None:
                    cp_f_zip = root / f"{scenario}-cpf-maxcase.zip"
                    cp_f_artifact = None
                    cp_f_download = {}
                    try:
                        cp_f_artifact = gatea.find_artifact(
                            cp_f_replay_artifacts, f"cp-f-replay-{scenario}", CP_F_REPLAY_RUN
                        )
                        cp_f_download = gatea.download_artifact(cp_f_artifact, cp_f_zip)
                        cp_f_maxcase_trial_id = _cpf_artifact_maxcase_trial_id(cp_f_zip, scenario)
                        if cp_f_maxcase_trial_id != int(selected["trial_id"]):
                            selected_daily_payload = _pending_maxcase_memo_rows(selected_daily_payload)
                            selected_daily_payload_source_rejection = {
                                "status": "MISSING_EVIDENCE_ROLE_IDENTITY_MISMATCH",
                                "source": "CP_F_REPLAY",
                                "artifact_id": int(cp_f_artifact["id"]),
                                "artifact_name": cp_f_artifact.get("name"),
                                "artifact_zip_sha256": cp_f_download.get("artifact_zip_sha256"),
                                "selected_trial_id": int(selected["trial_id"]),
                                "source_maxcase_trial_id": cp_f_maxcase_trial_id,
                                "reason": "CP-F artifact MaxCase is a different Trial; its daily memo balances cannot be reused for the selected Stage 13 Trial.",
                            }
                            report.setdefault("selected_payload_source_attempts", []).append({
                                "scenario": scenario,
                                "source": "CP_F_REPLAY",
                                "status": "REJECTED_SOURCE_CANDIDATE",
                                "selected_trial_id": int(selected["trial_id"]),
                                "source_maxcase_trial_id": cp_f_maxcase_trial_id,
                                "artifact_id": int(cp_f_artifact["id"]),
                            })
                        else:
                            selected_daily_payload, selected_daily_payload_source = (
                                _non_c100_daily_rows_from_cpf_artifact(
                                    scenario, cp_f_artifact, cp_f_zip,
                                    trial_hashes[int(selected["trial_id"])], selected, daily_rows,
                                )
                            )
                            selected_daily_payload_source.update(cp_f_download)
                    except Exception as exc:
                        selected_daily_payload = _pending_maxcase_memo_rows(selected_daily_payload)
                        selected_daily_payload_source_rejection = {
                            "status": "SOURCE_VALIDATION_FAILED",
                            "source": "CP_F_REPLAY",
                            "artifact_id": int(cp_f_artifact["id"]) if cp_f_artifact else None,
                            "artifact_name": cp_f_artifact.get("name") if cp_f_artifact else None,
                            "error": str(exc),
                        }
                        report.setdefault("selected_payload_source_attempts", []).append({
                            "scenario": scenario,
                            "source": "CP_F_REPLAY",
                            "status": "REJECTED_SOURCE_CANDIDATE",
                            "error": str(exc),
                        })
                    finally:
                        cp_f_zip.unlink(missing_ok=True)
                if not is_c100 and selected_daily_payload_source is None and selected_daily_payload_source_rejection is None:
                    selected_daily_payload = _pending_maxcase_memo_rows(selected_daily_payload)
                    selected_daily_payload_source_rejection = {
                        "status": "MISSING_EVIDENCE",
                        "source": "NONE",
                        "selected_trial_id": int(selected["trial_id"]),
                        "reason": "No exact selected-Trial role payload with verified partner memo balances is available.",
                    }
                extracted_payloads.append({
                    "scenario": scenario,
                    "case": "Max Case",
                    "trial_id": int(selected["trial_id"]),
                    "final_net_project_equity": int(selected["final_net_project_equity"]),
                    "final_cash": int(selected["final_cash"]),
                    "cumulative_project_profit": int(selected["cumulative_project_profit"]),
                    "partner_memo_fields_status": (
                        "VERIFIED_REUSED_SOURCE_ARTIFACT" if selected_daily_payload_source else "MISSING_EVIDENCE"
                    ),
                    "partner_memo_fields": [
                        "Partner1_Reinvestment_Balance", "Partner2_Reinvestment_Balance"
                    ],
                    "source_artifact": {
                        "run_id": STAGE12_RUN,
                        "run_head_sha": STAGE12_HEAD,
                        "artifact_id": int(stage12_artifact["id"]),
                        "artifact_name": stage12_name,
                        "artifact_size_bytes": int(stage12_artifact["size_in_bytes"]),
                        "artifact_api_digest": stage12_artifact.get("digest"),
                        **stage12_download,
                        **stage12_daily_evidence,
                    },
                    "selected_daily_payload_artifact": selected_daily_payload_source,
                    "selected_daily_payload_source_rejection": selected_daily_payload_source_rejection,
                    "daily_rows": selected_daily_payload,
                })
                report["stage12_daily_validation"]["scenarios_validated"] += 1
                report["stage12_daily_validation"]["daily_rows_validated"] += int(stage12_daily_evidence["daily_rows"])
                report["stage12_daily_validation"]["trial_result_fingerprint_mismatches"] += int(stage12_daily_evidence["mismatch_count"])
            else:
                report["stage12_daily_validation"]["scenarios_validated"] += 1
                report["stage12_daily_validation"]["daily_rows_validated"] += int(stage12_daily_evidence["daily_rows"])
            report["scenarios"].append({
                "scenario": scenario,
                "stage10_scenario_job": stage10_scenario_job,
                "source_artifact": {
                    "run_id": run_id,
                    "run_head_sha": expected_head,
                    "artifact_id": int(artifact["id"]),
                    "artifact_name": artifact_name,
                    "artifact_size_bytes": int(artifact["size_in_bytes"]),
                    "artifact_api_digest": artifact.get("digest"),
                    **download_evidence,
                },
                "trial_count": len(rows),
                "source_trial_rows_rehashed": sum(
                    int(item["trial_hashes_recomputed_from_parquet"]) for item in blocks
                ),
                "trial_result_hashes": {
                    str(trial_id): digest for trial_id, digest in sorted(trial_hashes.items())
                },
                "block_evidence": blocks,
                "stage12_daily_evidence": stage12_daily_evidence,
                "maxcase_daily_rows_extracted": len(selected_daily_payload) if selected_daily_payload is not None else 0,
                "maxcase_selection_status": selection_status,
                "maxcase_trial_id": int(selected["trial_id"]) if selected is not None else None,
                "maxcase_final_net_project_equity": (
                    selected["final_net_project_equity"] if selected is not None else None
                ),
                "maxcase_summary": selected,
                "maxcase_trial_result_sha256": (
                    trial_hashes.get(int(selected["trial_id"])) if selected is not None else None
                ),
                "existing_role_trial_ids": {
                    role: int(canonical_roles[role]) for role in ("P10", "P50", "P90", "Loss")
                },
                "representative_inventory_identity_matches_manifest": inventory_identity_matches,
                "matched_existing_roles": role_matches,
                "existing_payload_reusable_exactly": selected_daily_payload_source is not None,
                "selected_daily_payload_source_verified": selected_daily_payload_source is not None,
                "new_daily_payload_required": selected is not None and selected_daily_payload_source is None,
                "partner_memo_fields_available_in_stage12_contract": (
                    stage12_contract_has["Partner1_Reinvestment_Balance"]
                    and stage12_contract_has["Partner2_Reinvestment_Balance"]
                ),
            })

    selected = [x for x in report["scenarios"] if x["maxcase_selection_status"] == "PASS"]
    undefined = [x for x in report["scenarios"] if x["maxcase_selection_status"] != "PASS"]
    payload_reuse = [x for x in selected if x["existing_payload_reusable_exactly"]]
    payload_missing = [x for x in selected if x["new_daily_payload_required"]]
    verified_role_source_reuse = [
        x for x in extracted_payloads
        if x.get("partner_memo_fields_status") == "VERIFIED_REUSED_SOURCE_ARTIFACT"
    ]
    report["summary"] = {
        "scenario_count": len(report["scenarios"]),
        "expected_trial_rows": sum(1 if s.startswith("C100_") else 550 for s in SCENARIOS),
        "actual_trial_rows": sum(x["trial_count"] for x in report["scenarios"]),
        "trial_rows_rehashed": sum(x["source_trial_rows_rehashed"] for x in report["scenarios"]),
        "maxcase_positive_selected": len(selected),
        "undefined_business_rule_scenarios": [x["scenario"] for x in undefined],
        "maxcase_payload_can_reuse_existing_role": len(payload_reuse),
        "maxcase_payload_reused_from_verified_source_artifact": len(verified_role_source_reuse),
        "maxcase_payload_needs_new_daily_payload": len(payload_missing),
        "stage12_daily_scenarios_validated": report["stage12_daily_validation"]["scenarios_validated"],
        "stage12_daily_rows_validated": report["stage12_daily_validation"]["daily_rows_validated"],
        "maxcase_daily_rows_extracted": sum(len(x["daily_rows"]) for x in extracted_payloads),
        "c100_enriched_daily_payloads_verified": sum(
            1 for x in extracted_payloads
            if x["scenario"].startswith("C100_")
            and x.get("partner_memo_fields_status") == "VERIFIED_REUSED_SOURCE_ARTIFACT"
        ),
        "non_c100_maxcase_payloads_missing_partner_memo_source": [
            x["scenario"] for x in extracted_payloads
            if not x.get("selected_daily_payload_artifact")
        ],
        "representative_inventory_provenance_mismatch_count": len(inventory_mismatches),
        "representative_inventory_provenance_mismatch_scenarios": sorted(inventory_mismatch_scenarios),
        "new_payload_scenarios_missing_partner_memo_source": [
            x["scenario"] for x in payload_missing
            if not x["partner_memo_fields_available_in_stage12_contract"]
        ],
    }
    if (
        report["summary"]["scenario_count"] == 25
        and report["summary"]["actual_trial_rows"] == 11005
        and report["summary"]["trial_rows_rehashed"] == 11005
        and report["stage12_daily_validation"]["scenarios_validated"] == 25
        and report["stage12_daily_validation"]["daily_rows_validated"] == 22546465
        and report["stage12_daily_validation"]["trial_result_fingerprint_mismatches"] == 0
        and len(extracted_payloads) == 25
        and all(x["daily_rows"] for x in extracted_payloads)
        and all(x["source_artifact"]["artifact_zip_sha256"] == x["source_artifact"]["api_digest"].removeprefix("sha256:")
                for x in report["scenarios"])
        and all(x["source_artifact"]["artifact_zip_sha256"] == x["source_artifact"]["api_digest"].removeprefix("sha256:")
                for x in extracted_payloads)
    ):
        report["integrity_status"] = "PASS_SCOPED"
    else:
        report["integrity_status"] = "FAIL"
    if undefined:
        report["payload_status"] = "UNDEFINED_BUSINESS_RULE"
    elif (
        payload_missing
        or inventory_mismatches
        or any(
            x.get("partner_memo_fields_status") != "VERIFIED_REUSED_SOURCE_ARTIFACT"
            for x in extracted_payloads
        )
    ):
        report["payload_status"] = "MISSING_EVIDENCE"
    else:
        report["payload_status"] = "EXISTING_PAYLOADS_REUSABLE"
    daily_payload_document = {
        "schema_version": "stage13-maxcase-daily-payloads-v1",
        "created_at_utc": report["created_at_utc"],
        "repository": REPO,
        "tested_head_sha": report["tested_head_sha"],
        "scope": "READ_ONLY_EXTRACTION_FROM_VERIFIED_STAGE12_PARQUET; NO_SIMULATION; NO_HISTORICAL_MUTATION; NOT_A_FINAL_WORKBOOK",
        "source_identity": report["source_identity"],
        "stage12_run": stage12_run,
        "stage12_global_sha256": roll_forward.get("expected_global_sha256_from_cp12b"),
        "scenario_count": len(extracted_payloads),
        "maxcase_daily_rows": sum(len(x["daily_rows"]) for x in extracted_payloads),
        "missing_fields": (
            []
            if all(x.get("partner_memo_fields_status") == "VERIFIED_REUSED_SOURCE_ARTIFACT" for x in extracted_payloads)
            else ["Partner1_Reinvestment_Balance", "Partner2_Reinvestment_Balance"]
        ),
        "missing_fields_status": (
            "ALL_SCENARIOS_VERIFIED_REUSED_SOURCE_ARTIFACTS"
            if all(x.get("partner_memo_fields_status") == "VERIFIED_REUSED_SOURCE_ARTIFACT" for x in extracted_payloads)
            else "PARTIALLY_AVAILABLE_AND_PARTIALLY_MISSING"
        ),
        "scenarios_with_verified_partner_memo_fields": [
            x["scenario"] for x in extracted_payloads
            if x.get("partner_memo_fields_status") == "VERIFIED_REUSED_SOURCE_ARTIFACT"
        ],
        "scenarios": extracted_payloads,
    }
    Path("stage13_maxcase_daily_payloads.json").write_text(
        json.dumps(daily_payload_document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    out_path = Path("stage13_maxcase_source_audit.json")
    try:
        report = run_audit()
        out_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({
            "integrity_status": report["integrity_status"],
            "payload_status": report["payload_status"],
            "summary": report.get("summary"),
            "output": str(out_path),
        }, ensure_ascii=False, sort_keys=True))
        if report["integrity_status"] != "PASS_SCOPED":
            raise SystemExit(1)
    except Exception as exc:
        failure = {
            "integrity_status": "FAIL",
            "payload_status": "MISSING_EVIDENCE",
            "error": str(exc),
            "traceback": traceback.format_exc()[-8000:],
            "tested_head_sha": os.environ.get("GITHUB_SHA"),
            "tested_branch": os.environ.get("GITHUB_REF_NAME"),
            "simulation_or_trial_executed": False,
            "historical_artifacts_modified": False,
        }
        out_path.write_text(
            json.dumps(failure, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(failure, ensure_ascii=False, sort_keys=True))
        raise


if __name__ == "__main__":
    main()
