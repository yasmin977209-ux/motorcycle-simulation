import json
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

OUT = Path("deliverables")
EVIDENCE = Path("docs/stage_d")
FILES = [
    "التقرير_الكامل_AR.docx",
    "Full_Report_EN.docx",
    "الملخص_AR.docx",
    "Summary_EN.docx",
    "دراسة_الجدوى_AR.docx",
]

def document_text(doc):
    parts = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            parts.extend(cell.text for cell in row.cells)
    return "\n".join(parts)

def test_five_required_docx_outputs_open_and_have_evidence_seal():
    audit = json.loads((EVIDENCE / "D4_BUILD_AUDIT_2026-11-05.json").read_text(encoding="utf-8"))
    manifest_sha = audit["manifest_sha256"]
    for name in FILES:
        path = OUT / name
        assert path.is_file() and path.stat().st_size > 0
        doc = Document(path)
        text = document_text(doc)
        assert audit["tested_sha"] in text
        assert manifest_sha in text
        assert "FINAL_ACCEPTED" in text or "NOT_FINAL_BLOCKED" in text

def test_all_rendered_number_ids_resolve_to_registry_and_are_present():
    audit = json.loads((EVIDENCE / "D4_BUILD_AUDIT_2026-11-05.json").read_text(encoding="utf-8"))
    registry = json.loads(Path("results/number_registry.json").read_text(encoding="utf-8"))
    ids = {entry["number_id"] for entry in registry["entries"]}
    used = set(audit["number_ids"])
    assert audit["number_ids_rendered"] > 0
    assert used <= ids
    for name in FILES:
        text = document_text(Document(OUT / name))
        for number_id in used:
            assert number_id in text, (name, number_id)

def test_mandatory_disclosures_and_missing_fields_are_explicit():
    ar = document_text(Document(OUT / "التقرير_الكامل_AR.docx"))
    en = document_text(Document(OUT / "Full_Report_EN.docx"))
    feasibility = document_text(Document(OUT / "دراسة_الجدوى_AR.docx"))
    assert "ليس توقعاً واقعياً" in ar
    assert "not a realistic forecast" in en
    for field in ("Accounts_Receivable", "Accumulated_Depreciation", "Gross_Bike_Assets", "Guarantee_Claim_Receivable", "Total_Assets"):
        assert field in ar or field in feasibility

def test_arabic_documents_include_rtl_paragraph_properties():
    for name in ("التقرير_الكامل_AR.docx", "الملخص_AR.docx", "دراسة_الجدوى_AR.docx"):
        doc = Document(OUT / name)
        xml = doc._element.xml
        assert "w:bidi" in xml
        assert "w:rtl" in xml

def test_summary_pdf_page_count_is_two_or_three():
    from pypdf import PdfReader
    pdf_dir = Path("/tmp/d4-pdf")
    for name in ("الملخص_AR.pdf", "Summary_EN.pdf"):
        path = pdf_dir / name
        assert path.is_file(), f"missing rendered PDF: {path}"
        pages = len(PdfReader(str(path)).pages)
        assert 2 <= pages <= 3, (name, pages)
