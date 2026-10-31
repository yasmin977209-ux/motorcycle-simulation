"""Fail-closed, read-only resolver for representative Full Logging manifests."""
from __future__ import annotations
from typing import Any

def resolve_trial_manifest(archive, root_record: dict[str,Any], prefix: str, expected_key: dict[str,Any] | None = None) -> dict[str,Any]:
    folder=root_record["folder"]
    base=f"{prefix.rstrip('/')}/{folder}/"
    trial=archive.read_json(base+"trial_manifest.json")
    audit=archive.read_json(base+"post_write_audit.json")
    result=archive.read_json(base+"trial_result.json")
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
    normalized="NOT_VERIFIED"
    reasons=[]
    if not identity_ok: reasons.append("IDENTITY_MISMATCH")
    if not fingerprint_ok: reasons.append("FINGERPRINT_MISMATCH")
    if not audit_ok: reasons.append("POST_WRITE_AUDIT_NOT_PASS")
    return {"folder":folder,"original_status":trial.get("status"),
      "root_status":root_record.get("status"),"normalized_audit_status":normalized,
      "identity_match":identity_ok,"fingerprint_match":fingerprint_ok,
      "post_write_audit_pass":audit_ok,
      "reasons":reasons or ["INDEPENDENT_EXPECTED_BYTE_SIZES_MISSING"],
      "trial_manifest":trial,"post_write_audit":audit,"trial_result":result}
