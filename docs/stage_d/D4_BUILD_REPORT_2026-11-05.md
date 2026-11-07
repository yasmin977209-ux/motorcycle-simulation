# D4 DOCX Report Build — 2026-11-05

Status: PASS_SCOPED_WITH_LIMITATIONS.

- Tested source commit: 1fb4898480629c0a327dbff13792d455cd205a59.
- Workflow Run: 42387025927.
- D4 report manifest SHA-256: 902b58ec5129d4d9c9375be3ab975d61b3fadd07013ef75361b3e51cef133928.
- Number Registry SHA-256: 743ffcced8de09a766870f201c352aabcf5789c43c84bfeae654a939700e4f87; bytes: 24137036.
- Registry-backed number IDs rendered: 16.

## Deliverables

- deliverables/التقرير_الكامل_AR.docx — 42329 bytes; SHA-256 429f143bf84816c3f4ab7eb95dd9f34f758748035423be47ef79cb308c1aeec9.
- deliverables/Full_Report_EN.docx — 41726 bytes; SHA-256 d4d0e49f4b97baa321b9092813ffa40f328a763e7c519ee7201080a3b3c44044.
- deliverables/الملخص_AR.docx — 40517 bytes; SHA-256 17650a5c4c0a739eb87ba0b81b0a833aba6fcd844aea5230faea80f21840e2bd.
- deliverables/Summary_EN.docx — 40050 bytes; SHA-256 e938822db4c4e5d941457a14ea0a6f0fd4cc8808c29ac9722abf1e6ea8bba795.
- deliverables/دراسة_الجدوى_AR.docx — 40763 bytes; SHA-256 df8e5d5da036fd8526f0f33e618ec1b6a26da152caee27ce771cf39dee1cfe3f.

## Scope and limitations

- Reports use REFERENCE_COMPLIANT_BASELINE only; no external market assumptions were introduced.
- Every displayed financial/statistical value is registry-backed and carries its number_id; unavailable values remain MISSING_EVIDENCE.
- D3 remains PASS_SCOPED_WITH_LIMITATIONS; D4 does not change any upstream gate.
- C100 Golden revalidation remains NOT_RUN; Full Logging remains representative-only; the five historical accounting fields remain MISSING_EVIDENCE.
- Financial Gate A remains PASS_SCOPED; Production Gate A remains NOT_DECLARED; Gate B remains FAIL_SCOPED; Stability remains NOT_CONVERGED; N=4800 remains NOT_EXECUTED.
- FINAL_ACCEPTED remains NOT_DECLARED. D5 is the next stage only after D4 exact-head and remote readback pass.
