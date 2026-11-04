# D4 Requirements Matrix — 2026-11-05

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

- deliverables/التقرير_الكامل_AR.docx — 42249 bytes; SHA-256 332d7205d67ce19b12cbb196820f741cab34d99f5f11aa8780775446b1dec0bb.
- deliverables/Full_Report_EN.docx — 41645 bytes; SHA-256 945c11d9dbc71b185371cd21ff02d0db68e74d8770eec8f5e09cee00fad2a778.
- deliverables/الملخص_AR.docx — 40435 bytes; SHA-256 d1f5dcc7ac6ff67779d3a6a430645f65dad813c1ec8afa6130c9464a9109dc1d.
- deliverables/Summary_EN.docx — 39967 bytes; SHA-256 8310bbb52c0eb275ed3cbcca4d8cbb9227c438bf77db9b39454d0232d08e5699.
- deliverables/دراسة_الجدوى_AR.docx — 40761 bytes; SHA-256 1fe55fb3ece3dee3368c290551fd8461b0e47240e889fc2ceb384eb11155b3dc.

- Triggering tested SHA: c5327554d45dc836b7d7f265b4a024dd9049e1f5.
- Workflow Run: 41916830283.
- Number Registry IDs rendered: 16.
- Preserved limitations: C100 Golden NOT_RUN; Full Logging representative-only; five historical accounting fields MISSING_EVIDENCE; Production Gate A NOT_DECLARED; Gate B FAIL_SCOPED; Stability NOT_CONVERGED; N=4800 NOT_EXECUTED.
- No Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, identity change, main write, merge, Release or final acceptance.
