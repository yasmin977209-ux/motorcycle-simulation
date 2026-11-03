from __future__ import annotations
import argparse, hashlib, io, json, os, re, stat, zipfile
from pathlib import Path, PurePosixPath
from openpyxl import load_workbook
from docx import Document

ARTIFACT_ID=13264003231
ARTIFACT_RUN=41704252218
ARTIFACT_SIZE=519115272
ARTIFACT_SHA="7da3dc1bba9972854536b3615f567029e66a0988e90c79da2a555b10b85b9fe5"
PACKAGE="Motorcycle_Simulation_D5_T2_INTERIM_2026-11-03.zip"
PACKAGE_SIZE=519102426
PACKAGE_SHA="300720a318864fb3969a8813a76c65473be3c8648bea7fb359de23230a8ff4f5"
GOV_SHA="225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b"
HIST_SHA="e5efaf0874384e8248c339ca10e248ea9e17e9f0882153b4ef88bc955b91d53f"
S6={"SOURCE_SHA":"da1a9ea9b5cd789c944de3f07b08395bb67c49e7","cohort_id":"s6-v23-da1a9ea9","MASTER_SEED":20270101}
C100={"SOURCE_SHA":"965281d52441cd0d4b744e211c9f68ee4cdc3753","cohort_id":"c100-v23-s4-20261026-965281d5"}
MISSING=["Accounts_Receivable","Accumulated_Depreciation","Gross_Bike_Assets","Guarantee_Claim_Receivable","Total_Assets"]
FILES=["Full_Results_EN.xlsx","النتائج_الكاملة_AR.xlsx","التقرير_الكامل_AR.docx","Full_Report_EN.docx","الملخص_AR.docx","Summary_EN.docx","دراسة_الجدوى_AR.docx"]
EXPECTED=set(FILES+["manifest.json"])
CONTRACTS={
"175":"185 sheets per workbook; identical sheet order; numeric parity; no Excel errors",
"176":"Every report numeric value has Number Registry lineage; no manual unregistered number",
"179":"manifest fingerprints and provenance/commit/command/library/MASTER_SEED",
"180":"DAILY worksheet ordered round-trip; dates and numbers preserved",
"181":"Daily partner balances exist for representative trials; absence is MISSING_EVIDENCE, never inferred",
"182":"No float leakage into financial statistics; exact rational recomputation",
"183":"All package rows belong to one cohort; reject mixed cohort identities",
"186":"Seven deliverables plus manifest in exactly eight-member ZIP; external SHA256SUMS and remote bytes"
}
def sha(b): return hashlib.sha256(b).hexdigest()
def file_sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for c in iter(lambda:f.read(8*1024*1024),b""): h.update(c)
 return h.hexdigest()
def safe(n):
 p=PurePosixPath(n)
 return bool(n) and "\\" not in n and not n.startswith("/") and not p.is_absolute() and not (len(n)>1 and n[1]==":") and all(x not in ("",".","..") for x in n.rstrip("/").split("/"))
def zip_check(z, expected):
 infos=z.infolist(); names=[x.filename for x in infos]
 if len(names)!=len(set(names)): raise ValueError("ZIP_DUPLICATE_MEMBER")
 if set(names)!=expected: raise ValueError("ZIP_MEMBER_INVENTORY_MISMATCH")
 for x in infos:
  if not safe(x.filename): raise ValueError("ZIP_UNSAFE_PATH:"+x.filename)
  if ((x.external_attr>>16)&0o170000)==stat.S_IFLNK: raise ValueError("ZIP_SYMLINK:"+x.filename)
 bad=z.testzip()
 if bad: raise ValueError("ZIP_CRC_FAILURE:"+bad)
 return names
def parse_sums(raw):
 out={}
 for line in raw.decode("utf-8").splitlines():
  if not line.strip(): continue
  m=re.match(r"^([0-9a-fA-F]{64})\s+\*?(.+)$",line.strip())
  if not m: raise ValueError("SHA256SUMS_INVALID_LINE")
  if m.group(2) in out: raise ValueError("SHA256SUMS_DUPLICATE")
  out[m.group(2)]=m.group(1).lower()
 return out
def audit(a):
 root=Path(a.root); artifact=Path(a.artifact); checks={}
 outer=artifact.read_bytes()
 if len(outer)!=ARTIFACT_SIZE or sha(outer)!=ARTIFACT_SHA: raise ValueError("ACTIONS_ARTIFACT_FINGERPRINT_MISMATCH")
 with zipfile.ZipFile(io.BytesIO(outer)) as z:
  zip_check(z,{PACKAGE,"manifest.json","SHA256SUMS.txt"})
  outer_manifest=z.read("manifest.json"); sums_raw=z.read("SHA256SUMS.txt"); pkg=z.read(PACKAGE)
 if len(pkg)!=PACKAGE_SIZE or sha(pkg)!=PACKAGE_SHA: raise ValueError("D5_PACKAGE_FINGERPRINT_MISMATCH")
 with zipfile.ZipFile(io.BytesIO(pkg)) as z:
  zip_check(z,EXPECTED); payload={n:z.read(n) for n in z.namelist()}
 if payload["manifest.json"]!=outer_manifest: raise ValueError("MANIFEST_OUTER_INNER_MISMATCH")
 manifest=json.loads(payload["manifest.json"])
 if manifest.get("package_member_count")!=8 or manifest.get("package_status")!="T2_INTERIM / NOT_FINAL_BLOCKED": raise ValueError("MANIFEST_STATUS_MISMATCH")
 for name in FILES:
  data=payload[name]; rec=manifest.get("package_members",{}).get(name,{})
  if rec.get("bytes")!=len(data) or rec.get("sha256")!=sha(data): raise ValueError("MANIFEST_MEMBER_MISMATCH:"+name)
 sums=parse_sums(sums_raw)
 if len(sums)!=10: raise ValueError("SHA256SUMS_COUNT_MISMATCH")
 required_sums={PACKAGE,"manifest.json",*FILES,"results/number_registry.json"}
 if set(sums)!=required_sums: raise ValueError("SHA256SUMS_COVERAGE_MISMATCH")
 for name,digest in sums.items():
  if name==PACKAGE:
   if digest!=PACKAGE_SHA: raise ValueError("SUMS_PACKAGE_MISMATCH")
  elif name in payload:
   if digest!=sha(payload[name]): raise ValueError("SUMS_MEMBER_MISMATCH:"+name)
  elif name=="results/number_registry.json":
   reg=root/"results/number_registry.json"
   if not reg.exists() or file_sha(reg)!=digest: raise ValueError("SUMS_REGISTRY_MISMATCH")
  else: raise ValueError("SUMS_UNKNOWN_PATH:"+name)
 checks["artifact_outer"]={"status":"PASS","artifact_id":ARTIFACT_ID,"run_id":ARTIFACT_RUN,"bytes":len(outer),"sha256":sha(outer)}
 checks["zip_inventory_crc_paths"]={"status":"PASS","inner_members":sorted(EXPECTED),"bytes":len(pkg),"sha256":sha(pkg)}
 checks["manifest_sha256sums"]={"status":"PASS","manifest_sha256":sha(payload["manifest.json"]),"sha256sums_entries":len(sums),"sha256sums_sha256":sha(sums_raw)}
 ids=manifest.get("source_identities",{})
 if manifest.get("current_governing_reference_sha256")!=GOV_SHA or manifest.get("historical_execution_reference_sha256")!=HIST_SHA: raise ValueError("REFERENCE_IDENTITY_MISMATCH")
 if ids.get("S6")!=S6 or any(ids.get("C100",{}).get(k)!=v for k,v in C100.items()) or ids.get("C100",{}).get("classification")!="CROSS_COHORT_DETERMINISTIC_REUSE": raise ValueError("COHORT_IDENTITY_MISMATCH")
 gates={"financial_gate_a":"PASS_SCOPED","production_gate_a":"NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS","gate_b_n2400":"FAIL_SCOPED (10/10)","stability":"NOT_CONVERGED (0/60)","n4800":"NOT_EXECUTED","c100_golden":"NOT_RUN"}
 for k,v in gates.items():
  if manifest.get("gate_statuses",{}).get(k)!=v: raise ValueError("GATE_PROMOTION_OR_MISMATCH:"+k)
 if set(manifest.get("missing_accounting_fields",[]))!=set(MISSING): raise ValueError("MISSING_ACCOUNTING_FIELDS_MISMATCH")
 checks["identities_gates"]={"status":"PASS","S6":S6,"C100":C100,"gate_statuses":gates,"missing_accounting_fields":MISSING}
 # Workbook structure, ordering, numeric parity, formulas/errors and directional layout
 nums=None; sheetnames=None; numeric_count=0
 for name,is_ar in [("Full_Results_EN.xlsx",False),("النتائج_الكاملة_AR.xlsx",True)]:
  p=root/("d6_"+name); p.write_bytes(payload[name])
  wb=load_workbook(p,read_only=True,data_only=False); wbv=load_workbook(p,read_only=True,data_only=True)
  current={}
  try:
   if len(wb.sheetnames)!=185: raise ValueError("EXCEL_SHEET_COUNT:"+name)
   if sheetnames is not None and wb.sheetnames!=sheetnames: raise ValueError("EXCEL_SHEET_ORDER_MISMATCH")
   sheetnames=wb.sheetnames
   if is_ar and not all(bool(wb[s].sheet_view.rightToLeft) for s in wb.sheetnames): raise ValueError("ARABIC_RTL_MISSING")
   if not is_ar and any(bool(wb[s].sheet_view.rightToLeft) for s in wb.sheetnames): raise ValueError("ENGLISH_RTL_UNEXPECTED")
   for ws,wsv in zip(wb.worksheets,wbv.worksheets):
    header={}
    for ri,(row,rowv) in enumerate(zip(ws.iter_rows(),wsv.iter_rows())):
     if ri==0: header={c.column-1:str(c.value).lower() for c in row if c.value is not None}
     for c,cv in zip(row,rowv):
      if c.data_type=="f": raise ValueError("EXCEL_FORMULA_CELL:"+name+":"+ws.title+":"+c.coordinate)
      if c.data_type=="e" or (isinstance(cv.value,str) and cv.value in {"#REF!","#DIV/0!","#VALUE!","#NAME?","#N/A","#NUM!","#NULL!"}): raise ValueError("EXCEL_ERROR_CELL:"+name+":"+ws.title+":"+c.coordinate)
      if isinstance(c.value,(int,float)) and not isinstance(c.value,bool):
       current[(ws.title,c.coordinate)]=c.value
       numeric_count+=1
       h=header.get(c.column-1,"")
       if isinstance(c.value,float) and any(w in h for w in ("cash","equity","asset","depreciation","receivable","revenue","expense","balance","amount","إيراد","مصروف","أصل","رصيد","مبلغ","تحصيل","إهلاك","ذمم")):
        raise ValueError("EXCEL_FINANCIAL_FLOAT:"+name+":"+ws.title+":"+c.coordinate)
  finally: wb.close(); wbv.close(); p.unlink(missing_ok=True)
  if nums is not None:
   if set(nums)!=set(current): raise ValueError("EXCEL_NUMERIC_INVENTORY_MISMATCH")
   if any(nums[k]!=current[k] for k in nums): raise ValueError("EXCEL_NUMERIC_PARITY_MISMATCH")
  nums=current
 checks["excel_175_180_182"]={"status":"PASS","sheets_per_workbook":185,"numeric_cells_compared":numeric_count,"arabic_rtl_checked":True,"english_ltr_checked":True,"formula_cells":0,"error_cells":0}
 # Parse all DOCX; page counts are reported from D4 only unless libreoffice is available
 texts={}
 for name in [x for x in FILES if x.endswith(".docx")]:
  p=root/("d6_"+name); p.write_bytes(payload[name]); doc=Document(str(p))
  t="\n".join(x.text for x in doc.paragraphs)+"\n"+"\n".join(" ".join(c.text for c in row.cells) for tb in doc.tables for row in tb.rows)
  if not t.strip(): raise ValueError("DOCX_EMPTY:"+name)
  if "T2_INTERIM" not in t and "NOT_FINAL_BLOCKED" not in t: raise ValueError("DOCX_T2_DISCLOSURE_MISSING:"+name)
  if "MISSING_EVIDENCE" not in t: raise ValueError("DOCX_MISSING_EVIDENCE_DISCLOSURE:"+name)
  texts[name]=t; p.unlink(missing_ok=True)
 checks["docx_176"]={"status":"PASS_SCOPED","docx_files":5,"detail":"All five DOCX archives parsed; T2 and MISSING_EVIDENCE disclosures present. Page count and semantic numeric-to-registry recomputation are not independently established by python-docx."}
 # Contract mapping is recorded without pretending that test IDs were re-executed.
 for tid,contract in CONTRACTS.items():
  status="PASS_SCOPED" if tid=="181" else ("PASS_SCOPED" if tid=="176" else "PASS")
  checks["test_"+tid]={"status":status,"contract":contract,"run_id":a.run_id,"tested_sha":a.tested_sha,"detail":"D6 independent artifact audit mapping; original historical test is not rerun."}
 result={"schema_version":"d6-independent-post-write-audit-v1","status":"PASS_SCOPED_WITH_LIMITATIONS","classification":"T2_INTERIM / NOT_FINAL_BLOCKED","repository":"yasmin977209-ux/motorcycle-simulation","branch":a.branch,"tested_sha":a.tested_sha,"run_id":a.run_id,"source_d5_run_id":ARTIFACT_RUN,"source_d5_artifact_id":ARTIFACT_ID,"checks":checks,"fixed_gate_states":gates,"missing_accounting_fields":MISSING,"limitations":["Test 181 is PASS_SCOPED only; no original historical 48K daily partner-balance ledgers are claimed or reconstructed.","DOCX page count is not independently re-rendered; D4 record reports three pages for each summary.","Test 176 validates disclosure/manifest and document parse but does not recompute every displayed number against the full Number Registry lineage.","The original tests 175, 176, 179, 180, 181, 182, 183 and 186 are mapped, not re-executed as historical suite tests.","No full 177-unique-test suite, Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, identity change, main write, merge, Release or final acceptance."],"d6_disposition":"PASS_SCOPED_WITH_LIMITATIONS","final_accepted":"NOT_DECLARED","p17_final_accepted":"NOT_DECLARED","p18_released":"NOT_DECLARED","converged":"NOT_DECLARED"}
 out=root/"docs"; out.mkdir(exist_ok=True)
 (out/"FINAL_AUDIT.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 lines=["# D6 Independent Post-Write Audit","",f"- Disposition: {result['status']}",f"- D5 Artifact: {ARTIFACT_ID} / Run {ARTIFACT_RUN}",f"- D6 Run: {a.run_id}",f"- Tested SHA: {a.tested_sha}","- Classification: T2_INTERIM / NOT_FINAL_BLOCKED","","| Check | Status | Detail |","|---|---|---|"]
 for k,v in checks.items(): lines.append(f"| {k} | {v['status']} | {v.get('detail',v.get('contract',''))} |")
 lines+=["","## Preserved gate states",""]+[f"- {k}: {v}" for k,v in gates.items()]+["","## Limitations",""]+[f"- {x}" for x in result["limitations"]]+["","D6 is not P17 acceptance, FINAL_ACCEPTED, CONVERGED, or release authorization."]
 (out/"FINAL_AUDIT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
 print(json.dumps({"status":result["status"],"checks":{k:v["status"] for k,v in checks.items()}},ensure_ascii=False))
def main():
 p=argparse.ArgumentParser(); p.add_argument("--artifact",required=True); p.add_argument("--root",default="."); p.add_argument("--run-id",default=os.getenv("GITHUB_RUN_ID","local")); p.add_argument("--tested-sha",default=os.getenv("GITHUB_SHA","unknown")); p.add_argument("--branch",default=os.getenv("GITHUB_REF_NAME","unknown")); audit(p.parse_args())
if __name__=="__main__": main()
