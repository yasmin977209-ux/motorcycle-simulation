# R4 — Stage 13 canonical dataset fingerprint binding

- Date: 2026-10-19
- CP: `CP-STAGE13-CANONICAL-IDENTITY-FINGERPRINT-BINDING`
- Candidate branch: `tmp/cp-stage13-excel-compat-20261017`
- Candidate HEAD before change: `4fa2c633162b0134a48cfc2ccbf2b6b948108ae0`
- Base/main HEAD: `647c19826b90d8224ce73ef9b90c306a45e03fb0`
- Main `docs/stage11/dataset_identity.json` blob: `72a481d509d39820fba78732724fde4fa9f25134`
- Main `docs/stage11/global_manifest_11005_reconciled.json` blob: `b8947a60051a244784248875f5e0435b9996d95b`
- Main `docs/stage9a/dataset_manifest.json` blob: `e796fa2443493b607f1f9c60b58eb63607959c26`

## R4 — before change

| Item | Current state | Governing reference / approved decision | Controlling text | Ruling |
|---|---|---|---|---|
| Canonical mode dataset integrity | `_validate_mode_and_identity` checks expected `source_sha`, the scenario names, unique positive IDs, exact canonical ID ranges (C100: ID 1; others: 1..550), and 11,005 total rows. It does not load `docs/stage11/dataset_identity.json` or compare the actual canonical row content to the recorded per-scenario fingerprint. A changed monetary result row can preserve scenario and trial IDs and still satisfy these checks. | Main `DECISIONS_LOG.md`, D-2026-10-10-04; main Stage 11 `dataset_identity.json`; main `scripts/stage13_gatea_fingerprint_bridge.py` and its R4. | D-2026-10-10-04 declares canonical mode = 11,005 trials. Stage 11 identity records 25 scenarios and 11,005 trials; non-C100 combined 1..550 fingerprints are in `combined_dataset_fingerprint_sha256_stage10`; C100's canonical single-trial hashes are in `scenario_fingerprint_stage9a`. The Gate A bridge documents row-level SHA-256 recomputation and exact source fingerprint equality. | `K_CODE`: count/source-label validation alone does not bind canonical workbook input data to the authoritative 11,005-trial dataset. This is a validation gap; it does not prove that current production Parquet is corrupted. |
| Full dataset identity vs Stage 9A baseline | Stage 9A manifest's `global_manifest_sha256=892da438...` identifies only 9,005 baseline trials, not the full 11,005-trial set. Stage 11 explicitly says there is no new global hash for 11,005; the official full-scope identity is represented by per-scenario Stage 7/Stage 10 fingerprints. | Main `docs/stage11/R4_manifest_reconciliation.md` and `global_manifest_11005_reconciled.json`. | The reconciled R4 says to preserve separate the 9,005 Stage 9A hash and the 11,005 per-scenario identity; do not treat the former as the latter. | The minimal correction must use the 25 per-scenario canonical fingerprints; do not substitute the Stage 9A global hash. |
| Other build modes | Sample mode has a separate `STAGE13_SAMPLE_TRIAL_IDS_26_50_V2` cohort and demo mode is a small fixture; adaptive mode has its own ordered SHA-256 map. | D-2026-10-10-04 and the existing distinct-mode validations. | Canonical=11005, sample=625, demo=small fixture; adaptive is identified by `STAGE13_ADAPTIVE_STABLE_PER_SCENARIO_V1`. | This CP must not conflate the cohorts or invent an identity for the separate 625-trial sample. The corrective trusted-fingerprint check applies only to canonical mode. |

## Minimal correction

In canonical mode only, load the checked-in Stage 11 `dataset_identity.json` from the repository-relative path, require its Git blob identity and required top-level provenance/count/scenario fields to be the reviewed values, and recompute per-scenario fingerprints using the existing documented Stage 7/Stage 10 canonicalization: recursively encode Python floats with `float.hex()`, sort row keys, JSON separators `(",", ":")`, sort rows by `trial_id`, join the canonical JSON rows with one newline, and SHA-256 the result.

Compare each C100 single-trial hash against `scenario_fingerprint_stage9a`; compare each non-C100 550-trial hash against `combined_dataset_fingerprint_sha256_stage10`. Fail closed on missing/invalid identity metadata, bad trial coverage, or any mismatch. Do not use the Stage 9A 9,005 global hash as the 11,005 canonical identity. Leave sample/demo/adaptive handling and trial IDs unchanged.

## Acceptance criteria

1. A canonical input whose 11,005 rows match the recorded per-scenario identity passes this focused identity validation.
2. Changing any financial/result field while preserving scenario/Trial IDs is rejected as `CANONICAL_SCENARIO_FINGERPRINT_MISMATCH: <scenario>`.
3. The trusted identity file must be the reviewed blob; missing, edited, incomplete, mismatched or malformed identity is an explicit failure.
4. The check must distinguish the five C100 one-trial scenarios from the 20 non-C100 550-trial scenarios.
5. Stage 9A's global fingerprint stays scoped to its 9,005-row baseline; no new global fingerprint is invented for 11,005.
6. No production trial, source/seed/RNG/policy/cohort change, historic data edit, Workflow edit, main/state/reference change, merge or Release. Tests remain pending while the existing exact-branch test-Workflow authorization conflict is unresolved.

## Execution status before change

This R4 is written before implementation edits. Scope is the Stage 13 candidate assembler and synthetic tests only.
