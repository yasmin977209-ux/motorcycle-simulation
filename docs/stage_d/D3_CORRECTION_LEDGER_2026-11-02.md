# D3 Correction Ledger — 2026-11-02

## Scope and disposition

Append-only correction record for the D3 candidate publication produced by Actions Run `41352075552`. This record corrects stale fingerprints and an incorrect reference-copy classification. It does not rebuild or modify either workbook, does not change the governing reference, does not promote D3, and does not authorize D4.

## Correct published workbook identities

The earlier `D3_LIVE_REVIEW_AUDIT_2026-11-02.md` values were stale and came from the earlier candidate run. The current published workbook identities, as recorded in the D3 remote evidence ledger, are:

| Path | Bytes | SHA-256 | Git blob SHA-1 | Output commit |
|---|---:|---|---|---|
| `deliverables/النتائج_الكاملة_AR.xlsx` | 27,734,273 | `914da4091c45114f3a61a5c847c0697832956b44a134116fd77e45fb9d39b461` | `056b7f482bbb84583526f093ae886e13b8c01356` | `3f063c62fbb0ea7e62f0882d709371856d071bef` |
| `deliverables/Full_Results_EN.xlsx` | 27,722,355 | `89712da93a43af7b03d69d516348e9c7e76c3374702d3d0e56418c5704e6f191` | `a01c1f4061da731de24fcc8d061113bb195e65b1` | `3f063c62fbb0ea7e62f0882d709371856d071bef` |

No workbook rebuild or workbook-byte modification was performed for these corrections.

## Governing reference repository copy

The prior claim that `docs/governance/MOTORCYCLE_SIMULATION_GOVERNING_REFERENCE_V2.4.0.md` was a conflicting 269,253-byte candidate is withdrawn. The live tree records 401,397 bytes and Git blob SHA-1 `9fe43bfbb2cbfd2bb7f7010866e7469506d22c33`, matching the approved Gist blob identity. This is not by itself the required Raw-byte proof. The exact repository Raw bytes must match SHA-256 `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`, 401,397 bytes, and the recorded Git blob SHA-1 before the repository copy may be called `VERIFIED_LIVE`.

## Validation hardening

- `scripts/s6_excel_export.py::compare` now fails closed when paired worksheets have different dimensions, row counts, or row widths; this prevents `zip()` from silently ignoring trailing worksheet cells.
- `tests/test_s6_excel_export.py` includes a regression test for a trailing-row dimension mismatch.
- The two published XLSX files were not regenerated.

## No-rebuild exact-head workflow

Added `.github/workflows/d3-published-output-verification.yml`. It runs on pushes to `tmp/d1-rebuild-20261101` and manual dispatch. It checks out the exact triggering SHA, asserts exact HEAD, runs the focused exporter regression tests, then downloads committed Raw files at that exact SHA and verifies SHA-256, byte count, and Git blob SHA-1 for both workbooks, D3 audit JSON, manifest, build report, Number Registry, and repository copy of the governing reference. It does not build, rewrite, or upload workbooks.

Workflow file commit: `8ebbd4e730f9468cd205608d84e2cb63ab862c1b`.

## Preserved gates and limitations

- D3 remains `BLOCKED_MISSING_EVIDENCE`; no D4.
- Financial Gate A remains `PASS_SCOPED` only.
- Production Gate A remains `NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS`.
- Gate B N=2400 remains `FAIL_SCOPED (10/10)`; Stability remains `NOT_CONVERGED (0/60)`; N=4800 remains `NOT_EXECUTED`.
- Full Logging remains representative 105 keys only; normalized 105/105 remains `NOT_VERIFIED_105_OF_105`; C100 Golden revalidation remains `NOT_RUN`.
- The five missing accounting fields remain `MISSING_EVIDENCE` and must not be inferred or zero-filled.
- No Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, identity change, main update, merge, or Release was performed.

## Evidence status

The correction text and workflow file are committed. The new workflow's success and its final Raw readbacks must be established from the Actions run on the final correction HEAD. Until then, these additional checks are `NOT_RUN`, not `PASS`.


## D3 pre-cutoff source-processing incident — 2026-11-02 (append-only)

- The D3 completion workflow run 41358971225 was started against three pinned source runs whose GitHub metadata dates are earlier than the project cutoff 2026-10-31:
  - Aggregate run 40773412377: created 2026-10-28T21:36:57Z; artifact 12852969854.
  - Full Logging run 41098699740: created 2026-10-30T17:25:30Z; artifact 12998778418.
  - C100 run 40263424595: created 2026-10-26T03:18:29Z; artifact 12630457193.
- The workflow did download and read those source artifact contents before the cutoff rule was enforced. This was an execution error. Its content-derived temporary output is quarantined and MUST NOT be used as D3 evidence.
- The workflow was cancelled at 2026-11-01T22:52:26Z. Cancellation workflow run 41359264888 completed successfully. The cancelled run has no published Actions artifacts, made no repository commit, did not publish workbooks/manifests, and did not change the D3 candidate deliverables.
- The D3 completion workflow is now disabled; its orchestration script fails closed. The artifact reader also rejects all currently pinned pre-cutoff source runs before opening their archives.
- The 17 D3-focused regression tests passed in the cancelled run, but that test result is not a D3 gate pass and does not validate any pre-cutoff source content.
- No D3 status promotion is made. D3 remains BLOCKED_MISSING_EVIDENCE; D4 remains NOT_STARTED.


## D3 continuation — exporter provenance guard and source-free validation (2026-11-02, append-only)

- Source-free exporter hardening is committed on the working branch: the D3 extension records the source run creation timestamp, and the workbook exporter now rejects extensions unless each source role has the pinned run date at/after the project cutoff and exact pinned artifact/run metadata. This does not make the existing pre-cutoff sources eligible.
- Added regression coverage for pre-cutoff source dates, missing dates, acceptance of synthetic post-cutoff exact-pin metadata, and rejection of mismatched artifact pins. Synthetic tests are logic fixtures only; they are not project source evidence.
- Static validation Run [41360740452](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41360740452) succeeded on tested source SHA `463a4ec53aaef3c2d4a70e1bac448efd326135a0`: compileall PASS; 19 passed / 0 skipped; no source artifacts downloaded/read; no Trial/Simulation; no D3 gate promotion.
- The workflow committed `docs/stage_d/D3_CODE_STATIC_VALIDATION_REPORT_2026-11-02.json` and verified its Raw readback at final report commit `04e3786d3ae2767e5add9c715ecd6394620b6ad0`: 659 bytes; SHA-256 `cb7f390a72d59a7a575a4430c52ee6f710f6f9e6b7bbf2189d431e2bb110bdc5`; Git blob SHA-1 `026b1e3f0b66145a9f8778e8734dd386b92d51b1`.
- D3 candidate no-rebuild verification Run [41360740382](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41360740382) and D1-D2 validation Run [41360740521](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41360740521) succeeded on source SHA `463a4ec53aaef3c2d4a70e1bac448efd326135a0`. D1-D2 is not D3 source coverage; the no-rebuild check validates the existing candidate outputs only.
- Source-date cutoff remains `2026-10-31T00:00:00Z`; all three pinned D3 source runs remain pre-cutoff. No eligible post-cutoff D3 source artifacts were found in the reviewed inventory. D3-05 C100 daily and D3-07 through D3-13 remain `MISSING_EVIDENCE`.
- Overall D3 remains `BLOCKED_MISSING_EVIDENCE`; D4 remains `NOT_STARTED`. No source-date exception, Trial/Simulation/Monte Carlo, N expansion, source/cohort/seed change, backfill, zero-fill, main update, merge, Release or D4 work was performed.


## Correction to interim NOT_RUN and fingerprint entries — 2026-11-02 (append-only)

- The earlier checkpoint note that the new static workflow had no verified run is superseded by Run 41360740452: SUCCESS at tested source SHA 463a4ec53aaef3c2d4a70e1bac448efd326135a0; compileall PASS; 19 passed / 0 skipped; zero source artifacts downloaded/read; no Trial/Simulation.
- The earlier D3 no-rebuild verification checkpoint is superseded by Run 41360991252: SUCCESS at exact current branch HEAD 6e8b1654302c8e3a2b59827bd984ffe00a16397a; exact branch/HEAD assertion and Raw readback passed.
- The earlier SHA-256 values in the code fingerprint table for checkpoint 479ca3889c07fcb4d82b86b23bef61d8760adb64 are superseded. The corrected Raw SHA-256 values and corresponding Git blob SHA-1 values are appended in D3_REMOTE_EVIDENCE_LEDGER_2026-11-01.md.
- These corrections do not close missing source evidence. D3 remains BLOCKED_MISSING_EVIDENCE; D4 remains NOT_STARTED.


## Latest exact-head correction — 2026-11-02 (append-only)

The previous checkpoint exact-head result at 6e8b1654302c8e3a2b59827bd984ffe00a16397a is superseded by Run 41361423337, which passed at exact current branch HEAD 1c2fb72359480cf861566ced5c66d744cd65c58c. Raw output readback passed for all published candidate outputs, the Number Registry and governing reference. No rebuild or source archive read occurred.

The static code result remains Run 41360740452: compileall PASS, 19 passed / 0 skipped, no source artifact bytes read/downloaded, no Trial/Simulation. These checks do not resolve missing D3 source records and do not promote the D3 gate.



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
