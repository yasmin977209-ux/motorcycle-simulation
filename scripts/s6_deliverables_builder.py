"""Independent, read-only S6 Shared Model builder. Never runs or reselects Trials."""
from __future__ import annotations
import argparse, json
from decimal import Decimal
from pathlib import Path
from .s6_artifact_reader import S6ArtifactReader, S6_SOURCE, S6_COHORT, C100_SOURCE, C100_COHORT, MASTER_SEED
from .s6_deliverables_model import S6SharedModel, SourceRef, to_jsonable
from .s6_manifest_resolver import resolve_trial_manifest

GOVERNING_DECISION="D-2026-10-30-REFERENCE-V2.4.0"
GOVERNING_SHA="225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b"
HISTORICAL_S6_SHA="e5efaf0874384e8248c339ca10e248ea9e17e9f0882153b4ef88bc955b91d53f"

def build_shared_model(paths: dict[str,str]) -> S6SharedModel:
    reader=S6ArtifactReader(paths).open_all()
    try:
        agg,full=(reader.archives[k] for k in ("aggregate","full_logging"))
        manifest=agg.read_json("manifest.json")
        selection=full.read_json("stagec-output/representative_selection_map.json")
        unique=full.read_json("stagec-output/representative_unique_keys.json")
        root=full.read_json("stagec-output/representative_full_logging_manifest.json")
        reuse=agg.read_json("c100_reuse.json")
        if manifest.get("source_sha")!=S6_SOURCE or manifest.get("cohort_id")!=S6_COHORT: raise ValueError("S6_AGGREGATE_IDENTITY_MISMATCH")
        if manifest.get("master_seed")!=MASTER_SEED: raise ValueError("S6_MASTER_SEED_MISMATCH")
        if reuse.get("source_sha")!=C100_SOURCE or reuse.get("cohort_id")!=C100_COHORT: raise ValueError("C100_IDENTITY_MISMATCH")
        if reuse.get("status")!="REUSED_READ_ONLY" or reuse.get("rerun") is not False: raise ValueError("C100_REUSE_POLICY_MISMATCH")
        if selection.get("governing_decision_id")!=GOVERNING_DECISION or selection.get("governing_reference_sha256")!=GOVERNING_SHA: raise ValueError("GOVERNING_REFERENCE_PIN_MISMATCH")
        assignments=selection.get("assignments",[]); keys=unique.get("unique_keys",[]); root_rows=root.get("results",[])
        if len(assignments)!=125 or len(keys)!=105 or len(root_rows)!=105: raise ValueError("REPRESENTATIVE_INVENTORY_COUNT_MISMATCH")
        if unique.get("role_assignment_count")!=125 or unique.get("unique_key_count")!=105: raise ValueError("UNIQUE_KEY_MANIFEST_COUNT_MISMATCH")
        if root.get("role_assignment_count")!=125 or root.get("unique_key_count")!=105: raise ValueError("ROOT_MANIFEST_COUNT_MISMATCH")
        if root.get("full_logging_keys_completed")!=105 or root.get("full_logging_keys_failed")!=0: raise ValueError("FULL_LOGGING_COMPLETION_MISMATCH")
        role_keys={(a["scenario_id"],a["trial_id"],a["role"]) for a in assignments}
        key_index={(k["scenario_id"],k["trial_id"]):k for k in keys}
        root_index={(r["scenario_id"],r["trial_id"]):r for r in root_rows}
        if len(role_keys)!=125 or len(key_index)!=105 or set(key_index)!=set(root_index): raise ValueError("FROZEN_KEY_SET_MISMATCH")
        by_key={}
        for a in assignments:
            key=(a["scenario_id"],a["trial_id"]); k=key_index.get(key)
            if not k: raise ValueError("ASSIGNMENT_WITHOUT_UNIQUE_KEY")
            if any(a.get(x)!=k.get(x) for x in ("source_sha","cohort_id","trial_fingerprint")): raise ValueError("ASSIGNMENT_KEY_IDENTITY_MISMATCH")
            by_key.setdefault(key,[]).append(a["role"])
        for key,k in key_index.items():
            expected=(S6_SOURCE,S6_COHORT) if k["cohort_id"]==S6_COHORT else (C100_SOURCE,C100_COHORT) if k["cohort_id"]==C100_COHORT else (None,None)
            if (k.get("source_sha"),k.get("cohort_id"))!=expected or expected==(None,None): raise ValueError("UNKNOWN_OR_CROSS_BOUND_COHORT")
        trial_records=[]; reconciliation=[]
        for key,k in sorted(key_index.items()):
            rr=root_index[key]
            if rr.get("trial_fingerprint")!=k.get("trial_fingerprint"): raise ValueError("ROOT_FINGERPRINT_MISMATCH")
            res=resolve_trial_manifest(full,rr,"stagec-output/full_logging",k)
            trial,audit,result=res["trial_manifest"],res["post_write_audit"],res["trial_result"]
            if any(trial.get(x)!=k.get(x) for x in ("source_sha","cohort_id","scenario_id","trial_id")): raise ValueError("TRIAL_MANIFEST_IDENTITY_MISMATCH")
            if k["cohort_id"]==S6_COHORT and trial.get("master_seed")!=MASTER_SEED: raise ValueError("S6_TRIAL_SEED_MISMATCH")
            if result.get("trial_fingerprint")!=k.get("trial_fingerprint"): raise ValueError("TRIAL_RESULT_FINGERPRINT_MISMATCH")
            vals={a["final_net_project_equity"] for a in assignments if (a["scenario_id"],a["trial_id"])==key}
            if vals and vals!={result["final_net_project_equity"]}: raise ValueError("FROZEN_EQUITY_VALUE_MISMATCH")
            source=SourceRef(reader.archives["full_logging"].pin.artifact_id,reader.archives["full_logging"].pin.run_id,
              f"stagec-output/full_logging/{rr['folder']}/trial_result.json",
              trial.get("files",{}).get("trial_result.json",{}).get("sha256"),k["cohort_id"],k["source_sha"],k["trial_id"])
            values={name:{"value":value,"source":to_jsonable(source),"evidence_status":"VERIFIED_LOCAL"} for name,value in result.items()}
            trial_records.append({"scenario_id":key[0],"trial_id":key[1],"cohort_id":k["cohort_id"],
              "source_sha":k["source_sha"],"trial_fingerprint":k["trial_fingerprint"],
              "role_assignments":sorted(by_key.get(key,[])),"values":values,
              "trial_manifest_status":trial.get("status"),"post_write_audit_status":audit.get("status")})
            reconciliation.append({"scenario_id":key[0],"trial_id":key[1],"original_status":trial.get("status"),
              "normalized_audit_status":res["normalized_audit_status"],"identity_match":res["identity_match"],
              "fingerprint_match":res["fingerprint_match"],"post_write_audit_pass":res["post_write_audit_pass"],
              "trial_manifest_size_bytes":res["trial_manifest_size_bytes"],
              "trial_manifest_zip_central_directory_size_bytes":res["trial_manifest_zip_central_directory_size_bytes"],
              "trial_manifest_sha256":res["trial_manifest_sha256"],"trial_manifest_sha256_match":res["trial_manifest_sha256_match"],
              "post_write_audit_size_bytes":res["post_write_audit_size_bytes"],
              "post_write_audit_zip_central_directory_size_bytes":res["post_write_audit_zip_central_directory_size_bytes"],
              "post_write_audit_sha256":res["post_write_audit_sha256"],"post_write_audit_sha256_match":res["post_write_audit_sha256_match"],
              "reasons":res["reasons"]})
        s6=sum(k["cohort_id"]==S6_COHORT for k in keys); c100n=sum(k["cohort_id"]==C100_COHORT for k in keys)
        if (s6,c100n)!=(100,5): raise ValueError("COHORT_KEY_COUNTS_MISMATCH")
        return S6SharedModel("s6-shared-model-v1",GOVERNING_DECISION,GOVERNING_SHA,HISTORICAL_S6_SHA,
          {"S6":{"source_sha":S6_SOURCE,"cohort_id":S6_COHORT,"master_seed":MASTER_SEED},
           "C100":{"source_sha":C100_SOURCE,"cohort_id":C100_COHORT,"reuse_classification":"CROSS_COHORT_DETERMINISTIC_REUSE"}},
          assignments,keys,trial_records,reconciliation,
          ["105 representative keys only; not 48,000 trials.",
           "normalized_audit_status remains NOT_VERIFIED where independent expected byte sizes are absent.",
           "Parquet value-level revalidation is separate and is not implied by this shared model.",
           "Five historical accounting fields remain MISSING_EVIDENCE; no zero-fill or backfill.",
           "C100 is cross-cohort deterministic reuse, not independent S6 sampling."])
    finally: reader.close()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--aggregate",required=True); p.add_argument("--full-logging",required=True); p.add_argument("--c100",required=True); p.add_argument("--output",required=True)
    a=p.parse_args()
    model=build_shared_model({"aggregate":a.aggregate,"full_logging":a.full_logging,"c100":a.c100})
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    Path(a.output).write_text(json.dumps(to_jsonable(model),ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"role_assignments":len(model.representative_mapping),"unique_keys":len(model.unique_keys),
      "trial_records":len(model.trial_records),"manifest_not_verified":sum(x["normalized_audit_status"]=="NOT_VERIFIED" for x in model.manifest_reconciliation)},indent=2))

if __name__=="__main__": main()
