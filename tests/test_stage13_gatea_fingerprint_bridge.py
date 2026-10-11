from __future__ import annotations
import json
import pytest
from scripts.stage13_gatea_fingerprint_bridge import parse_json_bytes

def test_standard_json_is_parsed_unchanged():
    raw=b'{"scenario":"C070_G100","trial_count":550}\n'
    value,mode=parse_json_bytes(raw)
    assert value=={"scenario":"C070_G100","trial_count":550}
    assert mode=="standard_json"

def test_only_exact_known_stage10_suffix_can_be_parsed_in_memory():
    raw=b'{"scenario":"C070_G100","trial_count":550}'+bytes((92,110))
    value,mode=parse_json_bytes(raw,allow_known_stage10_suffix=True)
    assert value=={"scenario":"C070_G100","trial_count":550}
    assert mode=="known_stage10_literal_backslash_n_suffix_removed_in_memory"
    assert raw.endswith(bytes((125,92,110)))

def test_known_suffix_rejected_without_explicit_permission():
    raw=b'{"scenario":"C070_G100"}'+bytes((92,110))
    with pytest.raises(ValueError,match="UNEXPECTED_LITERAL_BACKSLASH_N_JSON_SUFFIX"):
        parse_json_bytes(raw)

def test_other_trailing_bytes_are_never_recovered():
    with pytest.raises(json.JSONDecodeError):
        parse_json_bytes(b'{"scenario":"C070_G100"} unexpected',allow_known_stage10_suffix=True)
