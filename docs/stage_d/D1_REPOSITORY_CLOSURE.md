# D1 Repository Closure — Independent S6 Builder

**Local implementation evidence:** `REPORTED_ONLY / LOCAL_TESTS_REPORTED`  
**Repository source publication:** `BLOCKED / SOURCE_BUNDLE_NOT_COMMITTED`  
**Classification:** `T2_INTERIM / NOT_FINAL_BLOCKED`

## Local verification
- Local package path: `/mnt/data/d1_work`.
- Builder tests: local report records 10 passed (`REPORTED_ONLY`).
- Number Registry tests: local report records 17 passed (`REPORTED_ONLY`).
- Combined suite: local report records **27 passed** (`REPORTED_ONLY`).
- `python -m compileall -q scripts tests`: reported local success (`REPORTED_ONLY`).
- Builder integration: three pinned D0 archives validated; 125 role assignments; 105 unique cohort-qualified keys (100 S6 + 5 C100); 105 manifest resolutions.
- Static AST scan: no Stage 13 assembler, legacy Excel builder, or Stage 12/13 role-selector imports.
- LossCase is `argmin(Final_Net_Project_Equity)`; MaxCase is `argmax(Final_Net_Project_Equity)` without positivity filter. The frozen map is retained; no re-selection.
- Manifest status remains `NOT_VERIFIED` for 105/105 due missing independent expected byte sizes. Original statuses remain unchanged.

## Remaining blockers
- The full local source/test bundle is not yet individually committed on the live Stage D branch.
- No exact-head Stage D validation workflow has run.
- Parquet schema/rows are not parseable in the current runtime; value-level P50/P10/P90/LossCase/MaxCase revalidation remains `NOT_VERIFIED`.
- Acceptance tests 175, 176, 179, 180, 181, 182, 183 and 186 remain `NOT_RUN` on an exact-head delivery commit.

**Disposition:** The local report records successful architecture, isolation, cohort separation, fail-closed manifest handling and unit tests. Under the evidence contract now in force, these are `REPORTED_ONLY` until the exact source files are committed, fetched back, hashed remotely, and tied to the commit. D1 is not repository-source-closed or delivery-acceptance-closed. No Excel/Word generation is authorized by this status.


## Corrective execution evidence — 2026-11-01 (append-only)

The prior statement that exact-head validation had not run is superseded for the rebuilt branch by the following live run:

- Workflow run: [41249462481](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41249462481)
- Tested commit: `7895f63ed1bb34508723d81ced956e6d77d5bda7`
- Conclusion: `success`; exact live branch-head assertion passed.
- Compile: `python -m compileall` passed.
- Tests: `26 passed, 0 failed, 0 skipped`.
- Actual artifact downloads: IDs `12852969854`, `12998778418`, `12630457193`; each download was checked against GitHub artifact metadata, exact size and SHA-256.
- Parquet integration: `pyarrow` installed; the frozen S6 `LossCase` and `MaxCase` roles were checked as global argmin/argmax of `Final_Net_Project_Equity` against the full pinned S6 `trials_summary.parquet`, across 20 S6 scenarios. The selection map was not modified or recomputed.
- ZIP safety tests for duplicate names, traversal/absolute/Windows/dot-segment paths and symlinks ran in the same suite.

Run 17 (`41249454018`) also completed the 26 tests successfully but failed only the final exact-head comparison because the branch advanced during concurrent documentation commits. Run 19 above is the exact-head success. Earlier source-only runs with 8 skipped integration tests remain historical and are not reclassified.

**Disposition remains `BLOCKED`, not D1 PASS.** The canonical full v2.4.0 reference and v2.3/v2.3.1 historical/quarantine full-text files still lack GitHub publication and remote readback. The local archive hash is not a substitute for the required remote evidence. The five missing accounting fields and all project gate limits remain unchanged. A documentation-only commit after Run 19 requires one more exact-head run.


## Final source/artifact gate refresh — 2026-11-01

- Latest previously completed exact-head run: [41251114795](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41251114795), tested SHA `76834d581c07d1bcfc5399044c759be13bdb2b63`, conclusion `success`; all 26 tests passed, no skips, all three pinned artifact downloads and SHA-256 checks passed, Parquet LossCase/MaxCase global argmin/argmax integration passed, and exact live HEAD assertion passed.
- A further documentation-only correction was appended after that run. Final branch HEAD now is `e1e707a8a2dbc137267c0e9a75d600c253a95947`; exact-head run [41251941533](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41251941533) was triggered for this HEAD and must complete successfully before this closure note is treated as exact-head validated.
- Reference publication was re-attempted using the available GitHub Contents API. Only a 10,000-character compressed payload fragment was staged temporarily, then replaced by an explicit warning; it is not a usable reference or evidence. No v2.4.0/v2.3/v2.3.1 canonical file was committed. Full source package remains locally verified; remote reference triples remain missing.
- Current D1 disposition: **BLOCKED** on the three complete reference publications and their remote readback triples. This report does not close D1 and does not authorize D2.
- Main remains unchanged at `c6e54349a5e94f65d5aa9f83141f225d777bb474`. No D1 PR, merge, Release, Trial, Simulation or Monte Carlo was performed.
