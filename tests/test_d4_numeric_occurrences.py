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


def test_parenthetical_enumeration_is_classified_as_section_item():
    from scripts.audit_d4_numeric_occurrences import classify
    assert classify("3", "الفقرة: (3) لا تمويل خارجي") == "Section/Item number"


def test_arabic_clause_ranges_are_classified_as_reference_constants():
    from scripts.audit_d4_numeric_occurrences import classify
    assert classify("17.1", "بنوداً كثيرة (17.1–17.2)") == "Reference constant"


def test_artifact_run_numeric_pair_is_classified_as_identifier():
    from scripts.audit_d4_numeric_occurrences import classify
    assert classify("12852969854", "12852969854/40773412377") == "Identifier"

def test_parenthetical_numbered_disclaimer_items_are_classified():
    for token, context in [
        ("3", "القيمة الدفترية؛ (2) لا إصلاحات؛ (3) لا تمويل خارجي؛ (4) الكفالة؛ (5) قد تظهر نتائج"),
        ("4", "no repairs; (3) no external financing; (4) guarantee multiplier"),
        ("5", "no external financing; (4) guarantee; (5) non-monotonic results"),
    ]:
        assert classify(token, context) == "Section/Item number"


def test_long_artifact_and_run_id_pair_is_classified_as_identifier():
    context = "12852969854/40773412377"
    assert classify("12852969854", context) == "Identifier"
    assert classify("40773412377", context) == "Identifier"
