# CP — Stage 13 representative payload coverage: read-only contract audit

**Date:** 2026-10-19  
**Mode:** R4/read-only data-contract inspection. No source, data, test, Workflow, or workbook changes.

## Live evidence

- Main HEAD: `647c19826b90d8224ce73ef9b90c306a45e03fb0`.
- Main `docs/stage9a/dataset_manifest.json` blob `e796fa2443493b607f1f9c60b58eb63607959c26`: `total_trials=9005`, `total_representatives=100`, 25 scenario keys, source SHA `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`.
- Main `scripts/excel_builder.py` blob `50115a2fea5812727e0e5a8bfbb07e1f853f026b`, `write_representatives` reads only `P10`, `P50`, `P90`, and `Loss` payloads for each scenario. This is four roles × 25 = 100, matching the manifest count.
- Candidate `tmp/cp-stage13-excel-compat-20261017` HEAD `4fa2c633162b0134a48cfc2ccbf2b6b948108ae0`, assembler blob `7561f73340ac45b0f4ab71b677c33b771eac008b`, builder blob `8dec3578a8221a6b12fb0915103cb09664f20a96`.
- Candidate `load_dataset` attempts five role payloads for every non-demo scenario, including `Max Case`; when a scenario has nonempty trial rows, a missing role causes load failure. Candidate `_validate_representatives` likewise requires payload and daily rows for all five roles.

## R4 / contract assessment

The candidate correctly implements the later normative decision D-2026-10-10-03 to add the fifth `Max Case` role, while the source dataset manifest and legacy builder are shaped for four roles. The main manifest is not an inventory of the actual per-scenario archive members, so `total_representatives=100` alone does **not** conclusively prove the archive lacks `Max Case` JSONs. The source package/archives and their identities were not available to inspect through the current GitHub file path, and no canonical dataset was downloaded, rewritten, or rebuilt in this CP.

Disposition: **`MISSING_EVIDENCE / POSSIBLE_SOURCE-CONTRACT_MISMATCH`**, not a proven runtime failure. Canonical Stage 13 acceptance remains blocked until the actual source package verifies that all 25 × 5 role payloads exist with expected summary/trial IDs and daily records, or a separately approved, identity-preserving derivation path produces the required fifth role using existing trusted evidence. Do not reduce the five-role requirement to match the old manifest; do not invent daily payloads or rerun trials.

## Constraints / next step

No canonical workbook was built; no pytest, CLI, production workflow, Monte Carlo, Trial, Checkpoint, or new artifact was run. No source SHA, seed/RNG, sampling, cohort, trial ID, historical data/Parquet, main/state, or reference changed. No PR was merged/closed and no Release was created. The candidate's runtime test authorization remains conflicted; the older Run `38995349182` applies only to its older SHA and does not verify current HEAD.

Next permitted step is an existing-input inventory: obtain/read the exact canonical enrichment artifact and hash, enumerate its members, count representative payloads by scenario/role, compare each summary `trial_id` to the approved representative assignments and the trial result cohort, and record missing daily records. No rebuilding or data mutation is required for that inventory.
