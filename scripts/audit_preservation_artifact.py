#!/usr/bin/env python3
"""Independent raw-byte, ZIP restore, and Parquet audit for one immutable Actions Artifact."""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, re, shutil, stat, tempfile, zipfile
import requests
import duckdb

PARQUET_REQUIRED={"trials_summary.parquet","daily_distribution.parquet","daily_snapshots.parquet"}

def sha_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

def safe_member(name):
    if "\\" in name: raise RuntimeError("UNSAFE_ZIP_MEMBER_BACKSLASH:"+name)
    p=pathlib.PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts: raise RuntimeError("UNSAFE_ZIP_MEMBER_PATH:"+name)
    return p

def extract_checked(zf, destination):
    destination=pathlib.Path(destination); destination.mkdir(parents=True,exist_ok=True)
    members=[]; total=0
    for info in zf.infolist():
        p=safe_member(info.filename)
        if info.is_dir():
            (destination/pathlib.Path(*p.parts)).mkdir(parents=True,exist_ok=True)
            continue
        mode=(info.external_attr>>16)&0o170000
        if mode==stat.S_IFLNK: raise RuntimeError("ZIP_SYMLINK_MEMBER_BLOCKED:"+info.filename)
        target=destination/pathlib.Path(*p.parts); target.parent.mkdir(parents=True,exist_ok=True)
        h=hashlib.sha256(); count=0
        with zf.open(info,"r") as src, target.open("wb") as dst:
            for block in iter(lambda:src.read(1024*1024),b""):
                dst.write(block); h.update(block); count+=len(block)
        if count!=info.file_size: raise RuntimeError("RESTORE_SIZE_MISMATCH:"+info.filename)
        members.append({"name":info.filename,"bytes":count,"sha256":h.hexdigest()})
        total+=count
    return members,total

def extract_nested(root, max_depth=3):
    reports=[]; queue=[(pathlib.Path(root),0)]
    while queue:
        folder,depth=queue.pop(0)
        if depth>=max_depth: continue
        for zpath in sorted(folder.rglob("*.zip")):
            target=zpath.parent/(zpath.stem+"_restored")
            if target.exists(): continue
            with zipfile.ZipFile(zpath) as z:
                bad=z.testzip()
                if bad: raise RuntimeError("NESTED_ZIP_CRC_FAILURE:"+str(zpath)+":"+bad)
                members,total=extract_checked(z,target)
            reports.append({"archive":str(zpath.relative_to(root)),"crc":"PASS","member_count":len(members),"restored_bytes":total})
            queue.append((target,depth+1))
    return reports

def metadata_hash_audit(root):
    metadata_files=[p for p in pathlib.Path(root).rglob("*") if p.is_file() and p.name.lower().startswith("source_run_metadata") and p.suffix.lower() in (".json",".txt",".sha256")]
    expected=[]
    def scan(value, trail=""):
        if isinstance(value,dict):
            for k,v in value.items():
                kl=str(k).lower()
                if kl in ("source_run_metadata_sha256","source_run_metadata.sha256"):
                    if isinstance(v,str): expected.append(v.removeprefix("sha256:").lower())
                if kl=="source_run_metadata" and isinstance(v,dict):
                    for kk,vv in v.items():
                        if str(kk).lower()=="sha256" and isinstance(vv,str): expected.append(vv.removeprefix("sha256:").lower())
                scan(v,trail+"/"+str(k))
        elif isinstance(value,list):
            for i,v in enumerate(value): scan(v,trail+f"/{i}")
    json_files=list(pathlib.Path(root).rglob("*.json"))
    for p in json_files:
        try: scan(json.loads(p.read_text(encoding="utf-8")))
        except Exception: pass
    actual=[{"path":str(p.relative_to(root)),"bytes":p.stat().st_size,"sha256":sha_file(p)} for p in metadata_files]
    if not expected: return {"status":"MISSING_EVIDENCE","expected_sha256_values":[],"metadata_files":actual}
    matched=[]
    for e in expected:
        matched.extend([a for a in actual if a["sha256"]==e])
    return {"status":"PASS" if matched else "FAIL","expected_sha256_values":sorted(set(expected)),"metadata_files":actual,"matching_files":matched}

def parquet_audit(root, required):
    files=sorted(p for p in pathlib.Path(root).rglob("*.parquet") if p.is_file())
    basenames={p.name for p in files}
    missing=sorted(PARQUET_REQUIRED-basenames) if required else []
    reports=[]
    con=duckdb.connect(database=":memory:")
    try:
        for p in files:
            literal=str(p.resolve()).replace("'","''")
            relation=f"read_parquet('{literal}')"
            desc=con.execute(f"DESCRIBE SELECT * FROM {relation}").fetchall()
            columns=[{"name":r[0],"type":r[1]} for r in desc]
            rows=int(con.execute(f"SELECT COUNT(*) FROM {relation}").fetchone()[0])
            nulls={}
            for col in columns:
                q='"'+col["name"].replace('"','""')+'"'
                nulls[col["name"]]=int(con.execute(f"SELECT COUNT(*) FILTER (WHERE {q} IS NULL) FROM {relation}").fetchone()[0])
            distinct=int(con.execute(f"SELECT COUNT(*) FROM (SELECT DISTINCT * FROM {relation})").fetchone()[0])
            reports.append({"path":str(p.relative_to(root)),"bytes":p.stat().st_size,"schema":columns,"row_count":rows,"null_counts":nulls,"duplicate_row_count":rows-distinct,"partition_path_parts":list(p.relative_to(root).parts[:-1])})
    finally: con.close()
    if required and not files: status="MISSING_EVIDENCE"
    elif missing: status="MISSING_EVIDENCE"
    else: status="PASS_SCOPED"
    return {"status":status,"parquet_file_count":len(files),"required_basenames":sorted(PARQUET_REQUIRED) if required else [],"missing_required_basenames":missing,"files":reports}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--artifact-id",type=int,required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--expected-size",type=int,required=True)
    ap.add_argument("--expected-sha256",required=True)
    ap.add_argument("--require-parquet",action="store_true")
    ap.add_argument("--require-source-metadata",action="store_true")
    ap.add_argument("--output",default="audit-output")
    a=ap.parse_args()
    repo="yasmin977209-ux/motorcycle-simulation"
    token=os.environ["GITHUB_TOKEN"]
    headers={"Authorization":f"Bearer {token}","Accept":"application/vnd.github+json"}
    meta=requests.get(f"https://api.github.com/repos/{repo}/actions/artifacts/{a.artifact_id}",headers=headers,timeout=45)
    meta.raise_for_status(); m=meta.json()
    if m.get("expired") or m.get("size_in_bytes")!=a.expected_size or m.get("digest")!=f"sha256:{a.expected_sha256}":
        raise SystemExit("ARTIFACT_METADATA_PIN_MISMATCH")
    work=pathlib.Path(tempfile.mkdtemp(prefix=f"artifact-{a.artifact_id}-"))
    archive=work/"artifact.zip"
    response=requests.get(f"https://api.github.com/repos/{repo}/actions/artifacts/{a.artifact_id}/zip",headers=headers,stream=True,timeout=(45,240))
    response.raise_for_status(); h=hashlib.sha256(); n=0
    with archive.open("wb") as f:
        for block in response.iter_content(1024*1024):
            if block: f.write(block); h.update(block); n+=len(block)
    if n!=a.expected_size or h.hexdigest()!=a.expected_sha256:
        raise SystemExit(f"RAW_SHA256_MISMATCH:{n}:{h.hexdigest()}")
    restore=work/"restore"
    with zipfile.ZipFile(archive) as z:
        if len(z.namelist())!=len(set(z.namelist())): raise SystemExit("DUPLICATE_ZIP_MEMBERS")
        bad=z.testzip()
        if bad: raise SystemExit("OUTER_ZIP_CRC_FAILURE:"+bad)
        members,restored_bytes=extract_checked(z,restore)
    nested=extract_nested(restore)
    metadata=metadata_hash_audit(restore)
    parquet=parquet_audit(restore,a.require_parquet)
    report={
      "schema_version":"preservation-raw-artifact-audit-v1","artifact_id":a.artifact_id,"artifact_name":a.artifact_name,
      "source":{"url":f"https://github.com/{repo}/actions/runs/{m.get('workflow_run',{}).get('id','')}/artifacts/{a.artifact_id}","run_id":m.get("workflow_run",{}).get("id"),"expired":m.get("expired")},
      "raw_archive":{"bytes":n,"sha256":h.hexdigest(),"expected_sha256":a.expected_sha256,"sha256_match":True},
      "outer_zip":{"crc":"PASS","member_count":len(members),"restored_bytes":restored_bytes},
      "restore_test":{"status":"PASS","restored_member_count":len(members),"nested_archives":nested},
      "source_run_metadata_sha256":metadata,"parquet_audit":parquet,
      "classification":"PASS_SCOPED" if (metadata["status"]=="PASS" or (not a.require_source_metadata and metadata["status"]=="MISSING_EVIDENCE")) and parquet["status"] in ("PASS_SCOPED","NOT_PRESENT") else "BLOCKED",
      "limitations":["GitHub source bytes are audited here; this runner cannot independently read back OneDrive or Dropbox object bytes. Provider metadata/size matches are separate evidence."]
    }
    out=pathlib.Path(a.output); out.mkdir(parents=True,exist_ok=True)
    dest=out/f"ARTIFACT_{a.artifact_id}_AUDIT.json"
    dest.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"artifact_id":a.artifact_id,"classification":report["classification"],"bytes":n,"sha256":h.hexdigest(),"zip_crc":"PASS","restore":"PASS","parquet_status":parquet["status"],"metadata_sha256":metadata["status"]},sort_keys=True),flush=True)
    if report["classification"]!="PASS_SCOPED": raise SystemExit("PRESERVATION_AUDIT_BLOCKED")

if __name__=="__main__": main()
