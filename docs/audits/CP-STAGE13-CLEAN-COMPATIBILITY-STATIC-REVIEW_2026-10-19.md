# CP-STAGE13-CLEAN-COMPATIBILITY-STATIC-REVIEW — 2026-10-19

## Disposition

**Candidate-only architecture/static review complete for the bounded check; exact-head tests and workbook generation remain PENDING/BLOCKED.** This CP made no changes to main or to workflow files.

## Live identities

- Clean-main Stage 13 candidate: `tmp/cp-stage13-excel-compat-20261017`, HEAD `c627b94230ccadca7552c835959a4299a10ac70e`.
- Base/main: `647c19826b90d8224ce73ef9b90c306a45e03fb0`; compare ahead 7 / behind 0, exactly eight changed paths (two R4 docs, authorization record, builder, assembler, two test modules and assembler tests).
- Current candidate blobs: builder `8dec3578a8221a6b12fb0915103cb09664f20a96`; assembler `1548d4393cd79922abfd570f1c9a90454d7e40fe`; assembler tests `68c64ea6a63c12b0cbc8602db44cdfa15d23c094).
- Main `state.json` blob stays `2178260bb18efeb81437486f13b6d10cf5e85936`.

## What static review confirmed

1. The candidate orchestrator follows the target separation: `scripts/excel_builder.py` delegates workbook creation to `scripts/stage13_assemble.py` and offers `build_excel(dataset_path, output_path, mode="canonical")` plus the legacy `build_workbook` path.
2. The candidate re-exports compatibility helpers needed by the current Stage 9C precision code/tests, including `patch_xlsx_numeric_values` and `save_workbook_preserving_stats_precision`; the legacy compatibility tests assert public names and signatures and the legacy daily-distribution writer route.
3. The Stage 13 writer contains the dictionary-to-value-row correction for per-scenario DAILY sheets: `value_rows = [[row.get(h) for h in headers] for h in headers]` is not the expression in source; the actual line is `value_rows = [[row.get(h) for h in headers] for row in rows]`. This matches the separate candidate P50 correction's minimal pattern. This is source inspection, not a generated-workbook pass.
4. `assemble_workbook` validates the 185-sheet expected names/order, 25 statistics sheets, 25 DAILY sheets, README sheet count, and zero formula/error cells after saving. These are acceptance checks in code, not proof that this candidate successfully generated an XLSX under this CP.
5. The new per-trial fingerprint binding correction from the adaptive candidate was ported surgically to this cleaner branch; its assembler/test blobs now exactly match the read-back candidate versions, including the strict 18-field TrialResult schema, canonical JSON digest recomputation, stale-digest and schema-drift regression cases.

## R4 / run authority conflict

Two live candidate documents conflict:
- `docs/stage13/OWNER_SCOPE_AUTHORIZATION_20261017.md` states an explicitly authorized temporary, read-only test workflow pinned to `tmp/cp-stage13-excel-compat-20261017`.
- `docs/stage13/R4_clean_main_excel_compat_20261017.md` states the prior temporary workflow approval was pinned to another branch and is not reused here, and that an exact-branch test path needs separate authorization.

The workflow file is currently absent (404) on this branch. No workflow was created/modified or triggered, no pytest was run and no workbook was generated in this CP. Since the evidence conflicts, runtime testing remains `PENDING/BLOCKED); the previous adaptive candidate Run `38995349182` does not test the current builder/test blobs or amended fingerprint logic.

## Protected state and blockers

main remains `647c19826b90d8224ce73ef9b90c306a45e03fb0), stage `12-CLOSED`, `repository_status=FINAL_DELIVERY_BLOCKERS_OPEN`, `source_sha=f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`. `scripts/stage13_assemble.py` remains absent from main. Stage 9C stays `PARTIAL`; Gate A provider, SOURCE_SHA drift, Stage 11 topology definition, Stage 13 adoption and final seven-file reconciliation remain open. PR #46 remains open/Draft/unmerged. No merge, Release, production simulation, trial, checkpoint, reference/data/source/seed/RNG or main-state change occurred.

## Next permitted action

Resolve the exact-branch test-workflow authorization conflict before performing a new workflow change. Continue independent read-only reconciliation of delivery evidence; keep this candidate `PARTIAL / NOT_READY_TO_MERGE` until its exact-head synthetic tests and a separate physical workbook audit pass.
