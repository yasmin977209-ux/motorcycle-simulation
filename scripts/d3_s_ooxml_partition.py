#!/usr/bin/env python3
"""Surgical OOXML partitioning and byte-exact worksheet reassembly for D3-S."""
from __future__ import annotations
import argparse, copy, hashlib, json, os, pathlib, posixpath, re, shutil, subprocess, tempfile, zipfile
from lxml import etree
from openpyxl import load_workbook

NS={
 "main":"http://schemas.openxmlformats.org/spreadsheetml/2006/main",
 "r":"http://schemas.openxmlformats.org/officeDocument/2006/relationships",
 "rel":"http://schemas.openxmlformats.org/package/2006/relationships",
 "ct":"http://schemas.openxmlformats.org/package/2006/content-types",
}
COLLECTIONS=("C030","C050","C070","C085","C100")
RECOVERIES=("G000","G030","G050","G070","G100")
SCENARIO_RE=re.compile(r"^(C\d{3})_(G\d{3})(?:_|$)")
EXPECTED_SHEETS=185
EXPECTED_SCENARIO_SHEETS=175
EXPECTED_SHARED_SHEETS=10
PARSER=etree.XMLParser(resolve_entities=False,no_network=True,remove_blank_text=False,huge_tree=True)

def sha(data:bytes)->str: return hashlib.sha256(data).hexdigest()
def file_sha(p:pathlib.Path)->str:
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
 return h.hexdigest()
def xml_bytes(root)->bytes:
 return etree.tostring(root,xml_declaration=True,encoding="UTF-8",standalone=True)
def rel_target(base_file:str,target:str)->str:
 if target.startswith("/"): return posixpath.normpath(target.lstrip("/"))
 return posixpath.normpath(posixpath.join(posixpath.dirname(base_file),target))
def rels_part(part:str)->str:
 d,n=posixpath.split(part)
 return posixpath.join(d,"_rels",n+".rels")
def rel_target_from_part(part:str,target:str)->str:
 return rel_target(part,target)

def load_package(source:pathlib.Path):
 with zipfile.ZipFile(source) as z:
  names=z.namelist()
  if len(names)!=len(set(names)): raise RuntimeError("SOURCE_ZIP_DUPLICATE_MEMBERS")
  bad=z.testzip()
  if bad: raise RuntimeError("SOURCE_ZIP_CRC_FAILURE:"+bad)
  if any(n.startswith("_xmlsignatures/") for n in names): raise RuntimeError("SIGNED_OOXML_PACKAGE_REQUIRES_SIGNATURE_POLICY")
  wb=etree.fromstring(z.read("xl/workbook.xml"),PARSER)
  relroot=etree.fromstring(z.read("xl/_rels/workbook.xml.rels"),PARSER)
  ct=etree.fromstring(z.read("[Content_Types].xml"),PARSER)
  relmap={}
  for r in relroot.findall("rel:Relationship",NS):
   relmap[r.get("Id")]=r
  sheets=[]
  for idx,s in enumerate(wb.findall("main:sheets/main:sheet",NS)):
   rid=s.get("{%s}id"%NS["r"])
   if rid not in relmap: raise RuntimeError("WORKBOOK_SHEET_RELATIONSHIP_MISSING:"+str(s.get("name")))
   target=relmap[rid].get("Target")
   part=rel_target("xl/workbook.xml",target)
   if part not in names: raise RuntimeError("WORKSHEET_PART_MISSING:"+part)
   sheets.append({"index":idx,"name":s.get("name"),"sheet_id":s.get("sheetId"),"rid":rid,"part":part})
  return names,wb,relroot,ct,relmap,sheets

def classify(sheets,lang,source):
 scenarios={}; shared=[]; mapping={}
 if len(sheets)!=EXPECTED_SHEETS: raise RuntimeError(f"SHEET_COUNT_MISMATCH:{len(sheets)}")
 with zipfile.ZipFile(source) as z:
  for s in sheets:
   m=SCENARIO_RE.match(s["name"])
   if m:
    c,g=m.group(1),m.group(2)
    if c not in COLLECTIONS or g not in RECOVERIES: raise RuntimeError("UNEXPECTED_SCENARIO_SHEET:"+s["name"])
    sid=f"{c}_{g}"; scenarios.setdefault(sid,[]).append(s["name"])
    cls="scenario_specific"
   else:
    shared.append(s["name"]); c=g=sid=None; cls="shared_supporting"
   part=etree.fromstring(z.read(s["part"]),PARSER)
   view=part.find("main:sheetViews/main:sheetView",NS)
   rtl=(view is not None and view.get("rightToLeft") in ("1","true","True"))
   expected=(lang=="AR")
   if rtl!=expected: raise RuntimeError(f"SHEET_DIRECTION_MISMATCH:{lang}:{s['name']}:rtl={rtl}")
   mapping[s["name"]]={"source_index":s["index"],"classification":cls,"scenario_id":sid,"collection":c,"recovery":g,"worksheet_part":s["part"],"worksheet_sha256":sha(z.read(s["part"]))}
 expected_ids={f"{c}_{g}" for c in COLLECTIONS for g in RECOVERIES}
 if set(scenarios)!=expected_ids or len(scenarios)!=25: raise RuntimeError("SCENARIO_MATRIX_NOT_25_OF_25")
 if len(shared)!=EXPECTED_SHARED_SHEETS or sum(map(len,scenarios.values()))!=EXPECTED_SCENARIO_SHEETS:
  raise RuntimeError(f"SHEET_CLASSIFICATION_MISMATCH:scenario={sum(map(len,scenarios.values()))}:shared={len(shared)}")
 for sid,ns in scenarios.items():
  if len(ns)!=7: raise RuntimeError("SCENARIO_SHEET_CARDINALITY_NOT_7:"+sid)
 return scenarios,shared,mapping

def build_partition(source:pathlib.Path,out:pathlib.Path,lang:str,collection:str,source_meta):
 names,wb,rels,ct,relmap,sheets=source_meta[:6]
 wb=copy.deepcopy(wb); rels=copy.deepcopy(rels); ct=copy.deepcopy(ct)
 relmap={r.get('Id'):r for r in rels.findall('rel:Relationship',NS)}
 scenarios,shared,mapping=source_meta[6]
 kept=[s for s in sheets if s["name"] in shared or (mapping[s["name"]]["collection"]==collection)]
 removed=[s for s in sheets if s not in kept]
 kept_names={s["name"] for s in kept}
 old_to_new={s["index"]:i for i,s in enumerate(kept)}
 # Drop local defined names bound to excluded sheets and remap retained localSheetId values.
 dns=wb.find("main:definedNames",NS)
 if dns is not None:
  for dn in list(dns):
   local=dn.get("localSheetId")
   if local is not None:
    old=int(local)
    if old not in old_to_new: dns.remove(dn)
    else: dn.set("localSheetId",str(old_to_new[old]))
   else:
    text_value="".join(dn.itertext())
    excluded=[s["name"] for s in removed if s["name"] in text_value]
    if excluded: raise RuntimeError("GLOBAL_DEFINED_NAME_REFERENCES_EXCLUDED_SHEET:"+dn.get("name","?")+":"+excluded[0])
 # Abort if retained formula XML refers to an excluded worksheet.
 removed_names={s["name"] for s in removed}
 with zipfile.ZipFile(source) as z:
  for s in kept:
   root=etree.fromstring(z.read(s["part"]),PARSER)
   for f in root.findall(".//main:f",NS):
    formula="".join(f.itertext())
    for name in removed_names:
     if name in formula: raise RuntimeError("CROSS_PARTITION_FORMULA_REFERENCE:"+s["name"]+":"+name)
 # Build filtered workbook + relationship + content-type documents.
 sheet_parent=wb.find("main:sheets",NS)
 for el in list(sheet_parent):
  if el.get("name") not in kept_names: sheet_parent.remove(el)
 for s in removed:
  rels.remove(relmap[s["rid"]])
 # calcChain contains sheet references for removed sheets; omit it from each derived workbook.
 calc_targets=[]
 for r in list(rels):
  typ=r.get("Type","")
  if typ.endswith("/calcChain"):
   calc_targets.append(rel_target("xl/workbook.xml",r.get("Target")))
   rels.remove(r)
 for target in calc_targets:
  pass
 for override in list(ct):
  if override.tag=="{%s}Override"%NS["ct"]:
   part=override.get("PartName","").lstrip("/")
   if part in {s["part"] for s in removed} or part in calc_targets: ct.remove(override)
 remove_parts={s["part"] for s in removed}
 remove_parts.update(rels_part(s["part"]) for s in removed)
 remove_parts.update(calc_targets)
 remove_parts={p for p in remove_parts if p in names}
 # Use Info-ZIP to retain compressed bytes of all unchanged package parts.
 shutil.copy2(source,out)
 out=out.resolve()
 with tempfile.TemporaryDirectory(prefix="d3s-ooxml-") as td:
  td=pathlib.Path(td); (td/"xl").mkdir()
  (td/"xl/workbook.xml").write_bytes(xml_bytes(wb))
  (td/"xl/_rels").mkdir(exist_ok=True)
  (td/"xl/_rels/workbook.xml.rels").write_bytes(xml_bytes(rels))
  (td/"[Content_Types].xml").write_bytes(xml_bytes(ct))
  if remove_parts:
   subprocess.run(["zip","-q","-d",str(out),*sorted(remove_parts)],check=True,capture_output=True)
  subprocess.run(["zip","-q","-u",str(out),"xl/workbook.xml","xl/_rels/workbook.xml.rels","[Content_Types].xml"],cwd=td,check=True,capture_output=True)
 with zipfile.ZipFile(out) as z:
  bad=z.testzip()
  if bad: raise RuntimeError("PARTITION_ZIP_CRC_FAILURE:"+bad)
  if "xl/sharedStrings.xml" in names and sha(z.read("xl/sharedStrings.xml"))!=source_meta[7]["shared_strings_sha256"]: raise RuntimeError("SHARED_STRINGS_CHANGED")
  if "xl/styles.xml" in names and sha(z.read("xl/styles.xml"))!=source_meta[7]["styles_sha256"]: raise RuntimeError("STYLES_CHANGED")
 # openpyxl verifies each derived workbook opens and presents the intended sheet list.
 check=load_workbook(out,read_only=True,data_only=False,keep_links=True)
 if check.sheetnames!=[s["name"] for s in kept]: raise RuntimeError("OPENPYXL_PARTITION_SHEETLIST_MISMATCH:"+collection)
 check.close()
 return {"filename":out.name,"bytes":out.stat().st_size,"sha256":file_sha(out),"sheet_count":len(kept),"sheet_names":[s["name"] for s in kept],"scenario_ids":[f"{collection}_{g}" for g in RECOVERIES],"shared_sheet_count":len(shared)}

def reassemble(source:pathlib.Path,outdir:pathlib.Path,lang:str,parts,source_meta):
 names,wb,rels,ct,relmap,sheets=source_meta[:6]
 mapping=source_meta[6][2]
 assembled_dir=outdir/"_verification"; assembled_dir.mkdir(exist_ok=True)
 assembled=assembled_dir/f"{lang}_reassembled.xlsx"
 shutil.copy2(source,assembled)
 assembled=assembled.resolve()
 all_sheet_parts={s["part"] for s in sheets}
 all_sheet_rels={rels_part(s["part"]) for s in sheets}
 with zipfile.ZipFile(source) as src:
  source_names=set(src.namelist())
  remove_parts=sorted((all_sheet_parts|all_sheet_rels)&source_names)
 # Remove every original worksheet and its relationship part, then rebuild those parts only from partition outputs.
 if remove_parts:
  subprocess.run(["zip","-q","-d",str(assembled),*remove_parts],check=True,capture_output=True)
 with tempfile.TemporaryDirectory(prefix="d3s-reassemble-") as td:
  td=pathlib.Path(td); add_members=[]
  for s in sheets:
   info=mapping[s["name"]]
   owner=info["collection"] if info["classification"]=="scenario_specific" else COLLECTIONS[0]
   part_file=outdir/parts[owner]["filename"]
   to_add=[s["part"]]
   rp=rels_part(s["part"])
   if rp in source_names: to_add.append(rp)
   with zipfile.ZipFile(part_file) as z:
    for member in to_add:
     target=td/member; target.parent.mkdir(parents=True,exist_ok=True)
     target.write_bytes(z.read(member))
     add_members.append(member)
  subprocess.run(["zip","-q","-u",str(assembled),*add_members],cwd=td,check=True,capture_output=True)
 with zipfile.ZipFile(source) as src, zipfile.ZipFile(assembled) as rebuilt:
  for s in sheets:
   if sha(src.read(s["part"]))!=sha(rebuilt.read(s["part"])): raise RuntimeError("REASSEMBLY_WORKSHEET_BYTE_MISMATCH:"+s["name"])
   rp=rels_part(s["part"])
   if rp in source_names and src.read(rp)!=rebuilt.read(rp): raise RuntimeError("REASSEMBLY_WORKSHEET_RELATIONSHIP_MISMATCH:"+s["name"])
  for part in ("xl/sharedStrings.xml","xl/styles.xml","xl/workbook.xml","xl/_rels/workbook.xml.rels","[Content_Types].xml"):
   if part in src.namelist() and src.read(part)!=rebuilt.read(part): raise RuntimeError("REASSEMBLY_GLOBAL_PART_MISMATCH:"+part)
  bad=rebuilt.testzip()
  if bad: raise RuntimeError("REASSEMBLY_ZIP_CRC_FAILURE:"+bad)
 check=load_workbook(assembled,read_only=True,data_only=False,keep_links=True)
 if check.sheetnames!=[s["name"] for s in sheets]: raise RuntimeError("REASSEMBLY_OPENPYXL_SHEETLIST_MISMATCH")
 check.close()
 return {"status":"PASS_SCOPED_BYTE_EXACT_WORKSHEET_REASSEMBLY","sheet_count":len(sheets),"worksheet_parts_byte_exact":len(sheets),"openpyxl_open":"PASS","bytes":assembled.stat().st_size,"sha256":file_sha(assembled)}

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--source",required=True); p.add_argument("--lang",choices=("EN","AR"),required=True); p.add_argument("--outdir",required=True)
 a=p.parse_args(); source=pathlib.Path(a.source); outdir=pathlib.Path(a.outdir); outdir.mkdir(parents=True,exist_ok=True)
 if not source.is_file(): raise SystemExit("SOURCE_WORKBOOK_MISSING")
 names,wb,rels,ct,relmap,sheets=load_package(source)
 scenarios,shared,mapping=classify(sheets,a.lang,source)
 with zipfile.ZipFile(source) as z:
  shared_meta={"shared_strings_sha256":sha(z.read("xl/sharedStrings.xml")) if "xl/sharedStrings.xml" in names else None,
               "styles_sha256":sha(z.read("xl/styles.xml")) if "xl/styles.xml" in names else None}
 source_meta=(names,wb,rels,ct,relmap,sheets, (scenarios,shared,mapping), shared_meta)
 parts={}
 for c in COLLECTIONS:
  out=outdir/f"{a.lang}_{c}.xlsx"
  parts[c]=build_partition(source,out,a.lang,c,source_meta)
  print(json.dumps({"event":"PARTITION_WRITTEN","lang":a.lang,"collection":c,**parts[c]},ensure_ascii=False,sort_keys=True),flush=True)
 reassembly=reassemble(source,outdir,a.lang,parts,source_meta)
 coverage={c:[f"{c}_{g}" for g in RECOVERIES] for c in COLLECTIONS}
 if sum(len(v) for v in coverage.values())!=25: raise RuntimeError("SCENARIO_COVERAGE_NOT_25")
 manifest={"schema_version":"d3-s-surgical-ooxml-v1","classification":"PASS_SCOPED","language":a.lang,
  "source":{"filename":source.name,"bytes":source.stat().st_size,"sha256":file_sha(source),"sheet_count":len(sheets)},
  "partition_count":5,"partitions":parts,"sheet_mapping":mapping,"scenario_coverage_matrix":coverage,
  "shared_sheets":shared,"shared_strings_sha256":shared_meta["shared_strings_sha256"],"styles_sha256":shared_meta["styles_sha256"],
  "reassembly":reassembly,"limitations":["Derived partitions preserve original worksheet XML bytes and sharedStrings/styles; unsupported cross-partition formulas or signed OOXML packages abort rather than being rewritten."]}
 (outdir/f"D3_S_{a.lang}_MANIFEST.json").write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
 (outdir/f"D3_S_{a.lang}_SHEET_MAPPING.json").write_text(json.dumps(mapping,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
 (outdir/f"D3_S_{a.lang}_SCENARIO_COVERAGE.json").write_text(json.dumps(coverage,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
 sums=[]
 for f in sorted(outdir.glob("*.xlsx")):
  if "reassembled" not in f.name: sums.append(f"{file_sha(f)}  {f.name}")
 (outdir/"SHA256SUMS.txt").write_text("\n".join(sums)+"\n",encoding="utf-8")
 print(json.dumps({"event":"LANGUAGE_COMPLETE","lang":a.lang,"status":"PASS_SCOPED","partitions":5,"scenario_coverage":"25/25","reassembly":reassembly},sort_keys=True),flush=True)

if __name__=="__main__": main()
