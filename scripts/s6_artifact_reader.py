"""Read-only, pinned artifact reader for S6 D1.

No simulator, trial runner, Stage 12/13 module, or legacy Excel code is imported.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import zipfile
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path, PurePosixPath
from typing import Any, Iterator

from scripts.s6_deliverables_model import SourceRef

PINNED = {
    "aggregate": {
        "artifact_id": 12852969854, "run_id": 40773412377,
        "sha256": "ec05a69ae8968585decf83cf0716d56c264f47f86187cfd3cf53b11f52ca2e54",
        "size": 9357996,
    },
    "full_logging": {
        "artifact_id": 12998778418, "run_id": 41098699740,
        "sha256": "403371cc8eb12880dda05529b4c83dd675bfa609e8680c09d35efa729c5b5aeb",
        "size": 310827203,
    },
    "c100": {
        "artifact_id": 12630457193, "run_id": 40263424595,
        "sha256": "c977d1cbb5204919eadc72358533f77cdbbc239902bcd6f921bf1a915a716e79",
        "size": 361733,
    },
}
S6_SOURCE = "da1a9ea9b5cd789c944de3f07b08395bb67c49e7"
S6_COHORT = "s6-v23-da1a9ea9"
S6_SEED = 20270101
C100_SOURCE = "965281d52441cd0d4b744e211c9f68ee4cdc3753"
C100_COHORT = "c100-v23-s4-20261026-965281d5"


class ArtifactValidationError(RuntimeError):
    pass


class MissingEvidenceError(RuntimeError):
    pass


def _json_load(raw: bytes) -> Any:
    return json.loads(raw.decode("utf-8"), parse_float=Decimal)


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_identity(manifest: dict[str, Any], kind: str) -> None:
    """Validate source/cohort/seed identity for one pinned cohort."""
    if kind == "aggregate":
        if manifest.get("source_sha") != S6_SOURCE or manifest.get("cohort_id") != S6_COHORT:
            raise ArtifactValidationError("S6_AGGREGATE_IDENTITY_MISMATCH")
        if manifest.get("master_seed") != S6_SEED:
            raise ArtifactValidationError("S6_MASTER_SEED_MISMATCH")
    elif kind == "c100":
        if manifest.get("source_sha") != C100_SOURCE or manifest.get("cohort_id") != C100_COHORT:
            raise ArtifactValidationError("C100_IDENTITY_MISMATCH")
        if manifest.get("status") not in {"REUSED_READ_ONLY", "CROSS_COHORT_DETERMINISTIC_REUSE"}:
            raise ArtifactValidationError("C100_REUSE_STATUS_MISMATCH")
    else:
        raise ValueError(f"UNKNOWN_COHORT_KIND:{kind}")


def _safe_member(info: zipfile.ZipInfo) -> None:
    name = info.filename
    p = PurePosixPath(name)
    mode = (info.external_attr >> 16) & 0xFFFF
    if not name or name.startswith("/") or "\\" in name or p.is_absolute():
        raise ArtifactValidationError(f"UNSAFE_ZIP_PATH:{name!r}")
    if any(part in ("", ".", "..") for part in p.parts):
        raise ArtifactValidationError(f"UNSAFE_ZIP_PATH:{name!r}")
    if re.match(r"^[A-Za-z]:", name):
        raise ArtifactValidationError(f"UNSAFE_ZIP_PATH:{name!r}")
    if stat.S_ISLNK(mode):
        raise ArtifactValidationError(f"ZIP_SYMLINK_FORBIDDEN:{name!r}")


@dataclass
class Archive:
    kind: str
    path: Path
    metadata: dict[str, Any]
    sha256: str
    size_bytes: int
    members: tuple[str, ...]
    _member_hashes: dict[str, str] = field(default_factory=dict, repr=False)

    def open_zip(self) -> zipfile.ZipFile:
        return zipfile.ZipFile(self.path, "r")

    def read_json(self, member: str) -> Any:
        with self.open_zip() as zf:
            try:
                return _json_load(zf.read(member))
            except KeyError as exc:
                raise MissingEvidenceError(f"MEMBER_MISSING:{member}") from exc

    def source_ref(self, member: str, member_sha: str | None = None,
                   row_or_key: str | None = None) -> SourceRef:
        if member not in self.members:
            raise MissingEvidenceError(f"MEMBER_MISSING:{member}")
        if member_sha is None:
            if member not in self._member_hashes:
                with self.open_zip() as zf:
                    self._member_hashes[member] = sha256_bytes(zf.read(member))
            member_sha = self._member_hashes[member]
        return SourceRef(
            artifact_id=self.metadata["artifact_id"], run_id=self.metadata["run_id"],
            archive_sha256=self.sha256, member_path=member,
            member_sha256=member_sha, row_or_key=row_or_key,
        )


class S6ArtifactReader:
    """Validate exact pinned ZIP inputs and expose read-only member streams."""

    def __init__(self, paths: dict[str, str | Path]):
        self.paths = {k: Path(v) for k, v in paths.items()}

    def open_all(self) -> dict[str, Archive]:
        if set(self.paths) != set(PINNED):
            raise ArtifactValidationError("EXACTLY_THREE_PINNED_INPUTS_REQUIRED")
        result: dict[str, Archive] = {}
        for kind, expected in PINNED.items():
            path = self.paths[kind]
            if not path.is_file():
                raise MissingEvidenceError(f"ARCHIVE_NOT_FOUND:{kind}:{path}")
            size = path.stat().st_size
            digest = sha256_file(path)
            if size != expected["size"]:
                raise ArtifactValidationError(f"ARCHIVE_SIZE_MISMATCH:{kind}:{size}")
            if digest != expected["sha256"]:
                raise ArtifactValidationError(f"ARCHIVE_SHA256_MISMATCH:{kind}:{digest}")
            with zipfile.ZipFile(path, "r") as zf:
                infos = zf.infolist()
                names = [i.filename for i in infos]
                if len(names) != len(set(names)):
                    raise ArtifactValidationError(f"DUPLICATE_ZIP_MEMBER:{kind}")
                normalized = [str(PurePosixPath(n)) for n in names]
                if len(normalized) != len(set(normalized)):
                    raise ArtifactValidationError(f"DUPLICATE_NORMALIZED_PATH:{kind}")
                for info in infos:
                    _safe_member(info)
                bad = zf.testzip()
                if bad is not None:
                    raise ArtifactValidationError(f"ZIP_CRC_FAILURE:{kind}:{bad}")
            result[kind] = Archive(kind, path, expected, digest, size, tuple(names))
        self._validate_archive_manifests(result)
        return result

    @staticmethod
    def _validate_archive_manifests(archives: dict[str, Archive]) -> None:
        aggregate = archives["aggregate"]
        manifest = aggregate.read_json("manifest.json")
        validate_identity(manifest, "aggregate")
        for member, meta in manifest.get("files", {}).items():
            with aggregate.open_zip() as zf:
                raw = zf.read(member)
            if len(raw) != meta.get("size_bytes") or sha256_bytes(raw) != meta.get("sha256"):
                raise ArtifactValidationError(f"AGGREGATE_MEMBER_MANIFEST_MISMATCH:{member}")

        c100 = archives["c100"]
        names = c100.members
        golden = next((n for n in names if n.endswith("C100_GOLDEN_965281d52441cd0d4b744e211c9f68ee4cdc3753.json")), None)
        c100_manifest = next((n for n in names if n.endswith("S4_C100_GOLDEN_MANIFEST_965281d52441cd0d4b744e211c9f68ee4cdc3753.json")), None)
        if not golden or not c100_manifest:
            raise MissingEvidenceError("C100_GOLDEN_OR_MANIFEST_MISSING")
        with c100.open_zip() as zf:
            golden_sha = sha256_bytes(zf.read(golden))
            c100_sha = sha256_bytes(zf.read(c100_manifest))
        if golden_sha != "39950d91c3b40b11bea0997b8504ac932a57bcc0ef8e0c51e12d031342a53327":
            raise ArtifactValidationError("C100_GOLDEN_SHA_MISMATCH")
        if c100_sha != "2097284d77ead6b00492bf75830d09aeef8dbde4aaa1c15dae6a877dc7e9ff04":
            raise ArtifactValidationError("C100_MANIFEST_SHA_MISMATCH")

        full = archives["full_logging"]
        root_name = next((n for n in full.members if n.endswith("representative_full_logging_manifest.json")), None)
        map_name = next((n for n in full.members if n.endswith("representative_selection_map.json")), None)
        if not root_name or not map_name:
            raise MissingEvidenceError("REPRESENTATIVE_ROOT_MANIFEST_OR_MAP_MISSING")
        root = full.read_json(root_name)
        role_map = full.read_json(map_name)
        if root.get("master_seed") != S6_SEED or role_map.get("s6_source", {}).get("source_sha") != S6_SOURCE:
            raise ArtifactValidationError("REPRESENTATIVE_S6_IDENTITY_MISMATCH")
        if root.get("governing_reference_sha256") != "225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b":
            raise ArtifactValidationError("REPRESENTATIVE_GOVERNING_REFERENCE_MISMATCH")
        if len(role_map.get("assignments", [])) != 125 or root.get("role_assignment_count") != 125:
            raise ArtifactValidationError("REPRESENTATIVE_ROLE_ASSIGNMENT_COUNT_MISMATCH")
        if root.get("unique_key_count") != 105 or root.get("duplicate_role_assignment_count") != 20:
            raise ArtifactValidationError("REPRESENTATIVE_UNIQUE_KEY_COUNTS_MISMATCH")

    def iter_jsonl_gzip(self, archive: Archive, member: str) -> Iterator[dict[str, Any]]:
        import gzip
        with archive.open_zip() as zf, zf.open(member, "r") as raw, gzip.GzipFile(fileobj=raw, mode="rb") as gz:
            for line in gz:
                if line.strip():
                    yield _json_load(line)

    def read_parquet(self, archive: Archive, member: str) -> Any:
        """Read Parquet only when pyarrow exists; never silently replace missing data."""
        try:
            import pyarrow.parquet as pq
        except ImportError as exc:
            raise MissingEvidenceError("PARQUET_READER_UNAVAILABLE: install pyarrow to inspect parquet schema/rows") from exc
        import tempfile
        with archive.open_zip() as zf:
            raw = zf.read(member)
        with tempfile.NamedTemporaryFile(suffix=".parquet") as tmp:
            tmp.write(raw); tmp.flush()
            table = pq.read_table(tmp.name)
        return table
