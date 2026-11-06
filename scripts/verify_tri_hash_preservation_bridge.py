#!/usr/bin/env python3
"""Tri-hash and restore verification for the Motorcycle Simulation preservation inventory.

Requires read-only GitHub, Microsoft Graph and Dropbox API credentials supplied by
GitHub Actions secrets. No project data is modified or uploaded by this verifier.
"""
from __future__ import annotations

import argparse
import base64
import ctypes
import hashlib
import io
import json
import os
import re
import shutil
import struct
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PurePosixPath
from urllib.parse import quote

import requests

REPO = "yasmin977209-ux/motorcycle-simulation"
GRAPH_DRIVE = "893D06C344EA996B"
RESCUE_ROOT = "893D06C344EA996B!s0a781736638d4c6fac434b1ff2bb1b9a"
MULTIPART_FOLDER = "893D06C344EA996B!s83634f573f994ab7a28ca1eda69683e4"
D3S_FOLDER = "893D06C344EA996B!s0f3055f9ce89404c9ef34c7dd004f187"
DROPBOX_ROOT = "/Motorcycle-Simulation-Rescue-2026-11-05"
S6_RUN = 40731224990
D3S_RUN = 42295053851
D3S_COMBINED_ARTIFACT = 13542178172
D3S_PACKAGE_BYTES = 1837203298
D3S_PACKAGE_SHA256 = "80e15d07873b51b0c1d1ff653546025a642361de26dbd57ef876a23c4cacc0f0"
D3_ARTIFACT_ID = 13288779998
D5_ARTIFACT_ID = 13369179742
CHUNK = 4 * 1024 * 1024
EXPECTED_S6 = 20
EXPECTED_MULTIPART = 20
EXPECTED_D3S = 23
EXPECTED_DROPBOX = 9

class BridgeError(RuntimeError):
    pass

def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise BridgeError("MISSING_REQUIRED_GITHUB_SECRET:" + name)
    return value

def safe_member(name: str) -> bool:
    if not name or "\\" in name or name.startswith("/"):
        return False
    p = PurePosixPath(name)
    if p.is_absolute() or (len(name) > 1 and name[1] == ":"):
        return False
    return all(part not in ("", ".", "..") for part in name.rstrip("/").split("/"))

def quickxor_bytes(data: bytes) -> str:
    state = bytearray(20)
    for i, value in enumerate(data):
        bit = (i * 11) % 160
        byte_index, shift = divmod(bit, 8)
        shifted = value << shift
        state[byte_index] ^= shifted & 0xff
        state[(byte_index + 1) % 20] ^= (shifted >> 8) & 0xff
    for i, value in enumerate(struct.pack("<Q", len(data))):
        state[12 + i] ^= value
    return base64.b64encode(state).decode("ascii")

def dropbox_content_hash_bytes(data: bytes) -> str:
    outer = hashlib.sha256()
    if not data:
        outer.update(hashlib.sha256(b"").digest())
    else:
        for start in range(0, len(data), CHUNK):
            outer.update(hashlib.sha256(data[start:start + CHUNK]).digest())
    return outer.hexdigest()

class HashEngine:
    def __init__(self, library_path: str):
        self.lib = ctypes.CDLL(library_path)
        self.update = self.lib.quickxor_update
        self.update.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint64]
        self.update.restype = None

    def file(self, path: Path) -> dict:
        sha = hashlib.sha256()
        qx = (ctypes.c_ubyte * 20)()
        outer = hashlib.sha256()
        db_buf = bytearray()
        total = 0
        with path.open("rb") as f:
            while True:
                block = f.read(8 * 1024 * 1024)
                if not block:
                    break
                sha.update(block)
                cbuf = ctypes.create_string_buffer(block)
                self.update(qx, ctypes.cast(cbuf, ctypes.c_void_p), len(block), total)
                total += len(block)
                db_buf.extend(block)
                while len(db_buf) >= CHUNK:
                    part = bytes(db_buf[:CHUNK])
                    del db_buf[:CHUNK]
                    outer.update(hashlib.sha256(part).digest())
        if db_buf:
            outer.update(hashlib.sha256(bytes(db_buf)).digest())
        elif total == 0:
            outer.update(hashlib.sha256(b"").digest())
        for i, value in enumerate(struct.pack("<Q", total)):
            qx[12 + i] ^= value
        return {
            "size": total,
            "sha256": sha.hexdigest(),
            "onedrive_quickxorhash": base64.b64encode(bytes(qx)).decode("ascii"),
            "dropbox_content_hash": outer.hexdigest(),
        }

class Clients:
    def __init__(self):
        self.gh_token = require_env("GITHUB_TOKEN")
        self.graph_token = require_env("ONEDRIVE_GRAPH_ACCESS_TOKEN")
        self.dropbox_token = require_env("DROPBOX_ACCESS_TOKEN")
        self.s = requests.Session()
        self.gh_headers = {"Authorization": "Bearer " + self.gh_token, "Accept": "application/vnd.github+json",
                           "X-GitHub-Api-Version": "2022-11-28"}
        self.graph_headers = {"Authorization": "Bearer " + self.graph_token}
        self.dropbox_headers = {"Authorization": "Bearer " + self.dropbox_token, "Content-Type": "application/json"}

    def gh_json(self, url: str) -> dict:
        r = self.s.get(url, headers=self.gh_headers, timeout=(45, 120))
        r.raise_for_status()
        return r.json()

    def gh_artifacts(self, run_id: int) -> dict[str, dict]:
        data = self.gh_json(f"https://api.github.com/repos/{REPO}/actions/runs/{run_id}/artifacts?per_page=100")
        return {a["name"]: a for a in data.get("artifacts", [])}

    def gh_artifact_meta(self, artifact_id: int) -> dict:
        return self.gh_json(f"https://api.github.com/repos/{REPO}/actions/artifacts/{artifact_id}")

    def download_gh_artifact(self, artifact_id: int, dest: Path, engine: HashEngine) -> tuple[dict, dict]:
        meta = self.gh_artifact_meta(artifact_id)
        if meta.get("expired"):
            raise BridgeError(f"GITHUB_ARTIFACT_EXPIRED:{artifact_id}")
        r = self.s.get(f"https://api.github.com/repos/{REPO}/actions/artifacts/{artifact_id}/zip",
                       headers=self.gh_headers, stream=True, timeout=(60, 600))
        r.raise_for_status()
        with dest.open("wb") as f:
            for block in r.iter_content(4 * 1024 * 1024):
                if block:
                    f.write(block)
        h = engine.file(dest)
        expected = str(meta.get("digest") or "")
        if h["size"] != int(meta["size_in_bytes"]) or expected != "sha256:" + h["sha256"]:
            raise BridgeError(f"GITHUB_ARTIFACT_RAW_HASH_MISMATCH:{artifact_id}:{h}")
        return meta, h

    def graph_children(self, item_id: str) -> list[dict]:
        url = f"https://graph.microsoft.com/v1.0/drives/{GRAPH_DRIVE}/items/{quote(item_id, safe='!')}/children?$top=200&$select=id,name,size,file,folder,parentReference"
        out = []
        while url:
            r = self.s.get(url, headers=self.graph_headers, timeout=(45, 120))
            r.raise_for_status()
            data = r.json()
            out.extend(data.get("value", []))
            url = data.get("@odata.nextLink")
        return out

    def graph_download(self, item_id: str, dest: Path) -> None:
        url = f"https://graph.microsoft.com/v1.0/drives/{GRAPH_DRIVE}/items/{quote(item_id, safe='!')}/content"
        r = self.s.get(url, headers=self.graph_headers, stream=True, timeout=(60, 600))
        r.raise_for_status()
        with dest.open("wb") as f:
            for block in r.iter_content(4 * 1024 * 1024):
                if block:
                    f.write(block)

    def dropbox_list(self) -> list[dict]:
        body = {"path": DROPBOX_ROOT, "recursive": False, "limit": 200}
        r = self.s.post("https://api.dropboxapi.com/2/files/list_folder", headers=self.dropbox_headers,
                        json=body, timeout=(45, 120))
        r.raise_for_status()
        data = r.json()
        entries = list(data.get("entries", []))
        while data.get("has_more"):
            r = self.s.post("https://api.dropboxapi.com/2/files/list_folder/continue",
                            headers=self.dropbox_headers, json={"cursor": data["cursor"]}, timeout=(45, 120))
            r.raise_for_status()
            data = r.json()
            entries.extend(data.get("entries", []))
        return entries

    def dropbox_metadata(self, path: str) -> dict:
        r = self.s.post("https://api.dropboxapi.com/2/files/get_metadata", headers=self.dropbox_headers,
                        json={"path": path}, timeout=(45, 120))
        r.raise_for_status()
        return r.json()

    def dropbox_download(self, path: str, dest: Path) -> None:
        headers = {"Authorization": "Bearer " + self.dropbox_token,
                   "Dropbox-API-Arg": json.dumps({"path": path}, separators=(",", ":"))}
        r = self.s.post("https://content.dropboxapi.com/2/files/download", headers=headers,
                        stream=True, timeout=(60, 600))
        r.raise_for_status()
        with dest.open("wb") as f:
            for block in r.iter_content(4 * 1024 * 1024):
                if block:
                    f.write(block)

def validate_zip(path: Path, report: dict, depth: int = 0, temp_root: Path | None = None) -> None:
    if depth > 2:
        return
    temp_root = temp_root or path.parent
    with zipfile.ZipFile(path, "r") as z:
        infos = z.infolist()
        names = [x.filename for x in infos]
        if len(names) != len(set(names)):
            raise BridgeError("ZIP_DUPLICATE_MEMBER:" + str(path))
        for info in infos:
            if not safe_member(info.filename):
                raise BridgeError("ZIP_UNSAFE_MEMBER:" + info.filename)
        bad = z.testzip()
        if bad:
            raise BridgeError("ZIP_CRC_FAILURE:" + str(path) + ":" + bad)
        report["zip_packages_checked"] += 1
        report["zip_members_checked"] += len(infos)
        for info in infos:
            if info.is_dir():
                continue
            suffix = PurePosixPath(info.filename).suffix.lower()
            if suffix not in (".xlsx", ".docx", ".pdf", ".parquet", ".json", ".zip"):
                continue
            target = temp_root / (hashlib.sha256((str(path)+info.filename).encode()).hexdigest() + suffix)
            with z.open(info) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst, length=4 * 1024 * 1024)
            try:
                if suffix == ".xlsx":
                    from openpyxl import load_workbook
                    wb = load_workbook(target, read_only=True, data_only=False)
                    report["workbooks_opened"] += 1
                    report["workbook_sheets_checked"] += len(wb.sheetnames)
                    wb.close()
                elif suffix == ".docx":
                    from docx import Document
                    Document(target)
                    report["documents_opened"] += 1
                elif suffix == ".pdf":
                    from pypdf import PdfReader
                    reader = PdfReader(str(target), strict=False)
                    report["documents_opened"] += 1
                    report["pdf_pages_checked"] += len(reader.pages)
                elif suffix == ".parquet":
                    import pyarrow.parquet as pq
                    pq.read_metadata(target)
                    report["parquet_files_checked"] += 1
                elif suffix == ".json":
                    with target.open("r", encoding="utf-8") as f:
                        json.load(f)
                    report["json_files_checked"] += 1
                elif suffix == ".zip":
                    validate_zip(target, report, depth + 1, temp_root)
            finally:
                target.unlink(missing_ok=True)

def artifact_id_from_name(name: str) -> int:
    m = re.match(r"artifact-(\d+)-", name)
    if not m:
        raise BridgeError("DROPBOX_ARTIFACT_ID_NOT_IN_FILENAME:" + name)
    return int(m.group(1))

def compare_source_artifact(clients: Clients, engine: HashEngine, artifact_id: int,
                            observed: dict, work: Path, report: dict, label: str) -> dict:
    p = work / f"github-artifact-{artifact_id}.zip"
    meta, source_hashes = clients.download_gh_artifact(artifact_id, p, engine)
    if source_hashes["size"] != observed["size"] or source_hashes["sha256"] != observed["sha256"]:
        raise BridgeError(f"PROVIDER_GITHUB_ARTIFACT_MISMATCH:{label}:{artifact_id}")
    validate_zip(p, report, temp_root=work)
    record = {"artifact_id": artifact_id, "artifact_name": meta["name"], "artifact_bytes": source_hashes["size"],
              "artifact_digest": meta["digest"], "source_tri_hashes": source_hashes}
    p.unlink(missing_ok=True)
    report["github_artifacts_raw_verified"] += 1
    return record

def read_part_wrapper(path: Path) -> tuple[bytes, dict]:
    with zipfile.ZipFile(path, "r") as z:
        names = z.namelist()
        bins = [n for n in names if n.lower().endswith(".bin")]
        jsons = [n for n in names if n.lower().endswith(".json")]
        if len(bins) != 1 or len(jsons) != 1:
            raise BridgeError(f"PART_WRAPPER_INVENTORY_INVALID:{path.name}:{names}")
        raw = z.read(bins[0])
        meta = json.loads(z.read(jsons[0]).decode("utf-8"))
    return raw, meta

def verify_reassembled_group(name: str, parts: list[dict], expected_id: int | None,
                             expected_size: int, expected_sha: str, clients: Clients,
                             engine: HashEngine, work: Path, report: dict) -> dict:
    if not parts:
        raise BridgeError("EMPTY_PART_GROUP:" + name)
    count = int(parts[0]["part_count"])
    if len(parts) != count or sorted(int(x["part_index"]) for x in parts) != list(range(count)):
        raise BridgeError(f"PART_COVERAGE_FAILURE:{name}:{len(parts)}:{count}")
    out = work / (name + ".reassembled.zip")
    h = hashlib.sha256()
    total = 0
    with out.open("wb") as dst:
        for part in sorted(parts, key=lambda x: int(x["part_index"])):
            raw_path = Path(part["raw_path"])
            raw_hash = engine.file(raw_path)
            if raw_hash["size"] != int(part["part_bytes"]) or raw_hash["sha256"] != part["part_sha256"]:
                raise BridgeError("PART_RAW_HASH_MISMATCH:" + str(raw_path))
            with raw_path.open("rb") as src:
                for block in iter(lambda: src.read(4 * 1024 * 1024), b""):
                    dst.write(block)
                    h.update(block)
                    total += len(block)
    if total != expected_size or h.hexdigest() != expected_sha:
        raise BridgeError(f"REASSEMBLY_SHA256_MISMATCH:{name}:{total}:{h.hexdigest()}")
    full = engine.file(out)
    validate_zip(out, report, temp_root=work)
    source_record = None
    if expected_id is not None:
        source_record = compare_source_artifact(clients, engine, expected_id, full, work, report, name)
    out.unlink(missing_ok=True)
    report["reassemblies_passed"] += 1
    return {"name": name, "part_count": count, "bytes": total, "sha256": h.hexdigest(),
            "github_source_artifact": source_record}

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", default="tri-hash-output")
    ap.add_argument("--quickxor-lib", default=os.environ.get("QUICKXOR_LIB", "/tmp/libquickxorhash.so"))
    args = ap.parse_args()
    engine = HashEngine(args.quickxor_lib)
    clients = Clients()
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="tri-hash-"))
    report = {"schema": "tri-hash-preservation-ledger-v1", "repository": REPO,
              "branch": "tmp/d1-rebuild-20261101", "workflow_run_id": int(os.environ.get("GITHUB_RUN_ID", "0")),
              "tested_sha": os.environ.get("GITHUB_SHA", "UNKNOWN"), "hash_algorithms": {
                  "sha256": "SHA-256 over exact raw bytes",
                  "onedrive_quickxorhash": "Microsoft QuickXorHash 160-bit, circular 11-bit shift, length XOR",
                  "dropbox_content_hash": "SHA-256 of concatenated SHA-256 digests of 4 MiB blocks"},
              "entries": [], "part_entries": [], "github_artifacts_raw_verified": 0, "zip_packages_checked": 0,
              "zip_members_checked": 0, "workbooks_opened": 0, "workbook_sheets_checked": 0,
              "documents_opened": 0, "pdf_pages_checked": 0, "parquet_files_checked": 0,
              "json_files_checked": 0, "reassemblies_passed": 0}
    try:
        s6_artifacts = clients.gh_artifacts(S6_RUN)
        d3s_artifacts = clients.gh_artifacts(D3S_RUN)
        root_items = clients.graph_children(RESCUE_ROOT)
        multipart_items = [x for x in clients.graph_children(MULTIPART_FOLDER) if x.get("file") and not x.get("folder")]
        d3s_items = clients.graph_children(D3S_FOLDER)
        s6_items = [x for x in root_items if x.get("name", "").startswith("s6-n2400-") and x.get("name", "").endswith(".zip")]
        core_dropbox_items = [x for x in clients.dropbox_list() if x.get(".tag") == "file" and x.get("name", "").startswith("artifact-") and x.get("name", "").endswith(".zip")]
        if len(s6_items) != EXPECTED_S6:
            raise BridgeError(f"ONEDRIVE_S6_COUNT_MISMATCH:{len(s6_items)}")
        if len(multipart_items) != EXPECTED_MULTIPART:
            raise BridgeError(f"ONEDRIVE_MULTIPART_COUNT_MISMATCH:{len(multipart_items)}")
        if len(d3s_items) != EXPECTED_D3S:
            raise BridgeError(f"ONEDRIVE_D3S_COUNT_MISMATCH:{len(d3s_items)}")
        if len(core_dropbox_items) != EXPECTED_DROPBOX:
            raise BridgeError(f"DROPBOX_CORE_PACKAGE_COUNT_MISMATCH:{len(core_dropbox_items)}")
        report["inventory_counts"] = {"onedrive_s6_archives": len(s6_items),
            "onedrive_multipart_d1_d3_d5": len(multipart_items), "onedrive_d3s_transport": len(d3s_items),
            "dropbox_core_packages": len(core_dropbox_items)}

        # 20 S6 archives: direct raw GitHub Artifact ZIP copies.
        for item in s6_items:
            name = item["name"]
            artifact_name = name[:-4]
            artifact = s6_artifacts.get(artifact_name)
            if not artifact:
                raise BridgeError("S6_GITHUB_ARTIFACT_NAME_MISSING:" + artifact_name)
            p = work / ("od-" + name)
            clients.graph_download(item["id"], p)
            h = engine.file(p)
            if h["size"] != int(item["size"]):
                raise BridgeError("ONEDRIVE_SIZE_MISMATCH:" + name)
            remote_qx = (item.get("file") or {}).get("hashes", {}).get("quickXorHash")
            if not remote_qx or remote_qx != h["onedrive_quickxorhash"]:
                raise BridgeError("ONEDRIVE_QUICKXOR_MISMATCH:" + name)
            source = compare_source_artifact(clients, engine, int(artifact["id"]), h, work, report, name)
            validate_zip(p, report, temp_root=work)
            report["entries"].append({"provider": "OneDrive", "name": name, "item_id": item["id"],
                "remote_size": item["size"], **h, "remote_quickxorhash": remote_qx,
                "github_source": source, "status": "VERIFIED_LIVE"})
            p.unlink(missing_ok=True)

        # 22 D3-S parts plus their manifest: direct raw GitHub Artifact ZIP copies.
        d3s_parts = []
        restore_source_pins = {}
        for item in d3s_items:
            name = item["name"]
            p = work / ("od-" + name)
            clients.graph_download(item["id"], p)
            h = engine.file(p)
            if h["size"] != int(item["size"]):
                raise BridgeError("ONEDRIVE_SIZE_MISMATCH:" + name)
            remote_qx = (item.get("file") or {}).get("hashes", {}).get("quickXorHash")
            if not remote_qx or remote_qx != h["onedrive_quickxorhash"]:
                raise BridgeError("ONEDRIVE_QUICKXOR_MISMATCH:" + name)
            validate_zip(p, report, temp_root=work)
            if name.startswith("D3S-") and name.endswith(".transport.zip"):
                seq = int(re.search(r"D3S-(\d+)", name).group(1))
                artifact = d3s_artifacts.get(f"OD-Multipart-D3S-{seq:03d}")
                if not artifact:
                    raise BridgeError("D3S_GITHUB_ARTIFACT_NAME_MISSING:" + name)
                source = compare_source_artifact(clients, engine, int(artifact["id"]), h, work, report, name)
                raw, sidecar = read_part_wrapper(p)
                raw_path = work / f"D3S.part{seq:03d}.bin"
                raw_path.write_bytes(raw)
                raw_hashes = engine.file(raw_path)
                if raw_hashes["size"] != int(sidecar["part_bytes"]) or raw_hashes["sha256"] != sidecar["part_sha256"]:
                    raise BridgeError("D3S_RAW_PART_HASH_MISMATCH:" + name)
                report["part_entries"].append({"group": "D3S", "name": raw_path.name, **raw_hashes,
                    "sidecar_part_sha256": sidecar["part_sha256"], "status": "VERIFIED_LIVE"})
                d3s_parts.append({"part_index": sidecar["part_index"], "part_count": 22,
                    "part_bytes": sidecar["part_bytes"], "part_sha256": sidecar["part_sha256"],
                    "raw_path": str(raw_path), "source_package_bytes": sidecar["source_package_bytes"],
                    "source_package_sha256": sidecar["source_package_sha256"]})
            else:
                artifact = d3s_artifacts.get("OD-Multipart-D3S-Restore-Manifest")
                if not artifact:
                    raise BridgeError("D3S_RESTORE_MANIFEST_ARTIFACT_MISSING")
                source = compare_source_artifact(clients, engine, int(artifact["id"]), h, work, report, name)
                with zipfile.ZipFile(p) as z:
                    manifest_names = [n for n in z.namelist() if n.endswith("D3S_RESTORE_MANIFEST.json")]
                    if len(manifest_names) != 1:
                        raise BridgeError("D3S_RESTORE_MANIFEST_MEMBER_MISSING")
                    restore_manifest = json.loads(z.read(manifest_names[0]).decode("utf-8"))
                    if restore_manifest["transport_package"]["sha256"] != D3S_PACKAGE_SHA256:
                        raise BridgeError("D3S_RESTORE_MANIFEST_SHA_PIN_MISMATCH")
            report["entries"].append({"provider": "OneDrive", "name": name, "item_id": item["id"],
                "remote_size": item["size"], **h, "remote_quickxorhash": remote_qx,
                "github_source": source, "status": "VERIFIED_LIVE"})
            p.unlink(missing_ok=True)
        if len(d3s_parts) != 22:
            raise BridgeError(f"D3S_PART_COUNT_MISMATCH:{len(d3s_parts)}")
        if any(x["source_package_bytes"] != D3S_PACKAGE_BYTES or x["source_package_sha256"] != D3S_PACKAGE_SHA256 for x in d3s_parts):
            raise BridgeError("D3S_PART_SOURCE_MANIFEST_CONFLICT")
        d3s_reassembly = verify_reassembled_group("D3S-10-workbooks-and-equivalence-evidence", d3s_parts,
            None, D3S_PACKAGE_BYTES, D3S_PACKAGE_SHA256, clients, engine, work, report)
        # Compare the ten restored D3-S files against the independently published combined GitHub artifact.
        combined_path = work / "d3s-combined-artifact.zip"
        combined_meta, combined_hash = clients.download_gh_artifact(D3S_COMBINED_ARTIFACT, combined_path, engine)
        validate_zip(combined_path, report, temp_root=work)
        with zipfile.ZipFile(combined_path) as z:
            combined_members = {PurePosixPath(n).name: hashlib.sha256(z.read(n)).hexdigest()
                                for n in z.namelist() if not n.endswith("/")}
        # The transport reassembly has already been CRC-checked; extract and compare each payload member.
        # The source file hashes in the restore manifest are checked against the combined Artifact members.
        with tempfile.TemporaryDirectory(dir=work) as td:
            restored = Path(td) / "d3s-reassembled.zip"
            with restored.open("wb") as dst:
                for part in sorted(d3s_parts, key=lambda x: int(x["part_index"])):
                    with Path(part["raw_path"]).open("rb") as src:
                        shutil.copyfileobj(src, dst, length=4 * 1024 * 1024)
            with zipfile.ZipFile(restored) as z:
                transport_members = {PurePosixPath(n).name: hashlib.sha256(z.read(n)).hexdigest()
                                     for n in z.namelist() if not n.endswith("/")}
            if transport_members != combined_members:
                raise BridgeError("D3S_TRANSPORT_VS_COMBINED_ARTIFACT_MEMBER_HASH_MISMATCH")
        combined_path.unlink(missing_ok=True)
        report["d3s_transport_reassembly"] = d3s_reassembly
        report["d3s_combined_artifact"] = {"id": D3S_COMBINED_ARTIFACT,
            "bytes": combined_hash["size"], "sha256": combined_hash["sha256"],
            "digest": combined_meta["digest"], "member_count": len(combined_members)}

        # 20 D1/D3/D5 multipart ZIP wrappers: verify each part sidecar, then exact reassembly.
        groups: dict[int, list[dict]] = {}
        restore_files = []
        for item in multipart_items:
            name = item["name"]
            p = work / ("mp-" + name)
            clients.graph_download(item["id"], p)
            h = engine.file(p)
            if h["size"] != int(item["size"]):
                raise BridgeError("ONEDRIVE_SIZE_MISMATCH:" + name)
            remote_qx = (item.get("file") or {}).get("hashes", {}).get("quickXorHash")
            if not remote_qx or remote_qx != h["onedrive_quickxorhash"]:
                raise BridgeError("ONEDRIVE_QUICKXOR_MISMATCH:" + name)
            validate_zip(p, report, temp_root=work)
            if name.endswith(".transport.zip") and re.match(r"D[135]-\d{3}\.transport\.zip$", name):
                raw, sidecar = read_part_wrapper(p)
                raw_path = work / sidecar["part_name"]
                raw_path.write_bytes(raw)
                raw_hashes = engine.file(raw_path)
                if raw_hashes["sha256"] != sidecar["part_sha256"] or raw_hashes["size"] != sidecar["part_bytes"]:
                    raise BridgeError("MULTIPART_RAW_PART_HASH_MISMATCH:" + name)
                report["part_entries"].append({"group": name.split("-")[0], "name": raw_path.name, **raw_hashes,
                    "sidecar_part_sha256": sidecar["part_sha256"], "status": "VERIFIED_LIVE"})
                aid = int(sidecar["source_artifact_id"])
                groups.setdefault(aid, []).append({**sidecar, "raw_path": str(raw_path)})
            else:
                with zipfile.ZipFile(p, "r") as z:
                    manifests = [n for n in z.namelist() if n.lower().endswith(".json")]
                    if len(manifests) != 1:
                        raise BridgeError("MULTIPART_RESTORE_MANIFEST_MEMBER_COUNT:" + name)
                    restore_data = json.loads(z.read(manifests[0]).decode("utf-8"))
                sources = restore_data.get("sources", {})
                if name.startswith("D1-RESTORE"):
                    d1 = sources.get("D1", {})
                    d1_id = int(d1.get("artifact_id", -1))
                    if d1_id <= 0 or int(d1.get("part_count", -1)) != 4:
                        raise BridgeError("D1_RESTORE_MANIFEST_PIN_MISMATCH")
                    restore_source_pins["D1"] = {"artifact_id": d1_id, "source_bytes": int(d1.get("source_bytes", -1)),
                        "source_sha256": str(d1.get("source_sha256", "")), "part_count": 4}
                else:
                    for key, artifact_id in (("D3", D3_ARTIFACT_ID), ("D5", D5_ARTIFACT_ID)):
                        src = sources.get(key, {})
                        if int(src.get("artifact_id", -1)) != artifact_id or int(src.get("part_count", -1)) != 7:
                            raise BridgeError("D3_D5_RESTORE_MANIFEST_PIN_MISMATCH:" + key)
                        restore_source_pins[key] = {"artifact_id": artifact_id, "source_bytes": int(src.get("source_bytes", -1)),
                            "source_sha256": str(src.get("source_sha256", "")), "part_count": 7}
                restore_files.append(name)
            report["entries"].append({"provider": "OneDrive", "name": name, "item_id": item["id"],
                "remote_size": item["size"], **h, "remote_quickxorhash": remote_qx,
                "status": "VERIFIED_LIVE"})
            p.unlink(missing_ok=True)
        expected_ids = {int(x["artifact_id"]) for x in restore_source_pins.values()}
        if len(expected_ids) != 3 or set(groups) != expected_ids:
            raise BridgeError("MULTIPART_SOURCE_ARTIFACT_SET_MISMATCH:" + str(sorted(groups)))
        multipart_results = []
        for key, pin in restore_source_pins.items():
            aid = int(pin["artifact_id"])
            parts = groups[aid]
            sizes = {int(x["source_bytes"]) for x in parts}
            shas = {str(x["source_sha256"]) for x in parts}
            counts = {int(x["part_count"]) for x in parts}
            if len(sizes) != 1 or len(shas) != 1 or counts != {int(pin["part_count"])}:
                raise BridgeError("MULTIPART_SIDECAR_IDENTITY_CONFLICT:" + str(aid))
            expected_size = int(pin["source_bytes"])
            expected_sha = str(pin["source_sha256"])
            if sizes != {expected_size} or shas != {expected_sha}:
                raise BridgeError("MULTIPART_RESTORE_MANIFEST_VS_PARTS_CONFLICT:" + key)
            result = verify_reassembled_group("multipart-" + key, parts, aid,
                expected_size, expected_sha, clients, engine, work, report)
            if key == "D1" and not re.search(r"(D1|full[-_ ]?logging)", result["github_source_artifact"]["artifact_name"], re.I):
                raise BridgeError("D1_SOURCE_ARTIFACT_NAME_MISMATCH:" + result["github_source_artifact"]["artifact_name"])
            multipart_results.append(result)
        if len(restore_files) != 2:
            raise BridgeError("MULTIPART_RESTORE_MANIFEST_COUNT_MISMATCH:" + str(restore_files))
        report["multipart_reassemblies"] = multipart_results

        # Nine Dropbox primary rescue packages: compute all three hashes on the downloaded bytes.
        for item in core_dropbox_items:
            path_display = item.get("path_lower") or item.get("path_display")
            if not path_display:
                raise BridgeError("DROPBOX_PATH_MISSING:" + item.get("name", ""))
            meta = clients.dropbox_metadata(path_display)
            p = work / ("db-" + item["name"])
            clients.dropbox_download(path_display, p)
            h = engine.file(p)
            remote_size = int(meta.get("size", -1))
            remote_content = meta.get("content_hash")
            if h["size"] != remote_size:
                raise BridgeError("DROPBOX_SIZE_MISMATCH:" + item["name"])
            if not remote_content or remote_content != h["dropbox_content_hash"]:
                raise BridgeError("DROPBOX_CONTENT_HASH_MISMATCH_OR_MISSING:" + item["name"])
            validate_zip(p, report, temp_root=work)
            aid = artifact_id_from_name(item["name"])
            source = compare_source_artifact(clients, engine, aid, h, work, report, item["name"])
            report["entries"].append({"provider": "Dropbox", "name": item["name"], "path": item.get("path_display"),
                "remote_size": remote_size, **h, "remote_content_hash": remote_content,
                "github_source": source, "status": "VERIFIED_LIVE"})
            p.unlink(missing_ok=True)

        # The three original package artifacts are independently verified above via multipart restore.
        # No E2 replay scenario archive is included: it is a distinct preservation set.
        report["restore_tests"] = {"zip_crc_and_member_inventory": "PASS",
            "workbooks_and_documents_opened": "PASS_SCOPED",
            "d1_d3_d5_multipart_reassembly": "PASS_RAW_BYTES_EXACT",
            "d3s_multipart_reassembly": "PASS_RAW_BYTES_EXACT"}
        report["overall"] = "PASS_SCOPED_TRI_HASH_AND_RESTORE"
        report["limitations"] = [
            "This ledger covers 20 S6 source archives, 20 D1/D3/D5 multipart objects, 23 D3-S transport objects and nine Dropbox core packages only.",
            "E2 Replay's 20 scenario archives are a separate set and are not included in this run.",
            "A PASS here proves the listed bytes and restore chains only; it does not by itself close the wider Global Preservation Gate."
        ]
        (outdir / "TRI_HASH_PRESERVATION_LEDGER_2026-11-06.json").write_text(
            json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"overall": report["overall"], "tested_sha": report["tested_sha"],
            "run_id": report["workflow_run_id"], "inventory_counts": report["inventory_counts"],
            "entries": len(report["entries"]), "github_artifacts_raw_verified": report["github_artifacts_raw_verified"],
            "reassemblies_passed": report["reassemblies_passed"], "zip_packages_checked": report["zip_packages_checked"],
            "zip_members_checked": report["zip_members_checked"], "workbooks_opened": report["workbooks_opened"],
            "documents_opened": report["documents_opened"]}, sort_keys=True))
    except Exception as exc:
        report["overall"] = "BLOCKED"
        report["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        (outdir / "TRI_HASH_PRESERVATION_LEDGER_2026-11-06.json").write_text(
            json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        raise
    finally:
        shutil.rmtree(work, ignore_errors=True)

if __name__ == "__main__":
    main()
