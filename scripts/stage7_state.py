from __future__ import annotations

import base64
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


class StateRemoteNotFound(RuntimeError):
    """Remote state does not exist; distinct from transient failure."""


class StateConflict(RuntimeError):
    """Remote state changed concurrently or already exists."""


class LeaseConflict(RuntimeError):
    """Another workflow currently owns the scenario state lease."""


class StateIntegrityError(RuntimeError):
    """Remote and local state did not reconcile exactly."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


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
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
    ) -> None:
        self.repo = repo
        self.token = token
        self.scenario = scenario
        self.source_sha = source_sha
        self.run_id = str(run_id)
        self.run_attempt = str(run_attempt)
        self.local_path = local_path
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

    def ensure_state_branch(self) -> None:
        try:
            self._request("GET", self._branch_ref_path())
            return
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
            self._request("GET", self._branch_ref_path())

    def load_state(self):
        payload = self._request("GET", self._state_contents_path())
        raw = base64.b64decode(str(payload["content"])).decode("utf-8")
        state = json.loads(raw)
        if not isinstance(state, dict):
            raise StateIntegrityError("state.json root must be an object")
        self._validate_identity(state)
        return state, str(payload["sha"])

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

    def _validate_identity(self, state):
        if state.get("scenario") not in (None, self.scenario):
            raise StateIntegrityError(
                f"State scenario mismatch: "
                f"{state.get('scenario')} != {self.scenario}"
            )
        if state.get("source_sha") not in (None, self.source_sha):
            raise StateIntegrityError(
                "State source SHA mismatch: "
                f"{state.get('source_sha')} != {self.source_sha}"
            )

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
        self.ensure_state_branch()
        try:
            state, blob_sha = self.load_state()
        except StateRemoteNotFound:
            initial_next_check_n = (
                1 if self.scenario.startswith("C100_") else 300
            )
            state = {
                "scenario": self.scenario,
                "source_sha": self.source_sha,
                "run_id": self.run_id,
                "run_attempt": int(self.run_attempt),
                "completed_trials": 0,
                "next_trial_id": 1,
                "next_check_n": initial_next_check_n,
                "final_fingerprint": None,
                "artifact_identity": None,
                "stability_history": [],
                "final_status": None,
                "reason_if_not_stable": None,
                "stable_at_n": None,
                "lease": self._lease_record(),
            }
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
    "validate_trial_sequence",
]
