# D0–D2 Live Evidence Reconciliation — 2026-11-05

## Scope and authority

- Repository: `yasmin977209-ux/motorcycle-simulation`
- Working branch: `tmp/d1-rebuild-20261101`
- Baseline branch HEAD before this addendum: `d08d4fcd74d43eab00a770ba8595fa0cd96b9329`
- Main HEAD: `01a6f79eedc522bb734ed9c5ea31beee581f2468` (read-only)
- Governing reference: v2.4.0, `D-2026-10-30-REFERENCE-V2.4.0`, `APPROVED_BY_OWNER`.
- Current governing reference SHA-256: `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`.
- Historical execution reference v2.3 SHA-256 remains separate: `e5efaf0874384e8248c339ca10e248ea9e17e9f0882153b4ef88bc955b91d53f`.
- This addendum corrects stale evidence descriptions append-only. It does not rewrite original audits, change business rules, alter identities, or promote any stage to `PASS_GAP_FREE`.

## D0 — Input integrity and provenance

### New exact-head evidence

Workflow [42099529644](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42099529644), Job `127498347595`, tested exact branch SHA `d08d4fcd74d43eab00a770ba8595fa0cd96b9329` and completed SUCCESS. The job log reports:

- Aggregate Artifact `12852969854`: 9,357,996 bytes; SHA-256 `ec05a69ae8968585decf83cf0716d56c264f47f86187cfd3cf53b11f52ca2e54`.
- Full Logging Artifact `12998778418`: 310,827,203 bytes; SHA-256 `403371cc8eb12880dda05529b4c83dd675bfa609e8680c09d35efa729c5b5aeb`.
- C100 reuse Artifact `12630457193`: 361,733 bytes; SHA-256 `c977d1cbb5204919eadc72358533f77cdbbc239902bcd6f921bf1a915a716e79`.
- All three were downloaded from exact Artifact IDs and their metadata size/digest pins matched the downloaded ZIP bytes.

The same workflow ran `compileall` and the artifact-backed Builder/Number Registry test set: **36 passed in 2.57s; no failures or skips**. The tests exercise the pinned reader and include negative ZIP cases for duplicate members, unsafe paths and symlinks. `scripts/s6_artifact_reader.py` validates duplicate names, absolute/traversal/Windows/dot-segment paths, normalized path collisions, symlinks and ZIP CRC before exposing members; it reads members without extracting untrusted paths to disk.

Parquet-related bounded evidence:
- The Builder integration test reads `trials_summary.parquet` and checks LossCase/MaxCase as global per-scenario argmin/argmax.
- The D2 build workflow separately parsed the daily distribution and resolved all 2,086,550 addressable points.
- These checks are not a complete fresh D0 audit of every Parquet column, null, duplicate, partition and source-run metadata field. The earlier `MISSING_EVIDENCE` / `NOT_RUN` fields are not all cleared by these focused tests.

### D0 disposition

`PASS_SCOPED_WITH_LIMITATIONS` remains the only supported D0 classification. The following remain unresolved and must not be inferred:
- The pinned aggregate manifest has `source_run_metadata.sha256 = null`.
- Original historical detailed daily/accounting ledgers for all 48,000 S6 trials are not present in the authorized original inputs.
- The five historical accounting fields remain `MISSING_EVIDENCE`: `Accounts_Receivable`, `Accumulated_Depreciation`, `Gross_Bike_Assets`, `Guarantee_Claim_Receivable`, `Total_Assets`.
- Full D0 Parquet metadata/schema/null/duplicate/partition matrix is not established by the focused D1/D2 workflows.
- C100 remains a separate cross-cohort deterministic reuse population, not S6 random evidence.

## D1 — Builder, reference and Full Logging manifest reconciliation

### 105-key manifest evidence

Workflow [42099529644](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42099529644), Job `127498347595`, generated `D1_105_MANIFEST_SIZE_EVIDENCE_2026-11-05.json`:

- 105 unique `(scenario_id, trial_id)` keys.
- 105/105 normalized statuses: `PASS_SCOPED_REPRESENTATIVE_FULL_LOGGING`.
- For every key, the actual `trial_manifest.json` and `post_write_audit.json` sizes and SHA-256 values matched the independent root-manifest hashes and ZIP central-directory sizes.
- JSON payload: 69,247 bytes; SHA-256 `8412adb32c32a000d624fbbd1ea965238dd4da4b1ef95949551e5b47bf19516f`.
- The workflow emitted the payload as base64 chunks in its job log. Decoding those exact chunks produced byte-for-byte text equality with the GitHub file at `docs/stage_d/D1_105_MANIFEST_SIZE_EVIDENCE_2026-11-05.json`.
- Git blob SHA-1: `2ea998a1faeeb7ebb36208f36fc878a9c20518f7`; the file is present at baseline HEAD `d08d4fcd74d43eab00a770ba8595fa0cd96b9329`.
- Uploaded workflow Artifact: `13450005224`, 10,545 bytes, digest `sha256:edbff0f8ecbf1385efbf5158542661f451cb482c49fa2a6851c0fcf2a0313721`, expires 2026-12-05T20:02:51Z.

This supersedes the older `NOT_VERIFIED_105_OF_105` description **only for these 105 selected representative keys**. The original D1 audit snapshots remain immutable historical records; this addendum is the newer reconciliation.

### Governing reference evidence

D2 completion Run [41335321803](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41335321803) verified the canonical v2.4.0 Raw bytes and owner decision on the same tested commit:
- Reference path: `docs/governance/MOTORCYCLE_SIMULATION_GOVERNING_REFERENCE_V2.4.0.md`.
- 401,397 bytes; SHA-256 `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`.
- Git blob SHA-1: `9fe43bfbb2cbfd2bb7f7010866e7469506d22c33`.
- Final Raw readback commit: `46c86795d64311b53106fb0b7a79f8bcde116112`.
- Owner decision path: `docs/governance/D-2026-10-30-REFERENCE-V2.4.0.md`, blob `58f89bc016523f1350345428b4a224ac42a8b130`, status `APPROVED_BY_OWNER`.

The current branch tree retains the same reference blob and the same 105-key evidence file. The v2.4.0 header's `PROPOSED` wording remains a preserved document conflict; the explicit owner decision governs.

### D1 disposition

`PASS_SCOPED_WITH_LIMITATIONS` remains. The 105-key issue is now resolved for the selected representative population, but it does not establish all-48K logging. `D1_BUILDER_AUDIT.json` records `IMPORTER_NOT_RUN`; this new evidence does not prove a full independent importer execution or two clean independent rebuilds. No full phase-level gap-free claim is made.

## D2 — Number Registry and numeric lineage

The successful D2 completion workflow [41335321803](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41335321803) records:
- 34 passed, 0 failed, 0 skipped in its D1–D2 source/integration validation.
- Registry: 2,640 explicit entries (960 aggregate checkpoint entries + 1,680 representative Full Logging entries).
- Daily series: 1,000.
- Daily points: 2,086,550; resolver verified 2,086,550/2,086,550 exact points, including exact value numerator/denominator, series, date and deterministic ID.
- Registry path: `results/number_registry.json`.
- Registry: 24,137,036 bytes; SHA-256 `743ffcced8de09a766870f201c352aabcf5789c43c84bfeae654a939700e4f87`; Git blob SHA-1 `8cf17de488c623f96c1961ca91d682fbbc7733d6`.
- Registry-containing commit `cc94985454d6e5971947e53c8e0a2782ad2de12d`; final Raw readback commit `46c86795d64311b53106fb0b7a79f8bcde116112`.
- The current branch tree retains the same registry blob, resolver source blob `af0f8585940ae9208b43e7181e5562f1912816d2`, test blob `2fe03aa5f701fb844e5ea0cd9fa3e88321b9729e`, and D2 workflow blob `a3193ae5bcd4727c8c80586a7ac50dbace61b285`.

The current `D2_NUMBER_REGISTRY_AUDIT.json` still contains the older field `full_logging_normalized_status=NOT_VERIFIED_105_OF_105`. Its value is superseded for the 105 representative keys by the new D1 evidence above; do not rewrite the historical audit snapshot. D2's overall status remains `PASS_SCOPED_WITH_LIMITATIONS`.

D2 does not establish full financial lineage for all 48,000 S6 trials, does not replace original daily/accounting ledgers or Parquet/SQLite sources, and does not close the production gate.

## Fixed limitations — unchanged

- Financial Gate A: `PASS_SCOPED` only.
- Production Gate A: `NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS`.
- Gate B at N=2400: `FAIL_SCOPED (10/10)`.
- Stability: `NOT_CONVERGED (0/60)`.
- N=4800: `NOT_EXECUTED`.
- C100 Golden revalidation: `NOT_RUN`.
- Full Logging: 105 selected representative keys only.
- Five missing accounting fields and null `source_run_metadata.sha256` remain missing; no zero-fill, backfill, inference or replay substitution.

## Final D0–D2 result

| Stage | Current classification | Reconciliation |
|---|---|---|
| D0 | `PASS_SCOPED_WITH_LIMITATIONS` | Three pinned inputs and ZIP safety/integration checks revalidated; historical source/Parquet gaps remain |
| D1 | `PASS_SCOPED_WITH_LIMITATIONS` | 105/105 representative manifest records now verified; importer/full-cohort gaps remain |
| D2 | `PASS_SCOPED_WITH_LIMITATIONS` | 2,640 entries and 2,086,550 points verified; full historical accounting lineage remains absent |

No business rule, reference byte, source SHA, cohort ID, seed, Trial identity, gate threshold, historical Artifact or manifest was changed. No Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, main write, merge, Release or D3/D4 progression was performed.
