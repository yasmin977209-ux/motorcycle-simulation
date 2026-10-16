from pathlib import Path
import pytest
from scripts.cp_daily_details_extension import (
    N2400_RUN_ID, N2400_TESTED_HEAD_SHA, SOURCE_SHA, MASTER_SEED, TARGET_SCENARIO,
    _validate_n2400_record, stage10_trial_result_sha256, validate_trial_id_coverage,
)
class Provider:
    def __init__(self, expected): self.expected=expected
    def get_fingerprint(self, scenario, trial_id):
        assert scenario == TARGET_SCENARIO
        return self.expected.get(trial_id)
def sample_record(trial_id=1201):
    payload={"scenario_id":TARGET_SCENARIO,"trial_id":trial_id,"collection_probability":0.3,
      "recovery_rate_pct":30,"final_cash":100,"final_net_project_equity":200,
      "partner1_final_entitlement":130,"partner2_final_entitlement":70,"final_close_date":"2031-04-06"}
    digest=stage10_trial_result_sha256(payload)
    return {"scenario_id":TARGET_SCENARIO,"trial_id":trial_id,"source_sha":SOURCE_SHA,"master_seed":MASTER_SEED,
      "source_commit":"0156c5f4272eb0ca7e32442657d0df9eaf4973d3","run_id":N2400_RUN_ID,"run_attempt":1,
      "tested_head_sha":N2400_TESTED_HEAD_SHA,"exact_golden_match":True,"result_sha256":digest,
      "approved_golden_sha256":digest,"trial_result":payload}
def test_trial_id_coverage_rejects_duplicates_gaps_and_extras():
    validate_trial_id_coverage([1201,1202,1203],[1201,1202,1203],"test")
    for ids in ([1201,1202,1202],[1201,1203],[1201,1202,1204]):
        with pytest.raises(RuntimeError, match="test"):
            validate_trial_id_coverage(ids,[1201,1202,1203],"test")
def test_n2400_record_requires_pinned_identity_and_golden_fingerprint():
    row=sample_record(); digest=row["result_sha256"]
    verified=_validate_n2400_record(row,trial_id=1201,provider=Provider({1201:digest}))
    assert verified["trial_id"]==1201 and verified["result_sha256"]==digest
    bad=dict(row); bad["source_sha"]="0"*40
    with pytest.raises(RuntimeError,match="SOURCE_IDENTITY"):
        _validate_n2400_record(bad,trial_id=1201,provider=Provider({1201:digest}))
    bad=dict(row); bad["exact_golden_match"]=False
    with pytest.raises(RuntimeError,match="GOLDEN_MATCH"):
        _validate_n2400_record(bad,trial_id=1201,provider=Provider({1201:digest}))
    bad=dict(row); bad["trial_result"]=dict(row["trial_result"],final_cash=101)
    with pytest.raises(RuntimeError,match="HASH_MISMATCH"):
        _validate_n2400_record(bad,trial_id=1201,provider=Provider({1201:digest}))
def test_daily_details_scope_is_delivery_only_and_fixed_to_authorized_ids():
    source=Path("scripts/cp_daily_details_extension.py").read_text(encoding="utf-8")
    assert 'TARGET_SCENARIO = "C030_G030"' in source
    assert "range(1201, 2401)" in source
    assert '"statistical_checkpoint_executed": False' in source
    assert '"historical_trial_ids_1_to_1200_replayed": False' in source
    assert '"source_sha_bumped": False' in source
