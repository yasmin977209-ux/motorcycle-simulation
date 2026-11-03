# D0-D4 Consolidated Gate Closure — 2026-11-03

Repository: `yasmin977209-ux/motorcycle-simulation`  
Branch: `tmp/d1-rebuild-20261101`  
Main HEAD: `c6e54349a5e94f65d5aa9f83141f225d777bb474` (unchanged)  
D4 output commit: `c0bfcbadac8d90932d52eb4ecaec2e72e6b4b909`  
Classification: `T2_INTERIM / NOT_FINAL_BLOCKED`

## Disposition

| Stage | Status | Live evidence |
|---|---|---|
| D0 | `PASS_SCOPED_WITH_LIMITATIONS` | Three pinned artifacts downloaded and SHA-256/size reverified in Run [41694461194](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41694461194). |
| D1 | `PASS_SCOPED_WITH_LIMITATIONS` | Six source modules/two test modules compiled; artifact-backed suite 34 passed; exact tested-head assertion passed in Run 41694461194. |
| D2 | `PASS_SCOPED_WITH_LIMITATIONS` | Registry 2,640 entries; 1,000 daily series; 2,086,550 daily points; validated in Run 41694461194. |
| D3 | `PASS_SCOPED_WITH_LIMITATIONS` | Owner-approved Artifact 13160434943 accepted in Run 41682389098; exact-head Run [41694461171](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41694461171): 36 tests, 35 Raw files. |
| D4 | `PASS_SCOPED_WITH_LIMITATIONS` | Run [41694460895](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41694460895): five DOCX, both summaries 3 pages, 5 tests, 13 Raw readbacks; output commit c0bfcbadac8d90932d52eb4ecaec2e72e6b4b909. |

## D0 — Input audit

Run 41694461194 re-downloaded and rehashed:
- Aggregate Artifact 12852969854: 9,357,996 bytes; SHA-256 `ec05a69ae8968585decf83cf0716d56c264f47f86187cfd3cf53b11f52ca2e54`.
- Full Logging Artifact 12998778418: 310,827,203 bytes; SHA-256 `403371cc8eb12880dda05529b4c83dd675bfa609e8680c09d35efa729c5b5aeb`.
- C100 Artifact 12630457193: 361,733 bytes; SHA-256 `c977d1cbb5204919eadc72358533f77cdbbc239902bcd6f921bf1a915a716e79`.

D0 remains input/preflight closure only. Historical 48K detailed ledgers and five accounting fields remain absent; no inferred values or zero-fill.

## D1 — Independent Builder

Run 41694461194 SUCCESS:
- Three pinned artifacts downloaded and byte-verified.
- Six D1 source modules and two D1 test modules compiled.
- Artifact-backed D1/D2 suite: 34 passed, 0 failed.
- Exact live branch-head assertion passed on tested SHA `17696ec48557a33f2c231634ba25f26cf831800e`.
- Governing v2.4.0 SHA-256: `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`; historical S6 execution reference v2.3 remains separate.

## D2 — Number Registry

- Path: `results/number_registry.json`
- 2,640 entries = 960 aggregate checkpoint + 1,680 representative numeric entries.
- 1,000 daily series; 2,086,550 addressable daily points; 105 representative records (100 S6 + 5 C100).
- Size 24,137,036 bytes; SHA-256 `743ffcced8de09a766870f201c352aabcf5789c43c84bfeae654a939700e4f87`; Git blob SHA-1 `8cf17de488c623f96c1961ca91d682fbbc7733d6`.
- Historical local claim of 13,954 entries remains REPORTED_ONLY, not the current registry.

## D3 — Excel delivery

- Owner-approved Artifact 13160434943: 535,358,202 bytes; SHA-256 `513f2a2edab7083c4f36d0e655de6b8a939403f67b51cf0d0d65d4e51f437b04`.
- Source Run 41480650491 / SHA `2f3cb05bf668cd003cdb5bcb121d2217d629d9f1`.
- Acceptance Run 41682389098: D3-18 PASS_SCOPED; 185 sheets per workbook; zero formula/error cells; ZIP/XLSX integrity checks passed.
- Exact-head Run 41694461171: 36 tests passed; 35 files fetched from Raw and verified.
- Artifact expires 2026-12-02T16:56:31Z; temporary, not permanent archival.

## D4 — DOCX reports

Run 41694460895 SUCCESS; tested SHA `17696ec48557a33f2c231634ba25f26cf831800e`; output commit `c0bfcbadac8d90932d52eb4ecaec2e72e6b4b909`.
- Both summaries: 3 actual pages each.
- Tests: 5 passed.
- Remote Raw readback: 13 files, byte-identical; exact final HEAD passed.
- Evidence Artifact 13260326514; SHA-256 `2e8e1ded9331cc8f5a15888880a692d2ead41b0c1d46d950d318519b6bd0e7e6`; expiry 2026-12-03T18:32:00Z.
- Number Registry IDs rendered: 16 only.

| DOCX | Bytes | SHA-256 |
|---|---:|---|
| التقرير_الكامل_AR.docx | 42,248 | `e0e0d9ef504aa4d799b16a94597f228471e1f94ef4d5747b55690e5c43d11dc4` |
| Full_Report_EN.docx | 41,645 | `927eae4fd072f765ee6d595e8da6aa4052d770b0ac23d8254154a5fe7436a064` |
| الملخص_AR.docx | 40,435 | `874c3a87dfa9f2b6648c59ef0bd51ba85779a991f744e08ab9da73e934115681` |
| Summary_EN.docx | 39,968 | `e0b589769b749d0429c0fb0cece03f68af8aabd87544ca0a2e5e791f0b04ced2` |
| دراسة_الجدوى_AR.docx | 40,761 | `08dd8602cd7666db1f7a48b146498d882cdfb07cb292f44759ddb8f2509f3ec3` |

## Preserved project-wide findings

- Financial Gate A: `PASS_SCOPED` only.
- Production Gate A: `NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS`.
- Gate B at N=2400: `FAIL_SCOPED (10/10)`.
- Stability: `NOT_CONVERGED (0/60)`.
- N=4800: `NOT_EXECUTED`.
- Full Logging: 105 representative keys only, not 48,000 trials.
- Missing fields, not inferred or zero-filled: `Accounts_Receivable`, `Accumulated_Depreciation`, `Gross_Bike_Assets`, `Guarantee_Claim_Receivable`, `Total_Assets`.
- C100 Golden revalidation: `NOT_RUN`.
- No Trial, Simulation, Monte Carlo, N expansion, historical backfill, zero-fill, identity change, main write, merge, Release or final acceptance.

## Final exact-head gate and stop point

This record is committed with the final-gate workflow. The final workflow must succeed on the same commit as this record; the push also triggers the dedicated D1-D2 and D3 exact-head workflows. The final workflow independently opens the five DOCX files, checks pagination/fingerprints, and reads the D0-D4 evidence set from GitHub Raw with SHA-256, Git blob SHA-1, size, URL and containing commit.

**Do not start D5 until all three final-head workflows succeed on the same SHA. Then stop and wait for the owner's explicit D5 start command.** D5 is `NOT_STARTED`; `FINAL_ACCEPTED` remains `NOT_DECLARED`.
