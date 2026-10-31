"""D2-ready exact registry normalizer; source publication only during D1."""
from __future__ import annotations
import json
from decimal import Decimal, ROUND_HALF_EVEN
from fractions import Fraction
from pathlib import Path

class RegistryError(ValueError): pass

def normalize_entries(source_entries: list[dict], artifact_id: int, run_id: int, member: str) -> list[dict]:
    out=[]; seen=set()
    for i,e in enumerate(source_entries):
        name=e.get("name")
        if not name: raise RegistryError("ENTRY_WITHOUT_NAME")
        number_id=f"S6NR-{i+1:06d}"
        if number_id in seen: raise RegistryError("DUPLICATE_NUMBER_ID")
        seen.add(number_id)
        n=e.get("exact_numerator"); d=e.get("exact_denominator")
        if not isinstance(n,int) or not isinstance(d,int) or d<=0: raise RegistryError("INVALID_EXACT_RATIONAL")
        exact=Fraction(n,d)
        display=(Decimal(exact.numerator)/Decimal(exact.denominator)).quantize(Decimal("0.01"),rounding=ROUND_HALF_EVEN)
        out.append({"number_id":number_id,"metric_name":name,"source_artifact_id":artifact_id,"source_run_id":run_id,
          "source_member":member,"source_sha256":None,"cohort_id":None,"trial_id":None,
          "numerator":n,"denominator":d,"exact_value":{"numerator":exact.numerator,"denominator":exact.denominator},
          "display_value":e.get("display_value",format(display,"f")),"rounding_method":e.get("rounding","ROUND_HALF_EVEN"),
          "evidence_status":"REPORTED_ONLY_SOURCE_REGISTRY_ENTRY"})
    return out

def build_registry(aggregate_zip: str, output: str):
    import zipfile
    with zipfile.ZipFile(aggregate_zip) as z: src=json.loads(z.read("number_registry.json").decode("utf-8"))
    entries=normalize_entries(src["entries"],12852969854,40773412377,"number_registry.json")
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    Path(output).write_text(json.dumps({"schema_version":"s6-number-registry-v1","entries":entries},indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return entries
