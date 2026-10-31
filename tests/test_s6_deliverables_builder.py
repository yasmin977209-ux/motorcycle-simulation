import os, zipfile, hashlib
import pytest
from scripts.s6_artifact_reader import ArtifactPin, Archive, ArtifactValidationError, S6_SOURCE, S6_COHORT, C100_SOURCE, C100_COHORT, MASTER_SEED
from scripts.s6_deliverables_model import to_jsonable, ModelValidationError, SourceRef, sourced
from scripts.s6_deliverables_builder import build_shared_model

P={"aggregate":os.environ.get("STAGE_D_AGGREGATE","/mnt/data/github-actions-artifact-12852969854.zip"),
   "full_logging":os.environ.get("STAGE_D_FULL_LOGGING","/mnt/data/github-actions-artifact-12998778418.zip"),
   "c100":os.environ.get("STAGE_D_C100","/mnt/data/github-actions-artifact-12630457193.zip")}

@pytest.fixture(scope="module")
def model():
    if not all(os.path.isfile(p) for p in P.values()):
        pytest.skip("pinned artifact ZIPs are supplied only to the local integration validation")
    return build_shared_model(P)

def test_pinned_identities():
    assert (S6_SOURCE,S6_COHORT,MASTER_SEED)==("da1a9ea9b5cd789c944de3f07b08395bb67c49e7","s6-v23-da1a9ea9",20270101)
    assert (C100_SOURCE,C100_COHORT)==("965281d52441cd0d4b744e211c9f68ee4cdc3753","c100-v23-s4-20261026-965281d5")

def test_float_rejected():
    with pytest.raises(ModelValidationError): to_jsonable({"financial":1.25})

def test_source_ref_keeps_provenance():
    s=SourceRef(1,2,"trial_result.json",cohort_id=S6_COHORT,source_sha=S6_SOURCE,trial_id=5)
    assert sourced(7,s)["source"]["trial_id"]==5

def test_zip_pin_and_crc(tmp_path):
    p=tmp_path/"tiny.zip"
    with zipfile.ZipFile(p,"w") as z:z.writestr("x.json",'{"a":1}')
    raw=p.read_bytes(); pin=ArtifactPin(1,2,len(raw),hashlib.sha256(raw).hexdigest(),"tiny.zip")
    a=Archive(str(p),pin).open()
    assert a.read_json("x.json")["a"]==1
    a.close()

def test_zip_wrong_digest_fails_closed(tmp_path):
    p=tmp_path/"tiny.zip"
    with zipfile.ZipFile(p,"w") as z:z.writestr("x","x")
    with pytest.raises(ArtifactValidationError): Archive(str(p),ArtifactPin(1,2,p.stat().st_size,"0"*64,"tiny.zip")).open()

def test_frozen_map_counts(model):
    assert (len(model.representative_mapping),len(model.unique_keys),len(model.trial_records))==(125,105,105)

def test_s6_and_c100_are_separate(model):
    counts={}
    for k in model.unique_keys: counts[k["cohort_id"]]=counts.get(k["cohort_id"],0)+1
    assert counts=={S6_COHORT:100,C100_COHORT:5}

def test_role_assignments_are_not_reselected(model):
    assert sum(len(x["role_assignments"]) for x in model.trial_records)==125

def test_manifest_status_is_not_upgraded(model):
    assert {x["normalized_audit_status"] for x in model.manifest_reconciliation}=={"NOT_VERIFIED"}

def test_each_value_has_artifact_provenance(model):
    assert model.trial_records[0]["values"]["final_net_project_equity"]["source"]["artifact_id"]==12998778418

def test_historical_and_governing_references_separate(model):
    assert model.governing_reference_sha256=="225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b"
    assert model.historical_execution_reference_sha256=="e5efaf0874384e8248c339ca10e248ea9e17e9f0882153b4ef88bc955b91d53f"

def test_48k_scope_not_claimed(model):
    assert any("105 representative keys only" in x for x in model.limitations)

def test_no_c100_relabeling(model):
    assert all(k["source_sha"]==C100_SOURCE for k in model.unique_keys if k["cohort_id"]==C100_COHORT)
