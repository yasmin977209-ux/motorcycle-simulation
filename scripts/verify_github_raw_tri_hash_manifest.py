#!/usr/bin/env python3
"""Stage A: hash original GitHub Actions artifact ZIP bytes without provider credentials."""
from __future__ import annotations
import argparse, base64, ctypes, hashlib, json, os, struct, tempfile, zipfile
from pathlib import Path
import requests

REPO = "yasmin977209-ux/motorcycle-simulation"
ARTIFACT_IDS = {
  "S6_RUN_40731224990": [12842976168,12842638708,12842495430,12842099758,12840482357,12840360793,12840210926,12839945046,12839875625,12839361726,12839102296,12839062393,12839053751,12838992458,12838987686,12838354545,12838339633,12838242824,12838164871,12836747552],
  "D3S_PROVIDER_OBJECTS_RUN_42295053851": [13542313112,13542996274,13542377114,13541793113,13541323505,13541753217,13542377163,13542486944,13541858064,13541629124,13541174824,13541898760,13543020271,13541389295,13541484157,13541414258,13543015359,13541484188,13543105044,13541988784,13541569332,13542691802,13542068569],
  "D1_D3_D5_MULTIPART_PROVIDER_OBJECTS": [13530847772,13531347485,13531037648,13531552090,13531537218,13530997846,13531222587,13531122727,13531212556,13531262474,13531037720,13531562213,13531127658,13531342529,13530877847,13531109443,13531139384,13530959565,13530954627,13530829722],
  "DROPBOX_RESCUE_SOURCE_ARTIFACTS": [13382253631,13364064483,13288779998,13371094066,12998778418,13373853115,13369179742,12852969854,12630457193]
}
CHUNK=4*1024*1024

class HashEngine:
    def __init__(self, library):
        self.lib=ctypes.CDLL(library)
        self.update=self.lib.quickxor_update
        self.update.argtypes=[ctypes.POINTER(ctypes.c_ubyte),ctypes.c_void_p,ctypes.c_size_t,ctypes.c_uint64]
        self.update.restype=None
    def file(self,path):
        sha=hashlib.sha256(); qx=(ctypes.c_ubyte*20)(); outer=hashlib.sha256()
        pending=bytearray(); total=0
        with open(path,"rb") as f:
            while True:
                block=f.read(8*1024*1024)
                if not block: break
                sha.update(block)
                buf=ctypes.create_string_buffer(block)
                self.update(qx,ctypes.cast(buf,ctypes.c_void_p),len(block),total)
                total+=len(block); pending.extend(block)
                while len(pending)>=CHUNK:
                    outer.update(hashlib.sha256(pending[:CHUNK]).digest()); del pending[:CHUNK]
        if pending: outer.update(hashlib.sha256(pending).digest())
        elif total==0: outer.update(hashlib.sha256(b"").digest())
        for i,v in enumerate(struct.pack("<Q",total)): qx[12+i]^=v
        return {"size":total,"sha256":sha.hexdigest(),
                "quickxorhash_base64":base64.b64encode(bytes(qx)).decode("ascii"),
                "dropbox_content_hash_hex":outer.hexdigest()}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--quickxor-lib",default=os.environ.get("QUICKXOR_LIB","/tmp/libquickxorhash.so"))
    ap.add_argument("--output",default="GITHUB_RAW_TRI_HASH_MANIFEST_2026-11-07.json")
    args=ap.parse_args()
    token=os.environ.get("GITHUB_TOKEN","").strip()
    if not token: raise SystemExit("GITHUB_TOKEN_REQUIRED")
    session=requests.Session()
    headers={"Authorization":"Bearer "+token,"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"}
    engine=HashEngine(args.quickxor_lib)
    rows=[]; seen=set()
    with tempfile.TemporaryDirectory(prefix="github-raw-trihash-") as td:
        for group,ids in ARTIFACT_IDS.items():
            for aid in ids:
                if aid in seen: continue
                seen.add(aid)
                meta_r=session.get(f"https://api.github.com/repos/{REPO}/actions/artifacts/{aid}",headers=headers,timeout=(30,90))
                meta_r.raise_for_status(); meta=meta_r.json()
                if meta.get("expired"): raise RuntimeError(f"ARTIFACT_EXPIRED:{aid}")
                path=Path(td)/f"{aid}.zip"
                with session.get(f"https://api.github.com/repos/{REPO}/actions/artifacts/{aid}/zip",headers=headers,stream=True,timeout=(60,900)) as r:
                    r.raise_for_status()
                    with path.open("wb") as f:
                        for chunk in r.iter_content(4*1024*1024):
                            if chunk: f.write(chunk)
                hashes=engine.file(path)
                expected=str(meta.get("digest") or "")
                if hashes["size"] != int(meta["size_in_bytes"]):
                    raise RuntimeError(f"ARTIFACT_SIZE_MISMATCH:{aid}:{hashes['size']}:{meta['size_in_bytes']}")
                if expected != "sha256:"+hashes["sha256"]:
                    raise RuntimeError(f"ARTIFACT_SHA256_DIGEST_MISMATCH:{aid}:{expected}:{hashes['sha256']}")
                with zipfile.ZipFile(path,"r") as z:
                    names=z.namelist()
                    if len(names)!=len(set(names)): raise RuntimeError(f"ZIP_DUPLICATE_MEMBER:{aid}")
                    bad=z.testzip()
                    if bad: raise RuntimeError(f"ZIP_CRC_FAILURE:{aid}:{bad}")
                    members=len(names)
                rows.append({"artifact_id":aid,"artifact_name":meta["name"],"source_group":group,
                    "run_id":meta.get("workflow_run",{}).get("id"),"github_artifact_digest":expected,
                    **hashes,"zip_crc":"PASS","zip_member_count":members,"status":"VERIFIED_GITHUB_RAW"})
                path.unlink(missing_ok=True)
    result={"schema":"github-raw-tri-hash-manifest-v1","repository":REPO,
      "branch":"tmp/d1-rebuild-20261101","tested_sha":os.environ.get("GITHUB_SHA","UNKNOWN"),
      "workflow_run_id":int(os.environ.get("GITHUB_RUN_ID","0")),
      "provider_credentials_required":False,"provider_reads":"NOT_PERFORMED_BY_DESIGN",
      "hash_definitions":{"sha256":"SHA-256 over exact GitHub Artifact ZIP response bytes",
       "quickxorhash_base64":"Microsoft QuickXorHash over exact same bytes",
       "dropbox_content_hash_hex":"SHA-256(concat(SHA-256(each consecutive 4 MiB block)))"},
      "expected_inventory":{"s6_artifacts":20,"d3s_parts_and_manifest":23,"multipart_transport_objects":20,"dropbox_source_artifacts":9,"total_provider_objects":72},
      "unique_artifact_count":len(rows),"entries":rows,
      "overall":"PASS_GITHUB_RAW_HASHING_ONLY",
      "limitations":["Stage A downloads and hashes exact GitHub Actions Artifact ZIP bytes; it does not download provider bytes.",
       "The 72 provider objects are represented by matching GitHub Artifact ZIP IDs: 20 S6, 23 D3-S, 20 D1/D3/D5 multipart, and 9 Dropbox source artifacts.",
       "Stage B compares live OneDrive QuickXorHash/size and Dropbox content_hash/size against computed raw-byte hashes; metadata equality is not a provider raw-byte readback.",
       "E2 Replay 20 scenario archives remain a separate preservation set outside this 72-object scope."]}
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"overall":result["overall"],"tested_sha":result["tested_sha"],"run_id":result["workflow_run_id"],"artifacts":len(rows),"groups":{k:len(v) for k,v in ARTIFACT_IDS.items()}}))

if __name__=="__main__": main()
