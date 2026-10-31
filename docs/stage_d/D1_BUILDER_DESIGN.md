# D1 — Independent S6 Deliverables Builder Design

**Classification:** `T2_INTERIM / NOT_FINAL_BLOCKED`  
**Local status:** `D1_COMPLETE / PASS_SCOPED_WITH_LIMITATIONS`  
**Repository publication:** pending complete source-bundle publication.

## Architecture
The local package is an S6-only read-only pipeline with four core components:

| Module | Responsibility | Public API |
|---|---|---|
| `scripts/s6_artifact_reader.py` | Pinned ZIP inputs, digest/size/CRC/path checks, identity validation, read-only member access. | `S6ArtifactReader(paths).open_all()`, `Archive.read_json()`, `Archive.iter_jsonl_gzip()`, `Archive.read_parquet()` |
| `scripts/s6_deliverables_model.py` | Source-attributed shared model and exact-safe serialization. | `SourceRef`, `SourcedValue`, `S6SharedModel`, `sourced()`, `to_jsonable()` |
| `scripts/s6_manifest_resolver.py` | Read-only comparison of trial manifest, sidecar and root manifest. | `resolve_trial_manifest()`, `resolve_full_logging_archive()` |
| `scripts/s6_deliverables_builder.py` | Cohort identity, frozen role-map validation and shared-model assembly. | `build_shared_model()`, `exact_fraction()`, `display_decimal()` |

D2 adds `scripts/s6_number_registry.py` for exact arithmetic and central number provenance. No Stage 13 assembler, legacy Excel builder, Stage 12/13 role selector, simulator, Trial runner or Monte Carlo runner is imported or called.

## Fixed inputs and identities
- Aggregate: Artifact 12852969854 / Run 40773412377 / SHA-256 `ec05a69ae8968585decf83cf0716d56c264f47f86187cfd3cf53b11f52ca2e54`.
- Full Logging: Artifact 12998778418 / Run 41098699740 / SHA-256 `403371cc8eb12880dda05529b4c83dd675bfa609e8680c09d35efa729c5b5aeb`.
- C100 reuse: Artifact 12630457193 / Run 40263424595 / SHA-256 `c977d1cbb5204919eadc72358533f77cdbbc239902bcd6f921bf1a915a716e79`.
- S6: source `da1a9ea9b5cd789c944de3f07b08395bb67c49e7`, cohort `s6-v23-da1a9ea9`, seed 20270101.
- C100: source `965281d52441cd0d4b744e211c9f68ee4cdc3753`, cohort `c100-v23-s4-20261026-965281d5`, deterministic reuse only.

Historical S6 execution reference v2.3 is kept separate from current governing v2.4.0. The historical digest is sourced from `docs/PROJECT_CONTINUITY.md#L1889` and remains `REPORTED_ONLY`; current governing SHA-256 is `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`.

## Role map and manifests
The frozen map is checked for 125 assignments, 25 scenarios × five roles, 105 unique keys (100 S6 + 5 C100), and exact key-set equality with the Full Logging root. P50/P10/P90 use nearest observed linear-quantile targets with smallest trial_id tie-break. LossCase is argmin Final_Net_Project_Equity; MaxCase is argmax Final_Net_Project_Equity without positivity condition. No re-selection occurs. Full Parquet value-level revalidation remains NOT_VERIFIED because Parquet support is unavailable.

Resolver preserves original manifest status and derives a separate `normalized_audit_status`. PASS_SCOPED requires SHA, size, source/cohort/trial identity, fingerprints, sidecar PASS and root PASS. Independent expected sizes are absent; all 105 normalized states remain NOT_VERIFIED.

## Numeric rules and failure behavior
Use int for integer values; Fraction for ratios/means/quantiles; Decimal only for display. Financial display uses precision 50 then `quantize(Decimal("0.01"), ROUND_HALF_EVEN)`, with denominator 1 emitted as integer. Recursive float rejection is enforced. Artifact, identity, schema or digest conflicts raise explicit validation exceptions; missing Parquet support raises `MissingEvidenceError`; manifest size gaps remain NOT_VERIFIED rather than PASS.

## Verification and limits
Local combined suite: 27 passed; compileall PASS; Builder integration: 125 assignments / 105 unique keys / 105 NOT_VERIFIED manifests. No Excel, Word, final ZIP, Trial, Simulation, Monte Carlo or N=4800. Repository exact-head validation and tests 175/176/179/180/181/182/183/186 remain NOT_RUN. This design report does not claim full D1 repository closure.
