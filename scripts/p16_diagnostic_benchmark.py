from __future__ import annotations
import copy, hashlib, io, json, os, re, shutil, sys, tarfile, time, zipfile
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from openpyxl import Workbook, load_workbook
from scripts import excel_builder_p16 as builder
from scripts import p16_produce_deliverables_v4 as producer
from scripts.stage13_assemble import audit_saved_workbook, validate_representative_payload

BASE_SHA = "30ba2d5d47d3a3d6c117f0ef667115401c337ad7"
SCENARIOS = ("C100_G100", "C030_G030")
ROLE_FILES = {"P10": "P10.json", "P50": "P50.json", "P90": "P90.json", "LossCase": "Loss.json"}
ROLE_LABELS = {"P10": "P10", "P50": "P50", "P90": "P90", "LossCase": "Loss", "MaxCase": "MaxCase"}
ROOT = Path.cwd()
WORK = ROOT / "p16_diag_work"
OUT = ROOT / "diagnostics"
TOKEN = os.environ.get("GITHUB_TOKEN")
T0 = time.monotonic()
REPORT = {
    "schema_version": "1.0", "status": "RUNNING",
    "workflow_head_sha": os.environ.get("GITHUB_SHA"),
    "base_code_sha": BASE_SHA, "branch": os.environ.get("GITHUB_REF_NAME"),
    "run_id": os.environ.get("GITHUB_RUN_ID"), "timeout_minutes": 20,
    "scenario_order": list(SCENARIOS),
    "no_simulation_or_trial_generation": True,
    "no_source_or_repository_parquet_modification": True,
    "identity": {}, "scenarios": {}, "shared_stages": {}, "acceptance": {}
}
OUT.mkdir(parents=True, exist_ok=True)
WORK.mkdir(parents=True, exist_ok=True)

def emit(event, **fields):
    print("[P16_DIAG] " + json.dumps({
        "event": event, "at_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_monotonic_seconds": round(time.monotonic() - T0, 6), **fields
    }, ensure_ascii=False, sort_keys=True, default=str), flush=True)

def persist():
    temp = OUT / "diagnostic_report.json.tmp"
    temp.write_text(json.dumps(REPORT, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    os.replace(temp, OUT / "diagnostic_report.json")

def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def git_blob_sha(path):
    raw = Path(path).read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()

def shape_profile(value):
    tokens = []
    list_shapes = Counter()
    object_shapes = Counter()
    scalar_shapes = Counter()
    def visit(node, path="$"):
        if isinstance(node, dict):
            keys = list(node.keys())
            tokens.append(["object", path, keys])
            object_shapes[(path, tuple(keys))] += 1
            for key, child in node.items():
                visit(child, path + "." + str(key))
        elif isinstance(node, list):
            tokens.append(["list", path, len(node)])
            list_shapes[(path, len(node))] += 1
            for child in node:
                visit(child, path + "[]")
        else:
            if node is None: typ, width = "null", 0
            elif isinstance(node, bool): typ, width = "bool", 0
            elif isinstance(node, int): typ, width = "int", 0
            elif isinstance(node, float): typ, width = "float", 0
            elif isinstance(node, datetime): typ, width = "datetime", 0
            elif isinstance(node, date): typ, width = "date", 0
            elif isinstance(node, str): typ, width = "str", len(node)
            else: typ, width = type(node).__name__, 0
            tokens.append(["scalar", path, typ, width])
            scalar_shapes[(path, typ, width)] += 1
    visit(value)
    encoded = json.dumps(tokens, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return {
        "shape_sha256": hashlib.sha256(encoded).hexdigest(),
        "list_lengths": {f"{k[0]}|length={k[1]}": v for k, v in sorted(list_shapes.items(), key=lambda x: repr(x[0]))},
        "object_key_shapes": {f"{k[0]}|keys={json.dumps(k[1], ensure_ascii=False)}": v for k, v in sorted(object_shapes.items(), key=lambda x: repr(x[0]))},
        "scalar_type_width_counts": {f"{k[0]}|{k[1]}|width={k[2]}": v for k, v in sorted(scalar_shapes.items(), key=lambda x: repr(x[0]))}
    }

def synthetic_value(value, key=None, date_map=None):
    if isinstance(value, dict):
        return {k: synthetic_value(v, k, date_map) for k, v in value.items()}
    if isinstance(value, list):
        return [synthetic_value(v, key, date_map) for v in value]
    if key in {"trial_id", "scenario_id", "scenario", "quantile_name", "collection_probability", "recovery_rate_pct"}:
        return value
    if isinstance(value, bool): return False
    if isinstance(value, int): return 0
    if isinstance(value, float): return 0.0
    if isinstance(value, datetime):
        if date_map and value in date_map: return date_map[value]
        return datetime(2000, 1, 1, tzinfo=value.tzinfo)
    if isinstance(value, date):
        if date_map and value in date_map: return date_map[value]
        return date(2000, 1, 1)
    if isinstance(value, str):
        if date_map and value in date_map: return date_map[value]
        if re.match(r"^\d{4}-\d{2}-\d{2}", value) and len(value) >= 10:
            return "2000-01-01" + value[10:]
        return "X" * len(value)
    return value

def synthetic_daily_distribution(path):
    source_file_sha256_before_syntheticization = file_sha(path)
    source = pq.read_table(path)
    original_rows = source.to_pylist()
    unique = []
    if original_rows and "date" in original_rows[0]:
        for row in original_rows:
            value = row["date"]
            if value not in unique: unique.append(value)
        unique.sort(key=str)
    mapped = {}
    for index, value in enumerate(unique):
        dt = date(2000, 1, 1) + timedelta(days=index)
        if isinstance(value, datetime):
            mapped[value] = datetime(2000, 1, 1, tzinfo=value.tzinfo) + timedelta(days=index)
        elif isinstance(value, date):
            mapped[value] = dt
        elif isinstance(value, str) and re.match(r"^\d{4}-\d{2}-\d{2}", value) and len(value) >= 10:
            mapped[value] = dt.isoformat() + value[10:]
        else:
            mapped[value] = value
    rows = [synthetic_value(row, date_map=mapped) for row in original_rows]
    synthetic_table = pa.Table.from_pylist(rows, schema=source.schema)
    if synthetic_table.num_rows != source.num_rows or not synthetic_table.schema.equals(source.schema, check_metadata=True):
        raise RuntimeError("DAILY_DISTRIBUTION_SYNTHETIC_SCHEMA_OR_ROW_MISMATCH")
    pq.write_table(synthetic_table, path, compression="snappy")
    back = pq.read_table(path)
    if back.num_rows != source.num_rows or not back.schema.equals(source.schema, check_metadata=True):
        raise RuntimeError("DAILY_DISTRIBUTION_SYNTHETIC_READBACK_MISMATCH")
    if original_rows and "quantile_name" in original_rows[0]:
        count_rows = len(unique)
    else:
        count_rows = len(original_rows)
    return {
        "source_rows": source.num_rows, "synthetic_rows": back.num_rows,
        "source_columns": source.schema.names, "synthetic_columns": back.schema.names,
        "column_count": len(source.schema.names),
        "schema_equal": back.schema.equals(source.schema, check_metadata=True),
        "row_count_equal": back.num_rows == source.num_rows,
        "unique_dates_source": len(unique), "expected_sheet_rows_including_header": count_rows + 1,
        "source_file_sha256_before_syntheticization": source_file_sha256_before_syntheticization,
        "synthetic_file_sha256": file_sha(path)
    }

def extract_artifact(artifact_zip, scenario, scenario_dir):
    scenario_dir.mkdir(parents=True, exist_ok=True)
    reps = scenario_dir / "representatives"
    reps.mkdir(parents=True, exist_ok=True)
    required = {
        "scenario_metadata.json": scenario_dir / "scenario_metadata.json",
        "trial_results.parquet": scenario_dir / "trial_results.parquet",
        "daily_distribution.parquet": scenario_dir / "daily_distribution.parquet",
        "trial_fingerprints.json": scenario_dir / "trial_fingerprints.json",
        "representatives/P10.json": reps / "P10.json",
        "representatives/P50.json": reps / "P50.json",
        "representatives/P90.json": reps / "P90.json",
        "representatives/Loss.json": reps / "Loss.json"
    }
    counts, sizes = Counter(), {}
    with zipfile.ZipFile(io.BytesIO(artifact_zip), "r") as outer:
        names = [n for n in outer.namelist() if n.endswith(".tar.gz") and not n.endswith("/")]
        if len(names) != 1: raise RuntimeError(f"OUTER_TAR_MEMBER_NOT_UNIQUE:{scenario}:{names}")
        with outer.open(names[0]) as src, (scenario_dir / f"{scenario}.tar.gz").open("wb") as dst:
            shutil.copyfileobj(src, dst, 1024 * 1024)
    with tarfile.open(scenario_dir / f"{scenario}.tar.gz", mode="r|gz") as archive:
        for member in archive:
            if not member.isfile(): continue
            name = member.name.replace("\\", "/").lstrip("./")
            key = next((k for k in required if name.endswith(k)), None)
            if key is None: continue
            counts[key] += 1
            if counts[key] != 1: raise RuntimeError(f"ARTIFACT_MEMBER_DUPLICATE:{scenario}:{key}")
            src = archive.extractfile(member)
            if src is None: raise RuntimeError(f"ARTIFACT_MEMBER_UNREADABLE:{scenario}:{key}")
            with src, required[key].open("wb") as dst: shutil.copyfileobj(src, dst, 1024 * 1024)
            sizes[key] = required[key].stat().st_size
    missing = [k for k in required if counts[k] != 1]
    if missing: raise RuntimeError(f"ARTIFACT_REQUIRED_MEMBERS_MISSING:{scenario}:{missing}")
    return {"member_count": dict(counts), "member_bytes": sizes, "tar_gz_bytes": (scenario_dir / f"{scenario}.tar.gz").stat().st_size}

def load_scenario(scenario, manifest):
    result = {
        "scenario": scenario,
        "phase_timings_seconds": {},
        "phase_exit_codes": {"metadata": None, "download": None, "decompress": None, "read": None, "write": None, "save": None, "readback": None},
        "identity": {}, "shape_equivalence": {}, "worksheet_dimensions": {}, "workbook": {}
    }
    started = time.monotonic()
    scenario_dir = WORK / scenario
    artifact_id = int(manifest["artifact_manifest"]["enriched_artifacts"][scenario])
    expected_run_id = int(manifest["artifact_manifest"]["enrichment_run_ids"][scenario])
    t = time.monotonic()
    meta = producer.api_json(f"https://api.github.com/repos/{producer.REPO}/actions/artifacts/{artifact_id}", TOKEN)
    if meta.get("id") != artifact_id or meta.get("expired") is True: raise RuntimeError(f"ARTIFACT_ID_OR_EXPIRY_FAIL:{scenario}")
    wr = meta.get("workflow_run") or {}
    if wr.get("id") != expected_run_id: raise RuntimeError(f"ARTIFACT_PRODUCER_RUN_MISMATCH:{scenario}:{wr.get('id')}")
    if not isinstance(wr.get("head_sha"), str) or len(wr["head_sha"]) != 40: raise RuntimeError(f"ARTIFACT_PRODUCER_SHA_MISSING:{scenario}")
    result["phase_timings_seconds"]["metadata"] = round(time.monotonic() - t, 6)
    result["phase_exit_codes"]["metadata"] = 0

    t = time.monotonic()
    raw_zip = producer.download_artifact_zip(artifact_id, TOKEN)
    zip_sha = hashlib.sha256(raw_zip).hexdigest()
    if len(raw_zip) != meta.get("size_in_bytes"): raise RuntimeError(f"ARTIFACT_BYTE_SIZE_MISMATCH:{scenario}")
    if meta.get("digest") and meta["digest"] != "sha256:" + zip_sha: raise RuntimeError(f"ARTIFACT_DIGEST_MISMATCH:{scenario}")
    result["phase_timings_seconds"]["download"] = round(time.monotonic() - t, 6)
    result["phase_exit_codes"]["download"] = 0

    t = time.monotonic()
    unpack = extract_artifact(raw_zip, scenario, scenario_dir)
    result["phase_timings_seconds"]["decompress"] = round(time.monotonic() - t, 6)
    result["phase_exit_codes"]["decompress"] = 0
    del raw_zip

    t = time.monotonic()
    metadata_path = scenario_dir / "scenario_metadata.json"
    scenario_meta = producer._normalise_scenario_meta(metadata_path.read_bytes())
    if scenario_meta.get("scenario") != scenario or scenario_meta.get("source_sha") != producer.SOURCE_SHA:
        raise RuntimeError(f"SCENARIO_SOURCE_IDENTITY_MISMATCH:{scenario}")
    if str(scenario_meta.get("run_id", "")) != str(manifest.get("run_id")): raise RuntimeError(f"OFFICIAL_RUN_ID_MISMATCH:{scenario}")
    if scenario_meta.get("global_manifest_sha256") not in (None, manifest.get("global_manifest_sha256")): raise RuntimeError(f"GLOBAL_MANIFEST_HASH_MISMATCH:{scenario}")
    if scenario_meta.get("reference_sha256") not in (None, producer.REFERENCE_SHA256): raise RuntimeError(f"REFERENCE_HASH_MISMATCH:{scenario}")

    trial_path = scenario_dir / "trial_results.parquet"
    table = pq.read_table(trial_path)
    trial_rows = table.to_pylist()
    expected_count = int(manifest["representative_trials"][scenario]["trial_count"])
    if len(trial_rows) != expected_count or int(scenario_meta.get("trial_count", -1)) != expected_count:
        raise RuntimeError(f"TRIAL_ROW_COUNT_MISMATCH:{scenario}:{len(trial_rows)}:{expected_count}")
    ids = [r.get("trial_id") for r in trial_rows]
    if any(type(x) is not int for x in ids) or sorted(ids) != list(range(1, expected_count + 1)):
        raise RuntimeError(f"TRIAL_ID_COVERAGE_FAIL:{scenario}")
    source_trial_profile = shape_profile(trial_rows)
    synthetic_rows = synthetic_value(copy.deepcopy(trial_rows))
    synthetic_trial_profile = shape_profile(synthetic_rows)
    trial_shape_equal = source_trial_profile == synthetic_trial_profile
    if not trial_shape_equal: raise RuntimeError(f"SYNTHETIC_TRIAL_SHAPE_MISMATCH:{scenario}")

    daily_path = scenario_dir / "daily_distribution.parquet"
    daily_info = synthetic_daily_distribution(daily_path)

    expected_ids = manifest["representative_trials"][scenario]
    maxcase = producer.select_maxcase_row(trial_rows)
    assignments = {
        "P10": int(expected_ids["P10"]), "P50": int(expected_ids["P50"]),
        "P90": int(expected_ids["P90"]), "LossCase": int(expected_ids["Loss"]),
        "MaxCase": int(maxcase["trial_id"])
    }
    reps = {}
    role_profiles = {}
    for role, fname in ROLE_FILES.items():
        p = scenario_dir / "representatives" / fname
        source_payload = json.loads(p.read_text(encoding="utf-8"))
        syn_payload = synthetic_value(copy.deepcopy(source_payload))
        s_profile, y_profile = shape_profile(source_payload), shape_profile(syn_payload)
        same = s_profile == y_profile
        if not same: raise RuntimeError(f"SYNTHETIC_REPRESENTATIVE_SHAPE_MISMATCH:{scenario}:{role}")
        validate_representative_payload(scenario, role, assignments[role], syn_payload)
        reps[role] = syn_payload
        role_profiles[role] = {
            "structure_equal": same, "source_shape_sha256": s_profile["shape_sha256"],
            "synthetic_shape_sha256": y_profile["shape_sha256"],
            "summary_keys": list(source_payload.get("summary", {}).keys()),
            "summary_columns": len(source_payload.get("summary", {})),
            "daily_keys": list(source_payload.get("daily", [{}])[0].keys()) if source_payload.get("daily") else [],
            "daily_columns": len(source_payload.get("daily", [{}])[0]) if source_payload.get("daily") else 0,
            "source_daily_rows": len(source_payload.get("daily", [])),
            "synthetic_daily_rows": len(syn_payload.get("daily", []))
        }
    result["phase_timings_seconds"]["read"] = round(time.monotonic() - t, 6)
    result["phase_exit_codes"]["read"] = 0
    result["identity"] = {
        "artifact_id": artifact_id, "artifact_producer_run_id": expected_run_id,
        "artifact_producer_head_sha": wr["head_sha"], "artifact_bytes": int(meta["size_in_bytes"]),
        "artifact_sha256": zip_sha, "artifact_members": unpack,
        "scenario": scenario, "source_sha": scenario_meta.get("source_sha"),
        "reference_sha256": scenario_meta.get("reference_sha256"),
        "global_manifest_sha256": scenario_meta.get("global_manifest_sha256"),
        "trial_count": len(trial_rows), "trial_columns": table.schema.names,
        "trial_column_count": len(table.schema.names),
        "trial_parquet_sha256_original_download_copy": file_sha(trial_path),
        "daily_distribution": daily_info, "representative_assignments": assignments,
        "source_maxcase_trial_id": int(maxcase["trial_id"]),
        "trial_shape_sha256_source": source_trial_profile["shape_sha256"],
        "trial_shape_sha256_synthetic": synthetic_trial_profile["shape_sha256"],
    }
    result["shape_equivalence"] = {
        "trial_rows_and_columns_equal": trial_shape_equal,
        "daily_distribution_row_count_and_schema_equal": daily_info["row_count_equal"] and daily_info["schema_equal"],
        "representative_payloads_all_equal": all(r["structure_equal"] for r in role_profiles.values()),
        "representative_payloads": role_profiles,
    }
    result["_trial_rows"] = synthetic_rows
    result["_reps"] = reps
    result["_daily_info"] = daily_info
    result["_scenario_dir"] = str(scenario_dir)
    result["_payload"] = reps["P50"]
    result["_started_monotonic"] = started
    emit("scenario_read_complete", scenario=scenario, phases=result["phase_timings_seconds"],
         trial_rows=len(trial_rows), trial_columns=len(table.schema.names),
         representative_shapes={k: {"daily_rows": v["source_daily_rows"], "daily_columns": v["daily_columns"], "equal": v["structure_equal"]} for k,v in role_profiles.items()},
         daily_shape={"rows": daily_info["source_rows"], "columns": daily_info["column_count"], "schema_equal": daily_info["schema_equal"]})
    return result

def expected_acctg_dim(payload):
    daily = payload.get("daily", [])
    maxrow, maxcol = len(daily) + 1, 11
    accounting = payload["accounting"]
    start = maxrow + 3
    balance = accounting.get("daily_balance_checks", [])
    if balance:
        maxrow = max(maxrow, start)
        maxrow = max(maxrow, start + 1 + len(balance))
        maxcol = max(maxcol, len(balance[0]))
        start = maxrow + 3
    for key in ("cash_rollforward", "ar_rollforward", "asset_rollforward", "equity_rollforward"):
        maxrow = max(maxrow, start)
        rows = accounting.get(key, [])
        if rows:
            maxrow = max(maxrow, start + 1 + len(rows))
            maxcol = max(maxcol, len(rows[0]))
            start = maxrow + 3
    return (maxrow, maxcol)

def expected_scenario_dims(scenario, item):
    p50 = item["_payload"]
    rows = item["_trial_rows"]
    reps = item["_reps"]
    stats_rows = 1 + len(builder.numeric_metrics(rows)) + 1
    daily = p50.get("daily", [])
    assets = p50.get("final_inventory", [])
    partner = p50.get("partner_memo", [])
    guarantee = p50.get("guarantee_claims", [])
    contracts = p50.get("contracts", [])
    def generic_dim(data):
        if not data: return (2, 1)
        if isinstance(data[0], dict): return (1 + len(data), len(data[0]))
        return (1, 1)
    return {
        f"{scenario}_STATS": (stats_rows, 13),
        f"{scenario}_DAILY": (1 + len(daily), len(daily[0]) if daily else 1),
        f"{scenario}_ASSETS": (1 + len(assets), 10),
        f"{scenario}_ACCTG": expected_acctg_dim(p50),
        f"{scenario}_PARTNER": (1 + len(partner) + 4, max(3, len(partner[0]) if partner else 0)),
        f"{scenario}_GUARANTEE": generic_dim(guarantee),
        f"{scenario}_CONTRACTS": generic_dim(contracts),
    }

def main():
    if not TOKEN: raise RuntimeError("GITHUB_TOKEN_UNAVAILABLE")
    manifest_path = ROOT / "docs/stage9a/dataset_manifest.json"
    if git_blob_sha(manifest_path) != producer.MAIN_MANIFEST_BLOB: raise RuntimeError("PINNED_MANIFEST_BLOB_MISMATCH")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("source_sha") != producer.SOURCE_SHA or manifest.get("reference_sha256") != producer.REFERENCE_SHA256:
        raise RuntimeError("PINNED_SOURCE_OR_REFERENCE_MISMATCH")
    if manifest.get("global_manifest_sha256") != "892da438955160bb59aff3046271402f57bdd61a4abb35f41db7188f61346ff6":
        raise RuntimeError("PINNED_GLOBAL_MANIFEST_MISMATCH")
    run_meta = producer.api_json(f"https://api.github.com/repos/{producer.REPO}/actions/runs/{os.environ['GITHUB_RUN_ID']}", TOKEN)
    created = run_meta.get("created_at")
    started = run_meta.get("run_started_at")
    queue_seconds = None
    if created and started:
        from datetime import datetime as dt
        queue_seconds = round((dt.fromisoformat(started.replace("Z", "+00:00")) - dt.fromisoformat(created.replace("Z", "+00:00"))).total_seconds(), 3)
    REPORT["identity"] = {
        "base_code_sha": BASE_SHA,
        "manifest_git_blob_sha": git_blob_sha(manifest_path),
        "global_manifest_sha256": manifest["global_manifest_sha256"],
        "source_sha": manifest["source_sha"],
        "reference_sha256": manifest["reference_sha256"],
        "official_source_run_id": manifest["run_id"],
        "run_created_at_utc": created, "run_started_at_utc": started,
        "queue_wait_seconds_api_timestamps": queue_seconds,
        "runner_execution_elapsed_monotonic_seconds_at_start": round(time.monotonic() - T0, 6),
    }
    persist()
    items = {}
    for scenario in SCENARIOS:
        emit("scenario_start", scenario=scenario)
        item = load_scenario(scenario, manifest)
        items[scenario] = item
        REPORT["scenarios"][scenario] = {k:v for k,v in item.items() if not k.startswith("_")}
        persist()

    builder.EXPECTED_SCENARIOS = list(SCENARIOS)
    builder._P16_TRIAL_ROWS_BY_SCENARIO = {s: items[s]["_trial_rows"] for s in SCENARIOS}
    wb = Workbook()
    wb.remove(wb.active)
    write_sheet_seconds = {}
    for scenario in SCENARIOS:
        t = time.monotonic()
        builder.write_stats_sheet(wb, scenario, items[scenario]["_trial_rows"], int(manifest["total_capital"]))
        builder.write_scenario_detail(wb, scenario, items[scenario]["_payload"])
        write_sheet_seconds[scenario] = time.monotonic() - t
        emit("scenario_detail_write_complete", scenario=scenario, seconds=round(write_sheet_seconds[scenario], 6))

    reps_for_writer = {s: items[s]["_reps"] for s in SCENARIOS}
    assignments = {s: items[s]["identity"]["representative_assignments"] for s in SCENARIOS}
    original_log = builder._p16_log
    rep_events = []
    def capture_log(event, **fields):
        rec = {"event": event, **fields}
        rep_events.append(rec)
        original_log(event, **fields)
    builder._p16_log = capture_log
    t = time.monotonic()
    builder.write_representatives(
        wb,
        {"_dataset_root": str(WORK)},
        reps_for_writer, assignments, ROLE_LABELS
    )
    rep_write_seconds = time.monotonic() - t
    builder._p16_log = original_log
    scenario_rep_seconds = {
        x["scenario"]: float(x["elapsed_seconds"])
        for x in rep_events if x.get("event") == "representative_scenario_complete"
    }
    missing_rep_events = [s for s in SCENARIOS if s not in scenario_rep_seconds]
    if missing_rep_events: raise RuntimeError(f"REPRESENTATIVE_SCENARIO_TIMING_MISSING:{missing_rep_events}")

    t = time.monotonic()
    builder.write_daily_distribution(wb, WORK)
    daily_write_seconds = time.monotonic() - t
    expected_dims = {}
    for scenario in SCENARIOS:
        expected_dims.update(expected_scenario_dims(scenario, items[scenario]))
    rep_headers = [
        "scenario","case","record_type","trial_id","date","final_close_date","Cash","Net_Equity",
        "Active_Bikes","Owned_Transferred_Bikes","Pending_Claims","Partner1_Reinvestment_Balance",
        "Partner2_Reinvestment_Balance","final_net_project_equity","final_cash","cumulative_project_profit",
        "termination_count","secondary_cycle_count","owned_bikes","held_assets","total_operating_revenue",
        "bad_debt","guarantee_recovered","payload_source"
    ]
    rep_data_rows = sum(1 + sum(1 + len(items[s]["_reps"][r]["daily"]) for r in ("P10","P50","P90","LossCase")) for s in SCENARIOS)
    expected_dims["REPRESENTATIVE_CASES"] = (1 + rep_data_rows, len(rep_headers))
    expected_distribution_rows = 1 + sum(items[s]["_daily_info"]["expected_sheet_rows_including_header"] - 1 for s in SCENARIOS)
    expected_dims["DAILY_DISTRIBUTION"] = (expected_distribution_rows, 28)
    expected_order = []
    for s in SCENARIOS:
        expected_order.extend([f"{s}_STATS", f"{s}_DAILY", f"{s}_ASSETS", f"{s}_ACCTG", f"{s}_PARTNER", f"{s}_GUARANTEE", f"{s}_CONTRACTS"])
    expected_order.extend(["REPRESENTATIVE_CASES", "DAILY_DISTRIBUTION"])
    actual_dims = {ws.title: (ws.max_row, ws.max_column) for ws in wb.worksheets}
    dims_equal = actual_dims == expected_dims
    if not dims_equal:
        REPORT["acceptance"]["dimension_mismatch"] = {"expected": expected_dims, "actual": actual_dims}
        persist()
        raise RuntimeError("SYNTHETIC_WORKSHEET_DIMENSIONS_NOT_EQUIVALENT")
    if wb.sheetnames != expected_order:
        raise RuntimeError("SYNTHETIC_WORKBOOK_ORDER_MISMATCH")
    total_cells_expected = sum(r*c for r,c in expected_dims.values())
    total_cells_actual = sum(ws.max_row * ws.max_column for ws in wb.worksheets)
    if total_cells_expected != total_cells_actual: raise RuntimeError("CELL_GRID_WRITE_VOLUME_MISMATCH")
    allocated_cells = {ws.title: len(ws._cells) for ws in wb.worksheets}
    value_cells = {ws.title: sum(1 for c in ws._cells.values() if c.value is not None) for ws in wb.worksheets}
    t = time.monotonic()
    workbook_path = OUT / "p16-two-scenario-synthetic-benchmark.xlsx"
    wb.save(workbook_path)
    wb.close()
    save_seconds = time.monotonic() - t
    t = time.monotonic()
    audit = audit_saved_workbook(workbook_path, expected_order)
    readwb = load_workbook(workbook_path, read_only=True, data_only=False)
    try:
        ws = readwb["REPRESENTATIVE_CASES"]
        headers = next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
        case_col = headers.index("case"); record_col = headers.index("record_type")
        pending_rows = sum(1 for row in ws.iter_rows(min_row=2, values_only=True) if row[case_col] == "MaxCase" and row[record_col] == "PENDING_DATA_SOURCE")
        pending_cells = sum(1 for row in ws.iter_rows(min_row=2, values_only=True) for value in row if value == "PENDING_DATA_SOURCE")
        readback_order = list(readwb.sheetnames)
    finally:
        readwb.close()
    readback_seconds = time.monotonic() - t
    if audit.get("sheet_count") != 17 or audit.get("sheet_names_exact") is not True or readback_order != expected_order:
        raise RuntimeError(f"SYNTHETIC_WORKBOOK_READBACK_SHEET_AUDIT_FAIL:{audit}")
    if audit.get("formula_cells") or audit.get("error_cells"): raise RuntimeError(f"SYNTHETIC_WORKBOOK_FORMULAS_OR_ERRORS:{audit}")
    expected_pending = len(SCENARIOS)
    if pending_rows != expected_pending: raise RuntimeError(f"ACTUAL_PENDING_ROW_COUNT_MISMATCH:{pending_rows}:{expected_pending}")

    all_shapes_equal = all(
        items[s]["shape_equivalence"]["trial_rows_and_columns_equal"]
        and items[s]["shape_equivalence"]["daily_distribution_row_count_and_schema_equal"]
        and items[s]["shape_equivalence"]["representative_payloads_all_equal"]
        for s in SCENARIOS
    )
    scenario_write = {}
    for s in SCENARIOS:
        scenario_write[s] = round(write_sheet_seconds[s] + scenario_rep_seconds[s], 6)
        items[s]["phase_timings_seconds"]["write"] = scenario_write[s]
        items[s]["phase_exit_codes"]["write"] = 0
        items[s]["phase_timings_seconds"]["save_shared_workbook"] = round(save_seconds, 6)
        items[s]["phase_exit_codes"]["save"] = 0
        items[s]["phase_timings_seconds"]["readback_shared_workbook"] = round(readback_seconds, 6)
        items[s]["phase_exit_codes"]["readback"] = 0
        items[s]["total_execution_seconds_including_shared_save"] = round(
            sum(items[s]["phase_timings_seconds"].get(p, 0) or 0 for p in ("metadata","download","decompress","read"))
            + scenario_write[s] + save_seconds + readback_seconds, 6
        )
        items[s]["shape_equivalence"]["worksheets_dimensions_equal"] = dims_equal
        items[s]["shape_equivalence"]["exact_writer_work_volume_equal"] = total_cells_actual == total_cells_expected
        REPORT["scenarios"][s] = {k:v for k,v in items[s].items() if not k.startswith("_")}

    total_elapsed = time.monotonic() - T0
    workbook_data = {
        "path": str(workbook_path.relative_to(ROOT)),
        "bytes": workbook_path.stat().st_size, "sha256": file_sha(workbook_path),
        "sheet_count": audit["sheet_count"], "sheet_names": readback_order,
        "formula_cells": audit.get("formula_cells"), "excel_error_cells": audit.get("error_cells"),
        "pending_maxcase_rows_observed": pending_rows, "pending_data_source_cells_observed": pending_cells,
        "worksheet_dimensions_expected": {k:list(v) for k,v in expected_dims.items()},
        "worksheet_dimensions_readback": {k:[actual_dims[k][0],actual_dims[k][1]] for k in expected_order},
        "worksheet_dimensions_equal": dims_equal,
        "total_cell_grid_volume_expected": total_cells_expected,
        "total_cell_grid_volume_actual": total_cells_actual,
        "allocated_cells_by_sheet": allocated_cells, "nonempty_value_cells_by_sheet": value_cells,
        "representative_case_rows_written": rep_data_rows,
        "representative_case_columns_written_per_row": len(rep_headers),
        "representative_row_cell_write_volume": rep_data_rows * len(rep_headers),
        "audit": audit,
    }
    REPORT["workbook"] = workbook_data
    REPORT["shared_stages"] = {
        "representative_cases_writer_seconds_total": round(rep_write_seconds, 6),
        "representative_cases_scenario_loop_seconds": {s: round(scenario_rep_seconds[s], 6) for s in SCENARIOS},
        "daily_distribution_writer_seconds_for_both_scenarios": round(daily_write_seconds, 6),
        "save_seconds_shared_two_scenario_workbook": round(save_seconds, 6),
        "readback_seconds_shared_two_scenario_workbook": round(readback_seconds, 6),
        "workbook_shape_and_write_volume_exactly_equal": dims_equal and total_cells_actual == total_cells_expected,
    }
    REPORT["acceptance"] = {
        "two_scenarios_completed": all(s in REPORT["scenarios"] for s in SCENARIOS),
        "source_identity_pass": True,
        "synthetic_structure_matches_source": all_shapes_equal,
        "sheet_names_order_and_dimensions_exact": dims_equal and wb.sheetnames == expected_order,
        "workbook_readback_pass": audit.get("sheet_count") == 17 and audit.get("sheet_names_exact") and not audit.get("formula_cells") and not audit.get("error_cells"),
        "pending_rows_measured_from_saved_workbook": pending_rows,
        "execution_seconds_monotonic": round(total_elapsed, 6),
        "under_20_minutes": total_elapsed < 1200,
        "eligible_for_full_run": bool(all_shapes_equal and dims_equal and pending_rows == len(SCENARIOS) and audit.get("sheet_count") == 17 and not audit.get("formula_cells") and not audit.get("error_cells") and total_elapsed < 1200),
        "full_run_gate": "PASS" if all_shapes_equal and dims_equal and pending_rows == len(SCENARIOS) and audit.get("sheet_count") == 17 and not audit.get("formula_cells") and not audit.get("error_cells") and total_elapsed < 1200 else "PARTIAL / DO NOT LAUNCH FULL RUN",
    }
    REPORT["status"] = "PASS_SCOPED_DIAGNOSTIC" if REPORT["acceptance"]["eligible_for_full_run"] else "PARTIAL"
    persist()
    emit("diagnostic_complete", status=REPORT["status"], acceptance=REPORT["acceptance"], scenario_write_seconds=scenario_write, shared=REPORT["shared_stages"])
    return 0 if REPORT["acceptance"]["eligible_for_full_run"] else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        REPORT["status"] = "FAIL"
        REPORT["error_type"] = type(exc).__name__
        REPORT["error"] = str(exc)
        REPORT["execution_seconds_monotonic"] = round(time.monotonic() - T0, 6)
        REPORT["acceptance"] = {
            **REPORT.get("acceptance", {}),
            "eligible_for_full_run": False, "full_run_gate": "PARTIAL / DO NOT LAUNCH FULL RUN"
        }
        persist()
        emit("diagnostic_fatal", error_type=type(exc).__name__, error=str(exc), exit_code=1)
        sys.exit(1)
