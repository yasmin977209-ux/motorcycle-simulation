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
