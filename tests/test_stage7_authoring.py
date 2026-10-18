from __future__ import annotations

import base64
import hashlib
import json
import urllib.parse
from datetime import datetime, timedelta, timezone
import re
from pathlib import Path

import pytest
import yaml

from scripts.stage7_state import (
    LeaseConflict,
    StateIntegrityError,
    StateRemoteNotFound,
    StateStore,
    STAGE7_RNG_POLICY_ID,
    _git_blob_sha,
    build_artifact_identity,
    build_durable_block_identity,
    validate_durable_block_identity,
    validate_trial_sequence,
)
from scripts.stage7_stability import evaluate_gate_a, evaluate_gate_b

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "stage7-full-run.yml"
AUTHORING_VERIFY = REPO_ROOT / ".github" / "workflows" / "stage7-authoring-verify.yml"
TRIAL_BLOCK = REPO_ROOT / "scripts" / "stage7_run_trial_block.py"

APPROVED_SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
MODEL_FILES = (
    "constants.py",
    "dateutils.py",
    "rng.py",
    "entities.py",
    "state_machine.py",
    "daily_engine.py",
    "accounting.py",
    "collection.py",
    "guarantee.py",
    "friday.py",
    "settlement.py",
    "closure.py",
    "partner_equity.py",
    "monte_carlo.py",
)

def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")

def _workflow() -> dict:
    return yaml.safe_load(_workflow_text())

def _metrics(means: tuple[float, float, float], stable: bool = True) -> dict[str, dict[str, float | bool]]:
    keys = ("final_net_project_equity", "partner1_final_entitlement", "partner2_final_entitlement")
    return {key: {"mean": value, "stable": stable} for key, value in zip(keys, means)}


def test_durable_block_manifest_binds_bytes_and_identity() -> None:
    parquet_bytes = b"deterministic-test-block-bytes"
    metadata = {
        "schema_version": "stage7-block-v1",
        "scenario": "C070_G100",
        "source_sha": APPROVED_SOURCE_SHA,
        "master_seed": 20270101,
        "rng_policy_id": STAGE7_RNG_POLICY_ID,
        "sampling_policy_id": "DOUBLING_FROM_300_V1",
        "trial_id_start": 1,
        "trial_id_end": 2,
        "trial_count": 2,
        "fingerprint_sha256": "a" * 64,
        "parquet_sha256": hashlib.sha256(parquet_bytes).hexdigest(),
        "per_trial_sha256": ["b" * 64, "c" * 64],
        "run_id": "123",
    }
    metadata_bytes = (
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    identity = build_durable_block_identity(
        metadata=metadata,
        parquet_bytes=parquet_bytes,
        metadata_bytes=metadata_bytes,
        scenario="C070_G100",
        source_sha=APPROVED_SOURCE_SHA,
        master_seed=20270101,
        sampling_policy_id="DOUBLING_FROM_300_V1",
    )
    validate_durable_block_identity(
        identity=identity,
        metadata=metadata,
        parquet_bytes=parquet_bytes,
        metadata_bytes=metadata_bytes,
        scenario="C070_G100",
        source_sha=APPROVED_SOURCE_SHA,
        master_seed=20270101,
        sampling_policy_id="DOUBLING_FROM_300_V1",
    )
    with pytest.raises(StateIntegrityError, match="manifest mismatch|Parquet block bytes"):
        validate_durable_block_identity(
            identity=identity,
            metadata=metadata,
            parquet_bytes=parquet_bytes + b"changed",
            metadata_bytes=metadata_bytes,
            scenario="C070_G100",
            source_sha=APPROVED_SOURCE_SHA,
            master_seed=20270101,
            sampling_policy_id="DOUBLING_FROM_300_V1",
        )


def test_durable_block_manifest_rejects_source_or_seed_drift() -> None:
    parquet_bytes = b"block"
    metadata = {
        "schema_version": "stage7-block-v1",
        "scenario": "C070_G100",
        "source_sha": APPROVED_SOURCE_SHA,
        "master_seed": 20270101,
        "rng_policy_id": STAGE7_RNG_POLICY_ID,
        "sampling_policy_id": "DOUBLING_FROM_300_V1",
        "trial_id_start": 1,
        "trial_id_end": 1,
        "trial_count": 1,
        "fingerprint_sha256": "a" * 64,
        "parquet_sha256": hashlib.sha256(parquet_bytes).hexdigest(),
        "per_trial_sha256": ["b" * 64],
        "run_id": "123",
    }
    metadata_bytes = (
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    for expected in (
        {"source_sha": "e" * 40, "master_seed": 20270101},
        {"source_sha": APPROVED_SOURCE_SHA, "master_seed": 20270102},
    ):
        with pytest.raises(StateIntegrityError):
            build_durable_block_identity(
                metadata=metadata,
                parquet_bytes=parquet_bytes,
                metadata_bytes=metadata_bytes,
                scenario="C070_G100",
                source_sha=expected["source_sha"],
                master_seed=expected["master_seed"],
                sampling_policy_id="DOUBLING_FROM_300_V1",
            )


def test_git_blob_sha_uses_git_object_header() -> None:
    assert _git_blob_sha(b"") == "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"


class InMemoryDurableBlockStore(StateStore):
    def __init__(self, local_path: Path) -> None:
        super().__init__(
            repo="example/repo",
            token="token",
            scenario="C070_G100",
            source_sha=APPROVED_SOURCE_SHA,
            run_id="900",
            run_attempt="1",
            local_path=local_path,
        )
        self.head = "base-head"
        self.files: dict[str, bytes] = {}
        self.blobs: dict[str, bytes] = {}
        self.trees: dict[str, dict] = {"base-tree": {"tree": []}}
        self.commits: dict[str, str] = {"base-head": "base-tree"}
        self.counter = 0
        initial_state = {
            "stage": "7",
            "scenario": "C070_G100",
            "source_sha": APPROVED_SOURCE_SHA,
            "completed_trials": 2,
            "next_trial_id": 3,
            "stability_history": [],
            "final_fingerprint": "a" * 64,
            "artifact_identity": None,
            "lease": None,
        }
        raw = (json.dumps(initial_state, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        self.files["state.json"] = raw
        self.blobs[_git_blob_sha(raw)] = raw

    def _request(self, method, path, payload=None):
        if method == "GET" and path == self._branch_ref_path():
            return {"object": {"sha": self.head}}
        if method == "GET" and path == f"git/commits/{self.head}":
            return {"tree": {"sha": self.commits[self.head]}}
        if method == "GET" and path.startswith("contents/"):
            route = path.split("?", 1)[0]
            route = urllib.parse.unquote(route[len("contents/"):])
            if route == "stage7-blocks":
                items = [
                    {
                        "name": item_path.rsplit("/", 1)[-1],
                        "path": item_path,
                        "type": "file",
                        "sha": _git_blob_sha(raw),
                    }
                    for item_path, raw in sorted(self.files.items())
                    if item_path.startswith("stage7-blocks/")
                ]
                if not items:
                    raise StateRemoteNotFound("no durable blocks")
                return items
            if route not in self.files:
                raise StateRemoteNotFound(f"missing file {route}")
            raw = self.files[route]
            return {
                "type": "file",
                "sha": _git_blob_sha(raw),
                "encoding": "base64",
                "content": base64.b64encode(raw).decode("ascii"),
            }
        if method == "GET" and path.startswith("git/blobs/"):
            sha = path.rsplit("/", 1)[-1]
            raw = self.blobs[sha]
            return {
                "sha": sha,
                "encoding": "base64",
                "content": base64.b64encode(raw).decode("ascii"),
            }
        if method == "POST" and path == "git/blobs":
            raw = base64.b64decode(payload["content"])
            sha = _git_blob_sha(raw)
            self.blobs[sha] = raw
            return {"sha": sha}
        if method == "POST" and path == "git/trees":
            self.counter += 1
            sha = f"tree-{self.counter}"
            self.trees[sha] = payload
            return {"sha": sha}
        if method == "POST" and path == "git/commits":
            self.counter += 1
            sha = f"commit-{self.counter}"
            self.commits[sha] = payload["tree"]
            return {"sha": sha}
        if method == "PATCH" and path == self._branch_refs_path():
            self.head = payload["sha"]
            tree = self.trees[self.commits[self.head]]
            for entry in tree["tree"]:
                self.files[entry["path"]] = self.blobs[entry["sha"]]
            return {"ref": self.state_branch}
        raise AssertionError(f"unexpected fake GitHub request: {method} {path}")


def test_durable_block_and_state_commit_atomically_and_restore(tmp_path: Path) -> None:
    store = InMemoryDurableBlockStore(tmp_path / "state.json")
    block_dir = tmp_path / "results_stage7" / "C070_G100" / "blocks"
    block_dir.mkdir(parents=True)
    parquet_bytes = b"deterministic-test-block-bytes"
    parquet_path = block_dir / "block_1_2.parquet"
    parquet_path.write_bytes(parquet_bytes)
    metadata = {
        "schema_version": "stage7-block-v1",
        "scenario": "C070_G100",
        "source_sha": APPROVED_SOURCE_SHA,
        "master_seed": 20270101,
        "rng_policy_id": STAGE7_RNG_POLICY_ID,
        "sampling_policy_id": "DOUBLING_FROM_300_V1",
        "trial_id_start": 1,
        "trial_id_end": 2,
        "trial_count": 2,
        "fingerprint_sha256": "a" * 64,
        "parquet_sha256": hashlib.sha256(parquet_bytes).hexdigest(),
        "per_trial_sha256": ["b" * 64, "c" * 64],
        "run_id": "123",
    }
    metadata_path = block_dir / "block_1_2_metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    state = {
        "stage": "7",
        "scenario": "C070_G100",
        "source_sha": APPROVED_SOURCE_SHA,
        "completed_trials": 2,
        "next_trial_id": 3,
        "stability_history": [],
        "final_fingerprint": "a" * 64,
        "artifact_identity": None,
        "lease": None,
    }
    blob_sha = store.persist_trial_blocks_and_state(
        block_pairs=[(parquet_path, metadata_path)],
        state=state,
        blob_sha=None,
        master_seed=20270101,
        sampling_policy_id="DOUBLING_FROM_300_V1",
    )
    assert store.head.startswith("commit-")
    assert "stage7-blocks/block_1_2.parquet" in store.files
    assert "stage7-blocks/block_1_2_metadata.json" in store.files
    assert "stage7-blocks/block_1_2_identity.json" in store.files
    assert json.loads(store.files["state.json"].decode("utf-8"))["completed_trials"] == 2
    assert blob_sha == _git_blob_sha(store.files["state.json"])

    restored = store.restore_trial_blocks(
        output_dir=tmp_path / "restored_results",
        master_seed=20270101,
        sampling_policy_id="DOUBLING_FROM_300_V1",
        expected_completed_trials=2,
    )
    assert restored == 1
    assert (tmp_path / "restored_results" / "C070_G100" / "blocks" / "block_1_2.parquet").read_bytes() == parquet_bytes
    assert (tmp_path / "restored_results" / "C070_G100" / "blocks" / "block_1_2_metadata.json").read_bytes() == metadata_path.read_bytes()



def test_durable_block_store_appends_next_chunk_without_rewriting_prefix(tmp_path: Path) -> None:
    store = InMemoryDurableBlockStore(tmp_path / "state.json")
    block_dir = tmp_path / "results_stage7" / "C070_G100" / "blocks"
    block_dir.mkdir(parents=True)

    def make_pair(start_id: int, end_id: int) -> tuple[Path, Path]:
        parquet_bytes = f"fixture-block-{start_id}-{end_id}".encode("ascii")
        parquet_path = block_dir / f"block_{start_id}_{end_id}.parquet"
        parquet_path.write_bytes(parquet_bytes)
        metadata = {
            "schema_version": "stage7-block-v1",
            "scenario": "C070_G100",
            "source_sha": APPROVED_SOURCE_SHA,
            "master_seed": 20270101,
            "rng_policy_id": STAGE7_RNG_POLICY_ID,
            "sampling_policy_id": "DOUBLING_FROM_300_V1",
            "trial_id_start": start_id,
            "trial_id_end": end_id,
            "trial_count": end_id - start_id + 1,
            "fingerprint_sha256": hashlib.sha256(parquet_bytes).hexdigest(),
            "parquet_sha256": hashlib.sha256(parquet_bytes).hexdigest(),
            "per_trial_sha256": [
                hashlib.sha256(f"trial-{trial_id}".encode("ascii")).hexdigest()
                for trial_id in range(start_id, end_id + 1)
            ],
            "run_id": "123",
        }
        metadata_path = block_dir / f"block_{start_id}_{end_id}_metadata.json"
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return parquet_path, metadata_path

    state = {
        "stage": "7",
        "scenario": "C070_G100",
        "source_sha": APPROVED_SOURCE_SHA,
        "completed_trials": 2,
        "next_trial_id": 3,
        "stability_history": [],
        "final_fingerprint": "a" * 64,
        "artifact_identity": None,
        "lease": None,
    }
    first_pair = make_pair(1, 2)
    store.persist_trial_blocks_and_state(
        block_pairs=[first_pair],
        state=state,
        blob_sha=None,
        master_seed=20270101,
        sampling_policy_id="DOUBLING_FROM_300_V1",
    )
    first_blob = _git_blob_sha(store.files["stage7-blocks/block_1_2.parquet"])

    second_pair = make_pair(3, 4)
    state["completed_trials"] = 4
    state["next_trial_id"] = 5
    state["final_fingerprint"] = "d" * 64
    store.persist_trial_blocks_and_state(
        block_pairs=[second_pair],
        state=state,
        blob_sha=None,
        master_seed=20270101,
        sampling_policy_id="DOUBLING_FROM_300_V1",
    )

    assert _git_blob_sha(store.files["stage7-blocks/block_1_2.parquet"]) == first_blob
    assert "stage7-blocks/block_3_4.parquet" in store.files
    assert json.loads(store.files["state.json"].decode("utf-8"))["completed_trials"] == 4
    assert store.restore_trial_blocks(
        output_dir=tmp_path / "restored",
        master_seed=20270101,
        sampling_policy_id="DOUBLING_FROM_300_V1",
        expected_completed_trials=4,
    ) == 2


def test_durable_block_restore_fails_closed_on_missing_identity_sidecar(tmp_path: Path) -> None:
    store = InMemoryDurableBlockStore(tmp_path / "state.json")
    block_dir = tmp_path / "results" / "C070_G100" / "blocks"
    block_dir.mkdir(parents=True)
    parquet_bytes = b"block"
    parquet_path = block_dir / "block_1_2.parquet"
    parquet_path.write_bytes(parquet_bytes)
    metadata = {
        "schema_version": "stage7-block-v1",
        "scenario": "C070_G100",
        "source_sha": APPROVED_SOURCE_SHA,
        "master_seed": 20270101,
        "rng_policy_id": STAGE7_RNG_POLICY_ID,
        "sampling_policy_id": "DOUBLING_FROM_300_V1",
        "trial_id_start": 1,
        "trial_id_end": 2,
        "trial_count": 2,
        "fingerprint_sha256": "a" * 64,
        "parquet_sha256": hashlib.sha256(parquet_bytes).hexdigest(),
        "per_trial_sha256": ["b" * 64, "c" * 64],
        "run_id": "123",
    }
    metadata_path = block_dir / "block_1_2_metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    state = {
        "stage": "7",
        "scenario": "C070_G100",
        "source_sha": APPROVED_SOURCE_SHA,
        "completed_trials": 2,
        "next_trial_id": 3,
        "stability_history": [],
        "final_fingerprint": "a" * 64,
        "artifact_identity": None,
        "lease": None,
    }
    store.persist_trial_blocks_and_state(
        block_pairs=[(parquet_path, metadata_path)],
        state=state,
        blob_sha=None,
        master_seed=20270101,
        sampling_policy_id="DOUBLING_FROM_300_V1",
    )
    del store.files["stage7-blocks/block_1_2_identity.json"]

    with pytest.raises(StateIntegrityError, match="triplet sets differ"):
        store.restore_trial_blocks(
            output_dir=tmp_path / "restored",
            master_seed=20270101,
            sampling_policy_id="DOUBLING_FROM_300_V1",
            expected_completed_trials=2,
        )


def test_legacy_block_migration_requires_verified_workflow_seed_and_source() -> None:
    parquet_bytes = b"legacy-block"
    metadata = {
        "scenario": "C070_G100",
        "source_sha": APPROVED_SOURCE_SHA,
        "trial_id_start": 1,
        "trial_id_end": 1,
        "trial_count": 1,
        "fingerprint_sha256": hashlib.sha256(parquet_bytes).hexdigest(),
        "per_trial_sha256": [hashlib.sha256(b"legacy-trial-1").hexdigest()],
        "run_id": "legacy-run-1",
    }
    metadata_bytes = (
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    kwargs = {
        "metadata": metadata,
        "parquet_bytes": parquet_bytes,
        "metadata_bytes": metadata_bytes,
        "scenario": "C070_G100",
        "source_sha": APPROVED_SOURCE_SHA,
        "master_seed": 20270101,
        "sampling_policy_id": "DOUBLING_FROM_300_V1",
        "allow_legacy_metadata": True,
    }
    with pytest.raises(StateIntegrityError, match="verified previous-run workflow identity"):
        build_durable_block_identity(**kwargs)

    proof = {
        "schema_version": "stage7-legacy-run-identity-v1",
        "scenario": "C070_G100",
        "source_sha": APPROVED_SOURCE_SHA,
        "master_seed": 20270101,
        "verified_runs": {
            "legacy-run-1": {
                "run_id": "legacy-run-1",
                "scenario": "C070_G100",
                "source_sha": APPROVED_SOURCE_SHA,
                "master_seed": 20270101,
                "head_sha": "d" * 40,
                "workflow_blob_sha": "e" * 40,
                "workflow_source_sha": APPROVED_SOURCE_SHA,
                "workflow_master_seed": 20270101,
            }
        },
    }
    identity = build_durable_block_identity(
        **kwargs,
        legacy_identity_proof=proof,
    )
    validate_durable_block_identity(
        identity=identity,
        metadata=metadata,
        parquet_bytes=parquet_bytes,
        metadata_bytes=metadata_bytes,
        scenario="C070_G100",
        source_sha=APPROVED_SOURCE_SHA,
        master_seed=20270101,
        sampling_policy_id="DOUBLING_FROM_300_V1",
    )
    assert identity["legacy_metadata_migrated"] is True
    assert identity["legacy_identity_proof"]["run_id"] == "legacy-run-1"


def test_stage7_workflow_commits_durable_blocks_before_moving_past_each_chunk() -> None:
    text = _workflow_text()
    assert "MAX_TRIALS_PER_BLOCK = 50" in text
    assert "restore_trial_blocks(" in text
    assert "persist_trial_blocks_and_state(" in text
    assert "LEGACY_BLOCK_IDENTITY_UNPROVEN" in text
    assert "STAGE7_STATE_IDENTITY_MISMATCH=" in text
    assert "stage7-legacy-run-identity-v1" in text
    assert "job wall-clock timeout reached" not in text


def test_requirements_include_pyyaml() -> None:
    requirements = (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "pyyaml" in requirements.lower()

def test_stage7_workflow_pins_approved_source_sha() -> None:
    assert _workflow()["env"]["SOURCE_SHA"] == APPROVED_SOURCE_SHA

def test_stage7_workflow_has_no_dynamic_origin_main_source_resolution() -> None:
    text = _workflow_text()
    assert "git rev-parse origin/main" not in text
    assert "Determine stable source SHA from main" not in text
    assert "steps.source.outputs.source_sha" not in text

def test_stage7_workflow_declares_model_source_boundary() -> None:
    text = _workflow_text()
    for path in MODEL_FILES:
        assert path in text

def test_stage7_workflow_verifies_pinned_commit_and_model_integrity() -> None:
    text = _workflow_text()
    assert 'git cat-file -e "${SOURCE_SHA}^{commit}"' in text
    assert "MODEL_SOURCE_DRIFT_DETECTED" in text
    assert "MODEL_SOURCE_BOUNDARY_OK" in text

def test_stage7_source_sha_is_passed_to_matrix_state_and_orchestrator() -> None:
    steps = _workflow()["jobs"]["matrix-simulation"]["steps"]
    env_blocks = [step.get("env", {}) for step in steps if isinstance(step, dict)]
    assert any(block.get("SOURCE_SHA") == "${{ env.SOURCE_SHA }}" for block in env_blocks)

def test_stage7_still_declares_exactly_25_scenarios() -> None:
    scenarios = _workflow()["jobs"]["matrix-simulation"]["strategy"]["matrix"]["scenario"]
    assert len(scenarios) == 25
    assert len(set(scenarios)) == 25

def test_stage7_authoring_verify_runs_contract_tests() -> None:
    assert "tests/test_stage7_authoring.py" in AUTHORING_VERIFY.read_text(encoding="utf-8")

def test_stage7_trial_block_records_source_sha_in_metadata() -> None:
    text = TRIAL_BLOCK.read_text(encoding="utf-8")
    assert '"source_sha": source_sha' in text
    assert '"master_seed": master_seed' in text
    assert '"rng_policy_id": STAGE7_RNG_POLICY_ID' in text
    assert '"sampling_policy_id": STATISTICAL_ESCALATION_POLICY_ID' in text
    assert '"parquet_sha256": parquet_sha256' in text

def test_stage7_has_no_internal_wall_clock_cutoff() -> None:
    text = _workflow_text()
    assert "JOB_TIMEOUT_MINUTES" not in text
    assert "JOB_TIMEOUT_SECONDS" not in text
    assert "job wall-clock timeout reached" not in text


def test_stage7_external_timeout_uses_hosted_runner_ceiling() -> None:
    matrix = _workflow()["jobs"]["matrix-simulation"]
    assert matrix["timeout-minutes"] == 360


def test_stage7_parallelizes_all_25_scenarios_when_runner_capacity_allows() -> None:
    workflow = _workflow()
    matrix = workflow["jobs"]["matrix-simulation"]["strategy"]
    assert matrix["max-parallel"] == 25
    scenarios = matrix["matrix"]["scenario"]
    assert len(scenarios) == 25
    assert len(set(scenarios)) == 25
    assert matrix["fail-fast"] is False


def test_stage7_summary_fails_closed_unless_all_scenarios_are_accepted() -> None:
    text = _workflow_text()
    assert "STAGE7_FAIL_CLOSED" in text
    assert 'row.get("final_status") == "stable"' in text
    assert 'row.get("final_stats_included") is True' in text
    assert "stable_count == expected_scenarios" in text
    assert "raise SystemExit(1)" in text

def test_stage7_workflow_has_concurrency_guard() -> None:
    text = _workflow_text()
    concurrency = _workflow()["concurrency"]
    assert concurrency == {
        "group": "stage7-full-run-${{ github.ref }}",
        "cancel-in-progress": False,
    }
    concurrency_text = text[text.index("concurrency:"):text.index("permissions:")]
    assert "${{ github.run_id }}" not in concurrency_text


def test_stage7_preflight_cancels_and_waits_for_stale_stage7_runs() -> None:
    text = _workflow_text()
    preflight = text[text.index("  preflight-gates:"):text.index("  matrix-simulation:")]
    assert "actions: write" in text[:text.index("jobs:")]
    assert "GH_TOKEN: ${{ github.token }}" in preflight
    assert "gh api --paginate" in preflight
    assert "actions/runs?branch=tmp%2Fstage7-full-run-20261004" in preflight
    assert "select(.conclusion == null)" in preflight
    assert "actions/runs/${run_id}/cancel" in preflight
    assert "CANCELLED_STALE_RUN=" in preflight
    assert "STALE_RUN_CANCELLATION_TIMEOUT=" in preflight
    assert "for attempt in $(seq 1 90); do" in preflight
    assert "STALE_RUN_STOPPED=" in preflight


def test_stage7_preflight_resets_all_scenario_state_branches() -> None:
    text = _workflow_text()
    preflight = text[text.index("  preflight-gates:"):text.index("  matrix-simulation:")]
    assert "SCENARIOS=(" in preflight
    assert "C100_G100 C100_G070 C100_G050 C100_G030 C100_G000" in preflight
    assert "C085_G100 C085_G070 C085_G050 C085_G030 C085_G000" in preflight
    assert "C070_G100 C070_G070 C070_G050 C070_G030 C070_G000" in preflight
    assert "C050_G100 C050_G070 C050_G050 C050_G030 C050_G000" in preflight
    assert "C030_G100 C030_G070 C030_G050 C030_G030 C030_G000" in preflight
    assert "STAGE7_STATE_RESET=" in preflight
    assert "STAGE7_STATE_ABSENT=" in preflight
    assert "git/refs/heads/${STATE_BRANCH}" in preflight
    assert '-f "sha=${SOURCE_SHA}"' in preflight
    assert "-F force=true" in preflight


def test_stage7_preflight_preserves_state_for_same_run_and_resets_other_runs() -> None:
    text = _workflow_text()
    preflight = text[text.index("  preflight-gates:"):text.index("  matrix-simulation:")]
    assert "STATE_CONTENTS=\"repos/${GITHUB_REPOSITORY}/contents/state.json?ref=${STATE_BRANCH}\"" in preflight
    assert "jq -r '.run_id // empty'" in preflight
    assert 'if [ "${state_run_id}" = "${GITHUB_RUN_ID}" ]; then' in preflight
    assert "STAGE7_STATE_RESUME=" in preflight
    assert "STAGE7_STATE_RESET=" in preflight


def test_stage7_restore_artifacts_is_scoped_to_current_workflow_run() -> None:
    text = _workflow_text()
    start = text.index("      - name: Restore previous scenario block artifacts when available")
    end = text.index("      - name: Adaptive scenario orchestration", start)
    restore = text[start:end]
    assert "actions/runs/${GITHUB_RUN_ID}/artifacts?per_page=100" in restore
    assert "actions/artifacts?per_page=100" not in restore
    assert "STAGE7_ARTIFACT_RESTORE=RUN_ID:" in restore
    assert "stage7-blocks-" in restore

def test_stage7_job_started_at_uses_epoch_not_workflow_start() -> None:
    text = _workflow_text()
    assert "JOB_STARTED_AT_EPOCH = time.time()" in text
    assert "return time.time() - JOB_STARTED_AT_EPOCH" in text
    assert 'os.environ["JOB_STARTED_AT"]' not in text
    assert "JOB_STARTED_AT:" not in text
    assert "github.run_started_at" not in text

def _matching_golden_kwargs() -> dict[str, str]:
    fingerprint = "a" * 64
    return {
        "expected_golden_fingerprint_sha256": fingerprint,
        "actual_fingerprint_sha256": fingerprint,
        "golden_reference_id": "test-approved-golden-v1",
        "expected_source_sha": APPROVED_SOURCE_SHA,
        "actual_source_sha": APPROVED_SOURCE_SHA,
    }


def test_gate_a_first_checkpoint_can_pass_only_with_exact_golden() -> None:
    current = _metrics((1000, 700, 300), stable=True)
    gate_a = evaluate_gate_a(
        previous_n=None, previous_metrics=None, current_n=300,
        current_metrics=current, escalation_multiplier=2,
        relative_epsilon=0.01, absolute_epsilon=1,
        **_matching_golden_kwargs(),
    )
    assert gate_a["checked"] is True
    assert gate_a["status"] == "PASS"
    assert gate_a["stable"] is True


def test_gate_a_missing_golden_is_blocked_even_when_metrics_are_close() -> None:
    previous = _metrics((1000, 700, 300), stable=True)
    current = _metrics((1001, 700.5, 300.2), stable=True)
    gate_a = evaluate_gate_a(
        previous_n=300, previous_metrics=previous, current_n=600,
        current_metrics=current, escalation_multiplier=2,
        relative_epsilon=0.01, absolute_epsilon=1,
    )
    gate_b = evaluate_gate_b(current)
    assert gate_a["checked"] is False
    assert gate_a["stable"] is False
    assert gate_a["status"] == "BLOCKED"
    assert gate_b["stable"] is True
    assert not (gate_a["stable"] and gate_b["stable"])


def test_gate_a_exact_fingerprint_pass_gate_b_fail_is_not_stable() -> None:
    previous = _metrics((1000, 700, 300), stable=False)
    current = _metrics((1001, 700.5, 300.2), stable=False)
    gate_a = evaluate_gate_a(
        previous_n=300, previous_metrics=previous, current_n=600,
        current_metrics=current, escalation_multiplier=2,
        relative_epsilon=0.01, absolute_epsilon=1,
        **_matching_golden_kwargs(),
    )
    gate_b = evaluate_gate_b(current)
    assert gate_a["status"] == "PASS"
    assert gate_a["stable"] is True
    assert gate_b["stable"] is False
    assert not (gate_a["stable"] and gate_b["stable"])


def test_gate_a_fingerprint_mismatch_gate_b_pass_is_not_stable() -> None:
    previous = _metrics((1000, 700, 300), stable=True)
    current = _metrics((1105, 770, 330), stable=True)
    wrong_actual = {
        **_matching_golden_kwargs(),
        "actual_fingerprint_sha256": "b" * 64,
    }
    gate_a = evaluate_gate_a(
        previous_n=300, previous_metrics=previous, current_n=600,
        current_metrics=current, escalation_multiplier=2,
        relative_epsilon=0.01, absolute_epsilon=1,
        **wrong_actual,
    )
    gate_b = evaluate_gate_b(current)
    assert gate_a["checked"] is True
    assert gate_a["status"] == "FAIL"
    assert gate_a["stable"] is False
    assert gate_b["stable"] is True
    assert not (gate_a["stable"] and gate_b["stable"])


def test_gate_a_fingerprint_mismatch_gate_b_fail_is_not_stable() -> None:
    previous = _metrics((1000, 700, 300), stable=False)
    current = _metrics((1105, 770, 330), stable=False)
    wrong_actual = {
        **_matching_golden_kwargs(),
        "actual_fingerprint_sha256": "b" * 64,
    }
    gate_a = evaluate_gate_a(
        previous_n=300, previous_metrics=previous, current_n=600,
        current_metrics=current, escalation_multiplier=2,
        relative_epsilon=0.01, absolute_epsilon=1,
        **wrong_actual,
    )
    gate_b = evaluate_gate_b(current)
    assert gate_a["status"] == "FAIL"
    assert gate_a["stable"] is False
    assert gate_b["stable"] is False
    assert not (gate_a["stable"] and gate_b["stable"])


def test_gate_a_exact_golden_and_gate_b_pass_requires_three_consecutive_points() -> None:
    previous = _metrics((1000, 700, 300), stable=True)
    p600 = _metrics((1001, 700.5, 300.2), stable=True)
    p1200 = _metrics((1002, 701.0, 300.4), stable=True)
    p2400 = _metrics((1003, 701.5, 300.6), stable=True)
    pairs = (
        (300, previous, 600, p600),
        (600, p600, 1200, p1200),
        (1200, p1200, 2400, p2400),
    )
    checks = []
    for previous_n, previous_metrics, current_n, current_metrics in pairs:
        gate_a = evaluate_gate_a(
            previous_n=previous_n, previous_metrics=previous_metrics,
            current_n=current_n, current_metrics=current_metrics,
            escalation_multiplier=2, relative_epsilon=0.01,
            absolute_epsilon=1, **_matching_golden_kwargs(),
        )
        gate_b = evaluate_gate_b(current_metrics)
        checks.append(gate_a["stable"] and gate_b["stable"])
    assert checks == [True, True, True]


def test_gate_a_rejects_source_identity_mismatch() -> None:
    previous = _metrics((1000, 700, 300), stable=True)
    current = _metrics((1001, 700.5, 300.2), stable=True)
    fields = {
        **_matching_golden_kwargs(),
        "actual_source_sha": "e" * 40,
    }
    gate_a = evaluate_gate_a(
        previous_n=300, previous_metrics=previous, current_n=600,
        current_metrics=current, escalation_multiplier=2,
        relative_epsilon=0.01, absolute_epsilon=1, **fields,
    )
    assert gate_a["checked"] is True
    assert gate_a["stable"] is False
    assert gate_a["status"] == "FAIL"
    assert gate_a["reason"] == "golden and actual source identities differ"


def test_gate_a_rejects_malformed_fingerprint() -> None:
    previous = _metrics((1000, 700, 300), stable=True)
    current = _metrics((1001, 700.5, 300.2), stable=True)
    fields = {
        **_matching_golden_kwargs(),
        "actual_fingerprint_sha256": "not-a-sha256",
    }
    gate_a = evaluate_gate_a(
        previous_n=300, previous_metrics=previous, current_n=600,
        current_metrics=current, escalation_multiplier=2,
        relative_epsilon=0.01, absolute_epsilon=1, **fields,
    )
    assert gate_a["checked"] is True
    assert gate_a["stable"] is False
    assert gate_a["status"] == "FAIL"


def test_stage7_fails_closed_on_unverified_resume_and_stable_state() -> None:
    text = _workflow_text()
    assert 'if not SCENARIO.startswith("C100_") and completed >= INITIAL_NON_C100:' in text
    assert 'latest_status = latest_gate_a.get("status")' in text
    assert 'state.get("final_status") == "stable"' in text
    assert 'item.get("gate_a", {}).get("status") == "PASS"' in text
    assert 'GATE_A_PREFLIGHT_BLOCKED=' in text


def test_c100_n1_without_rerun_is_not_allowed_to_be_stable() -> None:
    text = _workflow_text()
    assert "C100 primary sample must remain n=1" in text
    assert '"verification_trial_id": 2' in text

def test_c100_independent_rerun_uses_different_trial_id_and_derived_seed() -> None:
    text = _workflow_text()
    assert "trial_id=2" in text
    assert "different_trial_id" in text
    assert "different_derived_seed" in text
    assert "exact_result_equality" in text

def test_c100_mismatch_cannot_be_declared_stable() -> None:
    text = _workflow_text()
    assert 'state["final_status"] = None' in text
    assert "independent C100 trial result mismatch" in text

def test_c100_verification_excludes_trial_id_from_comparison() -> None:
    text = _workflow_text()
    assert 'primary_dict = asdict(primary)' in text
    assert 'verification_dict = asdict(verification)' in text
    assert 'primary_trial_id = primary_dict.pop("trial_id")' in text
    assert 'verification_trial_id = verification_dict.pop("trial_id")' in text
    assert 'if primary_trial_id == verification_trial_id:' in text
    assert 'raise AssertionError(' in text
    assert "C100 independence requires distinct trial_id" in text
    assert 'equality = primary_dict == verification_dict' in text
    assert 'equality = asdict(primary) == asdict(verification)' not in text


def test_c100_stability_is_after_independent_equality_proof() -> None:
    text = _workflow_text()
    equality_pos = text.index("equality = primary_dict == verification_dict")
    stable_pos = text.index('state["final_status"] = "stable"')
    assert equality_pos < stable_pos

def test_gate_a_requires_exact_doubling_checkpoint() -> None:
    previous = _metrics((1000, 700, 300), stable=True)
    current = _metrics((1001, 700.5, 300.2), stable=True)
    gate_a = evaluate_gate_a(
        previous_n=300, previous_metrics=previous, current_n=601,
        current_metrics=current, escalation_multiplier=2,
        relative_epsilon=0.01, absolute_epsilon=1,
        **_matching_golden_kwargs(),
    )
    assert gate_a["checked"] is False
    assert gate_a["status"] == "BLOCKED"


def test_gate_a_does_not_substitute_metric_deltas_for_golden_equality() -> None:
    previous = _metrics((1000, 700, 300), stable=True)
    current = _metrics((1001, 900, 300.2), stable=True)
    gate_a = evaluate_gate_a(
        previous_n=300, previous_metrics=previous, current_n=600,
        current_metrics=current, escalation_multiplier=2,
        relative_epsilon=0.01, absolute_epsilon=1,
        **_matching_golden_kwargs(),
    )
    assert gate_a["status"] == "PASS"
    assert gate_a["stable"] is True


def test_stage7_preflight_does_not_rerun_passed_stages() -> None:
    text = _workflow_text()
    preflight = text[text.index("  preflight-gates:"):text.index("  matrix-simulation:")]
    forbidden = (
        "tests/test_stage1.py",
        "tests/test_stage2.py",
        "tests/test_stage3a.py",
        "tests/test_stage3b_accounting.py",
        "tests/test_stage3b_partner_equity.py",
        "tests/test_stage3b_m_order.py",
        "tests/test_stage3b_closure.py",
        "tests/test_stage3b_path1.py",
        "tests/test_stage3b_paths.py",
        "tests/test_stage3b_no_time_cap.py",
        "tests/test_stage3b_determinism.py",
        "tests/test_acceptance_16_v2.py",
        "tests/test_monte_carlo_round1.py",
        "tests/test_monte_carlo_round2.py",
        "tests/test_monte_carlo_round3.py",
        "tests/test_monte_carlo_round4.py",
    )
    for marker in forbidden:
        assert marker not in preflight


def test_stage7_preflight_is_stage7_specific() -> None:
    text = _workflow_text()
    preflight = text[text.index("  preflight-gates:"):text.index("  matrix-simulation:")]
    assert "STAGE7_PREFLIGHT_OK" in preflight
    assert "SOURCE_SHA" in preflight

def test_stage7_state_module_has_distinct_remote_404_exception() -> None:
    assert issubclass(StateRemoteNotFound, RuntimeError)
    assert "404" in Path(
        REPO_ROOT / "scripts" / "stage7_state.py"
    ).read_text(encoding="utf-8")


def test_stage7_state_module_has_retry_backoff_contract() -> None:
    text = Path(
        REPO_ROOT / "scripts" / "stage7_state.py"
    ).read_text(encoding="utf-8")
    assert "MAX_ATTEMPTS = 4" in text
    assert "RETRYABLE_HTTP_STATUS" in text
    assert "time.sleep" in text
    assert "2**attempt" in text


def test_stage7_state_module_has_concurrency_lease_contract() -> None:
    text = Path(
        REPO_ROOT / "scripts" / "stage7_state.py"
    ).read_text(encoding="utf-8")
    assert "LeaseConflict" in text
    assert "lease_owner" in text
    assert "expires_at" in text
    assert "StateConflict" in text


def test_stage7_state_module_persists_initial_state_remotely() -> None:
    text = Path(
        REPO_ROOT / "scripts" / "stage7_state.py"
    ).read_text(encoding="utf-8")
    assert "self._put_state(state, None)" in text
    assert '"completed_trials": 0' in text
    assert '"next_trial_id": 1' in text


def test_stage7_state_module_has_local_remote_sync_verification() -> None:
    text = Path(
        REPO_ROOT / "scripts" / "stage7_state.py"
    ).read_text(encoding="utf-8")
    assert "_verify_remote_equals" in text
    assert "_write_local" in text


def test_stage7_workflow_uses_transactional_state_store() -> None:
    text = _workflow_text()
    assert "StateStore(" in text
    assert "state, blob_sha = store.acquire()" in text
    assert "store.save_state(state, blob_sha)" in text
    assert "atexit.register(store.release)" in text


def test_stage7_workflow_does_not_keep_the_old_nonpersistent_initializer() -> None:
    text = _workflow_text()
    assert "Initialize or restore scenario state" not in text
    assert "StateStore(" in text


def test_stage7_pause_resume_uses_persisted_next_trial_id() -> None:
    text = _workflow_text()
    assert 'run_attempt=os.environ["RUN_ATTEMPT"]' in text
    assert "next_trial_id = int(" in text
    assert "validate_trial_sequence(" in text


def test_stage7_artifact_identity_contains_exact_required_identity_fields() -> None:
    identity = build_artifact_identity(
        scenario="C070_G100",
        source_sha=APPROVED_SOURCE_SHA,
        trial_id_start=1,
        trial_id_end=300,
        fingerprint_sha256="abc123",
    )
    assert identity == {
        "scenario": "C070_G100",
        "source_sha": APPROVED_SOURCE_SHA,
        "trial_id_start": 1,
        "trial_id_end": 300,
        "fingerprint_sha256": "abc123",
    }


def test_stage7_trial_sequence_rejects_gap_and_duplicate() -> None:
    with pytest.raises(StateIntegrityError):
        validate_trial_sequence(
            trial_ids=[1, 2, 4],
            completed_trials=3,
            next_trial_id=4,
        )
    with pytest.raises(StateIntegrityError):
        validate_trial_sequence(
            trial_ids=[1, 2, 2],
            completed_trials=3,
            next_trial_id=4,
        )


def test_stage7_trial_sequence_accepts_exact_resume_boundary() -> None:
    validate_trial_sequence(
        trial_ids=list(range(1, 6)),
        completed_trials=5,
        next_trial_id=6,
    )


def test_stage7_workflow_binds_artifact_identity_to_state_and_final_artifact() -> None:
    text = _workflow_text()
    assert 'state["artifact_identity"] = build_artifact_identity(' in text
    assert '"artifact_identity": state["artifact_identity"]' in text


def test_stage7_cp3_pending_is_not_encoded_as_false() -> None:
    text = _workflow_text()
    report = text[text.index("  final-report:"):]
    assert "cp3_match = None" in report
    assert "cp3_match = False" not in report

def test_cp3_cross_reference_compares_only_overlapping_range() -> None:
    text = _workflow_text()
    start = text.index('if SCENARIO == CP3_SCENARIO:')
    end = text.index('write_json(', start)
    cross_reference = text[start:end]

    assert "cp3_overlap = min(" in cross_reference
    assert "len(results)" in cross_reference
    assert "len(cp3_results)" in cross_reference
    assert "1 <= result.trial_id <= cp3_overlap" in cross_reference
    assert "fingerprint_trial_results(stage7_prefix)" in cross_reference
    assert "fingerprint_trial_results(cp3_prefix)" in cross_reference
    assert "trial_id <= 6000" not in cross_reference
    assert "CP3_AGGREGATE_SHA256" not in cross_reference


def test_same_run_id_different_attempt_is_allowed_by_lease() -> None:
    store = StateStore(
        repo="example/repo",
        token="token",
        scenario="C070_G100",
        source_sha=APPROVED_SOURCE_SHA,
        run_id="100",
        run_attempt="2",
        local_path=REPO_ROOT / "state.json",
    )
    now = datetime.now(timezone.utc)
    lease = {
        "owner": "100",
        "run_id": "100",
        "run_attempt": 1,
        "acquired_at": (
            now - timedelta(minutes=1)
        ).isoformat().replace("+00:00", "Z"),
        "expires_at": (
            now + timedelta(minutes=10)
        ).isoformat().replace("+00:00", "Z"),
    }
    assert store._lease_is_active_for_other_owner(lease) is False


def test_different_run_id_is_rejected_while_lease_is_active() -> None:
    store = StateStore(
        repo="example/repo",
        token="token",
        scenario="C070_G100",
        source_sha=APPROVED_SOURCE_SHA,
        run_id="200",
        run_attempt="1",
        local_path=REPO_ROOT / "state.json",
    )
    now = datetime.now(timezone.utc)
    lease = {
        "owner": "100",
        "run_id": "100",
        "run_attempt": 1,
        "acquired_at": (
            now - timedelta(minutes=1)
        ).isoformat().replace("+00:00", "Z"),
        "expires_at": (
            now + timedelta(minutes=10)
        ).isoformat().replace("+00:00", "Z"),
    }
    assert store._lease_is_active_for_other_owner(lease) is True


def test_expired_lease_is_available_to_a_new_run_id() -> None:
    store = StateStore(
        repo="example/repo",
        token="token",
        scenario="C070_G100",
        source_sha=APPROVED_SOURCE_SHA,
        run_id="200",
        run_attempt="1",
        local_path=REPO_ROOT / "state.json",
    )
    now = datetime.now(timezone.utc)
    lease = {
        "owner": "100",
        "run_id": "100",
        "run_attempt": 1,
        "acquired_at": (
            now - timedelta(minutes=20)
        ).isoformat().replace("+00:00", "Z"),
        "expires_at": (
            now - timedelta(minutes=10)
        ).isoformat().replace("+00:00", "Z"),
    }
    assert store._lease_is_active_for_other_owner(lease) is False


def test_stage7_state_module_documents_same_run_id_re_run_policy() -> None:
    text = Path(
        REPO_ROOT / "scripts" / "stage7_state.py"
    ).read_text(encoding="utf-8")
    assert "Same run_id across GitHub re-runs is one logical lease owner." in text
    assert "run_attempt is retained in the record for auditability only." in text

def test_stage7_operational_limits_are_external_only() -> None:
    text = _workflow_text()
    assert "JOB_TIMEOUT_MINUTES" not in text
    matrix = _workflow()["jobs"]["matrix-simulation"]
    assert matrix["timeout-minutes"] == 360
    assert matrix["strategy"]["max-parallel"] == 25


def test_stage7_workflow_no_longer_exports_unused_log_events_setting() -> None:
    text = _workflow_text()
    assert 'LOG_EVENTS:' not in text
    assert 'os.environ["LOG_EVENTS"]' not in text


def test_stage7_timeout_state_is_excluded_from_final_statistics() -> None:
    text = _workflow_text()
    assert 'state["included_in_final_stats"] = False' in text
    assert '"final_stats_included": False' in text


def test_stage7_final_report_distinguishes_404_from_other_state_errors() -> None:
    text = _workflow_text()
    assert "STATE_NOT_FOUND_404" in text
    assert "STATE_REMOTE_HTTP_ERROR_" in text
    assert "STATE_REMOTE_TRANSPORT_ERROR" in text


def test_stage7_final_report_excludes_timeout_partial_counts() -> None:
    text = _workflow_text()
    assert 'is_timeout = state.get("final_status") == "timeout"' in text
    assert '"final_trial_count": None if is_timeout else' in text
    assert '"final_fingerprint": None if is_timeout else' in text
    assert "STAGE7_FAIL_CLOSED" in text


def test_stage7_final_report_uses_actual_uploaded_state_path() -> None:
    text = _workflow_text()
    assert '**/stage7-final-{scenario}-*/state.json' in text


def test_stage7_final_report_reports_state_path_and_error_count() -> None:
    text = _workflow_text()
    assert '"state_path": f"stage7-state/{scenario}/state.json"' in text
    assert '"error_count": error_count' in text


def test_stage7_state_initial_stats_inclusion_is_false() -> None:
    text = Path(
        REPO_ROOT / "scripts" / "stage7_state.py"
    ).read_text(encoding="utf-8")
    assert '"included_in_final_stats": False' in text


def test_stage7_authoring_verify_parses_all_stage7_helpers() -> None:
    text = AUTHORING_VERIFY.read_text(encoding="utf-8")
    assert "scripts/stage7_run_trial_block.py" in text
    assert "scripts/stage7_state.py" in text
    assert "scripts/stage7_stability.py" in text


def test_stage7_state_store_rejects_stage_6_5_schema() -> None:
    store = StateStore(
        repo="example/repo",
        token="token",
        scenario="C070_G100",
        source_sha=APPROVED_SOURCE_SHA,
        run_id="100",
        run_attempt="1",
        local_path=REPO_ROOT / "state.json",
    )
    state = {
        "stage": "6.5",
        "cp_completed": "CP5",
        "sha": "15b5c6e2c54ade5c1ddce07aecdc53d86a60ad95",
        "next": "stage7",
        "blockers": [],
    }
    with pytest.raises(StateIntegrityError):
        store._validate_identity(state)


def test_stage7_state_store_accepts_only_stage_7_schema() -> None:
    store = StateStore(
        repo="example/repo",
        token="token",
        scenario="C070_G100",
        source_sha=APPROVED_SOURCE_SHA,
        run_id="100",
        run_attempt="1",
        local_path=REPO_ROOT / "state.json",
    )
    state = {
        "stage": "7",
        "scenario": "C070_G100",
        "source_sha": APPROVED_SOURCE_SHA,
        "completed_trials": 0,
        "next_trial_id": 1,
        "stability_history": [],
    }
    store._validate_identity(state)


def test_stage7_new_branch_does_not_inherit_root_state() -> None:
    root_state = {
        "stage": "6.5",
        "cp_completed": "CP5",
        "sha": "15b5c6e2c54ade5c1ddce07aecdc53d86a60ad95",
        "next": "stage7",
        "blockers": [],
    }

    class FakeSourceBackedStateStore(StateStore):
        def __init__(self) -> None:
            super().__init__(
                repo="example/repo",
                token="token",
                scenario="C070_G100",
                source_sha=APPROVED_SOURCE_SHA,
                run_id="100",
                run_attempt="1",
                local_path=REPO_ROOT / "state.json",
            )
            self.branch_sha = APPROVED_SOURCE_SHA
            self.state = dict(root_state)
            self.state_blob_sha = "root-state-blob"
            self.put_payloads = []

        def _request(self, method, path, payload=None):
            if method == "GET" and path == self._branch_ref_path():
                return {"object": {"sha": self.branch_sha}}
            if method == "GET" and path == self._state_contents_path():
                raw = json.dumps(self.state).encode("utf-8")
                return {
                    "sha": self.state_blob_sha,
                    "content": base64.b64encode(raw).decode("ascii"),
                }
            if method == "PUT" and path == "contents/state.json":
                self.put_payloads.append(dict(payload))
                raw = base64.b64decode(payload["content"]).decode("utf-8")
                self.state = json.loads(raw)
                self.state_blob_sha = "stage7-state-blob"
                self.branch_sha = "stage7-checkpoint-commit"
                return {"content": {"sha": self.state_blob_sha}}
            raise AssertionError(f"unexpected request: {method} {path}")

    store = FakeSourceBackedStateStore()
    state, _ = store.acquire()

    assert store.branch_sha != APPROVED_SOURCE_SHA
    assert store.put_payloads[0]["sha"] == "root-state-blob"
    assert state["stage"] == "7"
    assert state["scenario"] == "C070_G100"
    assert state["source_sha"] == APPROVED_SOURCE_SHA
    assert state["completed_trials"] == 0
    assert state["next_trial_id"] == 1
    assert state["stability_history"] == []
    assert store.state["stage"] == "7"

def test_stage7_statistical_policy_is_the_approved_doubling_policy() -> None:
    from scripts.stage7_stability import is_statistical_checkpoint, next_statistical_checkpoint

    assert _workflow()["env"]["ESCALATION_MULTIPLIER"] == "2"
    assert _workflow()["env"]["INITIAL_NON_C100_TRIALS"] == "300"
    assert [next_statistical_checkpoint(n) for n in (0, 300, 350, 600, 1200)] == [
        300, 600, 600, 1200, 2400
    ]
    assert all(is_statistical_checkpoint(n) for n in (300, 600, 1200, 2400))
    assert not any(is_statistical_checkpoint(n) for n in (350, 400, 450, 500, 550))
