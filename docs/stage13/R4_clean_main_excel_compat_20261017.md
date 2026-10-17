# R4 — CP Stage 13 assembler and Excel compatibility on clean main

- Date: 2026-10-17
- Branch: `tmp/cp-stage13-excel-compat-20261017`
- Required base: `main` at `647c19826b90d8224ce73ef9b90c306a45e03fb0`
- Normative reference SHA-256: `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`
- Scope: Stage 13 worksheet assembly, Excel orchestration/legacy API compatibility, synthetic regression tests. No production simulation, new trial generation, source/seed/RNG/sampling changes, historical dataset edits, workflow changes, main changes, merge, or release.

## R4 before changes

| العنصر | الحالي على main | المرجع/القرار والفرع | النص الحاكم | الحكم |
|---|---|---|---|---|
| Stage 13 assembler | `scripts/stage13_assemble.py` is absent (404 when read on main); main state records `MISSING_ARTIFACT`. | `docs/governance/DECISIONS_LOG.md`, D-2026-10-10-04; main HEAD `647c19826b90d8224ce73ef9b90c306a45e03fb0`. | `scripts/stage13_assemble.py` is the assembler using `assemble_workbook` to build 185 sheets and validate the result. | K_CODE |
| Excel architecture | `scripts/excel_builder.py` combines data loading and worksheet generation in a 53 KB monolith (blob `50115a2fea5812727e0e5a8bfbb07e1f853f026b`). | D-2026-10-10-04. | `excel_builder.py` is the CLI/config/mode orchestrator and loader; worksheet creation belongs in Stage 13 assembler. | K_CODE |
| README sheet count | `write_readme` runs before the other sheets exist; README can record the partial count. | Normative reference delivery requires 185 named sheets: 10 global + 25×7 scenario sheets. | The final workbook must report and verify its full sheet count and exact sheet inventory after assembly. | K_CODE |
| Stage 9C numeric serializer imports | Main `scripts/stage9c_rebuild_precision_workbook.py` imports `patch_xlsx_numeric_values` from `scripts.excel_builder`; `tests/test_excel_builder_precision.py` imports `save_workbook_preserving_stats_precision` from that module. | Existing Stage 9C implementation and tests on main. | The architectural split must preserve both imports; changing the import path would widen scope and risk a regression. | K_CODE if not re-exported |
| Unknown cohort handling | Previous Stage 13 adapter distinguishes `canonical`, `sample`, `demo`, and `adaptive`; unknown counts fail closed. | D-2026-10-10-04 and the adaptive cohort candidate contract; adaptive proof is input validation only, not a claim of production stability. | Fixed cohorts remain separate; no unknown dataset may be silently interpreted as demo. | Preserve and regression-test |
| Test evidence | Previous focused Run `38995349182` reported 25/25 synthetic tests on SHA `3fdcdf8d006eff8f4a8fabb9ea2feb5c70c81633`, on a non-clean-main candidate base. | Run and artifact `12085749809` were inspected in the previous candidate context. | Evidence from that candidate does not certify this new clean-main branch/head. | Prior evidence only; this branch test status starts PENDING |

## Bounded change

1. Add `scripts/stage13_assemble.py` to implement the 185-sheet assembler and explicit adaptive-cohort evidence validation; it does not run Monte Carlo.
2. Replace the monolithic Excel entry path with an orchestrator/loader exposing new `build_excel(dataset_path, output_path, mode="canonical")` and legacy `build_workbook(dataset_root, output_path, manifest_path, representatives_path)` compatibility.
3. Re-export Stage 9C precision helpers from `scripts.excel_builder` and preserve older helper names where practical; delegate worksheet writing to Stage 13.
4. Add/retain synthetic tests for the assembler, adaptive mode resolution, and legacy imports/signatures.

## Acceptance criteria and evidence disposition

- Base ancestry must equal the exact main SHA above; no source-tree transplant from candidate commits is allowed except the scoped Stage 13 source/test blobs.
- Focused tests must run on the final tested branch SHA, and the actual test output/artifact must be inspected before PASS.
- Existing accepted Stage 9C numeric precision behavior and imports must remain intact.
- A generated workbook acceptance gate must verify 185 exact worksheet names/order, README count, zero formulas and zero Excel-error cells.
- Test workflow files remain untouched. The previous temporary workflow approval was pinned to a different branch and is not reused on this branch. The connected GitHub toolset has no workflow-dispatch action, and local clone/test execution is blocked because this runtime cannot resolve `github.com`; therefore test execution on this exact branch cannot currently be performed without separate authorization for an exact-branch test workflow. Until such authorization/execution path exists, pytest remains `PENDING/BLOCKED`, not PASS.
- No state.json, main, production, dataset, RNG, seed, source SHA, release or merge updates are in scope.
