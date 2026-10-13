#!/usr/bin/env python3
"""Materialize the verified Stage 12 exact per-trial golden map from immutable Gate A bridge artifacts."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
import subprocess
import zipfile
from pathlib import Path

SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
SOURCE_COMMIT = "0156c5f4272eb0ca7e32442657d0df9eaf4973d3"
MASTER_SEED = 20270101
BRIDGE_RUN_ID = 38169163565
BRIDGE_HEAD_SHA = "95288a2bccb40d6772f5a5d042fdabc152c9d89a"
STAGE7_RUN_ID = 37225915321
STAGE7_HEAD_SHA = "e0b2fab6710833774937d778097363d7a8ee8e59"
STAGE12_RUN_ID = 37964656154
STAGE12_HEAD_SHA = "0156c5f4272eb0ca7e32442657d0df9eaf4973d3"
EXPECTED_GLOBAL_SHA256 = "7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44"
ARTIFACTS = {"C030_G000":{"id":11713490832,"sha256":"5f8b16d10db08b37eb0d26017a21af5cfeb98d0d2c0cc33752b37cdaaccb9450"},"C030_G030":{"id":11713226122,"sha256":"6524a3e1c0f91734c6e08ebd65c187d9075922f543d21c49e115b1ba5537cfc0"},"C030_G050":{"id":11713486473,"sha256":"bd961651b8f08571de50e0216bb3c07d017b2bceb10ba7847f747d6c8e05c36e"},"C030_G070":{"id":11714150171,"sha256":"7b8514bd3bd1c492e6459e7d78b00cf27e7f85bd07265b37b2ebec1aa2951176"},"C030_G100":{"id":11713445830,"sha256":"8adb75bfeff6b1998d4d24ce7e8ff0bf8c752b00cd2fa0294a74cc4e15a8eed0"},"C050_G000":{"id":11713071539,"sha256":"fb81c05c6e6e54ffeb85f08ebe3243abd5384cfca72ab4af690ffbf4c5f0bf3f"},"C050_G030":{"id":11713780899,"sha256":"23b27808cbb4d7c1501358953ebad53cc9f8446b8ae9a948dc0bc9f18d719aad"},"C050_G050":{"id":11713751043,"sha256":"295e0039a0c187a9c5b9c106c4179caa5390353d2b30ebc4d9c7e58c1fc0001b"},"C050_G070":{"id":11713556234,"sha256":"b3c44ef3dcddcb59191215073b64413ad02569242d19ff68bfe1afd0663c5c3a"},"C050_G100":{"id":11712974806,"sha256":"842f51219fea4554cfbc9f33b35542a7144ab03be3831e3260f673b33858953f"},"C070_G000":{"id":11714070352,"sha256":"f47f7858617a916f9f3b9889e6427660831879ccd80bd2e13f304a387ae85616"},"C070_G030":{"id":11713850642,"sha256":"869175319bb67de5ffcc8169ba86361c2819bd23cc16caabacaea7ad506e109c"},"C070_G050":{"id":11713166224,"sha256":"99c2d94eff7857945927fb8bbda4439bf460a0da938234dd1dfcfe1cd3d43cdc"},"C070_G070":{"id":11713955486,"sha256":"edfe3936b76cdcc06624cde4830b90abd2ee7533d06986b7a2de5afc9866ae6d"},"C070_G100":{"id":11713441308,"sha256":"f06b1e1c2ccf32599c6ac894bda64746deeae9ca8c6092538fd1b9fc4df3c8b1"},"C085_G000":{"id":11713780771,"sha256":"1e5a3f526718935d0caafedf19fec2715780263a94b6b6a22d76fc979e0af1c7"},"C085_G030":{"id":11713196840,"sha256":"33158c1741b4ba1ca67bbe3080fb75bb9ac4db454243485e3162c61c9ef57ca7"},"C085_G050":{"id":11713750919,"sha256":"ccf0a3e0104c0e9f2a71d656204d0f1d8f3ae843d19490273d4e1db694d1e8e8"},"C085_G070":{"id":11713291505,"sha256":"c78b64f419a58c83d4dd87a1efdadeea6da99d71555a2b67858c3741a8938192"},"C085_G100":{"id":11713122067,"sha256":"88392022ab36e3097a5a10dec064d7c462884d81504669c009c86b8881b30493"},"C100_G000":{"id":11713800278,"sha256":"1da3692137f1c40a6a79082eb690061540822c2bab386020ac2bde39e0570dbd"},"C100_G030":{"id":11713285854,"sha256":"3df8e6a5d438c0ba34cd3076549d945e2f465a3ddda02ecf95da0d5ab0741304"},"C100_G050":{"id":11712314933,"sha256":"a82f6ea7a0099d06de10fa5661c4178a7ffeda5a2e8442b5832cd49d125e8463"},"C100_G070":{"id":11713610994,"sha256":"42106a5c87d518192b12da385bf858a3c6e245b0712ab2ff271ab0ce0561ed13"},"C100_G100":{"id":11713710440,"sha256":"5a51cddd264d96feab81bdbb822adb6ccb8148f76ade3385e4627907e3a100e7"}}

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def fetch_artifact(repo: str, artifact_id: int) -> bytes:
    env = os.environ.copy()
    if not env.get("GH_TOKEN"):
        raise RuntimeError("GH_TOKEN_REQUIRED_FOR_READ_ONLY_ARTIFACT_FETCH")
    result = subprocess.run(
        ["gh", "api", f"repos/{repo}/actions/artifacts/{artifact_id}/zip"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"ARTIFACT_DOWNLOAD_FAILED id={artifact_id} "
            f"exit={result.returncode} stderr={result.stderr.decode('utf-8', errors='replace')[-1000:]}"
        )
    return result.stdout

def validate_report(scenario: str, report: dict) -> dict[str, str]:
    if report.get("scenario") != scenario:
        raise RuntimeError(f"SCENARIO_MISMATCH expected={scenario} actual={report.get('scenario')}")
    if report.get("status") != "PASS" or report.get("fatal_error") is not None:
        raise RuntimeError(f"SCENARIO_REPORT_NOT_PASS scenario={scenario} fatal={report.get('fatal_error')}")
    if report.get("source_sha") != SOURCE_SHA or int(report.get("master_seed", -1)) != MASTER_SEED:
        raise RuntimeError(f"SOURCE_OR_SEED_IDENTITY_MISMATCH scenario={scenario}")
    if report.get("simulation_or_trial_executed") is not False:
        raise RuntimeError(f"UNEXPECTED_TRIAL_EXECUTION_IN_REFERENCE_ARTIFACT scenario={scenario}")
    if report.get("historical_dataset_modified") is not False or report.get("historical_artifacts_modified") is not False:
        raise RuntimeError(f"HISTORICAL_SOURCE_MUTATION_REPORTED scenario={scenario}")
    provenance = report.get("run_provenance", {})
    expected_provenance = (
        ("stage7", STAGE7_RUN_ID, STAGE7_HEAD_SHA, "success"),
        ("stage12", STAGE12_RUN_ID, STAGE12_HEAD_SHA, "success"),
    )
    for key, run_id, head_sha, conclusion in expected_provenance:
        item = provenance.get(key, {})
        if int(item.get("id", -1)) != run_id or item.get("head_sha") != head_sha or item.get("conclusion") != conclusion:
            raise RuntimeError(f"RUN_PROVENANCE_MISMATCH scenario={scenario} source={key}")
    identity = report.get("stage12_global_identity", {})
    if identity.get("both_match_known_identity") is not True:
        raise RuntimeError(f"STAGE12_GLOBAL_IDENTITY_NOT_PASS scenario={scenario}")
    if identity.get("cp12b_expected_global_sha256") != EXPECTED_GLOBAL_SHA256 or identity.get("cp12c_expected_global_sha256") != EXPECTED_GLOBAL_SHA256:
        raise RuntimeError(f"STAGE12_GLOBAL_SHA_MISMATCH scenario={scenario}")
    expected_count = 1 if scenario.startswith("C100_") else 550
    if int(report.get("source_golden_trial_count", -1)) != expected_count or int(report.get("exact_trial_comparisons", -1)) != expected_count:
        raise RuntimeError(f"CANONICAL_TRIAL_COUNT_MISMATCH scenario={scenario}")
    rows = report.get("trial_comparisons")
    if not isinstance(rows, list) or len(rows) != expected_count:
        raise RuntimeError(f"TRIAL_COMPARISON_LIST_MISMATCH scenario={scenario}")
    hashes: dict[str, str] = {}
    for expected_trial_id, row in enumerate(rows, start=1):
        if int(row.get("trial_id", -1)) != expected_trial_id:
            raise RuntimeError(f"TRIAL_ID_SEQUENCE_MISMATCH scenario={scenario} expected={expected_trial_id}")
        if row.get("exact_match") is not True or row.get("golden_sha256") != row.get("stage12_sha256"):
            raise RuntimeError(f"EXACT_GOLDEN_MISMATCH scenario={scenario} trial_id={expected_trial_id}")
        digest = row.get("golden_sha256")
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise RuntimeError(f"INVALID_GOLDEN_SHA256 scenario={scenario} trial_id={expected_trial_id}")
        hashes[str(expected_trial_id)] = digest
    if int(report.get("hash_mismatch_count", -1)) != 0:
        raise RuntimeError(f"NONZERO_REFERENCE_MISMATCH_COUNT scenario={scenario}")
    return hashes

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.repo != "yasmin977209-ux/motorcycle-simulation":
        raise RuntimeError(f"UNEXPECTED_GITHUB_REPOSITORY {args.repo!r}")
    if len(ARTIFACTS) != 25:
        raise RuntimeError("SCENARIO_ARTIFACT_MAP_COUNT_INVALID")
    reports = {}
    map_rows = []
    artifacts_manifest = {}
    for scenario in sorted(ARTIFACTS):
        entry = ARTIFACTS[scenario]
        archive = fetch_artifact(args.repo, int(entry["id"]))
        actual_archive_sha = sha256(archive)
        if actual_archive_sha != entry["sha256"]:
            raise RuntimeError(
                f"ARTIFACT_ARCHIVE_SHA256_MISMATCH scenario={scenario} "
                f"expected={entry['sha256']} actual={actual_archive_sha}"
            )
        with zipfile.ZipFile(io.BytesIO(archive)) as zf:
            expected_name = f"{scenario}.json"
            if zf.namelist() != [expected_name]:
                raise RuntimeError(f"ARTIFACT_ZIP_MEMBER_MISMATCH scenario={scenario} names={zf.namelist()}")
            report = json.loads(zf.read(expected_name).decode("utf-8"))
        hashes = validate_report(scenario, report)
        reports[scenario] = {"trial_hashes": hashes}
        for trial_id, trial_sha in hashes.items():
            map_rows.append((scenario, int(trial_id), trial_sha))
        artifacts_manifest[scenario] = {
            "artifact_id": int(entry["id"]),
            "artifact_name": f"gatea-scenario-{scenario}",
            "archive_sha256": actual_archive_sha,
            "source_golden_trial_count": len(hashes),
            "scenario_report_status": "PASS",
        }
    global_payload = "".join(
        f"{scenario}|{trial_id}|{trial_sha}\n"
        for scenario, trial_id, trial_sha in sorted(map_rows, key=lambda x: (x[0], x[1], x[2]))
    )
    actual_global = sha256(global_payload.encode("utf-8"))
    if len(map_rows) != 11005 or len({(s, t) for s, t, _ in map_rows}) != 11005:
        raise RuntimeError(f"GLOBAL_TRIAL_MAP_COVERAGE_MISMATCH rows={len(map_rows)}")
    if actual_global != EXPECTED_GLOBAL_SHA256:
        raise RuntimeError(
            f"GLOBAL_TRIAL_MAP_SHA256_MISMATCH expected={EXPECTED_GLOBAL_SHA256} actual={actual_global}"
        )
    manifest = {
        "manifest_version": "stage12-golden-per-trial-v1",
        "canonical_reference_id": "GATEA-EXACT-GOLDEN-BRIDGE-RUN-38169163565",
        "gate_a_bridge_run_id": BRIDGE_RUN_ID,
        "gate_a_bridge_run_head_sha": BRIDGE_HEAD_SHA,
        "gate_a_bridge_run_conclusion": "success",
        "source_sha": SOURCE_SHA,
        "source_commit": SOURCE_COMMIT,
        "master_seed": MASTER_SEED,
        "rng_policy_id": "SHA-256 seed key master_seed|scenario_id|trial_id|bike_id|date|event_type; draw=first_8_digest_bytes_big_endian/2^64",
        "canonical_trials_expected": 11005,
        "scenario_count_expected": 25,
        "global_ordered_trial_hash_map_sha256": EXPECTED_GLOBAL_SHA256,
        "hash_map_sha256_recomputed": actual_global,
        "coverage": {
            "C100": 1,
            "non_C100": 550,
            "scenarios": 25,
            "exact_match_count": len(map_rows),
            "mismatches": 0,
            "source_data_modified": False,
            "trial_executed": False,
        },
        "artifacts": artifacts_manifest,
        "scenarios": reports,
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "result": "PASS",
        "source_sha": SOURCE_SHA,
        "master_seed": MASTER_SEED,
        "scenario_count": 25,
        "trial_hash_count": len(map_rows),
        "hash_mismatch_count": 0,
        "global_hash_sha256": actual_global,
        "output": str(target),
        "output_sha256": sha256(target.read_bytes()),
        "output_bytes": target.stat().st_size,
    }, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
