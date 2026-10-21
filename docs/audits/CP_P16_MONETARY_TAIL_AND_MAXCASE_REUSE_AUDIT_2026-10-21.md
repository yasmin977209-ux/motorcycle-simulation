# CP P16 — monetary tail and MaxCase reuse audit — 2026-10-21

## Scope and disposition

- Type: read-only evidence audit / root-cause analysis; no production code or policy changed.
- Base `main` HEAD: `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`.
- Candidate branch: `tmp/cp-p16-monetary-tail-audit-20261021`.
- P16 Run: `39635040311`; artifact `12363135623`; sealed artifact `12363265619`.
- Tested producer SHA: `30ba2d5d47d3a3d6c117f0ef667115401c337ad7`.
- `scripts/excel_builder_p16.py` at tested producer SHA: Git blob `1274e0055a81988ef72709a4c6ff9fc1f1351f3a`.
- Disposition: `PASS_SCOPED_ARTIFACT_READBACK / ROOT_CAUSE_CANDIDATE / NOT_FIXED`.
- No workbook build, simulation, Trial, Checkpoint, workflow, repository test, historical artifact, manifest, or source data was modified.

## R4 — floating-point value in C030_G030_STATS!L3

| Field | Finding |
|---|---|
| Observed cell | `Full_Results_EN.xlsx` → `C030_G030_STATS!L3`; direct openpyxl read returns numeric `13185720.000000002` |
| Row / column meaning | Row 3 is `Final_Cash`; column L is `P90` |
| Source implementation | `metric_stats(rows, field)` creates `np.asarray(..., dtype=float)`; P90 uses `float(np.quantile(vals, 0.90, method="linear"))`; tested source blob above |
| Serializer behavior | The producer's `save_workbook_preserving_stats_precision` explicitly patches select `_STATS` cells to preserve floating-point round-trip values, motivated by exact Stage 9C equality. Its comments call out the `13185720.000000002` example. |
| Reference rule | Original reference §1 says financial amounts are integer YER and prohibits floats/rounding for financial arithmetic. Original reference §14.8 specifies `numpy.quantile(..., method="linear")` as the sole quantile standard. |
| Root-cause assessment | The value is produced upstream by the float-based linear-quantile path and deliberately preserved by the XLSX serializer; it is not merely a display format issue. The `+2e-9` tail is consistent with binary floating-point evaluation. |
| Remaining uncertainty | This environment did not have a Parquet reader available, so I verified the exact input archive and embedded Parquet SHA but did not independently decode the 450 Final_Cash values at the P90 order-statistic boundary. Therefore I do not assert the exact pair of adjacent values or classify the mathematical quantile as an integer without that read. |
| Safe conclusion | Do not patch by blind `round()`, by changing only the Excel display, or by weakening CP-D's exact comparison. The reference’s integer-money rule and linear interpolation rule must both be satisfied through a specified exact computation or an explicit owner decision on fractional statistical quantiles. |

### Reproducible source identity

The downloaded P16 input artifact for `C030_G030` (Artifact `11497409735`, Run `37655041728`) has ZIP SHA-256 `9331c726560471f3092b2c61893a7ad87f3bafed363217249b6f4a992c029c07`, which matches P16 `output_manifest.json`. Its embedded `trial_results.parquet` is 27,400 bytes with SHA-256 `deaaf22000a56eb674ea4d349235f1e6d9410b838979ae043f41712983924b54`, also matching the P16 manifest; `daily_distribution.parquet` and `trial_fingerprints.json` match their embedded manifest digests as well. These hashes confirm artifact bytes, not the statistical semantics of the quantile.

## R4 — direct MaxCase sidecar comparison against P16

### Artifacts opened and checked

- P16 primary artifact ZIP: 68,486,691 bytes; SHA-256 `7e2e821e8c1f8e13b37189638e9a975ac8fc8862ee349abce928fea0cd048ada`.
- P16 sealed artifact ZIP: 68,488,514 bytes; SHA-256 `b2bd6096b0b4b273e412cf2756d70c1f5e79bda19681cb39463ea867d3dd6a54`.
- Stage 13 MaxCase sidecar ZIP / Artifact `12239369983`: 1,567,864 bytes; SHA-256 `f3e036ef1c88fc188633b784da12f76b32c41d3fe3283c768a0c3ea1f4b669e9`. This matches the recorded digest.

The sidecar states `integrity_status=PASS_SCOPED`, `payload_status=MISSING_EVIDENCE`, `25/25` scenarios, `11,005/11,005` TrialResult fingerprints rehashed, `25/25` Stage 12 artifacts validated, `22,546,465/22,546,465` daily rows validated, and `52,541` selected MaxCase daily rows. The source identity declares source SHA `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`, seed `20270101`, reference SHA `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`, and Stage 12 Run `37964656154`.

### Direct ID match results

Comparison was computed directly from P16 `output_manifest.json` and sidecar `stage13_maxcase_daily_payloads.json`:

- Matching selected MaxCase IDs: **22/25**.
- Mismatches:
  - `C085_G070`: sidecar ID 464; P16 ID 285.
  - `C070_G050`: sidecar ID 544; P16 ID 214.
  - `C050_G050`: sidecar ID 543; P16 ID 416.
- Sidecar marks `Partner1_Reinvestment_Balance` and `Partner2_Reinvestment_Balance` as `MISSING_EVIDENCE`; no values for these fields may be inferred from Cash/Equity.

### Interpretation / reuse limits

The sidecar selected maxima from the Stage 12 cohort (non-C100 trial IDs 1..550), while P16 is explicitly `LEGACY_9005` (non-C100 IDs 1..450). In the 22 ID matches, the daily series is a viable reuse candidate only after the selected trial/source/schema/date/fingerprint joins are revalidated for the intended P16 contract. The three mismatched IDs require an extraction for P16's selected IDs from identity-matched existing Stage 12 daily Parquet; this is a data-only extraction, not a simulation rerun. This CP did not carry out that extraction or build a workbook.

Even for matching IDs, the sidecar is not a complete MaxCase production payload while partner memo balances remain missing. It cannot be used to claim the five-role daily contract complete. The separate `C050_G000` Stage 9A artifact/run provenance record remains `CONFLICTED / PENDING_APPROVAL` for representative inventory identity; do not overwrite the canonical manifest as part of this CP.

## Decision needed before a monetary patch

The source reference appears to require both:
1. exact integer financial amounts (no float arithmetic/rounding for financial values), and
2. NumPy linear quantiles as the only quantile method.

A production fix must demonstrate how it preserves the approved linear-quantile definition and integer-YER rule, plus the exact Stage 9C/CP-D cell-equality requirement. If the exact order-statistic interpolation for this P90 is mathematically integral, an exact-arithmetic implementation may be possible without changing the quantile definition; verify it from the 450 raw input values first. If it is mathematically fractional, the reference's two requirements conflict for this output and the owner must authorize the policy before code change.

No change to statistical formula, money values, spreadsheet, manifest, or delivery artifact was made in this audit.
