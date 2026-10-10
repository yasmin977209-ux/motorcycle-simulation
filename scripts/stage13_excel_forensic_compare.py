#!/usr/bin/env python3
"""Read-only raw/structural/semantic comparison of two Stage 13 XLSX workbooks."""
import hashlib
import json
import os
import posixpath
import re
import zipfile
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from pathlib import Path

OUT = Path("forensic-output")
OUT.mkdir(parents=True, exist_ok=True)
BOOK = "Stage13_Sample_Results_EN.xlsx"
CORE = "docProps/core.xml"
ACCEPTED_LOG_SHA = "26452c0a7968a66057ac364e38cfdd188fd612857f1f1d82fb5251058c1ef0"
FAILED_LOG_SHA = "1e88da892158f25f16702a971c38d8c5d1c004a8cf1c604107b49dc05c473ae2"
NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
DOC_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"

def q(name):
    return f"{{{NS}}}{name}"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def sha_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def stable_json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")

def find_workbook(folder):
    matches = sorted(Path(folder).rglob(BOOK))
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one {BOOK} in {folder}; found {len(matches)}"
        )
    return matches[0]

def normalize_number(value):
    try:
        number = Decimal(value)
        if not number.is_finite():
            return str(number)
        return "0" if number == 0 else format(number.normalize(), "f")
    except (InvalidOperation, ValueError):
        return value

def read_archive(path):
    members = {}
    entries = []
    order = []
    with zipfile.ZipFile(path) as archive:
        corrupt = archive.testzip()
        if corrupt is not None:
            raise RuntimeError(f"Corrupt ZIP member in {path}: {corrupt}")
        for info in archive.infolist():
            name = info.filename
            if name in members:
                raise RuntimeError(f"Duplicate ZIP member in {path}: {name}")
            data = archive.read(info)
            members[name] = data
            order.append(name)
            entries.append({
                "name": name,
                "date_time": list(info.date_time),
                "compression": info.compress_type,
                "compressed_size": info.compress_size,
                "uncompressed_size": info.file_size,
                "crc32": f"{info.CRC:08x}",
                "flag_bits": info.flag_bits,
                "create_system": info.create_system,
                "create_version": info.create_version,
                "extract_version": info.extract_version,
                "internal_attr": info.internal_attr,
                "external_attr": info.external_attr,
                "header_offset": info.header_offset,
                "extra_sha256": sha(info.extra),
                "comment_sha256": sha(info.comment),
                "sha256_uncompressed_member": sha(data),
            })
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "raw_sha256": sha_file(path),
        "member_order": order,
        "entries": entries,
        "members": members,
    }

def content_sha_excluding_core(members):
    """Hash sorted member names and uncompressed bytes, except core properties."""
    digest = hashlib.sha256()
    digest.update(b"STAGE13_XLSX_CONTENT_V1\0")
    for name in sorted(item for item in members if item != CORE):
        name_bytes = name.encode("utf-8")
        data = members[name]
        digest.update(len(name_bytes).to_bytes(8, "big"))
        digest.update(name_bytes)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()

def core_properties(members):
    data = members.get(CORE)
    if data is None:
        return {"present": False, "values": {}}
    root = ET.fromstring(data)
    return {
        "present": True,
        "raw_sha256": sha(data),
        "values": {
            child.tag.rsplit("}", 1)[-1]: child.text or ""
            for child in list(root)
        },
    }

def shared_strings(members):
    data = members.get("xl/sharedStrings.xml")
    if data is None:
        return []
    root = ET.fromstring(data)
    return [
        "".join(node.text or "" for node in item.iter(q("t")))
        for item in root.findall(q("si"))
    ]

def cell_model(cell, strings):
    cell_type = cell.get("t", "n")
    value_node = cell.find(q("v"))
    raw_value = None if value_node is None else value_node.text

    if cell_type == "inlineStr":
        value = "".join(node.text or "" for node in cell.iter(q("t")))
    elif cell_type == "s":
        if raw_value is None:
            value = None
        else:
            index = int(raw_value)
            value = (
                strings[index]
                if 0 <= index < len(strings)
                else {"invalid_shared_string_index": index}
            )
    elif cell_type == "b":
        value = None if raw_value is None else raw_value == "1"
    elif cell_type in ("e", "str"):
        value = raw_value
    elif raw_value is None:
        value = None
    elif cell_type == "n":
        value = normalize_number(raw_value)
    else:
        value = raw_value

    formula_node = cell.find(q("f"))
    formula = None
    if formula_node is not None:
        formula = {
            "text": formula_node.text or "",
            "attributes": dict(sorted(formula_node.attrib.items())),
        }
    return {"type": cell_type, "value": value, "formula": formula}

def cell_sort_key(address):
    match = re.match(r"^([A-Z]+)([0-9]+)$", address)
    if not match:
        return (10**9, 10**9, address)
    letters, row = match.groups()
    column = 0
    for char in letters:
        column = column * 26 + ord(char) - ord("A") + 1
    return (int(row), column, address)

def workbook_semantics(members):
    for name in ("xl/workbook.xml", "xl/_rels/workbook.xml.rels"):
        if name not in members:
            raise RuntimeError(f"Missing required XLSX member: {name}")

    workbook = ET.fromstring(members["xl/workbook.xml"])
    rel_root = ET.fromstring(members["xl/_rels/workbook.xml.rels"])
    relationships = {
        rel.get("Id"): rel.get("Target")
        for rel in rel_root.findall(f"{{{PKG_REL}}}Relationship")
    }
    strings = shared_strings(members)
    sheets_node = workbook.find(q("sheets"))
    if sheets_node is None:
        raise RuntimeError("Missing workbook <sheets> node")

    models = []
    cell_maps = {}
    formula_count = 0
    error_count = 0

    for order, sheet in enumerate(list(sheets_node), start=1):
        name = sheet.get("name", "")
        target = relationships.get(sheet.get(f"{{{DOC_REL}}}id"))
        if not target:
            raise RuntimeError(f"Missing worksheet relationship: {name!r}")
        sheet_path = (
            target.lstrip("/")
            if target.startswith("/")
            else posixpath.normpath(posixpath.join("xl", target))
        )
        if sheet_path not in members:
            raise RuntimeError(f"Worksheet XML missing: {sheet_path}")

        root = ET.fromstring(members[sheet_path])
        dimension_node = root.find(q("dimension"))
        dimension = None if dimension_node is None else dimension_node.get("ref")
        merge_node = root.find(q("mergeCells"))
        merges = [] if merge_node is None else sorted(
            item.get("ref", "") for item in merge_node.findall(q("mergeCell"))
        )

        cells = {}
        for cell in root.iter(q("c")):
            address = cell.get("r")
            if not address:
                continue
            value = cell_model(cell, strings)
            cells[address] = value
            if value["formula"] is not None:
                formula_count += 1
            if value["type"] == "e":
                error_count += 1
        cell_maps[name] = cells
        models.append({
            "order": order,
            "name": name,
            "state": sheet.get("state", "visible"),
            "dimension": dimension,
            "merged_ranges": merges,
            "cells": [
                {"address": address, **cells[address]}
                for address in sorted(cells, key=cell_sort_key)
            ],
        })

    full_model = {"sheets": models}
    return {
        "sheet_count": len(models),
        "formula_count": formula_count,
        "error_count": error_count,
        "semantic_sha256": sha(stable_json(full_model)),
        "sheets": [
            {
                "order": sheet["order"],
                "name": sheet["name"],
                "state": sheet["state"],
                "dimension": sheet["dimension"],
                "merged_range_count": len(sheet["merged_ranges"]),
                "cell_count": len(sheet["cells"]),
                "semantic_sha256": sha(stable_json(sheet)),
            }
            for sheet in models
        ],
        "_models": models,
        "_cells": cell_maps,
    }

def semantic_differences(left, right, limit=100):
    differences = []
    left_models, right_models = left["_models"], right["_models"]
    left_names = [sheet["name"] for sheet in left_models]
    right_names = [sheet["name"] for sheet in right_models]
    if left_names != right_names:
        differences.append({
            "kind": "worksheet_names_or_order",
            "accepted": left_names,
            "failed": right_names,
        })

    left_by_name = {sheet["name"]: sheet for sheet in left_models}
    right_by_name = {sheet["name"]: sheet for sheet in right_models}
    for name in sorted(set(left_by_name) | set(right_by_name)):
        a, b = left_by_name.get(name), right_by_name.get(name)
        if a is None or b is None:
            differences.append({
                "kind": "worksheet_added_or_removed",
                "sheet": name,
                "accepted_present": a is not None,
                "failed_present": b is not None,
            })
            if len(differences) >= limit:
                break
            continue

        for field in ("state", "dimension", "merged_ranges"):
            if a[field] != b[field]:
                differences.append({
                    "kind": "worksheet_structure", "sheet": name,
                    "field": field, "accepted": a[field], "failed": b[field],
                })
                if len(differences) >= limit:
                    break

        ac = left["_cells"].get(name, {})
        bc = right["_cells"].get(name, {})
        for address in sorted(set(ac) | set(bc), key=cell_sort_key):
            if ac.get(address) != bc.get(address):
                differences.append({
                    "kind": "cell", "sheet": name, "address": address,
                    "accepted": ac.get(address), "failed": bc.get(address),
                })
                if len(differences) >= limit:
                    break
        if len(differences) >= limit:
            break

    return {
        "sample_limit": limit,
        "difference_samples": differences,
        "limit_reached": len(differences) >= limit,
    }

def public_view(value):
    return {key: item for key, item in value.items() if not key.startswith("_")}

def run():
    accepted_path = find_workbook("forensic-input/accepted")
    failed_path = find_workbook("forensic-input/failed")
    accepted = read_archive(accepted_path)
    failed = read_archive(failed_path)
    am, fm = accepted["members"], failed["members"]
    ah = {name: sha(data) for name, data in am.items()}
    fh = {name: sha(data) for name, data in fm.items()}
    an, fn = set(am), set(fm)
    names_equal = an == fn
    member_differences = [
        {
            "name": name,
            "accepted_present": name in am,
            "failed_present": name in fm,
            "accepted_sha256": ah.get(name),
            "failed_sha256": fh.get(name),
        }
        for name in sorted(an | fn)
        if ah.get(name) != fh.get(name)
    ]
    non_core_a, non_core_f = an - {CORE}, fn - {CORE}
    non_core_equal = (
        non_core_a == non_core_f
        and all(ah[name] == fh[name] for name in non_core_a)
    )
    core_equal = am.get(CORE) == fm.get(CORE)
    content_a, content_f = content_sha_excluding_core(am), content_sha_excluding_core(fm)
    content_equal = content_a == content_f

    av, fv = workbook_semantics(am), workbook_semantics(fm)
    cells_equal = av["semantic_sha256"] == fv["semantic_sha256"]
    raw_equal = accepted["raw_sha256"] == failed["raw_sha256"]
    if raw_equal:
        result = "EXACT_RAW_MATCH"
    elif names_equal and non_core_equal and not core_equal:
        result = "CORE_PROPERTIES_OR_CONTAINER_METADATA_ONLY"
    elif names_equal and non_core_equal and core_equal:
        result = "ZIP_CONTAINER_METADATA_OR_ORDER_ONLY"
    elif cells_equal:
        result = "PACKAGE_XML_OR_PRESENTATION_DIFF_BUT_CELL_SEMANTICS_MATCH"
    else:
        result = "SEMANTIC_WORKBOOK_DIFFERENCE"

    ae = {entry["name"]: entry for entry in accepted["entries"]}
    fe = {entry["name"]: entry for entry in failed["entries"]}
    fields = (
        "date_time", "compression", "compressed_size", "uncompressed_size",
        "crc32", "flag_bits", "create_system", "create_version",
        "extract_version", "internal_attr", "external_attr", "header_offset",
        "extra_sha256", "comment_sha256",
    )
    metadata_differences = []
    for name in sorted(set(ae) & set(fe)):
        changes = {
            field: {"accepted": ae[name][field], "failed": fe[name][field]}
            for field in fields if ae[name][field] != fe[name][field]
        }
        if changes:
            metadata_differences.append({"name": name, "changes": changes})

    differences = semantic_differences(av, fv)
    accepted_log_match = accepted["raw_sha256"] == ACCEPTED_LOG_SHA
    failed_log_match = failed["raw_sha256"] == FAILED_LOG_SHA
    report = {
        "report_schema": "stage13-excel-forensic-v1",
        "purpose": "Read-only comparison; does not change the canonical SHA gate.",
        "comparison_result": result,
        "content_sha_excluding_core_equal": content_equal,
        "cell_semantics_equal": cells_equal,
        "source_runs": {
            "accepted_run_id": 38060796014,
            "failed_recovery_run_id": 38067364627,
            "cohort_id": "STAGE13_SAMPLE_TRIAL_IDS_26_50_V2",
            "expected_trials": 625,
            "trial_ids_per_scenario": "26..50",
        },
        "accepted": {
            "xlsx": {
                "path": str(accepted_path), "size_bytes": accepted["size_bytes"],
                "raw_sha256": accepted["raw_sha256"],
                "matches_run_log_sha256": accepted_log_match,
                "run_log_sha256": ACCEPTED_LOG_SHA,
            },
            "zip": {
                "member_count": len(accepted["entries"]),
                "member_order": accepted["member_order"],
                "entries": accepted["entries"],
                "core_properties": core_properties(am),
                "content_sha_excluding_core": content_a,
                "corrupt_member": None,
            },
            "workbook": public_view(av),
        },
        "failed": {
            "xlsx": {
                "path": str(failed_path), "size_bytes": failed["size_bytes"],
                "raw_sha256": failed["raw_sha256"],
                "matches_run_log_sha256": failed_log_match,
                "run_log_sha256": FAILED_LOG_SHA,
            },
            "zip": {
                "member_count": len(failed["entries"]),
                "member_order": failed["member_order"],
                "entries": failed["entries"],
                "core_properties": core_properties(fm),
                "content_sha_excluding_core": content_f,
                "corrupt_member": None,
            },
            "workbook": public_view(fv),
        },
        "comparison": {
            "raw_sha_match": raw_equal,
            "size_bytes_equal": accepted["size_bytes"] == failed["size_bytes"],
            "member_names_equal": names_equal,
            "member_order_equal": accepted["member_order"] == failed["member_order"],
            "member_content_differences": member_differences,
            "zip_member_metadata_differences": metadata_differences,
            "non_core_member_data_equal": non_core_equal,
            "core_properties_raw_equal": core_equal,
            "cell_semantic_difference_samples": differences,
        },
        "checks": {
            "accepted_sheets_185": av["sheet_count"] == 185,
            "failed_sheets_185": fv["sheet_count"] == 185,
            "accepted_formula_cells_zero": av["formula_count"] == 0,
            "failed_formula_cells_zero": fv["formula_count"] == 0,
            "accepted_excel_error_cells_zero": av["error_count"] == 0,
            "failed_excel_error_cells_zero": fv["error_count"] == 0,
        },
        "interpretation_note": (
            "Content SHA hashes sorted member names and uncompressed member bytes "
            "excluding docProps/core.xml; it does not canonicalize XML. Raw SHA "
            "remains byte-level identity. Completing this comparison is not CP-C-fix PASS."
        ),
    }
    (OUT / "comparison.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Stage 13 Excel forensic comparison", "",
        f"- comparison_result: {result}",
        f"- accepted_raw_sha256: {accepted['raw_sha256']}",
        f"- accepted_raw_sha_matches_run_log: {accepted_log_match}",
        f"- failed_raw_sha256: {failed['raw_sha256']}",
        f"- failed_raw_sha_matches_run_log: {failed_log_match}",
        f"- content_sha_excluding_core_equal: {content_equal}",
        f"- cell_semantics_equal: {cells_equal}",
        f"- accepted workbook: {av['sheet_count']} sheets, {av['formula_count']} formula cells, {av['error_count']} error cells",
        f"- failed workbook: {fv['sheet_count']} sheets, {fv['formula_count']} formula cells, {fv['error_count']} error cells",
        "", "This diagnostic does not change the canonical raw SHA or declare CP-C-fix PASS.",
    ]
    if not cells_equal:
        lines += ["", "## First five semantic differences"]
        lines += [
            f"{index}. {json.dumps(item, ensure_ascii=False, sort_keys=True)}"
            for index, item in enumerate(differences["difference_samples"][:5], 1)
        ]
    summary = "\n".join(lines) + "\n"
    print(summary)
    Path(os.environ["GITHUB_STEP_SUMMARY"]).write_text(summary, encoding="utf-8")

def main():
    try:
        run()
    except Exception as exc:
        failure = {
            "report_schema": "stage13-excel-forensic-v1",
            "comparison_result": "COMPARISON_COULD_NOT_BE_COMPLETED",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "note": "No equivalence or mismatch conclusion is valid for this failed comparison.",
        }
        (OUT / "comparison.json").write_text(
            json.dumps(failure, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        summary = (
            "# Stage 13 Excel forensic comparison\n\n"
            "**COMPARISON_COULD_NOT_BE_COMPLETED**\n\n"
            f"{type(exc).__name__}: {exc}\n\nNo equivalence conclusion is drawn.\n"
        )
        Path(os.environ["GITHUB_STEP_SUMMARY"]).write_text(summary, encoding="utf-8")
        raise

if __name__ == "__main__":
    main()
