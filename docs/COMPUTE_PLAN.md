# Compute Plan — v2.3 S6 parallel execution

**Plan status:** S5_SMOKE_VERIFIED_S6_RUNNER_READY  
**Branch scope:** tmp/s4-c100-golden-v23-20261026  
**Protected scope:** main and all historical cohorts remain untouched.  
**S4 reuse:** Reuse the pinned C100 Golden from source 965281d52441cd0d4b744e211c9f68ee4cdc3753 and Run 40263424595. Do not rerun any C100 scenario in S5 or S6.

## Evidence and timing

### Verified S5 run

- GitHub Actions Run: [40383552605](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40383552605), completed **success**, job exit code 0.
- Tested commit: `8df6392192df45a81727239ce9b319d9a4991b82`; pinned model `SOURCE_SHA=9fd34c2c4cf7250653ea6d86e33e1f939e6fba99`. The preflight verified the model files match the pinned source and recorded `TESTED_COMMIT_SHA` separately.
- Full test command: `python -m pytest -q tests --junitxml=s5_evidence/full-suite-junit.xml`; result **558 passed, 1 skipped, 1 warning**, exit 0, 374.28 seconds. Full-suite log SHA-256: `788996c6bc5b8c62caa8eb8a685c8c9a82478e397d4ab134f54c5cff57dde896`; JUnit SHA-256: `69e2bc010bf2aeb11927d075af91d800e7e53c8fcf4c273e68e468e5b7e02495`.
- Focused command from the workflow: S5 contract tests through `tests/test_acceptance_16_v2.py` and `tests/test_s5_stage5_output_contract.py`; **6 passed, 160 deselected**, 0.79 seconds.
- Actions artifact ID `12680198562`, size 25,068,927 bytes, ZIP SHA-256 `05f1640386bfd6f1dc8fff32959f2d31abd9d93b66cb556ab7e45abddede280f`. The downloaded ZIP digest independently matched the Actions artifact digest. `results_stage5/SHA256SUMS.txt`: 10 entries, all hashes matched. `s5_evidence/SHA256SUMS.txt`: 6 entries, all hashes matched.
- Output identity remains S5 smoke/cohort only: 20 stochastic scenarios × `trial_id=1..5`; no C100 rerun; no formal stability declaration; no production Gate A/B pass; no final delivery acceptance.

### Actual measured timings (from `results_stage5/benchmark.json`)

| Measurement | Exact elapsed | Mean elapsed per trial | Decision |
|---|---:|---:|---|
| Serial, 100 trial executions | `318467836537 ns` (`318.468 s`) | `3184678365 ns` (`3.185 s`) | Reference timing |
| 2-worker pool across 100 trial tasks | `200970568017 ns` (`200.971 s`) | `2009705680 ns` (`2.010 s`) | Exact result/daily-slice equivalence passed |
| 4-worker pool across 100 trial tasks | `194899345728 ns` (`194.899 s`) | `1948993457 ns` (`1.949 s`) | Lowest measured parallel elapsed; still a small N=5 pilot |
| Second-pass representative replay, 60 unique trials | `195319823196 ns` (`195.320 s`) | `3255330386 ns` (`3.255 s`) | Separate from first-pass timing |
| Complete S5 driver, including output assembly and checks | `966945258005 ns` (`966.945 s`) | Not a per-trial estimator | Actual measured run total |

All timing values above are actual `time.perf_counter_ns` measurements from Run `40383552605`; they are not projected N=300 timings. S5 is only a functional smoke sample (`N=5`), and no production ETA is inferred from it.

### Output and hash evidence

- `worker_equivalence_manifest.json`: 100 rows; `exact_all=true`. For every trial in each of the 20 stochastic scenarios, serial, 2-worker and 4-worker results, financial fingerprints, full result record SHA-256 and daily-slice SHA-256 matched.
- `representative_replay_manifest.json`: 100 representative-role rows and 60 unique full-recording replays; all first/second `trial_fingerprint`, full-record and daily-slice comparisons passed; all daily Partner 1/2 reinvestment balances were integers.
- `selection.parquet` contains the five per-scenario roles. `trials_summary.parquet`, `daily_distribution.parquet`, `representative_daily.parquet` and `stability_history.json` were produced. Daily distribution contains 410,950 rows with both `ACTIVE_ONLY` and `ALL_TRIALS_CARRY_FORWARD` populations and the required §14.7 population fields.
- The S5 driver re-read all four Parquet outputs and rejected any floating-point column; it also recursively checked its JSON outputs for floats. An independent stream scan of `number_registry.json` counted 2,055,310 records and found zero JSON float values. All 10 file hashes in the results manifest and all 6 execution-evidence hashes matched the uploaded ZIP's contents.
- Output hashes: `S5_evidence.json` `088ba7c9e0fde0600d76ecd08758e17d7aaf1ed92adcb3e1cad786ed4ceca936`; `worker_equivalence_manifest.json` `fd775e4fd7ad6df621ffc2b186d20dc9f1ee1ed1cd21bb186978cfc397498c78`; `representative_replay_manifest.json` `b133577a635cfc8c73a94dd1cb9a195bed52813522689767655319b24ca1625e`; `trials_summary.parquet` `2ea2c3984b6b3093cd44248b1aa78d71914726ff6b7daac574b6d189a8d3eb55`; `daily_distribution.parquet` `769e6f333fd6e04fcf8a60ca32d19fdcf6c8bed8f9c918e76d94b4b3de02d63a`; `stability_history.json` `d12e1cc84b2f721734eeafc9b42c0fc5f1f5b104143976b0b3403976cfb0068a`; `benchmark.json` `a58b82700d13b1b7e659fe0c83747f630917c3fa0daf57bf8f208f72356a71ae`; `number_registry.json` `81f2dc768d7cb6f76fa3d34c562bfe695331cd35a959c04ddcdf14d825eeeb17`.

## S6 checkpoint scope

- Stochastic scenarios only: the four collection percentages C085, C070, C050, C030 crossed with the five recovery levels G100/G070/G050/G030/G000, giving the twenty stochastic scenarios.
- First checkpoint: N = constants.STATISTICAL_CHECK_START_N = 300 repetitions per stochastic scenario. Reuse C100 only as the separate existing S4 deterministic reference; do not count it as an independent stochastic sample.
- Doubling schedule: 300 → 600 → 1200 → 2400 → ..., following constants.STATISTICAL_ESCALATION_MULTIPLIER. Each checkpoint receives its own immutable cohort identifier and evidence manifest.
- Top-level parallel partitioning in the prepared S6 workflow: the 20 non-C100 scenarios are mutually exclusive matrix jobs, with at most 5 scenario jobs running concurrently. Within each scenario job, the reference runner executes trial IDs 1..N serially and then with spawn-based 2- and 4-worker pools; it checks exact equality per trial before producing one scenario Golden and audit. Merging requires exactly one audit and Golden for every scenario, complete trial coverage 1..N, consistent SOURCE_SHA/tested commit/run/checkpoint identities, and a canonical sorted global map hash. This preparer does not emit independent contiguous range-shard artifacts; do not describe it as range-sharded execution.
- Worker-equivalence guard: for every shard/sample used to qualify execution, compare serial, two-worker and four-worker results and daily slices exactly; retain worker_equivalence_manifest.json and SHA-256 per canonical record. Any mismatch stops the checkpoint.
- RNG audit: retain rng_draw_count, rng_checksum and rng_checksum_fingerprint_sha256 separately from financial trial_fingerprint. If draw count is zero, require checksum zero. Check uniqueness of checksums across repetitions with positive draw count within each scenario/cohort.
- Financial integrity: check the daily Assets/Equity balance and all five daily roll-forwards, canonical bike IDs, exact-source Golden identity, no float columns/JSON values in financial reports, exact numerator/denominator persistence, and the five representative roles. For selected representatives, replay with full daily capture and compare the entire financial fingerprint plus daily partner reinvestment balances.
- Population reporting: write both ACTIVE_ONLY and ALL_TRIALS_CARRY_FORWARD as separately named populations. Preserve every statistic's exact numerator/denominator and its report display value.
- Gate transitions: evaluate the owner-approved time-uniform procedure at each approved doubling checkpoint. Declare CONVERGED only after the required three consecutive transitions across four cumulative checkpoints and the prescribed N versus N/2 precision guard. A small smoke sample cannot satisfy any production checkpoint or stability declaration.

## Dispatch gates

| Gate | Required evidence | Status |
|---|---|---|
| S5 execution | Completed Actions Run, exit code 0, pinned model SOURCE_SHA separate from tested commit, full and focused pytest evidence, real artifact, verified SHA256 manifests | **PASS — Run 40383552605** |
| S5 parallel equivalence (Test 127) | 100 trial rows across 20 scenarios, exact serial/2-worker/4-worker result and daily-slice equality | **PASS — `worker_equivalence_manifest.json`, `exact_all=true`** |
| S5 representative selection/replay (Tests 159/160/174/181) | 100 role rows; 60 unique second-pass replays; full records, financial fingerprints and daily slices match; daily partner balances are integers | **PASS — `representative_replay_manifest.json`** |
| S5 report precision (Test 182) and daily distribution (Test 161) | Parquet and JSON output contracts, exact numerator/denominator retention, both §14.7 populations and fields, verified SHA256 manifests | **PASS — real output artifact inspected** |
| S6 Gate A preparer and updated gate contract | Pinned SOURCE_SHA, independent seed-key recomputation, daily balance/roll-forward checks, RNG checksum rules, serial/parallel exact compare, refreshed scoped statistical gate contract | **PASS — latest verification Run 40388966534: 12 passed, 34 deselected; compileall success, exit 0** |
| S6 N=300 stochastic Golden execution | Explicit workflow dispatch, 20 scenario artifact set, full trial coverage and merged Golden/audit SHA256 manifest | **PREPARED, NOT DISPATCHED** |
| Production Gate A/B, convergence and release | Full authorized checkpoint evidence, independent gates and requalification of existing blockers | **BLOCKED_PENDING_EVIDENCE** |

### S6 dispatch configuration

- First checkpoint `N=300`; then `600 → 1200 → 2400 → ...`. No S6 checkpoint has been launched by this S5 run.
- Use the measured 4-worker pool as the current faster pilot setting (`1.949 s/trial` versus `2.010 s/trial` for 2 workers), while retaining both 2- and 4-worker exact-equivalence checks. The prepared workflow caps cross-scenario concurrency at 5 jobs. Because the pilot contains only five IDs per scenario, treat this as a configuration decision for a bounded first checkpoint—not as a production throughput estimate or ETA.
- The S6 manual workflow's generated per-scenario files are `PREPARED_PENDING_REVIEW`; the combined fingerprint map is not itself a production Gate A PASS. `C100` remains the separate immutable S4 reference and must not be rerun or merged into the stochastic cohort.
- The production gate remains scoped: `P90_Held_Assets` production acceptance and the historical `C030_G030` N=300→600 failure are not resolved by S5 smoke or by compiling the S6 preparer. The top-level status `AUTHORIZED_FOR_V2.3_EXECUTION` does not set the production trial, convergence or final acceptance booleans to true.

**Current disposition:** S5 smoke is verified; S6 runner and workflow are prepared and the non-simulation contract tests pass. The next authorized S6 step is an explicit manual dispatch at `N=300` once the owner decides to begin that production checkpoint; no time-uniform stability or final delivery claim is inferred from S5.

