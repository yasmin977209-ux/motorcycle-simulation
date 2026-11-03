from __future__ import annotations
import argparse, gzip, hashlib, io, json, os, re, stat, time, zipfile, xml.etree.ElementTree as ET
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
def worksheet_rtl_flags(xlsx_path):
    ns={"m":"http://schemas.openxmlformats.org/spreadsheetml/2006/main","r":"http://schemas.openxmlformats.org/officeDocument/2006/relationships","p":"http://schemas.openxmlformats.org/package/2006/relationships"}
    with zipfile.ZipFile(xlsx_path) as archive:
        workbook=ET.fromstring(archive.read("xl/workbook.xml"))
        rels=ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets={item.attrib["Id"]:item.attrib["Target"] for item in rels}
        flags=[]
        for sheet in workbook.findall("m:sheets/m:sheet",ns):
            target=targets[sheet.attrib["{"+ns["r"]+"}id"]]
            path=target.lstrip("/") if target.startswith("/") else "xl/"+target
            path=path.replace("xl/../","")
            root=ET.fromstring(archive.read(path))
            view=root.find("m:sheetViews/m:sheetView",ns)
            flags.append(bool(view is not None and view.attrib.get("rightToLeft") in ("1","true","True")))
        return flags

def scan_xlsx_xml(path, entries_by_id, series_by_id, ledger_by_id, registry):
    """Stream worksheet XML to avoid millions of openpyxl Cell objects."""
    import posixpath
    from decimal import Decimal, InvalidOperation
    ns={"m":"http://schemas.openxmlformats.org/spreadsheetml/2006/main","r":"http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
    q=lambda tag:"{"+ns["m"]+"}"+tag
    digest=hashlib.sha256(); numeric_count=financial_count=0
    with zipfile.ZipFile(path) as archive:
        workbook=ET.fromstring(archive.read("xl/workbook.xml"))
        rels=ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets={x.attrib["Id"]:x.attrib["Target"] for x in rels}
        shared=[]
        if "xl/sharedStrings.xml" in archive.namelist():
            with archive.open("xl/sharedStrings.xml") as stream:
                for _,item in ET.iterparse(stream,events=("end",)):
                    if item.tag==q("si"):
                        shared.append("".join(t.text or "" for t in item.iter(q("t")))); item.clear()
        sheets=[]
        for sheet in workbook.findall("m:sheets/m:sheet",ns):
            target=targets[sheet.attrib["{"+ns["r"]+"}id"]]
            sheets.append((sheet.attrib["name"],posixpath.normpath(target.lstrip("/") if target.startswith("/") else "xl/"+target)))
        if len(sheets)!=185: raise ValueError("EXCEL_SHEET_COUNT:"+str(len(sheets)))
        for title,member in sheets:
            header={}
            with archive.open(member) as stream:
                for _,row_elem in ET.iterparse(stream,events=("end",)):
                    if row_elem.tag!=q("row"): continue
                    cells={}
                    for cell in row_elem.findall("m:c",ns):
                        ref=cell.attrib.get("r",""); match=re.fullmatch(r"([A-Z]+)([0-9]+)",ref)
                        if not match: continue
                        col=0
                        for ch in match.group(1): col=col*26+ord(ch)-64
                        typ=cell.attrib.get("t"); vn=cell.find("m:v",ns); raw=vn.text if vn is not None else None
                        if cell.find("m:f",ns) is not None: raise ValueError("EXCEL_FORMULA_CELL:"+title+":"+ref)
                        if typ=="e" or (typ in ("str","inlineStr") and raw in {"#REF!","#DIV/0!","#VALUE!","#NAME?","#N/A","#NUM!","#NULL!"}):
                            raise ValueError("EXCEL_ERROR_CELL:"+title+":"+ref)
                        if typ=="s" and raw is not None: value=shared[int(raw)]
                        elif typ=="inlineStr": value="".join(t.text or "" for t in cell.iter(q("t")))
                        elif typ=="str": value=raw or ""
                        elif typ=="b": value=raw=="1"
                        elif typ in (None,"n") and raw is not None:
                            try: number=Decimal(raw)
                            except InvalidOperation as exc: raise ValueError("EXCEL_NUMERIC_PARSE:"+title+":"+ref) from exc
                            if not number.is_finite(): raise ValueError("EXCEL_NUMERIC_NONFINITE:"+title+":"+ref)
                            cells[col]=("number",number)
                            canonical=str(number.normalize()) if number else "0"
                            digest.update((title+"|"+ref+"|"+canonical+"\\n").encode("utf-8")); numeric_count+=1
                            continue
                        else: value=None
                        cells[col]=("value",value)
                    if row_elem.attrib.get("r")=="1":
                        header={col:str(value).lower() for col,(kind,value) in cells.items() if kind=="value" and value is not None}
                    for col,(kind,value) in cells.items():
                        if kind!="number": continue
                        h=header.get(col,"")
                        if any(word in h for word in FINANCIAL_WORDS):
                            rec=cells.get(col+1); number_id=rec[1] if rec and rec[0]=="value" else None
                            if not isinstance(number_id,str) or not (number_id.startswith("NR-") or number_id.startswith("D2D-")):
                                raise ValueError("EXCEL_FINANCIAL_NUMBER_ID_MISSING:"+title+":"+str(col)+":header="+repr(h))
                            expected=registry_display(registry,number_id,entries_by_id,series_by_id,ledger_by_id)
                            if not financial_value_matches(value,expected):
                                raise ValueError("EXCEL_FINANCIAL_EXACT_VALUE_MISMATCH:"+title+":"+str(col)+":value="+str(value)+":registry="+repr(expected)+":number_id="+number_id)
                            financial_count+=1
                    row_elem.clear()
    return {"sheetnames":[x[0] for x in sheets],"numeric_count":numeric_count,"financial_count":financial_count,"numeric_digest":digest.hexdigest()}

def parse_sums(raw):
 out={}
 for line in raw.decode("utf-8").splitlines():
  if not line.strip(): continue
  m=re.match(r"^([0-9a-fA-F]{64})\s+\*?(.+)$",line.strip())
  if not m: raise ValueError("SHA256SUMS_INVALID_LINE")
  if m.group(2) in out: raise ValueError("SHA256SUMS_DUPLICATE")
  out[m.group(2)]=m.group(1).lower()
 return out
REGISTRY_SIZE=24137036
REGISTRY_SHA="743ffcced8de09a766870f201c352aabcf5789c43c84bfeae654a939700e4f87"
EXTENSION_SIZE=16440292
EXTENSION_SHA="7b7e082424a0dab9519723028e8bb99e699e2e590168db258429bb14be6c4024"
FINANCIAL_WORDS=("cash","equity","asset","depreciation","receivable","revenue","expense","profit","entitlement","debt","recovered","balance","amount","إيراد","مصروف","ربح","استحقاق","دين","مسترد","أصل","رصيد","مبلغ","تحصيل","إهلاك","ذمم","نقد")

def exact_display(n,d):
 if type(n) is not int or type(d) is not int or d<1: raise ValueError("REGISTRY_EXACT_VALUE_INVALID")
 from fractions import Fraction
 from decimal import Decimal, ROUND_HALF_EVEN, localcontext
 f=Fraction(n,d)
 if (f.numerator,f.denominator)!=(n,d): raise ValueError("REGISTRY_EXACT_VALUE_NOT_REDUCED")
 if d==1: return str(n)
 with localcontext() as ctx:
  ctx.prec=50
  return format((Decimal(n)/Decimal(d)).quantize(Decimal("0.01"),rounding=ROUND_HALF_EVEN),"f")

def stable_registry_id(prefix, value, digits=24):
 raw=json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()
 return prefix+hashlib.sha256(raw).hexdigest()[:digits]

def ledger_number_id(case, member, row_index, field):
 source_member=case["source_member_prefix"]+member
 return stable_registry_id("NR-",["D3_LEDGER_NUMBER_V1",case["source_artifact_sha256"],case["scenario_id"],case["trial_id"],source_member,row_index,field])

def add_ledger_rows(target, case, rows_key, member):
 for i,row in enumerate(case.get(rows_key,[])):
  for field,value in row.items():
   if type(value) is int:
    target[ledger_number_id(case,member,i,field)]=str(value)

def build_d3_evidence_indexes(root, registry):
 ext_path=root/"deliverables/D3_NUMBER_REGISTRY_EXTENSION.json.gz"
 if not ext_path.exists(): raise ValueError("D3_REGISTRY_EXTENSION_MISSING")
 ext_raw=ext_path.read_bytes()
 if len(ext_raw)!=EXTENSION_SIZE or sha(ext_raw)!=EXTENSION_SHA: raise ValueError("D3_REGISTRY_EXTENSION_FINGERPRINT_MISMATCH")
 extension=json.loads(gzip.decompress(ext_raw).decode("utf-8"))
 if extension.get("schema_version")!="d3-number-registry-extension-v1" or extension.get("base_registry_sha256")!=REGISTRY_SHA: raise ValueError("D3_REGISTRY_EXTENSION_BASE_MISMATCH")
 entries_by_id={x.get("number_id"):x for x in registry.get("entries",[])}
 for entry in extension.get("aggregate_entries",[])+extension.get("sensitivity_entries",[]):
  if entry.get("number_id") in entries_by_id: raise ValueError("D3_REGISTRY_EXTENSION_ID_COLLISION")
  entries_by_id[entry.get("number_id")]=entry
 series_by_id={x.get("series_id"):x for x in registry.get("daily_series",[])}
 ledger_by_id={}
 c100=registry.get("scope",{}).get("C100",{})
 modes=sorted({x.get("mode") for x in registry.get("daily_series",[])})
 metrics=sorted({x.get("metric_name") for x in registry.get("daily_series",[])})
 quantiles=sorted({x.get("quantile_name") for x in registry.get("daily_series",[])})
 full_sha=extension.get("source_artifacts",{}).get("full_logging",{}).get("sha256")
 for case in extension.get("representative_cases",[]):
  if case.get("cohort_id")!=c100.get("cohort_id"): continue
  dates=[row.get("date") for row in case.get("daily_rows",[])]
  for mode in modes:
   for metric in metrics:
    for quantile in quantiles:
     sid=stable_registry_id("D2S6-",[case["scenario_id"],c100.get("source_sha"),c100.get("cohort_id"),mode,metric,quantile,full_sha],20)
     vals=[[int(row[metric]),1] for row in case.get("daily_rows",[])]
     series_by_id[sid]={"series_id":sid,"values":vals,"date_count":len(dates)}
 for case in extension.get("representative_cases",[])+extension.get("representative_role_cases",[]):
  add_ledger_rows(ledger_by_id,case,"daily_rows","daily_snapshots.jsonl.gz")
  add_ledger_rows(ledger_by_id,case,"assets","assets.jsonl.gz")
  add_ledger_rows(ledger_by_id,case,"claims","claims.jsonl.gz")
  add_ledger_rows(ledger_by_id,case,"contracts","contracts.jsonl.gz")
  for key,rows in case.get("rollforwards",{}).items():
   for i,row in enumerate(rows):
    for field,value in row.items():
     if type(value) is int: ledger_by_id[ledger_number_id(case,key+".jsonl.gz",i,field)]=str(value)
  for field,value in case.get("trial_summary",{}).items():
   if type(value) is int: ledger_by_id[ledger_number_id(case,"trial_result.json",0,field)]=str(value)
 return entries_by_id,series_by_id,ledger_by_id

def registry_display(registry, number_id, entries_by_id=None, series_by_id=None, ledger_by_id=None):
 if entries_by_id is None: entries_by_id={x.get("number_id"):x for x in registry.get("entries",[])}
 if series_by_id is None: series_by_id={x.get("series_id"):x for x in registry.get("daily_series",[])}
 entry=entries_by_id.get(number_id)
 if entry is not None:
  n,d=entry.get("numerator"),entry.get("denominator")
  shown=exact_display(n,d)
  if entry.get("display_value")!=shown: raise ValueError("REGISTRY_DISPLAY_VALUE_MISMATCH:"+number_id)
  return shown
 if ledger_by_id and number_id in ledger_by_id: return ledger_by_id[number_id]
 m=re.fullmatch(r"D2D-([0-9a-f]{20})-([0-9]{6})",str(number_id))
 if not m: raise ValueError("FINANCIAL_NUMBER_ID_INVALID:"+str(number_id))
 series_id="D2S6-"+m.group(1); offset=int(m.group(2))
 series=series_by_id.get(series_id)
 if series is None or offset>=len(series.get("values",[])): raise ValueError("FINANCIAL_DAILY_NUMBER_ID_UNRESOLVED:"+number_id)
 pair=series["values"][offset]
 if not isinstance(pair,list) or len(pair)!=2: raise ValueError("REGISTRY_DAILY_EXACT_VALUE_INVALID:"+number_id)
 return exact_display(pair[0],pair[1])

def financial_value_matches(value, expected_display):
 from decimal import Decimal, InvalidOperation
 try:
  actual=Decimal(str(value)); expected=Decimal(expected_display)
 except (InvalidOperation, ValueError, TypeError):
  return False
 return actual.is_finite() and expected.is_finite() and actual==expected

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
 # Verify the pinned Number Registry bytes used for exact-rational financial checks.
 reg_path=root/"results/number_registry.json"
 if not reg_path.exists(): raise ValueError("NUMBER_REGISTRY_MISSING")
 reg_raw=reg_path.read_bytes()
 if len(reg_raw)!=REGISTRY_SIZE or sha(reg_raw)!=REGISTRY_SHA: raise ValueError("NUMBER_REGISTRY_FINGERPRINT_MISMATCH")
 registry=json.loads(reg_raw.decode("utf-8"),parse_float=__import__("decimal").Decimal)
 entries_by_id,series_by_id,ledger_by_id=build_d3_evidence_indexes(root,registry)
 # Stream worksheet XML directly: bounded memory and no millions of openpyxl Cell objects.
 prior_sheetnames=None; numeric_count=financial_count=0; prior_digest=None
 for name,is_ar in [("Full_Results_EN.xlsx",False),("النتائج_الكاملة_AR.xlsx",True)]:
  p=root/("d6_"+name); p.write_bytes(payload[name])
  try:
   result=scan_xlsx_xml(p,entries_by_id,series_by_id,ledger_by_id,registry)
   if prior_sheetnames is not None and result["sheetnames"]!=prior_sheetnames: raise ValueError("EXCEL_SHEET_ORDER_MISMATCH")
   prior_sheetnames=result["sheetnames"]
   rtl_flags=worksheet_rtl_flags(p)
   if len(rtl_flags)!=len(result["sheetnames"]): raise ValueError("EXCEL_SHEET_VIEW_COUNT_MISMATCH:"+name)
   if is_ar and not all(rtl_flags): raise ValueError("ARABIC_RTL_MISSING")
   if not is_ar and any(rtl_flags): raise ValueError("ENGLISH_RTL_UNEXPECTED")
   if prior_digest is not None and result["numeric_digest"]!=prior_digest: raise ValueError("EXCEL_NUMERIC_PARITY_MISMATCH")
   prior_digest=result["numeric_digest"]
   numeric_count+=result["numeric_count"]; financial_count+=result["financial_count"]
  finally: p.unlink(missing_ok=True)
  print(f"D6_EXCEL_XML_SCAN_DONE file={name} numeric_cells={result['numeric_count']} financial_cells={result['financial_count']}",flush=True)
checks["excel_175_180_182"]={"status":"PASS","sheets_per_workbook":185,"numeric_cells_compared":numeric_count,"financial_cells_exact_registry_verified":financial_count,"arabic_rtl_checked":True,"english_ltr_checked":True,"formula_cells":0,"error_cells":0}
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
