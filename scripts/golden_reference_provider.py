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
DECISION_ID = "D-2026-10-14-01"  # Historical map provenance ID; not the effective authorization record.
EXPECTED_CANONICAL_MAP_SHA256 = "7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44"
EXPECTED_N600_MAP_SHA256 = "dd537fe96c5a8736201441e9a620db148a0d16cadae518d2a777fbc723db395f"
EXPECTED_N1200_MAP_SHA256 = "eaf1f8f3060aac6967b064d3199c082d2a9b47027c865628986f56cbb23c1fc3"
EXPECTED_FULL_MAP_SHA256 = "166cae242d972c597f1a4466d184062f3d959649eb5e2440ad8de8b75663ff2c"
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

# Approved scenario-specific extension authorized by D-2026-10-15-10.
APPROVED_SOURCE_COMMIT = "0156c5f4272eb0ca7e32442657d0df9eaf4973d3"
EXTENSION_DECISION_ID = "D-2026-10-15-10"
EXTENSION_SCENARIO = "C030_G030"
EXTENSION_TRIAL_ID_START = 1201
EXTENSION_TRIAL_ID_END = 2400
EXTENSION_TRIAL_COUNT = 1200
EXTENSION_RUN_ID = 38662076725
EXTENSION_RUN_HEAD = "aafe5946a8a51c991471057d71f5643c46087086"
EXTENSION_ARTIFACT_ID = 11940485523
EXTENSION_ARTIFACT_NAME = "gatea-golden-c030-g1201-2400-attempt-1"
EXTENSION_ARTIFACT_SHA256 = "049af21733b59d753967f27f251cb88fec122b5e1ff4f99d77b9215114c9d3e3"
EXPECTED_EXTENSION_MAP_SHA256 = "0c7679edfbee54797d64fc66e17116f0db617d1e0fa5f7ee21395fe98a628c65"
EXTENSION_ARTIFACT_MEMBER = "golden_extension.json"
BASE_TRIAL_COUNT = 24005
EXTENDED_TRIAL_COUNT = 25205

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


def golden_authority_status(
    decision_log_path: str | Path = Path("docs/governance/DECISIONS_LOG.md"),
) -> dict[str, Any]:
    """Validate the clean, current approval for this exact pinned Golden map.

    This does not reconstruct or claim to repair earlier missing/corrupted decisions.
    It accepts only the newer bounded authorization whose scope, fingerprints,
    extension provenance, and no-production-execution boundary are explicit.
    """
    path = Path(decision_log_path)
    if not path.is_file():
        return {"authorized": False, "status": "BLOCKED_GOVERNANCE_AUTHORITY",
                "blockers": ["GOLDEN_DECISION_LOG_MISSING"], "decision_log_path": str(path)}
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        return {"authorized": False, "status": "BLOCKED_GOVERNANCE_AUTHORITY",
                "blockers": [f"GOLDEN_DECISION_LOG_UNREADABLE:{type(exc).__name__}"],
                "decision_log_path": str(path)}

    match = re.search(r"(?m)^## D-2026-10-24-01(?:\s|$)", text)
    if match is None:
        return {
            "authorized": False,
            "status": "BLOCKED_GOVERNANCE_AUTHORITY",
            "decision_log_path": str(path),
            "decision_log_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "required_decisions": {"D-2026-10-24-01": {"present": False, "integrity": "MISSING"}},
            "blockers": ["GOLDEN_DECISION_MISSING:D-2026-10-24-01"],
        }
    next_decision = re.search(r"(?m)^## D-", text[match.end():])
    end = match.end() + next_decision.start() if next_decision else len(text)
    body = text[match.start():end]
    required_terms = (
        "APPROVED — current explicit project-owner delegation dated 2026-10-24",
        "20270101",
        "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b",
        "25,205 trial fingerprints",
        "24,005 fingerprints",
        "1..1200",
        "C100",
        "24,005-fingerprint base Gate A map SHA-256",
        "166cae242d972c597f1a4466d184062f3d959649eb5e2440ad8de8b75663ff2c",
        "25,205-fingerprint combined extended Gate A map SHA-256",
        "0fbe3aa87a253f9527953c77b0a122871c9344f75ece6c8a49da99b2a85c1ce1",
        "11,005-fingerprint Stage 12 canonical map SHA-256",
        "7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44",
        "dd537fe96c5a8736201441e9a620db148a0d16cadae518d2a777fbc723db395f",
        "eaf1f8f3060aac6967b064d3199c082d2a9b47027c865628986f56cbb23c1fc3",
        "C030_G030",
        "1201..2400",
        "38662076725",
        "11940485523",
        "049af21733b59d753967f27f251cb88fec122b5e1ff4f99d77b9215114c9d3e3",
        "0c7679edfbee54797d64fc66e17116f0db617d1e0fa5f7ee21395fe98a628c65",
        "Preserve the previous C030_G030 N=300→600 failure record",
        "STATISTICAL_INFERENCE_BLOCKED",
        "No production Monte Carlo, Trial, checkpoint",
        "does not reconstruct, replace, or claim recovery",
    )
    corrupted = "NaNNaN" in body
    missing = [term for term in required_terms if term not in body]
    blockers = []
    if corrupted:
        blockers.append("GOLDEN_DECISION_CORRUPTION_MARKER:D-2026-10-24-01")
    if missing:
        blockers.append("GOLDEN_DECISION_INCOMPLETE:D-2026-10-24-01")
    detail = {
        "present": True,
        "contains_corruption_marker": corrupted,
        "missing_required_terms": missing,
        "integrity": "PASS" if not corrupted and not missing else "FAIL",
        "scope": "exact pinned Golden map only; statistical execution remains separately blocked",
    }
    return {
        "authorized": not blockers,
        "status": "AUTHORIZED" if not blockers else "BLOCKED_GOVERNANCE_AUTHORITY",
        "decision_log_path": str(path),
        "decision_log_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "required_decisions": {"D-2026-10-24-01": detail},
        "blockers": blockers,
    }



def statistical_execution_status(
    contract_path: str | Path = Path("docs/stage7/statistical_execution_gate.json"),
) -> dict[str, Any]:
    """Require explicit reviewed statistical-method acceptance before any production sampling."""
    path = Path(contract_path)
    if not path.is_file():
        return {
            "authorized": False,
            "status": "STATISTICAL_INFERENCE_BLOCKED",
            "blockers": ["STATISTICAL_EXECUTION_CONTRACT_MISSING"],
            "contract_path": str(path),
        }
    try:
        contract = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "authorized": False,
            "status": "STATISTICAL_INFERENCE_BLOCKED",
            "blockers": [f"STATISTICAL_EXECUTION_CONTRACT_INVALID:{type(exc).__name__}"],
            "contract_path": str(path),
        }
    if not isinstance(contract, dict) or contract.get("schema_version") != "stage7-statistical-execution-gate-v1":
        return {
            "authorized": False,
            "status": "STATISTICAL_INFERENCE_BLOCKED",
            "blockers": ["STATISTICAL_EXECUTION_CONTRACT_SCHEMA_INVALID"],
            "contract_path": str(path),
        }

    blockers: list[str] = []
    if contract.get("status") != "ACCEPTED_FOR_PRODUCTION":
        blockers.append(f"STATISTICAL_GATE_STATUS:{contract.get('status', 'MISSING')}")
    execution = contract.get("execution_authorization", {})
    if (
        not isinstance(execution, dict)
        or execution.get("production_trial_checkpoint_monte_carlo_allowed") is not True
        or execution.get("scenario_stability_declaration_allowed") is not True
        or execution.get("final_delivery_acceptance_allowed") is not True
    ):
        blockers.append("STATISTICAL_EXECUTION_AUTHORIZATION_INCOMPLETE")

    approval = contract.get("implementation_approval", {})
    if (
        not isinstance(approval, dict)
        or approval.get("reviewed_approval_id") in (None, "")
        or approval.get("owner_approved") is not True
        or COMMIT_SHA_RE.fullmatch(str(approval.get("validated_source_head_sha", ""))) is None
        or SHA256_RE.fullmatch(str(approval.get("evidence_sha256", ""))) is None
    ):
        blockers.append("STATISTICAL_IMPLEMENTATION_APPROVAL_OR_EVIDENCE_MISSING")

    policy = contract.get("approved_policy", {})
    if (
        not isinstance(policy, dict)
        or policy.get("familywise_false_stability_target") != 0.05
        or policy.get("stochastic_scenario_count") != 20
        or policy.get("per_scenario_alpha") != 0.0025
        or policy.get("decision_framework") != "intersection_union_test"
        or policy.get("required_successful_adjacent_transitions") != 3
        or policy.get("required_cumulative_checkpoint_points") != 4
    ):
        blockers.append("STATISTICAL_POLICY_CONTRACT_MISMATCH")

    components = contract.get("component_status", {})
    required_components = (
        "gate_a_exact_golden",
        "gate_b_financial_means",
        "section_2_5_quantiles",
        "probability_of_accounting_loss",
        "p90_held_assets",
        "stopping_window",
        "gate_b_implementation_guards",
        "c030_g030_historical_transition",
    )
    if not isinstance(components, dict):
        blockers.append("STATISTICAL_COMPONENT_STATUS_MISSING")
    else:
        for name in required_components:
            value = components.get(name)
            if not isinstance(value, dict) or value.get("status") not in (
                "PASS",
                "PASS_REQUALIFIED",
                "IMPLEMENTED_AND_VALIDATED",
            ):
                state = value.get("status", "MISSING") if isinstance(value, dict) else "MISSING"
                if name == "p90_held_assets":
                    blockers.append(f"STATISTICAL_COMPONENT_NOT_ACCEPTED:P90_Held_Assets:{state}")
                else:
                    blockers.append(f"STATISTICAL_COMPONENT_NOT_ACCEPTED:{name}:{state}")

    return {
        "authorized": not blockers,
        "status": "AUTHORIZED" if not blockers else "STATISTICAL_INFERENCE_BLOCKED",
        "contract_path": str(path),
        "contract_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "declared_contract_status": contract.get("status"),
        "component_status": {
            key: value.get("status") if isinstance(value, dict) else "MISSING"
            for key, value in components.items()
        } if isinstance(components, dict) else {},
        "blockers": blockers,
    }


def stage10_trial_result_sha256(result: Any) -> str:
    """Hash one TrialResult exactly as Stage 10's per-trial result_sha does."""
    if is_dataclass(result):
        value = asdict(result)
    elif isinstance(result, dict):
        value = dict(result)
    else:
        raise TypeError("trial result must be a dataclass instance or dict")
    # RNG audit metadata uses its own fingerprint and must not alter historic
    # financial TrialResult hashes.
    value.pop("rng_checksum", None)
    value.pop("rng_draw_count", None)
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


def _load_and_verify_c030_g030_extension(
    fingerprints: dict[str, dict[int, str]], token: str
) -> dict[str, Any]:
    """Verify the decision-pinned extension artifact and merge it into the base map."""
    _verify_run(EXTENSION_RUN_ID, EXTENSION_RUN_HEAD, "success", token)
    extension_artifacts = _artifact_index(EXTENSION_RUN_ID, token)
    extension = _single_json_member(
        _download_artifact_bytes(
            run_id=EXTENSION_RUN_ID,
            artifact_index=extension_artifacts,
            artifact_name=EXTENSION_ARTIFACT_NAME,
            artifact_id=EXTENSION_ARTIFACT_ID,
            expected_sha256=EXTENSION_ARTIFACT_SHA256,
            token=token,
        ),
        EXTENSION_ARTIFACT_MEMBER,
    )

    base_map_sha = _ordered_map_sha256(fingerprints)
    if base_map_sha != EXPECTED_FULL_MAP_SHA256:
        raise RuntimeError("GOLDEN_EXTENSION_BASE_MAP_SHA_MISMATCH")
    run = _gh_json(f"repos/{REPOSITORY}/actions/runs/{EXTENSION_RUN_ID}", token)
    expected_top_level = (
        extension.get("schema_version") == "gate-a-golden-extension-v1",
        extension.get("status") == "PASS",
        extension.get("extension_decision_id") == EXTENSION_DECISION_ID,
        extension.get("base_decision_id") == DECISION_ID,
        extension.get("scenario_id") == EXTENSION_SCENARIO,
        extension.get("source_sha") == APPROVED_SOURCE_SHA,
        extension.get("source_commit") == APPROVED_SOURCE_COMMIT,
        extension.get("master_seed") == MASTER_SEED,
        extension.get("trial_id_start") == EXTENSION_TRIAL_ID_START,
        extension.get("trial_id_end") == EXTENSION_TRIAL_ID_END,
        extension.get("trial_count") == EXTENSION_TRIAL_COUNT,
        extension.get("run_id") == EXTENSION_RUN_ID,
        extension.get("run_attempt") == run.get("run_attempt") == 1,
        extension.get("workflow_head_sha") == EXTENSION_RUN_HEAD,
        run.get("head_sha") == EXTENSION_RUN_HEAD,
        extension.get("origin") == "pinned_approved_source_reference",
        extension.get("historical_ids_rerun") is False,
        extension.get("historical_dataset_modified") is False,
        extension.get("historical_parquet_modified") is False,
        extension.get("source_sha_bumped") is False,
        extension.get("production_checkpoint_accepted") is False,
        extension.get("base_golden_map_sha256") == base_map_sha,
    )
    if not all(expected_top_level):
        raise RuntimeError("GOLDEN_EXTENSION_TOP_LEVEL_IDENTITY_FAIL")

    rows = extension.get("records")
    if not isinstance(rows, list) or len(rows) != EXTENSION_TRIAL_COUNT:
        raise RuntimeError("GOLDEN_EXTENSION_RECORD_COUNT_MISMATCH")
    indexed: dict[int, str] = {}
    for record in rows:
        if not isinstance(record, dict):
            raise RuntimeError("GOLDEN_EXTENSION_RECORD_TYPE_INVALID")
        try:
            trial_id = int(record.get("trial_id", -1))
        except (TypeError, ValueError) as exc:
            raise RuntimeError("GOLDEN_EXTENSION_TRIAL_ID_INVALID") from exc
        row = record.get("trial_result")
        value = _valid_sha256(record.get("result_sha256"), f"{EXTENSION_SCENARIO}/{trial_id}")
        if not isinstance(row, dict):
            raise RuntimeError(f"GOLDEN_EXTENSION_TRIAL_RESULT_MISSING:{trial_id}")
        if (
            record.get("scenario_id") != EXTENSION_SCENARIO
            or row.get("scenario_id") != EXTENSION_SCENARIO
            or int(row.get("trial_id", -1)) != trial_id
            or record.get("source_sha") != APPROVED_SOURCE_SHA
            or record.get("source_commit") != APPROVED_SOURCE_COMMIT
            or int(record.get("master_seed", -1)) != MASTER_SEED
            or int(record.get("run_id", -1)) != EXTENSION_RUN_ID
            or int(record.get("run_attempt", -1)) != 1
            or record.get("origin") != "pinned_source_reference"
            or stage10_trial_result_sha256(row) != value
            or trial_id in indexed
        ):
            raise RuntimeError(f"GOLDEN_EXTENSION_TRIAL_PROVENANCE_OR_HASH_FAIL:{EXTENSION_SCENARIO}/{trial_id}")
        indexed[trial_id] = value
    if sorted(indexed) != list(range(EXTENSION_TRIAL_ID_START, EXTENSION_TRIAL_ID_END + 1)):
        raise RuntimeError("GOLDEN_EXTENSION_TRIAL_COVERAGE_FAIL")
    extension_map_payload = "".join(
        f"{EXTENSION_SCENARIO}|{trial_id}|{indexed[trial_id]}\n"
        for trial_id in sorted(indexed)
    )
    extension_map_sha = hashlib.sha256(extension_map_payload.encode("utf-8")).hexdigest()
    if extension_map_sha != extension.get("extension_map_sha256"):
        raise RuntimeError("GOLDEN_EXTENSION_MAP_SHA_MISMATCH")

    extended = {scenario: dict(values) for scenario, values in fingerprints.items()}
    target = extended.get(EXTENSION_SCENARIO)
    if target is None or sorted(target) != list(range(1, EXTENSION_TRIAL_ID_START)):
        raise RuntimeError("GOLDEN_EXTENSION_BASE_SCENARIO_COVERAGE_FAIL")
    if set(target).intersection(indexed):
        raise RuntimeError("GOLDEN_EXTENSION_OVERLAPS_ACCEPTED_TRIAL_IDS")
    target.update(indexed)
    if len(extended) != 25 or sum(map(len, extended.values())) != EXTENDED_TRIAL_COUNT:
        raise RuntimeError("GOLDEN_EXTENSION_EXTENDED_TOTAL_COUNT_MISMATCH")
    for scenario in SCENARIOS:
        expected_ids = (
            [1] if scenario.startswith("C100_")
            else list(range(1, EXTENSION_TRIAL_ID_END + 1))
            if scenario == EXTENSION_SCENARIO
            else list(range(1, 1201))
        )
        if sorted(extended.get(scenario, {})) != expected_ids:
            raise RuntimeError(f"GOLDEN_EXTENSION_FINAL_COVERAGE_FAIL:{scenario}")
    combined_map_sha = _ordered_map_sha256(extended)
    if not SHA256_RE.fullmatch(combined_map_sha):
        raise RuntimeError("GOLDEN_EXTENSION_COMBINED_MAP_SHA_INVALID")
    return {
        "fingerprints": extended,
        "base_trial_count": BASE_TRIAL_COUNT,
        "trial_count": EXTENDED_TRIAL_COUNT,
        "scenario_count": 25,
        "base_source_map_sha256": base_map_sha,
        "source_map_sha256": combined_map_sha,
        "extension_decision_id": EXTENSION_DECISION_ID,
        "extension_run_id": EXTENSION_RUN_ID,
        "extension_run_head_sha": EXTENSION_RUN_HEAD,
        "extension_artifact_id": EXTENSION_ARTIFACT_ID,
        "extension_artifact_sha256": EXTENSION_ARTIFACT_SHA256,
        "extension_map_sha256": extension_map_sha,
    }

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
    if full_map_sha != EXPECTED_FULL_MAP_SHA256:
        raise RuntimeError("GOLDEN_FULL_AGGREGATE_SHA_MISMATCH")
    extension_payload = _load_and_verify_c030_g030_extension(fingerprints, token)
    fingerprints = extension_payload["fingerprints"]
    extended_map_sha = extension_payload["source_map_sha256"]
    reference_id = f"{DECISION_ID}:GateA:{EXTENDED_TRIAL_COUNT}:{extended_map_sha}"
    return {
        "source_sha": APPROVED_SOURCE_SHA,
        "source_commit": APPROVED_SOURCE_COMMIT,
        "master_seed": MASTER_SEED,
        "decision_id": DECISION_ID,
        "trial_count": EXTENDED_TRIAL_COUNT,
        "scenario_count": 25,
        "source_map_sha256": extended_map_sha,
        "golden_reference_id": reference_id,
        "fingerprints": fingerprints,
        **{key: value for key, value in extension_payload.items() if key != "fingerprints"},
    }

class GoldenReferenceProvider:
    """Fail-closed access to the approved per-trial Gate A SHA-256 map."""

    def __init__(self) -> None:
        self.source_sha = APPROVED_SOURCE_SHA
        self.source_commit = APPROVED_SOURCE_COMMIT
        self.master_seed = MASTER_SEED
        self.base_trial_count = BASE_TRIAL_COUNT
        self.trial_count = 0
        self.scenario_count = 0
        self.base_source_map_sha256 = EXPECTED_FULL_MAP_SHA256
        self.source_map_sha256 = ""
        self.extension_decision_id = EXTENSION_DECISION_ID
        self.extension_run_id = EXTENSION_RUN_ID
        self.extension_run_head_sha = EXTENSION_RUN_HEAD
        self.extension_artifact_id = EXTENSION_ARTIFACT_ID
        self.extension_artifact_sha256 = EXTENSION_ARTIFACT_SHA256
        self.extension_map_sha256 = ""
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
            self.source_commit = payload.get("source_commit", "")
            self.base_trial_count = int(payload.get("base_trial_count", -1))
            self.trial_count = int(payload.get("trial_count", -1))
            self.scenario_count = int(payload.get("scenario_count", -1))
            self.base_source_map_sha256 = payload.get("base_source_map_sha256", "")
            self.source_map_sha256 = payload.get("source_map_sha256", "")
            self.extension_decision_id = payload.get("extension_decision_id", "")
            self.extension_run_id = int(payload.get("extension_run_id", -1))
            self.extension_run_head_sha = payload.get("extension_run_head_sha", "")
            self.extension_artifact_id = int(payload.get("extension_artifact_id", -1))
            self.extension_artifact_sha256 = payload.get("extension_artifact_sha256", "")
            self.extension_map_sha256 = payload.get("extension_map_sha256", "")
            self._verified = (
                payload.get("source_sha") == APPROVED_SOURCE_SHA
                and self.source_commit == APPROVED_SOURCE_COMMIT
                and payload.get("master_seed") == MASTER_SEED
                and payload.get("decision_id") == DECISION_ID
                and self.extension_decision_id == EXTENSION_DECISION_ID
                and self.base_trial_count == BASE_TRIAL_COUNT
                and self.trial_count == EXTENDED_TRIAL_COUNT
                and self.scenario_count == 25
                and self.base_source_map_sha256 == EXPECTED_FULL_MAP_SHA256
                and SHA256_RE.fullmatch(self.source_map_sha256 or "") is not None
                and SHA256_RE.fullmatch(self.extension_map_sha256 or "") is not None
                and self.extension_run_id == EXTENSION_RUN_ID
                and self.extension_run_head_sha == EXTENSION_RUN_HEAD
                and self.extension_artifact_id == EXTENSION_ARTIFACT_ID
                and self.extension_artifact_sha256 == EXTENSION_ARTIFACT_SHA256
                and sum(map(len, self._fingerprints.values())) == EXTENDED_TRIAL_COUNT
                and _ordered_map_sha256(self._fingerprints) == self.source_map_sha256
            )
            if not self._verified:
                raise RuntimeError("GOLDEN_PROVIDER_FINAL_IDENTITY_FAIL")
        except Exception as exc:
            self._fingerprints = {}
            self._golden_reference_id = ""
            self._verified = False
            self.load_error = str(exc)


    def to_verified_payload(self) -> dict[str, Any]:
        """Export a fully verified, digest-pinned map for same-run worker reuse."""
        if not self._verified:
            raise RuntimeError("GOLDEN_PROVIDER_NOT_VERIFIED")
        return {
            "schema_version": "gate-a-golden-provider-map-v1",
            "source_sha": self.source_sha,
            "source_commit": self.source_commit,
            "master_seed": self.master_seed,
            "decision_id": DECISION_ID,
            "trial_count": self.trial_count,
            "scenario_count": self.scenario_count,
            "base_trial_count": self.base_trial_count,
            "base_source_map_sha256": self.base_source_map_sha256,
            "source_map_sha256": self.source_map_sha256,
            "golden_reference_id": self._golden_reference_id,
            "extension_decision_id": self.extension_decision_id,
            "extension_run_id": self.extension_run_id,
            "extension_run_head_sha": self.extension_run_head_sha,
            "extension_artifact_id": self.extension_artifact_id,
            "extension_artifact_sha256": self.extension_artifact_sha256,
            "extension_map_sha256": self.extension_map_sha256,
            "fingerprints": {
                scenario: {
                    str(trial_id): value
                    for trial_id, value in sorted(values.items())
                }
                for scenario, values in sorted(self._fingerprints.items())
            },
        }

    @classmethod
    def from_verified_payload(cls, path: Path) -> "GoldenReferenceProvider":
        """Load a same-run cache only after strict source, decision and digest checks."""
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RuntimeError("GOLDEN_PROVIDER_CACHE_READ_FAILED") from exc
        if not isinstance(payload, dict) or payload.get("schema_version") != "gate-a-golden-provider-map-v1":
            raise RuntimeError("GOLDEN_PROVIDER_CACHE_SCHEMA_INVALID")
        expected_fixed = {
            "source_sha": APPROVED_SOURCE_SHA,
            "source_commit": APPROVED_SOURCE_COMMIT,
            "master_seed": MASTER_SEED,
            "decision_id": DECISION_ID,
            "trial_count": EXTENDED_TRIAL_COUNT,
            "scenario_count": 25,
            "base_trial_count": BASE_TRIAL_COUNT,
            "base_source_map_sha256": EXPECTED_FULL_MAP_SHA256,
            "extension_decision_id": EXTENSION_DECISION_ID,
            "extension_run_id": EXTENSION_RUN_ID,
            "extension_run_head_sha": EXTENSION_RUN_HEAD,
            "extension_artifact_id": EXTENSION_ARTIFACT_ID,
            "extension_artifact_sha256": EXTENSION_ARTIFACT_SHA256,
            "extension_map_sha256": EXPECTED_EXTENSION_MAP_SHA256,
        }
        for key, expected in expected_fixed.items():
            if payload.get(key) != expected:
                raise RuntimeError(f"GOLDEN_PROVIDER_CACHE_IDENTITY_MISMATCH:{key}")
        raw = payload.get("fingerprints")
        if not isinstance(raw, dict) or set(raw) != set(SCENARIOS):
            raise RuntimeError("GOLDEN_PROVIDER_CACHE_SCENARIO_COVERAGE_MISMATCH")
        fingerprints: dict[str, dict[int, str]] = {}
        for scenario in SCENARIOS:
            raw_values = raw.get(scenario)
            if not isinstance(raw_values, dict):
                raise RuntimeError(f"GOLDEN_PROVIDER_CACHE_MAP_INVALID:{scenario}")
            values: dict[int, str] = {}
            for raw_trial_id, digest in raw_values.items():
                try:
                    trial_id = int(raw_trial_id)
                except (TypeError, ValueError) as exc:
                    raise RuntimeError(f"GOLDEN_PROVIDER_CACHE_TRIAL_ID_INVALID:{scenario}") from exc
                if trial_id in values or not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
                    raise RuntimeError(f"GOLDEN_PROVIDER_CACHE_HASH_INVALID:{scenario}/{trial_id}")
                values[trial_id] = digest
            if scenario.startswith("C100_"):
                expected_ids = [1]
            elif scenario == EXTENSION_SCENARIO:
                expected_ids = list(range(1, EXTENSION_TRIAL_ID_END + 1))
            else:
                expected_ids = list(range(1, 1201))
            if sorted(values) != expected_ids:
                raise RuntimeError(f"GOLDEN_PROVIDER_CACHE_TRIAL_COVERAGE_MISMATCH:{scenario}")
            fingerprints[scenario] = values
        if sum(map(len, fingerprints.values())) != EXTENDED_TRIAL_COUNT:
            raise RuntimeError("GOLDEN_PROVIDER_CACHE_TOTAL_COUNT_MISMATCH")
        base_fingerprints = {
            scenario: {n: digest for n, digest in values.items()
                       if scenario.startswith("C100_") or n <= 1200}
            for scenario, values in fingerprints.items()
        }
        if _ordered_map_sha256(base_fingerprints) != EXPECTED_FULL_MAP_SHA256:
            raise RuntimeError("GOLDEN_PROVIDER_CACHE_BASE_MAP_SHA_MISMATCH")
        extension_values = {
            EXTENSION_SCENARIO: {
                n: digest for n, digest in fingerprints[EXTENSION_SCENARIO].items()
                if EXTENSION_TRIAL_ID_START <= n <= EXTENSION_TRIAL_ID_END
            }
        }
        if _ordered_map_sha256(extension_values) != payload.get("extension_map_sha256"):
            raise RuntimeError("GOLDEN_PROVIDER_CACHE_EXTENSION_MAP_SHA_MISMATCH")
        source_map_sha = _ordered_map_sha256(fingerprints)
        if source_map_sha != payload.get("source_map_sha256"):
            raise RuntimeError("GOLDEN_PROVIDER_CACHE_MAP_SHA_MISMATCH")
        expected_ref = f"{DECISION_ID}:GateA:{EXTENDED_TRIAL_COUNT}:{source_map_sha}"
        if payload.get("golden_reference_id") != expected_ref:
            raise RuntimeError("GOLDEN_PROVIDER_CACHE_REFERENCE_ID_MISMATCH")
        instance = cls.__new__(cls)
        instance.source_sha = APPROVED_SOURCE_SHA
        instance.source_commit = APPROVED_SOURCE_COMMIT
        instance.master_seed = MASTER_SEED
        instance.base_trial_count = BASE_TRIAL_COUNT
        instance.trial_count = EXTENDED_TRIAL_COUNT
        instance.scenario_count = 25
        instance.base_source_map_sha256 = EXPECTED_FULL_MAP_SHA256
        instance.source_map_sha256 = source_map_sha
        instance.extension_decision_id = EXTENSION_DECISION_ID
        instance.extension_run_id = EXTENSION_RUN_ID
        instance.extension_run_head_sha = EXTENSION_RUN_HEAD
        instance.extension_artifact_id = EXTENSION_ARTIFACT_ID
        instance.extension_artifact_sha256 = EXTENSION_ARTIFACT_SHA256
        instance.extension_map_sha256 = payload["extension_map_sha256"]
        instance._fingerprints = fingerprints
        instance._golden_reference_id = expected_ref
        instance._verified = True
        instance.load_error = None
        return instance

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
        instance.source_commit = APPROVED_SOURCE_COMMIT
        instance.master_seed = MASTER_SEED
        instance.base_trial_count = BASE_TRIAL_COUNT
        instance.trial_count = 0
        instance.scenario_count = 0
        instance.base_source_map_sha256 = EXPECTED_FULL_MAP_SHA256
        instance.source_map_sha256 = ""
        instance.extension_decision_id = EXTENSION_DECISION_ID
        instance.extension_run_id = EXTENSION_RUN_ID
        instance.extension_run_head_sha = EXTENSION_RUN_HEAD
        instance.extension_artifact_id = EXTENSION_ARTIFACT_ID
        instance.extension_artifact_sha256 = EXTENSION_ARTIFACT_SHA256
        instance.extension_map_sha256 = ""
        instance._fingerprints = {
            scenario: {int(trial_id): str(value) for trial_id, value in values.items()}
            for scenario, values in fingerprints.items()
        }
        instance._golden_reference_id = golden_reference_id
        instance.source_map_sha256 = _ordered_map_sha256(instance._fingerprints)
        instance.trial_count = sum(map(len, instance._fingerprints.values()))
        instance.scenario_count = len(instance._fingerprints)
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
