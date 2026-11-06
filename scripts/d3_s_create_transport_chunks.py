#!/usr/bin/env python3
"""Create verified 80 MiB transport parts for the combined D3-S evidence package."""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, zipfile

CHUNK = 80 * 1024 * 1024

def digest(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source-dir", default="combined-d3-s")
    p.add_argument("--output-dir", default="transport-parts")
    a = p.parse_args()
    source = pathlib.Path(a.source_dir)
    out = pathlib.Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    files = sorted(x for x in source.iterdir() if x.is_file())
    if len([x for x in files if x.suffix.lower() == ".xlsx"]) != 10:
        raise SystemExit("D3S_TRANSPORT_EXPECTED_TEN_WORKBOOKS")
    archive = out / "D3-S-10-workbooks-and-equivalence-evidence.transport.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as z:
        for item in files:
            z.write(item, arcname=item.name)
    with zipfile.ZipFile(archive) as z:
        if z.testzip():
            raise SystemExit("D3S_TRANSPORT_PACKAGE_CRC_FAILURE")
        if len(z.namelist()) != len(files) or len(z.namelist()) != len(set(z.namelist())):
            raise SystemExit("D3S_TRANSPORT_MEMBER_INVENTORY_FAILURE")
    full_size = archive.stat().st_size
    full_sha = digest(archive)
    parts = []
    with archive.open("rb") as src:
        index = 0
        while True:
            block = src.read(CHUNK)
            if not block:
                break
            name = f"D3S.part{index:03d}.bin"
            target = out / name
            target.write_bytes(block)
            record = {
                "part_index": index, "part_name": name, "part_bytes": len(block),
                "offset_bytes": index * CHUNK, "part_sha256": digest(target),
                "source_package_bytes": full_size, "source_package_sha256": full_sha,
                "tested_sha": os.environ["GITHUB_SHA"],
                "workflow_run_id": int(os.environ["GITHUB_RUN_ID"])
            }
            (out / f"D3S.part{index:03d}.json").write_text(
                json.dumps(record, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            parts.append(record)
            index += 1
    if len(parts) != 17:
        raise SystemExit(f"D3S_TRANSPORT_EXPECTED_17_PARTS_GOT_{len(parts)}")
    rebuilt = out / "D3S.reassembled.check.zip"
    h = hashlib.sha256()
    with rebuilt.open("wb") as dst:
        for item in parts:
            part = out / item["part_name"]
            if part.stat().st_size != item["part_bytes"] or digest(part) != item["part_sha256"]:
                raise SystemExit("D3S_TRANSPORT_PART_HASH_OR_SIZE_MISMATCH:" + item["part_name"])
            with part.open("rb") as src:
                for block in iter(lambda: src.read(4 * 1024 * 1024), b""):
                    dst.write(block)
                    h.update(block)
    if rebuilt.stat().st_size != full_size or h.hexdigest() != full_sha:
        raise SystemExit("D3S_TRANSPORT_REASSEMBLY_RAW_SHA256_MISMATCH")
    rebuilt.unlink()
    manifest = {
        "schema_version": "d3s-onedrive-transport-v1",
        "classification": "PASS_SCOPED_TRANSPORT",
        "tested_sha": os.environ["GITHUB_SHA"],
        "workflow_run_id": int(os.environ["GITHUB_RUN_ID"]),
        "source_files": [{"name": x.name, "bytes": x.stat().st_size, "sha256": digest(x)} for x in files],
        "transport_package": {"name": archive.name, "bytes": full_size, "sha256": full_sha, "zip_crc": "PASS"},
        "chunk_size_bytes": CHUNK, "part_count": len(parts), "parts": parts,
        "reassembly_test": "PASS_RAW_BYTES_EXACT",
        "limitations": [
            "The transport ZIP is a newly assembled ZIP_STORED container of the ten D3-S workbook/evidence files; it is not byte-identical to the GitHub Actions Artifact wrapper ZIP.",
            "Permanent external retention requires uploading all parts and manifest, then reading back every part and repeating the reassembly hash check."
        ]
    }
    (out / "D3S_RESTORE_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"classification": manifest["classification"], "package_bytes": full_size,
                      "package_sha256": full_sha, "part_count": len(parts),
                      "tested_sha": os.environ["GITHUB_SHA"], "run_id": os.environ["GITHUB_RUN_ID"]}, sort_keys=True))

if __name__ == "__main__":
    main()
