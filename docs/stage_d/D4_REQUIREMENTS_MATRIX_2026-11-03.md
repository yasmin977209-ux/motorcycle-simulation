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

- deliverables/التقرير_الكامل_AR.docx — 42246 bytes; SHA-256 cbab2a9b8352714f9a28ec2b7c89a5c51e3dcebb32d46960eeed6fc2b84ad714.
- deliverables/Full_Report_EN.docx — 41643 bytes; SHA-256 19d7f6c0875dd4bc2854cd314194bf703951743f96b4835ea061d9a1df86809a.
- deliverables/الملخص_AR.docx — 40432 bytes; SHA-256 8a6cbd6ef7ed89a94f795dc1b6769d124f480479c178d88649ada25c435880b5.
- deliverables/Summary_EN.docx — 39965 bytes; SHA-256 fca90d40cea95a002356db8b342f5b2ba39298b5fc91f1896a7ef53c3a00451f.
- deliverables/دراسة_الجدوى_AR.docx — 40758 bytes; SHA-256 1c386970ddd4aa5b68da1db9985731a908ca6335d01a25d11ebf7803cd26b244.

- Triggering tested SHA: e39549034af3ce360cab3e57b120bf6ef47d88bc.
- Workflow Run: 41691787043.
- Number Registry IDs rendered: 16.
- Preserved limitations: C100 Golden NOT_RUN; Full Logging representative-only; five historical accounting fields MISSING_EVIDENCE; Production Gate A NOT_DECLARED; Gate B FAIL_SCOPED; Stability NOT_CONVERGED; N=4800 NOT_EXECUTED.
- No Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, identity change, main write, merge, Release or final acceptance.
