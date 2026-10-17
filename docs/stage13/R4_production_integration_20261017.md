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
