from __future__ import annotations

import base64
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

RETRYABLE_HTTP_STATUS = frozenset({429, 500, 502, 503, 504})
MAX_ATTEMPTS = 4
RETRY_BASE_SECONDS = 1.0
DEFAULT_LEASE_SECONDS = 3600

RNG_POLICY_ID = "RNG_SHA256_DERIVED_V1"
SAMPLING_POLICY_ID = "SAMPLING_ADAPTIVE_1_300_PLUS50_V1"
STABILITY_POLICY_ID = "STABILITY_GATES_A_B_3_CONSECUTIVE_V1"
TRIAL_ID_POLICY_ID = "TRIAL_ID_SEQ_1_TO_N_NO_GAPS_V1"
STATE_SCHEMA_VERSION = "stage7_state_v2"


class StateRemoteNotFound(RuntimeError):
    """Remote state does not exist; distinct from transient failure."""


class StateConflict(RuntimeError):
    """Remote state changed concurrently or already exists."""


class LeaseConflict(RuntimeError):
    """Another workflow currently owns the scenario state lease."""


def build_artifact_identity(
    *,
    scenario: str,
    source_sha: str,
    trial_id_start: int,
    trial_id_end: int,
    fingerprint_sha256: str,
) -> dict[str, object]:
    if trial_id_start < 1:
        raise ValueError("trial_id_start must be >= 1")
    if trial_id_end < trial_id_start:
        raise ValueError("trial_id_end must be >= trial_id_start")
    return {
        "scenario": scenario,
        "source_sha": source_sha,
        "trial_id_start": trial_id_start,
        "trial_id_end": trial_id_end,
        "fingerprint_sha256": fingerprint_sha256,
    }


def build_stage7_identity_v2(
    *,
    source_sha: str,
    master_seed: int,
    scenario: str,
    dataset_fingerprint: str,
) -> dict[str, object]:
    return {
        "source_sha": source_sha,
        "master_seed": int(master_seed),
        "rng_policy_id": RNG_POLICY_ID,
        "sampling_policy_id": SAMPLING_POLICY_ID,
        "stability_policy_id": STABILITY_POLICY_ID,
        "trial_id_policy_id": TRIAL_ID_POLICY_ID,
        "state_schema_version": STATE_SCHEMA_VERSION,
        "scenario": scenario,
        "dataset_fingerprint": dataset_fingerprint,
    }


def compute_identity_fingerprint(identity_v2: dict[str, object]) -> str:
    canonical_json = json.dumps(
        identity_v2,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    domain_input = "stage7_identity_v2:" + canonical_json
    return hashlib.sha256(domain_input.encode("utf-8")).hexdigest()


 ValueError("trial_id_end must be >= trial_id_start")
    return {
        "scenario": scenario,
        "source_sha": source_sha,
        "trial_id_start": trial_id_start,
        "trial_id_end": trial_id_end,
        "fingerprint_sha256": fingerprint_sha256,
    }


def validate_trial_sequence(
    *,
    trial_ids: list[int],
    completed_trials: int,
    next_trial_id: int,
) -> None:
    ordered_ids = sorted(int(trial_id) for trial_id in trial_ids)
    expected_ids = list(range(1, completed_trials + 1))
    if ordered_ids != expected_ids:
        raise StateIntegrityError("trial sequence mismatch")
    if next_trial_id != completed_trials + 1:
        raise StateIntegrityError(
            "next_trial_id mismatch: "
            f"expected={completed_trials + 1}, actual={next_trial_id}"
        )


class StateStore:
    def __init__(
        self,
        *,
        repo: str,
        token: str,
        scenario: str,
        source_sha: str,
        run_id: str,
        run_attempt: str,
        local_path: Path,
        master_seed: int,
        expected_dataset_fingerprint: str | None = None,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
    ) -> None:
        self.repo = repo
        self.token = token
        self.scenario = scenario
        self.source_sha = source_sha
        self.run_id = str(run_id)
        self.run_attempt = str(run_attempt)
        self.local_path = local_path
        self.master_seed = int(master_seed)
        self.expected_dataset_fingerprint = expected_dataset_fingerprint
        self.lease_seconds = int(lease_seconds)
        if self.lease_seconds < 1:
            raise ValueError("lease_seconds must be >= 1")

    @property
    def state_branch(self) -> str:
        return f"stage7-state/{self.scenario}"

    @property
    def lease_owner(self) -> str:
        # Same run_id across GitHub re-runs is one logical lease owner.
        # run_attempt is retained in the record for auditability only.
        return self.run_id

    def _request(self, method, path, payload=None):
        for attempt in range(MAX_ATTEMPTS):
            request = urllib.request.Request(
                f"https://api.github.com/repos/{self.repo}/{path}",
                method=method,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
            if payload is not None:
                request.data = json.dumps(payload).encode("utf-8")
                request.add_header("Content-Type", "application/json")
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    raw = response.read()
                return json.loads(raw.decode("utf-8")) if raw else {}
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                if exc.code == 404:
                    raise StateRemoteNotFound(
                        f"GitHub API 404 for {method} {path}: {body}"
                    ) from exc
                if exc.code in {409, 422}:
                    raise StateConflict(
                        f"GitHub API conflict {exc.code} for {method} {path}: {body}"
                    ) from exc
                if (
                    exc.code in RETRYABLE_HTTP_STATUS
                    and attempt < MAX_ATTEMPTS - 1
                ):
                    retry_after = exc.headers.get("Retry-After")
                    if retry_after:
                        try:
                            delay = max(float(retry_after), RETRY_BASE_SECONDS)
                        except ValueError:
                            delay = RETRY_BASE_SECONDS * (2**attempt)
                    else:
                        delay = RETRY_BASE_SECONDS * (2**attempt)
                    time.sleep(delay)
                    continue
                raise RuntimeError(
                    f"GitHub API HTTP {exc.code} for {method} {path}: {body}"
                ) from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt < MAX_ATTEMPTS - 1:
                    time.sleep(RETRY_BASE_SECONDS * (2**attempt))
                    continue
                raise RuntimeError(
                    f"GitHub API transport failure for {method} {path}: {exc}"
                ) from exc

    def _state_contents_path(self) -> str:
        ref = urllib.parse.quote(self.state_branch, safe="")
        return f"contents/state.json?ref={ref}"

    def _branch_ref_path(self) -> str:
        branch = urllib.parse.quote(self.state_branch, safe="/")
        return f"git/ref/heads/{branch}"

    def _initial_state(self) -> dict[str, object]:
        initial_next_check_n = (
            1 if self.scenario.startswith("C100_") else 300
        )
        return {
            "stage": "7",
            "state_schema_version": STATE_SCHEMA_VERSION,
            "scenario": self.scenario,
            "source_sha": self.source_sha,
            "run_id": self.run_id,
            "run_attempt": int(self.run_attempt),
            "completed_trials": 0,
            "next_trial_id": 1,
            "next_check_n": initial_next_check_n,
            "final_fingerprint": None,
            "artifact_identity": None,
            "stage7_identity_v2": None,
            "identity_fingerprint": None,
            "included_in_final_stats": False,
            "stability_history": [],
            "final_status": None,
            "reason_if_not_stable": None,
            "stable_at_n": None,
            "lease": self._lease_record(),
        }

    def ensure_state_branch(self) -> bool:
        try:
            payload = self._request("GET", self._branch_ref_path())
            branch_sha = payload.get("object", {}).get("sha")
            if branch_sha is None:
                raise StateIntegrityError(
                    "state branch ref missing commit SHA"
                )
            return str(branch_sha) == self.source_sha
        except StateRemoteNotFound:
            pass
        try:
            self._request(
                "POST",
                "git/refs",
                {
                    "ref": f"refs/heads/{self.state_branch}",
                    "sha": self.source_sha,
                },
            )
        except StateConflict:
            payload = self._request("GET", self._branch_ref_path())
            branch_sha = payload.get("object", {}).get("sha")
            if branch_sha is None:
                raise StateIntegrityError(
                    "state branch ref missing commit SHA"
                )
            return str(branch_sha) == self.source_sha
        return True

    def _load_state_unvalidated(self):
        payload = self._request("GET", self._state_contents_path())
        raw = base64.b64decode(str(payload["content"])).decode("utf-8")
        state = json.loads(raw)
        if not isinstance(state, dict):
            raise StateIntegrityError("state.json root must be an object")
        return state, str(payload["sha"])

    def load_state(self):
        state, blob_sha = self._load_state_unvalidated()
        self._validate_identity(state)
        return state, blob_sha

    def _put_state(self, state, blob_sha):
        raw = json.dumps(
            state, ensure_ascii=False, indent=2, sort_keys=True
        ) + "\n"
        payload = {
            "message": (
                f"stage7: checkpoint {self.scenario} "
                f"n={state['completed_trials']}"
            ),
            "content": base64.b64encode(raw.encode("utf-8")).decode("ascii"),
            "branch": self.state_branch,
        }
        if blob_sha is not None:
            payload["sha"] = blob_sha
        response = self._request("PUT", "contents/state.json", payload)
        return str(response["content"]["sha"])

    def _lease_record(self):
        now = _utc_now()
        return {
            "owner": self.lease_owner,
            "run_id": self.run_id,
            "run_attempt": int(self.run_attempt),
            "acquired_at": _iso(now),
            "expires_at": _iso(
                now + timedelta(seconds=self.lease_seconds)
            ),
        }

    def _lease_is_active_for_other_owner(self, lease):
        if not isinstance(lease, dict):
            return False
        owner = lease.get("owner")
        expires_at = lease.get("expires_at")
        if not owner or not expires_at or owner == self.lease_owner:
            return False
        try:
            expiry = datetime.fromisoformat(
                str(expires_at).replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise StateIntegrityError(
                f"invalid lease expiry: {expires_at!r}"
            ) from exc
        return expiry > _utc_now()

    def _migrate_v1_to_v2(self, state):
        if self.expected_dataset_fingerprint is None:
            raise StateIntegrityError(
                "v1 checkpoint migration requires an independently verified "
                "dataset fingerprint"
            )
        if not state.get("run_id"):
            raise StateIntegrityError("v1 checkpoint migration requires run_id provenance")
        artifact_identity = state.get("artifact_identity")
        if not isinstance(artifact_identity, dict):
            raise StateIntegrityError("v1 checkpoint migration requires artifact_identity provenance")
        if artifact_identity.get("scenario") != self.scenario:
            raise StateIntegrityError("v1 artifact_identity scenario mismatch")
        if artifact_identity.get("source_sha") != self.source_sha:
            raise StateIntegrityError("v1 artifact_identity source SHA mismatch")
        dataset_fingerprint = artifact_identity.get("fingerprint_sha256")
        if not isinstance(dataset_fingerprint, str) or not dataset_fingerprint:
            raise StateIntegrityError("v1 checkpoint migration requires fingerprint_sha256 provenance")
        if dataset_fingerprint != self.expected_dataset_fingerprint:
            raise StateIntegrityError("v1 checkpoint dataset fingerprint differs from independently verified dataset")
        identity_v2 = build_stage7_identity_v2(
            source_sha=self.source_sha,
            master_seed=self.master_seed,
            scenario=self.scenario,
            dataset_fingerprint=dataset_fingerprint,
        )
        state["state_schema_version"] = STATE_SCHEMA_VERSION
        state["stage7_identity_v2"] = identity_v2
        state["identity_fingerprint"] = compute_identity_fingerprint(identity_v2)
        return state

    def _validate_identity(self, state):
        if state.get("stage") != "7":
            raise StateIntegrityError(f"State stage mismatch: {state.get('stage')} != 7")
        if state.get("scenario") != self.scenario:
            raise StateIntegrityError(f"State scenario mismatch: {state.get('scenario')} != {self.scenario}")
        if state.get("source_sha") != self.source_sha:
            raise StateIntegrityError("State source SHA mismatch: " f"{state.get('source_sha')} != {self.source_sha}")
        if state.get("state_schema_version") is None:
            state = self._migrate_v1_to_v2(state)
        elif state.get("state_schema_version") != STATE_SCHEMA_VERSION:
            raise StateIntegrityError("unsupported Stage 7 state schema version: " f"{state.get('state_schema_version')!r}")
        for key in ("completed_trials", "next_trial_id", "stability_history"):
            if key not in state:
                raise StateIntegrityError(f"state.json missing required Stage 7 field: {key}")
        completed_trials = int(state.get("completed_trials", 0))
        if completed_trials > 0:
            identity_v2 = state.get("stage7_identity_v2")
            if not isinstance(identity_v2, dict):
                raise StateIntegrityError("state.json missing stage7_identity_v2")
            artifact_identity = state.get("artifact_identity")
            dataset_fingerprint = artifact_identity.get("fingerprint_sha256") if isinstance(artifact_identity, dict) else ""
            expected_identity = build_stage7_identity_v2(
                source_sha=self.source_sha,
                master_seed=self.master_seed,
                scenario=self.scenario,
                dataset_fingerprint=str(dataset_fingerprint),
            )
            if identity_v2 != expected_identity:
                raise StateIntegrityError("Stage 7 identity v2 mismatch")
            expected_fingerprint = compute_identity_fingerprint(identity_v2)
            if state.get("identity_fingerprint") != expected_fingerprint:
                raise StateIntegrityError("Stage 7 identity fingerprint mismatch")
            if self.expected_dataset_fingerprint is not None and identity_v2["dataset_fingerprint"] != self.expected_dataset_fingerprint:
                raise StateIntegrityError("Stage 7 dataset fingerprint differs from independently verified dataset")
    def _write_local(self, state):
        self.local_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.local_path.with_name(
            f"{self.local_path.name}.tmp"
        )
        raw = json.dumps(
            state, ensure_ascii=False, indent=2, sort_keys=True
        ) + "\n"
        with temp_path.open("w", encoding="utf-8") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, self.local_path)

    def _verify_remote_equals(self, expected_state):
        remote_state, remote_sha = self.load_state()
        if remote_state != expected_state:
            raise StateIntegrityError(
                "remote state differs from locally committed state"
            )
        return remote_sha

    def acquire(self):
        branch_needs_initialization = self.ensure_state_branch()

        if branch_needs_initialization:
            state = self._initial_state()
            try:
                existing = self._request(
                    "GET",
                    self._state_contents_path(),
                )
            except StateRemoteNotFound:
                blob_sha = self._put_state(state, None)
            else:
                blob_sha = self._put_state(
                    state,
                    str(existing["sha"]),
                )
            remote_sha = self._verify_remote_equals(state)
            self._write_local(state)
            return state, remote_sha

        try:
            state, blob_sha = self.load_state()
        except StateRemoteNotFound:
            state = self._initial_state()
            try:
                blob_sha = self._put_state(state, None)
            except StateConflict:
                state, blob_sha = self.load_state()
            else:
                remote_sha = self._verify_remote_equals(state)
                self._write_local(state)
                return state, remote_sha

        if self._lease_is_active_for_other_owner(state.get("lease")):
            raise LeaseConflict(
                f"scenario {self.scenario} is leased by "
                f"{state['lease']['owner']}"
            )
        state["scenario"] = self.scenario
        state["source_sha"] = self.source_sha
        state["run_id"] = self.run_id
        state["run_attempt"] = int(self.run_attempt)
        state["lease"] = self._lease_record()
        self._put_state(state, blob_sha)
        remote_sha = self._verify_remote_equals(state)
        self._write_local(state)
        return state, remote_sha

    def save_state(self, state, blob_sha):
        self._validate_identity(state)
        lease = state.get("lease")
        if (
            isinstance(lease, dict)
            and lease.get("owner") not in (None, self.lease_owner)
        ):
            raise LeaseConflict(
                f"scenario {self.scenario} lease owner changed to "
                f"{lease.get('owner')}"
            )
        state["scenario"] = self.scenario
        state["source_sha"] = self.source_sha
        state["run_id"] = self.run_id
        state["run_attempt"] = int(self.run_attempt)
        state["lease"] = self._lease_record()
        self._put_state(state, blob_sha)
        remote_sha = self._verify_remote_equals(state)
        self._write_local(state)
        return remote_sha

    def release(self):
        try:
            state, blob_sha = self.load_state()
        except StateRemoteNotFound:
            return
        lease = state.get("lease")
        if not isinstance(lease, dict):
            return
        if lease.get("owner") != self.lease_owner:
            return
        state["lease"] = None
        try:
            self._put_state(state, blob_sha)
            self._verify_remote_equals(state)
            self._write_local(state)
        except (StateConflict, StateRemoteNotFound):
            return


__all__ = [
    "StateRemoteNotFound",
    "StateConflict",
    "LeaseConflict",
    "StateIntegrityError",
    "StateStore",
    "build_artifact_identity",
    "build_stage7_identity_v2",
    "compute_identity_fingerprint",
    "validate_trial_sequence",
]
