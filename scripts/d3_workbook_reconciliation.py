#!/usr/bin/env python3
"""Compare committed small workbooks with pinned D3/D5 workbook packages."""
from __future__ import annotations
import argparse, hashlib, json, pathlib, zipfile, xml.etree.ElementTree as ET
from openpyxl import load_workbook

MAIN="{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL="{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PKG="{http://schemas.openxmlformats.org/package/2006/relationships}"

def inspect_xlsx(path):
    path=pathlib.Path(path)
    raw_hash=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): raw_hash.update(b)
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        if len(names)!=len(set(names)): raise RuntimeError("XLSX_DUPLICATE_ZIP_MEMBERS:"+path.name)
        bad=z.testzip()
        if bad: raise RuntimeError("XLSX_ZIP_CRC_FAILURE:"+path.name+":"+bad)
        wb=ET.fromstring(z.read("xl/workbook.xml"))
        rels=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        relmap={r.get("Id"):r for r in rels.findall(PKG+"Relationship")}
        sheets=[]
        for s in wb.find(MAIN+"sheets"):
            rid=s.get(REL+"id")
            if rid not in relmap: raise RuntimeError("XLSX_SHEET_REL_MISSING:"+s.get("name",""))
            target=relmap[rid].get("Target")
            part=(target.lstrip("/") if target.startswith("/") else "xl/"+target)
            if part not in names: raise RuntimeError("XLSX_SHEET_XML_MISSING:"+part)
            with z.open(part) as stream:
                rows=cells=formulas=errors=numeric=0
                dimension=None
                for event,el in ET.iterparse(stream,events=("start","end")):
                    if event=="start" and el.tag==MAIN+"worksheet":
                        d=el.find(MAIN+"dimension")
                        if d is not None: dimension=d.get("ref")
                    if event=="end":
                        if el.tag==MAIN+"row": rows+=1
                        elif el.tag==MAIN+"c":
                            cells+=1
                            if el.find(MAIN+"f") is not None: formulas+=1
                            if el.get("t")=="e": errors+=1
                            elif el.get("t") not in ("s","inlineStr","str","b") and el.find(MAIN+"v") is not None: numeric+=1
                            el.clear()
                sheets.append({"name":s.get("name"),"part":part,"rows":rows,"cells":cells,"formulas":formulas,"errors":errors,"numeric_cells":numeric,"dimension":dimension})
    book=load_workbook(path,read_only=True,data_only=False,keep_links=True)
    openpyxl_names=list(book.sheetnames); book.close()
    expected=[s["name"] for s in sheets]
    if openpyxl_names!=expected: raise RuntimeError("OPENPYXL_SHEET_ORDER_MISMATCH:"+path.name)
    return {"filename":path.name,"bytes":path.stat().st_size,"sha256":raw_hash.hexdigest(),"zip_crc":"PASS","openpyxl_open":"PASS","sheet_count":len(sheets),"row_count_total":sum(s["rows"] for s in sheets),"cell_count_total":sum(s["cells"] for s in sheets),"formula_count_total":sum(s["formulas"] for s in sheets),"error_cell_count_total":sum(s["errors"] for s in sheets),"sheets":sheets}

def compare(a,b):
    am={x["name"]:x for x in a["sheets"]}; bm={x["name"]:x for x in b["sheets"]}
    changes=[]
    for name in sorted(set(am)|set(bm)):
        x,y=am.get(name),bm.get(name)
        if x is None or y is None:
            changes.append({"sheet":name,"change":"MISSING_IN_LEFT" if x is None else "MISSING_IN_RIGHT"})
        else:
            fields=("rows","cells","formulas","errors","numeric_cells","dimension")
            delta={k:{"left":x[k],"right":y[k]} for k in fields if x[k]!=y[k]}
            if delta: changes.append({"sheet":name,"change":"COUNTS_OR_DIMENSION_DIFFER","details":delta})
    return {"left":a["filename"],"right":b["filename"],"same_raw_sha256":a["sha256"]==b["sha256"],"same_sheet_count":a["sheet_count"]==b["sheet_count"],"sheet_differences":changes,"different_sheet_count":len(changes)}

def main():
    p=argparse.ArgumentParser()
    for x in ("git_en","git_ar","d3_en","d3_ar","d5_en","d5_ar"): p.add_argument("--"+x,required=True)
    p.add_argument("--d3-artifact-id",type=int,required=True); p.add_argument("--d5-artifact-id",type=int,required=True)
    p.add_argument("--output",default="reconciliation-output")
    a=p.parse_args()
    sources={k:inspect_xlsx(getattr(a,k)) for k in ("git_en","git_ar","d3_en","d3_ar","d5_en","d5_ar")}
    comparisons={
      "EN_git_vs_D3":compare(sources["git_en"],sources["d3_en"]),
      "AR_git_vs_D3":compare(sources["git_ar"],sources["d3_ar"]),
      "EN_D3_vs_D5":compare(sources["d3_en"],sources["d5_en"]),
      "AR_D3_vs_D5":compare(sources["d3_ar"],sources["d5_ar"])
    }
    record=json.loads(pathlib.Path("docs/stage_d/D3_18_INVOCATION_RECONCILIATION_2026-11-05.json").read_text(encoding="utf-8"))
    d3_18={"test_id":"D3-18","classification":record.get("gate",{}).get("d3_18),
      "run_id":record.get("acceptance",{}).get("workflow_run_id"),"job_id":record.get("acceptance",{}).get("job_id"),
      "tested_sha":record.get("acceptance",{}).get("workflow_head_sha"),"artifact_id":record.get("acceptance",{}).get("artifact_id")}
    if d3_18["classification"]!="PASS_SCOPED" or not d3_18["run_id"] or not d3_18["job_id"]: raise SystemExit("D3_18_PRIOR_INVOCATION_EVIDENCE_INVALID")
    d5_identity=all(comparisons[k]["same_raw_sha256"] for k in ("EN_D3_vs_D5","AR_D3_vs_D5"))
    report={"schema_version":"d3-workbook-size-identity-reconciliation-v1","classification":"PASS_SCOPED" if d5_identity else "CONFLICTED",
      "d3_artifact_id":a.d3_artifact_id,"d5_artifact_id":a.d5_artifact_id,"workbooks":sources,"comparisons":comparisons,"d3_18_prior_invocation":d3_18,
      "interpretation":{"git_tree_vs_published_artifact":"Differences are reported by sheet presence, actual worksheet XML row/cell counts, formulas, errors and dimensions; they are not silently reconciled.",
        "d3_vs_d5":"Exact byte identity is required and checked independently for each language."},
      "limitations":["This report does not close D3 or D3-S. It only reconciles the workbook package identities and structural counts."]}
    out=pathlib.Path(a.output); out.mkdir(parents=True,exist_ok=True)
    (out/"D3_WORKBOOK_SIZE_AND_IDENTITY_RECONCILIATION_2026-11-06.json").write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    lines=["# D3 Workbook Size and Identity Reconciliation — 2026-11-06","",
      f"- D3 Artifact: {a.d3_artifact_id}; D5 Artifact: {a.d5_artifact_id}.",
      f"- D3-18 prior invocation: {d3_18['classification']}, Run {d3_18['run_id']}, Job {d3_18['job_id']}, Test ID {d3_18['test_id']}, Tested SHA {d3_18['tested_sha']}.","",
      "| Workbook | Bytes | SHA-256 | Sheets | Worksheet rows | Cells | Formulas | Excel errors |",
      "|---|---:|---|---:|---:|---:|---:|---:|"]
    for k,v in sources.items():
      lines.append(f"| {k} | {v['bytes']} | {v['sha256']} | {v['sheet_count']} | {v['row_count_total']} | {v['cell_count_total']} | {v['formula_count_total']} | {v['error_cell_count_total']} |")
    lines += ["","## Comparison results"]
    for k,v in comparisons.items():
      lines.append(f"- {k}: exact bytes {v['same_raw_sha256']}; sheet-count equality {v['same_sheet_count']}; differing/missing sheets {v['different_sheet_count']}.")
    lines += ["","D3-18 scoped evidence does not close D3-S or the full D3 phase."]
    (out/"D3_WORKBOOK_SIZE_AND_IDENTITY_RECONCILIATION_2026-11-06.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps({"classification":report["classification"],"d5_byte_identity":d5_identity,"source_count":len(sources),"d3_18":d3_18},sort_keys=True),flush=True)
    if not d5_identity: raise SystemExit("D3_D5_WORKBOOK_BYTE_IDENTITY_CONFLICT")

if __name__=="__main__": main()
