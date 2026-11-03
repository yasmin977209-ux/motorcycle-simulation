# D4 Requirements Matrix — 2026-11-03

| Requirement | Disposition | Evidence |
|---|---|---|
| Five fixed DOCX deliverables | PASS_SCOPED | All five files generated and opened by python-docx. |
| Arabic RTL / English LTR | PASS_SCOPED | RTL properties checked for Arabic outputs; English outputs are LTR. |
| Executive summary pagination | PASS_SCOPED | Both summaries rendered to PDF and constrained to two or three actual pages. |
| Number provenance | PASS_SCOPED | Every displayed registry value carries a number_id resolved against the pinned Number Registry. |
| Mandatory section 17.3 disclosures | PASS_SCOPED | Arabic source disclosure and faithful English rendering included. |
| Gate and limitation preservation | PASS_SCOPED_WITH_LIMITATIONS | No upstream gate was promoted; missing accounting fields remain explicit. |
| External market assumptions | PASS_SCOPED | No market, inflation, FX, demand, maintenance or external financing assumptions added. |
| D4 final status | PASS_SCOPED_WITH_LIMITATIONS | D4 report generation only; not D5, D6, P17 or FINAL_ACCEPTED. |

## Output inventory

- deliverables/التقرير_الكامل_AR.docx — 42248 bytes; SHA-256 e0e0d9ef504aa4d799b16a94597f228471e1f94ef4d5747b55690e5c43d11dc4.
- deliverables/Full_Report_EN.docx — 41645 bytes; SHA-256 927eae4fd072f765ee6d595e8da6aa4052d770b0ac23d8254154a5fe7436a064.
- deliverables/الملخص_AR.docx — 40435 bytes; SHA-256 874c3a87dfa9f2b6648c59ef0bd51ba85779a991f744e08ab9da73e934115681.
- deliverables/Summary_EN.docx — 39968 bytes; SHA-256 e0b589769b749d0429c0fb0cece03f68af8aabd87544ca0a2e5e791f0b04ced2.
- deliverables/دراسة_الجدوى_AR.docx — 40761 bytes; SHA-256 08dd8602cd7666db1f7a48b146498d882cdfb07cb292f44759ddb8f2509f3ec3.

- Triggering tested SHA: 17696ec48557a33f2c231634ba25f26cf831800e.
- Workflow Run: 41694460895.
- Number Registry IDs rendered: 16.
- Preserved limitations: C100 Golden NOT_RUN; Full Logging representative-only; five historical accounting fields MISSING_EVIDENCE; Production Gate A NOT_DECLARED; Gate B FAIL_SCOPED; Stability NOT_CONVERGED; N=4800 NOT_EXECUTED.
- No Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, identity change, main write, merge, Release or final acceptance.
