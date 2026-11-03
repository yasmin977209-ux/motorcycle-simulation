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
    assert exact_display(10, 4) == "2.50"
    assert exact_display(5, 2) == "2.50"
    with pytest.raises(ValueError, match="REGISTRY_EXACT_VALUE_NOT_REDUCED"):
        exact_display(10, 2)
    registry = {"entries": [{
        "number_id": "NR-test", "numerator": 501055213, "denominator": 20,
        "display_value": "25052760.65"
    }], "daily_series": []}
    assert registry_display(registry, "NR-test") == "25052760.65"
