from __future__ import annotations
import hashlib, io, json, os, zipfile
from pathlib import Path

REPORT=Path("docs/stage_d/D4_NUMERIC_TOKEN_LINEAGE_2026-11-07.json")
D4_REPORT_MANIFEST=Path("docs/stage_d/D4_REPORT_MANIFEST_2026-11-05.json")
D4_BUILD_AUDIT=Path("docs/stage_d/D4_BUILD_AUDIT_2026-11-05.json")
PACKAGE="Motorcycle_Simulation_D5_T2_INTERIM_2026-11-05.zip"
DOCX_NAMES={"التقرير_الكامل_AR.docx","Full_Report_EN.docx","الملخص_AR.docx","Summary_EN.docx","دراسة_الجدوى_AR.docx"}
def _sha(data): return hashlib.sha256(data).hexdigest()

def test_176_numeric_token_lineage():
 report=json.loads(REPORT.read_text(encoding="utf-8"))
 assert report["acceptance"]=="PASS"
 assert (report["total_occurrences"],report["resolved_occurrences"],report["explicitly_classified_occurrences"],report["unresolved_occurrences"])==(241,64,177,0)
 assert 241==64+177+0
 docs=report["documents"]
 assert {d["file"] for d in docs}==DOCX_NAMES
 assert sum(d["total_occurrences"] for d in docs)==241
 assert sum(d["resolved_occurrences"] for d in docs)==64
 assert sum(d["explicitly_classified_occurrences"] for d in docs)==177
 assert sum(d["unresolved_occurrences"] for d in docs)==0
 artifact_path=os.environ.get("D5_ARTIFACT_ZIP")
 if not artifact_path: return
 with zipfile.ZipFile(artifact_path) as outer:
  assert outer.testzip() is None
  assert set(outer.namelist())=={PACKAGE,"manifest.json","SHA256SUMS.txt"}
  package_bytes=outer.read(PACKAGE)
 with zipfile.ZipFile(io.BytesIO(package_bytes)) as package:
  assert package.testzip() is None
  assert len(package.namelist())==8
  payload={name:package.read(name) for name in package.namelist()}
 manifest=json.loads(payload["manifest.json"])
 d4raw=D4_REPORT_MANIFEST.read_bytes()
 d4manifest=json.loads(d4raw.decode("utf-8"))
 d4build=json.loads(D4_BUILD_AUDIT.read_text(encoding="utf-8"))
 inputs=manifest["inputs"]
 assert _sha(d4raw)==inputs["D4_report_manifest_sha256"]
 assert str(d4manifest["workflow_run_id"])==str(inputs["D4_source_run_id"])
 assert d4manifest["tested_sha"]==inputs["D4_tested_sha"]
 assert str(d4build["workflow_run_id"])==str(inputs["D4_source_run_id"])
 assert d4build["tested_sha"]==inputs["D4_tested_sha"]
 for doc in docs:
  name=doc["file"]; raw=payload[name]
  assert len(raw)==doc["bytes"]
  assert len(raw)==d4build["outputs"][name]["bytes"]
  assert _sha(raw)==d4build["outputs"][name]["sha256"]
  assert len(raw)==manifest["package_members"][name]["bytes"]
  assert _sha(raw)==manifest["package_members"][name]["sha256"]
