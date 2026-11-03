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
