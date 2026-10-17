from __future__ import annotations
import pytest
from scripts.generate_c100_golden_extension import MASTER_SEED, SOURCE_COMMIT, SOURCE_SHA, EXTENSION_SCHEMA_VERSION, SCENARIOS, canonical_result_sha256
from scripts.resume_c100_golden_extension import PRIOR_RUN_ID, expected_extension_keys, expected_prior_keys, missing_keys, validate_record, validate_records

def row(s="C100_G000",n=2,rid=PRIOR_RUN_ID):
    result={"scenario_id":s,"trial_id":n,"value":n*10}
    return {"master_seed":MASTER_SEED,"origin":"pinned_source_reference","result_sha256":canonical_result_sha256(result),
      "run_attempt":1,"run_id":rid,"scenario_id":s,"schema_version":EXTENSION_SCHEMA_VERSION,
      "source_commit":SOURCE_COMMIT,"source_sha":SOURCE_SHA,"trial_id":n,"trial_result":result}

def test_expected_extension_is_exactly_2995_keys_across_only_five_c100_scenarios():
    keys=expected_extension_keys()
    assert len(keys)==2995
    assert {s for s,_ in keys}==set(SCENARIOS)
    assert all(2<=n<=600 for _,n in keys)

def test_gap_is_exactly_947_missing_ids_and_never_repeats_prior_keys():
    missing=set(missing_keys(expected_prior_keys()))
    expected=({("C100_G070",n) for n in range(253,601)} | {("C100_G100",n) for n in range(2,601)})
    assert len(missing)==947 and missing==expected
    assert not missing.intersection(expected_prior_keys())

def test_result_hash_is_recomputed_from_serialized_trial_result():
    r=row()
    assert validate_record(r)==("C100_G000",2,r["result_sha256"])
    r["result_sha256"]="0"*64
    with pytest.raises(RuntimeError,match="TRIAL_RESULT_SHA256_MISMATCH"): validate_record(r)

def test_identity_mismatch_is_rejected():
    r=row(); r["source_sha"]="a"*40
    with pytest.raises(RuntimeError,match="TRIAL_SOURCE_IDENTITY_MISMATCH"): validate_record(r)
    r=row(); r["trial_result"]["scenario_id"]="C085_G070"
    with pytest.raises(RuntimeError,match="TRIAL_RESULT_IDENTITY_MISMATCH"): validate_record(r)

def test_duplicate_keys_and_unapproved_run_provenance_are_rejected():
    r=row()
    with pytest.raises(RuntimeError,match="DUPLICATE_TRIAL_ID"): validate_records([r,dict(r)],{PRIOR_RUN_ID})
    r=row(rid=777)
    with pytest.raises(RuntimeError,match="TRIAL_RUN_NOT_ALLOWED"): validate_records([r],{PRIOR_RUN_ID})
