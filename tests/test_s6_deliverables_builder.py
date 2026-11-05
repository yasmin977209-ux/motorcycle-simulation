undefined
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

