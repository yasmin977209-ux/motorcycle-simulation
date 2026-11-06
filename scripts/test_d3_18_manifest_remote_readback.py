#!/usr/bin/env python3
"""Actual D3-18 invocation: exact-commit GitHub Raw readback for manifests and workbook deliverables."""
from __future__ import annotations
import hashlib, json, os, pathlib, requests, subprocess, sys

TEST_ID="D3-18-EXACT-HEAD-MANIFEST-RAW-READBACK-2026-11-06"
REQUIRED=(
 "deliverables/Full_Results_EN.xlsx",
 "deliverables/النتائج_الكاملة_AR.xlsx",
 "deliverables/D3_BUILD_AUDIT.json",
 "deliverables/D3_MANIFEST.json",
 "docs/stage_d/D3_18_INVOCATION_RECONCILIATION_2026-11-05.json",
)

def git_blob_sha1(raw:bytes)->str:
 return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()

def main():
 repo=os.environ["GITHUB_REPOSITORY"]
 branch="tmp/d1-rebuild-20261101"
 tested_sha=os.environ["GITHUB_SHA"]
 run_id=int(os.environ["GITHUB_RUN_ID"])
 token=os.environ["GITHUB_TOKEN"]
 headers={"Authorization":"Bearer "+token,"Accept":"application/vnd.github+json"}
 api=f"https://api.github.com/repos/{repo}"
 branch_ref=requests.get(f"{api}/git/ref/heads/{branch}",headers=headers,timeout=45)
 branch_ref.raise_for_status()
 live_head=branch_ref.json()["object"]["sha"]
 if live_head!=tested_sha:
  raise SystemExit(f"D3_18_BRANCH_HEAD_MISMATCH:{live_head}:{tested_sha}")
 jobs=requests.get(f"{api}/actions/runs/{run_id}/jobs",headers=headers,timeout=45)
 jobs.raise_for_status()
 job=next((j for j in jobs.json().get("jobs",[]) if j.get("name")=="D3-18 Manifest and Exact-HEAD Raw Readback"),None)
 if job is None: raise SystemExit("D3_18_CURRENT_JOB_ID_NOT_RESOLVED")
 results=[]
 for rel in REQUIRED:
  p=pathlib.Path(rel)
  if not p.is_file(): raise SystemExit("D3_18_REQUIRED_LOCAL_FILE_MISSING:"+rel)
  local=p.read_bytes()
  url=f"https://raw.githubusercontent.com/{repo}/{tested_sha}/"+requests.utils.quote(rel,safe="/")
  response=requests.get(url,headers={"Authorization":"Bearer "+token},timeout=(45,300))
  response.raise_for_status()
  remote=response.content
  if remote!=local: raise SystemExit("D3_18_RAW_BYTES_MISMATCH:"+rel)
  digest=hashlib.sha256(remote).hexdigest()
  blob=git_blob_sha1(remote)
  results.append({"path":rel,"url":url,"bytes":len(remote),"sha256":digest,"git_blob_sha1":blob,"commit_sha":tested_sha,"byte_equal_local":True})
  print(f"D3_18_VERIFIED_RAW path={rel} bytes={len(remote)} sha256={digest} blob_sha1={blob} commit={tested_sha}",flush=True)
 # Validate the JSON evidence records are parseable and preserve the scoped gate.
 for rel in ("deliverables/D3_BUILD_AUDIT.json","deliverables/D3_MANIFEST.json","docs/stage_d/D3_18_INVOCATION_RECONCILIATION_2026-11-05.json"):
  json.loads(pathlib.Path(rel).read_text(encoding="utf-8"))
 branch_ref=requests.get(f"{api}/git/ref/heads/{branch}",headers=headers,timeout=45)
 branch_ref.raise_for_status()
 final_head=branch_ref.json()["object"]["sha"]
 if final_head!=tested_sha: raise SystemExit(f"D3_18_FINAL_HEAD_MOVED:{final_head}:{tested_sha}")
 report={"schema_version":"d3-18-exact-head-raw-readback-v1","classification":"PASS_SCOPED",
  "test_id":TEST_ID,"workflow_run_id":run_id,"job_id":job["id"],"tested_sha":tested_sha,
  "branch":branch,"initial_live_head":live_head,"final_live_head":final_head,"required_file_count":len(results),
  "files":results,"limitations":["This invocation verifies exact-commit manifest/workbook GitHub Raw readback only. It does not close D3-S or overall D3, and does not establish permanent artifact retention."]}
 out=pathlib.Path("d3-18-output"); out.mkdir(exist_ok=True)
 (out/"D3_18_ACTUAL_INVOCATION_2026-11-06.json").write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"classification":report["classification"],"test_id":TEST_ID,"run_id":run_id,"job_id":job["id"],"tested_sha":tested_sha,"files":len(results)},sort_keys=True),flush=True)

if __name__=="__main__": main()
