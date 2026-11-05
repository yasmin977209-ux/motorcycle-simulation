from __future__ import annotations
import argparse, hashlib, json, subprocess
from pathlib import Path
SOURCE_COMMIT="a23ba71f48487f3ebead99bc30039b14ef9b7609"
def main():
 p=argparse.ArgumentParser(); p.add_argument("--source-dir",required=True,type=Path); p.add_argument("--overlay-dir",required=True,type=Path); a=p.parse_args()
 src=a.source_dir.resolve(); out=a.overlay_dir.resolve()
 head=subprocess.check_output(["git","-C",str(src),"rev-parse","HEAD"],text=True).strip()
 if head!=SOURCE_COMMIT: raise SystemExit(f"REPLAY_SOURCE_COMMIT_MISMATCH:{head}")
 raw=(src/"monte_carlo.py").read_bytes(); text=raw.decode()
 if "def _daily_snapshot(" not in text or "balance_sheet_snapshot" in text: raise SystemExit("REPLAY_SOURCE_SNAPSHOT_PRECONDITION_FAILED")
 wrapper="""

# E2 instrumentation only: preserve the original model and append its already-computed balance snapshot.
import accounting as _e2_accounting
_e2_original_daily_snapshot = _daily_snapshot
def _daily_snapshot(project, current_date, trial_id):
    row = _e2_original_daily_snapshot(project, current_date, trial_id)
    row.update(_e2_accounting.balance_sheet_snapshot(project))
    row["daily_balance_schema_version"] = "s6-daily-balance-v1"
    return row
"""
 out.mkdir(parents=True,exist_ok=True); target=out/"monte_carlo.py"; target.write_text(text+wrapper,encoding="utf-8")
 m={"status":"PREPARED_INSTRUMENTATION_ONLY","replay_label":"REPLAY_RECONSTRUCTED_NOT_ORIGINAL_PRESERVED","source_execution_commit":SOURCE_COMMIT,"source_monte_carlo_sha256":hashlib.sha256(raw).hexdigest(),"source_monte_carlo_git_blob_sha1":hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest(),"overlay_monte_carlo_sha256":hashlib.sha256(target.read_bytes()).hexdigest(),"instrumentation":"wrap original _daily_snapshot; append accounting.balance_sheet_snapshot; no model/RNG/posting/timing/Trial logic edits"}
 (out/"replay_instrumentation_manifest.json").write_text(json.dumps(m,indent=2,sort_keys=True)+"\n"); print(json.dumps(m,sort_keys=True))
if __name__=="__main__": main()
