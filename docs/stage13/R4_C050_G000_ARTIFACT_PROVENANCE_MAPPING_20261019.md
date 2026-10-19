# R4 — C050_G000 artifact provenance mapping correction

**Date:** 2026-10-19  
**Mode:** evidence-backed metadata correction on the Stage 13 candidate branch only.

## R4 matrix

| Element | Current state | Governing evidence | Ruling |
|---|---|---|---|
| Main manifest | Blob `e796fa2443493b607f1f9c60b58eb63607959c26`; `enriched_artifacts.C050_G000=11503191706`; `enrichment_run_ids.C050_G000=37662891608` | Read-back from main; main remains protected and is not changed | Proven provenance mismatch |
| Artifact 11503191706 | ZIP SHA-256 `f575044fb6a50cb5ed71d6303c40bd77841a6d38b633c105e560a4731e0a94f9`; belongs to Run `37660610243`, branch `tmp/stage9a-06-enrich-20261007-v2`, head `43e320abb79c3db82bdb70b8c6dece883ea7676d` | Live artifact listing for Run 37660610243 and direct download/hash/member inspection | Not the artifact produced by the run named in the manifest |
| Artifact 11503510055 | ZIP SHA-256 `111eb7a2abd7b85625a02c55ee6f3140a14644ef253141bfdc3f8fc5ae4c287d`; belongs to Run `37662891608`, branch `tmp/stage9a-06-enrich-20261007-v3`, head `6128b22864bb171ba49ec15dbb42439a6513c30c` | Live artifact listing for Run 37662891608 and direct download/hash/member inspection | Correct artifact ID for the run already recorded in the manifest |
| Data identity | Both packages have scenario `C050_G000`, source SHA `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`, historical trial run ID `37225915321`, 450 trials, the same four representative trial assignments and identical hashes for `trial_results.parquet`, `daily_distribution.parquet`, four representative JSONs and `trial_fingerprints.json` | Both archives downloaded and every regular member byte-hashed | Core trial data/fingerprints are identical |
| Metadata difference | Only `scenario_metadata.json` differs: `log_events=true` vs `log_events="representative_trials_only"`; the package/tar hashes therefore differ | Direct read-only package inspection | Preserve both hashes as evidence; do not pretend the ZIPs are byte-identical |

## Minimal correction authorized for this candidate

Change only `artifact_manifest.enriched_artifacts.C050_G000` from `11503191706` to `11503510055` on `tmp/cp-stage13-excel-compat-20261017`, so the artifact ID and the already-recorded `enrichment_run_ids.C050_G000=37662891608` refer to the same Run.

Do **not** change `global_manifest_sha256`, `source_sha`, `master_seed`, RNG/sampling policy, scenario/cohort identity, trial IDs, trial results, Parquet files, reference, state, or any file on main. The correction changes provenance mapping only; it does not make a missing Max Case payload available and does not establish Stage 13 acceptance.

## Acceptance

After the candidate-only write, fetch the manifest back and verify: the new artifact ID, unchanged run ID, unchanged global/source identity and trial-count fields, and unchanged main HEAD/state. Retain the old artifact ID/hash and the current artifact ID/hash in the audit record. No workflow, tests, simulation, Trial, Checkpoint, workbook, merge, or Release is part of this correction.
