"""Read-only, pinned ZIP artifact reader. Never extracts untrusted paths to disk."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json, stat, zipfile, gzip, io
from decimal import Decimal
from pathlib import PurePosixPath
from typing import Any, Iterator

class ArtifactValidationError(ValueError): pass
class MissingEvidenceError(RuntimeError): pass

@dataclass(frozen=True)
class ArtifactPin:
    artifact_id: int
    run_id: int
    size_bytes: int
    sha256: str
    filename: str

PINS = {
  "aggregate": ArtifactPin(12852969854,40773412377,9357996,"ec05a69ae8968585decf83cf0716d56c264f47f86187cfd3cf53b11f52ca2e54","s6-n2400.zip"),
  "full_logging": ArtifactPin(12998778418,41098699740,310827203,"403371cc8eb12880dda05529b4c83dd675bfa609e8680c09d35efa729c5b5aeb","full-logging.zip"),
  "c100": ArtifactPin(12630457193,40263424595,361733,"c977d1cbb5204919eadc72358533f77cdbbc239902bcd6f921bf1a915a716e79","c100-reuse.zip"),
}
S6_SOURCE = "da1a9ea9b5cd789c944de3f07b08395bb67c49e7"
S6_COHORT = "s6-v23-da1a9ea9"
C100_SOURCE = "965281d52441cd0d4b744e211c9f68ee4cdc3753"
C100_COHORT = "c100-v23-s4-20261026-965281d5"
MASTER_SEED = 20270101

class Archive:
    def __init__(self, path: str, pin: ArtifactPin):
        self.path, self.pin = path, pin
        self._zip = None
        self.digest = None
    def open(self) -> "Archive":
        raw = open(self.path,"rb").read()
        if len(raw) != self.pin.size_bytes: raise ArtifactValidationError("ARTIFACT_SIZE_MISMATCH")
        self.digest = hashlib.sha256(raw).hexdigest()
        if self.digest != self.pin.sha256: raise ArtifactValidationError("ARTIFACT_SHA256_MISMATCH")
        z = zipfile.ZipFile(io.BytesIO(raw))
        names = z.namelist()
        if len(names) != len(set(names)): raise ArtifactValidationError("DUPLICATE_ZIP_MEMBER")
        normalized = set()
        for name in names:
            p=PurePosixPath(name)
            parts=name.rstrip("/").split("/")
            if (not name or p.is_absolute() or name.startswith("/") or "\\" in name
                    or (len(name) >= 2 and name[1] == ":" and name[0].isalpha())
                    or any(part in ("", ".", "..") for part in parts)):
                raise ArtifactValidationError("UNSAFE_ZIP_PATH")
            norm=p.as_posix()
            if norm in normalized: raise ArtifactValidationError("DUPLICATE_NORMALIZED_ZIP_PATH")
            normalized.add(norm)
            mode=(z.getinfo(name).external_attr >> 16) & 0o170000
            if mode == stat.S_IFLNK: raise ArtifactValidationError("ZIP_SYMLINK")
        bad=z.testzip()
        if bad: raise ArtifactValidationError("ZIP_CRC_FAILURE:"+bad)
        self._zip=z
        return self
    def names(self) -> list[str]:
        self._require(); return self._zip.namelist()
    def member_size(self, member: str) -> int:
        """Return the uncompressed member size recorded in the verified ZIP central directory."""
        self._require()
        try: return int(self._zip.getinfo(member).file_size)
        except KeyError as exc: raise MissingEvidenceError("MISSING_MEMBER:"+member) from exc
    def read_bytes(self, member: str) -> bytes:
        self._require()
        if member not in self._zip.namelist(): raise MissingEvidenceError("MISSING_MEMBER:"+member)
        return self._zip.read(member)
    def read_json(self, member: str) -> Any:
        return json.loads(self.read_bytes(member).decode("utf-8"), parse_float=Decimal)
    def read_parquet(self, member: str):
        try: import pyarrow.parquet as pq
        except Exception as exc: raise MissingEvidenceError("PARQUET_READER_UNAVAILABLE") from exc
        data=self.read_bytes(member)
        return pq.read_table(io.BytesIO(data))
    def iter_jsonl_gzip(self, member: str) -> Iterator[dict[str, Any]]:
        raw=self.read_bytes(member)
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as f:
            for line in f:
                if line.strip(): yield json.loads(line, parse_float=Decimal)
    def _require(self):
        if self._zip is None: raise ArtifactValidationError("ARCHIVE_NOT_OPEN")
    def close(self):
        if self._zip: self._zip.close(); self._zip=None

class S6ArtifactReader:
    def __init__(self, paths: dict[str,str]):
        self.paths=paths
        self.archives={}
    def open_all(self):
        if set(self.paths) != set(PINS): raise ArtifactValidationError("PIN_SET_MISMATCH")
        for key,pin in PINS.items():
            self.archives[key]=Archive(self.paths[key],pin).open()
        return self
    def close(self):
        for a in self.archives.values(): a.close()
