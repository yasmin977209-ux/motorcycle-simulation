from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from scripts.s6_number_registry import validate_registry

GOVERNING_SHA = "225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b"
HISTORICAL_SHA = "e5efaf0874384e8248c339ca10e248ea9e17e9f0882153b4ef88bc955b91d53f"
MISSING_FIELDS = (
    "Accounts_Receivable", "Accumulated_Depreciation", "Gross_Bike_Assets",
    "Guarantee_Claim_Receivable", "Total_Assets",
)
SCENARIOS = [f"C{c:03d}_G{g:03d}" for c in (100, 85, 70, 55, 40) for g in (100, 85, 70, 55, 40)]
METRIC_GROUPS = {
    "profit": ("cumulativeprojectprofit", "profit"),
    "cash": ("finalcash", "cash"),
}
STATS = ("mean", "p10", "p50", "p90")

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())

def set_rtl_paragraph(paragraph, rtl: bool):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT if rtl else WD_ALIGN_PARAGRAPH.LEFT
    ppr = paragraph._p.get_or_add_pPr()
    bidi = ppr.find(qn("w:bidi"))
    if bidi is None:
        bidi = OxmlElement("w:bidi")
        ppr.append(bidi)
    bidi.set(qn("w:val"), "1" if rtl else "0")
    for run in paragraph.runs:
        rpr = run._r.get_or_add_rPr()
        rtl_el = rpr.find(qn("w:rtl"))
        if rtl_el is None:
            rtl_el = OxmlElement("w:rtl")
            rpr.append(rtl_el)
        rtl_el.set(qn("w:val"), "1" if rtl else "0")
        run.font.name = "Arial"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")

def set_cell_text(cell, text, rtl: bool, size=7):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.space_before = Pt(0)
    r = p.add_run(str(text))
    r.font.name = "Arial"
    r.font.size = Pt(size)
    r._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Arial")
    set_rtl_paragraph(p, rtl)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

def add_p(doc, text, rtl, bold=False, size=9, style=None):
    p = doc.add_paragraph(style=style)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(str(text))
    r.bold = bold
    r.font.name = "Arial"
    r.font.size = Pt(size)
    r._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Arial")
    set_rtl_paragraph(p, rtl)
    return p

def add_h(doc, text, rtl, level=1):
    p = doc.add_heading("", level=level)
    r = p.add_run(text)
    r.font.name = "Arial"
    r._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Arial")
    set_rtl_paragraph(p, rtl)
    return p

def add_table(doc, rows, rtl, font_size=7):
    table = doc.add_table(rows=0, cols=len(rows[0]))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for row in rows:
        cells = table.add_row().cells
        for cell, value in zip(cells, row):
            set_cell_text(cell, value, rtl, font_size)
    return table

def setup_doc(rtl: bool, landscape=False):
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = Cm(1.35)
    sec.bottom_margin = Cm(1.35)
    sec.left_margin = Cm(1.25)
    sec.right_margin = Cm(1.25)
    if landscape:
        sec.orientation = 1
        sec.page_width, sec.page_height = sec.page_height, sec.page_width
    normal = doc.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(9)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    return doc

def evidence_disclosure(reference: str) -> str:
    marker = "## 17.3 إفصاحات تفسيرية إلزامية في كل تقرير"
    start = reference.find(marker)
    if start < 0:
        raise ValueError("REFERENCE_17_3_NOT_FOUND")
    end = reference.find("\n## ", start + len(marker))
    if end < 0:
        raise ValueError("REFERENCE_17_3_END_NOT_FOUND")
    block = reference[start:end].strip()
    if "فجوة الواقعية" not in block or "ليس توقعاً واقعياً" not in block:
        raise ValueError("REFERENCE_17_3_DISCLOSURE_INCOMPLETE")
    return block

def scenario_entries(registry):
    by = {}
    for e in registry["entries"]:
        if e.get("trial_id") is None:
            by.setdefault(e["scenario_id"], []).append(e)
    for sid, rows in by.items():
        max_n = max(int(x.get("sample_n") or 0) for x in rows)
        by[sid] = [x for x in rows if int(x.get("sample_n") or 0) == max_n]
    return by

def find_value(rows, group, stat):
    if not rows:
        return None
    names = [(e, norm(e.get("metric_name", ""))) for e in rows]
    stat_alias = {"mean": ("mean", "avg"), "p10": ("p10",), "p50": ("p50", "median"), "p90": ("p90",)}[stat]
    for e, name in names:
        if not any(a in name for a in stat_alias):
            continue
        if group == "profit":
            if "profit" not in name or "operating" in name:
                continue
            if "cumulative" not in name and "project" not in name and "profit" not in name:
                continue
        else:
            if "cash" not in name or "final" not in name:
                continue
        return e
    return None

def value_cell(entry, used_ids):
    if entry is None:
        return "MISSING_EVIDENCE"
    nid = entry["number_id"]
    used_ids.add(nid)
    return f'{entry["display_value"]}\n[{nid}]'

def status_for(sid):
    if sid.startswith("C100_"):
        return "DEGENERATE_DETERMINISTIC / CROSS_COHORT_DETERMINISTIC_REUSE; Golden revalidation NOT_RUN"
    return "NOT_CONVERGED; Gate B FAIL_SCOPED at the recorded checkpoint"

def build_matrix(registry, used_ids):
    by = scenario_entries(registry)
    rows = [["Scenario", "Cohort / disposition", "Profit: Mean / P10 / P50 / P90", "Final Cash: Mean / P10 / P50 / P90"]]
    for sid in SCENARIOS:
        entries = by.get(sid, [])
        co = "C100 deterministic reuse" if sid.startswith("C100_") else "S6"
        p = [value_cell(find_value(entries, "profit", stat), used_ids) for stat in STATS]
        c = [value_cell(find_value(entries, "cash", stat), used_ids) for stat in STATS]
        rows.append([sid, co + "\n" + status_for(sid), " | ".join(p), " | ".join(c)])
    return rows

def source_rows(registry, used_ids):
    lookup = {x["number_id"]: x for x in registry["entries"]}
    rows = [["number_id", "metric", "scenario", "cohort", "source artifact/run", "source member SHA-256", "evidence"]]
    for nid in sorted(used_ids):
        e = lookup[nid]
        rows.append([
            nid, e["metric_name"], e["scenario_id"], e.get("cohort_id", ""),
            f'{e.get("source_artifact_id")}/{e.get("source_run_id")}',
            e.get("source_member_sha256", ""), e.get("evidence_status", ""),
        ])
    return rows

def add_evidence_seal(doc, rtl, tested_sha, run_id, manifest_sha, build_date):
    add_p(doc, f"Evidence seal | build commit: {tested_sha} | workflow run: {run_id} | D4 manifest SHA-256: {manifest_sha} | date: {build_date}", rtl, size=7)
    add_p(doc, "Package status: T2_INTERIM / NOT_FINAL_BLOCKED; FINAL_ACCEPTED: NOT_DECLARED.", rtl, size=7)
    add_p(doc, f"current_governing_reference_sha256: {GOVERNING_SHA}", rtl, size=7)
    add_p(doc, f"historical_execution_reference_sha256: {HISTORICAL_SHA}", rtl, size=7)

def english_disclosure():
    return """## 17.3 Mandatory interpretive disclosures\n\n**Reality gap (must be stated explicitly):** The model assumes unlimited demand and immediate re-rental on the following day, no fleet-size ceiling, no operating, maintenance, theft, or inflation costs, no tenant heterogeneity, and deterministic Friday fees and settlement rent. Therefore the large return produced (multiples of capital) is **not a realistic forecast**; it is a consequence of these assumptions and must be presented as such without exaggeration.\n\nBecause the model excludes many items, every report and feasibility study must state that results are **conditional on model limitations**, especially: (1) retained assets are valued at book value, not market value; (2) no repairs, fines, theft/accidents, administrative expenses, or taxes; (3) no external financing; (4) the guarantee is a deterministic multiplier and does not represent variability in actual recovery capacity; (5) non-monotonic scenario results may occur for structural reasons and lower collection must not be read as better merely because net entitlements are higher; (6) zero accounting-loss probability is not a guarantee, but a result of model assumptions. No value may be inferred for an unexecuted scenario."""

def make_full_report(path, rtl, title, registry, reference_disclosure, matrix, sources, seal):
    doc = setup_doc(rtl)
    add_h(doc, title, rtl, 0)
    add_evidence_seal(doc, rtl, *seal)
    add_h(doc, "Executive overview" if not rtl else "نظرة عامة", rtl)
    add_p(doc, "This report describes the reference-compliant baseline only. It is an interim, scoped evidence report; it is not a market forecast, a production Gate A declaration, statistical convergence, or final acceptance." if not rtl else "يعرض هذا التقرير خط الأساس المطابق للمرجع فقط. وهو تقرير أدلة مرحلي محدود النطاق، وليس توقعاً سوقياً أو إعلاناً لاجتياز Gate A الإنتاجية أو تقارباً إحصائياً أو قبولاً نهائياً.", rtl)
    add_h(doc, "Model and assumptions" if not rtl else "النموذج والافتراضات", rtl)
    add_p(doc, "The model starts from the approved governing reference v2.4.0. S6 and C100 remain separate identities. C100 is deterministic cross-cohort reuse and is not treated as independent random sampling. The partner allocation is 70/30 on total net rights; the first partner funded the initial capital, while the second did not contribute capital. Partner reinvestment balances are internal memo allocations, not additional cash or balance-sheet assets." if not rtl else "يبدأ النموذج من المرجع الحاكم المعتمد v2.4.0. تبقى هويتا S6 وC100 منفصلتين. C100 إعادة استخدام حتمية عابرة للأفواج ولا يُعامل كعينة عشوائية مستقلة. توزيع الحقوق 70/30 على صافي الحقوق الكلي؛ الشريك الأول موّل رأس المال الافتتاحي، بينما لم يساهم الشريك الثاني رأسمالياً. أرصدة إعادة استثمار الشركاء تخصيصات داخلية تذكيرية وليست نقداً إضافياً أو أصولاً في الميزانية.", rtl)
    add_h(doc, "Method and evidence" if not rtl else "المنهجية والأدلة", rtl)
    add_p(doc, "All displayed financial and statistical values are read from the Number Registry and are accompanied by their number_id. Missing values remain MISSING_EVIDENCE. No backfill, extrapolation, interpolation, zero-fill, or new Trial/Simulation/Monte Carlo run was performed for this report." if not rtl else "جميع القيم المالية والإحصائية المعروضة مأخوذة من Number Registry ومرفقة بمعرّف number_id. تبقى القيم غير المتاحة MISSING_EVIDENCE. لم يُنفَّذ backfill أو استقراء أو استيفاء أو ملء بالأصفار، ولم يُشغَّل أي Trial أو Simulation أو Monte Carlo جديد لإعداد هذا التقرير.", rtl)
    add_h(doc, "Scenario results" if not rtl else "نتائج التوليفات", rtl)
    add_p(doc, "The matrix reports only registry-backed Mean and P10/P50/P90 values for cumulative project profit and final cash. It does not rank scenarios. No statistically valid paired-difference confidence interval is asserted here; therefore no 'best' or 'worst' scenario conclusion is made." if not rtl else "تعرض المصفوفة فقط قيم Mean وP10/P50/P90 المسجلة في Number Registry للربح التراكمي للمشروع والنقد النهائي. لا ترتب السيناريوهات. لا ندّعي هنا وجود فاصل ثقة صالح زمنياً للفروق المزدوجة؛ لذلك لا نستنتج سيناريو «أفضل» أو «أسوأ».", rtl)
    add_table(doc, matrix, rtl, 5)
    add_h(doc, "Validation, gates and limitations" if not rtl else "التحقق والبوابات والقيود", rtl)
    limitations = [
        "Financial Gate A: PASS_SCOPED only.",
        "Production Gate A: NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS.",
        "Gate B: FAIL_SCOPED; Stability: NOT_CONVERGED.",
        "N=4800: NOT_EXECUTED.",
        "Full Logging is representative only; normalized statuses remain NOT_VERIFIED.",
        "C100 Golden revalidation: NOT_RUN.",
        "The five historical accounting fields remain MISSING_EVIDENCE and are not inferred or zero-filled.",
        "Final acceptance remains NOT_DECLARED; package classification remains T2_INTERIM / NOT_FINAL_BLOCKED.",
    ]
    if rtl:
        limitations = [
            "Gate A المالي: PASS_SCOPED فقط.",
            "Gate A الإنتاجية: NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS.",
            "Gate B: FAIL_SCOPED؛ الاستقرار: NOT_CONVERGED.",
            "N=4800: NOT_EXECUTED.",
            "Full Logging تمثيلي فقط؛ وتبقى الحالات المعيارية NOT_VERIFIED.",
            "إعادة التحقق الذهبي C100: NOT_RUN.",
            "تبقى الحقول المحاسبية التاريخية الخمسة MISSING_EVIDENCE ولا تُستنتج ولا تُصفّر.",
            "القبول النهائي NOT_DECLARED؛ وتصنيف الحزمة T2_INTERIM / NOT_FINAL_BLOCKED.",
        ]
    for item in limitations:
        add_p(doc, "• " + item, rtl, size=8)
    add_p(doc, "Missing historical accounting fields: " + ", ".join(MISSING_FIELDS), rtl, size=8)
    add_h(doc, "Required interpretive disclosures" if not rtl else "الإفصاحات التفسيرية الإلزامية", rtl)
    disclosure_text = reference_disclosure if rtl else english_disclosure()
    for line in disclosure_text.splitlines():
        if line.startswith("## 17.3"):
            continue
        if line.strip():
            add_p(doc, line, rtl, size=8)
    add_h(doc, "Number provenance appendix" if not rtl else "ملحق سلسلة نسب الأرقام", rtl)
    add_table(doc, sources, rtl, 6)
    doc.save(path)

def make_summary(path, rtl, title, registry, disclosure, matrix, sources, seal):
    doc = setup_doc(rtl, landscape=True)
    add_h(doc, title, rtl, 0)
    add_evidence_seal(doc, rtl, *seal)
    add_h(doc, "Key messages" if not rtl else "الرسائل الرئيسية", rtl)
    msgs = [
        "The output is a reference-compliant baseline, not a market forecast.",
        "S6 and C100 identities are separate; C100 is deterministic reuse.",
        "Only registry-backed values are shown; missing evidence is not estimated.",
        "Financial Gate A is scoped only; Production Gate A is not declared.",
        "Gate B remains FAIL_SCOPED and stability remains NOT_CONVERGED.",
        "Full Logging and accounting coverage remain limited.",
    ] if not rtl else [
        "المخرجات خط أساس مطابق للمرجع وليست توقعاً سوقياً.",
        "هويتا S6 وC100 منفصلتان؛ وC100 إعادة استخدام حتمية.",
        "لا تُعرض إلا القيم ذات المعرّف في السجل؛ ولا تُقدّر الأدلة المفقودة.",
        "Gate A المالي محدود النطاق؛ وGate A الإنتاجية غير معلنة.",
        "تبقى Gate B بحالة FAIL_SCOPED والاستقرار NOT_CONVERGED.",
        "تغطية Full Logging والمحاسبة ما زالت محدودة.",
    ]
    for m in msgs:
        add_p(doc, "• " + m, rtl, size=8)
    doc.add_page_break()
    add_h(doc, "Scenario matrix — registry values only" if not rtl else "مصفوفة السيناريوهات — قيم السجل فقط", rtl)
    add_p(doc, "Each numeric value is followed by its exact number_id. MISSING_EVIDENCE is not zero." if not rtl else "تتبع كل قيمة رقمية number_id الخاص بها. وMISSING_EVIDENCE لا تعني صفراً.", rtl, size=7)
    add_table(doc, matrix, rtl, 5)
    doc.add_page_break()
    add_h(doc, "Risks, limits and conditional conclusion" if not rtl else "المخاطر والقيود والاستنتاج المشروط", rtl)
    risks = [
        "Production accounting evidence is incomplete; the five historical balance fields remain missing.",
        "C100 Golden revalidation has not run; deterministic reuse is not independent validation.",
        "Gate B failure and non-convergence prevent any final statistical claim.",
    ] if not rtl else [
        "أدلة المحاسبة الإنتاجية غير مكتملة؛ والحقول التاريخية الخمسة ما زالت مفقودة.",
        "لم تُنفَّذ إعادة التحقق الذهبي C100؛ وإعادة الاستخدام الحتمية ليست تحققاً مستقلاً.",
        "فشل Gate B وعدم التقارب يمنعان أي ادعاء إحصائي نهائي.",
    ]
    for r in risks:
        add_p(doc, "• " + r, rtl, size=8)
    add_p(doc, "Conclusion: the registry supports a scoped interim description only. It does not support an investment forecast, scenario ranking, production Gate A, convergence, or FINAL_ACCEPTED." if not rtl else "الاستنتاج: يدعم السجل وصفاً مرحلياً محدوداً فقط. ولا يدعم توقعاً استثمارياً أو ترتيب السيناريوهات أو إعلان Gate A الإنتاجية أو التقارب أو FINAL_ACCEPTED.", rtl, bold=True, size=8)
    disclosure_text = disclosure if rtl else english_disclosure()
    for line in disclosure_text.splitlines():
        if line.startswith("## 17.3"):
            continue
        if line.strip():
            add_p(doc, line, rtl, size=6)
    # Compact landscape layout: keep the executive summary within three rendered pages.
    sec = doc.sections[0]
    sec.top_margin = Cm(0.55)
    sec.bottom_margin = Cm(0.55)
    sec.left_margin = Cm(0.6)
    sec.right_margin = Cm(0.6)
    for paragraph in doc.paragraphs:
        paragraph.paragraph_format.space_after = Pt(1)
        paragraph.paragraph_format.line_spacing = 0.9
        for run in paragraph.runs:
            run.font.size = Pt(7 if paragraph.style.name.startswith('Heading') else 6)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.space_after = Pt(0)
                    paragraph.paragraph_format.line_spacing = 0.85
                    for run in paragraph.runs:
                        run.font.size = Pt(4.5)
    doc.save(path)

def make_feasibility(path, registry, disclosure, matrix, sources, seal):
    doc = setup_doc(True)
    add_h(doc, "دراسة الجدوى المشروطة — REFERENCE_COMPLIANT_BASELINE", True, 0)
    add_p(doc, "ليست توقعاً سوقياً ولا نموذجاً واقعياً معايراً. تُستخدم فقط بيانات النموذج المنفذة والقيم ذات number_id.", True, bold=True)
    add_evidence_seal(doc, True, *seal)
    add_h(doc, "الغرض والنطاق", True)
    add_p(doc, "تقيّم هذه الدراسة ما يمكن قوله من خط الأساس المطابق للمرجع وحده. لا تستخدم بيانات سوق أو أسعاراً خارجية أو تضخماً أو طلباً أو مبيعات أو تكاليف صيانة أو تمويلاً خارجياً غير ممثل في المرجع.", True)
    add_h(doc, "نموذج العمل والهيكل المالي", True)
    add_p(doc, "المشروع نموذج تأجير دراجات بعقود أساسية ومسارات فسخ وكفالة وتأجير ثانوي وتمليك عند اكتمال السداد. يوزع صافي الحقوق بنسبة 70/30؛ الشريك الأول موّل رأس المال كاملاً، والشريك الثاني لم يساهم رأسمالياً. رصيد إعادة الاستثمار يحدد توقيت التوسع ولا يمثل ملكية أو نقداً إضافياً.", True)
    add_h(doc, "اقتصاديات الدراجة والنتائج", True)
    add_p(doc, "لا تتضمن Number Registry المتاحة سجلاً تفصيلياً كاملاً لكل دراجة أو جميع التكاليف والأحداث اليومية اللازمة لحساب فترة استرداد مستقلة أو قيمة سوقية. لذلك لا تُختلق قيمة تكلفة أو مدة استرداد. تُعرض القيم الموثقة فقط في ملحق سلسلة النسب.", True)
    c100 = [e for e in registry["entries"] if e.get("cohort_id","").startswith("c100") and e.get("trial_id") is not None]
    if c100:
        add_p(doc, "يُعامل C100 بوصفه إعادة استخدام حتمية عابرة للأفواج، لا فوجاً عشوائياً مستقلاً. وتبقى إعادة التحقق الذهبي NOT_RUN.", True)
    else:
        add_p(doc, "C100 daily and Golden validation detail is MISSING_EVIDENCE in this report.", True)
    add_h(doc, "المخاطر ومؤشرات القرار", True)
    for item in [
        "مخاطر التحصيل والكفالة والسيولة لا يمكن اختزالها إلى قيمة سوقية أو توقع واقعي.",
        "الأصول المحتفظ بها تقاس بالقيمة الدفترية لا السوقية.",
        "لا توجد بيانات معتمدة هنا لتقدير الطلب أو الشغور أو الصيانة أو السرقة أو الضرائب أو التمويل.",
        "لا يجوز عرض صافي الحقوق منفرداً؛ يجب قراءته مع النقد النهائي والأصول المحتفظ بها وصافي مركز كل شريك.",
        "لا يصدر ترتيب أفضلية بين السيناريوهات دون فواصل فروق صالحة زمنياً.",
    ]:
        add_p(doc, "• " + item, True, size=8)
    add_p(doc, "الحقول المحاسبية التاريخية المفقودة: " + ", ".join(MISSING_FIELDS), True, size=8)
    add_h(doc, "النتيجة المشروطة", True)
    add_p(doc, "لا تكفي الأدلة الحالية لإعلان جدوى استثمارية واقعية أو التوصية بتوسع فعلي. النتيجة مشروطة بافتراضات المرجع وبحدود التغطية المسجلة؛ يلزم استكمال أدلة المحاسبة الإنتاجية وإعادة التحقق الذهبي والبوابات الإحصائية قبل أي قرار نهائي.", True, bold=True)
    add_h(doc, "الإفصاحات الإلزامية وفق §17.3", True)
    for line in disclosure.splitlines():
        if line.startswith("## 17.3"):
            continue
        if line.strip():
            add_p(doc, line, True, size=8)
    add_h(doc, "ملحق سلسلة نسب الأرقام", True)
    add_table(doc, sources, True, 6)
    doc.save(path)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", required=True)
    ap.add_argument("--reference", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--evidence-dir", required=True)
    ap.add_argument("--tested-sha", required=True)
    ap.add_argument("--run-id", required=True)
    args = ap.parse_args()
    reg_path, ref_path = Path(args.registry), Path(args.reference)
    raw_reg, raw_ref = reg_path.read_bytes(), ref_path.read_bytes()
    registry = json.loads(raw_reg.decode("utf-8"))
    validate_registry(registry)
    if len(raw_reg) != 24137036 or digest(raw_reg) != "743ffcced8de09a766870f201c352aabcf5789c43c84bfeae654a939700e4f87":
        raise ValueError("NUMBER_REGISTRY_PIN_MISMATCH")
    if digest(raw_ref) != GOVERNING_SHA or len(raw_ref) != 401397:
        raise ValueError("GOVERNING_REFERENCE_PIN_MISMATCH")
    reference = raw_ref.decode("utf-8")
    disclosure = evidence_disclosure(reference)
    out, evidence = Path(args.output_dir), Path(args.evidence_dir)
    out.mkdir(parents=True, exist_ok=True)
    evidence.mkdir(parents=True, exist_ok=True)
    build_date = datetime.now(timezone.utc).date().isoformat()
    manifest = {
        "schema_version": "d4-report-input-manifest-v1",
        "tested_sha": args.tested_sha,
        "workflow_run_id": args.run_id,
        "build_date_utc": build_date,
        "governing_reference_sha256": GOVERNING_SHA,
        "historical_execution_reference_sha256": HISTORICAL_SHA,
        "registry_sha256": digest(raw_reg),
        "registry_bytes": len(raw_reg),
        "registry_entry_count": len(registry["entries"]),
        "registry_daily_series_count": len(registry["daily_series"]),
        "scope": "REFERENCE_COMPLIANT_BASELINE_ONLY",
        "no_trials_or_simulation": True,
    }
    manifest_path = evidence / "D4_REPORT_MANIFEST_2026-11-05.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest_sha = digest(manifest_path.read_bytes())
    seal = (args.tested_sha, args.run_id, manifest_sha, build_date)
    used_ids = set()
    matrix = build_matrix(registry, used_ids)
    sources = source_rows(registry, used_ids)
    outputs = {
        "ar_full": out / "التقرير_الكامل_AR.docx",
        "en_full": out / "Full_Report_EN.docx",
        "ar_summary": out / "الملخص_AR.docx",
        "en_summary": out / "Summary_EN.docx",
        "feasibility": out / "دراسة_الجدوى_AR.docx",
    }
    make_full_report(outputs["ar_full"], True, "التقرير الكامل — Motorcycle Simulation", registry, disclosure, matrix, sources, seal)
    make_full_report(outputs["en_full"], False, "Motorcycle Simulation — Full Report", registry, disclosure, matrix, sources, seal)
    make_summary(outputs["ar_summary"], True, "الملخص التنفيذي — Motorcycle Simulation", registry, disclosure, matrix, sources, seal)
    make_summary(outputs["en_summary"], False, "Motorcycle Simulation — Executive Summary", registry, disclosure, matrix, sources, seal)
    make_feasibility(outputs["feasibility"], registry, disclosure, matrix, sources, seal)
    # Every rendered registry value must resolve to one unique entry; IDs are printed next to values.
    ids = {e["number_id"] for e in registry["entries"]}
    if not used_ids.issubset(ids):
        raise ValueError("UNREGISTERED_NUMBER_ID_RENDERED")
    audit = {
        "status": "PASS_SCOPED_WITH_LIMITATIONS",
        "tested_sha": args.tested_sha,
        "workflow_run_id": args.run_id,
        "manifest_sha256": manifest_sha,
        "registry_sha256": digest(raw_reg),
        "registry_blob_sha1": "8cf17de488c623f96c1961ca91d682fbbc7733d6",
        "registry_bytes": len(raw_reg),
        "number_ids_rendered": len(used_ids),
        "number_ids": sorted(used_ids),
        "outputs": {
            p.name: {"bytes": p.stat().st_size, "sha256": digest(p.read_bytes())}
            for p in outputs.values()
        },
        "limitations": [
            "No unsupported values were inferred; absent registry metrics are labelled MISSING_EVIDENCE.",
            "C100 Golden revalidation remains NOT_RUN.",
            "Daily detailed ledgers, final close-date distributions and some partner/accounting details remain outside the available registry scope.",
            "Financial Gate A remains PASS_SCOPED only; Production Gate A remains NOT_DECLARED.",
            "Gate B remains FAIL_SCOPED; Stability remains NOT_CONVERGED; N=4800 remains NOT_EXECUTED.",
            "Five historical accounting fields remain MISSING_EVIDENCE and were not inferred or zero-filled.",
            "This D4 report build is not D5 package acceptance, D6 independent audit, P17 acceptance, or FINAL_ACCEPTED.",
        ],
    }
    (evidence / "D4_BUILD_AUDIT_2026-11-05.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"D4":"GENERATED","outputs":{k:str(v) for k,v in outputs.items()},"number_ids_rendered":len(used_ids),"manifest_sha256":manifest_sha},ensure_ascii=False))

if __name__ == "__main__":
    main()
