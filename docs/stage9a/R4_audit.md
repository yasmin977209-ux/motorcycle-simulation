# Stage 9A — R4 Audit (main / stage3b-preserved / reference)

## Source identities
- main branch head at audit: `702ddf9923e92ca477d39a0d2720189f7bca1cca`
- stage3b-preserved branch head at audit: `2e3aa381d833fe430d2aec42e98dd0d29918c3bf`
- reference SHA-256: `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`

## Triple comparison

| Element | main | stage3b-preserved | reference | verdict |
|---|---|---|---|---|
| `scripts/excel_builder.py` | absent at main HEAD | absent at stage3b HEAD | required as the Excel builder for the 185-sheet workbook (reference §19.2; delivery structure) | DEVIATION: required artifact not yet canonical on main; no source file exists on stage3b to copy |
| `requirements.txt` / `openpyxl` | `openpyxl` absent | `openpyxl` absent | `openpyxl` is an explicit technical dependency (reference §19.1) | DEVIATION: dependency not yet canonical on main |
| validation implementation | separate `validation.py` architecture is required; no builder file on main | no builder file | reference separates `excel_builder.py` from `validation.py` (§19.2) | MATCH on architecture; no requirement that validation logic be embedded inside builder |

## R4 conclusion

R4 identifies two concrete pre-canonicalization deviations: the builder artifact and its `openpyxl` dependency were absent from main. The reference does not require validation logic to be embedded inside `excel_builder.py`; it defines a separate `validation.py`.

The Stage 9A builder was therefore treated as a NEW-ARTIFACT on the temporary build lineage. This R4 record does not claim code lineage from `stage3b-preserved`; the inspected stage3b branch did not contain `scripts/excel_builder.py`.
