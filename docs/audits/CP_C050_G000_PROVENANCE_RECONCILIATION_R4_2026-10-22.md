# R4 — Reconcile Stage 9A C050_G000 artifact/run identity — 2026-10-22

## Scope and boundaries

- Base/current main HEAD at start: 7621ddefe6c971e9eb231eb2a987519c86a2cb51.
- Candidate branch: tmp/cp-c050-g000-provenance-reconcile-20261022.
- Classification: K_PROVENANCE / MANIFEST IDENTITY CORRECTION.
- Change requested: update only the C050_G000 enriched-artifact pointer in the canonical Stage 9A manifest from Artifact 11503191706 to Artifact 11503510055, in the two mirrored manifest locations (artifact_manifest.enriched_artifacts.C050_G000 and scenarios.C050_G000.enriched_artifact_id). Keep the recorded enrichment Run 37662891608 unchanged.
- No direct main write, no merge/release, no trial/checkpoint, no production workbook build, and no historical artifact mutation.

## Direct live API evidence

| Property | Current manifest pointer (V2) | Matching recorded run (V3) |
|---|---|---|
| Artifact ID | 11503191706 | 11503510055 |
| Artifact name | stage9a06-enriched-C050_G000 | stage9a06-enriched-C050_G000 |
| Actual producing Run | 37660610243 | 37662891608 |
| Producer branch | tmp/stage9a-06-enrich-20261007-v2 | tmp/stage9a-06-enrich-20261007-v3 |
| Producer head | 43e320abb79c3db82bdb70b8c6dece883ea7676d | 6128b22864bb171ba49ec15dbb42439a6513c30c |
| Run conclusion | success | success |
| ZIP size | 17,786,146 bytes | 17,787,110 bytes |
| Artifact ZIP SHA-256 | f575044fb6a50cb5ed71d6303c40bd77841a6d38b633c105e560a4731e0a94f9 | 111eb7a2abd7b85625a02c55ee6f3140a14644ef253141bfdc3f8fc5ae4c287d |

This proves the existing manifest pairing is internally inconsistent: it records Run 37662891608 while the referenced Artifact 11503191706 belongs to Run 37660610243. Artifact 11503510055 belongs to the recorded Run.

## Independent archive read-back

Both artifacts were downloaded from the live GitHub Actions artifact API and independently hashed locally. The actual ZIP byte lengths and SHA-256 values match their live API metadata. Each archive contains exactly one C050_G000.tar.gz member; both inner archives contain the same eight regular files.

Seven payload/data files are byte-identical:

- daily_distribution.parquet: SHA-256 caf8de98e7e907b01cb87ee2cfc879293a3acb740290f0d2a8ab6867ebb13cd3.
- trial_results.parquet: SHA-256 09c223d8348f93a5c5e9246a409614d6345a76b224ff65f865c6bdbaea5fbbe8.
- trial_fingerprints.json: SHA-256 82cb7a2725944edc3b749bcc722d22040459baac2db6c68f3c0ddde98b0db8f6.
- All four representative payloads: P10, P50, P90 and Loss; each file hash matched byte-for-byte across V2 and V3.

The only regular-file difference is scenario_metadata.json:

- V2: 887 bytes, SHA-256 21e2f33603e21346ae84873f372d39e301f399a0f449eb5db8e195e742d51735, with log_events=true.
- V3: 911 bytes, SHA-256 a143c3fb7f2cee8ab625b0beb40295ede2c5879975d08f455e59b85406004cab, with log_events=representative_trials_only.

The source/workflow inspection recorded in the integration audit explains this metadata difference: V2's workflow checked out the original enrichment control branch rather than its named V2 control branch, so its metadata describes the old log_events=true writer. V3 checked out its V3 control branch and generated the representative-only logging metadata expected by the recorded Run. TrialResult, daily-distribution, fingerprint and four role payloads remain exactly equal.

## Identity-preservation proof requirements

The manifest correction must preserve all the following:

- global_manifest_sha256: 892da438955160bb59aff3046271402f57bdd61a4abb35f41db7188f61346ff6.
- Source SHA: f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b.
- Master seed: 20270101.
- Scenario count: 25; C050_G000 trial count: 450; all representative assignments/values/fingerprints unchanged.
- Stage 11 identity record blob: 72a481d509d39820fba78732724fde4fa9f25134 (not modified by this CP).
- All other 24 scenario artifact IDs and all non-C050 manifest content unchanged.
- No change to TrialResult, Parquet, source SHA, RNG, seed, cohort or trial IDs.

Because this is a provenance-pointer correction rather than a data change, the global fingerprint is expected to remain unchanged; that expectation must be checked with an exact JSON diff before accepting the candidate.

## Verification / acceptance

1. Fetch the live main manifest and verify base blob e796fa2443493b607f1f9c60b58eb63607959c26.
2. Read back the candidate manifest; verify the two C050 pointers both equal 11503510055, enrichment_run_ids.C050_G000 remains 37662891608, and the scenario/data fingerprints are unchanged.
3. Compute a structured JSON diff: exactly the two duplicated artifact-ID values change; no other value changes.
4. Validate the candidate manifest with the Stage 13 source-audit helper/unit tests (synthetic input only, no canonical workbook build).
5. Run read-only identity assertions confirming V3's artifact ID/run pair exists in live API, the two archives' payload members remain equal apart from scenario metadata, and all canonical global/source/seed identity fields are unchanged.
6. Keep this on a draft PR. This R4 and the tests provide a reviewable correction; no main merge is included.

## Still unresolved after this correction

This change resolves only the C050_G000 artifact/run pointer conflict. It does not resolve missing Partner 1/Partner 2 MaxCase daily memo balances for the 20 non-C100 scenarios, does not provide Gate A provider coverage, does not resolve the undefined Stage 11 execution topology, and does not accept the seven-file delivery. Those remain explicit MISSING_EVIDENCE/blocked items.

## Initial status

PENDING_MANIFEST_WRITE_AND_EXACT_READBACK. No manifest has been changed yet.
