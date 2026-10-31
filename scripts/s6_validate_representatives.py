"""Validate frozen representative keys without reselecting cases or running trials."""
from __future__ import annotations
import json
from .s6_artifact_reader import S6ArtifactReader, MissingEvidenceError

def validate(paths: dict[str,str], output: str) -> dict:
    reader=S6ArtifactReader(paths).open_all()
    try:
        agg=reader.archives["aggregate"]; full=reader.archives["full_logging"]
        selection=full.read_json("stagec-output/representative_selection_map.json")
        root=full.read_json("stagec-output/representative_full_logging_manifest.json")
        assignments=selection["assignments"]
        s6_assignments=[a for a in assignments if a["cohort_id"]=="s6-v23-da1a9ea9"]
        c100_assignment_count=sum(1 for a in assignments if a["cohort_id"]=="c100-v23-s4-20261026-965281d5")
        parquet_status="NOT_VERIFIED"; detail="PARQUET_READER_UNAVAILABLE_OR_SCHEMA_UNCHECKED"
        try:
            table=agg.read_parquet("trials_summary.parquet")
            cols={c.lower():c for c in table.column_names}
            scenario=cols.get("scenario_id"); trial=cols.get("trial_id"); equity=cols.get("final_net_project_equity")
            if not all((scenario,trial,equity)): detail="REQUIRED_COLUMNS_NOT_FOUND:"+",".join(table.column_names)
            else:
                by={(r[scenario],r[trial]):r[equity] for r in table.select([scenario,trial,equity]).to_pylist()}
                mismatches=[(a["scenario_id"],a["trial_id"]) for a in s6_assignments
                  if by.get((a["scenario_id"],a["trial_id"])) is None or int(by[(a["scenario_id"],a["trial_id"])])!=int(a["final_net_project_equity"])]
                parquet_status="PASS_SCOPED" if not mismatches else "FAIL_SCOPED"
                detail={"rows_checked":len(s6_assignments),"mismatches":mismatches}
        except MissingEvidenceError: pass
        result={"status":"PASS_SCOPED_FROZEN_MAPPING_INTEGRITY","role_assignments":len(assignments),
          "unique_keys":root.get("unique_key_count"),"full_logging_completed":root.get("full_logging_keys_completed"),
          "full_logging_failed":root.get("full_logging_keys_failed"),"s6_role_assignments":len(s6_assignments),"c100_role_assignments":c100_assignment_count,"c100_golden_revalidation":"NOT_RUN_SEPARATE_GOLDEN_REQUIRED","parquet_value_revalidation":parquet_status,
          "parquet_detail":detail,"selection_recomputed":False,"trial_execution":"NOT_RUN"}
        if len(assignments)!=125 or root.get("role_assignment_count")!=125: raise ValueError("ROLE_ASSIGNMENT_COUNT_MISMATCH")
        if len(s6_assignments)!=100 or c100_assignment_count!=25: raise ValueError("COHORT_ROLE_ASSIGNMENT_COUNTS_MISMATCH")
        if root.get("unique_key_count")!=105 or root.get("full_logging_keys_completed")!=105: raise ValueError("UNIQUE_KEY_COUNT_MISMATCH")
        if root.get("full_logging_keys_failed")!=0: raise ValueError("FULL_LOGGING_FAILURES_PRESENT")
        if len({(a["scenario_id"],a["trial_id"]) for a in assignments})!=105: raise ValueError("UNIQUE_KEY_SET_MISMATCH")
        with open(output,"w",encoding="utf-8") as f: json.dump(result,f,ensure_ascii=False,indent=2,sort_keys=True); f.write("\n")
        return result
    finally: reader.close()

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    for name in ("aggregate","full-logging","c100"): p.add_argument("--"+name,required=True)
    p.add_argument("--output",required=True); a=p.parse_args()
    print(json.dumps(validate({"aggregate":a.aggregate,"full_logging":a.full_logging,"c100":a.c100},a.output),indent=2))
