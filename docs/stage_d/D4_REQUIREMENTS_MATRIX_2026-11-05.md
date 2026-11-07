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

- deliverables/التقرير_الكامل_AR.docx — 42329 bytes; SHA-256 429f143bf84816c3f4ab7eb95dd9f34f758748035423be47ef79cb308c1aeec9.
- deliverables/Full_Report_EN.docx — 41726 bytes; SHA-256 d4d0e49f4b97baa321b9092813ffa40f328a763e7c519ee7201080a3b3c44044.
- deliverables/الملخص_AR.docx — 40517 bytes; SHA-256 17650a5c4c0a739eb87ba0b81b0a833aba6fcd844aea5230faea80f21840e2bd.
- deliverables/Summary_EN.docx — 40050 bytes; SHA-256 e938822db4c4e5d941457a14ea0a6f0fd4cc8808c29ac9722abf1e6ea8bba795.
- deliverables/دراسة_الجدوى_AR.docx — 40763 bytes; SHA-256 df8e5d5da036fd8526f0f33e618ec1b6a26da152caee27ce771cf39dee1cfe3f.

- Triggering tested SHA: 1fb4898480629c0a327dbff13792d455cd205a59.
- Workflow Run: 42387025927.
- Number Registry IDs rendered: 16.
- Preserved limitations: C100 Golden NOT_RUN; Full Logging representative-only; five historical accounting fields MISSING_EVIDENCE; Production Gate A NOT_DECLARED; Gate B FAIL_SCOPED; Stability NOT_CONVERGED; N=4800 NOT_EXECUTED.
- No Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, identity change, main write, merge, Release or final acceptance.
