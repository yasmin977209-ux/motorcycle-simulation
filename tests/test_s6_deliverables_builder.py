import os, zipfile, hashlib, stat, warnings, io
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

def test_manifest_status_is_cryptographically_resolved(model):
    assert len(model.manifest_reconciliation)==105
    assert {x["normalized_audit_status"] for x in model.manifest_reconciliation}=={"PASS_SCOPED_REPRESENTATIVE_FULL_LOGGING"}
    assert all(x["trial_manifest_size_bytes"]>0 and x["post_write_audit_size_bytes"]>0 for x in model.manifest_reconciliation)
    assert all(x["trial_manifest_sha256_match"] and x["post_write_audit_sha256_match"] for x in model.manifest_reconciliation)

def test_each_value_has_artifact_provenance(model):
    assert model.trial_records[0]["values"]["final_net_project_equity"]["source"]["artifact_id"]==12998778418

def test_historical_and_governing_references_separate(model):
    assert model.governing_reference_sha256=="225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b"
    assert model.historical_execution_reference_sha256=="e5efaf0874384e8248c339ca10e248ea9e17e9f0882153b4ef88bc955b91d53f"

def test_48k_scope_not_claimed(model):
    assert any("105 representative keys only" in x for x in model.limitations)

def test_no_c100_relabeling(model):
    assert all(k["source_sha"]==C100_SOURCE for k in model.unique_keys if k["cohort_id"]==C100_COHORT)


def _make_archive(tmp_path, members):
    p=tmp_path/"safety.zip"
    with zipfile.ZipFile(p,"w") as z:
        for info, data in members:
            z.writestr(info, data)
    raw=p.read_bytes()
    pin=ArtifactPin(9,9,len(raw),hashlib.sha256(raw).hexdigest(),"safety.zip")
    return Archive(str(p),pin)

def test_zip_duplicate_member_rejected(tmp_path):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        a=_make_archive(tmp_path,[( "same.json",'{"a":1}'),("same.json",'{"a":2}')])
    with pytest.raises(ArtifactValidationError,match="DUPLICATE_ZIP_MEMBER"):
        a.open()

@pytest.mark.parametrize("member",["../escape.json","/absolute.json","C:/drive.json","a//b.json","a/./b.json"])
def test_zip_unsafe_paths_rejected(tmp_path,member):
    a=_make_archive(tmp_path,[(member,"x")])
    with pytest.raises(ArtifactValidationError,match="UNSAFE_ZIP_PATH"):
        a.open()

def test_zip_symlink_rejected(tmp_path):
    link=zipfile.ZipInfo("link")
    link.create_system=3
    link.external_attr=(stat.S_IFLNK|0o777)<<16
    a=_make_archive(tmp_path,[(link,"target")])
    with pytest.raises(ArtifactValidationError,match="ZIP_SYMLINK"):
        a.open()

def test_losscase_and_maxcase_are_global_argmin_argmax_read_only(model):
    import pyarrow.parquet as pq
    agg=zipfile.ZipFile(P["aggregate"])
    try:
        table=pq.read_table(io.BytesIO(agg.read("trials_summary.parquet")))
    finally:
        agg.close()
    cols={name.lower():name for name in table.column_names}
    scenario_col=cols.get("scenario_id")
    trial_col=cols.get("trial_id")
    equity_col=cols.get("final_net_project_equity")
    assert scenario_col and trial_col and equity_col, table.column_names
    extrema={}
    for row in table.select([scenario_col,trial_col,equity_col]).to_pylist():
        value=row[equity_col]
        assert not isinstance(value,float), "FLOAT_IN_TRIAL_SUMMARY"
        extrema.setdefault(row[scenario_col],[]).append((int(row[trial_col]),int(value)))
    frozen={}
    for assignment in model.representative_mapping:
        if assignment["cohort_id"] != S6_COHORT:
            continue
        frozen.setdefault(assignment["scenario_id"],{})[assignment["role"]]=assignment
    assert len(frozen)==20
    assert set(frozen)==set(extrema)
    for scenario, roles in frozen.items():
        values=[value for _,value in extrema[scenario]]
        assert roles["LossCase"]["final_net_project_equity"]==min(values), scenario
        assert roles["MaxCase"]["final_net_project_equity"]==max(values), scenario


def test_manifest_resolver_binds_central_directory_sizes_and_root_hashes(tmp_path):
    import json
    from scripts.s6_manifest_resolver import resolve_trial_manifest
    folder="C030_G000__trial_000156"
    base=f"stagec-output/full_logging/{folder}/"
    trial={"source_sha":S6_SOURCE,"cohort_id":S6_COHORT,"scenario_id":"C030_G000","trial_id":156,
           "status":"PASS_SCOPED_REPRESENTATIVE_FULL_LOGGING",
           "actual_trial_fingerprint":"a"*64,"expected_trial_fingerprint":"a"*64}
    audit={"status":"PASS_SCOPED_REPRESENTATIVE_FULL_LOGGING","trial_fingerprint":"a"*64,
           "trial_fingerprint_match":True,"rollforward_mismatch_count":0,"balance_mismatch_count":0}
    result={"trial_fingerprint":"a"*64}
    members={base+"trial_manifest.json":json.dumps(trial,sort_keys=True).encode(),
             base+"post_write_audit.json":json.dumps(audit,sort_keys=True).encode(),
             base+"trial_result.json":json.dumps(result,sort_keys=True).encode()}
    p=tmp_path/"resolver.zip"
    with zipfile.ZipFile(p,"w") as z:
        for name,data in members.items(): z.writestr(name,data)
    raw=p.read_bytes()
    archive=Archive(str(p),ArtifactPin(1,1,len(raw),hashlib.sha256(raw).hexdigest(),"resolver.zip")).open()
    try:
        root={"folder":folder,"source_sha":S6_SOURCE,"cohort_id":S6_COHORT,"scenario_id":"C030_G000","trial_id":156,
              "trial_fingerprint":"a"*64,"status":"PASS_SCOPED_REPRESENTATIVE_FULL_LOGGING",
              "trial_manifest_sha256":hashlib.sha256(members[base+"trial_manifest.json"]).hexdigest(),
              "post_write_audit_sha256":hashlib.sha256(members[base+"post_write_audit.json"]).hexdigest()}
        resolved=resolve_trial_manifest(archive,root,"stagec-output/full_logging",
            {"source_sha":S6_SOURCE,"cohort_id":S6_COHORT,"scenario_id":"C030_G000","trial_id":156})
        assert resolved["normalized_audit_status"]=="PASS_SCOPED_REPRESENTATIVE_FULL_LOGGING"
        assert resolved["trial_manifest_size_bytes"]==len(members[base+"trial_manifest.json"])
        assert resolved["post_write_audit_size_bytes"]==len(members[base+"post_write_audit.json"])
    finally:
        archive.close()


def test_manifest_resolver_rejects_root_hash_mismatch(tmp_path):
    import json
    from scripts.s6_manifest_resolver import resolve_trial_manifest
    folder="C030_G000__trial_000156"; base=f"stagec-output/full_logging/{folder}/"
    trial={"source_sha":S6_SOURCE,"cohort_id":S6_COHORT,"scenario_id":"C030_G000","trial_id":156,
           "actual_trial_fingerprint":"a"*64,"expected_trial_fingerprint":"a"*64}
    audit={"status":"PASS_SCOPED_REPRESENTATIVE_FULL_LOGGING","trial_fingerprint":"a"*64,
           "trial_fingerprint_match":True,"rollforward_mismatch_count":0,"balance_mismatch_count":0}
    result={"trial_fingerprint":"a"*64}
    members={base+"trial_manifest.json":json.dumps(trial).encode(),base+"post_write_audit.json":json.dumps(audit).encode(),
             base+"trial_result.json":json.dumps(result).encode()}
    p=tmp_path/"resolver.zip"
    with zipfile.ZipFile(p,"w") as z:
        for name,data in members.items(): z.writestr(name,data)
    raw=p.read_bytes(); archive=Archive(str(p),ArtifactPin(1,1,len(raw),hashlib.sha256(raw).hexdigest(),"resolver.zip")).open()
    try:
        root={"folder":folder,"trial_fingerprint":"a"*64,"trial_manifest_sha256":"0"*64,
              "post_write_audit_sha256":hashlib.sha256(members[base+"post_write_audit.json"]).hexdigest()}
        resolved=resolve_trial_manifest(archive,root,"stagec-output/full_logging")
        assert resolved["normalized_audit_status"]=="NOT_VERIFIED"
        assert "ROOT_MANIFEST_SHA256_MISMATCH" in resolved["reasons"]
    finally:
        archive.close()
