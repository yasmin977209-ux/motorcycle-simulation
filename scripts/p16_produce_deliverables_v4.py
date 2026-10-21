from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
import zipfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path, PurePosixPath
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

import pyarrow.parquet as pq
from openpyxl import load_workbook
from openpyxl.xml.constants import SHEET_MAIN_NS

from scripts import excel_builder_p16 as excel_builder


REPO = "yasmin977209-ux/motorcycle-simulation"
MAIN_HEAD_REQUIRED = "6a218ebe0fccf210ec18f3552b141afbdd1a49ef"
MAIN_MANIFEST_BLOB = "e796fa2443493b607f1f9c60b58eb63607959c26"
SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
REFERENCE_SHA256 = "ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479"
V3_SCENARIO = "C050_G000"
V3_ARTIFACT_ID = 11503510055
V3_RUN_ID = 37662891608
V3_PRODUCER_SHA = "6128b22864bb171ba49ec15dbb42439a6513c30c"
V3_ZIP_SHA256 = "111eb7a2abd7b85625a02c55ee6f3140a14644ef253141bfdc3f8fc5ae4c287d"
V3_TRIAL_PARQUET_SHA256 = "09c223d8348f93a5c5e9246a409614d6345a76b224ff65f865c6bdbaea5fbbe8"
V3_FINGERPRINTS_SHA256 = "82cb7a2725944edc3b749bcc722d22040459baac2db6c68f3c0ddde98b0db8f6"
ROLE_MAP = {"P10": "P10", "P50": "P50", "P90": "P90", "LossCase": "Loss", "MaxCase": "MaxCase"}
EXPECTED_PENDING_CASES = len(excel_builder.EXPECTED_SCENARIOS)

OUTPUT_NAMES = [
    "النتائج_الكاملة_AR.xlsx",
    "Full_Results_EN.xlsx",
    "التقرير_الكامل_AR",
    "Full_Report_EN",
    "الملخص_AR",
    "Summary_EN",
    "دراسة_الجدوى_AR",
]


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Avoid forwarding a GitHub bearer token to signed object-storage URLs.
        return None


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _progress(event: str, **fields) -> None:
    record = {"event": event, "at_utc": now_utc(), **fields}
    print("[P16_PROGRESS] " + json.dumps(record, ensure_ascii=False, sort_keys=True, default=str), flush=True)


def api_json(url: str, token: str) -> dict:
    req = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "motorcycle-simulation-p16-provisional-build",
        },
    )
    with urlopen(req, timeout=60) as response:
        value = json.loads(response.read())
    if not isinstance(value, dict):
        raise RuntimeError(f"API_JSON_ROOT_NOT_OBJECT: {url}")
    return value


def download_artifact_zip(artifact_id: int, token: str) -> bytes:
    url = f"https://api.github.com/repos/{REPO}/actions/artifacts/{artifact_id}/zip"
    req = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "motorcycle-simulation-p16-provisional-build",
        },
    )
    opener = build_opener(NoRedirect())
    try:
        with opener.open(req, timeout=120) as response:
            return response.read()
    except HTTPError as exc:
        if exc.code not in {301, 302, 303, 307, 308}:
            raise RuntimeError(f"ARTIFACT_DOWNLOAD_HTTP_{exc.code}: artifact={artifact_id}") from exc
        location = exc.headers.get("Location")
        if not location:
            raise RuntimeError(f"ARTIFACT_REDIRECT_LOCATION_MISSING: artifact={artifact_id}") from exc
        # The signed redirect is fetched without the GitHub token.
        with urlopen(Request(location, headers={"User-Agent": "read-only-artifact-fetch"}), timeout=240) as response:
            return response.read()


def select_maxcase_row(rows: list[dict]) -> dict:
    candidates = []
    for row in rows:
        trial_id = row.get("trial_id")
        equity = row.get("final_net_project_equity")
        if type(trial_id) is not int or trial_id < 1:
            raise RuntimeError(f"MAXCASE_INVALID_TRIAL_ID: {trial_id!r}")
        if type(equity) is not int:
            raise RuntimeError(f"MAXCASE_EQUITY_NOT_EXACT_INTEGER: trial_id={trial_id}, value={equity!r}")
        if equity > 0:
            candidates.append((equity, trial_id, row))
    if not candidates:
        raise RuntimeError("UNDEFINED_BUSINESS_RULE: MaxCase has no positive Final_Net_Project_Equity")
    max_equity = max(item[0] for item in candidates)
    return min((item for item in candidates if item[0] == max_equity), key=lambda item: item[1])[2]


def _tar_member(tar: tarfile.TarFile, suffix: str) -> bytes:
    candidates = [
        member for member in tar.getmembers()
        if member.isfile() and PurePosixPath(member.name).as_posix().lstrip("./").endswith(suffix)
    ]
    if len(candidates) != 1:
        raise RuntimeError(f"TAR_MEMBER_NOT_UNIQUE: suffix={suffix}, candidates={[m.name for m in candidates]}")
    stream = tar.extractfile(candidates[0])
    if stream is None:
        raise RuntimeError(f"TAR_MEMBER_NOT_READABLE: {suffix}")
    return stream.read()


def _normalise_scenario_meta(raw: bytes) -> dict:
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise RuntimeError("SCENARIO_METADATA_ROOT_NOT_OBJECT")
    return value


def _extract_scenario_inputs_and_cache_p50(tar_raw: bytes, scenario_dir: Path) -> dict:
    """Read one gzip tar sequentially, keeping compact files and a compressed P50 cache."""
    selected_suffixes = (
        "scenario_metadata.json",
        "trial_results.parquet",
        "daily_distribution.parquet",
        "trial_fingerprints.json",
        "representatives/P50.json",
    )
    selected = {}
    counts = {suffix: 0 for suffix in selected_suffixes}
    maxcase_count = 0
    reps_dir = scenario_dir / "representatives"
    reps_dir.mkdir(parents=True, exist_ok=True)
    p50_cache = reps_dir / "P50.json.gz"
    p50_temp = reps_dir / "P50.json.gz.tmp"
    started = time.monotonic()
    _progress("scenario_tar_stream_start", scenario=scenario_dir.name, tar_bytes=len(tar_raw))
    try:
        with tarfile.open(fileobj=io.BytesIO(tar_raw), mode="r|gz") as tar:
            for member in tar:
                if not member.isfile():
                    continue
                normalized = PurePosixPath(member.name.replace("\\", "/")).as_posix().lstrip("./")
                if normalized.endswith("representatives/MaxCase.json"):
                    maxcase_count += 1
                    if maxcase_count > 1:
                        raise RuntimeError(f"MAXCASE_MEMBER_DUPLICATE: {scenario_dir.name}")
                suffix = next((candidate for candidate in selected_suffixes if normalized.endswith(candidate)), None)
                if suffix is None:
                    continue
                counts[suffix] += 1
                if counts[suffix] > 1:
                    raise RuntimeError(f"SCENARIO_MEMBER_DUPLICATE: {scenario_dir.name}/{suffix}")
                source = tar.extractfile(member)
                if source is None:
                    raise RuntimeError(f"SCENARIO_MEMBER_UNREADABLE: {scenario_dir.name}/{suffix}")
                if suffix == "representatives/P50.json":
                    with source, p50_temp.open("wb") as raw_out:
                        with gzip.GzipFile(fileobj=raw_out, mode="wb", compresslevel=1, mtime=0) as compressed_out:
                            shutil.copyfileobj(source, compressed_out, length=1024 * 1024)
                    os.replace(p50_temp, p50_cache)
                    selected["p50_json_bytes_raw"] = int(member.size)
                else:
                    with source:
                        selected[suffix] = source.read()
        missing = [suffix for suffix, count in counts.items() if count != 1]
        if missing:
            raise RuntimeError(f"SCENARIO_MEMBERS_NOT_UNIQUE: {scenario_dir.name}: {missing}; counts={counts}")
        if maxcase_count > 1:
            raise RuntimeError(f"MAXCASE_MEMBER_NOT_UNIQUE: {scenario_dir.name}")
        selected["maxcase_payload_present"] = maxcase_count == 1
        selected["p50_cache_path"] = str(p50_cache)
        selected["p50_cache_bytes_gzip"] = p50_cache.stat().st_size
        _progress(
            "scenario_tar_stream_complete",
            scenario=scenario_dir.name,
            member_counts=counts,
            p50_json_bytes_raw=selected["p50_json_bytes_raw"],
            p50_cache_bytes_gzip=selected["p50_cache_bytes_gzip"],
            maxcase_payload_present=selected["maxcase_payload_present"],
            elapsed_seconds=round(time.monotonic() - started, 3),
        )
        return selected
    finally:
        p50_temp.unlink(missing_ok=True)


def fetch_scenario_artifact(
    *,
    scenario: str,
    artifact_id: int,
    expected_artifact_run_id: int,
    dataset_root: Path,
    token: str,
    manifest: dict,
) -> dict:
    started = time.monotonic()
    _progress("scenario_artifact_start", scenario=scenario, artifact_id=artifact_id, expected_run_id=expected_artifact_run_id)
    api_meta = api_json(f"https://api.github.com/repos/{REPO}/actions/artifacts/{artifact_id}", token)
    if api_meta.get("id") != artifact_id:
        raise RuntimeError(f"ARTIFACT_ID_MISMATCH: {scenario}")
    if api_meta.get("expired") is True:
        raise RuntimeError(f"ARTIFACT_EXPIRED: {scenario}/{artifact_id}")
    workflow_run = api_meta.get("workflow_run") or {}
    actual_run_id = workflow_run.get("id")
    actual_head_sha = workflow_run.get("head_sha")
    if actual_run_id != expected_artifact_run_id:
        raise RuntimeError(
            f"ARTIFACT_RUN_ID_MISMATCH: {scenario}; expected={expected_artifact_run_id}, actual={actual_run_id}"
        )
    if not isinstance(actual_head_sha, str) or len(actual_head_sha) != 40:
        raise RuntimeError(f"ARTIFACT_PRODUCER_HEAD_MISSING: {scenario}/{artifact_id}")
    if scenario == V3_SCENARIO and (artifact_id, actual_run_id, actual_head_sha) != (
        V3_ARTIFACT_ID, V3_RUN_ID, V3_PRODUCER_SHA
    ):
        raise RuntimeError("C050_G000_V3_IDENTITY_MISMATCH")
    download_started = time.monotonic()
    _progress("scenario_artifact_download_start", scenario=scenario, artifact_id=artifact_id, api_size_bytes=api_meta.get("size_in_bytes"))
    raw_zip = download_artifact_zip(artifact_id, token)
    _progress("scenario_artifact_download_complete", scenario=scenario, artifact_id=artifact_id, bytes=len(raw_zip), elapsed_seconds=round(time.monotonic() - download_started, 3))
    actual_zip_sha = sha256_bytes(raw_zip)
    api_digest = api_meta.get("digest")
    if len(raw_zip) != api_meta.get("size_in_bytes"):
        raise RuntimeError(
            f"ARTIFACT_SIZE_MISMATCH: {scenario}; expected={api_meta.get('size_in_bytes')}, actual={len(raw_zip)}"
        )
    if api_digest and api_digest != f"sha256:{actual_zip_sha}":
        raise RuntimeError(f"ARTIFACT_DIGEST_MISMATCH: {scenario}; api={api_digest}, actual={actual_zip_sha}")
    if scenario == V3_SCENARIO and actual_zip_sha != V3_ZIP_SHA256:
        raise RuntimeError("C050_G000_V3_ZIP_SHA256_MISMATCH")

    scenario_dir = dataset_root / scenario
    scenario_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(raw_zip), "r") as outer:
        inner_tar_names = [name for name in outer.namelist() if not name.endswith("/") and name.endswith(".tar.gz")]
        if len(inner_tar_names) != 1:
            raise RuntimeError(f"OUTER_ZIP_TAR_MEMBER_NOT_UNIQUE: {scenario}: {inner_tar_names}")
        tar_raw = outer.read(inner_tar_names[0])
    tar_path = scenario_dir / f"{scenario}.tar.gz"
    tar_path.write_bytes(tar_raw)
    extracted = _extract_scenario_inputs_and_cache_p50(tar_raw, scenario_dir)
    metadata_raw = extracted["scenario_metadata.json"]
    trial_parquet = extracted["trial_results.parquet"]
    daily_parquet = extracted["daily_distribution.parquet"]
    fingerprints_raw = extracted["trial_fingerprints.json"]
    maxcase_payload_present = extracted["maxcase_payload_present"]
    scenario_meta = _normalise_scenario_meta(metadata_raw)
    if scenario_meta.get("scenario") != scenario:
        raise RuntimeError(
            f"SCENARIO_METADATA_ID_MISMATCH: expected={scenario}, actual={scenario_meta.get('scenario')}"
        )
    if scenario_meta.get("source_sha") != SOURCE_SHA:
        raise RuntimeError(f"SCENARIO_SOURCE_SHA_MISMATCH: {scenario}")
    official_source_run = str(scenario_meta.get("run_id", ""))
    if official_source_run != str(manifest.get("run_id")):
        raise RuntimeError(
            f"OFFICIAL_SOURCE_RUN_MISMATCH: {scenario}; expected={manifest.get('run_id')}, actual={official_source_run}"
        )
    if scenario_meta.get("global_manifest_sha256") not in (None, manifest.get("global_manifest_sha256")):
        raise RuntimeError(f"SCENARIO_GLOBAL_MANIFEST_MISMATCH: {scenario}")
    count_expected = int(manifest["representative_trials"][scenario]["trial_count"])
    if scenario_meta.get("trial_count") != count_expected:
        raise RuntimeError(
            f"SCENARIO_TRIAL_COUNT_MISMATCH: {scenario}; expected={count_expected}, actual={scenario_meta.get('trial_count')}"
        )
    if scenario_meta.get("reference_sha256") not in (None, REFERENCE_SHA256):
        raise RuntimeError(f"SCENARIO_REFERENCE_SHA256_MISMATCH: {scenario}")
    if scenario == V3_SCENARIO:
        if sha256_bytes(trial_parquet) != V3_TRIAL_PARQUET_SHA256:
            raise RuntimeError("C050_G000_V3_TRIAL_PARQUET_SHA256_MISMATCH")
        if sha256_bytes(fingerprints_raw) != V3_FINGERPRINTS_SHA256:
            raise RuntimeError("C050_G000_V3_FINGERPRINTS_SHA256_MISMATCH")
    (scenario_dir / "scenario_metadata.json").write_bytes(metadata_raw)
    (scenario_dir / "trial_results.parquet").write_bytes(trial_parquet)
    (scenario_dir / "daily_distribution.parquet").write_bytes(daily_parquet)
    (scenario_dir / "trial_fingerprints.json").write_bytes(fingerprints_raw)
    table = pq.read_table(io.BytesIO(trial_parquet))
    rows = table.to_pylist()
    trial_ids = [row.get("trial_id") for row in rows]
    if len(rows) != count_expected or any(type(value) is not int for value in trial_ids):
        raise RuntimeError(f"TRIAL_RESULT_COVERAGE_INVALID: {scenario}; count={len(rows)}")
    if sorted(trial_ids) != list(range(1, count_expected + 1)):
        raise RuntimeError(f"TRIAL_ID_RANGE_INVALID: {scenario}")
    if len(set(trial_ids)) != count_expected:
        raise RuntimeError(f"TRIAL_ID_DUPLICATE: {scenario}")
    for row in rows:
        if row.get("scenario_id") not in (None, scenario):
            raise RuntimeError(f"TRIAL_SCENARIO_BINDING_MISMATCH: {scenario}/{row.get('trial_id')}")
        if "collection_probability" in row and row["collection_probability"] != int(scenario[1:4]) / 100:
            raise RuntimeError(f"TRIAL_COLLECTION_PARAMETER_MISMATCH: {scenario}/{row.get('trial_id')}")
        if "recovery_rate_pct" in row and row["recovery_rate_pct"] != int(scenario[6:9]):
            raise RuntimeError(f"TRIAL_RECOVERY_PARAMETER_MISMATCH: {scenario}/{row.get('trial_id')}")

    return {
        "scenario": scenario,
        "artifact_id": artifact_id,
        "artifact_name": api_meta.get("name"),
        "artifact_bytes": len(raw_zip),
        "artifact_sha256": actual_zip_sha,
        "api_digest": api_digest,
        "artifact_run_id": actual_run_id,
        "producer_branch": workflow_run.get("head_branch"),
        "producer_sha": actual_head_sha,
        "official_source_run_id": official_source_run,
        "source_sha": scenario_meta.get("source_sha"),
        "trial_count": len(rows),
        "trial_id_min": min(trial_ids),
        "trial_id_max": max(trial_ids),
        "trial_ids_unique_contiguous": True,
        "trial_results_parquet_sha256": sha256_bytes(trial_parquet),
        "daily_distribution_parquet_sha256": sha256_bytes(daily_parquet),
        "trial_fingerprints_sha256": sha256_bytes(fingerprints_raw),
        "scenario_metadata_sha256": sha256_bytes(metadata_raw),
        "log_events_metadata": scenario_meta.get("log_events"),
        "maxcase_payload_present": maxcase_payload_present,
        "maxcase": {
            "trial_id": select_maxcase_row(rows)["trial_id"],
            "final_net_project_equity": select_maxcase_row(rows)["final_net_project_equity"],
        },
        "_rows": rows,
        "p50_cache_path": extracted["p50_cache_path"],
        "p50_cache_bytes_gzip": extracted["p50_cache_bytes_gzip"],
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }


def _money(value) -> str:
    dec = Decimal(str(value))
    if dec == dec.to_integral_value():
        return format(dec, ",f")
    return format(dec, ",f")


def _percent(value) -> str:
    return format(Decimal(str(value)) * Decimal(100), ",f") + "%"


def _common_status_lines() -> list[str]:
    return [
        "STATISTICAL_POLICY_LEVEL = FIXED_LOOK_WITH_CS_PENDING",
        "MaxCase = PENDING_DATA_SOURCE (trial_id=60 for C050_G000; see REPRESENTATIVE_CASES for scenario-specific selections)",
        "log_events = PENDING_APPROVAL; V3 metadata used provisionally",
        "Gate A = BLOCKED",
        "Delivery = NOT_ACCEPTED",
        "Release = BLOCKED / NOT_AUTHORIZED",
    ]


def _report_table(rows_by_scenario: dict[str, list[dict]], summaries: dict[str, dict], assignments: dict[str, dict[str, int]], language: str) -> str:
    if language == "ar":
        header = "| السيناريو | التجارب | ربح تراكمي P10 | P50 | P90 | نقد نهائي P50 | نقد نهائي P90 | احتمال الخسارة الوصفي | MaxCase Trial ID | حمولة MaxCase |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"
    else:
        header = "| Scenario | Trials | Cumulative profit P10 | P50 | P90 | Final cash P50 | Final cash P90 | Descriptive loss probability | MaxCase trial ID | MaxCase payload |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"
    lines = [header]
    for scenario in excel_builder.EXPECTED_SCENARIOS:
        s = summaries[scenario]
        lines.append(
            f"| {scenario} | {s['trial_count']} | {_money(s['p10_profit'])} | {_money(s['p50_profit'])} | "
            f"{_money(s['p90_profit'])} | {_money(s['p50_cash'])} | {_money(s['p90_cash'])} | "
            f"{_percent(s['loss_probability'])} | {assignments[scenario]['MaxCase']} | PENDING_DATA_SOURCE |"
        )
    return "\n".join(lines)


def write_reports(
    output_dir: Path,
    dataset_root: Path,
    manifest: dict,
    input_artifacts: dict,
    summaries: dict,
    assignments: dict[str, dict[str, int]],
    total_trials: int,
    tested_sha: str,
    run_id: str,
) -> None:
    rows_by_scenario = {}
    for scenario in excel_builder.EXPECTED_SCENARIOS:
        rows_by_scenario[scenario] = pq.read_table(dataset_root / scenario / "trial_results.parquet").to_pylist()
    table_en = _report_table(rows_by_scenario, summaries, assignments, "en")
    table_ar = _report_table(rows_by_scenario, summaries, assignments, "ar")
    common = "\n".join(_common_status_lines())
    v3 = input_artifacts[V3_SCENARIO]
    provenance_rows = "\n".join(
        f"- {s}: Artifact {input_artifacts[s]['artifact_id']}, producer Run {input_artifacts[s]['artifact_run_id']}, "
        f"producer SHA {input_artifacts[s]['producer_sha']}, ZIP SHA-256 {input_artifacts[s]['artifact_sha256']}"
        for s in excel_builder.EXPECTED_SCENARIOS
    )
    median_sorted = sorted(summaries.items(), key=lambda item: item[1]["p50_profit"], reverse=True)
    loss_sorted = sorted(summaries.items(), key=lambda item: (item[1]["loss_probability"], -item[1]["p50_profit"]))
    top_profit_ar = "\n".join(f"- {s}: P50 للربح التراكمي = {_money(v['p50_profit'])} ريال." for s, v in median_sorted[:5])
    top_loss_ar = "\n".join(f"- {s}: احتمال الخسارة الوصفي = {_percent(v['loss_probability'])}." for s, v in loss_sorted[:5])
    top_profit_en = "\n".join(f"- {s}: cumulative-profit P50 = {_money(v['p50_profit'])} YER." for s, v in median_sorted[:5])
    top_loss_en = "\n".join(f"- {s}: descriptive loss probability = {_percent(v['loss_probability'])}." for s, v in loss_sorted[:5])

    full_ar = f"""# التقرير الكامل — نسخة مرحلية P16 غير مقبولة

## الحالة والحدود
{common}

هذه وثيقة نتائج وصفية مبنية على artifacts محفوظة لهوية المصدر {SOURCE_SHA} والمرجع SHA-256 {REFERENCE_SHA256}. عدد السيناريوهات {len(excel_builder.EXPECTED_SCENARIOS)}، وعدد trial rows المقروءة {total_trials}. لم تُشغّل محاكاة أو Trials أو Monte Carlo أو Confidence Sequences في هذا البناء. أرقام الاحتمال إحصاءات وصفية للعينة وليست ضمانات Confidence Sequence أو إثبات استقرار.

## هوية بناء P16
- branch: tmp/p16-provisional-outputs-20261021
- tested SHA: {tested_sha}
- workflow Run ID: {run_id}
- main HEAD الأساس: {MAIN_HEAD_REQUIRED}
- Main manifest Git blob: {MAIN_MANIFEST_BLOB}
- C050_G000 المصدر المؤقت: Artifact {V3_ARTIFACT_ID}, enrichment Run {V3_RUN_ID}, producer SHA {V3_PRODUCER_SHA}, SHA-256 {V3_ZIP_SHA256}
- القاعدة المعيارية: P10/P50/P90 من Final_Net_Project_Equity، LossCase أقل قيمة مطلقة، MaxCase أعلى قيمة موجبة؛ التعادل بأصغر trial_id.
- Cumulative_Project_Profit = Final_Retained_Earnings وفق §§10.9–10.10 في اللحظة نفسها؛ لا يوجد قرار مالك معلق حول هذه المساواة.

## نتائج السيناريوهات
{table_ar}

## عقد الأدوار
- P10/P50/P90/LossCase: حمولة الأربعة أدوار موجودة لكل سيناريو؛ في C050_G000 القيم المعتمدة مؤقتًا P10=131 (265,600,350)، P50=29 (276,669,500)، P90=18 (288,621,050)، LossCase=304 (249,030,500) من representatives/Loss.json.
- MaxCase في C050_G000: trial_id=60 وقيمة Final_Net_Project_Equity=308,412,450 ريال، أُعيد حسابها من جميع 450 TrialResult في V3؛ قيمة موجبة وحيدة عند الحد الأعلى.
- لا توجد حمولة MaxCase اليومية الخامسة في enrichment artifacts. يظهر صف MaxCase لكل سيناريو مع trial_id المحسوب وحقول الحمولة غير المتاحة موسومة PENDING_DATA_SOURCE، مع تعليق Excel على صف C050_G000 كما طلب المالك.
- أرصدة Partner1_Reinvestment_Balance وPartner2_Reinvestment_Balance غير موجودة في Stage 12 C050_G000 Parquet schema أو في حمولة MaxCase الخامسة المفقودة. تبقى هذه الحقول PENDING_DATA_SOURCE؛ لا تُشتق من Cash أو Equity أو Retained_Earnings.
- ملف LossCase يستخدم الاسم المعياري LossCase ومصدر representatives/Loss.json بصورة صريحة.

## provenance للأدلة المصدرية
{provenance_rows}

## بوابات مفتوحة
Gate A BLOCKED لغياب Golden provider، وSOURCE_SHA_DRIFT لم يُحل، وStage 9C التاريخية PARTIAL/CONFLICTED، وlog_events PENDING_APPROVAL (V3 metadata used provisionally). لا يُعلن SCENARIO_STABLE وفق السياسة الحديثة، ولا يرفع هذا البناء حالة التسليم.
"""
    full_en = f"""# Full report — provisional P16, not accepted

## Status and scope
{common}

This is a descriptive result package using existing artifacts tied to source SHA {SOURCE_SHA} and reference SHA-256 {REFERENCE_SHA256}. It covers {len(excel_builder.EXPECTED_SCENARIOS)} scenarios and {total_trials} loaded trial rows. No simulation, new Trial, Monte Carlo, or Confidence Sequence was run. Loss probabilities are descriptive sample frequencies, not Confidence Sequence guarantees or proof of stability.

## P16 build identity
- branch: tmp/p16-provisional-outputs-20261021
- tested SHA: {tested_sha}
- workflow Run ID: {run_id}
- base main HEAD: {MAIN_HEAD_REQUIRED}
- main manifest Git blob: {MAIN_MANIFEST_BLOB}
- provisional C050_G000 source: Artifact {V3_ARTIFACT_ID}, enrichment Run {V3_RUN_ID}, producer SHA {V3_PRODUCER_SHA}, SHA-256 {V3_ZIP_SHA256}
- normative role selection: P10/P50/P90 by Final_Net_Project_Equity quantiles, LossCase by minimum absolute value, MaxCase by maximum positive value; ties use smallest trial_id.
- Cumulative_Project_Profit = Final_Retained_Earnings under source reference §§10.9–10.10 at the same time; no owner decision is outstanding for that equality.

## Scenario results
{table_en}

## Representative roles
- P10/P50/P90/LossCase payloads are present for all scenarios. For C050_G000, provisionally sourced values are P10=131 (265,600,350), P50=29 (276,669,500), P90=18 (288,621,050), LossCase=304 (249,030,500) from representatives/Loss.json.
- C050_G000 MaxCase is trial_id=60, Final_Net_Project_Equity=308,412,450 YER, independently selected by scanning all 450 TrialResult rows in V3; one trial attains this positive maximum.
- The fifth daily MaxCase payload is absent from the enrichment artifacts. Every scenario receives a MaxCase row with the selected trial_id and unavailable payload fields marked PENDING_DATA_SOURCE; the C050_G000 Excel row contains the owner's exact requested comment.
- Partner1_Reinvestment_Balance and Partner2_Reinvestment_Balance are absent from the Stage 12 C050_G000 Parquet schema and the missing fifth MaxCase payload. They remain PENDING_DATA_SOURCE and are not derived from Cash, Equity, or Retained_Earnings.
- The role is named LossCase while its explicit legacy file source remains representatives/Loss.json.

## Source artifact provenance
{provenance_rows}

## Open gates
Gate A remains BLOCKED because the approved Golden provider is missing; SOURCE_SHA_DRIFT remains unresolved; historical Stage 9C remains PARTIAL/CONFLICTED; and log_events remains PENDING_APPROVAL (V3 metadata used provisionally). This package does not justify a modern SCENARIO_STABLE declaration or change delivery acceptance.
"""
    summary_ar = f"""# الملخص — P16 مرحلي

{common}

- المصدر: {SOURCE_SHA}؛ المرجع: {REFERENCE_SHA256}
- السيناريوهات: 25؛ صفوف TrialResult المقروءة: {total_trials}
- C050_G000: MaxCase trial_id=60، equity=308,412,450 ريال، مثبت من V3 (450 trial).
- أربع حمولات تمثيلية موجودة؛ MaxCase اليومي وأرصدة الشريكين موسومة PENDING_DATA_SOURCE.
- LossCase يرتبط صراحةً بملف representatives/Loss.json.
- لا CS؛ مستوى السياسة الإحصائية هو FIXED_LOOK_WITH_CS_PENDING.
- النتيجة مرحلية، لا تقبل الإنتاج: Gate A BLOCKED، log_events PENDING_APPROVAL، Stage 9C PARTIAL/CONFLICTED، التسليم NOT_ACCEPTED.
"""
    summary_en = f"""# Summary — provisional P16

{common}

- Source: {SOURCE_SHA}; reference: {REFERENCE_SHA256}
- Scenarios: 25; TrialResult rows read: {total_trials}
- C050_G000 MaxCase: trial_id=60, equity=308,412,450 YER, selected from V3's 450 trials.
- Four representative payloads exist; missing MaxCase daily data and partner balances are marked PENDING_DATA_SOURCE.
- LossCase is explicitly mapped to representatives/Loss.json.
- No CS was run; statistical policy level is FIXED_LOOK_WITH_CS_PENDING.
- Provisional only: Gate A BLOCKED, log_events PENDING_APPROVAL, Stage 9C PARTIAL/CONFLICTED, delivery NOT_ACCEPTED.
"""
    feasibility_ar = f"""# دراسة الجدوى العربية — قراءة وصفية مرحلية وليست قبولًا

## حالة الدراسة
{common}

هذه الدراسة تلخص نتائج cohort محفوظ فقط. لا تستبدل الدراسة معيار جدوى تجاريًا غير موجود في المرجع، ولا تعتبر التقديرات الوصفية دليلًا إحصائيًا متتابعًا. لم تُنفذ CS أو محاكاة أو Trial جديد.

## أعلى السيناريوهات بحسب وسيط الربح التراكمي الوصفي
{top_profit_ar}

## أقل احتمالات خسارة وصفية في العينة
{top_loss_ar}

## المؤشرات على مستوى السيناريوهات
{table_ar}

## قيود الاستنتاج
1. الاختيارات والنتائج مرتبطة بالمصدر {SOURCE_SHA} والمرجع {REFERENCE_SHA256} وبـartifacts المثبتة لكل سيناريو؛ ليست نتائج من إعادة تشغيل.
2. مقدار احتمال الخسارة هنا تكرار وصفي للعينة وليس Confidence Sequence، ولا يثبت شرط ثبات عبر الزمن أو التوقف التكيفي.
3. MaxCase اليومي غير متاح في artifacts. معرّف C050_G000 وequity الأقصى مثبتان من جدول TrialResult V3، لكن حقول DAILY المفقودة لا تُختلق.
4. Partner1_Reinvestment_Balance وPartner2_Reinvestment_Balance غير موجودتين ضمن Stage 12 Parquet schema المفحوصة؛ تبقيان PENDING_DATA_SOURCE.
5. Gate A BLOCKED، وSOURCE_SHA_DRIFT قائم، وStage 9C PARTIAL/CONFLICTED، وlog_events PENDING_APPROVAL. لذلك لا يصح إعلان قرار قبول نهائي أو SCENARIO_STABLE من هذه الحزمة.
"""
    files = {
        "التقرير_الكامل_AR": full_ar,
        "Full_Report_EN": full_en,
        "الملخص_AR": summary_ar,
        "Summary_EN": summary_en,
        "دراسة_الجدوى_AR": feasibility_ar,
    }
    for name, text in files.items():
        (output_dir / name).write_text(text, encoding="utf-8", newline="\n")


def _read_cell_value(cell, shared_strings):
    inline = cell.find(f"{{{SHEET_MAIN_NS}}}is")
    if inline is not None:
        text = inline.find(f"{{{SHEET_MAIN_NS}}}t")
        return "" if text is None else text.text or ""
    value = cell.find(f"{{{SHEET_MAIN_NS}}}v")
    if value is None:
        return ""
    if cell.attrib.get("t") == "s" and shared_strings:
        try:
            return shared_strings[int(value.text)]
        except (ValueError, IndexError, TypeError):
            return ""
    return value.text or ""


def _set_inline_string(cell, value: str) -> None:
    from xml.etree import ElementTree as ET
    ns = f"{{{SHEET_MAIN_NS}}}"
    cell.attrib["t"] = "inlineStr"
    for child in list(cell):
        cell.remove(child)
    inline = ET.SubElement(cell, f"{ns}is")
    text = ET.SubElement(inline, f"{ns}t")
    text.text = value


def localize_arabic_readme(source_xlsx: Path, target_xlsx: Path) -> None:
    import xml.etree.ElementTree as ET

    ET.register_namespace("", SHEET_MAIN_NS)
    labels = {
        "Project": "المشروع",
        "Workbook build provenance": "مصدر بناء المصنف",
        "Scenario count": "عدد السيناريوهات",
        "Total trials": "إجمالي التجارب المحفوظة",
        "Total representatives": "حمولات الأدوار المصدرية المؤكدة",
        "MASTER_SEED": "MASTER_SEED",
        "Source SHA": "بصمة المصدر",
        "Official Run ID": "معرّف التشغيل الرسمي",
        "Official Run HEAD SHA": "SHA رأس التشغيل الرسمي",
        "Reference SHA-256": "بصمة المرجع SHA-256",
        "Dataset manifest SHA-256": "بصمة manifest البيانات",
        "Dataset status": "حالة البيانات",
        "Validation status": "حالة التحقق",
        "Excel sheets": "عدد أوراق Excel",
        "Excel error count": "عدد أخطاء Excel",
        "Language": "اللغة",
    }
    values = {
        "Project": "محاكاة تأجير الدراجات النارية — مخرجات مرحلية",
        "Workbook build provenance": "بناء P16 مرحلي من artifacts محفوظة؛ ليس بناء إنتاج نهائي",
        "Dataset status": "مرحلي: حمولة MaxCase اليومية وأرصدة الشريكين غير متاحة",
        "Validation status": "اختبارات اصطناعية وتحقق من هوية الأدلة؛ Gate A ما زالت محجوبة",
        "Language": "العربية؛ أسماء الأوراق وحقول البيانات الفنية محفوظة وفق عقد المصنف",
    }
    with zipfile.ZipFile(source_xlsx, "r") as zin, zipfile.ZipFile(target_xlsx, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zout:
        shared_strings = []
        if "xl/sharedStrings.xml" in zin.namelist():
            root_shared = ET.fromstring(zin.read("xl/sharedStrings.xml"))
            for item in root_shared.findall(f"{{{SHEET_MAIN_NS}}}si"):
                shared_strings.append("".join((t.text or "") for t in item.iter(f"{{{SHEET_MAIN_NS}}}t")))
        for info in zin.infolist():
            if info.filename == "xl/worksheets/sheet1.xml":
                root = ET.fromstring(zin.read(info.filename))
                for row in root.findall(f".//{{{SHEET_MAIN_NS}}}sheetData/{{{SHEET_MAIN_NS}}}row"):
                    a_cell = next((c for c in row.findall(f"{{{SHEET_MAIN_NS}}}c") if c.attrib.get("r", "").startswith("A")), None)
                    b_cell = next((c for c in row.findall(f"{{{SHEET_MAIN_NS}}}c") if c.attrib.get("r", "").startswith("B")), None)
                    if a_cell is None:
                        continue
                    key = _read_cell_value(a_cell, shared_strings)
                    if key in labels:
                        _set_inline_string(a_cell, labels[key])
                        if b_cell is not None and key in values:
                            _set_inline_string(b_cell, values[key])
                payload = ET.tostring(root, encoding="utf-8", xml_declaration=True)
                zout.writestr(info, payload)
            else:
                with zin.open(info, "r") as src, zout.open(info, "w") as dst:
                    shutil.copyfileobj(src, dst, length=1024 * 1024)


def inspect_output(path: Path) -> dict:
    digest = sha256_file(path)
    result = {
        "filename": path.name,
        "bytes": path.stat().st_size,
        "sha256": digest,
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "artifact_id": None,
        "pending_data_source_rows": None,
        "pending_data_source_cells": None,
        "sheet_count": None,
        "excel_error_cells": None,
        "formula_cells": None,
    }
    if path.suffix.lower() == ".xlsx":
        formula_cells = 0
        excel_errors = 0
        pending_cells = 0
        pending_rows = 0
        wb = load_workbook(path, data_only=False, read_only=True)
        try:
            result["sheet_count"] = len(wb.sheetnames)
            expected_sheets = excel_builder.GLOBAL_SHEETS + [
                f"{scenario}{suffix}"
                for scenario in excel_builder.EXPECTED_SCENARIOS
                for suffix in excel_builder.SUFFIXES
            ]
            if wb.sheetnames != expected_sheets or len(wb.sheetnames) != 185:
                raise RuntimeError(f"OUTPUT_SHEET_CONTRACT_FAIL: {path.name}: {len(wb.sheetnames)}")
            for ws in wb.worksheets:
                if ws.title == "REPRESENTATIVE_CASES":
                    headers = next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
                    case_col = headers.index("case")
                    record_col = headers.index("record_type")
                    row_count = 0
                    for row in ws.iter_rows(min_row=2, values_only=True):
                        if row[case_col] == "MaxCase" and row[record_col] == "PENDING_DATA_SOURCE":
                            row_count += 1
                        pending_cells += sum(1 for value in row if value == "PENDING_DATA_SOURCE")
                    pending_rows = row_count
                for row in ws.iter_rows():
                    for cell in row:
                        if cell.data_type == "f":
                            formula_cells += 1
                        elif cell.data_type == "e":
                            excel_errors += 1
                        if cell.value == "PENDING_DATA_SOURCE":
                            pending_cells += 0
        finally:
            wb.close()
        result["pending_data_source_rows"] = pending_rows
        result["pending_data_source_cells"] = pending_cells
        result["formula_cells"] = formula_cells
        result["excel_error_cells"] = excel_errors
        if formula_cells != 0 or excel_errors != 0:
            raise RuntimeError(f"OUTPUT_EXCEL_ERROR_OR_FORMULA: {path.name}: f={formula_cells}, e={excel_errors}")
        if pending_rows != EXPECTED_PENDING_CASES:
            raise RuntimeError(f"MAXCASE_PENDING_ROW_COUNT_MISMATCH: {path.name}: {pending_rows}")
        with zipfile.ZipFile(path, "r") as zf:
            comment_xml = [name for name in zf.namelist() if "comment" in name.lower() and name.endswith(".xml")]
            all_comments = "\n".join(zf.read(name).decode("utf-8", errors="replace") for name in comment_xml)
            if "MaxCase trial_id=60; daily payload missing from V3" not in all_comments:
                raise RuntimeError(f"MAXCASE_COMMENT_MISSING: {path.name}")
        result["artifact_id"] = "see workflow run artifact record"
    else:
        raw = path.read_text(encoding="utf-8")
        result["pending_data_source_rows"] = sum(1 for line in raw.splitlines() if "PENDING_DATA_SOURCE" in line)
        result["pending_data_source_cells"] = None
    return result


def _translate_arabic_readme_file(source: Path, target: Path) -> None:
    localize_arabic_readme(source, target)
    # Verify the workbook remains readable and keeps its 185-sheet identity after XML-only localization.
    wb = load_workbook(target, read_only=True, data_only=False)
    try:
        expected = excel_builder.GLOBAL_SHEETS + [
            f"{scenario}{suffix}"
            for scenario in excel_builder.EXPECTED_SCENARIOS
            for suffix in excel_builder.SUFFIXES
        ]
        if len(wb.sheetnames) != 185 or wb.sheetnames != expected:
            raise RuntimeError("ARABIC_WORKBOOK_SHEET_CONTRACT_FAIL")
    finally:
        wb.close()


def main() -> int:
    output_dir = Path("deliverables")
    work_dir = Path("p16_work")
    dataset_root = work_dir / "dataset"
    output_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    evidence = {
        "schema_version": "1.0",
        "status": "RUNNING",
        "branch": os.environ.get("GITHUB_REF_NAME"),
        "tested_sha": os.environ.get("GITHUB_SHA"),
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "base_main_sha": MAIN_HEAD_REQUIRED,
        "source_sha": SOURCE_SHA,
        "reference_sha256": REFERENCE_SHA256,
        "main_manifest_expected_git_blob": MAIN_MANIFEST_BLOB,
        "started_at_utc": now_utc(),
        "simulation_or_trial_generation": False,
        "monte_carlo": False,
        "confidence_sequences": False,
        "main_modified": False,
        "source_data_modified": False,
        "parquet_modified": False,
        "inputs": {},
        "maxcase_by_scenario": {},
        "outputs": {},
    }
    evidence_path = output_dir / "p16_build_evidence.json"
    manifest_out_path = output_dir / "output_manifest.json"
    try:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise RuntimeError("GITHUB_TOKEN_UNAVAILABLE")
        main_ref = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        if main_ref != evidence["tested_sha"]:
            raise RuntimeError(f"TESTED_SHA_MISMATCH: expected={evidence['tested_sha']}, actual={main_ref}")
        manifest_path = Path("docs/stage9a/dataset_manifest.json")
        actual_manifest_blob = git_blob_sha(manifest_path)
        if actual_manifest_blob != MAIN_MANIFEST_BLOB:
            raise RuntimeError(
                f"MAIN_MANIFEST_BLOB_MISMATCH: expected={MAIN_MANIFEST_BLOB}, actual={actual_manifest_blob}"
            )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("source_sha") != SOURCE_SHA or manifest.get("reference_sha256") != REFERENCE_SHA256:
            raise RuntimeError("MAIN_MANIFEST_SOURCE_OR_REFERENCE_MISMATCH")
        if manifest.get("global_manifest_sha256") != "892da438955160bb59aff3046271402f57bdd61a4abb35f41db7188f61346ff6":
            raise RuntimeError("MAIN_MANIFEST_GLOBAL_IDENTITY_MISMATCH")
        if list(sorted(manifest.get("scenarios", {}))) != list(sorted(excel_builder.EXPECTED_SCENARIOS)):
            raise RuntimeError("MAIN_MANIFEST_SCENARIO_SET_MISMATCH")

        expected_runs = manifest["artifact_manifest"]["enrichment_run_ids"]
        scenario_artifacts = manifest["artifact_manifest"]["enriched_artifacts"]
        artifact_evidence = {}
        all_rows = {}
        assignments = {}
        maxcase_records = {}
        _progress(
            "build_start",
            branch=evidence["branch"],
            tested_sha=evidence["tested_sha"],
            run_id=evidence["run_id"],
            scenario_count=len(excel_builder.EXPECTED_SCENARIOS),
            dataset_disk_free_bytes=shutil.disk_usage(work_dir).free,
        )
        for scenario_index, scenario in enumerate(excel_builder.EXPECTED_SCENARIOS, start=1):
            if scenario == V3_SCENARIO:
                artifact_id, expected_run = V3_ARTIFACT_ID, V3_RUN_ID
            else:
                artifact_id = int(scenario_artifacts[scenario])
                expected_run = int(expected_runs[scenario])
            _progress(
                "scenario_acquisition_start",
                index=scenario_index,
                total=len(excel_builder.EXPECTED_SCENARIOS),
                scenario=scenario,
                artifact_id=artifact_id,
            )
            entry = fetch_scenario_artifact(
                scenario=scenario,
                artifact_id=artifact_id,
                expected_artifact_run_id=expected_run,
                dataset_root=dataset_root,
                token=token,
                manifest=manifest,
            )
            rows = entry.pop("_rows")
            entry["manifest_expected_artifact_id"] = int(scenario_artifacts[scenario])
            entry["manifest_expected_run_id"] = int(expected_runs[scenario])
            entry["runtime_v3_override"] = scenario == V3_SCENARIO
            artifact_evidence[scenario] = entry
            all_rows[scenario] = rows
            max_row = select_maxcase_row(rows)
            maxcase_records[scenario] = {
                "trial_id": max_row["trial_id"],
                "final_net_project_equity": max_row["final_net_project_equity"],
                "positive_trial_count": sum(1 for r in rows if r["final_net_project_equity"] > 0),
                "tie_count_at_maximum": sum(
                    1 for r in rows
                    if r["final_net_project_equity"] == max_row["final_net_project_equity"]
                ),
                "daily_payload_status": "PENDING_DATA_SOURCE",
            }
            source_roles = manifest["representative_trials"][scenario]
            assignments[scenario] = {
                "P10": int(source_roles["P10"]),
                "P50": int(source_roles["P50"]),
                "P90": int(source_roles["P90"]),
                "LossCase": int(source_roles["Loss"]),
                "MaxCase": int(max_row["trial_id"]),
            }
            if scenario == V3_SCENARIO:
                expected_fixed = {"P10": 131, "P50": 29, "P90": 18, "LossCase": 304, "MaxCase": 60}
                if assignments[scenario] != expected_fixed:
                    raise RuntimeError(f"C050_G000_ROLE_SELECTION_MISMATCH: {assignments[scenario]}")
                if max_row["final_net_project_equity"] != 308412450:
                    raise RuntimeError(f"C050_G000_MAXCASE_VALUE_MISMATCH: {max_row['final_net_project_equity']}")
            _progress(
                "scenario_acquisition_complete",
                index=scenario_index,
                total=len(excel_builder.EXPECTED_SCENARIOS),
                scenario=scenario,
                artifact_bytes=entry["artifact_bytes"],
                p50_cache_bytes_gzip=entry["p50_cache_bytes_gzip"],
                p50_json_bytes_raw=entry["p50_cache_bytes_raw"] if "p50_cache_bytes_raw" in entry else None,
                trial_rows=len(rows),
                elapsed_seconds=entry["elapsed_seconds"],
                disk_free_bytes=shutil.disk_usage(dataset_root).free,
            )
        total_trials = sum(len(rows) for rows in all_rows.values())
        if total_trials != int(manifest["total_trials"]):
            raise RuntimeError(f"TOTAL_TRIAL_COVERAGE_MISMATCH: expected={manifest['total_trials']}, actual={total_trials}")
        evidence["inputs"] = artifact_evidence
        evidence["maxcase_by_scenario"] = maxcase_records
        evidence["total_trial_rows"] = total_trials
        evidence["scenario_count"] = len(all_rows)
        evidence["main_manifest_git_blob"] = actual_manifest_blob
        evidence["dataset_status"] = "PROVISIONAL_EXISTING_ARTIFACTS_ONLY"
        _progress("source_acquisition_complete", scenario_count=len(all_rows), total_trials=total_trials, disk_free_bytes=shutil.disk_usage(dataset_root).free)

        # Keep the on-disk main manifest and its identity unchanged. This is an in-memory annotation.
        runtime_manifest = dict(manifest)
        runtime_manifest["dataset_status"] = "PROVISIONAL: missing MaxCase payload/partner balances; Gate A blocked"
        runtime_manifest["scenarios"] = {scenario: {**details, "final_status": "PROVISIONAL_PENDING_GATES"} for scenario, details in manifest["scenarios"].items()}
        runtime_manifest_path = work_dir / "runtime_manifest.json"
        runtime_manifest_path.write_text(json.dumps(runtime_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        assignments_path = work_dir / "representative_trial_ids.json"
        assignments_path.write_text(json.dumps({"scenarios": assignments}, indent=2) + "\n", encoding="utf-8")

        # The workbook builder reads the compact parquet rows to compute the 185-sheet result book.
        result_en = output_dir / "Full_Results_EN.xlsx"
        _progress("workbook_build_start", output_path=str(result_en), scenario_count=len(all_rows), total_trials=total_trials, disk_free_bytes=shutil.disk_usage(dataset_root).free)
        workbook_started = time.monotonic()
        build_result = excel_builder.build_workbook(
            str(dataset_root), str(result_en), str(runtime_manifest_path), str(assignments_path),
            role_to_payload_labels=ROLE_MAP,
        )
        if build_result.get("success") is not True or build_result.get("sheets_count") != 185:
            raise RuntimeError(f"ENGLISH_WORKBOOK_BUILD_FAILED: {build_result}")
        evidence["workbook_build"] = build_result
        _progress("workbook_build_complete", success=build_result.get("success"), sheets_count=build_result.get("sheets_count"), file_bytes=build_result.get("file_bytes"), elapsed_seconds=round(time.monotonic() - workbook_started, 3))
        result_ar = output_dir / "النتائج_الكاملة_AR.xlsx"
        _progress("arabic_workbook_translation_start")
        _translate_arabic_readme_file(result_en, result_ar)
        _progress("arabic_workbook_translation_complete", file_bytes=result_ar.stat().st_size)

        summaries = excel_builder.build_scenario_summary(all_rows)
        _progress("reports_start")
        write_reports(
            output_dir, dataset_root, manifest, artifact_evidence, summaries, assignments,
            total_trials, evidence["tested_sha"], evidence["run_id"],
        )
        _progress("reports_complete", expected_output_count=len(OUTPUT_NAMES))
        missing = [name for name in OUTPUT_NAMES if not (output_dir / name).is_file()]
        if missing:
            raise RuntimeError(f"DELIVERABLE_FILES_MISSING: {missing}")

        # Independent post-write read-back of each deliverable, including 185 sheets and pending rows.
        for output_index, name in enumerate(OUTPUT_NAMES, start=1):
            _progress("output_readback_start", index=output_index, total=len(OUTPUT_NAMES), name=name)
            evidence["outputs"][name] = inspect_output(output_dir / name)
            _progress("output_readback_complete", index=output_index, total=len(OUTPUT_NAMES), name=name, bytes=evidence["outputs"][name].get("bytes"), sha256=evidence["outputs"][name].get("sha256"))
        evidence["status"] = "PASS_SCOPED_PROVISIONAL_OUTPUTS_NOT_ACCEPTED"
        evidence["finished_at_utc"] = now_utc()
        output_manifest = {
            "schema_version": "1.0",
            "status": evidence["status"],
            "branch": evidence["branch"],
            "tested_sha": evidence["tested_sha"],
            "run_id": evidence["run_id"],
            "base_main_sha": MAIN_HEAD_REQUIRED,
            "source_sha": SOURCE_SHA,
            "reference_sha256": REFERENCE_SHA256,
            "main_manifest_git_blob": actual_manifest_blob,
            "cohort_total_trials": total_trials,
            "scenario_count": len(all_rows),
            "statistical_policy_level": "FIXED_LOOK_WITH_CS_PENDING",
            "gate_a": "BLOCKED",
            "log_events": "PENDING_APPROVAL; V3 metadata used provisionally",
            "delivery": "NOT_ACCEPTED",
            "release": "BLOCKED / NOT_AUTHORIZED",
            "seven_files": evidence["outputs"],
            "input_artifacts": {
                scenario: {
                    key: value for key, value in entry.items()
                    if key not in {"runtime_v3_override", "manifest_expected_artifact_id", "manifest_expected_run_id"}
                } | {
                    "manifest_expected_artifact_id": entry["manifest_expected_artifact_id"],
                    "manifest_expected_run_id": entry["manifest_expected_run_id"],
                    "runtime_v3_override": entry["runtime_v3_override"],
                }
                for scenario, entry in artifact_evidence.items()
            },
            "maxcase_by_scenario": maxcase_records,
            "loss_case_mapping": "LossCase -> representatives/Loss.json",
            "unresolved_fields": [
                "MaxCase daily payload",
                "Partner1_Reinvestment_Balance for MaxCase",
                "Partner2_Reinvestment_Balance for MaxCase",
            ],
        }
        manifest_out_path.write_text(json.dumps(output_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _progress("build_complete", status=evidence["status"], outputs=len(evidence["outputs"]), total_trials=total_trials, disk_free_bytes=shutil.disk_usage(output_dir).free)
        print(json.dumps({"status": evidence["status"], "outputs": evidence["outputs"], "total_trials": total_trials}, ensure_ascii=False, indent=2), flush=True)
        return 0
    except Exception as exc:
        _progress("build_error", error_type=type(exc).__name__, error=str(exc), disk_free_bytes=shutil.disk_usage(output_dir).free)
        evidence["status"] = "BLOCKED"
        evidence["error_type"] = type(exc).__name__
        evidence["error"] = str(exc)
        evidence["finished_at_utc"] = now_utc()
        evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        manifest_out_path.write_text(json.dumps({
            "schema_version": "1.0",
            "status": "BLOCKED",
            "branch": evidence.get("branch"),
            "tested_sha": evidence.get("tested_sha"),
            "run_id": evidence.get("run_id"),
            "error_type": evidence["error_type"],
            "error": evidence["error"],
            "partial_inputs": evidence.get("inputs", {}),
            "delivery": "NOT_ACCEPTED",
            "release": "BLOCKED / NOT_AUTHORIZED",
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "BLOCKED", "error": evidence["error"]}, ensure_ascii=False), flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
