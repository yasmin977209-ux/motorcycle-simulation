# STAGE9A_EVIDENCE

## Product evidence

- Stage 9A build Run ID: `37671448546`
- run_head_sha: `5e25a94743f44554093934c57404c0b168e69651`
- Final build branch_head_sha before canonicalization: `16f52cd940164a37292e095e4b74fd9bd084f69b`
- Excel SHA-256: `0fb325fc9e196a534ba8ab7484dcfd0541cefd3a2ca37c3b6f930e3215f62f6d`
- Global Manifest SHA-256: `892da438955160bb59aff3046271402f57bdd61a4abb35f41db7188f61346ff6`
- Workbook sheets: 185
- Excel errors: 0
- Formula cells: 0
- Scenarios: 25
- Trials: 9005
- Representatives: 100
- Acceptance inventory: 163
- Acceptance PASS: 162
- Acceptance FAIL: 0
- Acceptance EXCLUDED: 1
- Excluded test: Test 158 under the recorded override

## Provenance sources

- Stage 7 Run ID: `37225915321`
- Stage 7 run_head_sha: `e0b2fab6710833774937d778097363d7a8ee8e59`
- Stage 7 source_sha: `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`
- Final build branch manifest blob SHA: `e796fa2443493b607f1f9c60b58eb63607959c26`
- Final manifest commit SHA before canonicalization: `16f52cd940164a37292e095e4b74fd9bd084f69b`

## Canonical closure target

Stage 9A canonicalization consists of:
1. permanent R4 record;
2. canonical `excel_builder.py`;
3. canonical `openpyxl` dependency;
4. corrected `Stage9A_Report.json` provenance;
5. explicit deviations record.

This file distinguishes product evidence from procedure/provenance evidence.
