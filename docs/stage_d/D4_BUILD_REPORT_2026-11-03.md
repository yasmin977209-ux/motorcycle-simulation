# D4 DOCX Report Build — 2026-11-03

Status: PASS_SCOPED_WITH_LIMITATIONS.

- Tested source commit: 17696ec48557a33f2c231634ba25f26cf831800e.
- Workflow Run: 41694460895.
- D4 report manifest SHA-256: ac635d8458a9b48af7c9a9790ed406234c1b4636b5aa6e162e6bd08dfa8d5b2b.
- Number Registry SHA-256: 743ffcced8de09a766870f201c352aabcf5789c43c84bfeae654a939700e4f87; bytes: 24137036.
- Registry-backed number IDs rendered: 16.

## Deliverables

- deliverables/التقرير_الكامل_AR.docx — 42248 bytes; SHA-256 e0e0d9ef504aa4d799b16a94597f228471e1f94ef4d5747b55690e5c43d11dc4.
- deliverables/Full_Report_EN.docx — 41645 bytes; SHA-256 927eae4fd072f765ee6d595e8da6aa4052d770b0ac23d8254154a5fe7436a064.
- deliverables/الملخص_AR.docx — 40435 bytes; SHA-256 874c3a87dfa9f2b6648c59ef0bd51ba85779a991f744e08ab9da73e934115681.
- deliverables/Summary_EN.docx — 39968 bytes; SHA-256 e0b589769b749d0429c0fb0cece03f68af8aabd87544ca0a2e5e791f0b04ced2.
- deliverables/دراسة_الجدوى_AR.docx — 40761 bytes; SHA-256 08dd8602cd7666db1f7a48b146498d882cdfb07cb292f44759ddb8f2509f3ec3.

## Scope and limitations

- Reports use REFERENCE_COMPLIANT_BASELINE only; no external market assumptions were introduced.
- Every displayed financial/statistical value is registry-backed and carries its number_id; unavailable values remain MISSING_EVIDENCE.
- D3 remains PASS_SCOPED_WITH_LIMITATIONS; D4 does not change any upstream gate.
- C100 Golden revalidation remains NOT_RUN; Full Logging remains representative-only; the five historical accounting fields remain MISSING_EVIDENCE.
- Financial Gate A remains PASS_SCOPED; Production Gate A remains NOT_DECLARED; Gate B remains FAIL_SCOPED; Stability remains NOT_CONVERGED; N=4800 remains NOT_EXECUTED.
- FINAL_ACCEPTED remains NOT_DECLARED. D5 is the next stage only after D4 exact-head and remote readback pass.
