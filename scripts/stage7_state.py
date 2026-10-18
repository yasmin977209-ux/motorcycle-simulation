from __future__ import annotations

import base64
import hashlib
import json
import os
import re
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
DURABLE_BLOCK_SCHEMA_VERSION = "stage7-durable-block-v1"
STAGE7_RNG_POLICY_ID = "sha256(master_seed|scenario_id|trial_id|bike_id|date|event_type)"
_BLOCK_NAME_RE = re.compile(r"^block_(\d+)_(\d+)$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _git_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


def build_durable_block_identity(
    *,
    metadata: dict[str, object],
    parquet_bytes: bytes,
    metadata_bytes: bytes,
    scenario: str,
    source_sha: str,
    master_seed: int,
    sampling_policy_id: str,
    allow_legacy_metadata: bool = False,
) -> dict[str, object]:
    """Build a manifest that cryptographically binds block bytes to identity.

    Legacy metadata may omit master_seed and policy identifiers, but in that case
    callers must prove the complete restored prefix against the stored checkpoint
    before migration. The legacy omission is recorded in the manifest.
    """
    required = (
        "scenario", "source_sha", "trial_id_start", "trial_id_end",
        "trial_count", "fingerprint_sha256",
    )
    missing = [key for key in required if key not in metadata]
    if missing:
        raise StateIntegrityError(
            "block metadata missing required identity fields: " + ", ".join(missing)
        )
    if metadata.get("scenario") != scenario:
        raise StateIntegrityError("block scenario mismatch")
    if metadata.get("source_sha") != source_sha:
        raise StateIntegrityError("block source SHA mismatch")
    try:
        trial_start = int(metadata["trial_id_start"])
        trial_end = int(metadata["trial_id_end"])
        trial_count = int(metadata["trial_count"])
    except (TypeError, ValueError) as exc:
        raise StateIntegrityError("block trial range/count is invalid") from exc
    if trial_start < 1 or trial_end < trial_start:
        raise StateIntegrityError("block trial range is invalid")
    if trial_count != trial_end - trial_start + 1:
        raise StateIntegrityError("block trial count does not match its ID range")
    fingerprint = metadata.get("fingerprint_sha256")
    if not isinstance(fingerprint, str) or not _SHA256_RE.fullmatch(fingerprint):
        raise StateIntegrityError("block fingerprint is not a SHA-256 digest")
    if "master_seed" in metadata and int(metadata["master_seed"]) != master_seed:
        raise StateIntegrityError("block master_seed mismatch")
    if (
        "sampling_policy_id" in metadata
        and metadata["sampling_policy_id"] != sampling_policy_id
    ):
        raise StateIntegrityError("block sampling policy mismatch")
    if (
        "rng_policy_id" in metadata
        and metadata["rng_policy_id"] != STAGE7_RNG_POLICY_ID
    ):
        raise StateIntegrityError("block RNG policy mismatch")
    if not allow_legacy_metadata:
        for key in ("master_seed", "sampling_policy_id", "rng_policy_id", "schema_version"):
            if key not in metadata:
                raise StateIntegrityError(
                    f"new block metadata missing {key}; legacy migration not allowed"
                )
    parquet_sha256 = hashlib.sha256(parquet_bytes).hexdigest()
    if metadata.get("parquet_sha256") not in (None, parquet_sha256):
        raise StateIntegrityError("Parquet block bytes do not match metadata SHA-256")
    per_trial = metadata.get("per_trial_sha256")
    if per_trial is not None:
        if not isinstance(per_trial, list) or len(per_trial) != trial_count:
            raise StateIntegrityError("per-trial digest count does not match block trial count")
        if any(not isinstance(item, str) or not _SHA256_RE.fullmatch(item) for item in per_trial):
            raise StateIntegrityError("invalid per-trial SHA-256 digest")
    return {
        "schema_version": DURABLE_BLOCK_SCHEMA_VERSION,
        "scenario": scenario,
        "source_sha": source_sha,
        "master_seed": master_seed,
        "rng_policy_id": STAGE7_RNG_POLICY_ID,
        "sampling_policy_id": sampling_policy_id,
        "trial_id_policy": "contiguous-prefix-from-1-v1",
        "trial_id_start": trial_start,
        "trial_id_end": trial_end,
        "trial_count": trial_count,
        "block_fingerprint_sha256": fingerprint,
        "parquet_sha256": parquet_sha256,
        "metadata_sha256": hashlib.sha256(metadata_bytes).hexdigest(),
        "per_trial_sha256": per_trial,
        "origin_run_id": metadata.get("run_id"),
        "legacy_metadata_migrated": any(
            key not in metadata for key in (
                "master_seed", "sampling_policy_id", "rng_policy_id", "schema_version"
            )
        ),
        "legacy_migration_basis": (
            "existing_checkpoint_fingerprint_and_artifact_identity_verified"
            if allow_legacy_metadata and any(
                key not in metadata for key in (
                    "master_seed", "sampling_policy_id", "rng_policy_id", "schema_version"
                )
            )
            else None
        ),
    }


def validate_durable_block_identity(
    *,
    identity: dict[str, object],
    metadata: dict[str, object],
    parquet_bytes: bytes,
    metadata_bytes: bytes,
    scenario: str,
    source_sha: str,
    master_seed: int,
    sampling_policy_id: str,
) -> None:
    """Fail closed unless block metadata, bytes, and current run identity agree."""
    expected = build_durable_block_identity(
        metadata=metadata,
        parquet_bytes=parquet_bytes,
        metadata_bytes=metadata_bytes,
        scenario=scenario,
        source_sha=source_sha,
        master_seed=master_seed,
        sampling_policy_id=sampling_policy_id,
        allow_legacy_metadata=bool(identity.get("legacy_metadata_migrated")),
    )
    if identity != expected:
        raise StateIntegrityError("durable block identity manifest mismatch")


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

    def _initial_state(self) -> dict[str, object]:
        initial_next_check_n = (
            1 if self.scenario.startswith("C100_") else 300
        )
        return {
            "stage": "7",
            "scenario": self.scenario,
            "source_sha": self.source_sha,
            "run_id": self.run_id,
            "run_attempt": int(self.run_attempt),
            "completed_trials": 0,
            "next_trial_id": 1,
            "next_check_n": initial_next_check_n,
            "final_fingerprint": None,
            "artifact_identity": None,
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

    def _validate_identity(self, state):
        if state.get("stage") != "7":
            raise StateIntegrityError(
                f"State stage mismatch: "
                f"{state.get('stage')} != 7"
            )
        if state.get("scenario") != self.scenario:
            raise StateIntegrityError(
                f"State scenario mismatch: "
                f"{state.get('scenario')} != {self.scenario}"
            )
        if state.get("source_sha") != self.source_sha:
            raise StateIntegrityError(
                "State source SHA mismatch: "
                f"{state.get('source_sha')} != {self.source_sha}"
            )
        for key in (
            "completed_trials",
            "next_trial_id",
            "stability_history",
        ):
            if key not in state:
                raise StateIntegrityError(
                    f"state.json missing required Stage 7 field: {key}"
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

    def _branch_refs_path(self) -> str:
        branch = urllib.parse.quote(self.state_branch, safe="/")
        return f"git/refs/heads/{branch}"

    def _contents_file_path(self, relative_path: str) -> str:
        path = urllib.parse.quote(relative_path, safe="/")
        ref = urllib.parse.quote(self.state_branch, safe="")
        return f"contents/{path}?ref={ref}"

    def _read_remote_blob(self, relative_path: str, expected_blob_sha: str | None = None) -> bytes:
        file_payload = self._request("GET", self._contents_file_path(relative_path))
        blob_sha = str(file_payload.get("sha") or "")
        if not blob_sha or (expected_blob_sha and blob_sha != expected_blob_sha):
            raise StateIntegrityError(f"remote blob SHA mismatch for {relative_path}")
        blob = self._request("GET", f"git/blobs/{blob_sha}")
        if blob.get("encoding") != "base64" or not isinstance(blob.get("content"), str):
            raise StateIntegrityError(f"remote blob content unavailable for {relative_path}")
        try:
            raw = base64.b64decode(blob["content"], validate=False)
        except (ValueError, TypeError) as exc:
            raise StateIntegrityError(f"remote blob base64 invalid for {relative_path}") from exc
        if _git_blob_sha(raw) != blob_sha:
            raise StateIntegrityError(f"remote Git blob digest mismatch for {relative_path}")
        return raw

    def _commit_files_atomically(self, files: dict[str, bytes], message: str) -> dict[str, str]:
        """Commit multiple files on the scenario state branch in one Git ref update."""
        if not files:
            raise ValueError("at least one file is required for an atomic commit")
        ref_payload = self._request("GET", self._branch_ref_path())
        parent_sha = str(ref_payload.get("object", {}).get("sha") or "")
        if not parent_sha:
            raise StateIntegrityError("state branch head SHA missing before block commit")
        parent_commit = self._request("GET", f"git/commits/{parent_sha}")
        base_tree_sha = str(parent_commit.get("tree", {}).get("sha") or "")
        if not base_tree_sha:
            raise StateIntegrityError("state branch tree SHA missing before block commit")

        blob_shas: dict[str, str] = {}
        tree_entries = []
        for path, raw in sorted(files.items()):
            blob = self._request(
                "POST",
                "git/blobs",
                {
                    "content": base64.b64encode(raw).decode("ascii"),
                    "encoding": "base64",
                },
            )
            blob_sha = str(blob.get("sha") or "")
            if not blob_sha or blob_sha != _git_blob_sha(raw):
                raise StateIntegrityError(f"GitHub created an unexpected blob SHA for {path}")
            blob_shas[path] = blob_sha
            tree_entries.append({
                "path": path,
                "mode": "100644",
                "type": "blob",
                "sha": blob_sha,
            })

        tree = self._request(
            "POST",
            "git/trees",
            {"base_tree": base_tree_sha, "tree": tree_entries},
        )
        tree_sha = str(tree.get("sha") or "")
        if not tree_sha:
            raise StateIntegrityError("GitHub did not return a tree SHA for block commit")
        commit = self._request(
            "POST",
            "git/commits",
            {"message": message, "tree": tree_sha, "parents": [parent_sha]},
        )
        commit_sha = str(commit.get("sha") or "")
        if not commit_sha:
            raise StateIntegrityError("GitHub did not return a commit SHA for block commit")
        self._request(
            "PATCH",
            self._branch_refs_path(),
            {"sha": commit_sha, "force": False},
        )
        read_ref = self._request("GET", self._branch_ref_path())
        actual_head = str(read_ref.get("object", {}).get("sha") or "")
        if actual_head != commit_sha:
            raise StateIntegrityError(
                f"state branch moved during block commit: {actual_head} != {commit_sha}"
            )
        for path, expected_sha in blob_shas.items():
            content_payload = self._request("GET", self._contents_file_path(path))
            if str(content_payload.get("sha") or "") != expected_sha:
                raise StateIntegrityError(f"atomic block commit read-back failed for {path}")
        return blob_shas

    def _block_listing(self) -> list[dict[str, object]]:
        path = "contents/stage7-blocks?ref=" + urllib.parse.quote(self.state_branch, safe="")
        try:
            payload = self._request("GET", path)
        except StateRemoteNotFound:
            return []
        if not isinstance(payload, list):
            raise StateIntegrityError("stage7-blocks remote path is not a directory")
        return [item for item in payload if isinstance(item, dict)]

    def restore_trial_blocks(
        self,
        *,
        output_dir: Path,
        master_seed: int,
        sampling_policy_id: str,
        expected_completed_trials: int,
    ) -> int:
        """Restore atomically persisted trial-block triplets and verify every identity."""
        listing = self._block_listing()
        if not listing:
            return 0
        by_name = {str(item.get("name")): item for item in listing if item.get("type") == "file"}
        parquet_names = {name for name in by_name if name.startswith("block_") and name.endswith(".parquet")}
        metadata_names = {name for name in by_name if name.startswith("block_") and name.endswith("_metadata.json")}
        identity_names = {name for name in by_name if name.startswith("block_") and name.endswith("_identity.json")}
        parquet_keys = {name[len("block_"):-len(".parquet")] for name in parquet_names}
        metadata_keys = {name[len("block_"):-len("_metadata.json")] for name in metadata_names}
        identity_keys = {name[len("block_"):-len("_identity.json")] for name in identity_names}
        if parquet_keys != metadata_keys or parquet_keys != identity_keys:
            raise StateIntegrityError(
                "persisted Stage 7 block files are incomplete: Parquet/metadata/identity sets differ"
            )

        destination = output_dir / self.scenario / "blocks"
        destination.mkdir(parents=True, exist_ok=True)
        ranges: list[tuple[int, int]] = []
        restored = 0
        for key in sorted(parquet_keys, key=lambda value: tuple(int(x) for x in value.split("_"))):
            match = _BLOCK_NAME_RE.fullmatch("block_" + key)
            if match is None:
                raise StateIntegrityError(f"invalid durable block filename key: {key}")
            start, end = int(match.group(1)), int(match.group(2))
            parquet_name = f"block_{key}.parquet"
            metadata_name = f"block_{key}_metadata.json"
            identity_name = f"block_{key}_identity.json"
            parquet_bytes = self._read_remote_blob(
                f"stage7-blocks/{parquet_name}", str(by_name[parquet_name].get("sha") or "")
            )
            metadata_bytes = self._read_remote_blob(
                f"stage7-blocks/{metadata_name}", str(by_name[metadata_name].get("sha") or "")
            )
            identity_bytes = self._read_remote_blob(
                f"stage7-blocks/{identity_name}", str(by_name[identity_name].get("sha") or "")
            )
            try:
                metadata = json.loads(metadata_bytes.decode("utf-8"))
                identity = json.loads(identity_bytes.decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise StateIntegrityError(f"durable block metadata JSON invalid for block_{key}") from exc
            if not isinstance(metadata, dict) or not isinstance(identity, dict):
                raise StateIntegrityError(f"durable block metadata root invalid for block_{key}")
            validate_durable_block_identity(
                identity=identity,
                metadata=metadata,
                parquet_bytes=parquet_bytes,
                metadata_bytes=metadata_bytes,
                scenario=self.scenario,
                source_sha=self.source_sha,
                master_seed=master_seed,
                sampling_policy_id=sampling_policy_id,
            )
            if int(identity["trial_id_start"]) != start or int(identity["trial_id_end"]) != end:
                raise StateIntegrityError(f"durable filename/range mismatch for block_{key}")
            local_files = (
                (destination / parquet_name, parquet_bytes),
                (destination / metadata_name, metadata_bytes),
            )
            for local_path, raw in local_files:
                if local_path.exists() and local_path.read_bytes() != raw:
                    raise StateIntegrityError(
                        f"local and durable Stage 7 block disagree: {local_path}"
                    )
                if not local_path.exists():
                    local_path.write_bytes(raw)
            ranges.append((start, end))
            restored += 1

        expected_start = 1
        for start, end in sorted(ranges):
            if start != expected_start or end < start:
                raise StateIntegrityError("durable Stage 7 blocks contain a gap or overlap")
            expected_start = end + 1
        actual_completed = expected_start - 1
        if actual_completed != expected_completed_trials:
            raise StateIntegrityError(
                "durable block/state checkpoint mismatch: "
                f"blocks={actual_completed}, state={expected_completed_trials}"
            )
        return restored

    def persist_trial_blocks_and_state(
        self,
        *,
        block_pairs: list[tuple[Path, Path]],
        state: dict[str, object],
        blob_sha: str | None,
        master_seed: int,
        sampling_policy_id: str,
        allow_legacy_metadata: bool = False,
    ) -> str:
        """Atomically persist verified block files, identity manifests, and state.json."""
        self._validate_identity(state)
        lease = state.get("lease")
        if isinstance(lease, dict) and lease.get("owner") not in (None, self.lease_owner):
            raise LeaseConflict(f"scenario {self.scenario} lease owner changed during block commit")

        files: dict[str, bytes] = {}
        ranges: list[tuple[int, int]] = []
        for parquet_path, metadata_path in sorted(
            block_pairs, key=lambda pair: pair[0].name
        ):
            parquet_bytes = parquet_path.read_bytes()
            metadata_bytes = metadata_path.read_bytes()
            try:
                metadata = json.loads(metadata_bytes.decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise StateIntegrityError(f"local block metadata is invalid: {metadata_path}") from exc
            if not isinstance(metadata, dict):
                raise StateIntegrityError(f"local block metadata root is invalid: {metadata_path}")
            identity = build_durable_block_identity(
                metadata=metadata,
                parquet_bytes=parquet_bytes,
                metadata_bytes=metadata_bytes,
                scenario=self.scenario,
                source_sha=self.source_sha,
                master_seed=master_seed,
                sampling_policy_id=sampling_policy_id,
                allow_legacy_metadata=allow_legacy_metadata,
            )
            key = f"{int(identity['trial_id_start'])}_{int(identity['trial_id_end'])}"
            if parquet_path.name != f"block_{key}.parquet" or metadata_path.name != f"block_{key}_metadata.json":
                raise StateIntegrityError("local block filename does not match its metadata range")
            ranges.append((int(identity["trial_id_start"]), int(identity["trial_id_end"])))
            prefix = f"stage7-blocks/block_{key}"
            files[f"{prefix}.parquet"] = parquet_bytes
            files[f"{prefix}_metadata.json"] = metadata_bytes
            files[f"{prefix}_identity.json"] = (
                json.dumps(identity, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            ).encode("utf-8")

        if ranges:
            # For both a new checkpoint and a legacy recovery, files must form the
            # exact prefix represented by the state being committed.
            expected_start = 1
            for start, end in sorted(ranges):
                if start != expected_start or end < start:
                    raise StateIntegrityError("local block files contain a gap or overlap")
                expected_start = end + 1
            if expected_start - 1 != int(state.get("completed_trials", -1)):
                raise StateIntegrityError(
                    "local block prefix does not match state.completed_trials"
                )
            prefix_fingerprint = state.get("final_fingerprint")
            if not isinstance(prefix_fingerprint, str) or not _SHA256_RE.fullmatch(prefix_fingerprint):
                raise StateIntegrityError("state final_fingerprint is missing before durable commit")

        state["scenario"] = self.scenario
        state["source_sha"] = self.source_sha
        state["run_id"] = self.run_id
        state["run_attempt"] = int(self.run_attempt)
        state["lease"] = self._lease_record()
        state_raw = (json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        files["state.json"] = state_raw

        # Refuse overwriting any previously persisted block with different bytes.
        existing_listing = self._block_listing()
        existing = {str(item.get("name")): item for item in existing_listing if item.get("type") == "file"}
        for path, raw in list(files.items()):
            if not path.startswith("stage7-blocks/"):
                continue
            name = path.rsplit("/", 1)[-1]
            if name in existing:
                expected_blob_sha = _git_blob_sha(raw)
                actual_blob_sha = str(existing[name].get("sha") or "")
                if actual_blob_sha != expected_blob_sha:
                    raise StateIntegrityError(f"refusing to overwrite durable block {name}")
                # Existing immutable block bytes are already committed; do not upload
                # them again when a newer block and state checkpoint are committed.
                files.pop(path)

        blob_shas = self._commit_files_atomically(
            files,
            message=(
                f"stage7: durable block checkpoint {self.scenario} "
                f"n={state.get('completed_trials')}"
            ),
        )
        self._write_local(state)
        return self._verify_remote_equals(state)

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
    "STAGE7_RNG_POLICY_ID",
    "build_artifact_identity",
    "build_durable_block_identity",
    "validate_durable_block_identity",
    "validate_trial_sequence",
]
