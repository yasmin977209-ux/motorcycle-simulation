#!/usr/bin/env python3
"""Hash exact GitHub Artifact ZIPs for D3S-010 and the 20 multipart OneDrive objects."""
from __future__ import annotations
import argparse,hashlib,json,os,pathlib,sys,tempfile,zipfile
from pathlib import Path
import requests
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.verify_tri_hash_preservation_bridge import HashEngine
REPO="yasmin977209-ux/motorcycle-simulation"
TARGETS=[
("D3S-010.transport.zip",13541174824,42295053851),
("D1-000.transport.zip",13531109443,42274900045),("D1-001.transport.zip",13531139384,42274900045),
("D1-002.transport.zip",13530959565,42274900045),("D1-003.transport.zip",13530954627,42274900045),
("D1-RESTORE-MANIFEST.transport.zip",13530829722,42274900045),
("D3-000.transport.zip",13530847772,42273360334),("D3-001.transport.zip",13531347485,42273360334),
("D3-002.transport.zip",13531037648,42273360334),("D3-003.transport.zip",13531552090,42273360334),
("D3-004.transport.zip",13531537218,42273360334),("D3-005.transport.zip",13530997846,42273360334),
("D3-006.transport.zip",13531222587,42273360334),
("D5-000.transport.zip",13531122727,42273360334),("D5-001.transport.zip",13531212556,42273360334),
("D5-002.transport.zip",13531262474,42273360334),("D5-003.transport.zip",13531037720,42273360334),
("D5-004.transport.zip",13531562213,42273360334),("D5-005.transport.zip",13531127658,42273360334),
("D5-006.transport.zip",13531342529,42273360334),("RESTORE-MANIFEST.transport.zip",13530877847,42273360334)]
STAGE_A=(13557202516,42330906466,11125,"a785c6bc51f9427c9e728a94797829eb4cf83ab33fc6509e1e49a6a1044d3b25")
def get_artifact(s,h,aid,p):
 r=s.get(f"https://api.github.com/repos/{REPO}/actions/artifacts/{aid}",headers=h,timeout=(30,90));r.raise_for_status();m=r.json()
 if m.get("expired"):raise RuntimeError("ARTIFACT_EXPIRED:"+str(aid))
 with s.get(f"https://api.github.com/repos/{REPO}/actions/artifacts/{aid}/zip",headers=h,stream=True,timeout=(60,900)) as d:
  d.raise_for_status()
  with p.open("wb") as f:
   for b in d.iter_content(4*1024*1024):
    if b:f.write(b)
 return m
def inner_hashes(p,engine,work):
 out=[]
 with zipfile.ZipFile(p) as z:
  infos=[i for i in z.infolist() if not i.is_dir()]
  if z.testzip():raise RuntimeError("ZIP_CRC_FAILURE:"+p.name)
  if len({i.filename for i in infos})!=len(infos):raise RuntimeError("ZIP_DUPLICATE_MEMBER:"+p.name)
  for i,info in enumerate(infos):
   dest=work/(p.stem+"-inner-"+str(i))
   with z.open(info) as src,dest.open("wb") as dst:
    while True:
     b=src.read(8*1024*1024)
     if not b:break
     dst.write(b)
   h=engine.file(dest);dest.unlink()
   out.append({"member_name":info.filename,"inner_member_size":h["size"],
    "inner_member_sha256":h["sha256"],"inner_member_quickxorhash_base64":h["onedrive_quickxorhash"]})
 return out
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--ledger",required=True);ap.add_argument("--output",required=True);a=ap.parse_args()
 token=os.environ.get("GITHUB_TOKEN","")
 if not token:raise SystemExit("GITHUB_TOKEN_REQUIRED")
 engine=HashEngine(os.environ.get("QUICKXOR_LIB","/tmp/libquickxorhash.so"))
 ledger=json.loads(Path(a.ledger).read_text(encoding="utf-8"));byname={x["name"]:x for x in ledger["records"]}
 headers={"Authorization":"Bearer "+token,"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"}
 s=requests.Session();rows=[]
 with tempfile.TemporaryDirectory(prefix="multipart-ref-") as td:
  work=Path(td);aid,run,size,sha=STAGE_A;p=work/"stage-a.zip";m=get_artifact(s,headers,aid,p);h=engine.file(p)
  if m.get("workflow_run",{}).get("id")!=run or h["size"]!=size or h["sha256"]!=sha:raise RuntimeError("STAGE_A_PIN_MISMATCH")
  stage={"run_id":run,"artifact_id":aid,"outer_zip_size":h["size"],"outer_zip_sha256":h["sha256"],
   "outer_zip_quickxorhash_base64":h["onedrive_quickxorhash"]}
  print("STAGE_A_REFERENCE "+json.dumps(stage,sort_keys=True))
  for name,aid,run in TARGETS:
   rec=byname[name]
   p=work/(str(aid)+".zip");m=get_artifact(s,headers,aid,p)
   if m.get("workflow_run",{}).get("id")!=run:raise RuntimeError("ARTIFACT_RUN_MISMATCH:"+str(aid))
   h=engine.file(p)
   if h["size"]!=int(m["size_in_bytes"]) or m.get("digest")!="sha256:"+h["sha256"]:raise RuntimeError("GITHUB_ARTIFACT_HASH_MISMATCH:"+str(aid))
   members=inner_hashes(p,engine,work)
   match=h["size"]==int(rec["bytes"]) and h["onedrive_quickxorhash"]==rec["provider_hash"]
   row={"name":name,"run_id":run,"artifact_id":aid,"artifact_name":m["name"],"artifact_digest":m["digest"],
    "outer_zip_size":h["size"],"outer_zip_sha256":h["sha256"],"outer_zip_quickxorhash_base64":h["onedrive_quickxorhash"],
    "inner_members":members,"onedrive_item_id":rec["provider_item_id"],"onedrive_recorded_size":rec["bytes"],
    "onedrive_recorded_quickxorhash_base64":rec["provider_hash"],"provider_metadata_match":match,
    "provider_metadata_disposition":"MATCH" if match else "MISMATCH"}
   rows.append(row);print("REFERENCE_21 "+json.dumps(row,sort_keys=True));p.unlink()
 if len(rows)!=21:raise RuntimeError("REFERENCE_COUNT_NOT_21")
 old=sum(x["provider"]=="OneDrive" and x["metadata_disposition"]=="MATCH" for x in ledger["records"])
 drop=sum(x["provider"]=="Dropbox" and x["metadata_disposition"]=="MATCH" for x in ledger["records"])
 good=sum(x["provider_metadata_match"] for x in rows);new={x["name"]:x for x in rows};full=[]
 for rec in ledger["records"]:
  x={"name":rec["name"],"provider":rec["provider"],"size":rec["bytes"],"provider_hash":rec["provider_hash"]}
  if rec["name"] in new:
   y=new[rec["name"]];x.update({"reference_sha256":y["outer_zip_sha256"],"reference_quickxorhash_base64":y["outer_zip_quickxorhash_base64"],
    "provider_metadata_match":y["provider_metadata_match"],"disposition":y["provider_metadata_disposition"]})
  elif rec["provider"]=="OneDrive" and rec["metadata_disposition"]=="MATCH":x.update({"provider_metadata_match":True,"disposition":"VERIFIED_LIVE_PRIOR"})
  elif rec["provider"]=="Dropbox" and rec["metadata_disposition"]=="MATCH":x.update({"provider_metadata_match":None,"disposition":"REPORTED_ONLY_DROPBOX_HASH_NOT_RECHECKED"})
  else:x.update({"provider_metadata_match":None,"disposition":"NOT_COMPARABLE"})
  full.append(x)
 report={"schema_version":"multipart-21-reference-hash-report-v1","tested_sha":os.environ.get("GITHUB_SHA","UNKNOWN"),
  "workflow_run_id":int(os.environ.get("GITHUB_RUN_ID","0")),"stage_a_artifact":stage,"reference_count":21,"references":rows,"ledger_72":full,
  "counts":{"total":72,"onedrive_provider_metadata_match":old+good,"newly_compared_21":good,"dropbox_reported_only":drop,
   "mismatch":sum(not x["provider_metadata_match"] for x in rows),"not_comparable":sum(x["disposition"]=="NOT_COMPARABLE" for x in full)},
  "raw_byte_hash_match":"NOT_RUN","restore_verified":"NOT_RUN","e2_replay_20":"NOT_TRANSFERRED",
  "global_preservation_status":"BLOCKED","final_acceptance":"NOT_ACCEPTED"}
 Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
 print("REFERENCE_HASH_REPORT_BEGIN");print(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2));print("REFERENCE_HASH_REPORT_END")
 if report["counts"]["mismatch"] or report["counts"]["onedrive_provider_metadata_match"]!=63:raise SystemExit("PROVIDER_METADATA_MATCH_GATE_FAILED")
 print("PROVIDER_METADATA_MATCH=63/72 (63 OneDrive verified; 9 Dropbox REPORTED_ONLY)")
if __name__=="__main__":main()
