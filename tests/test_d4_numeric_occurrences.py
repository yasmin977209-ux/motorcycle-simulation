from scripts.audit_d4_numeric_occurrences import TOKEN, classify

def test_numeric_token_regex_supports_arabic_and_hindi_digits_and_percent():
    values=[m.group(0) for m in TOKEN.finditer("12 ١٢ ۱۲ ١٢٫٥٪ 1,250.50%")]
    assert values == ["12","١٢","۱۲","١٢٫٥٪","1,250.50%"]

def test_numeric_token_classification_covers_normative_categories():
    assert classify("٢٠٢٦","تاريخ التقرير ٢٠٢٦") == "Date/Time"
    assert classify("17.3","§17.3 disclosure") == "Reference constant"
    assert classify("12","12 تجربة إحصائية") == "Section/Item number"
    assert classify("15","عدد الصفحات 15 صفحة") == "Quantity/Unit"
    assert classify("3","رقم الصفحة 3") == "Pagination"
    assert classify("2","قيمة رأس المال 2 ريال") == "Financial"
    assert classify("5","احتمال الخسارة 5٪") == "Statistical"
    assert classify("4","معادلة تعتمد على 4") == "Formula constant"
    assert classify("42","Artifact ID 42") == "Identifier"
    assert classify("9","unlabelled token 9") == "Unresolved"
