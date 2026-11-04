# D4 DOCX Report Build — 2026-11-05

Status: PASS_SCOPED_WITH_LIMITATIONS.

- Tested source commit: c5327554d45dc836b7d7f265b4a024dd9049e1f5.
- Workflow Run: 41916830283.
- D4 report manifest SHA-256: 7a16d94649d8e1ea14e537ab8cd751b867a844821f62d5f68eebb693d5bd11ab.
- Number Registry SHA-256: 743ffcced8de09a766870f201c352aabcf5789c43c84bfeae654a939700e4f87; bytes: 24137036.
- Registry-backed number IDs rendered: 16.

## Deliverables

- deliverables/التقرير_الكامل_AR.docx — 42249 bytes; SHA-256 332d7205d67ce19b12cbb196820f741cab34d99f5f11aa8780775446b1dec0bb.
- deliverables/Full_Report_EN.docx — 41645 bytes; SHA-256 945c11d9dbc71b185371cd21ff02d0db68e74d8770eec8f5e09cee00fad2a778.
- deliverables/الملخص_AR.docx — 40435 bytes; SHA-256 d1f5dcc7ac6ff67779d3a6a430645f65dad813c1ec8afa6130c9464a9109dc1d.
- deliverables/Summary_EN.docx — 39967 bytes; SHA-256 8310bbb52c0eb275ed3cbcca4d8cbb9227c438bf77db9b39454d0232d08e5699.
- deliverables/دراسة_الجدوى_AR.docx — 40761 bytes; SHA-256 1fe55fb3ece3dee3368c290551fd8461b0e47240e889fc2ceb384eb11155b3dc.

## Scope and limitations

- Reports use REFERENCE_COMPLIANT_BASELINE only; no external market assumptions were introduced.
- Every displayed financial/statistical value is registry-backed and carries its number_id; unavailable values remain MISSING_EVIDENCE.
- D3 remains PASS_SCOPED_WITH_LIMITATIONS; D4 does not change any upstream gate.
- C100 Golden revalidation remains NOT_RUN; Full Logging remains representative-only; the five historical accounting fields remain MISSING_EVIDENCE.
- Financial Gate A remains PASS_SCOPED; Production Gate A remains NOT_DECLARED; Gate B remains FAIL_SCOPED; Stability remains NOT_CONVERGED; N=4800 remains NOT_EXECUTED.
- FINAL_ACCEPTED remains NOT_DECLARED. D5 is the next stage only after D4 exact-head and remote readback pass.
