import pytest
from scripts.s6_number_registry import normalize_entries, RegistryError

def test_exact_fraction_and_provenance():
    x=normalize_entries([{"name":"x","exact_numerator":3,"exact_denominator":2,"display_value":"1.50"}],1,2,"registry.json")[0]
    assert x["exact_value"]=={"numerator":3,"denominator":2}
    assert x["display_value"]=="1.50"
    assert x["source_artifact_id"]==1

def test_zero_denominator_rejected():
    with pytest.raises(RegistryError): normalize_entries([{"name":"x","exact_numerator":1,"exact_denominator":0}],1,2,"m")

def test_missing_metric_name_rejected():
    with pytest.raises(RegistryError): normalize_entries([{"exact_numerator":1,"exact_denominator":1}],1,2,"m")

def test_ids_are_deterministic():
    entries=[{"name":"a","exact_numerator":1,"exact_denominator":1},{"name":"b","exact_numerator":2,"exact_denominator":1}]
    assert [x["number_id"] for x in normalize_entries(entries,1,2,"m")]==[x["number_id"] for x in normalize_entries(entries,1,2,"m")]

def test_source_evidence_is_not_overstated():
    x=normalize_entries([{"name":"a","exact_numerator":5,"exact_denominator":2}],7,8,"m")[0]
    assert x["evidence_status"]=="REPORTED_ONLY_SOURCE_REGISTRY_ENTRY"
