# D3 Preflight Audit — 2026-11-01

## Decision

D2 is closed as PASS_SCOPED_WITH_LIMITATIONS on exact final HEAD 46c86795d64311b53106fb0b7a79f8bcde116112. The official D3 prompt is therefore eligible to start. D3 must use the current Number Registry and may not borrow Stage 12/13 lineage.

## Live source boundary

- Number Registry: results/number_registry.json
- Bytes: 24,137,036
- SHA-256: 743ffcced8de09a766870f201c352aabcf5789c43c84bfeae654a939700e4f87
- Git blob SHA-1: 8cf17de488c623f96c1961ca91d682fbbc7733d6
- Containing commit: 46c86795d64311b53106fb0b7a79f8bcde116112
- Explicit entries: 2,640 = 960 aggregate checkpoint values + 1,680 numeric values for 105 representative keys
- Daily series: 1,000; addressable points: 2,086,550; all points resolved by the D2 validator
- Cohorts: 100 S6 representative keys + 5 C100 representative keys; C100 is CROSS_COHORT_DETERMINISTIC_REUSE
- Full Logging remains 105 representative keys only, not 48,000 trials.

## D3 data availability

| D3 content | Current evidence | Disposition |
|---|---|---|
| 20 S6 daily distributions | 1,000 series / 2,086,550 resolvable points | Available within pinned scope |
| 5 C100 daily distributions | No C100 daily series in Number Registry | MISSING_EVIDENCE |
| 105 representative summary cases | 1,680 registry numeric entries | Available as summary only |
| Representative P50 daily sheets | No representative daily series in Number Registry | MISSING_EVIDENCE |
| ASSETS detail | No per-bike asset/depreciation ledger in Number Registry | MISSING_EVIDENCE |
| ACCTG detail | No daily balance-sheet / income-statement roll-forward | MISSING_EVIDENCE |
| PARTNER detail | No daily partner reinvestment balance series | MISSING_EVIDENCE |
| GUARANTEE detail | No per-claim lifecycle rows | MISSING_EVIDENCE |
| CONTRACTS detail | No per-contract lifecycle rows | MISSING_EVIDENCE |
| Final closure summary | No all-trial close-date distribution | MISSING_EVIDENCE |

The five historical accounting fields remain null and must not be estimated or zero-filled: Accounts_Receivable, Accumulated_Depreciation, Gross_Bike_Assets, Guarantee_Claim_Receivable, Total_Assets.

## Code and lineage review

- scripts/excel_builder.py and scripts/stage13_assemble.py belong to a different Stage 12/13 lineage and are not valid inputs for D3.
- D3 must be built as a dedicated S6 Number Registry consumer.
- D3 can publish an interim workbook only if every unavailable value is explicitly marked MISSING_EVIDENCE and no sheet is presented as complete.
- The D3 gate remains BLOCKED_MISSING_EVIDENCE until required detail sources and all D3 validations are available.

## Preserved gates

Financial Gate A PASS_SCOPED only; Production Gate A NOT_DECLARED; Gate B N=2400 FAIL_SCOPED (10/10); Stability NOT_CONVERGED (0/60); N=4800 NOT_EXECUTED; Full Logging 105 keys only; C100 Golden revalidation NOT_RUN.

No Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, business-rule change, source identity change, main update, PR, merge or Release was performed by this preflight.


## Live D3 status correction — 2026-11-01 (append-only)

- Review baseline branch HEAD: 454b30b7cbd29839ba53b0e16da41d19baf5c161; main remains c6e54349a5e94f65d5aa9f83141f225d777bb474. The D3 live review audit is recorded in docs/stage_d/D3_LIVE_REVIEW_AUDIT_2026-11-01.md.
- D2 remains PASS_SCOPED_WITH_LIMITATIONS at exact closure HEAD 46c86795d64311b53106fb0b7a79f8bcde116112. Current D1 and D1-D2 source validation runs 41341008321 and 41341008307 passed on baseline HEAD 454b30b.
- D3 remains BLOCKED. Runs 41340409949 (4 passed/1 failed: constants parser), 41340511093 (5 tests passed, build audit FORMULA_OR_ERROR_CELLS_FOUND), and 41341008368 (5 passed/1 failed: NameError rosafe_append) all failed. Latest failure is in constants_from_reference(); the current source calls undefined rosafe_append instead of rows.append. The previous formula/error audit does not report separate counts; full workbook safety remains unverified.
- No workbook, manifest, build audit, D3 remote evidence ledger, Actions artifact, or final exact-head output readback exists. deliverables/ is absent. D3 has not closed; D4 remains NOT_STARTED.
- Registry scope and limitations are unchanged: 20 S6 daily scenarios, 1,000 series, 2,086,550 daily points, 105 representative keys / 1,680 numeric entries; C100 daily distributions and representative raw P50 daily logs are missing, as are detailed ASSETS, ACCTG, PARTNER, GUARANTEE, CONTRACTS and final close-date data. Five historical accounting fields remain MISSING_EVIDENCE and must not be inferred or zero-filled.
- Preserve all gates: financial Gate A PASS_SCOPED only; production Gate A NOT_DECLARED; Gate B N=2400 FAIL_SCOPED (10/10); Stability NOT_CONVERGED (0/60); N=4800 NOT_EXECUTED; Full Logging 105 representative keys only / NOT_VERIFIED_105_OF_105; C100 Golden NOT_RUN.
- No Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, main update, PR, merge, Release or D4 transition. Await the owner's explicit continuation instruction.
