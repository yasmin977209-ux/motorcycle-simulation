#!/usr/bin/env python3
"""Convert pytest JUnit evidence into an explicit 163-test acceptance gate."""
from __future__ import annotations
import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--junit", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()

    junit = Path(args.junit)
    if not junit.exists():
        raise SystemExit(f"JUNIT_EVIDENCE_MISSING: {junit}")
    root = ET.parse(junit).getroot()
    cases = []
    for case in root.iter("testcase"):
        classname = case.attrib.get("classname", "")
        filename = case.attrib.get("file", "")
        name = case.attrib.get("name", "")
        if "test_acceptance_16_v2" not in classname and "test_acceptance_16_v2.py" not in filename:
            continue
        match = re.match(r"test_(\d{3})", name)
        if not match:
            continue
        test_id = int(match.group(1))
        skipped = case.find("skipped") is not None
        failed = case.find("failure") is not None or case.find("error") is not None
        if skipped:
            status = "EXCLUDED"
        elif failed:
            status = "FAIL"
        else:
            status = "PASS"
        cases.append({
            "ID": test_id,
            "Name": name,
            "Expected": "reference acceptance assertion",
            "Actual": status,
            "Status": status,
            "Evidence": f"JUnit testcase {classname}::{name}",
        })
    cases.sort(key=lambda row: row["ID"])
    ids = [row["ID"] for row in cases]
    counts = {
        "inventory": len(cases),
        "pass": sum(row["Status"] == "PASS" for row in cases),
        "fail": sum(row["Status"] == "FAIL" for row in cases),
        "excluded": sum(row["Status"] == "EXCLUDED" for row in cases),
        "duplicate_ids": len(ids) - len(set(ids)),
        "missing_ids": sorted(set(range(1, 164)) - set(ids)),
        "unexpected_exclusions": [
            row["ID"] for row in cases
            if row["Status"] == "EXCLUDED" and row["ID"] != 158
        ],
        "test_158_excluded": any(row["ID"] == 158 and row["Status"] == "EXCLUDED" for row in cases),
    }
    passed = (
        counts["inventory"] == 163
        and counts["pass"] == 162
        and counts["fail"] == 0
        and counts["excluded"] == 1
        and counts["duplicate_ids"] == 0
        and not counts["missing_ids"]
        and not counts["unexpected_exclusions"]
        and counts["test_158_excluded"]
    )
    report = {
        "schema_version": "stage13-acceptance-163-v1",
        "status": "PASS" if passed else "FAIL",
        "source_sha": args.source_sha,
        "run_id": args.run_id,
        "run_head_sha": args.head_sha,
        "gate": "acceptance_inventory_163",
        "counts": counts,
        "tests": cases,
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "counts": counts}, ensure_ascii=False, sort_keys=True))
    if not passed:
        raise SystemExit("ACCEPTANCE_163_GATE_FAIL")


if __name__ == "__main__":
    main()
