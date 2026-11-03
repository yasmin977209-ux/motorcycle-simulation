# D4 DOCX Report Build — 2026-11-03

Status: PASS_SCOPED_WITH_LIMITATIONS.

- Tested source commit: e39549034af3ce360cab3e57b120bf6ef47d88bc.
- Workflow Run: 41691787043.
- D4 report manifest SHA-256: f6092f6bcd4bc45594c845c94f46e36d277fdb0ace7838daa4bd9e4b5e79337b.
- Number Registry SHA-256: 743ffcced8de09a766870f201c352aabcf5789c43c84bfeae654a939700e4f87; bytes: 24137036.
- Registry-backed number IDs rendered: 16.

## Deliverables

- deliverables/التقرير_الكامل_AR.docx — 42246 bytes; SHA-256 cbab2a9b8352714f9a28ec2b7c89a5c51e3dcebb32d46960eeed6fc2b84ad714.
- deliverables/Full_Report_EN.docx — 41643 bytes; SHA-256 19d7f6c0875dd4bc2854cd314194bf703951743f96b4835ea061d9a1df86809a.
- deliverables/الملخص_AR.docx — 40432 bytes; SHA-256 8a6cbd6ef7ed89a94f795dc1b6769d124f480479c178d88649ada25c435880b5.
- deliverables/Summary_EN.docx — 39965 bytes; SHA-256 fca90d40cea95a002356db8b342f5b2ba39298b5fc91f1896a7ef53c3a00451f.
- deliverables/دراسة_الجدوى_AR.docx — 40758 bytes; SHA-256 1c386970ddd4aa5b68da1db9985731a908ca6335d01a25d11ebf7803cd26b244.

## Scope and limitations

- Reports use REFERENCE_COMPLIANT_BASELINE only; no external market assumptions were introduced.
- Every displayed financial/statistical value is registry-backed and carries its number_id; unavailable values remain MISSING_EVIDENCE.
- D3 remains PASS_SCOPED_WITH_LIMITATIONS; D4 does not change any upstream gate.
- C100 Golden revalidation remains NOT_RUN; Full Logging remains representative-only; the five historical accounting fields remain MISSING_EVIDENCE.
- Financial Gate A remains PASS_SCOPED; Production Gate A remains NOT_DECLARED; Gate B remains FAIL_SCOPED; Stability remains NOT_CONVERGED; N=4800 remains NOT_EXECUTED.
- FINAL_ACCEPTED remains NOT_DECLARED. D5 is the next stage only after D4 exact-head and remote readback pass.
