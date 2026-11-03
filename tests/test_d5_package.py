from __future__ import annotations

import hashlib
import json
import tempfile
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.d5_package import (
    MEMBERS, REGISTRY_PATH, PACKAGE_NAME, safe_member, verify_zip_safety,
    sha256_file, verify,
)

def test_safe_member_rejects_traversal_absolute_and_windows_paths():
    assert safe_member("manifest.json")
    assert safe_member("folder/file.docx")
    assert not safe_member("../manifest.json")
    assert not safe_member("/manifest.json")
    assert not safe_member("C:/manifest.json")
    assert not safe_member("folder\\file.docx")

def test_zip_requires_exact_unique_members_and_crc(tmp_path):
    good = tmp_path / "good.zip"
    with zipfile.ZipFile(good, "w") as z:
        z.writestr("manifest.json", "{}")
        z.writestr("report.docx", b"docx")
    assert set(verify_zip_safety(good)) == {"manifest.json", "report.docx"}

    duplicate = tmp_path / "duplicate.zip"
    with zipfile.ZipFile(duplicate, "w") as z:
        z.writestr("manifest.json", "{}")
        z.writestr("manifest.json", "{}")
    with pytest.raises(ValueError, match="ZIP_DUPLICATE_MEMBER"):
        verify_zip_safety(duplicate)

def test_package_validator_detects_missing_and_extra_members(tmp_path):
    p = tmp_path / "package.zip"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("manifest.json", "{}")
        z.writestr("unexpected.txt", "x")
    expected = set(MEMBERS) | {"manifest.json"}
    with pytest.raises(ValueError, match="ZIP_MEMBER_SET_MISMATCH"):
        verify_zip_safety(p, expected)

def test_sha256_file_is_streamed_and_exact(tmp_path):
    p = tmp_path / "sample.bin"
    raw = b"motorcycle-simulation-d5" * 1000
    p.write_bytes(raw)
    assert sha256_file(p) == hashlib.sha256(raw).hexdigest()

def test_sha256sums_validator_rejects_unexpected_inventory(tmp_path):
    root = tmp_path
    out = root / "deliverables"
    out.mkdir()
    (root / REGISTRY_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / REGISTRY_PATH).write_bytes(b"registry")
    for name in MEMBERS:
        (out / name).write_bytes(name.encode())
    (out / "manifest.json").write_text(json.dumps({
        "package_member_count": 8,
        "package_status": "T2_INTERIM / NOT_FINAL_BLOCKED"
    }), encoding="utf-8")
    (out / PACKAGE_NAME).write_bytes(b"zip-placeholder")
    (out / "SHA256SUMS.txt").write_text("0"*64+"  unexpected.txt\n", encoding="utf-8")
    args = SimpleNamespace(package_name=PACKAGE_NAME, root=str(root))
    with pytest.raises(ValueError, match="D5_SHA256SUMS_COVERAGE_MISMATCH"):
        verify(args)
