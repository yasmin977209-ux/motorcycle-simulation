# Stage 13 diagnostic workbook assembly — 2026-10-24

## Purpose and status

This is a bounded diagnostic execution only. It downloads and rehashes the 25 existing Stage 9A enriched artifacts selected by the current canonical manifest and inventory, validates the digest-pinned MaxCase source audit and exact selected-Trial replay bundle, and invokes the current Stage 13 adapter over these existing files.

The workflow must fail if the top-level statistical gate is not BLOCKED_FOR_IMPLEMENTATION, if any production execution or final acceptance authorization is true, or if the assembler emits a final-acceptance status other than NOT_FINAL_BLOCKED. It does not call monte_carlo.run_single_trial, start the simulation engine, generate new Trial IDs, alter Stage 12, write the canonical manifest, merge data, or create a release.

## Inputs pinned

- Canonical manifest: docs/stage9a/dataset_manifest.json, Git blob identity expected by the payload inventory c8591aac3d309fd94c4e67a547d33fb62ac5694d.
- Inventory: docs/audits/stage9a_payload_inventory_20261020.json, containing 25 explicit artifact IDs and ZIP SHA-256 values.
- MaxCase source audit ZIP artifact ID 12544311885, ZIP SHA-256 93b150e5d3360c8d160f3facad85c28dc676819466ed3fded3167bcb703c3f32.
- Exact selected-Trial replay ZIP artifact ID 12542814312, ZIP SHA-256 85e0d747044910d8d9837085b3a221a7459feb418eb78776ae3b4f1a31f5db68; recovery JSON SHA-256 c477e390a5b0b9c8c35a3d5474e5b359056e59d1f2254395e589af4621982006.

The workflow independently checks each source archive size and SHA-256, exact archive member names, manifest-to-artifact pointer, audit/replay pair semantics, Stage 12 common-field agreement and selected Trial fingerprints before workbook construction.

## Acceptance boundary

Even a successful workbook build remains NOT_FINAL_BLOCKED. The workbook is named Stage13_Diagnostic_Candidate_NOT_FINAL.xlsx; the uploaded artifact is explicitly stage13-diagnostic-candidate-not-final-<run-id>. This is not the required seven-file Arabic/English final delivery, not P17/P18 release acceptance, and not a statistical gate pass. Current known blockers remain: time-uniform financial-mean inference/K_SPEC, unintegrated quantile and Bernoulli candidates, incomplete Golden coverage, P90_Held_Assets acceptance, historical C030_G030 N=300→600 P90_Final_Cash failure, Stage 10 metadata/fidelity drift, and G2 runtime evidence.

## Verification evidence

The run report records the exact tested commit, manifest digest, all 25 artifact ids/digests, audit/replay digests, workbook SHA-256, sheet count, MaxCase scenario coverage, memo-field pending count and Excel error count. Missing evidence or any identity mismatch is a hard failure and is not repaired by rerunning the model.
