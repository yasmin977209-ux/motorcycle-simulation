# D3 Requirements Matrix — Registry-backed Excel Candidates

Baseline: D2 PASS_SCOPED_WITH_LIMITATIONS on exact final HEAD 46c86795d64311b53106fb0b7a79f8bcde116112.
D3 scope: two bilingual 185-sheet candidates, sourced only from results/number_registry.json; no Stage 12/13 lineage reuse.
Initial status: NOT_RUN pending candidate build.

| ID | Requirement | Evidence / acceptance rule | Initial status |
|---|---|---|---|
| D3-01 | Governing reference and registry | exact v2.4.0 SHA and registry SHA pin | PASS_SCOPED |
| D3-02 | S6/C100 cohort identities | no pooling; C100 remains cross-cohort deterministic reuse | PASS_SCOPED |
| D3-03 | 185 sheets per language | 10 global + 7 × 25 scenario sheets | NOT_RUN |
| D3-04 | Arabic/English workbook pair | identical sheet names/order and all numeric cells | NOT_RUN |
| D3-05 | Daily Distribution | 20 S6 scenarios, 1,000 series and 2,086,550 points; C100 explicitly missing | PASS_SCOPED_WITH_LIMITATIONS |
| D3-06 | Representative cases | 105 representative keys / 1,680 numeric registry entries only | PASS_SCOPED_WITH_LIMITATIONS |
| D3-07 | Representative P50 DAILY sheets | daily representative values must be in Number Registry | MISSING_EVIDENCE |
| D3-08 | ASSETS detailed ledgers | bike-level data must be in Number Registry | MISSING_EVIDENCE |
| D3-09 | ACCTG daily roll-forward | full accounting values must be in Number Registry | MISSING_EVIDENCE |
| D3-10 | PARTNER daily balances | both daily reinvestment balances must be in Number Registry | MISSING_EVIDENCE |
| D3-11 | GUARANTEE claim ledger | per-claim detail must be in Number Registry | MISSING_EVIDENCE |
| D3-12 | CONTRACTS ledger | per-contract detail must be in Number Registry | MISSING_EVIDENCE |
| D3-13 | Final close-date distribution | all-trial close dates must be in Number Registry | MISSING_EVIDENCE |
| D3-14 | Excel safety | zero formula cells and zero Excel error cells | NOT_RUN |
| D3-15 | Numeric traceability | each numeric data cell paired with number_id or source IDs | NOT_RUN |
| D3-16 | No float financial computation | exact numerator/denominator; Decimal ROUND_HALF_EVEN display | PASS_SCOPED |
| D3-17 | Preserve limitations | five missing accounting fields, 105 statuses NOT_VERIFIED, C100 Golden NOT_RUN, Gate B FAIL, Stability NOT_CONVERGED, N=4800 NOT_EXECUTED | PASS_SCOPED |
| D3-18 | Manifest and remote readback | SHA-256, blob SHA-1, byte size, containing commit, exact final HEAD | NOT_RUN |

Gate rule: structural candidate generation may succeed while D3 remains BLOCKED_MISSING_EVIDENCE. No D4 transition until all mandatory detail sources and acceptance evidence are present.

## Live D3 status correction — 2026-11-01 (append-only)

- Review baseline branch HEAD: 454b30b7cbd29839ba53b0e16da41d19baf5c161; main remains c6e54349a5e94f65d5aa9f83141f225d777bb474. The D3 live review audit is recorded in docs/stage_d/D3_LIVE_REVIEW_AUDIT_2026-11-01.md.
- D2 remains PASS_SCOPED_WITH_LIMITATIONS at exact closure HEAD 46c86795d64311b53106fb0b7a79f8bcde116112. Current D1 and D1-D2 source validation runs 41341008321 and 41341008307 passed on baseline HEAD 454b30b.
- D3 remains BLOCKED. Runs 41340409949 (4 passed/1 failed: constants parser), 41340511093 (5 tests passed, build audit FORMULA_OR_ERROR_CELLS_FOUND), and 41341008368 (5 passed/1 failed: NameError rosafe_append) all failed. Latest failure is in constants_from_reference(); the current source calls undefined rosafe_append instead of rows.append. The previous formula/error audit does not report separate counts; full workbook safety remains unverified.
- No workbook, manifest, build audit, D3 remote evidence ledger, Actions artifact, or final exact-head output readback exists. deliverables/ is absent. D3 has not closed; D4 remains NOT_STARTED.
- Registry scope and limitations are unchanged: 20 S6 daily scenarios, 1,000 series, 2,086,550 daily points, 105 representative keys / 1,680 numeric entries; C100 daily distributions and representative raw P50 daily logs are missing, as are detailed ASSETS, ACCTG, PARTNER, GUARANTEE, CONTRACTS and final close-date data. Five historical accounting fields remain MISSING_EVIDENCE and must not be inferred or zero-filled.
- Preserve all gates: financial Gate A PASS_SCOPED only; production Gate A NOT_DECLARED; Gate B N=2400 FAIL_SCOPED (10/10); Stability NOT_CONVERGED (0/60); N=4800 NOT_EXECUTED; Full Logging 105 representative keys only / NOT_VERIFIED_105_OF_105; C100 Golden NOT_RUN.
- No Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, main update, PR, merge, Release or D4 transition. Await the owner's explicit continuation instruction.
