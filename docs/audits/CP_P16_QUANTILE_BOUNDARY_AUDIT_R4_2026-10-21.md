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


## Exact-SHA run and source values

- Successful read-only Actions Run: `39676592373`, exact SHA `61ac5b4e5458e13b65ed4392dc7f84e1b051e1ab`; URL https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39676592373.
- Evidence artifact: ID `12381982953`, name `p16-quantile-boundary-audit`, ZIP SHA-256 `d1a8c072fc41062d3a2212a36df56e45c6691ceeabfa03475422f74485e29ed0`. The downloaded evidence artifact was re-hashed locally and matched the Actions API digest.
- Downloaded immutable input ZIP SHA matched `9331c726560471f3092b2c61893a7ad87f3bafed363217249b6f4a992c029c07`; inner Parquet SHA matched `deaaf22000a56eb674ea4d349235f1e6d9410b838979ae043f41712983924b54`. The audit verified exactly 450 rows and integer `final_cash` values; all historical inputs were read-only.
- For N=450, NumPy's linear P90 index is `404.1`: lower value at zero-based index 404 is `13,181,600`; upper value at index 405 is `13,222,800`; linear weight is `1/10`. Exact rational interpolation is `13,185,720/1` YER, an integer.
- NumPy float64 output is `13185720.000000002`; exact linear interpolation is `13185720.0`; difference is approximately `1.862645149230957e-9`. The output reproduces the observed P16 cell `C030_G030_STATS!L3` exactly. Classification: `EXACT_INTEGER_QUANTILE_FLOAT_TAIL_CANDIDATE`.
- A first audit run (`39676486085`) failed before reading input because urllib forwarded the GitHub API authorization header through a redirect to the signed artifact-storage URL, resulting in HTTP 401. The redirect handler was corrected to confine the token to the API request and fetch the signed URL without Authorization. No input data was changed. Successful rerun is the authoritative evidence.
- Disposition: the apparent decimal tail is a binary floating-point evaluation artifact for this verified P90; the exact linear quantile of the integer observations is exactly 13,185,720 YER. However, CP-D requires exact numeric equality to the already-published workbook and its R4 explicitly forbids changing the quantile formula, underlying metric, or historical workbook. This audit therefore **does not patch** the producer or any workbook. A change to stored numeric values must be versioned and reconciled with that exact historical comparison contract before production code is changed.
