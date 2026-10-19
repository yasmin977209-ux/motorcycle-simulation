# CP — Stage 13 representative payload coverage: read-only contract audit

**Date:** 2026-10-19  
**Mode:** R4/read-only data-contract inspection. No source, data, test, Workflow, or workbook changes.

## Live evidence

- Main HEAD before the accidental report commit: `647c19826b90d8224ce73ef9b90c306a45e03fb0`; current observed main HEAD after that one-file commit is `b70cc0b7517b4f5f8a559b035bea166059b269ea`.
- Main `docs/stage9a/dataset_manifest.json` blob `e796fa2443493b607f1f9c60b58eb63607959c26`: `total_trials=9005`, `total_representatives=100`, 25 scenario keys, source SHA `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`.
- Main `scripts/excel_builder.py` blob `50115a2fea5812727e0e5a8bfbb07e1f853f026b`, `write_representatives` reads only `P10`, `P50`, `P90`, and `Loss` payloads for each scenario. This is four roles × 25 = 100, matching the manifest count.
- Candidate `tmp/cp-stage13-excel-compat-20261017` HEAD `4fa2c633162b0134a48cfc2ccbf2b6b948108ae0`, assembler blob `7561f73340ac45b0f4ab71b677c33b771eac008b`, builder blob `8dec3578a8221a6b12fb0915103cb09664f20a96`.
- Candidate `load_dataset` attempts five role payloads for every non-demo scenario, including `Max Case`; when a scenario has nonempty trial rows, a missing role causes load failure. Candidate `_validate_representatives` likewise requires payload and daily rows for all five roles.

## R4 / contract assessment

The candidate implements the later normative decision D-2026-10-10-03 to add the fifth `Max Case` role, while the source dataset manifest and legacy builder are shaped for four roles. The main manifest is not an inventory of the actual per-scenario archive members, so `total_representatives=100` alone does **not** conclusively prove the archive lacks `Max Case` JSONs. The source package/archives and their identities were not available to inspect through the current GitHub file path, and no canonical dataset was downloaded, rewritten, or rebuilt in this CP.

Disposition: **`MISSING_EVIDENCE / POSSIBLE_SOURCE-CONTRACT_MISMATCH`**, not a proven runtime failure. Canonical Stage 13 acceptance remains blocked until the actual source package verifies that all 25 × 5 role payloads exist with expected summary/trial IDs and daily records, or a separately approved, identity-preserving derivation path produces the required fifth role using existing trusted evidence. Do not reduce the five-role requirement to match the old manifest; do not invent daily payloads or rerun trials.

## Constraints / next step

No canonical workbook was built; no pytest, CLI, production workflow, Monte Carlo, Trial, Checkpoint, or new artifact was run. No source SHA, seed/RNG, sampling, cohort, trial ID, historical data/Parquet, or reference changed. `state.json` blob remains `2178260bb18efeb81437486f13b6d10cf5e85936`, with `12-CLOSED / FINAL_DELIVERY_BLOCKERS_OPEN`. No PR was merged/closed and no Release was created. The candidate's runtime test authorization remains conflicted; the older Run `38995349182` applies only to its older SHA and does not verify current HEAD.

Next permitted step is an existing-input inventory: obtain/read the exact canonical enrichment artifact and hash, enumerate its members, count representative payloads by scenario/role, compare each summary `trial_id` to the approved representative assignments and the trial result cohort, and record missing daily records. No rebuilding or data mutation is required for that inventory.

## Note on repository write boundary

An earlier attempt to save this audit omitted the target branch argument and unexpectedly created this file on `main` in commit `b70cc0b7517b4f5f8a559b035bea166059b269ea`. The before/after compare returned exactly one added path (this audit file); `main/state.json` blob is unchanged. This was an unintended write. No additional action on `main` will be taken absent the separately required owner authorization to remove/revert that single documentation file.

## Addendum — source-package role count confirmed in main deviation record

A subsequent read of main `docs/stage9a/DEVIATIONS.md` (blob `ac8fb3e2dc65816bb2329aab19d4fe3c88d885d6`), line 25, states literally: “The enriched scenario artifact contains `trial_results.parquet`, `daily_distribution.parquet`, four representative JSON payloads, and fingerprints; it does not contain an individual daily accounting ledger for all trials.” This moves the fifth-role finding from merely a count-based possibility to a **documented source-contract gap**: the approved Max Case role was added after the artifact package contract that contains four representative payloads.

Candidate `load_dataset` iterates `P10`, `P50`, `P90`, `Loss`, and `Max Case`; missing payloads for a populated non-demo scenario are fatal, and representative validation also requires a nonempty daily record. The current source package description expressly supplies only four representative payloads. The candidate therefore cannot claim complete canonical five-role input coverage from the documented enriched package contract as-is. This is a source/input-contract mismatch, not proof that a particular artifact byte stream has been opened in this session; no zip containing the 25 current enriched packages was available for member-level enumeration.

**Updated disposition:** `INPUT_CONTRACT_MISMATCH_DOCUMENTED / MAX_CASE_PAYLOAD_MISSING_FROM_SPECIFIED_FOUR-ROLE-PACKAGE_CONTRACT / CANDIDATE_CANONICAL_BUILD_NOT_VERIFIED`. The approved fifth role must be produced from an identity-matched, already-authorized source of the selected trial's summary and full daily accounting, or a separately approved data-contract decision. No representative trial IDs are changed, no missing daily rows are synthesized, and no historical trials are rerun here. The Stage 13 candidate's exact-branch workflow authorization conflict remains in force.

