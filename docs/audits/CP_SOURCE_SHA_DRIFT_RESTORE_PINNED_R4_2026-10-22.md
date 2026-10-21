# R4 — Restore exact pinned daily_engine source identity — 2026-10-22

## Scope and baseline

- Base/main HEAD: `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`.
- Candidate branch: `tmp/cp-source-sha-drift-restore-pinned-20261022`.
- Pinned source commit: `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`.
- Pinned `daily_engine.py` Git blob: `6c4496c3e9a9b41668c3d93063ad31d96df5f878`, 1,162 lines.
- Main `daily_engine.py` Git blob: `0d17d1923fbf95ba7f3e4b6ae695bfbf80f85964`, 1,173 lines.
- Source drift R4 in the current-main continuity log established an exact diff of 11 insertions and no deletions: only a historical compatibility wrapper `_create_contract(...)` delegating to the existing canonical `_new_contract(...)`.
- Search of current main showed `_create_contract` was referenced only by `tests/test_stage3_path_integration.py`; production code defines and uses `_new_contract`.

## Intended minimal repair

1. Restore `daily_engine.py` byte-for-byte to the file at pinned source commit `f3af4f06...`, which should make its blob SHA equal `6c4496c3e9a9b41668c3d93063ad31d96df5f878`.
2. Update the stale test fixture call in `tests/test_stage3_path_integration.py` from non-existent historical alias `daily_engine._create_contract` to the actual canonical `daily_engine._new_contract` with the same arguments.
3. Add a candidate-only, read-only workflow asserting exact file blob/source identity for `daily_engine.py` and `monte_carlo.py`, compiling the affected modules, and running focused Stage 3 path regression files only.

## R4 basis

The project records the alias addition as source-identity drift and a historical raw-test workaround; this patch removes the unnecessary adapter rather than changing `SOURCE_SHA` or redefining the dataset identity. It aligns the test fixture to the actual implementation contract rather than introducing a new production API solely for an out-of-inventory test.

## Explicit exclusions

- No changes to the pinned source commit or `SOURCE_SHA` constant.
- No change to monetary/business logic, RNG/seed, source data, canonical trial IDs, cohort, historical Parquet, dataset manifest, state status, Golden/provider, or Stage 7 production workflow.
- No simulation, Monte Carlo, Trial, Checkpoint, production run, main write, merge, PR closure, or release.
- The CP does not itself resolve Gate A, Stage 11 topology, C050_G000 provenance, or Stage 13 missing source evidence.

## Acceptance criteria

1. Read-back `daily_engine.py` blob matches the pinned Git blob SHA exactly.
2. The stale test uses `_new_contract` and its behavior is preserved.
3. Candidate-only CI passes on an exact SHA for source identity, compile checks, and targeted path tests.
4. Main remains unchanged, and the candidate diff is limited to this R4, `daily_engine.py`, the one test file, a candidate-only verification workflow, and continuity evidence.

## Status

`PENDING_STATIC_READBACK_AND_CI`. Do not claim source drift is resolved unless exact content identity and targeted tests both pass.
