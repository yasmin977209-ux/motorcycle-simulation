# R4 — Full repository regression suite for Stage 13 adapter/assembler migration — 2026-10-22

## Scope

- Base/main HEAD: `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`.
- Candidate branch: `tmp/cp-stage13-current-main-integration-20261021`.
- Classification: `K_TEST / CANDIDATE-ONLY FULL PYTEST INVENTORY`.
- Reason: the Stage 13 candidate moves the previous large `scripts/excel_builder.py` implementation into the new `scripts/stage13_assemble.py` and leaves a compatibility entrypoint. Although focused Stage 13 contracts pass, a full existing test inventory reduces risk of regressions to unrelated functions/public names.

## Exact permitted action

Add a temporary push-only workflow on this candidate branch that checks out `github.sha`, installs repository requirements, compiles the candidate Stage 13 modules, and runs `python -m pytest -q tests`. Preserve test outputs, JUnit XML, tested HEAD, code/test Git blob SHAs, and the canonical Stage 9A manifest blob in a small evidence artifact. No source or test file may be edited in this CP.

## Safety

- Tests are existing deterministic unit/integration tests. No production workbook command is invoked by the workflow; fixture workbooks use temporary test paths.
- The workflow does not dispatch the production Stage 7 workflow, does not invoke a standalone Monte Carlo command, and does not generate a production Trial/Checkpoint or alter a canonical data artifact.
- The canonical `docs/stage9a/dataset_manifest.json` must remain blob `e796fa2443493b607f1f9c60b58eb63607959c26`, identical to base main.
- The pinned Stage 11 identity file must remain blob `72a481d509d39820fba78732724fde4fa9f25134`.
- If the suite fails, keep the run as a failure and document exact test names/errors; do not skip, xfail, or weaken existing assertions merely to obtain PASS.

## Existing bounded evidence

The focused candidate workflow previously passed 55 tests on exact SHA `0d027c85c9b09fdfcfa8ae719e81187e0334b011`. An immediately preceding candidate run failed only because the carried-over DAILY fixture expected insertion-order columns while the Stage 13 assembler intentionally places `Final_Close_Date` immediately after `date`. The candidate fixture was then updated to express that existing assembler ordering, while retaining assertions that all cells equal `row.get(header)`, preserve integer types, nulls, date formatting, and freeze panes. The rerun passed 55 tests. Both outcomes must be preserved in the audit history.

## Acceptance

- Exact-SHA checkout and dependencies pass.
- Full `tests` inventory finishes and its total passed/failed/skipped/warning count is recorded verbatim.
- The evidence artifact proves the tested SHA and every relevant Git blob.
- No production/model/data/manifest source changed.

## Status

`PENDING_FULL_SUITE_CI`. Focused 55-test success is not a full repository suite result and is not production delivery acceptance.


## Exact-SHA full-suite result — baseline control pending

- Run `39685754846` completed with failure on exact candidate SHA `b4fbb7208f7385cec59d6e6f1ba80d3b7c5406cb`: **4 failed, 429 passed, 1 skipped in 259.30s**. All modules compiled successfully. URL: https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39685754846.
- Evidence artifact `12386527129`, name `stage13-full-repository-regression`, size 15,407 bytes, API SHA-256 `203c483b086af3626f592ecb565aa8732d44c53ee02c8fc10149aa3c53fe65cd`. Downloaded evidence ZIP digest was verified to match the API digest; it contains the full log, JUnit XML, and source identity record.
- The only four failures are Stage 5 acceptance tests 127, 159, 160 and 161, each failing before its assertion because required generated files under `results_stage5/` are absent: `worker_equivalence_manifest.json`, `trials_summary.parquet`, or `daily_distribution.parquet`. The recursive current-main Git tree contains no `results_stage5/` paths. This is evidence of an external fixture/artifact dependency, but is not yet classified as pre-existing until the main-based control finishes.
- Source identity artifact records tested Stage 13 blobs: assembler `47fc1828dfb0d298aa4528f58b558bf012882076`; Excel entrypoint `c5db5f1113294224d371e98bab2edd7b015a30d2`; MaxCase audit `f7835b5a6f2584f9a0679a496b565a5a229f6b4c`; Stage 9A manifest `e796fa2443493b607f1f9c60b58eb63607959c26`; Stage 11 identity `72a481d509d39820fba78732724fde4fa9f25134`. Both identities match main.
- No full-suite PASS is claimed. Keep `PASS_FOCUSED_STAGE13_55_TESTS / FULL_SUITE_NOT_PASS`; all 429 passing tests remain useful evidence, but the four missing-fixture failures remain visible. Baseline control Run is `39686434487` on unchanged main-based source pending result.


## Main-based control conclusion

- Baseline control Run `39686434487` on main-derived SHA `08d1ebedb0d970a9cde7afea5aebcebd4ed8a29f` reproduced all four failures with the same paths: missing `worker_equivalence_manifest.json`, `trials_summary.parquet`, and `daily_distribution.parquet`. Exactly `4 failed, 159 deselected` in `0.74s`. URL: https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39686434487.
- Baseline evidence artifact `12386996668`, ZIP SHA-256 `aae5a1314d87a572c086b216fca91c9dbe6b598e0a16755d142dda02de3a93d9`, was downloaded and re-hashed to match the API digest. It confirms the untouched test blob `a93dba6435e0561f82600617ba6c658999409d59`, `stage13_assembler_present=false`, and an empty tracked `results_stage5/` path list.
- The four full-suite failures are now classified `BASELINE_TEST_FIXTURE_DEFECT_CONFIRMED`, not regressions introduced by Stage 13. The candidate's overall full suite result remains verbatim `4 failed, 429 passed, 1 skipped`; it is **not a full-suite PASS** because the baseline-dependent tests do fail in a clean main-derived checkout.
- Stage 13 scoped acceptance status: `PASS_FOCUSED_STAGE13_55_TESTS / FULL_SUITE_HAS_4_BASELINE_FIXTURE_FAILURES`. Any repair to the Stage 5 test fixture contract must be a separate scope; this migration must not create fake results or weaken acceptance assertions.


## Supersession note

The earlier paragraph above that labels the baseline control as “pending” is a timestamped interim observation and is superseded by the completed main-based control conclusion in the next section. Final classification is `BASELINE_TEST_FIXTURE_DEFECT_CONFIRMED`; the full-suite run remains `4 failed, 429 passed, 1 skipped`, not PASS.
