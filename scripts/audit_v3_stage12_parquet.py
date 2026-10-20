from __future__ import annotations

import hashlib
import io
import json
import os
import re
import sys
import tarfile
import zipfile
from datetime import datetime, timezone
from pathlib import PurePosixPath
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen
from pathlib import Path


REPO = "yasmin977209-ux/motorcycle-simulation"
V3_ARTIFACT = {
    "id": 11503510055,
    "run_id": 37662891608,
    "head_sha": "6128b22864bb171ba49ec15dbb42439a6513c30c",
    "source_sha": "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b",
    "zip_sha256": "111eb7a2abd7b85625a02c55ee6f3140a14644ef253141bfdc3f8fc5ae4c287d",
    "size_bytes": 17787110,
}
STAGE12_ARTIFACT = {
    "id": 11634501915,
    "run_id": 37964656154,
    "head_sha": "0156c5f4272eb0ca7e32442657d0df9eaf4973d3",
    "source_sha": "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b",
    "zip_sha256": "7d67097186dad801c6f0377a70decb5cf8dadea8f82a0b86956823a6a4191cf1",
    "size_bytes": 65578787,
    "parquet_member": "C050_G000.parquet",
    "parquet_sha256": "6beecb837a3c6b71f34aedbeb958e8dd176cce3d60b2dfa1b95ee9bd57e6a380",
}
EXPECTED_REFERENCE_SHA256 = "ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479"
EXPECTED_V3_TRIAL_PARQUET_SHA256 = "09c223d8348f93a5c5e9246a409614d6345a76b224ff65f865c6bdbaea5fbbe8"
EXPECTED_V3_FINGERPRINTS_SHA256 = "82cb7a2725944edc3b749bcc722d22040459baac2db6c68f3c0ddde98b0db8f6"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward the GitHub bearer token to a signed object-storage URL.
        return None


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def api_json(url: str, token: str) -> dict:
    req = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "motorcycle-simulation-readonly-parquet-audit",
        },
    )
    with urlopen(req, timeout=45) as response:
        data = json.loads(response.read())
    if not isinstance(data, dict):
        raise RuntimeError(f"API_JSON_ROOT_NOT_OBJECT: {url}")
    return data


def download_artifact(artifact_id: int, token: str) -> bytes:
    url = f"https://api.github.com/repos/{REPO}/actions/artifacts/{artifact_id}/zip"
    req = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "motorcycle-simulation-readonly-parquet-audit",
        },
    )
    opener = build_opener(NoRedirect)
    try:
        with opener.open(req, timeout=90) as response:
            return response.read()
    except HTTPError as exc:
        if exc.code not in {301, 302, 303, 307, 308}:
            raise RuntimeError(f"ARTIFACT_DOWNLOAD_HTTP_{exc.code}: artifact={artifact_id}") from exc
        location = exc.headers.get("Location")
        if not location:
            raise RuntimeError(f"ARTIFACT_REDIRECT_LOCATION_MISSING: artifact={artifact_id}") from exc
        # The redirect is a signed URL. Deliberately send no GitHub Authorization header.
        with urlopen(Request(location, headers={"User-Agent": "read-only-artifact-audit"}), timeout=180) as response:
            return response.read()


def validate_artifact_metadata(spec: dict, token: str) -> dict:
    meta = api_json(
        f"https://api.github.com/repos/{REPO}/actions/artifacts/{spec['id']}", token
    )
    if meta.get("id") != spec["id"]:
        raise RuntimeError(f"ARTIFACT_ID_MISMATCH: {spec['id']}")
    if meta.get("expired") is True:
        raise RuntimeError(f"ARTIFACT_EXPIRED: {spec['id']}")
    if meta.get("size_in_bytes") != spec["size_bytes"]:
        raise RuntimeError(
            f"ARTIFACT_SIZE_MISMATCH: {spec['id']} "
            f"expected={spec['size_bytes']} actual={meta.get('size_in_bytes')}"
        )
    run = meta.get("workflow_run") or {}
    if run.get("id") != spec["run_id"]:
        raise RuntimeError(
            f"ARTIFACT_RUN_ID_MISMATCH: {spec['id']} "
            f"expected={spec['run_id']} actual={run.get('id')}"
        )
    if run.get("head_sha") != spec["head_sha"]:
        raise RuntimeError(
            f"ARTIFACT_PRODUCER_SHA_MISMATCH: {spec['id']} "
            f"expected={spec['head_sha']} actual={run.get('head_sha')}"
        )
    reported_digest = meta.get("digest")
    expected_digest = f"sha256:{spec['zip_sha256']}"
    if reported_digest and reported_digest != expected_digest:
        raise RuntimeError(
            f"ARTIFACT_API_DIGEST_MISMATCH: {spec['id']} "
            f"expected={expected_digest} actual={reported_digest}"
        )
    return {
        "artifact_id": meta["id"],
        "name": meta.get("name"),
        "size_in_bytes": meta["size_in_bytes"],
        "expired": meta.get("expired"),
        "api_digest": reported_digest,
        "run_id": run.get("id"),
        "head_branch": run.get("head_branch"),
        "head_sha": run.get("head_sha"),
        "created_at": meta.get("created_at"),
        "expires_at": meta.get("expires_at"),
    }


def check_zip_digest(raw: bytes, spec: dict) -> dict:
    actual = sha256(raw)
    if len(raw) != spec["size_bytes"]:
        raise RuntimeError(
            f"ARTIFACT_DOWNLOADED_SIZE_MISMATCH: {spec['id']} "
            f"expected={spec['size_bytes']} actual={len(raw)}"
        )
    if actual != spec["zip_sha256"]:
        raise RuntimeError(
            f"ARTIFACT_ZIP_SHA256_MISMATCH: {spec['id']} "
            f"expected={spec['zip_sha256']} actual={actual}"
        )
    return {"bytes": len(raw), "sha256": actual}


def safe_zip_member(zf: zipfile.ZipFile, exact_suffix: str) -> bytes:
    candidates = [
        name for name in zf.namelist()
        if not name.endswith("/") and name.replace("\\", "/").endswith(exact_suffix)
    ]
    if len(candidates) != 1:
        raise RuntimeError(
            f"ZIP_MEMBER_NOT_UNIQUE: suffix={exact_suffix} matches={candidates}"
        )
    return zf.read(candidates[0])


def parquet_member_from_v3(zip_raw: bytes) -> tuple[dict, bytes, bytes]:
    with zipfile.ZipFile(io.BytesIO(zip_raw), "r") as outer:
        tar_names = [n for n in outer.namelist() if n.endswith(".tar.gz")]
        if len(tar_names) != 1:
            raise RuntimeError(f"V3_OUTER_TAR_NOT_UNIQUE: {tar_names}")
        tar_raw = outer.read(tar_names[0])
    with tarfile.open(fileobj=io.BytesIO(tar_raw), mode="r:gz") as tar:
        def extract(suffix: str) -> bytes:
            matches = [
                m for m in tar.getmembers()
                if m.isfile() and PurePosixPath(m.name).as_posix().endswith(suffix)
            ]
            if len(matches) != 1:
                raise RuntimeError(f"V3_TAR_MEMBER_NOT_UNIQUE: suffix={suffix}")
            stream = tar.extractfile(matches[0])
            if stream is None:
                raise RuntimeError(f"V3_TAR_MEMBER_NOT_READABLE: suffix={suffix}")
            return stream.read()
        meta_raw = extract("scenario_metadata.json")
        trials_raw = extract("trial_results.parquet")
        fingerprints_raw = extract("trial_fingerprints.json")
    meta = json.loads(meta_raw)
    if meta.get("scenario") != "C050_G000" or meta.get("trial_count") != 450:
        raise RuntimeError(
            f"V3_SCENARIO_OR_TRIAL_COUNT_MISMATCH: "
            f"{meta.get('scenario')} / {meta.get('trial_count')}"
        )
    if meta.get("source_sha") != V3_ARTIFACT["source_sha"]:
        raise RuntimeError("V3_INTERNAL_SOURCE_SHA_MISMATCH")
    if str(meta.get("run_id")) != "37225915321":
        raise RuntimeError(f"V3_OFFICIAL_SOURCE_RUN_MISMATCH: {meta.get('run_id')}")
    if sha256(trials_raw) != EXPECTED_V3_TRIAL_PARQUET_SHA256:
        raise RuntimeError("V3_TRIAL_RESULTS_PARQUET_SHA256_MISMATCH")
    if sha256(fingerprints_raw) != EXPECTED_V3_FINGERPRINTS_SHA256:
        raise RuntimeError("V3_TRIAL_FINGERPRINTS_SHA256_MISMATCH")
    return meta, trials_raw, fingerprints_raw


def normalize_column(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.casefold())


def date_text(value) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def main() -> int:
    evidence_dir = Path("parquet_audit_evidence")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_dir / "v3_stage12_parquet_audit.json"
    evidence = {
        "schema_version": "1.0",
        "audit_type": "V3_MAXCASE_AND_STAGE12_PARTNER_BALANCE_SCHEMA",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "branch": os.environ.get("GITHUB_REF_NAME"),
        "tested_sha": os.environ.get("GITHUB_SHA"),
        "reference_sha256": EXPECTED_REFERENCE_SHA256,
        "artifacts": {
            "v3": {"spec": V3_ARTIFACT},
            "stage12": {"spec": STAGE12_ARTIFACT},
        },
        "simulation_or_trial_generation": False,
        "source_data_modified": False,
        "main_modified": False,
    }
    try:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise RuntimeError("GITHUB_TOKEN_UNAVAILABLE")
        import pyarrow.parquet as pq

        for key, spec in (("v3", V3_ARTIFACT), ("stage12", STAGE12_ARTIFACT)):
            evidence["artifacts"][key]["api_metadata"] = validate_artifact_metadata(spec, token)
            raw = download_artifact(spec["id"], token)
            evidence["artifacts"][key]["download"] = check_zip_digest(raw, spec)
            evidence["artifacts"][key]["_raw_zip"] = raw

        v3_zip = evidence["artifacts"]["v3"].pop("_raw_zip")
        meta, v3_parquet_raw, fingerprints_raw = parquet_member_from_v3(v3_zip)
        v3_pf = pq.ParquetFile(io.BytesIO(v3_parquet_raw))
        v3_schema = v3_pf.schema_arrow
        v3_rows = pq.read_table(io.BytesIO(v3_parquet_raw)).to_pylist()
        v3_names = list(v3_schema.names)
        normalized = {normalize_column(n): n for n in v3_names}
        trial_col = normalized.get("trialid")
        equity_col = normalized.get("finalnetprojectequity")
        if trial_col is None or equity_col is None:
            raise RuntimeError(
                f"V3_REQUIRED_COLUMN_MISSING: trial_col={trial_col}, equity_col={equity_col}, columns={v3_names}"
            )
        trial_ids = []
        equity_by_id = {}
        for row in v3_rows:
            trial_id = row.get(trial_col)
            equity = row.get(equity_col)
            if type(trial_id) is not int or type(equity) is not int:
                raise RuntimeError(
                    f"V3_TRIAL_OR_EQUITY_NOT_EXACT_INTEGER: trial_id={trial_id!r}, equity={equity!r}"
                )
            trial_ids.append(trial_id)
            if trial_id in equity_by_id:
                raise RuntimeError(f"V3_DUPLICATE_TRIAL_ID: {trial_id}")
            equity_by_id[trial_id] = equity
        if sorted(trial_ids) != list(range(1, 451)):
            raise RuntimeError(
                f"V3_TRIAL_COVERAGE_MISMATCH: rows={len(v3_rows)}, "
                f"ids_count={len(set(trial_ids))}, min={min(trial_ids) if trial_ids else None}, "
                f"max={max(trial_ids) if trial_ids else None}"
            )
        fingerprint_obj = json.loads(fingerprints_raw)
        fingerprints = fingerprint_obj.get("fingerprints", {})
        if len(fingerprints) != 450 or set(fingerprints) != {str(i) for i in range(1, 451)}:
            raise RuntimeError(f"V3_FINGERPRINT_COVERAGE_MISMATCH: {len(fingerprints)}")
        positive = [(equity, trial_id) for trial_id, equity in equity_by_id.items() if equity > 0]
        if positive:
            maximum_value = max(value for value, _ in positive)
            maxcase_id = min(trial_id for value, trial_id in positive if value == maximum_value)
            maxcase = {
                "status": "PASS_SCOPED",
                "trial_id": maxcase_id,
                "final_net_project_equity": maximum_value,
                "tie_count_at_maximum": sum(1 for value, _ in positive if value == maximum_value),
                "positive_trial_count": len(positive),
                "selected_trial_id_matches_stage12_trial60": maxcase_id == 60,
            }
        else:
            maxcase = {
                "status": "UNDEFINED_BUSINESS_RULE",
                "trial_id": None,
                "final_net_project_equity": None,
                "positive_trial_count": 0,
                "selected_trial_id_matches_stage12_trial60": False,
            }
        rep_ids = meta.get("representative_trials", {})
        representative_equities = {
            role: {
                "trial_id": int(trial_id),
                "final_net_project_equity": equity_by_id.get(int(trial_id)),
            }
            for role, trial_id in rep_ids.items()
        }
        evidence["v3"] = {
            "artifact_id": V3_ARTIFACT["id"],
            "producer_run_id": V3_ARTIFACT["run_id"],
            "producer_sha": V3_ARTIFACT["head_sha"],
            "official_source_run_id": meta.get("run_id"),
            "source_sha": meta.get("source_sha"),
            "scenario": meta.get("scenario"),
            "trial_count_metadata": meta.get("trial_count"),
            "daily_row_count_metadata": meta.get("daily_row_count"),
            "trial_results_parquet_sha256": sha256(v3_parquet_raw),
            "trial_rows_read": len(v3_rows),
            "trial_id_min": min(trial_ids),
            "trial_id_max": max(trial_ids),
            "unique_trial_ids": len(set(trial_ids)),
            "trial_ids_contiguous_1_to_450": True,
            "trial_fingerprints_count": len(fingerprints),
            "columns": v3_names,
            "equity_column": equity_col,
            "maxcase": maxcase,
            "recorded_representatives_with_values": representative_equities,
            "log_events_metadata": meta.get("log_events"),
        }

        stage12_zip = evidence["artifacts"]["stage12"].pop("_raw_zip")
        with zipfile.ZipFile(io.BytesIO(stage12_zip), "r") as zf:
            parquet_raw = safe_zip_member(zf, STAGE12_ARTIFACT["parquet_member"])
        actual_parquet_sha = sha256(parquet_raw)
        if actual_parquet_sha != STAGE12_ARTIFACT["parquet_sha256"]:
            raise RuntimeError(
                f"STAGE12_PARQUET_MEMBER_SHA_MISMATCH: "
                f"expected={STAGE12_ARTIFACT['parquet_sha256']} actual={actual_parquet_sha}"
            )
        stage12_pf = pq.ParquetFile(io.BytesIO(parquet_raw))
        stage12_names = list(stage12_pf.schema_arrow.names)
        norm_stage12 = {normalize_column(n): n for n in stage12_names}
        stage12_trial_col = norm_stage12.get("trialid")
        stage12_date_col = norm_stage12.get("date") or norm_stage12.get("dailydate")
        if stage12_trial_col is None:
            raise RuntimeError(f"STAGE12_TRIAL_ID_COLUMN_MISSING: {stage12_names}")
        candidates = [
            name for name in stage12_names
            if any(token in normalize_column(name) for token in ("partner", "memo", "reinvest", "balance"))
        ]
        exact_required = {
            "Partner1_Reinvestment_Balance": "partner1reinvestmentbalance",
            "Partner2_Reinvestment_Balance": "partner2reinvestmentbalance",
        }
        required_presence = {
            name: normalize in norm_stage12
            for name, normalize in exact_required.items()
        }
        profit_field = norm_stage12.get("cumulativeprojectprofit")
        retained_field = norm_stage12.get("retainedearnings")
        scan_cols = list(dict.fromkeys([stage12_trial_col] + ([stage12_date_col] if stage12_date_col else []) + candidates))
        candidate_non_nulls = {name: 0 for name in candidates}
        trial60_rows = 0
        trial60_dates = []
        rows_scanned = 0
        for batch in stage12_pf.iter_batches(columns=scan_cols, batch_size=100_000):
            rows_scanned += batch.num_rows
            ids = batch.column(batch.schema.get_field_index(stage12_trial_col)).to_pylist()
            date_values = (
                batch.column(batch.schema.get_field_index(stage12_date_col)).to_pylist()
                if stage12_date_col else [None] * batch.num_rows
            )
            candidate_values = {
                name: batch.column(batch.schema.get_field_index(name)).to_pylist()
                for name in candidates
            }
            for i, trial_id in enumerate(ids):
                if trial_id == 60:
                    trial60_rows += 1
                    if date_values[i] is not None:
                        text_value = date_text(date_values[i])
                        if text_value:
                            trial60_dates.append(text_value)
            for name, values in candidate_values.items():
                candidate_non_nulls[name] += sum(value is not None for value in values)
        partner1_candidates = [
            c for c in candidates if "partner1" in normalize_column(c) or "partnerone" in normalize_column(c)
        ]
        partner2_candidates = [
            c for c in candidates if "partner2" in normalize_column(c) or "partnertwo" in normalize_column(c)
        ]
        partner_source_status = (
            "SCHEMA_FIELDS_PRESENT"
            if required_presence["Partner1_Reinvestment_Balance"] and required_presence["Partner2_Reinvestment_Balance"]
            else "MISSING_EVIDENCE"
        )
        evidence["stage12"] = {
            "artifact_id": STAGE12_ARTIFACT["id"],
            "producer_run_id": STAGE12_ARTIFACT["run_id"],
            "producer_sha": STAGE12_ARTIFACT["head_sha"],
            "source_sha": STAGE12_ARTIFACT["source_sha"],
            "zip_sha256": STAGE12_ARTIFACT["zip_sha256"],
            "parquet_member": STAGE12_ARTIFACT["parquet_member"],
            "parquet_member_sha256": actual_parquet_sha,
            "parquet_num_rows": stage12_pf.metadata.num_rows,
            "rows_scanned_for_schema_field_presence": rows_scanned,
            "columns": stage12_names,
            "date_column": stage12_date_col,
            "partner_balance_memo_candidate_columns": candidates,
            "partner1_candidate_columns": partner1_candidates,
            "partner2_candidate_columns": partner2_candidates,
            "exact_required_fields_present": required_presence,
            "candidate_non_null_counts": candidate_non_nulls,
            "cumulative_project_profit_column_present": profit_field is not None,
            "retained_earnings_column_present": retained_field is not None,
            "partner_source_status": partner_source_status,
            "trial60_daily_rows": trial60_rows,
            "trial60_first_date": min(trial60_dates) if trial60_dates else None,
            "trial60_last_date": max(trial60_dates) if trial60_dates else None,
        }
        evidence["status"] = (
            "UNDEFINED_BUSINESS_RULE"
            if maxcase["status"] == "UNDEFINED_BUSINESS_RULE"
            else "PASS_SCOPED"
        )
        evidence["limitations"] = [
            "This audit reads existing artifacts only; no trial or simulation was run.",
            "Stage12 partner-column name candidates are observations, not automatic authorization to equate differently named financial fields.",
            "This evidence does not close Gate A, SOURCE_SHA_DRIFT, Stage 9C, or delivery acceptance.",
        ]
        evidence["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(evidence, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        evidence["status"] = "BLOCKED"
        evidence["error_type"] = type(exc).__name__
        evidence["error"] = str(exc)
        evidence["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(evidence, indent=2, sort_keys=True))
        return 1


if __name__ == "__main__":
    sys.exit(main())
