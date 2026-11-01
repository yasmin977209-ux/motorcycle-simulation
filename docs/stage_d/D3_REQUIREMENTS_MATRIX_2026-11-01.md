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

## Candidate publication and validation — append-only

- D3-01 approved v2.4.0 bytes and Number Registry identity: PASS_SCOPED; the exact approved reference is fetched from its pinned GitHub Gist revision and hash-checked.
- D3-02 S6/C100 cohort separation: PASS_SCOPED.
- D3-03 185-sheet inventory per workbook: PASS_SCOPED.
- D3-04 bilingual sheet order and numeric parity: PASS_SCOPED.
- D3-05 20 S6 daily series / 2,086,550 points: PASS_SCOPED_WITH_LIMITATIONS; C100 daily series remain MISSING_EVIDENCE.
- D3-06 105 representative keys / 1,680 numeric entries: PASS_SCOPED_WITH_LIMITATIONS.
- D3-07 through D3-13 detailed P50, ASSETS, ACCTG, PARTNER, GUARANTEE, CONTRACTS and close-date records: MISSING_EVIDENCE.
- D3-14 Excel formula/error and RTL/LTR checks: PASS_SCOPED.
- D3-15 Number-ID traceability: PASS_SCOPED.
- D3-16 exact integer-ratio / Decimal arithmetic: PASS_SCOPED.
- D3-17 preserved gate and evidence limitations: PASS_SCOPED.
- D3-18 manifest and remote raw readback: PASS_SCOPED after the exact final HEAD validation step succeeds.
- Overall D3 gate remains BLOCKED_MISSING_EVIDENCE; D4 must not start.

## Candidate publication and validation — append-only

- D3-01 approved v2.4.0 bytes and Number Registry identity: PASS_SCOPED; the exact approved reference is fetched from its pinned GitHub Gist revision and hash-checked.
- D3-02 S6/C100 cohort separation: PASS_SCOPED.
- D3-03 185-sheet inventory per workbook: PASS_SCOPED.
- D3-04 bilingual sheet order and numeric parity: PASS_SCOPED.
- D3-05 20 S6 daily series / 2,086,550 points: PASS_SCOPED_WITH_LIMITATIONS; C100 daily series remain MISSING_EVIDENCE.
- D3-06 105 representative keys / 1,680 numeric entries: PASS_SCOPED_WITH_LIMITATIONS.
- D3-07 through D3-13 detailed P50, ASSETS, ACCTG, PARTNER, GUARANTEE, CONTRACTS and close-date records: MISSING_EVIDENCE.
- D3-14 Excel formula/error and RTL/LTR checks: PASS_SCOPED.
- D3-15 Number-ID traceability: PASS_SCOPED.
- D3-16 exact integer-ratio / Decimal arithmetic: PASS_SCOPED.
- D3-17 preserved gate and evidence limitations: PASS_SCOPED.
- D3-18 manifest and remote raw readback: PASS_SCOPED after the exact final HEAD validation step succeeds.
- Overall D3 gate remains BLOCKED_MISSING_EVIDENCE; D4 must not start.


## D3 source-date eligibility reassessment — 2026-11-02 (append-only)

- The three source artifact runs previously considered for detailed D3 reconstruction were created before the 2026-10-31 cutoff and are ineligible for reading under the current project rule.
- A processing attempt (workflow run 41358971225) was cancelled after those artifacts had already been downloaded and read. Its temporary derived output is quarantined, unpublished and excluded from evidence. No repository commit or Actions artifact was produced by that run.
- The D3 completion workflow is disabled and the extension builder now fails closed on the currently pinned pre-cutoff runs.
- D3-05 remains PASS_SCOPED_WITH_LIMITATIONS for 20 S6 series only; C100 daily remains MISSING_EVIDENCE.
- D3-06 remains PASS_SCOPED_WITH_LIMITATIONS for 105 keys / 1,680 registry entries only; representative raw daily logs remain MISSING_EVIDENCE.
- D3-07 through D3-13 remain MISSING_EVIDENCE.
- D3-14 through D3-18 retain their previously recorded scoped evidence. Overall D3 remains BLOCKED_MISSING_EVIDENCE. D4 remains NOT_STARTED.

 
## Source-date and source-free validation update — 2026-11-02 (append-only)

- Owner continuation instruction received at 2026-11-01T23:02:43Z. This permits D3 technical remediation but does not waive the 2026-10-31 source-date cutoff.
- Source-date audit confirms zero eligible post-cutoff D3 source artifacts in the audited inventory. The three pinned source runs remain pre-cutoff; cancelled run 41358971225 and all its derived temporary output are excluded.
- D3-05 remains PASS_SCOPED_WITH_LIMITATIONS for 20 S6 daily series only; C100 daily is MISSING_EVIDENCE.
- D3-06 remains PASS_SCOPED_WITH_LIMITATIONS for 105 representative keys / 1,680 numeric registry entries only; raw representative daily logs are MISSING_EVIDENCE.
- D3-07 through D3-13 remain MISSING_EVIDENCE.
- Added source-free static tests and workflow. The workflow is configured to compile both D3 implementation modules and run 15 tests, but no successful workflow run/report has been verified at this checkpoint: NOT_RUN. No status promotion follows.
- Candidate workbook Raw verification run 41359344854 passed at exact HEAD 7aea74e774084fb7a622f411c5b1dbfad40a2d0d. Current branch HEAD is newer; exact final-head verification at the current checkpoint remains NOT_RUN.
- Overall D3 remains BLOCKED_MISSING_EVIDENCE. D4 remains NOT_STARTED.


## Exact-head and static-code verification update — 2026-11-02

- Source-free code validation: PASS. Run 41360740452 tested SHA 463a4ec53aaef3c2d4a70e1bac448efd326135a0; compileall PASS; 19 passed / 0 skipped. This validates code/test behavior only and is not a D3 gate pass.
- Published-output verification: PASS_SCOPED at exact current branch HEAD 6e8b1654302c8e3a2b59827bd984ffe00a16397a, Run 41360991252. Exact branch/HEAD assertion and Raw readback of the existing bilingual candidate outputs, audit, manifest, report, D2 registry and governing reference passed. No rebuild was performed.
- D3-05 remains PASS_SCOPED_WITH_LIMITATIONS for the 20 S6 daily series only; C100 daily distributions remain MISSING_EVIDENCE.
- D3-06 remains PASS_SCOPED_WITH_LIMITATIONS for 105 representative keys / 1,680 numeric registry entries only; representative P50 raw daily logs remain MISSING_EVIDENCE.
- D3-07 through D3-13 remain MISSING_EVIDENCE for the detailed ledgers and all-trial final close-date distribution.
- D3-14 through D3-18 retain their scoped output/traceability evidence; exact-head no-rebuild validation now covers current HEAD 6e8b1654302c8e3a2b59827bd984ffe00a16397a.
- Overall D3 remains BLOCKED_MISSING_EVIDENCE. D4 remains NOT_STARTED. No status promotion is inferred from static tests or workbook publication.


## Final branch exact-head verification — 2026-11-02

- Run 41361423337 passed at exact current branch HEAD 1c2fb72359480cf861566ced5c66d744cd65c58c. Exact branch/HEAD assertion and Raw output readback passed.
- D3-05: PASS_SCOPED_WITH_LIMITATIONS for 20 S6 daily series only; C100 daily remains MISSING_EVIDENCE.
- D3-06: PASS_SCOPED_WITH_LIMITATIONS for 105 representative keys / 1,680 registry entries only; representative P50 raw daily logs remain MISSING_EVIDENCE.
- D3-07 through D3-13 remain MISSING_EVIDENCE.
- D3-14 through D3-18 retain scoped output and traceability evidence; exact-head verification passed at 1c2fb72359480cf861566ced5c66d744cd65c58c.
- Overall D3 remains BLOCKED_MISSING_EVIDENCE. D4 remains NOT_STARTED.



## D3 operational audit and remediation — 2026-11-02 (verified against live GitHub)

- Live starting point for this audit: branch `tmp/d1-rebuild-20261101` at `2e845974e1337b086de2403150903b0bc0ffaf5e`; `main` remained `c6e54349a5e94f65d5aa9f83141f225d777bb474`.
- The source-date rule is `2026-10-31T00:00:00Z`. GitHub API confirms the three pinned source runs are pre-cutoff: S6 aggregate Run 40773412377 (2026-10-28T21:36:57Z), Full Logging Run 41098699740 (2026-10-30T17:25:30Z), and C100 Run 40263424595 (2026-10-26T03:18:29Z).
- Run 41358971225 downloaded and read those three artifacts before cancellation. This was a process violation; cancellation did not undo the reads. All content-derived temporary output from that run is quarantined and excluded. The run published no Actions artifact and made no repository commit. The cancellation action is recorded in Run 41359264888.
- The fail-closed workflow `.github/workflows/d3-complete-from-pinned-artifacts.yml` now has a disabled job (`if: false`); `scripts/d3_registry_extension.py::build_extension` calls `enforce_source_date_cutoff()` before reading the registry or opening archives. Regression test `test_build_extension_blocks_before_reading_registry_or_opening_archives` confirms the reader is not opened for current pre-cutoff pins.
- The bilingual workbook candidate build is separate from the invalid source-processing attempt. Run 41352075552 built from the pinned D2 Number Registry only, then published the two candidate workbooks and audit/manifest/report. It validated 185 sheets per language, zero formula/error cells, 2,425,143 numeric parity comparisons with zero mismatches, and 4,850,286 numeric cells with zero untraced cells. These are scoped workbook checks, not proof of the missing D3 detailed source ledgers.
- The stale workbook fingerprints in the initial D3 live-review record were corrected append-only. The current identities are Arabic: 27,734,273 bytes, SHA-256 `914da4091c45114f3a61a5c847c0697832956b44a134116fd77e45fb9d39b461`, blob `056b7f482bbb84583526f093ae886e13b8c01356`; English: 27,722,355 bytes, SHA-256 `89712da93a43af7b03d69d516348e9c7e76c3374702d3d0e56418c5704e6f191`, blob `a01c1f4061da731de24fcc8d061113bb195e65b1`. Run 41361573887 verified both Raw files, the audit, manifest, build report, Number Registry and governing reference at exact HEAD `ac04c3931ceb3974d10ce7a59adfcb47a936675b`.
- A latent classification defect was found in `scripts/d3_excel_export_complete.py`: it hard-coded D3-07 through D3-13 as `PASS_SCOPED` and the overall gate as `PASS_SCOPED_WITH_LIMITATIONS`, despite the required source records being absent. The candidate workbooks were not generated by this path: the published candidate workflow at source HEAD `3604ff2fabf2ba8b752b839094eec89835ff4e78` invokes `scripts.s6_excel_export`, and its published audit/manifest explicitly retain `BLOCKED_MISSING_EVIDENCE`. Thus the defect was latent in the unused complete-exporter path, not evidence that the published workbooks were promoted.
- Corrected the exporter to classify D3-07 through D3-13 as `MISSING_EVIDENCE`, D3-05 and D3-06 as `PASS_SCOPED_WITH_LIMITATIONS`, and compute the overall gate as `BLOCKED_MISSING_EVIDENCE` whenever any mandatory requirement is `MISSING_EVIDENCE`, `BLOCKED`, or `NOT_RUN`. Added regression coverage. Code commit: `1b6e78cd6ce456d8bfc50ee6755fd2bb5466d717`; test commit: `1f1de991aa79ff1a3942c17d633a2eb740fcc489`.
- Static validation Run 41361783363 passed on tested source SHA `1f1de991aa79ff1a3942c17d633a2eb740fcc489`: compileall PASS, 20 passed, 0 skipped, zero source artifacts downloaded/read, zero Trial/Simulation, no D3 gate promotion. Its machine-readable report was committed as `2e845974e1337b086de2403150903b0bc0ffaf5e`; report: 659 bytes, SHA-256 `b2f404ede5aacd26ae170a940269c6178a87392f03228682e13447ec74604c40`, Git blob SHA-1 `5afbd0de189e7df07d262048b2a177fb4750a318`.
- Run 41361762401 is a failed attempt after 19 tests passed: the report commit/push step failed because the branch advanced concurrently from its tested SHA. This is a workflow race, not a failed unit test. The subsequent run 41361783363 tested the newer exact SHA and completed successfully.
- D3 output exact-head verification Run 41361783543 succeeded at `1f1de991aa79ff1a3942c17d633a2eb740fcc489`. It verifies the previously published bytes only; it does not rebuild or supply source data. A final exact-head verification is still required after this documentation commit.
- Current D3 requirement disposition remains: D3-01..04 `PASS_SCOPED`; D3-05 `PASS_SCOPED_WITH_LIMITATIONS` for the 20 S6 daily series only (C100 daily missing); D3-06 `PASS_SCOPED_WITH_LIMITATIONS` for 105 representative keys / 1,680 numeric registry entries only; D3-07..13 `MISSING_EVIDENCE`; D3-14..18 `PASS_SCOPED` within the candidate workbook/readback scope. Overall D3 remains `BLOCKED_MISSING_EVIDENCE`.
- Missing source evidence still includes C100 daily distributions, representative P50 raw daily ledgers, bike-level ASSETS, daily ACCTG and roll-forwards, PARTNER balances, GUARANTEE claims, CONTRACTS records, and the all-trial final close-date distribution. The five historical accounting fields remain `MISSING_EVIDENCE` and must not be inferred or zero-filled.
- Preserved project gates: financial Gate A `PASS_SCOPED`; production Gate A `NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS`; Gate B N=2400 `FAIL_SCOPED (10/10)`; Stability `NOT_CONVERGED (0/60)`; N=4800 `NOT_EXECUTED`; Full Logging scope remains 105 representative keys only; C100 Golden revalidation `NOT_RUN`.
- No eligible post-cutoff source artifacts were found in the audited recent Actions inventory. The missing source records cannot be reconstructed from the current pre-cutoff pins under the cutoff rule. Any new source identity, SOURCE_SHA/cohort/seed change, new Trials, or cutoff exception requires a separate owner decision. No such action was taken.
- No D4 work, Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, main update, merge, PR, Release or final-acceptance declaration was performed.
- Disposition: D3 remains `BLOCKED_MISSING_EVIDENCE`; D4 remains `NOT_STARTED`. Stop before D4.
