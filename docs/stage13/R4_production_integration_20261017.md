# R4 — Stage 13 production integration on an isolated candidate
Date: 2026-10-17
CP: CP-STAGE13-PRODUCTION-20261017
Base branch: main
Base SHA: 647c19826b90d8224ce73ef9b90c306a45e03fb0
Normative reference SHA-256: ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479

## Scope

Integrate the already-existing, focused-tested Stage 13 assembler component into a new branch rooted at the exact main HEAD. Replace the current monolithic Excel builder with the thin orchestrator from the Stage 13 candidate, while preserving the legacy public import `patch_xlsx_numeric_values` used by the existing Stage 9C rebuild script. Copy only the assembler and adapter code. Preserve the fixed `canonical`, `sample`, and `demo` modes as separate contracts and keep the adaptive mode fail-closed.

This CP does not create production workbooks, run Monte Carlo, extend a cohort, rerun a completed trial, change the historical dataset/Parquet, change `SOURCE_SHA`, source commit, master seed, RNG, sampling policy, normative reference, tests, workflows, `main`, project state, pull requests, or releases. The final seven delivery files are explicitly out of scope.

## R4 — before changes

| العنصر | الحالي | المرجع/القرار والفرع | النص الحاكم | الحكم |
|---|---|---|---|---|
| Stage 13 assembler path | `scripts/stage13_assemble.py` is absent on main HEAD `647c19826b90d8224ce73ef9b90c306a45e03fb0`. | D-2026-10-10-04 recorded in main `docs/governance/DECISIONS_LOG.md`; Stage 13 candidate component `tmp/cp-stage13-adaptive-assembler-20261017`, blob `c082dbe7ce59233449e9a3af383840834234bbda`. | The approved architecture names `scripts/excel_builder.py` as orchestrator and `scripts/stage13_assemble.py` as assembler. | K_CODE — missing component on main. |
| Existing Excel orchestrator | Main `scripts/excel_builder.py`, blob `50115a2fea5812727e0e5a8bfbb07e1f853f026b`, contains both build logic and compatibility helpers. | Candidate adapter `b59f77df4ea4434bafab5f6f25c04533cc9453be` delegates worksheet construction to the assembler. | Existing callers import `patch_xlsx_numeric_values` from `scripts.excel_builder`, including `scripts/stage9c_rebuild_precision_workbook.py`; preserve public imports while refactoring. | K_CODE — a direct replacement without a re-export would break Stage 9C import. |
| Adaptive cohort validation | Not present on main because the assembler module is absent. | Owner-approved decision D-2026-10-17-06 in candidate decision log; normative reference SHA above. | All 25 scenarios require IDs 1..300 as coverage only; first eligible §2.5 comparison is 300→600; subsequent schedule doubles per scenario and all seven metrics/gates must pass. This decision does not authorize production execution. | K_CODE for integration; production cohort acceptance remains separately gated. |
| Synthetic assembler evidence | Component has focused synthetic evidence at tested HEAD `3fdcdf8d006eff8f4a8fabb9ea2feb5c70c81633`, Run `38995349182`, Artifact `12085749809`, 3,787 bytes, SHA-256 `3a77d5f85385380abebece7811decdf87749dfee77a001b9fac3e26aede71c1c`. | Candidate assembler and adapter blobs are unchanged through branch head `aba7766a7ac7fe3ce94946e1d9024de4852a0afd); the focused suite was synthetic only. | Component tests do not prove a production cohort was read, assembled, or independently audited. | Prior component evidence only; new branch integration gate remains PENDING until the compatibility change is tested. |
| Gate A, source identity, Stage 9C | Main state reports `GATEA_PROVIDER_MISSING`, existing `SOURCE_SHA_DRIFT`, and Stage 9C report remains PARTIAL for missing full-scope daily ledger. | main `state.json` blob `2178260bb18efeb81437486f13b6d10cf5e85936`; main Stage 9C report blob `81fb79720988cfe261fa6d8d29371e616f9f9850`. | Do not change SOURCE_SHA or historical records; no full PASS without its defined evidence. | BLOCKED for final production delivery; do not represent adapter integration as gate acceptance. |

## Implementation contract

1. Start from the exact main base SHA above; keep the CP isolated on `tmp/cp-stage13-production-20261017`.
2. Copy the reviewed assembler source and thin adapter only; add `patch_xlsx_numeric_values` to the adapter's imports from `scripts.stage13_assemble` so it remains available as `scripts.excel_builder.patch_xlsx_numeric_values`.
3. No test or workflow files are changed in this CP. Consequently, the prior synthetic tests are component evidence only; the modified adapter's compatibility import is not declared runtime-tested here.
4. Validate branch/file SHAs, the exact diff versus main, and confirm main HEAD and its state remain unchanged.
5. Do not create any output workbook from a cohort; do not infer Gate A/Gate B/§2.5 or overall stability from manifest status strings alone.

## Acceptance status at R4 time

- Reference SHA: verified.
- Candidate base identity: verified against current main HEAD.
- Code diff/runtime evidence: PENDING before implementation.
- Production cohort identity and independent Gate A evidence: BLOCKED.
- Final deliverables/Release: NOT AUTHORIZED in this CP.


## R4 addendum — authorized temporary integration-test workflow
Recorded: 2026-10-17, before workflow change.

The project owner explicitly approved in chat (“نعم”) a temporary, branch-pinned workflow to run focused integration checks and upload inspectable evidence. This changes only the no-workflow-edits exclusion for the single workflow below. It does not authorize editing tests in the repository, running simulations/trials, production dataset assembly, editing `main` or `state.json`, merging, creating a PR, or releasing deliverables.

### Workflow contract
- Exact path: `.github/workflows/cp-stage13-production-integration.yml`.
- Trigger: path-filtered `push` only, exact branch `tmp/cp-stage13-production-20261017`; no `workflow_dispatch`, schedule, self-dispatch, or wildcard branch pin.
- Checkout the triggering SHA and assert the checked-out commit equals `GITHUB_SHA`.
- Read-only minimum token permissions; job-level timeout.
- Python compile and smoke-test the integrated assembler/adapter, including backward-compatible `patch_xlsx_numeric_values` imports required by `scripts/stage9c_rebuild_precision_workbook.py`.
- Run focused Stage 13 synthetic tests from the exact previously tested component commit `3fdcdf8d006eff8f4a8fabb9ea2feb5c70c81633`, verifying the three test-file blob SHAs before running them from a temporary directory. Run the existing main-branch precision regression test on this integration branch too.
- No test source files are added or modified in this CP. The candidate tests are fetched read-only from the exact test-evidence commit and import the current integration-branch source via `PYTHONPATH=.`.
- Upload bounded evidence unconditionally, including tested SHA, source file hashes/bytes, Python/dependency versions, pytest output/JUnit XML, compile result and the exact temporary test-source blob hashes. Missing evidence fails the job.
- After the Run completes, inspect its exact jobs and downloaded artifact contents, calculate artifact/member SHA-256 and sizes, and verify provenance before classifying the integration test gate.
- If the Run cannot be inspected, report PENDING/BLOCKED. After evidence inspection, remove this workflow alone from the candidate branch in a cleanup commit, keep the branch and evidence, and do not edit `main`.

### Acceptance boundary
A passing workflow validates only the code integration and synthetic/precision regression scope. It does not establish that a production dataset was supplied or that Gate A, Gate B, §2.5 stability, Stage 9C full-scope accounting, or the seven final delivery contracts passed. Production artifact generation remains blocked by the current project identity/golden-provider/data-scope blockers.


## Owner authorization addendum — temporary integration verification workflow

**Recorded:** 2026-10-17  
**Owner authorization:** Direct user replies “نعم” and “نعم” in response to the explicit request to create one temporary branch-pinned integration verification workflow and remove it after independent inspection of its Run and Artifact. This addendum changes only the no-workflow-change exclusion for that single workflow; it does not authorize changing tests in the repository, production simulations, trial generation, historical datasets, `SOURCE_SHA`, seed/RNG/sampling policy, main/state, merge, delivery approval, or Release.

### Bounded workflow contract
- Path: `.github/workflows/cp-stage13-production-verify.yml`.
- Trigger: push only on `tmp/cp-stage13-production-20261017`, restricted to the workflow and the three Stage 13/Stage 9C integration files.
- Checkout and audit the exact event SHA; no self-dispatch and no `workflow_dispatch`.
- Minimal token permissions: `contents: read`; job timeout: 30 minutes.
- Install declared project dependencies; Python compilation and compatibility smoke check only (no cohort loading or workbook generation).
- Run unchanged reviewed Stage 13 synthetic tests from exact commit `aba7766a7ac7fe3ce94946e1d9024de4852a0afd` (blobs `eb8e87be963665bf856ef35e92f1a21601f92128` and `1c3b0a37d3643c2fd45270a63df61b8525b36d5f`) plus the existing Stage 9C numeric-precision regression test from the current main lineage (blob `a7252e757fc222cc764b8247b68d0e7295efa866`). The reviewed test sources are materialized temporarily during the job and are not committed or modified by this CP.
- Upload bounded evidence with exact tested HEAD, test source identities, file hashes, Python/dependency versions, compile/import results, pytest logs, JUnit XML, and process exit code.
- After completion, inspect the actual Artifact contents and hashes before removing the workflow via a bounded cleanup commit. Keep the branch, production files, and Artifact evidence; do not edit main/state or change any gate verdict.
- If the Run is incomplete or evidence cannot be inspected, record PENDING/BLOCKED; do not retry/poll an in-progress Run or claim PASS from workflow status alone.

### Acceptance boundary
The workflow may prove only code compilation, compatibility imports, and synthetic Stage 13 / existing Stage 9C precision regressions on its exact tested SHA. It must not read or build a production cohort. Gate A provider, source identity drift, Stage 9C PARTIAL, delivery acceptance, and Release remain separate blockers.
