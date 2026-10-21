# R4 — Gate A production provider coverage and authority audit — 2026-10-21

## Decision boundary and scope

- Base/main HEAD: `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`.
- Candidate branch: `tmp/cp-gatea-provider-coverage-audit-20261021`.
- Classification: `K_AUDIT / PROVENANCE / GATE COVERAGE`.
- Scope: compare the already-verified historical Gate A fingerprint bridge, current production call sites, the separate provider-preflight run, and effective main decisions/state. This is read-only; no provider is connected and no trial/checkpoint is run.

## Evidence 1 — historical exact-golden comparison is real but not the production runtime provider

- Historical bridge Run `38169163565` succeeded on tested head `95288a2bccb40d6772f5a5d042fdabc152c9d89a`, with 27/27 jobs successful, 25/25 scenario reports, 11,005/11,005 exact trial fingerprint comparisons, 22,546,465/22,546,465 Stage 12 daily rows and zero SHA mismatch.
- Its aggregate artifact is `11713395913`, ZIP digest `e00afa6a5d5ddbc8f84b5e225755535818460ec016d211fad0d1d2a210cfd996`. Actual and source-golden ordered-map SHA both matched official global SHA `7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44`.
- The bridge validates immutable historical source records. It does not itself pass the validated provider values into the current production calls within `run_batch.py`.

## Evidence 2 — production call sites omit the exact evidence required to pass Gate A

At main `run_batch.py` blob `0418ddea818c194a5b582df94778fa5f13a3ecc4`:
- initial reconstructed baseline call (around line 669) passes only `previous_metrics`, `previous_n`, `current_metrics`, and `current_n`;
- checkpoint call (around line 833) likewise passes only the metric and N arguments.

Neither supplies `expected_golden_fingerprint_sha256`, `actual_fingerprint_sha256`, `golden_reference_id`, `expected_source_sha`, nor `actual_source_sha`. Main `scripts/stage7_stability.py` blob `468b96b7b592a1ddd55cd4440962775632ab55a1` explicitly returns `BLOCKED` when those five fields are absent and requires canonical SHA formats, exact source identity equality, and exact fingerprint equality. This is fail-closed by design; a provider must be connected before Gate A can pass in production.

## Evidence 3 — candidate provider preflight exists but is not an effective main-approved provider

- GitHub Actions Run `38830875732` completed successfully on branch `tmp/cp-gatea-provider-bind-20261016`, head `cb2f603aacd93b910093d497deeea43710e7b0d3`.
- Artifact `12016903462`, name `cp-gatea-provider-bind-report`, size 1,719 bytes, API digest `sha256:72f122bc2a78ab079f6c7064c45d78d40b6e9463b83454a1366e32138c0359d6`.
- The recorded candidate report says its map covers 25,205 fingerprints: 20 non-C100 scenarios through trial 1200, five C100 scenarios at trial 1, and `C030_G030` through trial 2400. It reports source label `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`, source commit `0156c5f4272eb0ca7e32442657d0df9eaf4973d3`, and ordered-map SHA `0fbe3aa87a253f9527953c77b0a122871c9344f75ece6c8a49da99b2a85c1ce1`.
- Its reported coverage is not universal across future checkpoints: only `C030_G030` is explicitly covered through 2400; the other non-C100 maps are reported through 1200. The map also records a Golden/source identity exception and refers to candidate-only decision identifiers.

## Effective authority check

The effective main `docs/governance/DECISIONS_LOG.md` does not contain `D-2026-10-14-01` or `D-2026-10-15-10`. Those identifiers appear in candidate-related reports but not the live main decision log. An artifact or a candidate document's own label is not, by itself, effective authorization to promote that provider/extension. The approved D-2026-10-10-01 says Gate A compares to the approved reference/golden; it does not approve this provider map or waive the separate source identity drift blocker.

## Resulting judgment

`GATE A = BLOCKED / PROVIDER AUTHORITY + COVERAGE UNRESOLVED`.

It would be incorrect to connect this provider and declare Gate A PASS merely because its preflight workflow succeeded. The historical Gate A audit establishes exact comparisons for the historical 11,005-trial dataset; it does not establish that all next production checkpoint inputs have an approved golden map bound to the current executable source identity.

## Permitted next step

Keep all production calls fail-closed. Before provider wiring or a new checkpoint:
1. resolve the source SHA drift without silently changing `SOURCE_SHA` or mixing outputs;
2. establish effective governance authority for the exact provider artifact/map and any source-identity exception;
3. prove all Golden coverage needed for each scenario/checkpoint that the approved continuation policy may run, including the adaptive N=2400 path where required;
4. write a separate R4 for production caller/provider integration and exact regression tests, then run only the approved read-only validation before any trial/checkpoint is allowed.

No new Golden values, trial IDs, source SHA, seed/RNG, cohort, data, production workflow or state status were altered in this audit. The production Gate A helper continues to fail closed.


## Direct preflight artifact read-back

- Downloaded Artifact `12016903462` and verified ZIP size 1,719 bytes and SHA-256 `72f122bc2a78ab079f6c7064c45d78d40b6e9463b83454a1366e32138c0359d6`, matching its Actions API digest.
- Embedded `gatea_provider_preflight_report.json` (4,017 bytes, SHA-256 `5e200622ab0ed79dccf8a0abf0d9908c227680fb2e954f86dfd9927f9cd73f22`) reports:
  - base map count 24,005 and extension to total 25,205;
  - base map SHA-256 `166cae242d972c597f1a4466d184062f3d959649eb5e2440ad8de8b75663ff2c`;
  - extension Artifact `11940485523`, digest `049af21733b59d753967f27f251cb88fec122b5e1ff4f99d77b9215114c9d3e3`, Run `38662076725`, head `aafe5946a8a51c991471057d71f5643c46087086`, extension-map SHA `0c7679edfbee54797d64fc66e17116f0db617d1e0fa5f7ee21395fe98a628c65`, and referenced decision `D-2026-10-15-10`;
  - combined map SHA `0fbe3aa87a253f9527953c77b0a122871c9344f75ece6c8a49da99b2a85c1ce1`, Golden reference label `D-2026-10-14-01:GateA:25205:0fbe3aa87a253f9527953c77b0a122871c9344f75ece6c8a49da99b2a85c1ce1`;
  - the 20 non-C100 scenarios have IDs 1..1200, five C100 scenarios have ID 1, and only `C030_G030` extends through 2400. It states no trial generation, Parquet mutation, historical dataset mutation, Workflow or Monte Carlo was executed.
- Embedded `source_identity_exception_report.json` (995 bytes, SHA-256 `9c0a98ae2d7d18621ab8177733a51ee4be0d0140a39db0b32b5beff9aa3badbc`) labels the change an `additive_compatibility_adapter`, but also makes the byte-level discrepancy explicit: pinned `daily_engine.py` SHA-256 `a1c83c12232bc4e06b091f92878c16e3e34435ee9bc2caf3725a8a23b12e8b87` versus candidate `bd0263df323d42e88ddeb9d87a3526ba295fd26ed264086025041f6c18fe9301`. It reports a 10/10 fingerprint replay on Run `38461464864`, tested SHA `6da81aadbf451131304024d919f6a89be772b717`, but repository pytest still had 3 failed, 384 passed, 1 skipped. The source SHA was not bumped.
- The explicit authority check independently re-read current main's `DECISIONS_LOG.md`: `D-2026-10-14-01` and `D-2026-10-15-10` are absent. Thus the candidate report's internal reference to them does not by itself authorize the extension map or identity exception.
- Result: the preflight artifact is real and cryptographically identified, but the authority and future checkpoint coverage gap remain. No provider is connected.
