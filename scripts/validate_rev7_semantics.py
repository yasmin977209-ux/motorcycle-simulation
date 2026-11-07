#!/usr/bin/env python3
"""Fail-closed semantic/relational checks for operative REV7 sections 3 and 4."""
import argparse,json,re
from pathlib import Path
STAGES=("D0","D1","D2","D3","D4","D5","D6")
TEST_IDS=("175","176","179","180","181","182","183","186")
CONSTANTS={"financial_gate_a":"PASS_SCOPED","production_gate_a":"NOT_DECLARED",
 "gate_b_n2400":"FAIL_SCOPED (10/10)","stability":"NOT_CONVERGED (0/60)","n4800":"NOT_EXECUTED"}
MISSING=("Accounts_Receivable","Accumulated_Depreciation","Gross_Bike_Assets","Guarantee_Claim_Receivable","Total_Assets")
def main():
 p=argparse.ArgumentParser();p.add_argument("--library",required=True);p.add_argument("--closure",required=True);a=p.parse_args()
 text=Path(a.library).read_text(encoding="utf-8")
 section=text[text.index("## REV7 — Unified active operating contract"):]
 s3=section.split("### 3. Independent status dimensions and Fail-Closed",1)[1].split("### 4. D0–D6 sequence",1)[0]
 s4=section.split("### 4. D0–D6 sequence and current observed dispositions",1)[1].split("### 5.",1)[0]
 for field in ("Workflow_Status","Audit_Status","Stage_Disposition","Global_Preservation_Status","Final_Acceptance"):
  assert s3.count(field)==1,("REV7_STATUS_DIMENSION_MISSING_OR_DUPLICATED",field)
 closure=json.loads(Path(a.closure).read_text(encoding="utf-8"));stages=closure.get("stages",{})
 assert set(stages)==set(STAGES),("CLOSURE_STAGE_SET_MISMATCH",sorted(stages))
 extracted={}
 for stage in STAGES:
  match=re.search(r"^- "+stage+r":\s*([^;\n]+)",s4,re.M)
  assert match,("REV7_STAGE_ROW_MISSING",stage)
  extracted[stage]=match.group(1).split(" on tested SHA",1)[0].strip()
  assert extracted[stage]==stages[stage],("REV7_CLOSURE_STATUS_CONFLICT",stage,extracted[stage],stages[stage])
 for tid in TEST_IDS: assert re.search(r"(?<!\d)"+tid+r"(?!\d)",s4),("REV7_REQUIRED_TEST_ID_MISSING",tid)
 for value in CONSTANTS.values(): assert value in section,("REV7_CONSTANT_MISSING",value)
 gates=closure.get("preserved_gates",{})
 for key,value in CONSTANTS.items(): assert str(gates.get(key,""))==value,("CLOSURE_CONSTANT_CONFLICT",key,gates.get(key),value)
 for field in MISSING:
  assert field in section and field in gates.get("missing_fields",[]),("MISSING_ACCOUNTING_FIELD_CONFLICT",field)
 assert "241 = 64 + 177 + 0" in s4
 assert closure.get("project_status")=="T2_INTERIM / NOT_FINAL_BLOCKED"
 assert closure.get("preservation",{}).get("global_gate")=="BLOCKED"
 print(json.dumps({"REV7_001":"PASS","stage_statuses":extracted,"normative_test_ids":list(TEST_IDS),
  "immutable_constants":CONSTANTS,"missing_accounting_fields":list(MISSING),
  "global_preservation":"BLOCKED","project_status":"T2_INTERIM / NOT_FINAL_BLOCKED"},sort_keys=True))
if __name__=="__main__": main()
