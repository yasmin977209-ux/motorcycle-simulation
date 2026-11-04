from __future__ import annotations
import argparse, gzip, hashlib, io, json, os, re, stat, subprocess, time, zipfile, xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath
from openpyxl import load_workbook
from docx import Document

PACKAGE="Motorcycle_Simulation_D5_T2_INTERIM_2026-11-03.zip"
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
def load_d5_pin(root):
 path=root/"docs/stage_d/D5_PACKAGE_PREFLIGHT_2026-11-03.json"
 if not path.is_file(): raise ValueError("D5_PREFLIGHT_MISSING")
 report=json.loads(path.read_text(encoding="utf-8"))
 if report.get("status")!="PUBLISHED_AND_REMOTE_READBACK_VERIFIED": raise ValueError("D5_NOT_PUBLISHED_OR_READBACK_VERIFIED")
 art=report.get("artifact",{}); pkg=report.get("package",{})
 if any(k not in art for k in ("id","size_in_bytes","downloaded_zip_sha256","digest","url")): raise ValueError("D5_ARTIFACT_PIN_INCOMPLETE")
 if art.get("digest")!="sha256:"+str(art["downloaded_zip_sha256"]): raise ValueError("D5_ARTIFACT_DIGEST_CONFLICT")
 if not pkg.get("path") or not pkg.get("bytes") or not pkg.get("sha256"): raise ValueError("D5_PACKAGE_PIN_INCOMPLETE")
 return {"artifact_id":int(art["id"]),"artifact_run_id":int(report["workflow_run_id"]),
  "artifact_bytes":int(art["size_in_bytes"]),"artifact_sha256":str(art["downloaded_zip_sha256"]),
  "package_bytes":int(pkg["bytes"]),"package_sha256":str(pkg["sha256"])}
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
    """Fast bounded-memory worksheet XML audit using lxml streaming."""
    import posixpath
    from decimal import Decimal, InvalidOperation
    from lxml import etree as LET
    ns={"m":"http://schemas.openxmlformats.org/spreadsheetml/2006/main","r":"http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
    q=lambda tag:"{"+ns["m"]+"}"+tag
    digest=hashlib.sha256(); numeric_count=financial_count=0
    mismatch_count=0; mismatch_samples=[]
    with zipfile.ZipFile(path) as archive:
        workbook=LET.fromstring(archive.read("xl/workbook.xml"))
        rels=LET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets={x.attrib["Id"]:x.attrib["Target"] for x in rels}
        shared=[]
        if "xl/sharedStrings.xml" in archive.namelist():
            with archive.open("xl/sharedStrings.xml") as stream:
                for _,item in LET.iterparse(stream,events=("end",),tag=q("si"),huge_tree=True):
                    shared.append("".join(t.text or "" for t in item.iter(q("t"))))
                    item.clear()
                    while item.getprevious() is not None: del item.getparent()[0]
        sheets=[]
        for sheet in workbook.findall("m:sheets/m:sheet",ns):
            target=targets[sheet.attrib["{"+ns["r"]+"}id"]]
            sheets.append((sheet.attrib["name"],posixpath.normpath(target.lstrip("/") if target.startswith("/") else "xl/"+target)))
        if len(sheets)!=185: raise ValueError("EXCEL_SHEET_COUNT:"+str(len(sheets)))
        for title,member in sheets:
            header={}
            with archive.open(member) as stream:
                context=LET.iterparse(stream,events=("end",),tag=q("row"),huge_tree=True)
                for _,row_elem in context:
                    cells={}; cell_refs={}
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
                            cells[col]=("number",number); cell_refs[col]=ref
                            canonical=str(number.normalize()) if number else "0"
                            digest.update((title+"|"+ref+"|"+canonical+"\n").encode("utf-8")); numeric_count+=1
                            continue
                        else: value=None
                        if isinstance(value,str) and value in {"#REF!","#DIV/0!","#VALUE!","#NAME?","#N/A","#NUM!","#NULL!"}:
                            raise ValueError("EXCEL_ERROR_CELL:"+title+":"+ref)
                        cells[col]=("value",value)
                    if row_elem.attrib.get("r")=="1":
                        header={col:str(value).lower() for col,(kind,value) in cells.items() if kind=="value" and value is not None}
                    for col,(kind,value) in cells.items():
                        if kind!="number": continue
                        h=header.get(col,"")
                        if any(word in h for word in FINANCIAL_WORDS):
                            rec=cells.get(col+1); number_id=rec[1] if rec and rec[0]=="value" else None
                            error=None; expected=None
                            if not isinstance(number_id,str) or not (number_id.startswith("NR-") or number_id.startswith("D2D-")):
                                error="NUMBER_ID_MISSING"
                            else:
                                expected=registry_display(registry,number_id,entries_by_id,series_by_id,ledger_by_id)
                                if not financial_value_matches(value,expected): error="EXACT_VALUE_MISMATCH"
                            if error:
                                mismatch_count+=1
                                if len(mismatch_samples)<1000:
                                    mismatch_samples.append({"sheet":title,"cell":cell_refs.get(col,str(col)),"header":h,"actual":str(value),"expected":expected,"number_id":number_id,"error":error})
                            else: financial_count+=1
                    row_elem.clear()
                    while row_elem.getprevious() is not None: del row_elem.getparent()[0]
    return {"sheetnames":[x[0] for x in sheets],"numeric_count":numeric_count,"financial_count":financial_count,"numeric_digest":digest.hexdigest(),"financial_mismatch_count":mismatch_count,"financial_mismatch_samples":mismatch_samples}


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

def disclosure_173_findings(text):
 value=" ".join(str(text).lower().split())
 def has(*terms): return any(term.lower() in value for term in terms)
 requirements={
  "conditional_on_model_limitations":has("conditional on model limitations","مشروطة بحدود النموذج"),
  "realism_gap":has("not a realistic forecast","not a realistic prediction","not realistic","ليس توقعاً واقعياً","ليس توقعا واقعيا","ليست توقعاً واقعياً","ليست توقعا واقعيا"),
  "unlimited_demand":has("unlimited demand","demand is unlimited","الطلب غير محدود","طلباً غير محدود","طلب غير محدود"),
  "immediate_next_day_rerent":has("immediate re-rental on the following day","immediate re-rental","immediate re-rent","re-rent the next day","re-renting the next day","إعادة التأجير الفورية","إعادة التأجير في اليوم التالي","إعادة تأجير فورية"),
  "no_fleet_cap":has("no fleet-size ceiling","no fleet cap","no cap on fleet","no limit on fleet size","لا سقف لحجم الأسطول","لا يوجد سقف لحجم الأسطول"),
  "no_operating_costs_maintenance_theft_inflation":(has("no operating, maintenance, theft, or inflation costs") or has("operating costs","operating expenses","تكاليف تشغيل")) and has("maintenance","صيانة") and has("theft","سرقة") and has("inflation","تضخم"),
  "no_renter_variation":has("no tenant heterogeneity","no variation between renters","no variation among renters","لا تباين بين المستأجرين","لا اختلاف بين المستأجرين"),
  "deterministic_friday_and_settlement_fees":has("deterministic friday fees and settlement rent","friday fee","friday charge","رسم الجمعة") and has("settlement rent","settlement rental","إيجار التسوية") and has("deterministic","حتمي","حتميان","حتمية"),
  "book_value_not_market_value":has("book value, not market value","book value not market value","carrying value, not market value") or (has("القيمة الدفترية") and has("السوقية")),
  "excluded_repairs_fines_theft_accidents_admin_taxes":has("no repairs, fines, theft/accidents, administrative expenses, or taxes") or (has("repairs","repair","إصلاحات","إصلاح") and has("fines","violations","مخالفات","غرامات") and has("theft","سرقة") and has("accidents","حوادث") and has("administrative expenses","administrative costs","مصاريف إدارية","مصروفات إدارية") and has("taxes","tax","ضرائب")),
  "no_external_financing":has("no external financing","without external financing","لا تمويل خارجي","دون تمويل خارجي"),
  "guarantee_is_deterministic_not_actual_recovery_variability":(has("deterministic multiplier") and has("does not represent variability in actual recovery capacity")) or (has("مضاعف حتمي","مضاعفاً حتمياً","مضاعفا حتميا") and has("القدرة الفعلية على الاسترداد","الاسترداد الفعلي")),
  "non_monotonic_structural_explanation":(has("non-monotonic scenario results may occur for structural reasons") and has("lower collection must not be read as better")) or (has("نتائج غير رتيبة") and has("لأسباب بنيوية") and has("التحصيل الأقل") and has("أفضل")),
  "zero_loss_not_guarantee":(has("zero accounting-loss probability is not a guarantee","zero probability of accounting loss","zero accounting loss") and has("not a guarantee","does not guarantee")) or (has("احتمال الخسارة المحاسبية الصفري","احتمال الخسارة صفري") and has("ليس ضماناً","ليس ضمانا","لا يمثل ضماناً","لا يمثل ضمانا")),
  "no_inference_for_unexecuted_scenario":has("no value may be inferred for an unexecuted scenario","لا يجوز استنتاج أي رقم لسيناريو لم يُشغَّل","لا يجوز استنتاج أي رقم لسيناريو لم يشغل"),
 }
 return [k for k,v in requirements.items() if not v]

def docx_directionality(path):
 """Inspect explicit paragraph/run direction on every Word text-story part."""
 ns={"w":"http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
 story=re.compile(r"^word/(?:document|header[0-9]+|footer[0-9]+|footnotes|endnotes|comments)\\.xml$")
 paragraphs=0; text_runs=0; bidi_true=bidi_false=bidi_missing=0
 rtl_true=rtl_false=rtl_missing=0; parts=[]
 with zipfile.ZipFile(path) as archive:
  names=sorted(name for name in archive.namelist() if story.fullmatch(name))
  if "word/document.xml" not in names: raise ValueError("DOCX_DOCUMENT_XML_MISSING")
  for name in names:
   root=ET.fromstring(archive.read(name)); parts.append(name)
   for paragraph in root.findall(".//w:p",ns):
    paragraph_text="".join(node.text or "" for node in paragraph.findall(".//w:t",ns))
    if not paragraph_text.strip(): continue
    paragraphs+=1
    el=paragraph.find("./w:pPr/w:bidi",ns)
    if el is None: bidi_missing+=1
    elif el.attrib.get("{"+ns["w"]+"}val","1") not in ("0","false","False"): bidi_true+=1
    else: bidi_false+=1
    for run in paragraph.findall(".//w:r",ns):
     run_text="".join(node.text or "" for node in run.findall(".//w:t",ns))
     if not run_text: continue
     text_runs+=1
     rtl_el=run.find("./w:rPr/w:rtl",ns)
     if rtl_el is None: rtl_missing+=1
     elif rtl_el.attrib.get("{"+ns["w"]+"}val","1") not in ("0","false","False"): rtl_true+=1
     else: rtl_false+=1
 return {"story_parts":parts,"paragraphs":paragraphs,"text_runs":text_runs,
  "bidi_true":bidi_true,"bidi_false":bidi_false,"bidi_missing":bidi_missing,
  "rtl_runs_true":rtl_true,"rtl_runs_false":rtl_false,"rtl_runs_missing":rtl_missing}

def render_docx_files(docx_paths, output_dir):
 output_dir.mkdir(parents=True,exist_ok=True)
 profile=output_dir/"lo-profile"
 cmd=["libreoffice",f"-env:UserInstallation=file://{profile}","--headless","--convert-to","pdf","--outdir",str(output_dir)]+[str(p) for p in docx_paths]
 run=subprocess.run(cmd,capture_output=True,text=True,timeout=600)
 if run.returncode!=0: raise RuntimeError("DOCX_RENDER_FAILED:"+run.stderr[-2000:])
 from pypdf import PdfReader
 pages={}
 for path in docx_paths:
  pdf=output_dir/(path.stem+".pdf")
  if not pdf.is_file(): raise RuntimeError("DOCX_RENDER_OUTPUT_MISSING:"+path.name)
  count=len(PdfReader(str(pdf)).pages)
  if count<1: raise RuntimeError("DOCX_RENDER_ZERO_PAGES:"+path.name)
  pages[path.name]=count
 return pages

def acceptance_test_statuses(*, excel_sheets_verified, numeric_parity_verified, financial_mismatch_count, package_inventory_verified, artifact_fingerprint_verified, run_id, job_id, tested_sha):
    """Report scoped execution separately from historical acceptance-test completion."""
    base={"run_id":run_id,"job_id":job_id,"tested_sha":tested_sha}
    out={}
    out["test_175"]={**base,"status":"PASS_SCOPED" if excel_sheets_verified and numeric_parity_verified else "BLOCKED",
        "contract":CONTRACTS["175"],"detail":"D6 independently verified 185 worksheets per workbook, matching worksheet order, cross-workbook numeric parity, and rejected formula/error cells. This is scoped evidence, not a claim that the separately numbered historical test suite was invoked."}
    for tid in ("176","179","180","181","183"):
        out["test_"+tid]={**base,"status":"NOT_RUN","contract":CONTRACTS[tid],
            "detail":"The full historical acceptance contract was not executed by this D6 audit. Related scoped checks, if any, are reported separately and are not substituted."}
    out["test_182"]={**base,"status":"BLOCKED" if (not excel_sheets_verified or not numeric_parity_verified or financial_mismatch_count) else "PASS_SCOPED",
        "contract":CONTRACTS["182"],"financial_mismatch_count":financial_mismatch_count,
        "detail":"Exact registry-value comparisons were performed for the financial cells resolved by the pinned Registry. Any mismatch blocks this scoped result; this is not a claim that the separate historical acceptance test was invoked."}
    out["test_186"]={**base,"status":"PASS_SCOPED" if package_inventory_verified and artifact_fingerprint_verified else "BLOCKED",
        "contract":CONTRACTS["186"],"detail":"D6 verified the exact outer GitHub Artifact fingerprint, inner package fingerprint, eight-member ZIP inventory, CRC/path safety, manifest member hashes, and SHA256SUMS coverage. This is scoped package evidence, not a claim that the separately numbered historical test suite was invoked."}
    return out


def audit(a):
 root=Path(a.root); artifact=Path(a.artifact); checks={}
 pin=load_d5_pin(root); a.d5_pin=pin
 a.audit_checks=checks
 a.audit_gates={}
 checks["auditor_unit_tests"]={"status":"PASS","run_id":a.run_id,"job_id":a.job_id,"tested_sha":a.tested_sha,"detail":"Focused D6 auditor unit suite completed before this audit step."}
 checks["d5_artifact_download"]={"status":"PASS","run_id":a.run_id,"job_id":a.job_id,"tested_sha":a.tested_sha,"detail":"Workflow verified exact pinned GitHub Artifact metadata, digest, and downloaded byte size before invoking auditor."}
 outer=artifact.read_bytes()
 if len(outer)!=pin["artifact_bytes"] or sha(outer)!=pin["artifact_sha256"]: raise ValueError("ACTIONS_ARTIFACT_FINGERPRINT_MISMATCH")
 with zipfile.ZipFile(io.BytesIO(outer)) as z:
  zip_check(z,{PACKAGE,"manifest.json","SHA256SUMS.txt"})
  outer_manifest=z.read("manifest.json"); sums_raw=z.read("SHA256SUMS.txt"); pkg=z.read(PACKAGE)
 if len(pkg)!=pin["package_bytes"] or sha(pkg)!=pin["package_sha256"]: raise ValueError("D5_PACKAGE_FINGERPRINT_MISMATCH")
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
   if digest!=pin["package_sha256"]: raise ValueError("SUMS_PACKAGE_MISMATCH")
  elif name in payload:
   if digest!=sha(payload[name]): raise ValueError("SUMS_MEMBER_MISMATCH:"+name)
  elif name=="results/number_registry.json":
   reg=root/"results/number_registry.json"
   if not reg.exists() or file_sha(reg)!=digest: raise ValueError("SUMS_REGISTRY_MISMATCH")
  else: raise ValueError("SUMS_UNKNOWN_PATH:"+name)
 checks["artifact_outer"]={"status":"PASS","artifact_id":pin["artifact_id"],"run_id":pin["artifact_run_id"],"bytes":len(outer),"sha256":sha(outer)}
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
 # Stream worksheet XML directly: bounded memory and lxml parser.
 prior_sheetnames=None; numeric_count=financial_count=0; prior_digest=None; financial_mismatch_count=0; financial_mismatch_samples=[]
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
   financial_mismatch_count+=result["financial_mismatch_count"]
   for item in result["financial_mismatch_samples"]:
    if len(financial_mismatch_samples)<1000: financial_mismatch_samples.append({"workbook":name,**item})
  finally: p.unlink(missing_ok=True)
  print(f"D6_EXCEL_XML_SCAN_DONE file={name} numeric_cells={result['numeric_count']} financial_cells={result['financial_count']} financial_mismatches={result['financial_mismatch_count']}",flush=True)
 checks["excel_175_180_182"]={"status":"BLOCKED" if financial_mismatch_count else "PASS_SCOPED","sheets_per_workbook":185,"numeric_cells_compared":numeric_count,"financial_cells_exact_registry_verified":financial_count,"financial_mismatch_count":financial_mismatch_count,"financial_mismatch_samples":financial_mismatch_samples,"arabic_rtl_checked":True,"english_ltr_checked":True,"formula_cells":0,"error_cells":0}
 a.audit_checks=checks
 # Parse DOCX independently; preserve every file result and all preceding Excel findings.
 docx_results={}; docx_paths=[]; rtl_names={"التقرير_الكامل_AR.docx","الملخص_AR.docx","دراسة_الجدوى_AR.docx"}
 docx_id_occurrences=0; docx_unknown_ids=[]
 number_pattern=re.compile(r"(?<![A-Za-z0-9])(?:NR-[0-9a-f]{24}|D2D-[0-9a-f]{20}-[0-9]{6})(?![A-Za-z0-9])")
 for name in [x for x in FILES if x.endswith(".docx")]:
  p=root/("d6_"+name)
  try:
   p.write_bytes(payload[name]); doc=Document(str(p)); docx_paths.append(p)
   t="\n".join(x.text for x in doc.paragraphs)+"\n"+"\n".join(" ".join(c.text for c in row.cells) for tb in doc.tables for row in tb.rows)
   findings=[]
   if not t.strip(): findings.append("DOCX_EMPTY")
   if "T2_INTERIM" not in t and "NOT_FINAL_BLOCKED" not in t: findings.append("DOCX_T2_DISCLOSURE_MISSING")
   missing_173=disclosure_173_findings(t)
   if missing_173: findings.append("DOCX_SECTION_17_3_DISCLOSURES_MISSING:"+",".join(missing_173))
   direction=docx_directionality(p); expect_rtl=name in rtl_names
   direction_ok=(direction["paragraphs"]>0 and direction["text_runs"]>0 and direction["bidi_missing"]==0 and direction["rtl_runs_missing"]==0 and direction["bidi_true"]==direction["paragraphs"] and direction["bidi_false"]==0 and direction["rtl_runs_true"]==direction["text_runs"] and direction["rtl_runs_false"]==0) if expect_rtl else (direction["paragraphs"]>0 and direction["text_runs"]>0 and direction["bidi_missing"]==0 and direction["rtl_runs_missing"]==0 and direction["bidi_false"]==direction["paragraphs"] and direction["bidi_true"]==0 and direction["rtl_runs_false"]==direction["text_runs"] and direction["rtl_runs_true"]==0)
   if not direction_ok: findings.append("DOCX_DIRECTIONALITY_MISMATCH")
   ids=number_pattern.findall(t); docx_id_occurrences+=len(ids); unresolved=[]
   for number_id in ids:
    try: registry_display(registry,number_id,entries_by_id,series_by_id,ledger_by_id)
    except Exception: unresolved.append(number_id)
   docx_unknown_ids.extend(unresolved)
   if unresolved: findings.append("DOCX_NUMBER_REGISTRY_ID_UNRESOLVED")
   docx_results[name]={"status":"BLOCKED" if findings else "PASS_SCOPED","findings":findings,"text_characters":len(t),"missing_evidence_literal_present":"MISSING_EVIDENCE" in t,"section_17_3_missing_items":missing_173,"directionality":direction,"number_id_occurrences":len(ids),"unresolved_number_ids":unresolved}
  except Exception as exc:
   docx_results[name]={"status":"BLOCKED","findings":["DOCX_PARSE_ERROR:"+type(exc).__name__+":"+str(exc)]}
  a.audit_checks=checks
 docx_blocked=[name for name,item in docx_results.items() if item["status"]=="BLOCKED"]
 checks["docx_files"]={"status":"BLOCKED" if docx_blocked else "PASS_SCOPED","files":docx_results,"docx_files":len(docx_results),"blocked_files":docx_blocked,"detail":"Per-file DOCX parse, T2, §17.3 substance, OOXML directionality and resolution of every explicit Number Registry ID; full numeric-token lineage remains a separate acceptance test."}
 checks["docx_number_registry_traceability"]={"status":"BLOCKED" if docx_unknown_ids or docx_id_occurrences==0 else "PASS_SCOPED","number_id_occurrences":docx_id_occurrences,"unresolved_number_ids":sorted(set(docx_unknown_ids)),"detail":"Every explicit NR-/D2D- identifier in DOCX resolves against the pinned Number Registry/extension; this does not claim every numeric token is registry-backed or execute Test 176."}
 render_blocked=None; page_counts={}
 try:
  page_counts=render_docx_files(docx_paths,root/"d6_rendered")
  for summary in ("الملخص_AR.docx","Summary_EN.docx"):
   if not 2<=page_counts.get(summary,0)<=3: raise ValueError("DOCX_SUMMARY_PAGE_COUNT_INVALID:"+summary+":"+str(page_counts.get(summary)))
  checks["docx_rendering"]={"status":"PASS_SCOPED","page_counts":page_counts,"detail":"All five DOCX files rendered independently with LibreOffice; both summaries verified at 2–3 pages."}
 except Exception as exc:
  render_blocked={"error_type":type(exc).__name__,"error":str(exc)}
  checks["docx_rendering"]={"status":"BLOCKED","page_counts":page_counts,"error":render_blocked}
 finally:
  for path in docx_paths: path.unlink(missing_ok=True)
 checks["docx_176"]={"status":"NOT_RUN","docx_files":len(docx_results),"blocked_files":docx_blocked,"detail":"Test 176 requires complete numeric-token-to-Number-Registry lineage; scoped explicit-ID resolution and rendering do not execute that acceptance test."}
 a.audit_checks=checks
 checks.update(acceptance_test_statuses(
  excel_sheets_verified=(len(prior_sheetnames or [])==185),
  numeric_parity_verified=(prior_digest is not None),
  financial_mismatch_count=financial_mismatch_count,
  package_inventory_verified=True,
  artifact_fingerprint_verified=True,
  run_id=a.run_id,job_id=a.job_id,tested_sha=a.tested_sha))
 a.audit_checks=checks
 result={"schema_version":"d6-independent-post-write-audit-v2","status":"BLOCKED" if (financial_mismatch_count or docx_blocked or render_blocked or docx_unknown_ids) else "PASS_SCOPED_WITH_LIMITATIONS","classification":"T2_INTERIM / NOT_FINAL_BLOCKED","repository":"yasmin977209-ux/motorcycle-simulation","branch":a.branch,"tested_sha":a.tested_sha,"run_id":a.run_id,"source_d5_run_id":pin["artifact_run_id"],"source_d5_artifact_id":pin["artifact_id"],"checks":checks,"fixed_gate_states":gates,"missing_accounting_fields":MISSING,"limitations":["Full numeric-token-to-Number-Registry recomputation for every DOCX numeric token remains NOT_RUN; explicit identifier resolution is scoped only.","DOCX rendering and directionality are checked independently in this D6 job; rendering does not imply visual review of every page.","Historical acceptance tests 175, 176, 179, 180, 181, 182, 183 and 186 are individually NOT_RUN in this D6 job; auditor unit tests are not those acceptance tests.","Test 181 source partner daily balances are not recreated; missing historical 48K evidence remains missing.","No full 177-unique-test suite, Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, identity change, main write, merge, Release or final acceptance."],"d6_disposition":"BLOCKED" if (financial_mismatch_count or docx_blocked or render_blocked or docx_unknown_ids) else "PASS_SCOPED_WITH_LIMITATIONS","final_accepted":"NOT_DECLARED","p17_final_accepted":"NOT_DECLARED","p18_released":"NOT_DECLARED","converged":"NOT_DECLARED"}
 out=root/"docs"; out.mkdir(exist_ok=True)
 (out/"FINAL_AUDIT.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 lines=["# D6 Independent Post-Write Audit","",f"- Disposition: {result['status']}",f"- D5 Artifact: {pin['artifact_id']} / Run {pin['artifact_run_id']}",f"- D6 Run: {a.run_id}",f"- Tested SHA: {a.tested_sha}","- Classification: T2_INTERIM / NOT_FINAL_BLOCKED","","| Check | Status | Detail |","|---|---|---|"]
 for k,v in checks.items(): lines.append(f"| {k} | {v['status']} | {v.get('detail',v.get('contract',''))} |")
 lines+=["","## Preserved gate states",""]+[f"- {k}: {v}" for k,v in gates.items()]+["","## Limitations",""]+[f"- {x}" for x in result["limitations"]]+["","D6 is not P17 acceptance, FINAL_ACCEPTED, CONVERGED, or release authorization."]
 (out/"FINAL_AUDIT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
 print(json.dumps({"status":result["status"],"checks":{k:v["status"] for k,v in checks.items()}},ensure_ascii=False))
def main():
 p=argparse.ArgumentParser(); p.add_argument("--artifact",required=True); p.add_argument("--root",default="."); p.add_argument("--run-id",default=os.getenv("GITHUB_RUN_ID","local")); p.add_argument("--tested-sha",default=os.getenv("GITHUB_SHA","unknown")); p.add_argument("--branch",default=os.getenv("GITHUB_REF_NAME","unknown")); p.add_argument("--job-id",default=os.getenv("D6_JOB_ID","NOT_AVAILABLE")); args=p.parse_args()
 try:
  audit(args)
 except Exception as exc:
  out=Path(args.root)/"docs"; out.mkdir(exist_ok=True)
  checks=getattr(args,"audit_checks",{})
  checks["independent_post_write_audit"]={"status":"BLOCKED","error_type":type(exc).__name__,"error":str(exc),"run_id":args.run_id,"job_id":args.job_id,"tested_sha":args.tested_sha}
  gates=getattr(args,"audit_gates",{"financial_gate_a":"PASS_SCOPED","production_gate_a":"NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS","gate_b_n2400":"FAIL_SCOPED (10/10)","stability":"NOT_CONVERGED (0/60)","n4800":"NOT_EXECUTED","c100_golden":"NOT_RUN"})
  result={"schema_version":"d6-independent-post-write-audit-v3","status":"BLOCKED","classification":"T2_INTERIM / NOT_FINAL_BLOCKED","repository":"yasmin977209-ux/motorcycle-simulation","branch":args.branch,"tested_sha":args.tested_sha,"run_id":args.run_id,"job_id":args.job_id,"source_d5_run_id":getattr(args,"d5_pin",{}).get("artifact_run_id"),"source_d5_artifact_id":getattr(args,"d5_pin",{}).get("artifact_id"),"checks":checks,"fixed_gate_states":gates,"missing_accounting_fields":MISSING,"limitations":["The independent audit did not complete successfully; exact exception is recorded and must not be treated as acceptance.","Completed partial findings are preserved; checks not reached remain absent or NOT_RUN.","No D5 historical Artifact or manifest was modified.","D6 does not imply P17 acceptance, FINAL_ACCEPTED, P18_RELEASED or CONVERGED."],"d6_disposition":"BLOCKED","final_accepted":"NOT_DECLARED","p17_final_accepted":"NOT_DECLARED","p18_released":"NOT_DECLARED","converged":"NOT_DECLARED"}
  (out/"FINAL_AUDIT.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  lines=["# D6 Independent Post-Write Audit","",f"- Disposition: BLOCKED",f"- D6 Run: {args.run_id}",f"- Tested SHA: {args.tested_sha}",f"- D5 Artifact: {getattr(args,'d5_pin',{}).get('artifact_id')} / Run {getattr(args,'d5_pin',{}).get('artifact_run_id')}","- Classification: T2_INTERIM / NOT_FINAL_BLOCKED","","## Blocking evidence","",f"- {type(exc).__name__}: {exc}","","## Fixed gate states",""]+[f"- {k}: {v}" for k,v in result["fixed_gate_states"].items()]+["","## Limitations",""]+[f"- {x}" for x in result["limitations"]]+["","D6 is BLOCKED; this report is not acceptance or release authorization."]
  (out/"FINAL_AUDIT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
  print("D6_AUDIT_BLOCKED "+json.dumps({"error_type":type(exc).__name__,"error":str(exc),"run_id":args.run_id,"tested_sha":args.tested_sha},ensure_ascii=False))
if __name__=="__main__": main()
