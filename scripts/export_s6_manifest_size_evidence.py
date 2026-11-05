"""Export exact read-only evidence for the 105 representative Full Logging keys."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from scripts.s6_deliverables_builder import build_shared_model
from scripts.s6_artifact_reader import PINS

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--aggregate",required=True)
    p.add_argument("--full-logging",required=True)
    p.add_argument("--c100",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    model=build_shared_model({"aggregate":a.aggregate,"full_logging":a.full_logging,"c100":a.c100})
    rows=model.manifest_reconciliation
    if len(rows)!=105:
        raise SystemExit(f"D1_KEY_COUNT_MISMATCH:{len(rows)}")
    if any(r.get("normalized_audit_status")!="PASS_SCOPED_REPRESENTATIVE_FULL_LOGGING" for r in rows):
        raise SystemExit("D1_REPRESENTATIVE_STATUS_NOT_ALL_PASS")
    required=("trial_manifest_size_bytes","post_write_audit_size_bytes",
              "trial_manifest_zip_central_directory_size_bytes","post_write_audit_zip_central_directory_size_bytes",
              "trial_manifest_sha256","post_write_audit_sha256","trial_manifest_sha256_match","post_write_audit_sha256_match")
    if any(any(k not in r or r[k] in (None,"") for k in required) for r in rows):
        raise SystemExit("D1_REQUIRED_SIZE_OR_HASH_EVIDENCE_MISSING")
    if any(not r["trial_manifest_sha256_match"] or not r["post_write_audit_sha256_match"] for r in rows):
        raise SystemExit("D1_ROOT_HASH_RECONCILIATION_FAILED")
    compact=[]
    for r in rows:
        compact.append({
          "scenario_id":r["scenario_id"],"trial_id":r["trial_id"],
          "trial_manifest_size_bytes":r["trial_manifest_size_bytes"],
          "trial_manifest_zip_central_directory_size_bytes":r["trial_manifest_zip_central_directory_size_bytes"],
          "trial_manifest_sha256":r["trial_manifest_sha256"],
          "trial_manifest_sha256_match":r["trial_manifest_sha256_match"],
          "post_write_audit_size_bytes":r["post_write_audit_size_bytes"],
          "post_write_audit_zip_central_directory_size_bytes":r["post_write_audit_zip_central_directory_size_bytes"],
          "post_write_audit_sha256":r["post_write_audit_sha256"],
          "post_write_audit_sha256_match":r["post_write_audit_sha256_match"],
          "normalized_audit_status":r["normalized_audit_status"]
        })
    payload={
      "schema_version":"d1-105-manifest-size-evidence-v1",
      "classification":"PASS_SCOPED_REPRESENTATIVE_FULL_LOGGING",
      "repository":"yasmin977209-ux/motorcycle-simulation",
      "source_artifacts":{
        name:{"artifact_id":pin.artifact_id,"run_id":pin.run_id,"size_bytes":pin.size_bytes,"sha256":pin.sha256,"filename":pin.filename}
        for name,pin in PINS.items()
      },
      "key_count":105,"verified_key_count":105,
      "size_semantics":"Actual decompressed member byte lengths are recorded and cross-checked against ZIP central-directory uncompressed sizes; each exact byte stream is independently SHA-256 matched to the per-key digest in the Full Logging root manifest.",
      "records":compact,
      "limitations":["105 representative keys only; not all 48,000 historical trial payloads.",
        "Original archive members remain unmodified.",
        "Five historical accounting fields remain MISSING_EVIDENCE; no zero-fill or backfill."]
    }
    raw=(json.dumps(payload,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf-8")
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_bytes(raw)
    print(json.dumps({"status":payload["classification"],"keys":105,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()},sort_keys=True))

if __name__=="__main__": main()
