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

- deliverables/التقرير_الكامل_AR.docx — 42249 bytes; SHA-256 760ae57e4b637785a97e1db2b3c9b615b36de89588f3e66199ba1e2e658a8f75.
- deliverables/Full_Report_EN.docx — 41645 bytes; SHA-256 b353e4027f0706ae448f7a5ee134d9742493d92ce60fe6a869344d385d38741c.
- deliverables/الملخص_AR.docx — 40434 bytes; SHA-256 13e70976805a3695fcee392b9a5e677cead58cbe96f8fbf702a39f1502679bd0.
- deliverables/Summary_EN.docx — 39968 bytes; SHA-256 b442b4b53754965c9aa184e74616b37d668c14d0b20cce08b3798fc7ab0404b8.
- deliverables/دراسة_الجدوى_AR.docx — 40761 bytes; SHA-256 a6cc798f85b15fb2873d886cf9363fc9bb8bf148754c44ce70014a7438a64be6.

- Triggering tested SHA: 13a23122e44240760b461df9d269509218592fd3.
- Workflow Run: 41692077060.
- Number Registry IDs rendered: 16.
- Preserved limitations: C100 Golden NOT_RUN; Full Logging representative-only; five historical accounting fields MISSING_EVIDENCE; Production Gate A NOT_DECLARED; Gate B FAIL_SCOPED; Stability NOT_CONVERGED; N=4800 NOT_EXECUTED.
- No Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, identity change, main write, merge, Release or final acceptance.
