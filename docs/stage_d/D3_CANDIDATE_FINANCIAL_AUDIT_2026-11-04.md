# D3 Candidate Exact Financial Registry Audit — 2026-11-04

- Candidate D3 source Run: 41754147172.
- Candidate D3 source SHA: 3325fd961005c2c47de071d25904a748af7a21a6.
- Candidate Artifact: 13288779998.
- Candidate Artifact bytes: 535567142.
- Candidate Artifact SHA-256: e49b206d8d80034b1dc0cb284bfee76d81f9e9759e2459b1608fad2f5c933ffe.
- Audit status: PASS_SCOPED — exact financial Registry comparisons and bilingual numeric parity passed.
- This is a candidate-specific scoped check; it does not by itself close D3, reopen D4, or authorize D5.

## Workbooks

| Workbook | Bytes | SHA-256 | Sheets | Numeric cells | Financial Registry matches | Mismatches |
|---|---:|---|---:|---:|---:|---:|
| Full_Results_EN.xlsx | 259442692 | 8b14ec0b2555beae117d453722abc6c733b49ef941bfa8b3e15d299d7983d77d | 185 | 10452370 | 5953640 | 0 |
| النتائج_الكاملة_AR.xlsx | 259444534 | e6617de7799e9a1ee00533e9e5eb77da3ab7d32d3c9d6940fcb87dd04afcbc5d | 185 | 10452370 | 5953640 | 0 |

## Exact cells under review

- SCENARIO_MATRIX!UB7 — NR-e51bacd2a4c626dbc4c5e832 — expected exact Decimal 83735327.68.
- SCENARIO_MATRIX!AFJ10 — NR-b48c8eb8a49a603dc4fbf63d — expected exact Decimal 91969804.71.
- The XML-level scan compared every financial numeric cell against the pinned Number Registry; zero mismatches were required for PASS_SCOPED.

## Preserved boundaries

- D3 remains NOT_PROMOTED pending separate acceptance and D4 rerun.
- No historical Artifact or manifest was changed.
- No Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, identity change, main write, merge, Release, or final acceptance.
