# R4 — Correct C050_G000 artifact/run pairing from live provenance — 2026-10-22

## Scope and authorization

- Base/main HEAD: `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`.
- Candidate branch: `tmp/cp-c050-provenance-correction-20261022`.
- Classification: `K_PROVENANCE / one-field manifest repair`.
- Owner has explicitly delegated all work necessary in the current conversation on 2026-10-21, including technical changes and tests. This CP applies that authorization only to the exact, evidence-backed C050_G000 pointer inconsistency; it does not permit changes to source identity, cohort, trial IDs, data values, fingerprints, or overall project acceptance.
- Target file: `docs/stage9a/dataset_manifest.json`, base Git blob `e796fa2443493b607f1f9c60b58eb63607959c26`.

## Direct live API evidence (retrieved on 2026-10-22)

The main manifest associates `C050_G000` artifact `11503191706` with enrichment Run `37662891608`. Direct GitHub API read-back shows:

| Item | Live run evidence | Live artifact evidence |
|---|---|---|
| Manifest artifact `11503191706` | Run `37660610243`, branch `tmp/stage9a-06-enrich-20261007-v2`, HEAD `43e320abb79c3db82bdb70b8c6dece883ea7676d`, conclusion success | Name `stage9a06-enriched-C050_G000`, size 17,786,146, SHA-256 `f575044fb6a50cb5ed71d6303c40bd77841a6d38b633c105e560a4731e0a94f9` |
| Manifest-recorded run `37662891608` | Branch `tmp/stage9a-06-enrich-20261007-v3`, HEAD `6128b22864bb171ba49ec15dbb42439a6513c30c`, conclusion success | Its `C050_G000` artifact is ID `11503510055`, same name, size 17,787,110, SHA-256 `111eb7a2abd7b85625a02c55ee6f3140a14644ef253141bfdc3f8fc5ae4c287d` |

The recorded run ID therefore contradicts the artifact ID in exactly this one manifest entry. A prior direct archive comparison found seven payload/data files byte-identical across V2/V3, while `scenario_metadata.json` is the only regular-file difference: the V2 artifact says `log_events: true`, the V3 artifact says `log_events: "representative_trials_only"`. Producer/workflow inspection found V2's workflow checked out an older control branch despite the V2 run HEAD; V3 checked out the V3 control branch. The existing manifest's scenario metrics, representative trial IDs, counts, source SHA, seed, and global dataset fingerprint remain unchanged by this proposed pointer correction.

## Minimal change

Change only `artifact_manifest.enriched_artifacts.C050_G000` from `11503191706` to `11503510055`, so the stored artifact pointer resolves to the artifact created by the already-recorded `enrichment_run_ids.C050_G000=37662891608`.

Do not change:
- `enrichment_run_ids.C050_G000` (already correct);
- the 9005-trial/global fingerprint, scenario representative IDs, scenario counts, source SHA or master seed;
- any Parquet, representative JSON payload, historical artifact, Stage 11 identity, workbook, Gate A coverage, or runtime logic.

## Verification contract

A read-only, candidate-only checker will query the two unique recorded Runs, verify every one of the 25 scenario artifact/run pairs against the live Actions API, and fail if any ID, artifact name, run ID, digest, or expiration state is inconsistent. A deterministic unit test will assert that the candidate manifest preserves all identity values and carries the corrected C050_G000 pairing. The workflow will checkout the exact candidate SHA, use only `contents: read` and `actions: read`, and upload JSON evidence. It will not download or modify production datasets or build a workbook.

## Acceptance limits

- Passing this CP resolves the manifest artifact/run metadata inconsistency for C050_G000 only.
- It does not establish that the incomplete MaxCase Partner 1/2 memo balances exist. They remain `MISSING_EVIDENCE`.
- It does not establish Gate A/provider readiness, clear the model `SOURCE_SHA_DRIFT`, define Stage 11 topology, or accept Stage 13/final delivery.
- No historical artifact is rewritten; only a candidate manifest pointer changes. Main remains unchanged and this change must be reviewed before merge.

## Status

`PENDING_CHANGE_AND_EXACT_SHA_CHECK`.
