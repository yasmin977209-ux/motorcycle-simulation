from __future__ import annotations
import io, zipfile
import pytest
from scripts.audit_s6_deliverables_bundle import safe, zip_check, parse_sums, CONTRACTS, EXPECTED

def test_safe_paths_reject_traversal_and_absolute():
    assert safe("manifest.json")
    assert safe("folder/report.docx")
    for value in ("../x","/x","C:/x","folder\\x","a/../b"):
        assert not safe(value)

def test_zip_exact_inventory_crc_and_duplicate_rejection():
    good=io.BytesIO()
    with zipfile.ZipFile(good,"w") as z:
        for name in EXPECTED: z.writestr(name,b"x")
    with zipfile.ZipFile(io.BytesIO(good.getvalue())) as z:
        assert set(zip_check(z,EXPECTED))==EXPECTED
    dup=io.BytesIO()
    with zipfile.ZipFile(dup,"w") as z:
        z.writestr("manifest.json",b"{}")
        z.writestr("manifest.json",b"{}")
    with zipfile.ZipFile(io.BytesIO(dup.getvalue())) as z:
        with pytest.raises(ValueError,match="ZIP_DUPLICATE_MEMBER"):
            zip_check(z,{"manifest.json"})

def test_sha256sums_parser_rejects_duplicate_and_bad_lines():
    assert parse_sums(b"0"*64+b"  file.zip\n")=={"file.zip":"0"*64}
    with pytest.raises(ValueError,match="SHA256SUMS_DUPLICATE"):
        parse_sums(b"0"*64+b"  file\n"+b"1"*64+b"  file\n")
    with pytest.raises(ValueError,match="SHA256SUMS_INVALID_LINE"):
        parse_sums(b"bad\n")

def test_required_historical_test_contracts_are_present():
    assert set(CONTRACTS)=={"175","176","179","180","181","182","183","186"}
    assert len(EXPECTED)==8


def test_worksheet_rtl_flags_reads_xlsx_xml_without_readonly_sheet_view(tmp_path):
    from openpyxl import Workbook
    from scripts.audit_s6_deliverables_bundle import worksheet_rtl_flags
    path=tmp_path/"layout.xlsx"
    wb=Workbook()
    ws=wb.active
    ws.title="EN"
    ws.sheet_view.rightToLeft=False
    ar=wb.create_sheet("AR")
    ar.sheet_view.rightToLeft=True
    wb.save(path)
    assert worksheet_rtl_flags(path)==[False, True]

def test_excel_numeric_float_representation_is_checked_against_exact_registry_display():
    from scripts.audit_s6_deliverables_bundle import financial_value_matches
    assert financial_value_matches(25052760.65, "25052760.65")
    assert financial_value_matches(25052760, "25052760")
    assert not financial_value_matches(25052760.650000002, "25052760.65")
    assert not financial_value_matches(25052760.65, "25052760.66")


def test_registry_display_uses_reduced_exact_rational_and_two_decimal_half_even():
    from scripts.audit_s6_deliverables_bundle import exact_display, registry_display
    assert exact_display(501055213, 20) == "25052760.65"
    assert exact_display(5, 2) == "2.50"
    with pytest.raises(ValueError, match="REGISTRY_EXACT_VALUE_NOT_REDUCED"):
        exact_display(10, 2)
    registry = {"entries": [{
        "number_id": "NR-test", "numerator": 501055213, "denominator": 20,
        "display_value": "25052760.65"
    }], "daily_series": []}
    assert registry_display(registry, "NR-test") == "25052760.65"

def test_d3_ledger_number_id_is_deterministic_and_source_bound():
    from scripts.audit_s6_deliverables_bundle import ledger_number_id
    case = {"source_member_prefix": "stagec-output/full_logging/X/",
            "source_artifact_sha256": "a" * 64, "scenario_id": "C030_G000", "trial_id": 7}
    first = ledger_number_id(case, "daily_snapshots.jsonl.gz", 0, "Cash")
    assert first.startswith("NR-") and len(first) == 27
    assert first == ledger_number_id(case, "daily_snapshots.jsonl.gz", 0, "Cash")
    assert first != ledger_number_id(case, "daily_snapshots.jsonl.gz", 1, "Cash")


def test_extension_entries_and_daily_series_are_supported_by_exact_resolver():
    from scripts.audit_s6_deliverables_bundle import registry_display
    entry = {"number_id": "NR-test", "numerator": 1202532511,
             "denominator": 48, "display_value": "25052760.65"}
    registry = {"entries": [], "daily_series": []}
    assert registry_display(registry, "NR-test", {"NR-test": entry}, {}, {}) == "25052760.65"
    assert registry_display(registry, "NR-ledger", {}, {}, {"NR-ledger": "25052760.65"}) == "25052760.65"


def test_streamed_xlsx_xml_audit_reads_185_sheets_and_numeric_values(tmp_path):
    from openpyxl import Workbook
    from scripts.audit_s6_deliverables_bundle import scan_xlsx_xml
    path = tmp_path / "stream.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet001"
    ws["A1"] = "metric"
    ws["B1"] = "number_id"
    ws["A2"] = 12.5
    for i in range(2, 186):
        wb.create_sheet(f"Sheet{i:03d}")
    wb.save(path)
    result = scan_xlsx_xml(path, {}, {}, {}, {"entries": [], "daily_series": []})
    assert len(result["sheetnames"]) == 185
    assert result["numeric_count"] == 1
    assert result["financial_count"] == 0
    assert len(result["numeric_digest"]) == 64


def test_streamed_xlsx_xml_audit_rejects_formula_and_error_cells(tmp_path):
    from openpyxl import Workbook
    from scripts.audit_s6_deliverables_bundle import scan_xlsx_xml
    path = tmp_path / "bad.xlsx"
    wb = Workbook()
    ws = wb.active
    ws["A1"] = "=1+1"
    for i in range(2, 186):
        wb.create_sheet(f"Sheet{i:03d}")
    wb.save(path)
    with pytest.raises(ValueError, match="EXCEL_FORMULA_CELL"):
        scan_xlsx_xml(path, {}, {}, {}, {"entries": [], "daily_series": []})
    ws = wb.active
    ws["A1"] = "#DIV/0!"
    ws["A1"].data_type = "e"
    wb.save(path)
    with pytest.raises(ValueError, match="EXCEL_ERROR_CELL"):
        scan_xlsx_xml(path, {}, {}, {}, {"entries": [], "daily_series": []})


def test_section_17_3_accepts_the_actual_english_generator_disclosure():
    from scripts.audit_s6_deliverables_bundle import disclosure_173_findings
    from scripts.s6_docx_reports import english_disclosure
    assert disclosure_173_findings(english_disclosure()) == []


def test_section_17_3_accepts_the_exact_arabic_governing_reference_wording():
    from scripts.audit_s6_deliverables_bundle import disclosure_173_findings
    arabic = """فجوة الواقعية (إلزامية الذكر نصاً): يفترض النموذج طلباً غير محدود وإعادة تأجير فورية في اليوم التالي، ولا سقف لحجم الأسطول، ولا تكاليف تشغيل أو صيانة أو سرقة أو تضخم، ولا تباين بين المستأجرين، ورسم الجمعة وإيجار التسوية حتميان. لذلك العائد الكبير الناتج (أضعاف رأس المال) ليس توقعاً واقعياً بل نتيجة هذه الافتراضات ويُعرض بهذا المعنى دون تضخيم.
    لأن النموذج يستبعد بنوداً كثيرة، يجب أن يتضمن كل تقرير ودراسة جدوى فقرة صريحة تبيّن أن النتائج مشروطة بحدود النموذج، خصوصاً: الأصول المحتفظ بها تُقيَّم بالقيمة الدفترية لا السوقية؛ لا إصلاحات ولا مخالفات ولا سرقة/حوادث ولا مصاريف إدارية ولا ضرائب؛ لا تمويل خارجي؛ الكفالة مضاعف حتمي لا يعكس تذبذب القدرة الفعلية على الاسترداد؛ قد تظهر نتائج غير رتيبة بين السيناريوهات لأسباب بنيوية، فلا يُقرأ التحصيل الأقل على أنه أفضل لمجرد ارتفاع صافي الحقوق؛ احتمال الخسارة المحاسبية الصفري ليس ضماناً بل نتيجة افتراضات النموذج. ولا يجوز استنتاج أي رقم لسيناريو لم يُشغَّل."""
    assert disclosure_173_findings(arabic) == []


def test_section_17_3_does_not_misclassify_partner_structure_as_a_173_requirement():
    from scripts.audit_s6_deliverables_bundle import disclosure_173_findings
    from scripts.s6_docx_reports import english_disclosure
    assert "partner_funded_capital_and_70_30_net_equity" not in disclosure_173_findings(english_disclosure())


def test_section_17_3_still_fails_closed_when_required_disclosures_are_missing():
    from scripts.audit_s6_deliverables_bundle import disclosure_173_findings
    findings = disclosure_173_findings("MISSING_EVIDENCE only")
    assert "book_value_not_market_value" in findings
    assert "no_inference_for_unexecuted_scenario" in findings


def test_docx_directionality_detects_arabic_and_english_ooxml(tmp_path):
    from docx import Document
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from scripts.audit_s6_deliverables_bundle import docx_directionality
    ar = Document()
    p = ar.add_paragraph("عربي")
    ppr = p._p.get_or_add_pPr()
    bidi = OxmlElement("w:bidi"); bidi.set(qn("w:val"), "1"); ppr.append(bidi)
    rpr = p.runs[0]._r.get_or_add_rPr()
    rtl = OxmlElement("w:rtl"); rtl.set(qn("w:val"), "1"); rpr.append(rtl)
    ar_path = tmp_path / "ar.docx"; ar.save(ar_path)
    en = Document(); en.add_paragraph("English")
    ppr = en.paragraphs[0]._p.get_or_add_pPr()
    bidi = OxmlElement("w:bidi"); bidi.set(qn("w:val"), "0"); ppr.append(bidi)
    rpr = en.paragraphs[0].runs[0]._r.get_or_add_rPr()
    rtl = OxmlElement("w:rtl"); rtl.set(qn("w:val"), "0"); rpr.append(rtl)
    en_path = tmp_path / "en.docx"; en.save(en_path)
    # A text-bearing header is part of the DOCX story and must be checked too.
    header_p = ar.sections[0].header.paragraphs[0]
    header_run = header_p.add_run("عنوان")
    header_ppr = header_p._p.get_or_add_pPr()
    header_bidi = OxmlElement("w:bidi"); header_bidi.set(qn("w:val"), "1"); header_ppr.append(header_bidi)
    header_rpr = header_run._r.get_or_add_rPr()
    header_rtl = OxmlElement("w:rtl"); header_rtl.set(qn("w:val"), "1"); header_rpr.append(header_rtl)
    ar.save(ar_path)
    ar_result = docx_directionality(ar_path)
    assert ar_result["bidi_true"] == 2
    assert ar_result["rtl_runs_true"] == 2
    assert any(name.startswith("word/header") for name in ar_result["story_parts"])
    assert ar_result["bidi_missing"] == 0
    assert ar_result["rtl_runs_missing"] == 0
    assert docx_directionality(en_path)["bidi_false"] == 1

    # Missing explicit flags on visible text must fail closed, not disappear from counts.
    plain = Document(); plain.add_paragraph("Unmarked visible text")
    plain_path = tmp_path / "plain.docx"; plain.save(plain_path)
    plain_result = docx_directionality(plain_path)
    assert plain_result["paragraphs"] == 1
    assert plain_result["text_runs"] == 1
    assert plain_result["bidi_missing"] == 1
    assert plain_result["rtl_runs_missing"] == 1


def test_d6_acceptance_statuses_distinguish_scoped_checks_from_unrun_contracts():
    from scripts.audit_s6_deliverables_bundle import acceptance_test_statuses
    result = acceptance_test_statuses(
        excel_sheets_verified=True,
        numeric_parity_verified=True,
        financial_mismatch_count=4,
        package_inventory_verified=True,
        artifact_fingerprint_verified=True,
        run_id="run-1", job_id="job-1", tested_sha="abc123",
    )
    assert result["test_175"]["status"] == "PASS_SCOPED"
    assert result["test_182"]["status"] == "BLOCKED"
    assert result["test_186"]["status"] == "PASS_SCOPED"
    for test_id in ("176", "179", "180", "181", "183"):
        assert result["test_" + test_id]["status"] == "NOT_RUN"
        assert result["test_" + test_id]["tested_sha"] == "abc123"


def test_d6_acceptance_statuses_fail_closed_when_scoped_prerequisites_missing():
    from scripts.audit_s6_deliverables_bundle import acceptance_test_statuses
    result = acceptance_test_statuses(
        excel_sheets_verified=False,
        numeric_parity_verified=False,
        financial_mismatch_count=0,
        package_inventory_verified=False,
        artifact_fingerprint_verified=False,
        run_id="run-2", job_id="job-2", tested_sha="def456",
    )
    assert result["test_175"]["status"] == "BLOCKED"
    assert result["test_182"]["status"] == "BLOCKED"
    assert result["test_186"]["status"] == "BLOCKED"


def test_docx_renderer_isolates_each_file_and_continues_after_timeout(tmp_path, monkeypatch):
    import subprocess
    from types import SimpleNamespace
    from pypdf import PdfWriter
    from scripts import audit_s6_deliverables_bundle as auditor

    paths = [tmp_path / "first.docx", tmp_path / "second.docx"]
    for path in paths:
        path.write_bytes(b"fixture")
    calls = []

    def fake_run(cmd, capture_output, text, timeout):
        calls.append((cmd, timeout))
        if len(calls) == 1:
            raise subprocess.TimeoutExpired(cmd, timeout)
        outdir = pathlib.Path(cmd[cmd.index("--outdir") + 1])
        source = pathlib.Path(cmd[-1])
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        with (outdir / (source.stem + ".pdf")).open("wb") as stream:
            writer.write(stream)
        return SimpleNamespace(returncode=0, stderr="")

    import pathlib
    monkeypatch.setattr(auditor.subprocess, "run", fake_run)
    result = auditor.render_docx_files(paths, tmp_path / "rendered")
    assert result["page_counts"] == {"second.docx": 1}
    assert result["failures"]["first.docx"]["error_type"] == "TimeoutExpired"
    assert len(calls) == 2
    assert all(call[1] == 120 for call in calls)
    profiles = [next(arg for arg in call[0] if arg.startswith("-env:UserInstallation=")) for call in calls]
    assert profiles[0] != profiles[1]
    assert all(arg.startswith("-env:UserInstallation=file:///") for arg in profiles)
    assert all(pathlib.Path(arg.split("=", 1)[1].removeprefix("file://")).is_absolute() for arg in profiles)
    assert all(pathlib.Path(arg.split("=", 1)[1].removeprefix("file://")).is_dir() for arg in profiles)

