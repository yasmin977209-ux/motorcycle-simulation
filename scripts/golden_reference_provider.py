"""Read-only provider for the approved Gate A exact per-trial golden fingerprints.

The provider rebuilds its map from immutable, digest-pinned GitHub Actions evidence.
It never runs Monte Carlo trials or writes historical datasets.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import zipfile
from dataclasses import asdict, is_dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, Mapping

REPOSITORY = "yasmin977209-ux/motorcycle-simulation"
APPROVED_SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
MASTER_SEED = 20270101
DECISION_ID = "D-2026-10-14-01"
EXPECTED_CANONICAL_MAP_SHA256 = "7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44"
EXPECTED_N600_MAP_SHA256 = "dd537fe96c5a8736201441e9a620db148a0d16cadae518d2a777fbc723db395f"
EXPECTED_N1200_MAP_SHA256 = "eaf1f8f3060aac6967b064d3199c082d2a9b47027c865628986f56cbb23c1fc3"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

GATE_A_RUN_ID = 38169163565
GATE_A_RUN_HEAD = "95288a2bccb40d6772f5a5d042fdabc152c9d89a"
N600_RUN_ID = 38174743440
N600_RUN_HEAD = "61ae9e2354ff37b1d4d9d13849bd6b264cf9cfa3"
N600_REPORT_ARTIFACT_ID = 11715388165
N600_REPORT_ARTIFACT_NAME = "gateb-historical-and-new-n600-report"
N600_REPORT_ZIP_SHA256 = "67d5033a67eec27bd7a90b735c56f7f7ceff4181e32c88271dd07f39f3b8e8ae"
N1200_RUN_ID = 38179919488
N1200_RUN_HEAD = "54822f2737fc8e474239598ea15d47ae0f55cb4e"
N1200_REPORT_ARTIFACT_ID = 11717929259
N1200_REPORT_ARTIFACT_NAME = "gateb-n1200-checkpoint-report"
N1200_REPORT_ZIP_SHA256 = "17391caa64a7ed0fb7f3819a5df2f3b69bee982fb16060f3c542c84370bee7c0"
N1200_UPSTREAM_CANCELLED_RUN_ID = 38178068848
N1200_UPSTREAM_CANCELLED_RUN_HEAD = "dae9cd6d5ba639ad2265a6d52a1b086a2c9dbe95"

SCENARIOS = tuple(
    f"C{collection:03d}_G{recovery:03d}"
    for collection in (100, 85, 70, 50, 30)
    for recovery in (100, 70, 50, 30, 0)
)
NON_C100_SCENARIOS = tuple(s for s in SCENARIOS if not s.startswith("C100_"))

# Artifact IDs and archive digests are pinned to the live, successful Gate A bridge run.
GATE_A_SCENARIO_ARTIFACTS: dict[str, tuple[int, str]] = {
    "C100_G000": (11713800278, "1da3692137f1c40a6a79082eb690061540822c2bab386020ac2bde39e0570dbd"),
    "C100_G030": (11713285854, "3df8e6a5d438c0ba34cd3076549d945e2f465a3ddda02ecf95da0d5ab0741304"),
    "C100_G050": (11712314933, "a82f6ea7a0099d06de10fa5661c4178a7ffeda5a2e8442b5832cd49d125e8463"),
    "C100_G070": (11713610994, "42106a5c87d518192b12da385bf858a3c6e245b0712ab2ff271ab0ce0561ed13"),
    "C100_G100": (11713710440, "5a51cddd264d96feab81bdbb822adb6ccb8148f76ade3385e4627907e3a100e7"),
    "C085_G000": (11713780771, "1e5a3f526718935d0caafedf19fec2715780263a94b6b6a22d76fc979e0af1c7"),
    "C085_G030": (11713196840, "33158c1741b4ba1ca67bbe3080fb75bb9ac4db454243485e3162c61c9ef57ca7"),
    "C085_G050": (11713750919, "ccf0a3e0104c0e9f2a71d656204d0f1d8f3ae843d19490273d4e1db694d1e8e8"),
    "C085_G070": (11713291505, "c78b64f419a58c83d4dd87a1efdadeea6da99d71555a2b67858c3741a8938192"),
    "C085_G100": (11713122067, "88392022ab36e3097a5a10dec064d7c462884d81504669c009c86b8881b30493"),
    "C070_G000": (11714070352, "f47f7858617a916f9f3b9889e6427660831879ccd80bd2e13f304a387ae85616"),
    "C070_G030": (11713850642, "869175319bb67de5ffcc8169ba86361c2819bd23cc16caabacaea7ad506e109c"),
    "C070_G050": (11713166224, "99c2d94eff7857945927fb8bbda4439bf460a0da938234dd1dfcfe1cd3d43cdc"),
    "C070_G070": (11713955486, "edfe3936b76cdcc06624cde4830b90abd2ee7533d06986b7a2de5afc9866ae6d"),
    "C070_G100": (11713441308, "f06b1e1c2ccf32599c6ac894bda64746deeae9ca8c6092538fd1b9fc4df3c8b1"),
    "C050_G000": (11713071539, "fb81c05c6e6e54ffeb85f08ebe3243abd5384cfca72ab4af690ffbf4c5f0bf3f"),
    "C050_G030": (11713780899, "23b27808cbb4d7c1501358953ebad53cc9f8446b8ae9a948dc0bc9f18d719aad"),
    "C050_G050": (11713751043, "295e0039a0c187a9c5b9c106c4179caa5390353d2b30ebc4d9c7e58c1fc0001b"),
    "C050_G070": (11713556234, "b3c44ef3dcddcb59191215073b64413ad02569242d19ff68bfe1afd0663c5c3a"),
    "C050_G100": (11712974806, "842f51219fea4554cfbc9f33b35542a7144ab03be3831e3260f673b33858953f"),
    "C030_G000": (11713490832, "5f8b16d10db08b37eb0d26017a21af5cfeb98d0d2c0cc33752b37cdaaccb9450"),
    "C030_G030": (11713226122, "6524a3e1c0f91734c6e08ebd65c187d9075922f543d21c49e115b1ba5537cfc0"),
    "C030_G050": (11713486473, "bd961651b8f08571de50e0216bb3c07d017b2bceb10ba7847f747d6c8e05c36e"),
    "C030_G070": (11714150171, "7b8514bd3bd1c492e6459e7d78b00cf27e7f85bd07265b37b2ebec1aa2951176"),
    "C030_G100": (11713445830, "8adb75bfeff6b1998d4d24ce7e8ff0bf8c752b00cd2fa0294a74cc4e15a8eed0"),
}

# These runs are explicitly disclosed by the approved N=1200 report's trial-output map.
UPSTREAM_RUNS = {
    N1200_UPSTREAM_CANCELLED_RUN_ID: {
        "head_sha": N1200_UPSTREAM_CANCELLED_RUN_HEAD,
        "conclusion": "cancelled",
    },
    N1200_RUN_ID: {
        "head_sha": N1200_RUN_HEAD,
        "conclusion": "success",
    },
}

def _valid_sha256(value: Any, context: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise RuntimeError(f"INVALID_GOLDEN_SHA256:{context}")
    return value

def _ordered_map_sha256(
    fingerprints: Mapping[str, Mapping[int, str]],
) -> str:
    payload = "".join(
        f"{scenario}|{trial_id}|{fingerprints[scenario][trial_id]}\n"
        for scenario in sorted(fingerprints)
        for trial_id in sorted(fingerprints[scenario])
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def stage10_trial_result_sha256(result: Any) -> str:
    """Hash one TrialResult exactly as Stage 10's per-trial result_sha does."""
    if is_dataclass(result):
        value = asdict(result)
    elif isinstance(result, dict):
        value = result
    else:
        raise TypeError("trial result must be a dataclass instance or dict")
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

def _gh_json(endpoint: str, token: str) -> dict[str, Any]:
    env = os.environ.copy()
    env["GH_TOKEN"] = token
    completed = subprocess.run(
        ["gh", "api", endpoint],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(
            f"GITHUB_API_READ_FAILED:{endpoint}:"
            f"{completed.stderr[-1200:]}"
        )
    value = json.loads(completed.stdout)
    if not isinstance(value, dict):
        raise RuntimeError(f"GITHUB_API_RESPONSE_NOT_OBJECT:{endpoint}")
    return value

def _verify_run(
    run_id: int,
    expected_head: str,
    expected_conclusion: str,
    token: str,
) -> dict[str, Any]:
    run = _gh_json(f"repos/{REPOSITORY}/actions/runs/{run_id}", token)
    if (
        int(run.get("id", -1)) != run_id
        or run.get("head_sha") != expected_head
        or run.get("status") != "completed"
        or run.get("conclusion") != expected_conclusion
    ):
        raise RuntimeError(f"GOLDEN_RUN_IDENTITY_MISMATCH:{run_id}")
    return run

def _artifact_index(run_id: int, token: str) -> dict[str, dict[str, Any]]:
    response = _gh_json(
        f"repos/{REPOSITORY}/actions/runs/{run_id}/artifacts?per_page=100",
        token,
    )
    artifacts = response.get("artifacts")
    if (
        not isinstance(artifacts, list)
        or int(response.get("total_count", -1)) != len(artifacts)
    ):
        raise RuntimeError(f"GOLDEN_ARTIFACT_LIST_INCOMPLETE:{run_id}")
    index: dict[str, dict[str, Any]] = {}
    for artifact in artifacts:
        name = artifact.get("name")
        if artifact.get("expired") or not name:
            continue
        if name in index:
            raise RuntimeError(f"DUPLICATE_GOLDEN_ARTIFACT_NAME:{run_id}:{name}")
        workflow_run = artifact.get("workflow_run") or {}
        if workflow_run and int(workflow_run.get("id", -1)) != run_id:
            raise RuntimeError(f"GOLDEN_ARTIFACT_WRONG_RUN:{run_id}:{name}")
        index[name] = artifact
    return index

def _download_artifact_bytes(
    *,
    run_id: int,
    artifact_index: Mapping[str, Mapping[str, Any]],
    artifact_name: str,
    artifact_id: int,
    expected_sha256: str,
    token: str,
) -> bytes:
    item = artifact_index.get(artifact_name)
    if (
        item is None
        or int(item.get("id", -1)) != artifact_id
        or str(item.get("digest", "")).removeprefix("sha256:") != expected_sha256
        or item.get("expired") is not False
    ):
        raise RuntimeError(f"GOLDEN_ARTIFACT_IDENTITY_MISMATCH:{run_id}:{artifact_name}")
    env = os.environ.copy()
    env["GH_TOKEN"] = token
    with tempfile.TemporaryDirectory(prefix="gate-a-golden-") as tmp:
        path = Path(tmp) / "artifact.zip"
        with path.open("wb") as stream:
            completed = subprocess.run(
                ["gh", "api", f"repos/{REPOSITORY}/actions/artifacts/{artifact_id}/zip"],
                env=env,
                stdout=stream,
                stderr=subprocess.PIPE,
                check=False,
            )
        if completed.returncode:
            raise RuntimeError(
                f"GOLDEN_ARTIFACT_DOWNLOAD_FAILED:{artifact_id}:"
                f"{completed.stderr.decode('utf-8', errors='replace')[-1200:]}"
            )
        raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected_sha256:
        raise RuntimeError(
            f"GOLDEN_ARTIFACT_DIGEST_MISMATCH:{artifact_id}:"
            f"expected={expected_sha256}:actual={actual}"
        )
    if not zipfile.is_zipfile(BytesIO(raw)):
        raise RuntimeError(f"GOLDEN_ARTIFACT_NOT_ZIP:{artifact_id}")
    return raw

def _single_json_member(raw_zip: bytes, expected_name: str) -> dict[str, Any]:
    with zipfile.ZipFile(BytesIO(raw_zip)) as archive:
        names = archive.namelist()
        if names != [expected_name]:
            raise RuntimeError(
                f"GOLDEN_ARTIFACT_MEMBER_MISMATCH:{expected_name}:{names}"
            )
        data = json.loads(archive.read(expected_name).decode("utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"GOLDEN_ARTIFACT_JSON_ROOT_INVALID:{expected_name}")
    return data

def _load_approved_reference() -> dict[str, Any]:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GOLDEN_PROVIDER_TOKEN_MISSING")
    try:
        subprocess.run(
            ["gh", "--version"],
            env={**os.environ, "GH_TOKEN": token},
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("GOLDEN_PROVIDER_GH_CLI_UNAVAILABLE") from exc

    _verify_run(GATE_A_RUN_ID, GATE_A_RUN_HEAD, "success", token)
    _verify_run(N600_RUN_ID, N600_RUN_HEAD, "success", token)
    _verify_run(N1200_RUN_ID, N1200_RUN_HEAD, "success", token)
    _verify_run(
        N1200_UPSTREAM_CANCELLED_RUN_ID,
        N1200_UPSTREAM_CANCELLED_RUN_HEAD,
        "cancelled",
        token,
    )
    gate_a_artifacts = _artifact_index(GATE_A_RUN_ID, token)
    n600_artifacts = _artifact_index(N600_RUN_ID, token)
    n1200_artifacts = _artifact_index(N1200_RUN_ID, token)

    fingerprints: dict[str, dict[int, str]] = {}
    for scenario in SCENARIOS:
        if scenario not in GATE_A_SCENARIO_ARTIFACTS:
            raise RuntimeError(f"GOLDEN_SCENARIO_ARTIFACT_MISSING:{scenario}")
        artifact_id, digest = GATE_A_SCENARIO_ARTIFACTS[scenario]
        report = _single_json_member(
            _download_artifact_bytes(
                run_id=GATE_A_RUN_ID,
                artifact_index=gate_a_artifacts,
                artifact_name=f"gatea-scenario-{scenario}",
                artifact_id=artifact_id,
                expected_sha256=digest,
                token=token,
            ),
            f"{scenario}.json",
        )
        expected_count = 1 if scenario.startswith("C100_") else 550
        provenance = report.get("run_provenance") or {}
        stage7 = provenance.get("stage7") or {}
        stage10 = provenance.get("stage10") or {}
        stage12 = provenance.get("stage12") or {}
        checks = (
            report.get("scenario") == scenario,
            report.get("status") == "PASS",
            report.get("source_sha") == APPROVED_SOURCE_SHA,
            report.get("master_seed") == MASTER_SEED,
            report.get("source_golden_trial_count") == expected_count,
            report.get("exact_trial_comparisons") == expected_count,
            report.get("hash_mismatch_count") == 0,
            report.get("simulation_or_trial_executed") is False,
            report.get("historical_dataset_modified") is False,
            report.get("historical_artifacts_modified") is False,
            stage7.get("id") == 37225915321,
            stage7.get("head_sha") == "e0b2fab6710833774937d778097363d7a8ee8e59",
            stage7.get("conclusion") == "success",
            stage10.get("id") == 37709936740,
            stage10.get("head_sha") == "ca73f2df37baacebbcad965fc5f433f129675820",
            stage12.get("id") == 37964656154,
            stage12.get("head_sha") == "0156c5f4272eb0ca7e32442657d0df9eaf4973d3",
            report.get("stage10_identity_metadata_deviation", {}).get("classification") == "K_CODE",
            report.get("stage10_identity_metadata_deviation", {}).get("matches_live_run") is False,
        )
        if not all(checks):
            raise RuntimeError(f"GOLDEN_CANONICAL_REPORT_IDENTITY_FAIL:{scenario}")
        rows = report.get("trial_comparisons")
        if not isinstance(rows, list) or len(rows) != expected_count:
            raise RuntimeError(f"GOLDEN_CANONICAL_ROWS_MISSING:{scenario}")
        values: dict[int, str] = {}
        for row in rows:
            trial_id = int(row.get("trial_id", -1))
            value = _valid_sha256(row.get("golden_sha256"), f"{scenario}/{trial_id}")
            if (
                row.get("exact_match") is not True
                or row.get("stage12_sha256") != value
                or trial_id in values
            ):
                raise RuntimeError(f"GOLDEN_CANONICAL_ROW_MISMATCH:{scenario}/{trial_id}")
            values[trial_id] = value
        if sorted(values) != list(range(1, expected_count + 1)):
            raise RuntimeError(f"GOLDEN_CANONICAL_COVERAGE_FAIL:{scenario}")
        fingerprints[scenario] = values

    if sum(map(len, fingerprints.values())) != 11005:
        raise RuntimeError("GOLDEN_CANONICAL_TOTAL_COUNT_MISMATCH")
    if _ordered_map_sha256(fingerprints) != EXPECTED_CANONICAL_MAP_SHA256:
        raise RuntimeError("GOLDEN_CANONICAL_AGGREGATE_SHA_MISMATCH")

    n600_report = _single_json_member(
        _download_artifact_bytes(
            run_id=N600_RUN_ID,
            artifact_index=n600_artifacts,
            artifact_name=N600_REPORT_ARTIFACT_NAME,
            artifact_id=N600_REPORT_ARTIFACT_ID,
            expected_sha256=N600_REPORT_ZIP_SHA256,
            token=token,
        ),
        "gate_b_n600_report.json",
    )
    if not (
        n600_report.get("status") == "PASS"
        and n600_report.get("checkpoint") == "N=600"
        and n600_report.get("source_sha") == APPROVED_SOURCE_SHA
        and n600_report.get("master_seed") == MASTER_SEED
        and n600_report.get("new_trial_run_id") == N600_RUN_ID
        and n600_report.get("new_trials_expected") == 1000
        and n600_report.get("new_trials_verified") == 1000
        and n600_report.get("historical_inputs_expected") == 11000
        and n600_report.get("historical_inputs_verified") == 11000
        and n600_report.get("no_historical_trial_rerun") is True
        and n600_report.get("historical_dataset_modified") is False
        and n600_report.get("historical_metadata_modified") is False
        and n600_report.get("historical_identity_changed") is False
    ):
        raise RuntimeError("GOLDEN_N600_REPORT_IDENTITY_FAIL")
    non_c100_n600 = {
        scenario: dict(values)
        for scenario, values in fingerprints.items()
        if not scenario.startswith("C100_")
    }
    reported_n600_scenarios = {
        item.get("scenario_id"): item for item in n600_report.get("scenarios", [])
    }
    if set(reported_n600_scenarios) != set(NON_C100_SCENARIOS):
        raise RuntimeError("GOLDEN_N600_SCENARIO_COVERAGE_FAIL")
    for scenario in NON_C100_SCENARIOS:
        report_scenario = reported_n600_scenarios[scenario]
        rows = report_scenario.get("new_trial_attempts")
        if not isinstance(rows, list) or len(rows) != 50:
            raise RuntimeError(f"GOLDEN_N600_NEW_TRIAL_COUNT_FAIL:{scenario}")
        values: dict[int, str] = {}
        for row in rows:
            trial_id = int(row.get("trial_id", -1))
            value = _valid_sha256(row.get("result_sha256"), f"{scenario}/{trial_id}")
            if (
                row.get("run_id") != N600_RUN_ID
                or row.get("source_commit") != "0156c5f4272eb0ca7e32442657d0df9eaf4973d3"
                or trial_id in values
            ):
                raise RuntimeError(f"GOLDEN_N600_TRIAL_PROVENANCE_FAIL:{scenario}/{trial_id}")
            values[trial_id] = value
        if sorted(values) != list(range(551, 601)):
            raise RuntimeError(f"GOLDEN_N600_TRIAL_COVERAGE_FAIL:{scenario}")
        non_c100_n600[scenario].update(values)
    if _ordered_map_sha256(non_c100_n600) != EXPECTED_N600_MAP_SHA256:
        raise RuntimeError("GOLDEN_N600_AGGREGATE_SHA_MISMATCH")

    n1200_report = _single_json_member(
        _download_artifact_bytes(
            run_id=N1200_RUN_ID,
            artifact_index=n1200_artifacts,
            artifact_name=N1200_REPORT_ARTIFACT_NAME,
            artifact_id=N1200_REPORT_ARTIFACT_ID,
            expected_sha256=N1200_REPORT_ZIP_SHA256,
            token=token,
        ),
        "gate_b_n1200_report.json",
    )
    if not (
        n1200_report.get("status") == "PASS_AT_N1200_ONLY"
        and n1200_report.get("checkpoint") == "N=1200"
        and n1200_report.get("source_sha") == APPROVED_SOURCE_SHA
        and n1200_report.get("master_seed") == MASTER_SEED
        and n1200_report.get("new_trials_expected") == 12000
        and n1200_report.get("new_trials_verified") == 12000
        and n1200_report.get("trial_keys_expected") == 24000
        and n1200_report.get("trial_keys_verified") == 24000
        and n1200_report.get("historical_trials_rerun") is False
        and n1200_report.get("historical_dataset_modified") is False
        and n1200_report.get("historical_metadata_modified") is False
        and n1200_report.get("historical_identity_changed") is False
        and n1200_report.get("overall_gate_b") == "NOT_ESTABLISHED_BY_N1200_ALONE"
        and set(n1200_report.get("trial_output_run_ids", []))
        == set(UPSTREAM_RUNS)
    ):
        raise RuntimeError("GOLDEN_N1200_REPORT_IDENTITY_FAIL")
    non_c100_n1200 = {
        scenario: dict(values)
        for scenario, values in non_c100_n600.items()
    }
    reported_n1200_scenarios = {
        item.get("scenario_id"): item for item in n1200_report.get("scenarios", [])
    }
    if set(reported_n1200_scenarios) != set(NON_C100_SCENARIOS):
        raise RuntimeError("GOLDEN_N1200_SCENARIO_COVERAGE_FAIL")
    for scenario in NON_C100_SCENARIOS:
        values = reported_n1200_scenarios[scenario].get("new_trial_artifacts")
        if not isinstance(values, dict) or len(values) != 600:
            raise RuntimeError(f"GOLDEN_N1200_NEW_TRIAL_COUNT_FAIL:{scenario}")
        hashes: dict[int, str] = {}
        for raw_trial_id, item in values.items():
            trial_id = int(raw_trial_id)
            value = _valid_sha256(item.get("result_sha256"), f"{scenario}/{trial_id}")
            if (
                item.get("run_id") not in UPSTREAM_RUNS
                or item.get("run_attempt") not in (1, 2)
                or trial_id in hashes
            ):
                raise RuntimeError(f"GOLDEN_N1200_TRIAL_PROVENANCE_FAIL:{scenario}/{trial_id}")
            hashes[trial_id] = value
        if sorted(hashes) != list(range(601, 1201)):
            raise RuntimeError(f"GOLDEN_N1200_TRIAL_COVERAGE_FAIL:{scenario}")
        non_c100_n1200[scenario].update(hashes)
    if _ordered_map_sha256(non_c100_n1200) != EXPECTED_N1200_MAP_SHA256:
        raise RuntimeError("GOLDEN_N1200_AGGREGATE_SHA_MISMATCH")

    fingerprints = {
        scenario: dict(values)
        for scenario, values in non_c100_n1200.items()
    } | {
        scenario: dict(values)
        for scenario, values in fingerprints.items()
        if scenario.startswith("C100_")
    }
    if len(fingerprints) != 25 or sum(map(len, fingerprints.values())) != 24005:
        raise RuntimeError("GOLDEN_FULL_COVERAGE_FAIL")
    for scenario in SCENARIOS:
        expected_ids = [1] if scenario.startswith("C100_") else list(range(1, 1201))
        if sorted(fingerprints.get(scenario, {})) != expected_ids:
            raise RuntimeError(f"GOLDEN_FULL_SCENARIO_COVERAGE_FAIL:{scenario}")
    if any(not SHA256_RE.fullmatch(value) for values in fingerprints.values() for value in values.values()):
        raise RuntimeError("GOLDEN_FULL_HASH_FORMAT_FAIL")

    full_map_sha = _ordered_map_sha256(fingerprints)
    reference_id = f"{DECISION_ID}:GateA:24005:{full_map_sha}"
    return {
        "source_sha": APPROVED_SOURCE_SHA,
        "master_seed": MASTER_SEED,
        "decision_id": DECISION_ID,
        "trial_count": 24005,
        "scenario_count": 25,
        "source_map_sha256": full_map_sha,
        "golden_reference_id": reference_id,
        "fingerprints": fingerprints,
    }

class GoldenReferenceProvider:
    """Fail-closed access to the approved per-trial Gate A SHA-256 map."""

    def __init__(self) -> None:
        self.source_sha = APPROVED_SOURCE_SHA
        self._fingerprints: dict[str, dict[int, str]] = {}
        self._golden_reference_id = ""
        self._verified = False
        self.load_error: str | None = None
        # Do not attempt network access for local runs without an explicit GH token.
        if not (os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")):
            self.load_error = "GOLDEN_PROVIDER_TOKEN_MISSING"
            return
        try:
            payload = _load_approved_reference()
            self._fingerprints = payload["fingerprints"]
            self._golden_reference_id = payload["golden_reference_id"]
            self._verified = (
                payload.get("source_sha") == APPROVED_SOURCE_SHA
                and payload.get("master_seed") == MASTER_SEED
                and payload.get("decision_id") == DECISION_ID
                and payload.get("scenario_count") == 25
                and payload.get("trial_count") == 24005
                and sum(map(len, self._fingerprints.values())) == 24005
            )
            if not self._verified:
                raise RuntimeError("GOLDEN_PROVIDER_FINAL_IDENTITY_FAIL")
        except Exception as exc:
            self._fingerprints = {}
            self._golden_reference_id = ""
            self._verified = False
            self.load_error = str(exc)

    @classmethod
    def _from_test_map(
        cls,
        fingerprints: Mapping[str, Mapping[int, str]],
        *,
        source_sha: str = APPROVED_SOURCE_SHA,
        golden_reference_id: str = "test-golden-reference",
    ) -> "GoldenReferenceProvider":
        instance = cls.__new__(cls)
        instance.source_sha = source_sha
        instance._fingerprints = {
            scenario: {int(trial_id): str(value) for trial_id, value in values.items()}
            for scenario, values in fingerprints.items()
        }
        instance._golden_reference_id = golden_reference_id
        instance._verified = True
        instance.load_error = None
        return instance

    def get_fingerprint(self, scenario_id: str, trial_id: int) -> str | None:
        if not self._verified:
            return None
        value = self._fingerprints.get(scenario_id, {}).get(int(trial_id))
        if value is None or SHA256_RE.fullmatch(value) is None:
            return None
        return value

    def get_coverage(self, scenario_id: str) -> set[int]:
        if not self._verified:
            return set()
        return set(self._fingerprints.get(scenario_id, {}))

    def verify_source_identity(self, source_sha: str) -> bool:
        return (
            self._verified
            and source_sha == self.source_sha == APPROVED_SOURCE_SHA
            and COMMIT_SHA_RE.fullmatch(source_sha or "") is not None
        )

    def get_golden_reference_id(self) -> str:
        return self._golden_reference_id if self._verified else ""
