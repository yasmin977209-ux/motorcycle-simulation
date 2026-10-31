# D1 Builder Design — Reconstructed 2026-11-01

D1 source modules were reimplemented independently from the live D1 prompt and pinned GitHub Actions artifacts. The importer was not run.

## Components
- `s6_artifact_reader.py`: verifies artifact byte length and SHA-256, ZIP CRC, member uniqueness, safe paths and symlink absence; reads JSON, JSONL.GZ and Parquet in memory.
- `s6_deliverables_model.py`: typed shared model with provenance on every trial-result value; exact Decimal/Fraction JSON conversion and recursive float rejection.
- `s6_manifest_resolver.py`: read-only root/sidecar resolver; preserves original statuses and does not promote missing independent byte-size evidence to PASS.
- `s6_deliverables_builder.py`: validates frozen representative map, fingerprints, source/cohort/seed identity and 125/105/100+5 counts; no selection rerun or Trial execution.
- `s6_validate_representatives.py`: checks only the 100 S6 assignments against S6 aggregate Parquet; C100 assignments remain separate and are not compared to S6 Parquet.
- `s6_number_registry.py`: D2-ready source only; no D2 registry output is generated in D1.

## Frozen identities
Governing reference: v2.4.0 / D-2026-10-30-REFERENCE-V2.4.0 / `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`.
Historical S6 execution reference v2.3: `e5efaf0874384e8248c339ca10e248ea9e17e9f0882153b4ef88bc955b91d53f`.
S6: `da1a9ea9b5cd789c944de3f07b08395bb67c49e7` / `s6-v23-da1a9ea9` / seed `20270101`.
C100: `965281d52441cd0d4b744e211c9f68ee4cdc3753` / `c100-v23-s4-20261026-965281d5` / `CROSS_COHORT_DETERMINISTIC_REUSE`.

Frozen map = 125 role assignments / 105 unique keys / 100 S6 + 5 C100. Full Logging remains 105 representative keys only, not 48,000 trials. Missing historical accounting fields are not backfilled or zero-filled.