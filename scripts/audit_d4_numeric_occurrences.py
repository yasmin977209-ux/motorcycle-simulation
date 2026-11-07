#!/usr/bin/env python3
"""Occurrence-level numeric token lineage audit across all WordprocessingML story parts."""
from __future__ import annotations
import argparse, json, re, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

W="{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
TOKEN=re.compile(r"(?<![A-Za-z0-9_])(?:[0-9٠-٩۰-۹]{1,3}(?:[,٬][0-9٠-٩۰-۹]{3})+(?:[.٫][0-9٠-٩۰-۹]+)?|[0-9٠-٩۰-۹]+(?:[.٫][0-9٠-٩۰-۹]+)?)(?:[%٪])?(?![A-Za-z0-9_])")
REGISTRY_ID=re.compile(r"\bNR-[A-Za-z0-9_-]{8,}\b")
DATE=re.compile(r"[0-9٠-٩۰-۹]{1,4}[-/][0-9٠-٩۰-۹]{1,2}[-/][0-9٠-٩۰-۹]{1,4}")
FINANCIAL=re.compile(r"(?i)(£|\$|€|ريال|جنيه|دولار|رأس المال|رأس مال|الإيراد|الإيرادات|الأصول|الالتزامات|الحقوق|الربح|الخسارة|equity|capital|revenue|asset|liabilit|profit|loss|cash|balance)")
STATISTICAL=re.compile(r"(?i)(%|٪|نسبة|احتمال|متوسط|وسيط|انحراف|مئين|كمية|تجربة|تجارب|scenario|trial|mean|median|percent|probability|rate|sample|n\s*=)")
REFERENCE=re.compile(r"(?i)(§|المادة|الفقرة|البند|مرجع|reference|section|clause|v2\.)")
FORMULA=re.compile(r"(?i)(formula|معادلة|equation|calculated|يحسب|ناتج المعادلة)")
QUANTITY=re.compile(r"(?i)(كمية|عدد|صفحة|صفحات|يوم|أيام|ساعة|ساعات|شهر|أشهر|سنة|سنوات|kg|km|days?|hours?|months?|years?|pages?|units?)")
IDENTIFIER=re.compile(r"(?i)(id\b|identifier|معرّف|معرف|كود|code|run\s*id|artifact\s*id|job\s*id|sha)")
PAGINATION=re.compile(r"(?i)(\bPAGE\b|\bNUMPAGES\b|page number|رقم الصفحة)")

def classify(token:str, context:str, field_context:str="")->str:
    if PAGINATION.search(field_context) or PAGINATION.search(context): return "Pagination"
    if REFERENCE.search(context): return "Reference constant"
    if DATE.search(context) or re.search(r"(?i)(تاريخ|date|time|وقت|اليوم)",context): return "Date/Time"
    if re.match(r"^\s*[0-9٠-٩۰-۹]+(?:[.)،-])?\s+",context): return "Section/Item number"
    if FINANCIAL.search(context): return "Financial"
    if STATISTICAL.search(context): return "Statistical"
    if FORMULA.search(context): return "Formula constant"
    if QUANTITY.search(context): return "Quantity/Unit"
    if IDENTIFIER.search(context): return "Identifier"
    return "Unresolved"

def audit_docx(path:Path)->dict:
    occurrences=[]; part_count=0
    with zipfile.ZipFile(path) as z:
        bad=z.testzip()
        if bad: raise ValueError(f"DOCX_ZIP_CRC_FAILURE:{path.name}:{bad}")
        for name in sorted(n for n in z.namelist() if n.startswith("word/") and n.endswith(".xml")):
            part_count+=1
            root=ET.fromstring(z.read(name))
            pindex=0
            for para in root.iter(W+"p"):
                pindex+=1
                chunks=[]
                for node in para.iter():
                    if node.tag in (W+"t",W+"instrText") and node.text:
                        chunks.append(node.text)
                text="".join(chunks)
                if not text: continue
                field_context=" ".join((x.text or "") for x in para.iter(W+"instrText"))
                ids=REGISTRY_ID.findall(text)
                for match in TOKEN.finditer(text):
                    token=match.group(0)
                    context=text[max(0,match.start()-100):min(len(text),match.end()+100)]
                    category=classify(token,context,field_context)
                    linked_id=ids[0] if ids else None
                    resolved=(category in ("Financial","Statistical") and linked_id is not None)
                    if resolved: disposition="RESOLVED"
                    elif category!="Unresolved": disposition="EXPLICITLY_CLASSIFIED"
                    else: disposition="UNRESOLVED"
                    occurrences.append({"part":name,"paragraph_index":pindex,"token":token,
                        "context":context,
                        "category":category,"number_id":linked_id if resolved else None,
                        "disposition":disposition})
    counts={}
    for x in occurrences: counts[x["category"]]=counts.get(x["category"],0)+1
    resolved=sum(x["disposition"]=="RESOLVED" for x in occurrences)
    explicit=sum(x["disposition"]=="EXPLICITLY_CLASSIFIED" for x in occurrences)
    unresolved=sum(x["disposition"]=="UNRESOLVED" for x in occurrences)
    return {"file":path.name,"bytes":path.stat().st_size,"xml_parts_scanned":part_count,
      "total_occurrences":len(occurrences),"resolved_occurrences":resolved,
      "explicitly_classified_occurrences":explicit,"unresolved_occurrences":unresolved,
      "category_counts":counts,"identity_equation":len(occurrences)==resolved+explicit+unresolved,
      "occurrences":occurrences}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input-dir",default="deliverables")
    ap.add_argument("--output",default="docs/stage_d/D4_NUMERIC_TOKEN_LINEAGE_2026-11-07.json")
    args=ap.parse_args()
    root=Path(args.input_dir)
    names=["التقرير_الكامل_AR.docx","Full_Report_EN.docx","الملخص_AR.docx","Summary_EN.docx","دراسة_الجدوى_AR.docx"]
    results=[audit_docx(root/n) for n in names]
    total=sum(x["total_occurrences"] for x in results)
    resolved=sum(x["resolved_occurrences"] for x in results)
    explicit=sum(x["explicitly_classified_occurrences"] for x in results)
    unresolved=sum(x["unresolved_occurrences"] for x in results)
    report={"schema":"d4-occurrence-level-numeric-lineage-v1","documents":results,
      "total_occurrences":total,"resolved_occurrences":resolved,
      "explicitly_classified_occurrences":explicit,"unresolved_occurrences":unresolved,
      "identity_equation":total==resolved+explicit+unresolved,
      "unresolved_samples":[{"file":x["file"],"part":o["part"],"token":o["token"],"context":o["context"]} for x in results for o in x["occurrences"] if o["disposition"]=="UNRESOLVED"][:100],
      "acceptance":"PASS" if total==resolved+explicit and unresolved==0 else "BLOCKED"}
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    Path(args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("total_occurrences","resolved_occurrences","explicitly_classified_occurrences","unresolved_occurrences","identity_equation","acceptance","unresolved_samples")}))
    if report["acceptance"]!="PASS": raise SystemExit("D4_NUMERIC_TOKEN_LINEAGE_NOT_GAP_FREE")
if __name__=="__main__": main()
