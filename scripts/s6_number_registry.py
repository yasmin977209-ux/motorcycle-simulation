from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import zipfile
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
from pathlib import Path


from scripts.s6_artifact_reader import PINS, S6_SOURCE, S6_COHORT, C100_SOURCE, C100_COHORT, MASTER_SEED
from scripts.s6_deliverables_builder import build_shared_model

GOVERNING_DECISION = "D-2026-10-30-REFERENCE-V2.4.0"
CURRENT_REFERENCE_SHA256 = "225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b"
HISTORICAL_EXECUTION_REFERENCE_SHA256 = "e5efaf0874384e8248c339ca10e248ea9e17e9f0882153b4ef88bc955b91d53f"
SCHEMA_VERSION = "s6-number-registry-v2"
MODES = ("ACTIVE_ONLY", "ALL_TRIALS_CARRY_FORWARD")
METRICS = ("Cash", "Net_Equity", "Active_Bikes", "Owned_Transferred_Bikes", "Pending_Claims")
QUANTILES = ("P10", "P25", "P50", "P75", "P90")
TRIAL_FIELDS = (
    "bad_debt", "claims_created", "collection_probability", "cumulative_project_profit",
    "final_cash", "final_net_project_equity", "guarantee_recovered", "held_assets",
    "operating_net_profit", "owned_bikes", "partner1_final_entitlement",
    "partner2_final_entitlement", "recovery_rate_pct", "secondary_cycle_count",
    "termination_count", "total_operating_revenue",
)
MISSING_FIELDS = (
    "Accounts_Receivable", "Accumulated_Depreciation", "Gross_Bike_Assets",
    "Guarantee_Claim_Receivable", "Total_Assets",
)
DAILY_COLUMNS = {
    "source_sha", "cohort_id", "scenario_id", "date", "mode", "quantile_name",
    "active_trial_count", "sample_trial_count", "metric_name",
    "exact_numerator", "exact_denominator", "display_value",
}


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def stable_id(prefix: str, value, digits: int = 24) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    return prefix + hashlib.sha256(raw).hexdigest()[:digits]


DAILY_NUMBER_RE = re.compile(r"^D2D-([0-9a-f]{20})-([0-9]{6})$")


def daily_number_id(series_id: str, offset: int) -> str:
    if not isinstance(series_id, str) or not re.fullmatch(r"D2S6-[0-9a-f]{20}", series_id):
        raise ValueError("DAILY_SERIES_ID_INVALID")
    if type(offset) is not int or offset < 0 or offset > 999999:
        raise ValueError("DAILY_NUMBER_OFFSET_INVALID")
    return f"D2D-{series_id[5:]}-{offset:06d}"


def _daily_resolution_indexes(registry: dict):
    """Build O(1) indexes for repeated resolution across the full daily registry."""
    series_by_id = {item.get("series_id"): item for item in registry.get("daily_series", [])}
    date_indexes_by_scenario = {
        item.get("scenario_id"): item for item in registry.get("daily_date_indexes", [])
    }
    return series_by_id, date_indexes_by_scenario


def _resolve_daily_number(registry: dict, number_id: str, series_by_id: dict, date_indexes_by_scenario: dict) -> dict:
    match = DAILY_NUMBER_RE.fullmatch(number_id)
    if match is None:
        raise KeyError(number_id)
    suffix, offset_text = match.groups()
    offset = int(offset_text)
    expected_series_id = "D2S6-" + suffix
    series = series_by_id.get(expected_series_id)
    if series is None or type(series.get("date_count")) is not int:
        raise KeyError(number_id)
    if offset >= series["date_count"] or offset >= len(series.get("values", [])):
        raise KeyError(number_id)

    date_index = date_indexes_by_scenario.get(series.get("scenario_id"))
    if date_index is None:
        raise KeyError(number_id)
    counts = date_index.get("active_trial_counts")
    if not isinstance(counts, list) or offset >= len(counts):
        raise KeyError(number_id)

    active_count = counts[offset]
    n_total = series.get("N_total")
    mode = series.get("mode")
    if type(active_count) is not int or type(n_total) is not int or n_total < 1:
        raise ValueError("DAILY_NUMBER_SAMPLE_PROVENANCE_INVALID")
    if mode not in MODES:
        raise ValueError("DAILY_NUMBER_MODE_INVALID")
    sample_count = active_count if mode == "ACTIVE_ONLY" else n_total
    n, d = series["values"][offset]
    display = display_fraction(n, d)
    first_date = date.fromisoformat(series["first_date"])
    point_date = first_date + timedelta(days=offset)

    return {
        "number_id": number_id,
        "metric_name": series["metric_name"],
        "scenario_id": series["scenario_id"],
        "date": point_date.isoformat(),
        "mode": mode,
        "quantile_name": series["quantile_name"],
        "numerator": n,
        "denominator": d,
        "exact_value": {"numerator": n, "denominator": d},
        "display_value": display,
        "active_trial_count": active_count,
        "sample_trial_count": sample_count,
        "unit": series.get("unit"),
        "source_artifact_id": series["source_artifact_id"],
        "source_run_id": series["source_run_id"],
        "source_member": series["source_member"],
        "source_member_sha256": series["source_member_sha256"],
        "source_member_size_bytes": series.get("source_member_size_bytes"),
        "source_artifact_sha256": series.get("source_artifact_sha256"),
        "source_file_path": series["source_file_path"],
        "source_commit": series["source_commit"],
        "source_sha": series["source_sha"],
        "cohort_id": series["cohort_id"],
        "N_total": n_total,
        "N_closed": series.get("N_closed"),
        "N_censored": series.get("N_censored"),
        "N_unique_paths": series.get("N_unique_paths"),
        "gate_status": series.get("gate_status"),
        "evidence_status": series["evidence_status"],
        "calculation_method": series.get("calculation_method"),
        "rounding_method": series.get("rounding_method"),
        "locator": (
            f"{series['source_member']}#{series['scenario_id']}/"
            f"{point_date.isoformat()}/{mode}/{series['metric_name']}/"
            f"{series['quantile_name']}"
        ),
    }


def resolve_number(registry: dict, number_id: str) -> dict:
    """Resolve an explicit registry ID or a compact daily point ID to full provenance."""
    if not isinstance(number_id, str) or not number_id:
        raise KeyError(number_id)
    for entry in registry.get("entries", []):
        if entry.get("number_id") == number_id:
            return dict(entry)
    series_by_id, date_indexes_by_scenario = _daily_resolution_indexes(registry)
    return _resolve_daily_number(registry, number_id, series_by_id, date_indexes_by_scenario)


def display_fraction(n: int, d: int) -> str:
    if type(n) is not int or type(d) is not int or d < 1:
        raise ValueError("EXACT_RATIONAL_FIELDS_INVALID")
    f = Fraction(n, d)
    if (f.numerator, f.denominator) != (n, d):
        raise ValueError("EXACT_RATIONAL_NOT_REDUCED")
    if d == 1:
        return str(n)
    with localcontext() as ctx:
        ctx.prec = 50
        return format((Decimal(n) / Decimal(d)).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN), "f")


def source_number(value):
    if isinstance(value, bool):
        raise ValueError("BOOLEAN_NOT_NUMERIC")
    if type(value) is int:
        return value, 1, str(value), "EXACT_INTEGER"
    if isinstance(value, Decimal):
        f = Fraction(value)
        return f.numerator, f.denominator, format(value, "f"), "SOURCE_DECIMAL_EXACT"
    raise ValueError("UNSUPPORTED_NUMERIC_TYPE:" + type(value).__name__)


def unit(name):
    x = name.lower()
    if "probability" in x:
        return "probability"
    if x.endswith("_pct"):
        return "percent"
    if any(t in x for t in ("cash", "equity", "profit", "entitlement", "debt", "revenue", "recovered")):
        return "YER"
    if any(t in x for t in ("bike", "asset", "claim", "termination", "cycle", "count")):
        return "count"
    return None


def verify_zip(path, key):
    pin = PINS[key]
    raw = Path(path).read_bytes()
    if len(raw) != pin.size_bytes or sha256(raw) != pin.sha256:
        raise ValueError("ARTIFACT_PIN_MISMATCH:" + key)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None:
            raise ValueError("ARTIFACT_CRC_FAILURE:" + key)
    return {
        "artifact_id": pin.artifact_id, "run_id": pin.run_id, "size_bytes": len(raw),
        "sha256": pin.sha256, "filename": pin.filename, "evidence_status": "VERIFIED_LIVE",
    }


def read_json(z, name):
    return json.loads(z.read(name).decode("utf-8"), parse_float=Decimal)


def verify_member(z, name, meta):
    raw = z.read(name)
    if type(meta.get("size_bytes")) is not int or len(raw) != meta["size_bytes"] or sha256(raw) != meta.get("sha256"):
        raise ValueError("ARTIFACT_MEMBER_PIN_MISMATCH:" + name)
    return raw, sha256(raw)


def no_floats(value, path="$"):
    if isinstance(value, float):
        raise ValueError("FLOAT_FORBIDDEN:" + path)
    if isinstance(value, dict):
        for k, v in value.items():
            no_floats(v, path + "." + str(k))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            no_floats(v, path + "[" + str(i) + "]")


def build_daily(aggregate_zip, manifest, artifact):
    import pyarrow.parquet as pq
    raw, member_digest = verify_member(
        aggregate_zip, "daily_distribution.parquet", manifest["files"]["daily_distribution.parquet"],
    )
    parquet = pq.ParquetFile(io.BytesIO(raw))
    if not DAILY_COLUMNS.issubset(set(parquet.schema_arrow.names)):
        raise ValueError("DAILY_DISTRIBUTION_SCHEMA_MISSING")
    summaries = {x["scenario_id"]: x for x in manifest["scenario_summaries"]}
    if len(summaries) != 20:
        raise ValueError("S6_SCENARIO_SUMMARY_COUNT_INVALID")

    grouped = {}
    active = {}
    rows_per_day = {}
    row_count = 0
    for batch in parquet.iter_batches(batch_size=50000, columns=sorted(DAILY_COLUMNS)):
        for row in batch.to_pylist():
            row_count += 1
            sid = row["scenario_id"]
            if sid not in summaries or row["source_sha"] != S6_SOURCE or row["cohort_id"] != S6_COHORT:
                raise ValueError("DAILY_SOURCE_OR_SCENARIO_IDENTITY_MISMATCH")
            if row["mode"] not in MODES or row["metric_name"] not in METRICS or row["quantile_name"] not in QUANTILES:
                raise ValueError("DAILY_DIMENSION_INVALID")
            dte = date.fromisoformat(row["date"])
            if dte.isoformat() != row["date"]:
                raise ValueError("DAILY_DATE_INVALID")
            a, sample, n, den = (row[k] for k in ("active_trial_count", "sample_trial_count", "exact_numerator", "exact_denominator"))
            if any(type(v) is not int for v in (a, sample, n, den)):
                raise ValueError("DAILY_EXACT_FIELD_TYPE_INVALID")
            total = int(summaries[sid]["n_total"])
            if not 1 <= a <= total or sample != (a if row["mode"] == "ACTIVE_ONLY" else total):
                raise ValueError("DAILY_SAMPLE_COUNT_INVALID")
            if row["display_value"] != display_fraction(n, den):
                raise ValueError("DAILY_DISPLAY_VALUE_MISMATCH")
            key = (sid, row["mode"], row["metric_name"], row["quantile_name"])
            state = grouped.setdefault(key, {"first": dte, "last": None, "values": []})
            if state["last"] is not None and dte != state["last"] + timedelta(days=1):
                raise ValueError("DAILY_DUPLICATE_OR_GAPPED_SERIES:" + repr(key))
            state["last"] = dte
            state["values"].append([n, den])
            day = dte.isoformat()
            prior = active.setdefault(sid, {}).setdefault(day, a)
            if prior != a:
                raise ValueError("DAILY_ACTIVE_COUNT_CONFLICT")
            rows_per_day[(sid, day)] = rows_per_day.get((sid, day), 0) + 1

    per_day = len(MODES) * len(METRICS) * len(QUANTILES)
    if row_count == 0 or len(grouped) != 20 * per_day:
        raise ValueError("DAILY_SERIES_COVERAGE_INVALID")
    indexes, series = [], []
    for sid in sorted(summaries):
        local = [(k, v) for k, v in grouped.items() if k[0] == sid]
        ranges = {(x["first"], x["last"], len(x["values"])) for _, x in local}
        if len(local) != per_day or len(ranges) != 1:
            raise ValueError("DAILY_SERIES_RANGE_CONFLICT:" + sid)
        first, last, count = next(iter(ranges))
        dates = [first + timedelta(days=i) for i in range(count)]
        if dates[-1] != last or set(active[sid]) != {x.isoformat() for x in dates}:
            raise ValueError("DAILY_DATE_COVERAGE_INVALID:" + sid)
        for dte in dates:
            if rows_per_day.get((sid, dte.isoformat())) != per_day:
                raise ValueError("DAILY_ROWS_PER_DATE_INVALID:" + sid)
        indexes.append({
            "scenario_id": sid, "first_date": first.isoformat(), "date_count": count,
            "active_trial_counts": [active[sid][x.isoformat()] for x in dates],
            "source_sha": S6_SOURCE, "cohort_id": S6_COHORT,
        })
        for key, state in sorted(local):
            series_id = stable_id(
                "D2S6-", [sid, S6_SOURCE, S6_COHORT, key[1], key[2], key[3], artifact["sha256"]], 20,
            )
            summary = summaries[sid]
            series.append({
                "series_id": series_id, "scenario_id": sid, "mode": key[1],
                "metric_name": key[2], "quantile_name": key[3],
                "first_date": first.isoformat(), "last_date": last.isoformat(),
                "date_count": count, "values": state["values"],
                "number_id_scheme": "D2D-{series_sha20}-{zero_based_date_offset_6_digits}",
                "unit": unit(key[2]), "source_artifact_id": artifact["artifact_id"],
                "source_run_id": artifact["run_id"], "source_member": "daily_distribution.parquet",
                "source_member_sha256": member_digest, "source_member_size_bytes": len(raw),
                "source_artifact_sha256": artifact["sha256"],
                "source_file_path": "results_stage7_s6/aggregate/daily_distribution.parquet",
                "source_commit": manifest["git_commit"], "source_sha": S6_SOURCE, "cohort_id": S6_COHORT,
                "N_total": int(summary["n_total"]), "N_closed": int(summary["n_closed"]),
                "N_censored": int(summary["n_censored"]), "N_unique_paths": int(summary["n_unique_paths"]),
                "gate_status": {"gate_a": "NOT_DECLARED", "gate_b": "FAIL_SCOPED"},
                "evidence_status": "VERIFIED_LIVE", "calculation_method": "LINEAR_QUANTILE_FRACTION",
                "rounding_method": "ROUND_HALF_EVEN_IF_NON_INTEGER_ELSE_EXACT_INTEGER",
            })
    return series, indexes, {
        "row_count": row_count, "series_count": len(series),
        "point_count": sum(x["date_count"] for x in series),
        "member_sha256": member_digest, "member_size_bytes": len(raw),
    }


def build_registry(paths, source_head, workflow_run_id):
    artifacts = {key: verify_zip(path, key) for key, path in paths.items()}
    model = build_shared_model(paths)
    if (len(model.representative_mapping), len(model.unique_keys), len(model.trial_records)) != (125, 105, 105):
        raise ValueError("D1_SHARED_MODEL_COUNTS_INVALID")

    with zipfile.ZipFile(paths["aggregate"]) as agg, zipfile.ZipFile(paths["full_logging"]) as full, zipfile.ZipFile(paths["c100"]) as c100:
        manifest = read_json(agg, "manifest.json")
        expected_manifest = (S6_SOURCE, S6_COHORT, MASTER_SEED, str(artifacts["aggregate"]["run_id"]), "4f2f2cc16d0cb5125262088704febccbae6f50ed")
        actual_manifest = (manifest.get("source_sha"), manifest.get("cohort_id"), manifest.get("master_seed"), manifest.get("run_id"), manifest.get("git_commit"))
        if actual_manifest != expected_manifest:
            raise ValueError("AGGREGATE_MANIFEST_IDENTITY_MISMATCH")
        summaries = {x["scenario_id"]: x for x in manifest["scenario_summaries"]}
        raw_numbers, numbers_sha = verify_member(agg, "number_registry.json", manifest["files"]["number_registry.json"])
        source_numbers = json.loads(raw_numbers.decode("utf-8"), parse_float=Decimal)
        raw_entries = source_numbers.get("entries")
        if source_numbers.get("schema_version") != "number-registry-v1" or len(raw_entries) != 960:
            raise ValueError("AGGREGATE_NUMBER_REGISTRY_COUNT_INVALID")
        stat = read_json(agg, "statistical_evaluation.json")
        if stat.get("gate_b_final") != "FAIL_SCOPED" or stat.get("scenario_stability_final") != "NOT_CONVERGED":
            raise ValueError("STATISTICAL_GATE_STATUS_CONFLICT")
        gates = {}
        for scenario, data in stat["scenarios"].items():
            for point in data["checkpoint_points"]:
                gates[(scenario, int(point["n"]))] = {
                    "gate_a": point["gate_a"]["status"], "gate_b": point["gate_b"]["status"],
                }

        entries, seen = [], set()
        for i, item in enumerate(raw_entries):
            name, locator = item.get("name"), item.get("source")
            if not isinstance(name, str) or name in seen or not isinstance(locator, str):
                raise ValueError("AGGREGATE_NUMBER_DUPLICATE_OR_NO_LOCATOR")
            seen.add(name)
            parts = locator.split("/")
            if len(parts) < 4 or parts[:2] != [S6_SOURCE, S6_COHORT] or parts[2] not in summaries or not re.fullmatch(r"N[0-9]+", parts[3]):
                raise ValueError("AGGREGATE_NUMBER_SOURCE_LOCATOR_INVALID")
            n, d = item.get("exact_numerator"), item.get("exact_denominator")
            if type(n) is not int or type(d) is not int or d < 1:
                raise ValueError("AGGREGATE_NUMBER_EXACT_FIELDS_INVALID")
            if item.get("rounding") not in ("EXACT_INTEGER", "ROUND_HALF_EVEN") or (item["rounding"] == "EXACT_INTEGER" and d != 1):
                raise ValueError("AGGREGATE_NUMBER_ROUNDING_INVALID")
            if item.get("display_value") != display_fraction(n, d):
                raise ValueError("AGGREGATE_NUMBER_DISPLAY_INVALID")
            sm = summaries[parts[2]]
            entries.append({
                "number_id": stable_id("NR-", [artifacts["aggregate"]["sha256"], name, locator]),
                "metric_name": name, "scenario_id": parts[2], "sample_n": int(parts[3][1:]),
                "source_artifact_id": artifacts["aggregate"]["artifact_id"], "source_run_id": artifacts["aggregate"]["run_id"],
                "source_member": "number_registry.json", "source_member_sha256": numbers_sha,
                "source_member_size_bytes": len(raw_numbers), "source_artifact_sha256": artifacts["aggregate"]["sha256"],
                "source_file_path": "results_stage7_s6/aggregate/number_registry.json",
                "source_commit": manifest["git_commit"], "source_sha": S6_SOURCE, "cohort_id": S6_COHORT,
                "numerator": n, "denominator": d, "exact_value": {"numerator": n, "denominator": d},
                "display_value": item["display_value"], "unit": unit(name),
                "calculation_method": "EXACT_SOURCE_REGISTRY_VALUE", "rounding_method": item["rounding"],
                "N_total": int(sm["n_total"]), "N_closed": int(sm["n_closed"]),
                "N_censored": int(sm["n_censored"]), "N_unique_paths": int(sm["n_unique_paths"]),
                "gate_status": gates.get((parts[2], int(parts[3][1:]))),
                "evidence_status": "VERIFIED_LIVE", "locator": f"number_registry.json#entries[{i}]|{locator}",
            })

        daily_series, daily_indexes, daily_summary = build_daily(agg, manifest, artifacts["aggregate"])

        root = read_json(full, "stagec-output/representative_full_logging_manifest.json")
        select = read_json(full, "stagec-output/representative_selection_map.json")
        unique = read_json(full, "stagec-output/representative_unique_keys.json")
        counts = (root.get("role_assignment_count"), root.get("unique_key_count"), root.get("full_logging_keys_completed"), root.get("full_logging_keys_failed"), len(root.get("results", [])), len(select.get("assignments", [])), len(unique.get("unique_keys", [])))
        if counts != (125, 105, 105, 0, 105, 125, 105):
            raise ValueError("FULL_LOGGING_ROOT_COUNTS_INVALID")
        for doc in (root, select):
            if doc.get("governing_decision_id") != GOVERNING_DECISION or doc.get("governing_reference_sha256") != CURRENT_REFERENCE_SHA256:
                raise ValueError("FULL_LOGGING_REFERENCE_PIN_MISMATCH")
        role_map = {}
        for assignment in select["assignments"]:
            role_map.setdefault((assignment["scenario_id"], int(assignment["trial_id"])), []).append(assignment["role"])

        cmeta = read_json(c100, "docs/audits/S4_C100_GOLDEN_MANIFEST_965281d52441cd0d4b744e211c9f68ee4cdc3753.json")
        if (
            cmeta.get("source_sha") != C100_SOURCE
            or cmeta.get("cohort_id") != C100_COHORT
            or cmeta.get("trial_count_total") != 1500
            or cmeta.get("trial_ids_per_scenario") != [1, 300]
            or len(cmeta.get("scenario_ids", [])) != 5
            or cmeta.get("N_unique_paths") != 1
            or cmeta.get("workflow_run_id") != str(artifacts["c100"]["run_id"])
        ):
            raise ValueError("C100_SOURCE_IDENTITY_INVALID")

        cohort_counts = {S6_COHORT: 0, C100_COHORT: 0}
        for rr in root["results"]:
            scenario, trial_id, folder = rr["scenario_id"], int(rr["trial_id"]), rr["folder"]
            prefix = f"stagec-output/full_logging/{folder}/"
            tm_raw, result_raw, audit_raw = (full.read(prefix + name) for name in ("trial_manifest.json", "trial_result.json", "post_write_audit.json"))
            if sha256(tm_raw) != rr["trial_manifest_sha256"] or sha256(audit_raw) != rr["post_write_audit_sha256"]:
                raise ValueError("REPRESENTATIVE_SIDECAR_HASH_MISMATCH:" + folder)
            tm = json.loads(tm_raw.decode("utf-8"), parse_float=Decimal)
            result = json.loads(result_raw.decode("utf-8"), parse_float=Decimal)
            audit = json.loads(audit_raw.decode("utf-8"), parse_float=Decimal)
            meta = tm.get("files", {}).get("trial_result.json", {})
            if meta.get("size_bytes") != len(result_raw) or meta.get("sha256") != sha256(result_raw):
                raise ValueError("REPRESENTATIVE_RESULT_HASH_MISMATCH:" + folder)
            for field in ("scenario_id", "trial_id", "source_sha", "cohort_id"):
                if result.get(field) != tm.get(field):
                    raise ValueError("REPRESENTATIVE_IDENTITY_MISMATCH:" + folder + ":" + field)
            if result.get("trial_fingerprint") != tm.get("actual_trial_fingerprint"):
                raise ValueError("REPRESENTATIVE_ACTUAL_FINGERPRINT_MISMATCH:" + folder)
            if (rr.get("scenario_id"), rr.get("trial_id"), rr.get("trial_fingerprint")) != (scenario, trial_id, result.get("trial_fingerprint")):
                raise ValueError("REPRESENTATIVE_ROOT_IDENTITY_MISMATCH:" + folder)
            if (tm.get("actual_trial_fingerprint") != tm.get("expected_trial_fingerprint") or audit.get("trial_fingerprint") != result.get("trial_fingerprint") or audit.get("trial_fingerprint_match") is not True or audit.get("status") != "PASS_SCOPED_REPRESENTATIVE_FULL_LOGGING" or audit.get("rollforward_mismatch_count") != 0 or audit.get("balance_mismatch_count") != 0):
                raise ValueError("REPRESENTATIVE_POST_WRITE_AUDIT_MISMATCH:" + folder)

            cohort, source = result["cohort_id"], result["source_sha"]
            if (cohort, source, tm.get("master_seed")) == (S6_COHORT, S6_SOURCE, MASTER_SEED):
                sm = summaries[scenario]
                sample_data = (int(sm["n_total"]), int(sm["n_closed"]), int(sm["n_censored"]), int(sm["n_unique_paths"]))
                origin_run, reuse = artifacts["aggregate"]["run_id"], None
            elif (cohort, source, tm.get("master_seed")) == (C100_COHORT, C100_SOURCE, MASTER_SEED):
                sample_data = (300, None, None, 1)
                origin_run, reuse = artifacts["c100"]["run_id"], "CROSS_COHORT_DETERMINISTIC_REUSE"
            else:
                raise ValueError("REPRESENTATIVE_SOURCE_OR_COHORT_INVALID:" + folder)
            cohort_counts[cohort] += 1

            for field in TRIAL_FIELDS:
                if field not in result:
                    raise ValueError("REPRESENTATIVE_METRIC_MISSING:" + field)
                n, d, shown, rounding = source_number(result[field])
                entries.append({
                    "number_id": stable_id("NR-", [artifacts["full_logging"]["sha256"], cohort, scenario, trial_id, field]),
                    "metric_name": field, "scenario_id": scenario, "source_sha": source, "cohort_id": cohort,
                    "trial_id": trial_id, "sample_n": 1, "role_assignments": sorted(role_map.get((scenario, trial_id), [])),
                    "source_artifact_id": artifacts["full_logging"]["artifact_id"], "source_run_id": artifacts["full_logging"]["run_id"],
                    "origin_run_id": origin_run, "origin_artifact_id": artifacts["c100"]["artifact_id"] if cohort == C100_COHORT else artifacts["aggregate"]["artifact_id"],
                    "source_member": prefix + "trial_result.json", "source_member_sha256": sha256(result_raw),
                    "source_member_size_bytes": len(result_raw), "source_artifact_sha256": artifacts["full_logging"]["sha256"],
                    "source_file_path": prefix + "trial_result.json", "source_commit": result.get("execution_git_commit"),
                    "numerator": n, "denominator": d, "exact_value": {"numerator": n, "denominator": d},
                    "display_value": shown, "unit": unit(field), "calculation_method": "SOURCE_TRIAL_RESULT_FIELD_NO_RECALCULATION",
                    "rounding_method": rounding, "N_total": sample_data[0], "N_closed": sample_data[1],
                    "N_censored": sample_data[2], "N_unique_paths": sample_data[3],
                    "gate_status": None, "evidence_status": "VERIFIED_LIVE",
                    "normalized_audit_status": "NOT_VERIFIED", "post_write_audit_status": audit["status"],
                    "reuse_classification": reuse, "locator": prefix + "trial_result.json#" + field,
                })
            if len(entries) and len(entries) != len(set(x["number_id"] for x in entries)):
                raise ValueError("DUPLICATE_NUMBER_ID")
        if cohort_counts != {S6_COHORT: 100, C100_COHORT: 5}:
            raise ValueError("REPRESENTATIVE_COHORT_COUNTS_INVALID")

    missing = [{
        "metric_name": name, "value": None, "evidence_status": "MISSING_EVIDENCE",
        "reason": "MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS", "do_not_infer_or_zero_fill": True,
    } for name in MISSING_FIELDS]
    if (manifest.get("source_run_metadata") or {}).get("sha256") is None:
        missing.append({"metric_name": "source_run_metadata.sha256", "value": None, "evidence_status": "MISSING_EVIDENCE", "reason": "NULL_IN_PINNED_AGGREGATE_MANIFEST", "do_not_infer_or_zero_fill": True})

    gates = {
        "gate_a_financial": "PASS_SCOPED",
        "gate_a_production": "NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS",
        "gate_b_n2400": "FAIL_SCOPED (10/10)", "stability": "NOT_CONVERGED (0/60)",
        "n4800": "NOT_EXECUTED", "full_logging": "PASS_SCOPED_105_KEYS_ONLY",
        "c100_golden_revalidation": "NOT_RUN",
    }
    registry = {
        "schema_version": SCHEMA_VERSION, "registry_id": "D2-S6-NUMBER-REGISTRY-2026-11-01",
        "governing_decision_id": GOVERNING_DECISION,
        "current_governing_reference_sha256": CURRENT_REFERENCE_SHA256,
        "historical_execution_reference_sha256": HISTORICAL_EXECUTION_REFERENCE_SHA256,
        "generated_from_commit": source_head, "generated_by_workflow_run_id": str(workflow_run_id),
        "scope": {
            "S6": {"source_sha": S6_SOURCE, "cohort_id": S6_COHORT, "master_seed": MASTER_SEED},
            "C100": {"source_sha": C100_SOURCE, "cohort_id": C100_COHORT, "reuse_classification": "CROSS_COHORT_DETERMINISTIC_REUSE", "golden_revalidation": "NOT_RUN"},
            "full_logging_scope": "105_REPRESENTATIVE_KEYS_ONLY_NOT_48000",
        },
        "source_artifacts": artifacts,
        "aggregate_summary": {
            "scenario_count": 20, "checkpoint_values": len(raw_entries),
            "daily_distribution_rows": daily_summary["row_count"], "daily_series_count": daily_summary["series_count"],
            "daily_number_count": daily_summary["point_count"], "representative_trial_count": sum(cohort_counts.values()),
            "representative_numeric_entries": sum(cohort_counts.values()) * len(TRIAL_FIELDS),
        },
        "entries": sorted(entries, key=lambda x: x["number_id"]),
        "daily_date_indexes": daily_indexes, "daily_series": sorted(daily_series, key=lambda x: (x["scenario_id"], x["mode"], x["metric_name"], x["quantile_name"])),
        "daily_number_id_resolution": {
            "rule": "D2D-{series_sha20}-{zero_based_date_offset_6_digits}",
            "date_rule": "first_date plus offset calendar days; all series checked gap-free",
            "lookup_function": "scripts.s6_number_registry.resolve_number",
            "number_id_function": "scripts.s6_number_registry.daily_number_id",
            "series_id_prefix": "D2S6-",
            "point_id_prefix": "D2D-",
        },
        "gate_statuses": gates, "unavailable_evidence": missing,
        "legacy_local_audit": {"path": "docs/stage_d/D2_NUMBER_REGISTRY_AUDIT.md", "reported_entry_count": 13954, "classification": "REPORTED_ONLY"},
        "limitations": [
            "105 representative Full Logging keys only; not 48,000-trial Full Logging.",
            "105 normalized Full Logging statuses remain NOT_VERIFIED.",
            "C100 remains CROSS_COHORT_DETERMINISTIC_REUSE and Golden revalidation remains NOT_RUN.",
            "Production Gate A remains NOT_DECLARED; five historical accounting fields remain MISSING_EVIDENCE.",
            "No Trial, Simulation, Monte Carlo, N expansion, backfill or zero-fill was performed.",
        ],
    }
    no_floats(registry)
    audit = {
        "d2_status": "PASS_SCOPED_WITH_LIMITATIONS", "registry_path": "results/number_registry.json",
        "entry_count": len(entries), "daily_series_count": daily_summary["series_count"],
        "daily_point_count": daily_summary["point_count"], "daily_distribution_rows": daily_summary["row_count"],
        "aggregate_checkpoint_entries": len(raw_entries), "representative_trial_count": sum(cohort_counts.values()),
        "representative_numeric_entries": sum(cohort_counts.values()) * len(TRIAL_FIELDS),
        "cohort_counts": {"S6_representative_keys": cohort_counts[S6_COHORT], "C100_representative_keys": cohort_counts[C100_COHORT]},
        "full_logging_normalized_status": "NOT_VERIFIED_105_OF_105", "c100_golden_revalidation": "NOT_RUN",
        "gate_statuses": gates, "unavailable_evidence": missing, "artifact_pins": artifacts,
        "aggregate_source": {
            "run_id": manifest["run_id"], "source_run_id": manifest["source_run_id"],
            "source_commit": manifest["git_commit"], "source_sha": S6_SOURCE, "cohort_id": S6_COHORT,
            "number_registry_member_sha256": numbers_sha, "daily_distribution_member_sha256": daily_summary["member_sha256"],
            "daily_distribution_member_size_bytes": daily_summary["member_size_bytes"],
        },
        "legacy_local_claim": {"entry_count": 13954, "classification": "REPORTED_ONLY"},
    }
    return registry, audit


def validate_registry(registry):
    if registry.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("REGISTRY_SCHEMA_INVALID")
    if registry.get("current_governing_reference_sha256") != CURRENT_REFERENCE_SHA256 or registry.get("historical_execution_reference_sha256") != HISTORICAL_EXECUTION_REFERENCE_SHA256:
        raise ValueError("REFERENCE_IDENTITY_INVALID")
    no_floats(registry)
    entries, series = registry.get("entries"), registry.get("daily_series")
    if not isinstance(entries, list) or not isinstance(series, list):
        raise ValueError("REGISTRY_COLLECTION_INVALID")
    ids = [x.get("number_id") for x in entries]
    if any(not isinstance(value, str) or not value.startswith("NR-") for value in ids) or len(ids) != len(set(ids)):
        raise ValueError("REGISTRY_NUMBER_ID_DUPLICATE_OR_INVALID")
    for item in entries:
        n, d = item.get("numerator"), item.get("denominator")
        if type(n) is not int or type(d) is not int or d < 1 or item.get("exact_value") != {"numerator": n, "denominator": d}:
            raise ValueError("ENTRY_EXACT_VALUE_INVALID")
        if Fraction(n, d).numerator != n or Fraction(n, d).denominator != d:
            raise ValueError("ENTRY_EXACT_VALUE_NOT_REDUCED")
        for field in ("metric_name", "scenario_id", "source_artifact_id", "source_run_id", "source_member_sha256", "source_file_path", "locator", "evidence_status"):
            if item.get(field) is None:
                raise ValueError("ENTRY_PROVENANCE_MISSING:" + field)
    series_ids = [x.get("series_id") for x in series]
    if any(not isinstance(value, str) or not re.fullmatch(r"D2S6-[0-9a-f]{20}", value) for value in series_ids):
        raise ValueError("DAILY_SERIES_ID_INVALID")
    if len(series_ids) != len(set(series_ids)) or len(series) != 1000:
        raise ValueError("DAILY_SERIES_ID_OR_COUNT_INVALID")
    indexes_list = registry.get("daily_date_indexes", [])
    indexes = {x.get("scenario_id"): x for x in indexes_list}
    if len(indexes) != len(indexes_list) or len(indexes) != 20:
        raise ValueError("DAILY_DATE_INDEX_SCENARIO_COVERAGE_INVALID")
    points = 0
    series_by_id, date_indexes_by_scenario = _daily_resolution_indexes(registry)
    resolved_points = 0
    for item in series:
        if item.get("mode") not in MODES or item.get("metric_name") not in METRICS or item.get("quantile_name") not in QUANTILES:
            raise ValueError("DAILY_SERIES_DIMENSION_INVALID")
        if item.get("date_count") != len(item.get("values", [])) or type(item.get("date_count")) is not int or item["date_count"] < 1:
            raise ValueError("DAILY_SERIES_METADATA_INVALID")
        if not item.get("source_member_sha256") or not item.get("source_artifact_id") or not item.get("source_run_id") or not item.get("source_file_path"):
            raise ValueError("DAILY_SERIES_PROVENANCE_MISSING")
        first = date.fromisoformat(item["first_date"])
        end = first + timedelta(days=item["date_count"] - 1)
        if end.isoformat() != item.get("last_date"):
            raise ValueError("DAILY_SERIES_DATE_RANGE_INVALID")
        index = indexes.get(item.get("scenario_id"))
        if index is None or index.get("first_date") != item["first_date"] or index.get("date_count") != item["date_count"]:
            raise ValueError("DAILY_DATE_INDEX_INVALID")
        active_counts = index.get("active_trial_counts")
        if not isinstance(active_counts, list) or len(active_counts) != item["date_count"]:
            raise ValueError("DAILY_ACTIVE_COUNT_INDEX_INVALID")
        if any(type(value) is not int or value < 1 or value > item["N_total"] for value in active_counts):
            raise ValueError("DAILY_ACTIVE_COUNT_VALUE_INVALID")
        for offset, value in enumerate(item["values"]):
            if not isinstance(value, list) or len(value) != 2:
                raise ValueError("DAILY_SERIES_VALUE_SHAPE_INVALID")
            n, d = value
            if type(n) is not int or type(d) is not int or d < 1:
                raise ValueError("DAILY_SERIES_EXACT_VALUE_INVALID")
            if Fraction(n, d).numerator != n or Fraction(n, d).denominator != d:
                raise ValueError("DAILY_SERIES_FRACTION_NOT_REDUCED")
            point_id = daily_number_id(item["series_id"], offset)
            if DAILY_NUMBER_RE.fullmatch(point_id) is None:
                raise ValueError("DAILY_NUMBER_ID_FORMAT_INVALID")
            # Resolve every addressable point through the same indexed resolver used by callers.
            resolved = _resolve_daily_number(registry, point_id, series_by_id, date_indexes_by_scenario)
            point_date = (first + timedelta(days=offset)).isoformat()
            if (
                resolved.get("numerator") != n
                or resolved.get("denominator") != d
                or resolved.get("scenario_id") != item["scenario_id"]
                or resolved.get("date") != point_date
                or resolved.get("number_id") != point_id
                or resolved.get("exact_value") != {"numerator": n, "denominator": d}
            ):
                raise ValueError("DAILY_NUMBER_ID_RESOLUTION_MISMATCH")
            resolved_points += 1
        points += item["date_count"]
    if resolved_points != points:
        raise ValueError("DAILY_NUMBER_RESOLUTION_COVERAGE_MISMATCH")
    return {
        "entry_count": len(entries),
        "daily_series_count": len(series),
        "daily_point_count": points,
        "daily_points_resolved": resolved_points,
    }


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    for arg in ("aggregate", "full-logging", "c100", "source-head", "workflow-run-id"):
        build.add_argument("--" + arg, required=True)
    build.add_argument("--output", default="results/number_registry.json")
    build.add_argument("--audit-json", default="docs/stage_d/D2_NUMBER_REGISTRY_AUDIT_LIVE_2026-11-01.json")
    build.add_argument("--audit-md", default="docs/stage_d/D2_NUMBER_REGISTRY_AUDIT.md")
    validate = sub.add_parser("validate")
    validate.add_argument("--registry", default="results/number_registry.json")
    args = parser.parse_args()
    if args.command == "validate":
        print(json.dumps(validate_registry(json.loads(Path(args.registry).read_text(encoding="utf-8"))), sort_keys=True))
        return
    paths = {"aggregate": args.aggregate, "full_logging": args.full_logging, "c100": args.c100}
    registry, audit = build_registry(paths, args.source_head, args.workflow_run_id)
    raw = (json.dumps(registry, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_bytes(raw)
    audit.update({
        "registry_size_bytes": len(raw), "registry_sha256": sha256(raw), "registry_git_blob_sha1": blob_sha1(raw),
        "registry_containing_commit": "RECORDED_IN_EXACT_HEAD_WORKFLOW_LOG",
        "workflow_run_id": str(args.workflow_run_id), "source_head": args.source_head,
        "exact_head_validation": "RECORDED_IN_EXACT_HEAD_WORKFLOW_LOG",
    })
    Path(args.audit_json).write_text(json.dumps(audit, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    md = Path(args.audit_md)
    old = md.read_text(encoding="utf-8") if md.exists() else ""
    marker = "## D2 live registry build — 2026-11-01"
    if marker not in old:
        with md.open("a", encoding="utf-8") as out:
            out.write(
                "\n\n" + marker + "\n\n"
                + f"- D2 disposition: PASS_SCOPED_WITH_LIMITATIONS, subject to exact-head validation in Run {args.workflow_run_id}.\n"
                + f"- Registry: {audit['entry_count']} entries; {audit['daily_series_count']} daily series; {audit['daily_point_count']} addressable daily points.\n"
                + f"- Daily Distribution source rows validated: {audit['daily_distribution_rows']}; aggregate checkpoint values: {audit['aggregate_checkpoint_entries']}.\n"
                + "- Historical local count 13,954 remains REPORTED_ONLY and is not the live registry count.\n"
                + "- Preserved: Full Logging 105 representatives only; statuses NOT_VERIFIED; C100 Golden NOT_RUN; Gate A financial PASS_SCOPED; production NOT_DECLARED; Gate B FAIL_SCOPED; Stability NOT_CONVERGED; N=4800 NOT_EXECUTED; five accounting fields MISSING_EVIDENCE.\n"
                + "- No Trial, Simulation, Monte Carlo, N expansion, historical backfill or zero-fill was performed.\n"
            )
    print(json.dumps({"status": audit["d2_status"], **validate_registry(registry), **audit}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
