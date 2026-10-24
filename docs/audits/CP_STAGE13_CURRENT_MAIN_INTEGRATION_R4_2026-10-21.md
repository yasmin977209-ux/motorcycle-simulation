# R4 — Stage 13 assembler candidate against unchanged main manifest — 2026-10-21

## Scope

- Base/main HEAD: `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`.
- Candidate branch: `tmp/cp-stage13-current-main-integration-20261021`.
- Classification: `K_CODE + K_TEST + K_WORKFLOW`, candidate-only, synthetic verification only.
- Objective: restore the missing Stage 13 assembler/entrypoint on an isolated branch and test its contract using synthetic fixtures; never build the real delivery workbook in this CP.

## Source and provenance constraints

- Main currently lacks `scripts/stage13_assemble.py`; the binding architecture decision D-2026-10-10-04 identifies `scripts/excel_builder.py` as orchestrator and `scripts/stage13_assemble.py` as assembler.
- Reviewed candidate source comes from `tmp/cp-stage13-integration-20261020`, tested historically by integration Run `39512959275` on candidate SHA `e93bc0383be93ce268f57586319c7669fc1c8dec`. The previously tested candidate changed the Stage 9A manifest blob, so this new candidate explicitly starts from current main and must retain main's canonical `docs/stage9a/dataset_manifest.json` blob `e796fa2443493b607f1f9c60b58eb63607959c26`.
- Main's C050_G000 manifest points to Artifact `11503191706` while its recorded run is `37662891608`. Artifact `11503191706` belongs to Run `37660610243`; Artifact `11503510055` belongs to Run `37662891608`. The data files are largely byte-identical but `scenario_metadata.json` differs in `log_events`. This remains `CONFLICTED / PENDING_APPROVAL`; this CP must not switch IDs or rewrite the manifest.
- Source reports confirm MaxCase partner memo daily balances are absent for the 20 non-C100 selected cases. Do not fabricate these values, derive them from aggregated cash/equity, fill zero, or create a complete production workbook from incomplete daily source data.

## Candidate source set

Port the reviewed Stage 13 assembler, its Excel entrypoint, MaxCase source-audit helper, and focused synthetic tests. All writes are isolated to the candidate branch. The approved cohort size, source SHA, master seed, representative roles, exact fingerprints, stage11 identity and manifest are not changed.

## Verification approach

A dedicated candidate-only, read-only GitHub Actions workflow will:
1. Checkout exactly `github.sha`.
2. Install repository dependencies.
3. Compile Stage 13 modules.
4. Run only synthetic/contract tests for the Stage 13 assembler, MaxCase pending-field handling, and the Excel entrypoint compatibility.
5. Upload logs/JUnit and tested source blobs as run evidence.
It will not download canonical production datasets or build a production workbook; no Monte Carlo, trial, checkpoint, or Golden expansion is allowed.

## Required assertions

- The reviewed Stage 11 identity binding is unchanged and canonical-mode validation fails closed for altered identity/data.
- Synthetic build yields the required 185-sheet structure and five representative roles.
- MaxCase with missing partner memo balances is explicitly pending, never substituted with zero or a guessed accounting value.
- Source audit catches the C050_G000 artifact/run mismatch rather than silently normalizing it.
- Main Stage 9A manifest remains byte-identical to the base blob.

## Acceptance limits

A passing synthetic candidate CI only proves the scoped assembler contract. It does not prove a production workbook can be accepted, does not resolve C050 provenance or missing partner balances, and does not clear overall delivery blockers.

## Explicit exclusions

No main write, merge, release, production workbook build, canonical cohort extraction, simulation, Monte Carlo, trial/checkpoint, data artifact change, manifest/identity change, source SHA, seed/RNG or trial/cohort changes. Do not claim Stage 13 or final delivery accepted while data and provenance are incomplete.

## Status

`PENDING_STATIC_REVIEW`. The Stage 13 code/test/workflow port and tests are not yet accepted until an exact-current-candidate SHA succeeds and the main manifest read-back is unchanged.


## Exact-SHA verification result

- First synthetic-only run `39677426514` passed 54 tests on code/test SHA `e7616f7e34945286856fd665ad0489dbc73378fe`. The workflow was then improved to retain JUnit, log, and source identity evidence.
- Final evidence run `39677625206` completed successfully on exact SHA `5058e764c77c8d4a98776902f9311cbc42eadf7d`: https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39677625206.
- All steps passed: exact-SHA checkout, dependency installation, module compilation, synthetic/compatibility pytest, source-identity capture, evidence artifact upload.
- Pytest result: **54 passed, 0 failures, 0 skips** in `22.97s`.
- Evidence artifact `12382449150`, name `stage13-current-main-synthetic-verification`, ZIP size 2,724 bytes, SHA-256 `468dbde762973ccc830e07277ec5a077454b03d3a4a110c99e600ae57abaccf8`; it was downloaded and re-hashed, matching the Actions API digest. It contains `pytest.junit.xml`, `pytest.log`, and `source_identity.json`.
- Source identity artifact confirms tested HEAD `5058e764c77c8d4a98776902f9311cbc42eadf7d`; assembler blob `47fc1828dfb0d298aa4528f58b558bf012882076`; orchestrator blob `c5db5f1113294224d371e98bab2edd7b015a30d2`; MaxCase audit blob `f7835b5a6f2584f9a0679a496b565a5a229f6b4c`; tests blobs `d4c0f8c52da53cb3ad50994e71632c04502ff873`, `182c7e0ec62e6f48a1fce2d2c4d6bb692e76bce4`, `1c3b0a37d3643c2fd45270a63df61b8525b36d5f`, `968006169c4b46408269fb954c4714e561065f31`, and existing `a7252e757fc222cc764b8247b68d0e7295efa866`.
- Crucially, artifact confirms the candidate Stage 9A dataset manifest Git blob remains exactly `e796fa2443493b607f1f9c60b58eb63607959c26`, identical to main. Its JSON was not rewritten; no canonical input artifact, production workbook, trial, or checkpoint was read/written by this workflow (aside from the tests' synthetic fixtures).
- Disposition: `PASS_SYNTHETIC_CONTRACT_CI / PRODUCTION_DATA_BLOCKED`. No production workbook was built. The manifest's C050_G000 artifact/run conflict and missing daily partner memo balances remain explicit blockers; 54 passing tests do not represent Stage 13 delivery acceptance.


## Exact-SHA synthetic integration result

- GitHub Actions Run `39677426514`, tested SHA `e7616f7e34945286856fd665ad0489dbc73378fe`, conclusion `success`: https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39677426514.
- Dependency installation, module compilation, and the scoped synthetic tests completed successfully: `54 passed in 24.49s`.
- Tested blobs at that exact SHA: `scripts/stage13_assemble.py` `47fc1828dfb0d298aa4528f58b558bf012882076`; `scripts/excel_builder.py` `c5db5f1113294224d371e98bab2edd7b015a30d2`; `scripts/stage13_maxcase_source_audit.py` `f7835b5a6f2584f9a0679a496b565a5a229f6b4c`; `tests/test_stage13_assembler.py` `d4c0f8c52da53cb3ad50994e71632c04502ff873`; `tests/test_stage13_maxcase_pending_fields.py` `182c7e0ec62e6f48a1fce2d2c4d6bb692e76bce4`; `tests/test_excel_builder_adaptive_mode.py` `1c3b0a37d3643c2fd45270a63df61b8525b36d5f`; `tests/test_excel_builder_legacy_compat.py` `968006169c4b46408269fb954c4714e561065f31`.
- The authoritative `docs/stage9a/dataset_manifest.json` remained byte-identical to current main: Git blob `e796fa2443493b607f1f9c60b58eb63607959c26`.
- The run used synthetic fixtures only; it did not download canonical production inputs or build a production workbook. It does not resolve `C050_G000` artifact/run provenance or the missing Partner 1/2 daily memo balances.
- Disposition: `PASS_SYNTHETIC_STAGE13_INTEGRATION / PRODUCTION_DELIVERY_BLOCKED`. The current main branch remains unchanged.


## Final DAILY serialization regression — exact-SHA verification

- Added `tests/test_excel_daily_serialization.py` from the prior focused Excel regression candidate. The test asserts value-to-header alignment while respecting the Stage 13 contract's canonical column order (date followed by Final_Close_Date, with trial_id last where present).
- First run with the test enabled, Run `39685371440` on SHA `c2627fdc879f8e8bb3226429c2a4077d7bffaa07`, correctly caught a test-fixture expectation that assumed the previous writer's header order. No production code was changed to satisfy that outdated expectation; the test now follows the declared Stage 13 writer contract. The run had 1 failed, 54 passed.
- Final successful Run `39685450968`, tested SHA `0d027c85c9b09fdfcfa8ae719e81187e0334b011`: https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39685450968.
- Final result: compile succeeded; `55 passed in 24.35s`, zero failures and zero skipped. Evidence Artifact `12386935266`, name `stage13-current-main-synthetic-verification`, ZIP SHA-256 `a34c7b293a3519a74a839025d9d20f237fe20f30aecb80379bba4cbd4c7c2486`. Local downloaded ZIP SHA matched the Actions API digest.
- Evidence record in the artifact pins tested HEAD `0d027c85c9b09fdfcfa8ae719e81187e0334b011` and confirms the Stage 9A manifest's Git blob is still `e796fa2443493b607f1f9c60b58eb63607959c26`, matching main.
- Final tested blobs: `scripts/stage13_assemble.py` `47fc1828dfb0d298aa4528f58b558bf012882076`; `scripts/excel_builder.py` `c5db5f1113294224d371e98bab2edd7b015a30d2`; `scripts/stage13_maxcase_source_audit.py` `f7835b5a6f2584f9a0679a496b565a5a229f6b4c`; `tests/test_stage13_assembler.py` `d4c0f8c52da53cb3ad50994e71632c04502ff873`; `tests/test_excel_daily_serialization.py` `6f6defb27d07c0491a190ad570132df16763c361`.
- No canonical data was downloaded and no production workbook was built. C050_G000 provenance and missing partner memo balances remain open.
- Final disposition: `PASS_SYNTHETIC_STAGE13_INTEGRATION_PLUS_DAILY_WRITER_REGRESSION / PRODUCTION_DELIVERY_BLOCKED`.


## Additional compatibility test history — DAILY column contract (2026-10-22)

- Exact candidate Run `39685371440` failed on SHA `c2627fdc879f8e8bb3226429c2a4077d7bffaa07`: `1 failed, 54 passed`. Failure was in `tests/test_excel_daily_serialization.py`: its original assertion expected the payload's insertion order (`date, Cash, Final_Close_Date, ...`), while the Stage 13 assembler intentionally canonicalizes `Final_Close_Date` immediately after `date`.
- The code path was not changed to bypass the failure. The candidate test fixture was updated so its expected header list applies the existing Stage 13 canonical-order rule, then computes expected row values by looking up each header from the source mappings. It still asserts header/value alignment, integer Cash type, null preservation, date formatting and freeze panes.
- Rerun `39685450968` passed on exact SHA `0d027c85c9b09fdfcfa8ae719e81187e0334b011`: **55 passed in 24.35s**, zero failures. The workflow includes this DAILY compatibility test in addition to the five existing targeted Stage 13/Excel test files. URL: https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39685450968.
- Evidence artifact `12386935266`, `stage13-current-main-synthetic-verification`, size 2,804 bytes, API SHA-256 `a34c7b293a3519a74a839025d9d20f237fe20f30aecb80379bba4cbd4c7c2486`; all job steps passed through the evidence upload.
- Current Stage 9A manifest remains the exact main blob `e796fa2443493b607f1f9c60b58eb63607959c26`; no production workbook/data was produced or changed.
- A full repository test run is now being executed separately under `CP_STAGE13_FULL_SUITE_REGRESSION_R4_2026-10-22.md` / `.github/workflows/cp-stage13-full-suite-regression-20261022.yml`. Until that completes, full-suite compatibility remains `PENDING_FULL_SUITE_CI`.


## Final validation reconciliation — full-suite status is no longer pending (2026-10-22)

This section supersedes the earlier interim line in the DAILY compatibility addendum saying the full suite was still pending.

- Focused synthetic Stage 13/Excel contract: `PASS`, 55 passed in 24.35s, Run `39685450968` on exact SHA `0d027c85c9b09fdfcfa8ae719e81187e0334b011`.
- Full repository suite: `NOT PASS`, 4 failed / 429 passed / 1 skipped in 259.30s, Run `39685754846` on SHA `b4fbb7208f7385cec59d6e6f1ba80d3b7c5406cb`. The four failures are tests 127, 159, 160, 161 in `tests/test_acceptance_16_v2.py`, all caused by absent `results_stage5/` artifacts.
- Main-based control Run `39686434487`, SHA `08d1ebedb0d970a9cde7afea5aebcebd4ed8a29f`, reproduces the same four missing-file failures with unchanged test blob `a93dba6435e0561f82600617ba6c658999409d59`; the main tree tracks no `results_stage5/` paths. Classification: `BASELINE_TEST_FIXTURE_DEFECT_CONFIRMED`, not a regression caused by this Stage 13 branch.
- Full-suite run artifact `12386527129` digest `203c483b086af3626f592ecb565aa8732d44c53ee02c8fc10149aa3c53fe65cd`; baseline artifact `12386996668` digest `aae5a1314d87a572c086b216fca91c9dbe6b598e0a16755d142dda02de3a93d9`. Both archives were downloaded and their digest verified against the Actions API.
- Current draft PR #49 remains limited to synthetic/compatibility evidence. It does not claim full-suite PASS or production Stage 13 delivery acceptance.


## Latest integrated-main exact-SHA verification (2026-10-22)

- Focused Stage 13/Excel Run `39689589357`, exact SHA `0d5556eb77b9efcac3abf468654b9f4a8bf4ca81`, conclusion `success`: https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39689589357.
- Result: **55 passed in 15.62s**, with successful compile and evidence capture. Artifact `12388231063`, SHA-256 `adfe1aa4acf885d1efd1921608a150008389e6da778e67a43aa201078c47ee22`; the downloaded ZIP matched the API digest and contains `pytest.log`, `pytest.junit.xml`, and `source_identity.json`.
- The evidence binds `scripts/stage13_assemble.py` blob `47fc1828dfb0d298aa4528f58b558bf012882076`, `scripts/excel_builder.py` blob `c5db5f1113294224d371e98bab2edd7b015a30d2`, `scripts/stage13_maxcase_source_audit.py` blob `f7835b5a6f2584f9a0679a496b565a5a229f6b4c`; Stage 9A manifest `e796fa2443493b607f1f9c60b58eb63607959c26`; Stage 11 identity `72a481d509d39820fba78732724fde4fa9f25134`. Both canonical identity blobs match main.
- The full inventory on the same merged-main code/test blobs, Run `39689267217`, exact SHA `a3416ccdd4e3e0d6a535b5d6b8acf89f0a70b6c9`, concluded `failure`: **4 failed, 433 passed, 1 skipped in 243.73s**. Evidence artifact `12388381410`, digest `522cd6b2d559a3d48aaf2b25a7f556458548491ec2022dd7fd631e9950481633`, download digest verified.
- The four failures remain the same Stage 5 fixture-dependent tests 127,159,160,161. Main-based control Run `39686434487` had already reproduced the identical missing-file errors from the same test blob. Candidate’s broader suite is therefore not a full PASS.
- The final complete-suite rerun against SHA `de032129140792d7aad8e2e13b287d05261eb566` is in progress; that commit changes the full-suite workflow display name only relative to the tested code/test tree. Record its final state before final PR disposition.

## Base refresh after C050_G000 provenance merge — 2026-10-24

- Main advanced via PR #62 merge commit 7d0b26588cbe58eb2228e539745787eaa202b654. The canonical Stage 9A manifest is now blob c8591aac3d309fd94c4e67a547d33fb62ac5694d and C050_G000 points to artifact 11503510055 from Run 37662891608.
- Earlier audit results from heads based on 7621ddefe6c971e9eb231eb2a987519c86a2cb51 preserve the pre-merge outcome (one C050_G000 pointer mismatch); they must not describe the refreshed branch's result.
- This candidate keeps historical audit/replay artifact identities as pinned inputs and updates its exact-head regression check to the new canonical manifest blob. Read-only audit and focused/full test runs must repeat against the refreshed commit.
- The Stage 9A inventory retains its snapshot identity while adding the post-merge canonical manifest pointer; it is not silently re-labelled as if generated against the new blob.
- This refresh does not approve Stage 11 topology, production checkpoint execution, adaptive statistical inference, workbook acceptance, or Release.
