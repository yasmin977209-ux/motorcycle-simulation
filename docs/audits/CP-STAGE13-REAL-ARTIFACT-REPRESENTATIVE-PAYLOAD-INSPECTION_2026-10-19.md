# CP-STAGE13-REAL-ARTIFACT-REPRESENTATIVE-PAYLOAD-INSPECTION — 2026-10-19

## Disposition
**Real source package inspected; Stage 13 canonical input remains blocked by a proved representative-role contract mismatch.** The source archive was downloaded read-only, hash-verified, and inspected without altering source bytes. No simulation, CLI, Trial, Checkpoint, Workflow, test, workbook build, or production data change occurred.

## Artifact identity
- GitHub artifact ID: `11497409735`, file name `canonical-enriched-input.zip`.
- ZIP: `4,781,258` bytes; SHA-256 `9331c726560471f3092b2c61893a7ad87f3bafed363217249b6f4a992c029c07`.
- The ZIP contains one member, `C030_G030.tar.gz`, `6,827,620` bytes; SHA-256 `a2403a9175ef85ec30663fbdb7ecd322c88beaf9672e1b73b30488312cd4aa10`. Both hashes match the previously recorded source-identity evidence.
- Scenario metadata: `C030_G030`, Run `37225915321`, `SOURCE_SHA=f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`, 450 trials, fingerprint reconciliation `expected=450/matched=450`, source dates 2027-01-01 through 2031-07-23.
- `trial_fingerprints.json`: 450 unique keys for IDs 1..450, contiguous; recorded algorithm `sha256(canonical_json(asdict(TrialResult)))`.

## Exact archive inventory
The TAR contains: `daily_distribution.parquet`, `trial_results.parquet`, `trial_fingerprints.json`, `scenario_metadata.json`, and four files under `representatives/`:
- `P10.json`: trial 235; 70,228,187 bytes; SHA-256 `7080e62a32ca712b0466c1cf51806caced4e669cfc7c0ae74c33f9ba92602c07`; 1,557 daily rows.
- `P50.json`: trial 156; 71,839,257 bytes; SHA-256 `e86d0c48cd48028f465dcc10cab92b60f672ef919cefc7d400097fe303ac00de`; 1,568 daily rows.
- `P90.json`: trial 67; 75,868,458 bytes; SHA-256 `c3c7c1b99c025e74c42a53759cc9eadb4e8481467b9e9d740756c47a47042d35`; 1,605 daily rows.
- `Loss.json`: trial 359; 66,833,724 bytes; SHA-256 `0984390b1bb1b9776d73a045f6d4b593b276f06656f4b7828ffbdbc0186a650c`; 1,517 daily rows.

Each of these four JSON payloads has the full payload object and a non-empty `daily` array; their `error_log` lists are empty. **There is no `MaxCase.json`, `Max Case.json`, or fifth representative payload in this archive.** The inventory was obtained from the real source bytes, not from a synthetic fixture. The two Parquet members were hashed and listed, but not parsed locally because this inspection environment has no Parquet reader installed; no Parquet row values or schema are claimed here.

## Normative requirement vs actual source contract
- Main `docs/governance/DECISIONS_LOG.md` blob `df4910e6a86bcce84f6b71d6d260913800474f95`, D-2026-10-10-03 (approved/normative), specifies five roles: P50/P10/P90/LossCase/MaxCase. MaxCase is the highest positive `Final_Net_Project_Equity`, tie-broken by the smallest `trial_id`; if none is positive, the rule is undefined and approval for that scenario stops.
- Main `docs/stage9a/DEVIATIONS.md` blob `ac8fb3e2dc65816bb2329aab19d4fe3c88d885d6`, line 25, defines the enriched scenario artifact as containing **four** representative JSON payloads and states that `daily_distribution.parquet` is not an individual daily accounting ledger for every trial. Main Stage 9A manifest blob `e796fa2443493b607f1f9c60b58eb63607959c26` records `total_representatives=100`, i.e. four roles for 25 scenarios.
- Candidate Stage 13 `scripts/stage13_assemble.py` blob `4cb4632fe787c92ee87190769bbbf05b65b61416` requires all five roles, exact selected trial ID and a non-empty `daily` payload for each. With the inspected source TAR, it must fail at `MISSING_REPRESENTATIVE_PAYLOAD: C030_G030/Max Case` rather than silently accepting four.

**Classification:** `MISSING_EVIDENCE / SOURCE_CONTRACT_MISMATCH`. This proves the mismatch for the inspected canonical `C030_G030` package and aligns with the main source-contract declaration; it does not claim that all 25 TARs were individually inspected. Do not relabel P90 or another role as MaxCase, do not synthesize a missing daily ledger, and do not weaken the approved five-role requirement. Resolution requires an identity-matched approved source with a valid MaxCase full payload or a separately authorized, identity-preserving derivation path. No new trial or historic Trial ID may be rerun as a workaround.

## Protected-state boundary
No main/state/reference/source/RNG/sampling/cohort/Trial/data/Parquet/workflow/test/output change, merge, PR closure or Release. Main state remains stage `12-CLOSED`, `FINAL_DELIVERY_BLOCKERS_OPEN`, with `state.json` blob `2178260bb18efeb81437486f13b6d10cf5e85936`. The Stage 13 candidate remains separate and untested at its current exact HEAD; overall project remains PARTIAL / NOT READY TO DELIVER.
