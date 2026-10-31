"""Strict read-only resolver for original and derived trial audit statuses."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ManifestResolution:
    scenario_id: str
    trial_id: int
    original_status: str
    sidecar_status: str
    root_status: str
    manifest_sha256_match: bool
    audit_sha256_match: bool
    manifest_size_match: bool | None
    audit_size_match: bool | None
    identity_match: bool
    fingerprint_match: bool
    sidecar_pass: bool
    root_pass: bool
    normalized_audit_status: str
    reason: str


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def resolve_trial_manifest(
    trial_manifest_raw: bytes,
    post_write_audit_raw: bytes,
    root_entry: dict[str, Any],
    *,
    expected_manifest_size: int | None,
    expected_audit_size: int | None,
) -> ManifestResolution:
    """Resolve status without editing source bytes.

    PASS is deliberately withheld unless SHA, byte size, identity, fingerprints,
    sidecar PASS and root PASS all independently agree.
    """
    tm = json.loads(trial_manifest_raw.decode("utf-8"))
    audit = json.loads(post_write_audit_raw.decode("utf-8"))
    msha, asha = _sha(trial_manifest_raw), _sha(post_write_audit_raw)
    msha_ok = msha == root_entry.get("trial_manifest_sha256")
    asha_ok = asha == root_entry.get("post_write_audit_sha256")
    msize_ok = None if expected_manifest_size is None else len(trial_manifest_raw) == expected_manifest_size
    asize_ok = None if expected_audit_size is None else len(post_write_audit_raw) == expected_audit_size
    identity_ok = all((
        tm.get("scenario_id") == root_entry.get("scenario_id") == audit.get("scenario_id"),
        tm.get("trial_id") == root_entry.get("trial_id") == audit.get("trial_id"),
        tm.get("source_sha") == audit.get("source_sha"),
        tm.get("cohort_id") == audit.get("cohort_id"),
    ))
    expected_fp = tm.get("expected_trial_fingerprint")
    actual_fp = tm.get("actual_trial_fingerprint")
    audit_fp = audit.get("trial_fingerprint")
    root_fp = root_entry.get("trial_fingerprint")
    fingerprint_ok = bool(expected_fp and expected_fp == actual_fp == audit_fp == root_fp)
    sidecar_pass = audit.get("status") == "PASS_SCOPED_REPRESENTATIVE_FULL_LOGGING" and audit.get("trial_fingerprint_match") is True
    root_pass = root_entry.get("status") == "PASS_SCOPED_REPRESENTATIVE_FULL_LOGGING"
    all_pass = (
        msha_ok and asha_ok and msize_ok is True and asize_ok is True and
        identity_ok and fingerprint_ok and sidecar_pass and root_pass
    )
    missing = []
    if msize_ok is None: missing.append("EXPECTED_TRIAL_MANIFEST_SIZE_MISSING")
    elif not msize_ok: missing.append("TRIAL_MANIFEST_SIZE_MISMATCH")
    if asize_ok is None: missing.append("EXPECTED_POST_WRITE_AUDIT_SIZE_MISSING")
    elif not asize_ok: missing.append("POST_WRITE_AUDIT_SIZE_MISMATCH")
    if not msha_ok: missing.append("TRIAL_MANIFEST_SHA_MISMATCH")
    if not asha_ok: missing.append("POST_WRITE_AUDIT_SHA_MISMATCH")
    if not identity_ok: missing.append("SOURCE_COHORT_TRIAL_IDENTITY_MISMATCH")
    if not fingerprint_ok: missing.append("EXPECTED_ACTUAL_ROOT_FINGERPRINT_MISMATCH")
    if not sidecar_pass: missing.append("SIDECAR_AUDIT_NOT_PASS")
    if not root_pass: missing.append("ROOT_MANIFEST_NOT_PASS")
    normalized = "PASS_SCOPED_REPRESENTATIVE_FULL_LOGGING" if all_pass else "NOT_VERIFIED"
    return ManifestResolution(
        scenario_id=str(tm.get("scenario_id")), trial_id=int(tm.get("trial_id")),
        original_status=str(tm.get("status")), sidecar_status=str(audit.get("status")),
        root_status=str(root_entry.get("status")), manifest_sha256_match=msha_ok,
        audit_sha256_match=asha_ok, manifest_size_match=msize_ok, audit_size_match=asize_ok,
        identity_match=identity_ok, fingerprint_match=fingerprint_ok, sidecar_pass=sidecar_pass,
        root_pass=root_pass, normalized_audit_status=normalized,
        reason=";".join(missing) if missing else "ALL_REQUIRED_EVIDENCE_MATCHED",
    )


def resolve_full_logging_archive(archive, root_manifest_name: str) -> list[ManifestResolution]:
    """Resolve all root entries; absent expected sizes remain NOT_VERIFIED."""
    import zipfile
    root = archive.read_json(root_manifest_name)
    results = []
    with zipfile.ZipFile(archive.path, "r") as zf:
        for entry in root.get("results", []):
            folder = entry["folder"]
            tm_name = f"stagec-output/full_logging/{folder}/trial_manifest.json"
            audit_name = f"stagec-output/full_logging/{folder}/post_write_audit.json"
            tm_raw, audit_raw = zf.read(tm_name), zf.read(audit_name)
            # Root manifest records SHA values but no independent byte-size expectations.
            results.append(resolve_trial_manifest(
                tm_raw, audit_raw, entry,
                expected_manifest_size=entry.get("trial_manifest_size_bytes"),
                expected_audit_size=entry.get("post_write_audit_size_bytes"),
            ))
    return results
