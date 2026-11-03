# D4 DOCX Report Build — 2026-11-03

Status: PASS_SCOPED_WITH_LIMITATIONS.

- Tested source commit: 13a23122e44240760b461df9d269509218592fd3.
- Workflow Run: 41692077060.
- D4 report manifest SHA-256: 486768a22d7610ab55b81f00a1d4a0c594ad95b580af17c5563b9f03d2e92b5f.
- Number Registry SHA-256: 743ffcced8de09a766870f201c352aabcf5789c43c84bfeae654a939700e4f87; bytes: 24137036.
- Registry-backed number IDs rendered: 16.

## Deliverables

- deliverables/التقرير_الكامل_AR.docx — 42249 bytes; SHA-256 760ae57e4b637785a97e1db2b3c9b615b36de89588f3e66199ba1e2e658a8f75.
- deliverables/Full_Report_EN.docx — 41645 bytes; SHA-256 b353e4027f0706ae448f7a5ee134d9742493d92ce60fe6a869344d385d38741c.
- deliverables/الملخص_AR.docx — 40434 bytes; SHA-256 13e70976805a3695fcee392b9a5e677cead58cbe96f8fbf702a39f1502679bd0.
- deliverables/Summary_EN.docx — 39968 bytes; SHA-256 b442b4b53754965c9aa184e74616b37d668c14d0b20cce08b3798fc7ab0404b8.
- deliverables/دراسة_الجدوى_AR.docx — 40761 bytes; SHA-256 a6cc798f85b15fb2873d886cf9363fc9bb8bf148754c44ce70014a7438a64be6.

## Scope and limitations

- Reports use REFERENCE_COMPLIANT_BASELINE only; no external market assumptions were introduced.
- Every displayed financial/statistical value is registry-backed and carries its number_id; unavailable values remain MISSING_EVIDENCE.
- D3 remains PASS_SCOPED_WITH_LIMITATIONS; D4 does not change any upstream gate.
- C100 Golden revalidation remains NOT_RUN; Full Logging remains representative-only; the five historical accounting fields remain MISSING_EVIDENCE.
- Financial Gate A remains PASS_SCOPED; Production Gate A remains NOT_DECLARED; Gate B remains FAIL_SCOPED; Stability remains NOT_CONVERGED; N=4800 remains NOT_EXECUTED.
- FINAL_ACCEPTED remains NOT_DECLARED. D5 is the next stage only after D4 exact-head and remote readback pass.
