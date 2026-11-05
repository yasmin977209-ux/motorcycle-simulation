"""D3-S1 partitioning and D3-S2 semantic reassembly for the pinned D3 workbooks."""
from __future__ import annotations
import argparse, copy, datetime, hashlib, json, re, sys, gc
from pathlib import Path
from openpyxl import Workbook, load_workbook
from openpyxl.cell.cell import MergedCell

COLLECTIONS=("C030","C050","C070","C085","C100")
RECOVERIES=("G000","G030","G050","G070","G100")
SCENARIO_RE=re.compile(r"^(C\d{3})_(G\d{3})(?:_|$)")
EXPECTED_SHEETS=185

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def normalize(v):
    if isinstance(v,(datetime.datetime,datetime.date,datetime.time)): return {"type":type(v).__name__,"value":v.isoformat()}
    if isinstance(v,bytes): return {"type":"bytes","value":v.hex()}
    if isinstance(v,(str,int,float,bool)) or v is None: return v
    return {"type":type(v).__name__,"value":str(v)}

def dim_record(d):
    return {"min":getattr(d,"min",None),"max":getattr(d,"max",None),"width":getattr(d,"width",None),
      "height":getattr(d,"height",None),"hidden":getattr(d,"hidden",None),"outlineLevel":getattr(d,"outlineLevel",None),
      "collapsed":getattr(d,"collapsed",None),"style":str(getattr(d,"style",None))}

def sheet_digest(ws):
    cells=[]
    for c in sorted(ws._cells.values(),key=lambda x:(x.row,x.column)):
        if isinstance(c,MergedCell): continue
        if c.value is None and not c.has_style and not c.hyperlink and not c.comment: continue
        cells.append([c.coordinate,c.data_type,normalize(c.value),str(c.font),str(c.fill),str(c.border),
          str(c.alignment),str(c.protection),c.number_format,
          c.hyperlink.target if c.hyperlink else None,
          c.hyperlink.location if c.hyperlink else None,
          c.comment.text if c.comment else None,c.comment.author if c.comment else None])
    payload={
      "title":ws.title,"state":ws.sheet_state,"rtl":bool(ws.sheet_view.rightToLeft),
      "freeze_panes":str(ws.freeze_panes) if ws.freeze_panes else None,
      "dimension":ws.calculate_dimension(),"max_row":ws.max_row,"max_column":ws.max_column,
      "merged":[str(x) for x in ws.merged_cells.ranges],
      "rows":{str(k):dim_record(v) for k,v in sorted(ws.row_dimensions.items())},
      "columns":{str(k):dim_record(v) for k,v in sorted(ws.column_dimensions.items())},
      "cells":cells,"auto_filter":str(ws.auto_filter),
      "data_validations":[str(x) for x in getattr(ws.data_validations,"dataValidation",[])],
      "conditional_formatting":[(str(k),[str(x) for x in v]) for k,v in getattr(ws.conditional_formatting,"_cf_rules",{}).items()],
      "page_setup":str(ws.page_setup),"page_margins":str(ws.page_margins),
      "print_options":str(ws.print_options),"sheet_format":str(ws.sheet_format),
      "sheet_properties":str(ws.sheet_properties),"protection":str(ws.protection),
      "print_area":str(ws.print_area),"print_title_rows":ws.print_title_rows,"print_title_cols":ws.print_title_cols,
      "tables":sorted(ws.tables.keys()),"charts":len(ws._charts),"images":len(ws._images)
    }
    raw=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":"),default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest(),{"nonempty_or_styled_cell_count":len(cells),
      "numeric_cell_count":sum(1 for c in ws._cells.values() if not isinstance(c,MergedCell) and isinstance(c.value,(int,float)) and not isinstance(c.value,bool)),
      "formula_cell_count":sum(1 for c in ws._cells.values() if not isinstance(c,MergedCell) and c.data_type=="f"),
      "error_cell_count":sum(1 for c in ws._cells.values() if not isinstance(c,MergedCell) and c.data_type=="e"),
      "hidden_state":ws.sheet_state,"rtl":bool(ws.sheet_view.rightToLeft),"dimension":ws.calculate_dimension()}

def copy_sheet(src,dst_wb):
    if src._charts or src._images or src.tables:
        raise RuntimeError(f"UNSUPPORTED_DRAWING_OR_TABLE:{src.title}:charts={len(src._charts)}:images={len(src._images)}:tables={len(src.tables)}")
    dst=dst_wb.create_sheet(src.title)
    dst.sheet_state=src.sheet_state
    dst.sheet_format=copy.copy(src.sheet_format)
    dst.sheet_properties=copy.copy(src.sheet_properties)
    dst.sheet_view=copy.copy(src.sheet_view)
    dst.page_margins=copy.copy(src.page_margins)
    dst.page_setup=copy.copy(src.page_setup)
    dst.print_options=copy.copy(src.print_options)
    dst.protection=copy.copy(src.protection)
    dst.auto_filter=copy.copy(src.auto_filter)
    dst.freeze_panes=src.freeze_panes
    dst.data_validations=copy.deepcopy(src.data_validations)
    dst.conditional_formatting=copy.deepcopy(src.conditional_formatting)
    for c in sorted(src._cells.values(),key=lambda x:(x.row,x.column)):
        if isinstance(c,MergedCell): continue
        if c.value is None and not c.has_style and not c.hyperlink and not c.comment: continue
        n=dst.cell(row=c.row,column=c.column,value=c.value)
        if c.has_style:
            n.font=copy.copy(c.font); n.fill=copy.copy(c.fill); n.border=copy.copy(c.border)
            n.alignment=copy.copy(c.alignment); n.number_format=c.number_format; n.protection=copy.copy(c.protection)
        if c.hyperlink: n._hyperlink=copy.copy(c.hyperlink)
        if c.comment: n.comment=copy.copy(c.comment)
    for merged in src.merged_cells.ranges: dst.merge_cells(str(merged))
    for k,v in src.row_dimensions.items():
        d=copy.copy(v); d.worksheet=dst; dst.row_dimensions[k]=d
    for k,v in src.column_dimensions.items():
        d=copy.copy(v); d.worksheet=dst; dst.column_dimensions[k]=d
    if src.print_area: dst.print_area=src.print_area
    if src.print_title_rows: dst.print_title_rows=src.print_title_rows
    if src.print_title_cols: dst.print_title_cols=src.print_title_cols
    return dst

def copy_wb_metadata(src,dst):
    dst.properties=copy.copy(src.properties)
    dst.security=copy.copy(src.security)
    if hasattr(src,"calculation") and hasattr(dst,"calculation"): dst.calculation=copy.copy(src.calculation)
    if hasattr(src,"views") and hasattr(dst,"views"): dst.views=copy.deepcopy(src.views)
    if hasattr(dst,"views") and dst.views: dst.views[0].activeTab=0
    if hasattr(src,"defined_names") and len(src.defined_names):
        raise RuntimeError("WORKBOOK_DEFINED_NAMES_REQUIRE_EXPLICIT_MAPPING")
    if getattr(src,"_external_links",[]): raise RuntimeError("WORKBOOK_EXTERNAL_LINKS_REQUIRE_EXPLICIT_MAPPING")

def classify(wb, expected_rtl, lang):
    names=list(wb.sheetnames)
    if len(names)!=EXPECTED_SHEETS: raise RuntimeError(f"SHEET_COUNT_MISMATCH:{lang}:{len(names)}")
    scenarios={}; shared=[]; details={}
    for index,name in enumerate(names):
        m=SCENARIO_RE.match(name)
        ws=wb[name]
        rtl=bool(ws.sheet_view.rightToLeft)
        if expected_rtl and not rtl: raise RuntimeError(f"RTL_NOT_SET:{lang}:{name}")
        if not expected_rtl and rtl: raise RuntimeError(f"LTR_NOT_SET:{lang}:{name}")
        if m:
            c,g=m.group(1),m.group(2)
            if c not in COLLECTIONS or g not in RECOVERIES: raise RuntimeError(f"UNEXPECTED_SCENARIO_SHEET:{name}")
            sid=f"{c}_{g}"
            scenarios.setdefault(sid,[]).append(name)
            details[name]={"source_index":index,"classification":"scenario_specific","scenario_id":sid,"collection":c,"recovery":g}
        else:
            shared.append(name)
            details[name]={"source_index":index,"classification":"shared_supporting","scenario_id":None,"collection":None,"recovery":None}
    expected={f"{c}_{g}" for c in COLLECTIONS for g in RECOVERIES}
    if set(scenarios)!=expected: raise RuntimeError("SCENARIO_SET_MISMATCH:"+repr(sorted(expected-set(scenarios))))
    if len(scenarios)!=25 or len(shared)!=10 or sum(map(len,scenarios.values()))!=175:
        raise RuntimeError(f"SHEET_CLASSIFICATION_COUNT_MISMATCH:scenario_sheets={sum(map(len,scenarios.values()))}:shared={len(shared)}")
    return names,scenarios,shared,details

def new_workbook_from(src_wb):
    out=Workbook()
    out.remove(out.active)
    copy_wb_metadata(src_wb,out)
    return out

def partition_one(source:Path, outdir:Path, lang:str, expected_rtl:bool):
    wb=load_workbook(source,data_only=False,read_only=False,keep_links=True)
    names,scenarios,shared,details=classify(wb,expected_rtl,lang)
    source_hashes={}; sheet_metrics={}
    for name in names:
        source_hashes[name],sheet_metrics[name]=sheet_digest(wb[name])
    part_files={}; shared_hashes={}
    for c in COLLECTIONS:
        selected=[n for n in names if (details[n]["classification"]=="shared_supporting" or details[n].get("collection")==c)]
        if len(selected)!=len(shared)+sum(len(v) for k,v in scenarios.items() if k.startswith(c+"_")):
            raise RuntimeError("PART_SHEET_SELECTION_MISMATCH:"+c)
        dest=new_workbook_from(wb)
        for n in selected: copy_sheet(wb[n],dest)
        if dest.sheetnames!=selected: raise RuntimeError("PART_SHEET_ORDER_MISMATCH:"+c)
        if len(dest.sheetnames)!=len(set(dest.sheetnames)): raise RuntimeError("PART_DUPLICATE_SHEET:"+c)
        out=outdir/f"{lang}_{c}.xlsx"; out.parent.mkdir(parents=True,exist_ok=True); dest.save(out); dest.close()
        check=load_workbook(out,data_only=False,read_only=False,keep_links=True)
        if check.sheetnames!=selected: raise RuntimeError("PART_READBACK_SHEET_LIST_MISMATCH:"+c)
        for n in selected:
            h,metrics=sheet_digest(check[n])
            if h!=source_hashes[n]: raise RuntimeError(f"PART_SEMANTIC_MISMATCH:{lang}:{c}:{n}")
            if n in shared:
                previous=shared_hashes.get(n)
                if previous and previous!=h: raise RuntimeError("SHARED_SHEET_CANONICAL_IDENTITY_MISMATCH:"+n)
                shared_hashes[n]=h
        check.close(); dest.close()
        part_files[c]={"filename":out.name,"bytes":out.stat().st_size,"sha256":sha256_file(out),
          "sheet_count":len(selected),"sheets":selected,
          "scenario_ids":[f"{c}_{g}" for g in RECOVERIES],"shared_sheet_count":len(shared),
          "git_permanent_eligible":out.stat().st_size<100*1024*1024,
          "preferred_git_target":"permanent_archive/v240_stage_d/d3_s/"+out.name}
        print(json.dumps({"event":"PART_WRITTEN","lang":lang,"collection":c,"bytes":out.stat().st_size,"sha256":part_files[c]["sha256"],"sheets":len(selected)},sort_keys=True),flush=True)
    # Logical + physical reassembly from the five independent part files.
    assembled=new_workbook_from(wb); added=set()
    for c in COLLECTIONS:
        part=load_workbook(outdir/part_files[c]["filename"],data_only=False,read_only=False,keep_links=True)
        for n in part.sheetnames:
            h,_=sheet_digest(part[n])
            if n in added:
                if n not in shared or h!=source_hashes[n]: raise RuntimeError("REASSEMBLY_DUPLICATE_NONSHARED_OR_MISMATCH:"+n)
                continue
            copy_sheet(part[n],assembled); added.add(n)
        part.close()
    if added!=set(names): raise RuntimeError("REASSEMBLY_SHEET_COVERAGE_MISMATCH")
    assembled._sheets=[assembled[n] for n in names]
    if assembled.sheetnames!=names: raise RuntimeError("REASSEMBLY_ORDER_MISMATCH")
    reassembly_dir=outdir/"reassembly_test"; reassembly_dir.mkdir(parents=True,exist_ok=True)
    p1=reassembly_dir/f"{lang}_reassembled_pass1.xlsx"; assembled.save(p1); assembled.close()
    rb1=load_workbook(p1,data_only=False,read_only=False,keep_links=True)
    pass1={}
    for n in names:
        h,_=sheet_digest(rb1[n]); pass1[n]=h
        if h!=source_hashes[n]: raise RuntimeError(f"REASSEMBLY_PASS1_SEMANTIC_MISMATCH:{lang}:{n}")
    p2=reassembly_dir/f"{lang}_reassembled_pass2.xlsx"; rb1.save(p2); rb1.close()
    rb2=load_workbook(p2,data_only=False,read_only=False,keep_links=True)
    pass2={}
    for n in names:
        h,_=sheet_digest(rb2[n]); pass2[n]=h
        if h!=source_hashes[n] or h!=pass1[n]: raise RuntimeError(f"REASSEMBLY_PASS2_DETERMINISM_MISMATCH:{lang}:{n}")
    rb2.close(); p1.unlink(missing_ok=True); p2.unlink(missing_ok=True); reassembly_dir.rmdir()
    wb.close(); gc.collect()
    return {"language":lang,"source":{"filename":source.name,"bytes":source.stat().st_size,"sha256":sha256_file(source),
      "sheet_count":len(names),"rtl":expected_rtl,"sheet_order":names},
      "partitions":part_files,"sheet_map":details,"shared_sheets":shared,
      "sheet_hashes":source_hashes,"sheet_metrics":sheet_metrics,
      "reassembly":{"status":"PASS_SCOPED_SEMANTIC_EQUIVALENCE","source_sheet_count":len(names),
        "reassembled_sheet_count":len(added),"pass1_matches":len(pass1),"pass2_matches":len(pass2),
        "deterministic_round_trips":2,"shared_sheet_canonical_hashes":shared_hashes}}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--english",required=True); p.add_argument("--arabic",required=True); p.add_argument("--outdir",required=True)
    a=p.parse_args(); out=Path(a.outdir); out.mkdir(parents=True,exist_ok=True)
    en=Path(a.english); ar=Path(a.arabic)
    if not en.is_file() or not ar.is_file(): raise SystemExit("SOURCE_WORKBOOK_MISSING")
    if en.resolve()==ar.resolve(): raise SystemExit("SOURCE_WORKBOOK_PATH_COLLISION")
    en_result=partition_one(en,out,"EN",False)
    ar_result=partition_one(ar,out,"AR",True)
    expected_files={f"{lang}_{c}.xlsx" for lang in ("EN","AR") for c in COLLECTIONS}
    actual_files={p.name for p in out.glob("*.xlsx")}
    if actual_files!=expected_files: raise SystemExit("TEN_PART_OUTPUT_INVENTORY_MISMATCH")
    manifest={"schema_version":"d3-s-partition-and-reassembly-v1","classification":"PASS_SCOPED",
      "partition_count":10,"languages":{"EN":en_result,"AR":ar_result},
      "scenario_matrix":{c:[f"{c}_{g}" for g in RECOVERIES] for c in COLLECTIONS},
      "limitations":["D3-S outputs are derived; original workbooks were not overwritten.",
        "Actions Artifact publication is temporary and does not satisfy permanent preservation.",
        "Git permanent archive and Dropbox placement/restore are separate required steps."]}
    mpath=out/"D3_S_PARTITION_MANIFEST.json"
    mpath.write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    report={"schema_version":"d3-s-reassembly-equivalence-v1","status":"PASS_SCOPED_SEMANTIC_EQUIVALENCE",
      "workbooks":{"EN":en_result["reassembly"],"AR":ar_result["reassembly"]},
      "sheet_count_per_source":185,"part_count":10,"round_trips_per_language":2}
    (out/"D3_S_REASSEMBLY_EQUIVALENCE.json").write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"D3_S_PARTITION_AND_REASSEMBLY_PASS_SCOPED","parts":10,
      "manifest":str(mpath),"manifest_bytes":mpath.stat().st_size,"manifest_sha256":sha256_file(mpath),
      "equivalence_report_bytes":(out/"D3_S_REASSEMBLY_EQUIVALENCE.json").stat().st_size},sort_keys=True),flush=True)

if __name__=="__main__": main()
