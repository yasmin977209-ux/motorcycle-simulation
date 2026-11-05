"""Fail-closed, read-only resolver for representative Full Logging manifests."""
from __future__ import annotations
import hashlib
from typing import Any


def _member_evidence(archive, member: str, expected_sha256: str | None) -> dict[str, Any]:
    """Bind ZIP central-directory size to decompressed bytes and an independent root-manifest digest."""
    central_size = archive.member_size(member)
    raw = archive.read_bytes(member)
    actual_size = len(raw)
    actual_sha256 = hashlib.sha256(raw).hexdigest()
    size_match = actual_size == central_size
    sha_match = isinstance(expected_sha256, str) and actual_sha256 == expected_sha256
    return {
        "member": member,
        "central_directory_size_bytes": central_size,
        "actual_size_bytes": actual_size,
        "size_match": size_match,
        "expected_sha256_from_root_manifest": expected_sha256,
        "actual_sha256": actual_sha256,
        "sha256_match": sha_match,
        "bytes": raw,
    }


def resolve_trial_manifest(archive, root_record: dict[str,Any], prefix: str, expected_key: dict[str,Any] | None = None) -> dict[str,Any]:
    folder=root_record["folder"]
    base=f"{prefix.rstrip('/')}/{folder}/"
    trial_member=base+"trial_manifest.json"
    audit_member=base+"post_write_audit.json"
    result_member=base+"trial_result.json"
    trial_evidence=_member_evidence(archive,trial_member,root_record.get("trial_manifest_sha256"))
    audit_evidence=_member_evidence(archive,audit_member,root_record.get("post_write_audit_sha256"))
    result=archive.read_json(result_member)
    import json
    trial=json.loads(trial_evidence["bytes"].decode("utf-8"))
    audit=json.loads(audit_evidence["bytes"].decode("utf-8"))
    identity_fields=("source_sha","cohort_id","scenario_id","trial_id")
    expected=expected_key or root_record
    identity_ok=all(trial.get(k)==expected.get(k) for k in identity_fields)
    fingerprint=trial.get("actual_trial_fingerprint")
    fingerprint_ok=(fingerprint is not None and
                    fingerprint==trial.get("expected_trial_fingerprint")==
                    root_record.get("trial_fingerprint")==
                    audit.get("trial_fingerprint")==result.get("trial_fingerprint"))
    audit_ok=(audit.get("status")=="PASS_SCOPED_REPRESENTATIVE_FULL_LOGGING"
              and audit.get("trial_fingerprint_match") is True
              and audit.get("rollforward_mismatch_count")==0
              and audit.get("balance_mismatch_count")==0)
    size_ok=trial_evidence["size_match"] and audit_evidence["size_match"]
    hash_ok=trial_evidence["sha256_match"] and audit_evidence["sha256_match"]
    normalized=("PASS_SCOPED_REPRESENTATIVE_FULL_LOGGING"
                if identity_ok and fingerprint_ok and audit_ok and size_ok and hash_ok
                else "NOT_VERIFIED")
    reasons=[]
    if not identity_ok: reasons.append("IDENTITY_MISMATCH")
    if not fingerprint_ok: reasons.append("FINGERPRINT_MISMATCH")
    if not audit_ok: reasons.append("POST_WRITE_AUDIT_NOT_PASS")
    if not size_ok: reasons.append("ZIP_CENTRAL_DIRECTORY_SIZE_MISMATCH")
    if not hash_ok: reasons.append("ROOT_MANIFEST_SHA256_MISMATCH")
    return {
      "folder":folder,"original_status":trial.get("status"),
      "root_status":root_record.get("status"),"normalized_audit_status":normalized,
      "identity_match":identity_ok,"fingerprint_match":fingerprint_ok,
      "post_write_audit_pass":audit_ok,
      "trial_manifest_size_bytes":trial_evidence["actual_size_bytes"],
      "trial_manifest_zip_central_directory_size_bytes":trial_evidence["central_directory_size_bytes"],
      "trial_manifest_sha256":trial_evidence["actual_sha256"],
      "trial_manifest_sha256_match":trial_evidence["sha256_match"],
      "post_write_audit_size_bytes":audit_evidence["actual_size_bytes"],
      "post_write_audit_zip_central_directory_size_bytes":audit_evidence["central_directory_size_bytes"],
      "post_write_audit_sha256":audit_evidence["actual_sha256"],
      "post_write_audit_sha256_match":audit_evidence["sha256_match"],
      "reasons":reasons,
      "trial_manifest":trial,"post_write_audit":audit,"trial_result":result
    }
