# R4 — Read-only exact quantile boundary audit for P16 C030_G030 — 2026-10-21

## Scope and identity

- Base/main HEAD: `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`.
- Candidate branch: `tmp/cp-p16-quantile-boundary-audit-20261021`.
- Classification: `K_AUDIT / HISTORICAL INPUT READ ONLY`.
- Input artifact ID: `11497409735`; originating Run `37655041728`; artifact ZIP SHA-256: `9331c726560471f3092b2c61893a7ad87f3bafed363217249b6f4a992c029c07`.
- Embedded `trial_results.parquet` SHA-256: `deaaf22000a56eb674ea4d349235f1e6d9410b838979ae043f41712983924b54`; P16 manifest recorded 450 trial rows for this scenario.
- Observed P16 cell: `C030_G030_STATS!L3`, mapped by the producer to `Final_Cash / P90`, raw value `13185720.000000002`.
- Tested producer identity in prior P16 report: source commit `30ba2d5d47d3a3d6c117f0ef667115401c337ad7`, source file blob `1274e0055a81988ef72709a4c6ff9fc1f1351f3a`.

## Question to resolve

P16 uses `numpy.quantile(values, 0.90, method="linear")` on float arrays, and its OOXML serializer deliberately preserves round-trip float values for the exact Stage 9C gate. The reference also requires integer YER financial amounts. This read-only audit computes the two order statistics surrounding the 90th percentile from the verified input Parquet and compares:
1. NumPy's float64 linear quantile output,
2. the exact rational interpolation of integer order statistics, and
3. the integer-money requirement.

For 450 observations the linear position is `(450 - 1) × 0.9 = 404.1` (zero-based), so the relevant sorted values are indices 404 and 405. No rounding decision will be made before their exact relation is measured.

## Execution plan

A dedicated candidate-only GitHub Actions workflow will download the exact artifact through the read-only Actions API, verify the ZIP and inner Parquet SHA-256 values, read the Parquet using the repository's declared dependencies, enforce 450 non-null integer `final_cash` values, and produce a short JSON evidence artifact. It will not write to the repository data, modify the source artifact, build a workbook, run a simulation, or execute trials/checkpoints.

## Interpretation

- If exact interpolation is an integer but NumPy emits a tiny fractional tail, an exact-arithmetic implementation equivalent to NumPy's linear order-statistic definition may be proposed for a later scoped code CP; it must also preserve Stage 9C exact comparison.
- If exact interpolation is fractional, the normative integer-YER requirement and linear interpolation need an explicit project-owner decision before a money quantile code change.
- Either result is read-only evidence, not permission to alter the already-published workbook or historical dataset.

## Exclusions

No production source, tests, statistical policy, money value, model source SHA, seed/RNG, trial IDs, cohort, historical Parquet, manifest, published workbook, `state.json`, main, merge, or release is changed.

## Status

`PENDING_EXACT_ORDER_STATISTIC_READBACK`. Do not patch with blind rounding.
