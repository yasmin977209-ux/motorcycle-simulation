# D0-D6 Master Closure — 2026-11-05

Repository: `yasmin977209-ux/motorcycle-simulation`
Branch: `tmp/d1-rebuild-20261101`
Reviewed HEAD: `bd64c72593755b97867665a0cb587966dee699b2`
main: `c6e54349a5e94f65d5aa9f83141f225d777bb474`

Overall: `D0-D6 = PASS_SCOPED_WITH_LIMITATIONS` within the individually evidenced scope. Project remains `T2_INTERIM / NOT_FINAL_BLOCKED`.

| Stage | Status | Primary evidence |
|---|---|---|
| D0 | PASS_SCOPED_WITH_LIMITATIONS | pinned inputs revalidated, Run 41694461194 |
| D1 | PASS_SCOPED_WITH_LIMITATIONS | v2.4.0 publication and exact-source validation |
| D2 | PASS_SCOPED_WITH_LIMITATIONS | Run 41333300530; 2,640 registry entries; 2,086,550 daily points resolved |
| D3 | PASS_SCOPED_WITH_LIMITATIONS | owner-approved Artifact 13288779998; Run 41914970361 |
| D4 | PASS_SCOPED_WITH_LIMITATIONS | Run 41916830283; five DOCX outputs |
| D5 | PASS_SCOPED_WITH_LIMITATIONS | Run 41928234377; Artifact 13369179742; exact readback |
| D6 | PASS_SCOPED_WITH_LIMITATIONS | Run 41929888796; Job 126923812128; independent audit |

## D0 — Input audit
Three pinned source artifacts were re-downloaded and their size/SHA-256/ZIP integrity rechecked in Run 41694461194. Inputs: Aggregate 12852969854 (9,357,996 bytes; `ec05a69ae8968585decf83cf0716d56c264f47f86187cfd3cf53b11f52ca2e54`); Full Logging 12998778418 (310,827,203 bytes; `403371cc8eb12880dda05529b4c83dd675bfa609e8680c09d35efa729c5b5aeb`); C100 12630457193 (361,733 bytes; `c977d1cbb5204919eadc72358533f77cdbbc239902bcd6f921bf1a915a716e79`). Scope is input identity/integrity and cohort boundary only. Full Logging remains 105 representative keys; historical 48K ledgers and five accounting fields remain missing.

## D1 — Independent Builder
D1 was corrected from its earlier pre-publication BLOCKED snapshot after the owner-approved v2.4.0 reference was published and exact-head validation passed. Governing v2.4.0 SHA-256: `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`; historical v2.3 execution SHA-256 remains separate: `e5efaf0874384e8248c339ca10e248ea9e17e9f0882153b4ef88bc955b91d53f`. D1-D2 source validation Run 41694461194 reports 34 passed, 0 failed. Limitations: 105 manifest statuses NOT_VERIFIED; representative-only Full Logging; C100 Golden NOT_RUN.

## D2 — Number Registry
Registry `results/number_registry.json`: 2,640 explicit entries, 1,000 daily series, 2,086,550 addressable daily points. Full resolver validation covered all 2,086,550 points. Completion Run 41333300530; source/integration Run 41694461194. Completion fingerprint: 24,137,036 bytes; SHA-256 `47e72ecae6f8c9f8cff3c8599909c42bf5e8a4ddaa3d3bceb0be764717b7b321`; Git blob SHA-1 `ba7ead51a67b244ebfcb87d35be59dbaf62fccfc`. The old 13,954-entry local audit is historical REPORTED_ONLY_LOCAL_ONLY, not current registry. Missing evidence remains missing.

## D3 — Excel delivery
Owner approved Artifact 13288779998 as the final immediate D3 delivery object. Acceptance Run 41914970361, tested SHA `b3dfd886ec57308c0bf68f5eec4cc8417faaa3e1`. Artifact 535,567,142 bytes; SHA-256 `e49b206d8d80034b1dc0cb284bfee76d81f9e9759e2459b1608fad2f5c933ffe`; CRC and 15 member fingerprints passed. Both workbooks have 185 sheets, zero formulas and zero Excel error cells. D3-18 PASS_SCOPED. D3-05..12 and D3-17 remain scoped with limitations; C100 Golden NOT_RUN; Full Logging 105 keys only; artifact temporary retention.

## D4 — DOCX generation
Run 41916830283, tested SHA `c5327554d45dc836b7d7f265b4a024dd9049e1f5`, status PASS_SCOPED_WITH_LIMITATIONS. Five DOCX generated from pinned Registry/reference; Arabic RTL, English LTR; executive summaries rendered to 2–3 pages; registry IDs rendered: 16. D4 does not prove full numeric-token lineage for every report value; D6 test 176 remains NOT_RUN.

## D5 — Delivery package
Run 41928234377, tested SHA `baf696af1e951cbf4a79e8a9e009c60c6b053b2d`. Inner ZIP 519,104,296 bytes, SHA-256 `313fa322ffbdda858efa973b5e3e264c26b55cfff0609634b0c919c33733b107`; 8-member inventory/CRC passed. Manifest SHA-256 `5896249f0c3061796229323d1c6a5e9ff05f8436b9a1915376ca15adcb2bb8c5`; SHA256SUMS SHA-256 `349fc09650297bda69e274ca642fca2ce605bc101b9ba2b3c0a57e02624cf8b7`. Artifact 13369179742, 519,116,689 bytes, SHA-256 `80caf0567e31a6bf5397543dac8ef191b38999105dd3cedce4c3dad75b20bff1`. Exact-ID remote readback passed. Full 177-unique-test suite NOT_RUN; artifact temporary retention.

## D6 — Independent post-write audit
Run 41929888796, Job 126923812128, tested SHA `48ae9fbf5a7264834a523504706a7c04b654061b`. Reopened exact D5 Artifact; outer/inner fingerprints, 8-member inventory, CRC, manifest and SHA256SUMS passed. Excel: 20,904,740 numeric cells compared; 11,907,280 financial cells exact to Registry; zero mismatches. Five DOCX parsed/rendered; 112 explicit registry-ID occurrences resolved. Test dispositions: 175 PASS_SCOPED (historical invocation NOT_RUN); 176 NOT_RUN; 179 NOT_RUN; 180 NOT_RUN; 181 NOT_RUN; 182 PASS_SCOPED (historical invocation NOT_RUN); 183 NOT_RUN; 186 PASS_SCOPED (historical invocation NOT_RUN). Full 177-test suite NOT_RUN.

## Invariant gates and limits
Financial Gate A `PASS_SCOPED`; Production Gate A `NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS`; Gate B N=2400 `FAIL_SCOPED (10/10)`; Stability `NOT_CONVERGED (0/60)`; N=4800 `NOT_EXECUTED`; Full Logging 105 representative keys; C100 Golden `NOT_RUN`. Missing accounting fields: `Accounts_Receivable`, `Accumulated_Depreciation`, `Gross_Bike_Assets`, `Guarantee_Claim_Receivable`, `Total_Assets` — do not infer, backfill or zero-fill.

## Final declaration
D0–D6 are each closed only within the scoped evidence above. `FINAL_ACCEPTED`, `P17_FINAL_ACCEPTED`, `P18_RELEASED`, and `CONVERGED` remain NOT_DECLARED. E0 has not been started. No Trials, Simulation, Monte Carlo, N expansion, historical backfill, identity change, main write, merge or Release was performed by this closure record. See the stage-specific files in this directory for detailed matrices, audits, run records and evidence ledgers.
