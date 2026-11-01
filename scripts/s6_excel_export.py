"""Stage D3 bilingual Excel candidate exporter. Numeric values are resolved only from D2 Number Registry."""
import argparse, hashlib, json, re, platform, zipfile
from datetime import date, timedelta, datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from pathlib import Path
from openpyxl import Workbook, load_workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import Font, PatternFill
from scripts.s6_number_registry import validate_registry, daily_number_id, _daily_resolution_indexes, _resolve_daily_number, METRICS, QUANTILES

GOVERNING="225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b"
GOVERNING_BYTES=401397
HISTORICAL="e5efaf0874384e8248c339ca10e248ea9e17e9f0882153b4ef88bc955b91d53f"
SCENARIO_RE=re.compile(r"^C([0-9]{3})_G([0-9]{3})$")
MODES=("ACTIVE_ONLY","ALL_TRIALS_CARRY_FORWARD")
DETAILS={"ASSETS":{"owned_bikes","held_assets"},"ACCTG":{"bad_debt","cumulative_project_profit","final_cash","final_net_project_equity","operating_net_profit","total_operating_revenue"},"PARTNER":{"partner1_final_entitlement","partner2_final_entitlement"},"GUARANTEE":{"claims_created","guarantee_recovered","recovery_rate_pct"},"CONTRACTS":{"termination_count","secondary_cycle_count"}}
GAPS={"DAILY":"Representative P50 daily raw ledger is not represented in Number Registry.","ASSETS":"Per-bike asset rows, purchase/delivery dates, gross cost and depreciation are not represented in Number Registry.","ACCTG":"Daily income statement and balance-sheet roll-forward fields are not represented in Number Registry.","PARTNER":"Daily Partner1/2_Reinvestment_Balance series are not represented in Number Registry.","GUARANTEE":"Per-claim source, amount, creation date and settlement outcome rows are not represented in Number Registry.","CONTRACTS":"Per-contract dates and status are not represented in Number Registry."}
ACCOUNTING_MISSING_FIELDS=("Accounts_Receivable","Accumulated_Depreciation","Gross_Bike_Assets","Guarantee_Claim_Receivable","Total_Assets")
H={"en":{"scenario":"Scenario","cohort":"Cohort","source":"Source","status":"Status","metric":"Metric","sample":"Checkpoint","value":"Value","id":"number_id","trial":"Trial key","roles":"Role assignments","date":"Date","mode":"Population mode","total":"Total trials","active":"Active trials","closed":"Closed trials","sample_count":"Sample trials","field":"Field","notes":"Notes","reason":"Reason","evidence":"Evidence status"},"ar":{"scenario":"السيناريو","cohort":"الفوج","source":"المصدر","status":"الحالة","metric":"المؤشر","sample":"نقطة الفحص","value":"القيمة","id":"number_id","trial":"مفتاح التكرار","roles":"الأدوار التمثيلية","date":"التاريخ","mode":"مجموعة السكان","total":"إجمالي التكرارات","active":"التكرارات النشطة","closed":"التكرارات المغلقة","sample_count":"حجم العينة","field":"الحقل","notes":"ملاحظات","reason":"السبب","evidence":"حالة الدليل"}}

def exact_value(n,d):
    if type(n) is not int or type(d) is not int or d<1: raise ValueError("EXACT_VALUE_INVALID")
    if n%d==0: return n//d
    with localcontext() as ctx:
        ctx.prec=60
        return (Decimal(n)/Decimal(d)).quantize(Decimal("0.01"),rounding=ROUND_HALF_EVEN)
def ev(e): return exact_value(e["numerator"],e["denominator"])

def safe_append(ws, values):
    cells=[]
    for value in values:
        cell=WriteOnlyCell(ws,value=value)
        if isinstance(value,str): cell.data_type="s"
        cells.append(cell)
    ws.append(cells)
def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()
def blob_sha(raw): return hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
def constants_from_reference(text):
    """Read identifier/value/description rows using the governing reference's Markdown table format."""
    active=False; rows=[]
    for line in text.splitlines():
        if line.startswith("# الباب الثاني") or line.startswith("## 2.1") or line.startswith("## 2.2"): active=True
        if active and (line.startswith("# الباب الثالث") or line.startswith("## 3.")): break
        if not active or not line.strip().startswith("|"): continue
        cells=[x.strip() for x in line.strip().strip("|").split("|")]
        if len(cells)<2 or all(re.fullmatch(r"[-: ]+",x or " ") for x in cells): continue
        identifier=cells[0].strip().strip("`").strip()
        if identifier in {"المعرّف","الثابت","#","مصدر المطالبة"}: continue
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*",identifier): continue
        normalized=[x.strip().strip("`").strip() for x in cells]
        rows.append((normalized+["",""])[:3])
    if not rows: raise ValueError("REFERENCE_CONSTANTS_NOT_FOUND")
    return rows
def scenarios(reg):
    ids={x["scenario_id"] for x in reg["entries"]}; ids.update(x["scenario_id"] for x in reg["daily_series"]); ids=sorted(ids)
    if len(ids)!=25 or any(not SCENARIO_RE.fullmatch(x) for x in ids): raise ValueError("SCENARIO_COVERAGE_INVALID")
    if len({SCENARIO_RE.fullmatch(x).group(1) for x in ids})!=5 or len({SCENARIO_RE.fullmatch(x).group(2) for x in ids})!=5: raise ValueError("SCENARIO_GRID_INVALID")
    return ids
def scenario_sheet_names(ids):
    names=[f"{sid}_{s}" for sid in ids for s in ("STATS","DAILY","ASSETS","ACCTG","PARTNER","GUARANTEE","CONTRACTS")]
    if len(names)!=175 or any(len(x)>31 or not x.isascii() for x in names): raise ValueError("SCENARIO_SHEET_NAMES_INVALID")
    return names
def header(ws,values):
    cells=[]
    for v in values:
        c=WriteOnlyCell(ws,value=v); c.font=Font(bold=True,color="FFFFFF"); c.fill=PatternFill(fill_type="solid",fgColor="17365D"); cells.append(c)
    ws.append(cells)
def new_sheet(wb,name,lang):
    ws=wb.create_sheet(name); ws.sheet_view.rightToLeft=(lang=="ar"); ws.sheet_view.showGridLines=False; ws.freeze_panes="A2"; return ws
def missing(ws,reason,lang):
    h=H[lang]; safe_append(ws,[h["status"],"MISSING_EVIDENCE",h["reason"],reason])
def write_missing_accounting_fields(ws,sid):
    for field in ACCOUNTING_MISSING_FIELDS:
        safe_append(ws,[sid,"MISSING_EVIDENCE","MISSING_EVIDENCE","",field,"MISSING_EVIDENCE","","MISSING_EVIDENCE","Historical field absent; not inferred or zero-filled."])
def max_rows(reg,sid):
    rows=[x for x in reg["entries"] if x.get("scenario_id")==sid and x.get("trial_id") is None]
    if not rows:return []
    n=max(x.get("sample_n",0) for x in rows)
    return sorted([x for x in rows if x.get("sample_n")==n],key=lambda x:x["metric_name"])
def cohort(reg,sid):
    if any(x["scenario_id"]==sid for x in reg["daily_series"]): return reg["scope"]["S6"]["cohort_id"],"S6"
    e=next((x for x in reg["entries"] if x.get("scenario_id")==sid and x.get("trial_id") is not None),None)
    return (e.get("cohort_id"),"C100_CROSS_COHORT_DETERMINISTIC_REUSE") if e else ("MISSING_EVIDENCE","MISSING_EVIDENCE")

def write_daily(ws,reg,ids,lang):
    h=H[lang]; cols=[h["scenario"],h["date"],h["mode"],h["total"],"total_trials_source_number_id",h["active"],"active_trial_count_source_number_id",h["closed"],"closed_trial_count_source_number_id",h["sample_count"],"sample_trial_count_source_number_id"]
    for m in METRICS:
        for q in QUANTILES: cols.extend([m+"_"+q,m+"_"+q+"_number_id"])
    header(ws,cols)
    smap={(x["scenario_id"],x["mode"],x["metric_name"],x["quantile_name"]):x for x in reg["daily_series"]}
    series_by_id,indexes=_daily_resolution_indexes(reg); indexes={x["scenario_id"]:x for x in reg["daily_date_indexes"]}
    for sid in ids:
        if sid not in indexes:
            safe_append(ws,[sid,"MISSING_EVIDENCE","MISSING_EVIDENCE"]+["MISSING_EVIDENCE"]*(len(cols)-3)); continue
        idx=indexes[sid]; first=date.fromisoformat(idx["first_date"])
        for mode in MODES:
            local={(m,q):smap[(sid,mode,m,q)] for m in METRICS for q in QUANTILES}; count_series=local[("Cash","P50")]
            for offset in range(idx["date_count"]):
                nid=daily_number_id(count_series["series_id"],offset); rr=_resolve_daily_number(reg,nid,series_by_id,indexes)
                active,total,sample=rr["active_trial_count"],rr["N_total"],rr["sample_trial_count"]
                row=[sid,first+timedelta(days=offset),mode,total,nid,active,nid,total-active,nid,sample,nid]
                for m in METRICS:
                    for q in QUANTILES:
                        s=local[(m,q)]; n,d=s["values"][offset]; row.extend([exact_value(n,d),daily_number_id(s["series_id"],offset)])
                safe_append(ws,row)

def write_globals(wb,reg,ids,lang,constants,source_head,run_id,regsha):
    h=H[lang]
    ws=new_sheet(wb,"README",lang); header(ws,[h["field"],h["value"]])
    for row in [
      ["Project","Motorcycle Rental Simulation"],["Classification","T2_INTERIM / NOT_FINAL_BLOCKED"],["D3 gate","BLOCKED_MISSING_EVIDENCE"],
      ["Generation date UTC",datetime.now(timezone.utc).date().isoformat()],["Governing decision",reg["governing_decision_id"]],
      ["Current governing reference SHA-256",reg["current_governing_reference_sha256"]],["Historical execution reference SHA-256",reg["historical_execution_reference_sha256"]],
      ["Number Registry SHA-256",regsha],["Source commit",source_head],["Workflow run",str(run_id)],["MASTER_SEED",str(reg["scope"]["S6"]["master_seed"])],
      ["Scenario coverage","25 scenarios: 20 S6 + 5 C100 reuse"],["Full Logging","105 representative keys only; not 48,000 trials"],
      ["C100","CROSS_COHORT_DETERMINISTIC_REUSE; Golden revalidation NOT_RUN"],["Financial Gate A","PASS_SCOPED only"],
      ["Production Gate A","NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS"],["Gate B N=2400","FAIL_SCOPED (10/10)"],
      ["Stability","NOT_CONVERGED (0/60)"],["N=4800","NOT_EXECUTED"],["Important","Missing evidence is not zero and is not estimated."]
    ]: safe_append(ws,row)
    ws=new_sheet(wb,"CONSTANTS",lang); header(ws,[h["field"],h["value"],h["notes"]])
    for row in constants: safe_append(ws,row)
    metrics=sorted({x["metric_name"] for x in reg["entries"] if x.get("trial_id") is None})
    ws=new_sheet(wb,"SCENARIO_MATRIX",lang)
    cols=[h["scenario"],h["cohort"],h["source"],h["status"],"N_total","N_total_source_number_id","N_unique_paths","N_unique_paths_source_number_id",h["notes"]]
    for m in metrics: cols.extend([m,m+"_number_id"])
    header(ws,cols)
    series_by_id,indexes=_daily_resolution_indexes(reg); indexes={x["scenario_id"]:x for x in reg["daily_date_indexes"]}
    for sid in ids:
        co,src=cohort(reg,sid); rows=max_rows(reg,sid); by={x["metric_name"]:x for x in rows}; first=next((x for x in reg["daily_series"] if x["scenario_id"]==sid),None)
        nt=nti=nu=nui="MISSING_EVIDENCE"
        if first:
            nid=daily_number_id(first["series_id"],0); rr=_resolve_daily_number(reg,nid,series_by_id,indexes)
            nt,nti=rr["N_total"],nid; nu,nui=rr["N_unique_paths"],nid; status="NOT_CONVERGED (0/60)"
        else:
            rep=next((x for x in reg["entries"] if x.get("scenario_id")==sid and x.get("trial_id") is not None),None)
            if rep: nt,nti=rep.get("N_total","MISSING_EVIDENCE"),rep["number_id"]; nu,nui=rep.get("N_unique_paths","MISSING_EVIDENCE"),rep["number_id"]
            status="C100_GOLDEN_REVALIDATION_NOT_RUN"
        row=[sid,co,src,status,nt,nti,nu,nui,"Available checkpoint values only; not convergence or final acceptance."]
        for m in metrics:
            e=by.get(m); row.extend([ev(e),e["number_id"]] if e else ["MISSING_EVIDENCE",""])
        safe_append(ws,row)
    ws=new_sheet(wb,"HEATMAP",lang); header(ws,[h["metric"],"C-level","G-level values; each numeric value followed by number_id"])
    cs=sorted({SCENARIO_RE.fullmatch(x).group(1) for x in ids}); gs=sorted({SCENARIO_RE.fullmatch(x).group(2) for x in ids})
    for metric in metrics:
        safe_append(ws,["METRIC",metric,"5×5 registry-backed grid"])
        for c in cs:
            row=[metric,"C"+c]
            for g in gs:
                e=next((x for x in max_rows(reg,f"C{c}_G{g}") if x["metric_name"]==metric),None)
                row.extend([ev(e),e["number_id"]] if e else ["MISSING_EVIDENCE",""])
            safe_append(ws,row)
    ws=new_sheet(wb,"SENSITIVITY",lang); header(ws,["Dimension","Held fixed","From","To","Derived delta","Source number_ids","Status"])
    safe_append(ws,["ALL","ALL","MISSING_EVIDENCE","MISSING_EVIDENCE","MISSING_EVIDENCE","","No registered mean-profit metric was promoted to a sensitivity result."])
    ws=new_sheet(wb,"VALIDATION_SUMMARY",lang); header(ws,[h["field"],h["status"],h["notes"]])
    for row in [["D0","PASS_SCOPED_WITH_LIMITATIONS","Input identity and archive integrity scope only."],["D1","PASS_SCOPED_WITH_LIMITATIONS","Approved v2.4.0 publication and exact-head evidence."],["D2","PASS_SCOPED_WITH_LIMITATIONS","Number Registry exact-head readback; 34 focused tests passed."],["D3 structure","PENDING_POST_WRITE_VALIDATION","See D3 build audit."],["D3 bilingual parity","PENDING_POST_WRITE_VALIDATION","See D3 build audit."],["Full model acceptance suite","NOT_EXECUTED_HERE","Do not infer 177 unique tests passed."],["Final acceptance","NOT_DECLARED","D3 candidate is interim and blocked."]]: safe_append(ws,row)
    ws=new_sheet(wb,"ERROR_LOG",lang); header(ws,[h["field"],h["status"],h["reason"],h["notes"]])
    for x in reg.get("unavailable_evidence",[]): safe_append(ws,[x.get("metric_name"),x.get("evidence_status"),x.get("reason"),"No inference or zero-fill."])
    for key,reason in GAPS.items(): safe_append(ws,[key,"MISSING_EVIDENCE",reason,"Sheet is intentionally not represented as complete."])
    safe_append(ws,["C100 daily distribution","MISSING_EVIDENCE","No C100 daily series in Number Registry.","Golden revalidation NOT_RUN."])
    safe_append(ws,["Full Logging","NOT_VERIFIED_105_OF_105","105 representative keys only.","Not 48,000 trials."])
    ws=new_sheet(wb,"FINAL_CLOSURE_SUMMARY",lang); header(ws,[h["scenario"],h["status"],"final_close_date",h["reason"]])
    for sid in ids: safe_append(ws,[sid,"MISSING_EVIDENCE","MISSING_EVIDENCE","Full close-date distribution absent from Number Registry."])
    ws=new_sheet(wb,"DAILY_DISTRIBUTION",lang); write_daily(ws,reg,ids,lang)
    ws=new_sheet(wb,"REPRESENTATIVE_CASES",lang); header(ws,[h["scenario"],h["cohort"],h["trial"],h["roles"],h["metric"],h["value"],h["id"],h["source"],h["evidence"]])
    reps=[x for x in reg["entries"] if x.get("trial_id") is not None]
    for e in sorted(reps,key=lambda x:(x["scenario_id"],x["trial_id"],x["metric_name"])):
        safe_append(ws,[e["scenario_id"],e["cohort_id"],"trial_id="+str(e["trial_id"]),", ".join(e.get("role_assignments",[])),e["metric_name"],ev(e),e["number_id"],e.get("source_member"),e.get("evidence_status")])

def build_one(reg,constants,ids,lang,path,source_head,run_id,regsha):
    wb=Workbook(write_only=True); write_globals(wb,reg,ids,lang,constants,source_head,run_id,regsha)
    for sid in ids:
        for suffix in ("STATS","DAILY","ASSETS","ACCTG","PARTNER","GUARANTEE","CONTRACTS"):
            ws=new_sheet(wb,f"{sid}_{suffix}",lang); h=H[lang]
            if suffix=="STATS":
                header(ws,[h["scenario"],h["cohort"],h["metric"],h["sample"],h["value"],h["id"],h["evidence"]])
                rows=[x for x in reg["entries"] if x.get("scenario_id")==sid and x.get("trial_id") is None]
                for e in sorted(rows,key=lambda x:(x.get("sample_n",0),x["metric_name"])):
                    safe_append(ws,[sid,e.get("cohort_id"),e["metric_name"],"N="+str(e["sample_n"]),ev(e),e["number_id"],e["evidence_status"]])
                if not rows: missing(ws,"No aggregate statistical checkpoint entries in Number Registry.",lang)
            elif suffix=="DAILY":
                header(ws,[h["scenario"],h["status"],h["reason"]]); safe_append(ws,[sid,"MISSING_EVIDENCE",GAPS["DAILY"]])
            else:
                header(ws,[h["scenario"],h["cohort"],h["trial"],h["roles"],h["metric"],h["value"],h["id"],h["evidence"],h["notes"]])
                rows=[x for x in reg["entries"] if x.get("scenario_id")==sid and x.get("trial_id") is not None and x["metric_name"] in DETAILS[suffix]]
                for e in sorted(rows,key=lambda x:(x["trial_id"],x["metric_name"])):
                    safe_append(ws,[sid,e["cohort_id"],"trial_id="+str(e["trial_id"]),", ".join(e.get("role_assignments",[])),e["metric_name"],ev(e),e["number_id"],e["evidence_status"],"Summary metric only; detailed ledger missing."])
                safe_append(ws,[sid,"MISSING_EVIDENCE","MISSING_EVIDENCE","",suffix+"_DETAIL_LEDGER","MISSING_EVIDENCE","","MISSING_EVIDENCE",GAPS[suffix]])
                if suffix=="ACCTG": write_missing_accounting_fields(ws,sid)
    path.parent.mkdir(parents=True,exist_ok=True); wb.save(path)

def audit(path,expected,expected_rtl=None):
    wb=load_workbook(path,read_only=True,data_only=False)
    try:
        if wb.sheetnames!=expected: raise ValueError("WORKSHEET_NAMES_OR_ORDER_MISMATCH")
        formula_cells=[]; excel_error_cells=[]; direction_mismatches=[]; numeric=0
        for ws in wb.worksheets:
            for row in ws.iter_rows():
                for c in row:
                    if c.data_type=="f":
                        formula_cells.append({"sheet":ws.title,"cell":c.coordinate,"classification":"FORMULA_CELL","formula":str(c.value)})
                    elif c.data_type=="e":
                        excel_error_cells.append({"sheet":ws.title,"cell":c.coordinate,"classification":"EXCEL_ERROR_CELL","error_type":str(c.value)})
                    if isinstance(c.value,(int,float,Decimal)) and not isinstance(c.value,bool): numeric+=1
        if expected_rtl is not None:
            with zipfile.ZipFile(path,"r") as archive:
                for index,name in enumerate(expected,1):
                    sheet_xml=archive.read(f"xl/worksheets/sheet{index}.xml")
                    view=re.search(rb"<sheetView\b([^>]*)>",sheet_xml)
                    rtl=bool(view and b'rightToLeft="1"' in view.group(1))
                    if rtl!=expected_rtl:
                        direction_mismatches.append({"sheet":name,"expected":"RTL" if expected_rtl else "LTR","actual":"RTL" if rtl else "LTR"})
        return {"sheet_count":len(wb.sheetnames),"formula_cell_count":len(formula_cells),"formula_cells":formula_cells,
            "excel_error_cell_count":len(excel_error_cells),"excel_error_cells":excel_error_cells,
            "excel_safety_status":"PASS" if not formula_cells and not excel_error_cells else "FAIL",
            "sheet_direction_status":"NOT_CHECKED" if expected_rtl is None else ("PASS" if not direction_mismatches else "FAIL"),
            "sheet_direction_mismatches":direction_mismatches,
            "numeric_cells":numeric,"bytes":path.stat().st_size,"sha256":sha(path)}
    finally: wb.close()
def compare(ar,en,names):
    a=load_workbook(ar,read_only=True,data_only=False); b=load_workbook(en,read_only=True,data_only=False); n=0
    try:
        if a.sheetnames!=b.sheetnames or a.sheetnames!=names: raise ValueError("BILINGUAL_SHEET_ORDER_MISMATCH")
        for name in names:
            for ra,rb in zip(a[name].iter_rows(),b[name].iter_rows()):
                for x,y in zip(ra,rb):
                    nx=isinstance(x.value,(int,float,Decimal)) and not isinstance(x.value,bool); ny=isinstance(y.value,(int,float,Decimal)) and not isinstance(y.value,bool)
                    if nx or ny:
                        n+=1
                        if not (nx and ny and x.value==y.value): raise ValueError("BILINGUAL_NUMERIC_MISMATCH:"+name+":"+x.coordinate)
        return {"numeric_comparisons":n,"numeric_mismatches":0}
    finally: a.close(); b.close()
def trace_ids(paths):
    n=0
    for path in paths:
        wb=load_workbook(path,read_only=True,data_only=False)
        try:
            for ws in wb.worksheets:
                if ws.title in {"README","CONSTANTS","VALIDATION_SUMMARY","ERROR_LOG","FINAL_CLOSURE_SUMMARY"}: continue
                for row in ws.iter_rows():
                    for i,c in enumerate(row):
                        if isinstance(c.value,(int,float,Decimal)) and not isinstance(c.value,bool):
                            nxt=row[i+1].value if i+1<len(row) else None
                            if not isinstance(nxt,str) or not ("NR-" in nxt or "D2D-" in nxt): raise ValueError("UNTRACED_NUMERIC_CELL:"+ws.title+":"+c.coordinate)
                            n+=1
        finally: wb.close()
    return {"numeric_cells_checked":n,"untraced_numeric_cells":0}

def build(args):
    raw=Path(args.registry).read_bytes(); regsha=hashlib.sha256(raw).hexdigest()
    if len(raw)!=24137036 or regsha!="743ffcced8de09a766870f201c352aabcf5789c43c84bfeae654a939700e4f87": raise ValueError("REGISTRY_PIN_MISMATCH")
    reg=json.loads(raw.decode("utf-8"),parse_float=Decimal); validation=validate_registry(reg)
    if reg["current_governing_reference_sha256"]!=GOVERNING or reg["historical_execution_reference_sha256"]!=HISTORICAL: raise ValueError("REFERENCE_IDENTITY_MISMATCH")
    reference_raw=Path(args.reference).read_bytes(); reference_sha=hashlib.sha256(reference_raw).hexdigest()
    if len(reference_raw)!=GOVERNING_BYTES or reference_sha!=GOVERNING: raise ValueError("GOVERNING_REFERENCE_PIN_MISMATCH")
    constants=constants_from_reference(reference_raw.decode("utf-8")); ids=scenarios(reg)
    names=["README","CONSTANTS","SCENARIO_MATRIX","HEATMAP","SENSITIVITY","VALIDATION_SUMMARY","ERROR_LOG","FINAL_CLOSURE_SUMMARY","DAILY_DISTRIBUTION","REPRESENTATIVE_CASES"]+scenario_sheet_names(ids)
    out=Path(args.output_dir); ar=out/"النتائج_الكاملة_AR.xlsx"; en=out/"Full_Results_EN.xlsx"
    build_one(reg,constants,ids,"ar",ar,args.source_head,args.run_id,regsha); build_one(reg,constants,ids,"en",en,args.source_head,args.run_id,regsha)
    aa=audit(ar,names,expected_rtl=True); ee=audit(en,names,expected_rtl=False); parity=compare(ar,en,names); trace=trace_ids([ar,en])
    missing_list=["C100 daily distributions absent from Number Registry.","Representative P50 raw daily ledgers absent from Number Registry.","Detailed ASSETS, ACCTG, PARTNER, GUARANTEE and CONTRACTS ledgers absent from Number Registry.","Final closure-date distribution absent from Number Registry.","Historical accounting fields remain MISSING_EVIDENCE and must not be inferred or zero-filled: "+", ".join(ACCOUNTING_MISSING_FIELDS)+".","Full Logging normalized statuses remain NOT_VERIFIED_105_OF_105.","C100 Golden revalidation remains NOT_RUN."]
    reference_info={"path":"Gist reference_v240.md","bytes":len(reference_raw),"sha256":reference_sha,"git_blob_sha1":blob_sha(reference_raw),"containing_commit":"384c27810e76572e77e79e9829c5f92c1c4165d7","url":"https://gist.githubusercontent.com/yasmin977209-ux/c3e5362f5928da22ee079fc94817224e/raw/384c27810e76572e77e79e9829c5f92c1c4165d7/reference_v240.md"}
    result={"d3_candidate_status":"T2_INTERIM / NOT_FINAL_BLOCKED","d3_gate_status":"BLOCKED_MISSING_EVIDENCE","source_head":args.source_head,"workflow_run_id":str(args.run_id),
      "current_governing_reference":reference_info,"historical_execution_reference_sha256":HISTORICAL,
      "registry":{"bytes":len(raw),"sha256":regsha,"git_blob_sha1":blob_sha(raw),**validation},"scenario_count":len(ids),"worksheet_count_per_workbook":len(names),
      "arabic_workbook":aa,"english_workbook":ee,"bilingual_numeric_parity":parity,"number_id_traceability":trace,"missing_evidence":missing_list,"gate_statuses_preserved":reg["gate_statuses"],"no_trials_or_simulation_executed":True}
    out.mkdir(parents=True,exist_ok=True)
    (out/"D3_BUILD_AUDIT.json").write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    safety_violations={"arabic":{"formula_cell_count":aa["formula_cell_count"],"formula_cells":aa["formula_cells"],"excel_error_cell_count":aa["excel_error_cell_count"],"excel_error_cells":aa["excel_error_cells"],"sheet_direction_mismatches":aa["sheet_direction_mismatches"]},
      "english":{"formula_cell_count":ee["formula_cell_count"],"formula_cells":ee["formula_cells"],"excel_error_cell_count":ee["excel_error_cell_count"],"excel_error_cells":ee["excel_error_cells"],"sheet_direction_mismatches":ee["sheet_direction_mismatches"]}}
    if any(v["formula_cell_count"] or v["excel_error_cell_count"] or v["sheet_direction_mismatches"] for v in safety_violations.values()):
        raise ValueError("EXCEL_SAFETY_VIOLATIONS:"+json.dumps(safety_violations,ensure_ascii=False,sort_keys=True))
    manifest={"classification":result["d3_candidate_status"],"d3_gate_status":result["d3_gate_status"],"source_head":args.source_head,"workflow_run_id":str(args.run_id),"current_governing_reference":reference_info,"historical_execution_reference_sha256":HISTORICAL,"registry_sha256":regsha,
      "master_seed":reg["scope"]["S6"]["master_seed"],"files":{ar.name:{"bytes":aa["bytes"],"sha256":aa["sha256"]},en.name:{"bytes":ee["bytes"],"sha256":ee["sha256"]}},
      "numeric_comparisons":parity["numeric_comparisons"],"number_id_traceability":trace,"missing_evidence":missing_list,"python_version":platform.python_version(),"openpyxl_version":__import__("openpyxl").__version__}
    (out/"D3_MANIFEST.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    report=["# D3 Excel Deliverables — Scoped Candidate Report","","- Candidate: "+result["d3_candidate_status"],f"- D3 gate: {result['d3_gate_status']}",f"- Source HEAD: {args.source_head}",f"- Workflow run: {args.run_id}",f"- Governing reference: {reference_info['url']}",f"- Governing reference SHA-256: {reference_sha}; bytes: {len(reference_raw)}; blob: {reference_info['git_blob_sha1']}; Gist commit: {reference_info['containing_commit']}",f"- Registry SHA-256: {regsha}",f"- Sheets per workbook: {len(names)}",f"- Arabic RTL / English LTR: {aa['sheet_direction_status']} / {ee['sheet_direction_status']}",f"- Excel formulas/errors: AR {aa['formula_cell_count']}/{aa['excel_error_cell_count']}; EN {ee['formula_cell_count']}/{ee['excel_error_cell_count']}",f"- Daily points validated: {validation['daily_points_resolved']}",f"- Bilingual numeric comparisons: {parity['numeric_comparisons']}; mismatches: 0",f"- Number-ID traced numeric cells: {trace['numeric_cells_checked']}; untraced: 0","","## Missing evidence",*[f"- {x}" for x in missing_list],"","These workbooks are interim evidence views, not full D3 acceptance or final project acceptance. D3 remains blocked; D4 must not start."]
    Path("docs/stage_d/D3_BUILD_REPORT_2026-11-01.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
def main():
    p=argparse.ArgumentParser(); s=p.add_subparsers(dest="cmd",required=True); b=s.add_parser("build")
    b.add_argument("--registry",required=True); b.add_argument("--reference",required=True); b.add_argument("--output-dir",default="deliverables"); b.add_argument("--source-head",required=True); b.add_argument("--run-id",required=True)
    a=p.parse_args()
    if a.cmd=="build": build(a)
if __name__=="__main__": main()
