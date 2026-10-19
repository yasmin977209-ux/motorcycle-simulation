# CP — C050_G000 artifact provenance, MaxCase route, and bounded runtime validation

**Date:** 2026-10-19  
**Mode:** evidence-backed candidate metadata correction plus read-only contract analysis; synthetic-only runtime verification is separate and tied to its own exact SHA.

## 1. C050_G000 source-artifact conflict — resolved at provenance level

Live GitHub artifact lists establish:

| Artifact ID | Originating Run | Branch / head | ZIP SHA-256 |
|---:|---:|---|---|
| `11503191706` | `37660610243` | `tmp/stage9a-06-enrich-20261007-v2` / `43e320abb79c3db82bdb70b8c6dece883ea7676d` | `f575044fb6a50cb5ed71d6303c40bd77841a6d38b633c105e560a4731e0a94f9` |
| `11503510055` | `37662891608` | `tmp/stage9a-06-enrich-20261007-v3` / `6128b22864bb171ba49ec15dbb42439a6513c30c` | `111eb7a2abd7b85625a02c55ee6f3140a14644ef253141bfdc3f8fc5ae4c287d` |

The main manifest's `enrichment_run_ids.C050_G000` is `37662891608`, but its `artifact_manifest.enriched_artifacts.C050_G000` was `11503191706`, an artifact produced by a different run. Both ZIPs were downloaded and hashed locally; both open and contain the same scenario TAR. All seven non-metadata files inside the TAR are byte-identical, including four representative JSONs, both Parquet files and trial fingerprints. `scenario_metadata.json` alone differs: `log_events=true` in v2 versus `log_events="representative_trials_only"` in v3. Both packages record source SHA `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`, historical trial run ID `37225915321`, scenario `C050_G000`, 450 trials and the same representative assignments/block fingerprints.

### Candidate-only correction

- R4 report: `docs/stage13/R4_C050_G000_ARTIFACT_PROVENANCE_MAPPING_20261019.md`, blob `5c758005d70952ba700ad58f6c324153cac3f9d9`, read back before edit.
- Changed only `artifact_manifest.enriched_artifacts.C050_G000` from `11503191706` to `11503510055` on `tmp/cp-stage13-excel-compat-20261017`.
- Candidate manifest commit: `7f4d35232a60452c64eebe214a24f5ac215341d2`; manifest blob after read-back `ec0d4749f86c6f81d743dbb071f92e9f0eddef3d`.
- Deep comparison against main's manifest found exactly one field difference: `artifact_manifest.enriched_artifacts.C050_G000`. `enrichment_run_ids.C050_G000=37662891608`, `source_sha`, `global_manifest_sha256=892da438955160bb59aff3046271402f57bdd61a4abb35f41db7188f61346ff6`, `master_seed=20270101`, total trials and representative count are unchanged.
- Main was not changed: HEAD remains `7c41ac64c4b599f4e1d6a50be055f82cdd87a7b5`; state blob `2178260bb18efeb81437486f13b6d10cf5e85936`; `12-CLOSED / FINAL_DELIVERY_BLOCKERS_OPEN`.

## 2. MaxCase — normative rule confirmed; payload route remains conditional

Normative authority is D-2026-10-10-03 / Amendment-03, not a report or candidate implementation:

- Select the row with the highest **positive** `Final_Net_Project_Equity`; break ties by the smallest `trial_id`.
- If no positive value exists, return `UNDEFINED_BUSINESS_RULE` and hold approval for that scenario; no substitute role may be invented.
- Candidate `select_representative_trial_ids` implements that selection and the no-positive fail-closed condition.

The inspected source-package contract is still only four representative payloads (`P10`, `P50`, `P90`, `Loss`) plus `trial_results.parquet`, `daily_distribution.parquet`, and fingerprints. The aggregate daily-distribution file is not the individual full daily-accounting ledger required for a representative case. No inspected package contains a MaxCase JSON.

**Safe route using already-authorized evidence:**
1. Derive the normative MaxCase `trial_id` from the identity-matched existing `trial_results.parquet` for each scenario, without changing the cohort or IDs.
2. If that exact `trial_id` is already one of the four stored representatives, reuse that existing payload only after verifying its summary equals the selected trial-result row and its full daily records/terminal values bind to the same ID.
3. If the selected ID is distinct and no identity-matched full daily payload already exists elsewhere, keep the scenario blocked. Do not synthesize daily rows, relabel P90, or replay a completed trial without separate explicit authorization.

Therefore the **selection rule is approved**, but there is **no approved complete payload-materialization path for a distinct missing MaxCase** in the currently inspected source set. The next safe step is a read-only inventory of any existing identity-matched full daily payloads. If none exists, owner approval must explicitly define the narrow materialization/replay scope and acceptance criteria before any such run; no such run was started here.

## 3. Code validation — exact-SHA boundary

### Stage 13 strict trial_id fix
- Candidate source blob `71e05034bafb551aea2949adc94013e8bb23d239` on code head `250b855c9ad97875c92e3dc682e6e2f7b2071a2a` requires exact `int` types for summary and daily `trial_id`.
- R4: `docs/stage13/R4_SYNTHETIC_RUNTIME_VERIFICATION_20261019.md`, blob `7c0a354d54260998412be2153595b3bf62d7b52b`.
- Temporary workflow `.github/workflows/cp-stage13-synthetic-compat-verify.yml` was added under the scoped owner authorization with read-only contents permission, branch/path restrictions, synthetic fixtures only, no `workflow_dispatch`, and bounded artifact retention.
- The first Actions query found Run `39299680243`, event `push`, status `in_progress`, exact workflow head `027e452e3af5a27de9f465b96c00255efa46e4f2`. This is not a PASS. The run is pinned to that SHA; the later candidate manifest metadata correction does not change its tested source/test files or trigger another run.
- After the run completes, inspect its logs and uploaded artifact once; then remove the temporary workflow on this candidate branch as the owner authorization requires. Do not substitute an older run or claim a runtime result without exact-SHA evidence.

### Stage 10 JSON newline fix
An isolated execution of the exact read-back `write_json` function from candidate `47bcd45076f9a264307a30e5cddae51855ff2a42` passed AST compilation, JSON round-trip and actual terminal-newline assertions. This is an isolated function check only: no repository pytest/Actions run, CLI, benchmark, simulation or trial was run for that SHA.

## 4. Boundaries and remaining blockers

No source code, tests, model source, Parquet data, historical trial output, seed/RNG, sampling policy, cohort, trial ID, reference, main, state, production workflow, Monte Carlo, Trial, Checkpoint, canonical workbook, merge, delivery acceptance or Release was changed or performed in this CP. The candidate manifest correction is limited to one artifact-ID provenance field. Stage 13 remains blocked by missing distinct MaxCase full daily payloads and other project gates. Overall project status remains `FINAL_DELIVERY_BLOCKERS_OPEN`.

The continuity ledger `docs/PROJECT_CONTINUITY.md` is not updated by this report; a prior code-CP append was blocked by platform safety, so no bypass was attempted. This report is to be registered in `docs/continuity/SESSION_OUTPUTS.jsonl` on the continuity branch after read-back.
