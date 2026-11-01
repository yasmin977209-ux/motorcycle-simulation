from decimal import Decimal
from scripts.s6_excel_export import exact_value, scenario_sheet_names, constants_from_reference, SCENARIO_RE, DETAILS, GAPS

def test_exact_values_do_not_use_float():
    assert exact_value(12,3)==4
    value=exact_value(5,2)
    assert value==Decimal("2.50")
    assert not isinstance(value,float)

def test_25_scenario_sheet_inventory():
    ids=[f"C{c:03d}_G{g:03d}" for c in (30,50,70,85,100) for g in (0,30,50,70,100)]
    names=scenario_sheet_names(ids)
    assert len(names)==175
    assert all(len(x)<=31 and x.isascii() for x in names)
    assert names[0]=="C030_G000_STATS"

def test_scenario_pattern():
    assert SCENARIO_RE.fullmatch("C085_G070")
    assert not SCENARIO_RE.fullmatch("C85_G070")

def test_missing_detail_scope_explicit():
    assert set(DETAILS)=={"ASSETS","ACCTG","PARTNER","GUARANTEE","CONTRACTS"}
    assert set(GAPS)=={"DAILY",*DETAILS}
    assert all("not represented in Number Registry" in x for x in GAPS.values())

def test_reference_constants_parser():
    sample="""# الباب الثاني: الثوابت
| المعرّف | القيمة (ريال يمني) | الوصف |
|---|---|---|
| `TOTAL_CAPITAL` | `3,700,000` | رأس المال الكلي، مموَّل بالكامل من الشريك الأول |
| `BIKE_BASE_PURCHASE_COST` | `350,000` | سعر شراء الدراجة الأساسي |
# الباب الثالث: entities
"""
    assert constants_from_reference(sample)==[
        ["TOTAL_CAPITAL","3,700,000","رأس المال الكلي، مموَّل بالكامل من الشريك الأول"],
        ["BIKE_BASE_PURCHASE_COST","350,000","سعر شراء الدراجة الأساسي"]
    ]


def test_sheet_direction_audit(tmp_path):
    from openpyxl import Workbook
    from scripts.s6_excel_export import audit
    path=tmp_path / "direction.xlsx"
    wb=Workbook(); ws=wb.active; ws.title="T"; ws.sheet_view.rightToLeft=True; wb.save(path); wb.close()
    assert audit(path,["T"],expected_rtl=True)["sheet_direction_status"]=="PASS"
    report=audit(path,["T"],expected_rtl=False)
    assert report["sheet_direction_status"]=="FAIL"
    assert report["sheet_direction_mismatches"]==[{"sheet":"T","expected":"LTR","actual":"RTL"}]


def test_missing_accounting_fields_are_explicit_and_not_zero_filled(tmp_path):
    from openpyxl import Workbook, load_workbook
    from scripts.s6_excel_export import ACCOUNTING_MISSING_FIELDS, write_missing_accounting_fields
    path=tmp_path / "accounting_missing.xlsx"
    wb=Workbook(write_only=True); ws=wb.create_sheet("ACCTG")
    write_missing_accounting_fields(ws,"C030_G000"); wb.save(path)
    check=load_workbook(path,read_only=True,data_only=False)
    try:
        rows=list(check["ACCTG"].iter_rows(values_only=True))
        assert [row[4] for row in rows]==list(ACCOUNTING_MISSING_FIELDS)
        assert all(row[5]=="MISSING_EVIDENCE" and row[5] is not None for row in rows)
        assert all(not isinstance(row[5],(int,float,Decimal)) for row in rows)
    finally: check.close()


def test_formula_like_strings_are_written_as_text(tmp_path):
    from openpyxl import Workbook, load_workbook
    from scripts.s6_excel_export import safe_append, audit
    path=tmp_path / "safe.xlsx"
    wb=Workbook(write_only=True)
    ws=wb.create_sheet("T")
    safe_append(ws, ["= 5 + 5", "+1000", "@name", 10])
    wb.save(path)
    check=load_workbook(path,read_only=True,data_only=False)
    try:
        row=next(check["T"].iter_rows())
        assert row[0].data_type=="s" and row[0].value=="= 5 + 5"
        assert row[3].value==10
        assert all(cell.data_type!="f" for cell in row)
    finally:
        check.close()
    assert audit(path,["T"])["excel_safety_status"]=="PASS"

    unsafe=tmp_path / "unsafe.xlsx"
    bad=Workbook()
    ws=bad.active; ws.title="T"
    ws["A1"]="=1+1"
    ws["B1"]="#VALUE!"; ws["B1"].data_type="e"
    bad.save(unsafe); bad.close()
    report=audit(unsafe,["T"])
    assert report["formula_cell_count"]==1
    assert report["formula_cells"]==[{"sheet":"T","cell":"A1","classification":"FORMULA_CELL","formula":"=1+1"}]
    assert report["excel_error_cell_count"]==1
    assert report["excel_error_cells"]==[{"sheet":"T","cell":"B1","classification":"EXCEL_ERROR_CELL","error_type":"#VALUE!"}]
    assert report["excel_safety_status"]=="FAIL"


def test_bilingual_compare_rejects_trailing_dimension_mismatch(tmp_path):
    import pytest
    from openpyxl import Workbook
    from scripts.s6_excel_export import compare

    ar = tmp_path / "ar.xlsx"
    en = tmp_path / "en.xlsx"
    left = Workbook()
    left.active.title = "T"
    left.active["A1"] = 10
    left.save(ar)
    left.close()

    right = Workbook()
    right.active.title = "T"
    right.active["A1"] = 10
    right.active["A2"] = 20
    right.save(en)
    right.close()

    with pytest.raises(ValueError, match="BILINGUAL_DIMENSION_MISMATCH:T"):
        compare(ar, en, ["T"])
