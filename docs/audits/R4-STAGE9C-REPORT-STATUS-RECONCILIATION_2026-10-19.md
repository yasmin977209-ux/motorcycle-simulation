# R4 — Stage 9C report and closure-status reconciliation

- Date: 2026-10-19
- Candidate branch: `tmp/cp-stage9c-status-report-reconcile-20261019`
- Exact base/main SHA: `647c19826b90d8224ce73ef9b90c306a45e03fb0`
- Normative reference SHA-256: `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`
- Change type: documentation-only, append-only reconciliation of the Stage 9C report and unified 9A–9C closure report. No engine, source, state.json, reference, tests, workflow, data, seed/RNG, Parquet, workbook, threshold, trial, cohort, merge or Release change.

## R4 before edits

| Item | Current candidate/base state | Governing decision and exact evidence | Ruling |
|---|---|---|---|
| Stage 9C report | `docs/stage9c/STAGE9C_REPORT.md`, blob `81fb79720988cfe261fa6d8d29371e616f9f9850`, 323 lines. It preserves an original Stage 9A package-scope `PARTIAL` decision because the package then available did not contain the full trial-level daily accounting ledger. | Main state blob `2178260bb18efeb81437486f13b6d10cf5e85936` records `full_stage9c_status=PASS` based on the separately merged PR #38 C-1..C-6 re-audit, merge `74b103cd782c9e75e210a090c94fbcb4b01844c4`. | Do not delete or overwrite the original PARTIAL reasoning. Add a dated, evidence-scoped addendum explaining the later reassessment and the precise boundary of the new PASS. |
| Unified 9A/9B/9C closure report | `docs/CP-MEGA-CLOSURE-9ABC_FINAL_REPORT_AR.md`, blob `f2e3733b9ff48d00e5b512523a2ba98d20a3af33`, 239 lines; it currently says overall closure PARTIAL, Stage 9C PARTIAL, Stage 10 not authorized. | PR #38 updated only state.json. The seven-file delivery set, Stage 11 topology and other main blockers remain unresolved. | Preserve overall project / mega-closure PARTIAL; append the corrected Stage 9C substatus without implying project acceptance or authorization to enter Stage 10. |
| Re-audit evidence | Main state includes exact C-1..C-6 outputs and run references, but its named supporting R4 file `Stage9C_Ledger_Reaudit_R4_AR.md` has `repository_committed=false` and returns 404 on main. | Read-back of Runs 38169163565, 37971902520, 37972735159 and 38165878333; detailed synthesis is in `docs/audits/CP-STAGE9C-C1-C6-STATUS-RECONCILIATION_2026-10-19.md`, blob `3453e5db2a9335a78582140631528f31c55cbb24` on the continuity branch. | This CP creates a separately tracked provenance addendum on the candidate branch; keep the missing historical report status explicit and do not claim its original bytes were recovered. |
| Historical raw test diagnostic | Run 38164248220 is recorded as `11 failed, 338 passed, 1 skipped, 1 warning`. | It is a repository-wide diagnostic outside the bounded C-1..C-6 inventory; failures are explicitly not reclassified by PR #38. | Preserve the non-PASS result verbatim. Stage 9C substatus and raw all-repository test status are separate findings. |

## Run evidence to append

- Gate A fingerprint bridge Run `38169163565`, tested SHA `95288a2bccb40d6772f5a5d042fdabc152c9d89a`: 25/25 scenario reports, 11,005/11,005 exact trial-hash comparisons, zero mismatches, and actual/source-golden trial maps equal to the official CP-12 global SHA `7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44`.
- CP-12-C Run `37971902520`, tested SHA `d4b335926d25d4bc2c6440effc7568260ef5aeb8`: 11,005 trials, 22,546,465 daily rows, 18 listed checks, zero violations, source SHA `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`, seed `20270101`.
- CP-12-D Run `37972735159`, tested SHA `4b39e45c58aac3f7272002f4f241f930ca3c800c`: dynamic closure / terminal checks over 22,546,465 daily rows and zero violations. Retain the source report's limitation: this data schema does not support a per-bike settlement-duration census.
- CP-D Run `38165878333`, tested SHA `2680335d365a8f923aec076f1fb72cb410f821fb`: the strict Parquet-to-`_STATS` gate reported 500/500 exact comparisons, 185 worksheets, zero formula cells and zero Excel-error cells. Original published workbook SHA remains `0fb325fc9e196a534ba8ab7484dcfd0541cefd3a2ca37c3b6f930e3215f62f6d`; the separate candidate workbook was `4bc35a3047b5790e3921475d78a5dd84e05a5c52a729e3ce1f5caa01355185b1`.

## Acceptance and non-goals

The two report changes must be **append-only**: do not alter existing historical paragraphs, tables, dates or verdicts. The new addenda must state that Stage 9C C-1..C-6 was separately re-audited over the identity-matched 9,005-trial Stage 9A cohort using the pre-existing Stage 12 ledger superset, exact trial fingerprint maps and CP-D export evidence. The recorded Stage 9A cohort is 1..450 for 20 non-C100 scenarios plus Trial 1 for five C100 scenarios; the read-only reconciliation recorded 18,449,224 daily rows for that cohort and no dataset rows were regenerated.

These addenda must not:
- call overall repository/delivery status PASS;
- erase the historical Stage 9C PARTIAL decision or raw Run 38164248220 failures;
- imply PR #38 provided the missing standalone report file (it changed state.json only);
- imply the current main Stage 7 Gate A provider is wired or source drift is resolved;
- declare Stage 11 defined, Stage 13 assembled on main, the seven final deliverables complete, or Stage 10 authorized;
- change main/state, reference, source, model outputs, historical data, tests or workflows.

**Before-edit status:** R4 recorded; target reports unchanged; candidate-only appendendum is the sole proposed modification.
