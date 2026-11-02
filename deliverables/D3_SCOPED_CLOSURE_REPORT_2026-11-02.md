# D3 Excel Candidate Build Report — NOT CLOSED

- Candidate: T2_INTERIM / NOT_FINAL_BLOCKED
- D3 gate: BLOCKED_MISSING_EVIDENCE
- D3 input manifest SHA-256: 80c58c30b61d6c68a984c2c06528a724b6b46cf655c6ca9f1752b071ba529bc7
- Source HEAD: 2f3cb05bf668cd003cdb5bcb121d2217d629d9f1
- Workflow run: 41480650491
- Governing reference SHA-256: 225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b; bytes: 401397
- D2 Number Registry SHA-256: 743ffcced8de09a766870f201c352aabcf5789c43c84bfeae654a939700e4f87
- D3 Number Registry extension SHA-256: 7b7e082424a0dab9519723028e8bb99e699e2e590168db258429bb14be6c4024
- Sheets per workbook: 185
- Arabic RTL / English LTR: PASS / PASS
- Excel formulas/errors: AR 0/0; EN 0/0
- S6 daily distribution points: 2086550
- C100 daily reuse points: 549500
- P50 detailed scenarios: 25; all representative daily role keys: 105; role assignments: 125
- All-trial final close-date distribution: source-backed for 49,500 trials (48,000 S6 + 1,500 C100) across 25 scenarios; not inferred from the 105 representative keys.
- Bilingual numeric comparisons: 10346928; mismatches: 0
- Number-ID traced numeric cells: 20693856; untraced: 0

## Requirement status
- D3-01: PASS_SCOPED
- D3-02: PASS_SCOPED
- D3-03: PASS_SCOPED
- D3-04: PASS_SCOPED
- D3-05: PASS_SCOPED_WITH_LIMITATIONS
- D3-06: PASS_SCOPED_WITH_LIMITATIONS
- D3-07: PASS_SCOPED_WITH_LIMITATIONS
- D3-08: PASS_SCOPED_WITH_LIMITATIONS
- D3-09: PASS_SCOPED_WITH_LIMITATIONS
- D3-10: PASS_SCOPED_WITH_LIMITATIONS
- D3-11: PASS_SCOPED_WITH_LIMITATIONS
- D3-12: PASS_SCOPED_WITH_LIMITATIONS
- D3-13: PASS_SCOPED
- D3-14: PASS_SCOPED
- D3-15: PASS_SCOPED
- D3-16: PASS_SCOPED
- D3-17: PASS_SCOPED_WITH_LIMITATIONS
- D3-18: NOT_RUN

## Preserved limitations
- Full Logging contains 105 representative keys / 125 role assignments only; it is not 48,000-trial full daily logging.
- C100 daily distributions are source-backed as deterministic reuse for five scenarios (2,198 rows each); C100 Golden revalidation remains NOT_RUN.
- Representative P50 raw daily ledgers are source-backed for 25 selected cases only; this does not establish full 48,000-trial daily logging.
- Detailed ASSETS, ACCTG, PARTNER, GUARANTEE and CONTRACTS ledgers are source-backed for 25 representative P50 cases only; this does not establish full-cohort detail.
- The all-trial final close-date distribution is source-backed for 49,500 trials (48,000 S6 + 1,500 C100) across 25 scenarios and is not inferred from the 105 representative keys.
- The five historical accounting fields remain MISSING_EVIDENCE for the full 48,000-trial cohort and must not be inferred or zero-filled.
- Full Logging normalized status remains NOT_VERIFIED_105_OF_105; 105 representative keys do not prove all 48,000 trials.
- C100 Golden revalidation remains NOT_RUN; deterministic daily reuse and common-field comparisons do not replace the Golden revalidation gate.
- Financial Gate A remains PASS_SCOPED only; Production Gate A remains NOT_DECLARED.
- Gate B N=2400 remains FAIL_SCOPED (10/10); Stability remains NOT_CONVERGED (0/60); N=4800 remains NOT_EXECUTED.

D3 remains BLOCKED_MISSING_EVIDENCE. This candidate report is not a D3 closure record and does not authorize D4.
