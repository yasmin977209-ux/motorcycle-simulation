# Compute Plan — v2.3 S6 parallel execution

**Plan status:** PREPARED_PENDING_VERIFIED_S5_RUNTIME  
**Branch scope:** tmp/s4-c100-golden-v23-20261026  
**Protected scope:** main and all historical cohorts remain untouched.  
**S4 reuse:** Reuse the pinned C100 Golden from source 965281d52441cd0d4b744e211c9f68ee4cdc3753 and Run 40263424595. Do not rerun any C100 scenario in S5 or S6.

## Evidence and timing

The S5 driver now pins the simulation/model SOURCE_SHA separately from the tested Git commit. Model SOURCE_SHA for the current candidate is `9fd34c2c4cf7250653ea6d86e33e1f939e6fba99`; the most recent code-and-test candidate commit is `8df6392192df45a81727239ce9b319d9a4991b82`. The pinned C100 reference remains the separate S4 cohort on SOURCE_SHA `965281d52441cd0d4b744e211c9f68ee4cdc3753`; S5 excludes all C100 scenarios. Runs `40381756114`, `40382013569`, and `40382155854` failed at the full pytest gate (four or five failures each) and did not run the S5 stochastic smoke driver. Their artifact digests are diagnostic only. Run `40383314937` on tested commit `e722de8f456defba0d0dd58ce199e3496eb6524b` was still in the full pytest step at the last verified read; Run `40383552605` on `8df6392192df45a81727239ce9b319d9a4991b82` was pending behind the branch-scoped concurrency group. Therefore, no successful S5 runtime or output artifact has been verified yet.

| Measurement | Evidence value | Decision |
|---|---|---|
| Serial elapsed time / trial | NOT_VERIFIED — read from results_stage5/benchmark.json in the completed S5 artifact | Do not substitute an estimate |
| Two-worker elapsed time / trial | NOT_VERIFIED — same artifact | Use only if measured exact equivalence is true |
| Four-worker elapsed time / trial | NOT_VERIFIED — same artifact | Use only if measured exact equivalence is true |
| Representative replay time | NOT_VERIFIED — same artifact | Keep replay as a separate workload |
| Model SOURCE_SHA / tested commit / Run ID / artifact SHA-256 | Model SOURCE_SHA=9fd34c2c4cf7250653ea6d86e33e1f939e6fba99; latest candidate commit=8df6392192df45a81727239ce9b319d9a4991b82; successful S5 Run ID and artifact digest NOT_VERIFIED | No performance claim until the canonical run succeeds and the artifacts are verified |

No ETA or throughput extrapolation is asserted without those measured values. This document is structurally ready for the S6 plan but is **not a release authorization** until the missing S5 evidence is reconciled.

## S6 checkpoint scope

- Stochastic scenarios only: the four collection percentages C085, C070, C050, C030 crossed with the five recovery levels G100/G070/G050/G030/G000, giving the twenty stochastic scenarios.
- First checkpoint: N = constants.STATISTICAL_CHECK_START_N = 300 repetitions per stochastic scenario. Reuse C100 only as the separate existing S4 deterministic reference; do not count it as an independent stochastic sample.
- Doubling schedule: 300 → 600 → 1200 → 2400 → ..., following constants.STATISTICAL_ESCALATION_MULTIPLIER. Each checkpoint receives its own immutable cohort identifier and evidence manifest.
- Partitioning: for each tuple (SOURCE_SHA, scenario_id, checkpoint_N), split the integer trial-ID set 1..N into mutually exclusive contiguous ranges. Compute quotient/remainder from N and number of shards; assign the extra one-trial remainder to the earliest shards. The union must equal 1..N exactly, without overlap or gaps. Sort merged outputs by (scenario_id, trial_id) before hashing.
- Worker-equivalence guard: for every shard/sample used to qualify execution, compare serial, two-worker and four-worker results and daily slices exactly; retain worker_equivalence_manifest.json and SHA-256 per canonical record. Any mismatch stops the checkpoint.
- RNG audit: retain rng_draw_count, rng_checksum and rng_checksum_fingerprint_sha256 separately from financial trial_fingerprint. If draw count is zero, require checksum zero. Check uniqueness of checksums across repetitions with positive draw count within each scenario/cohort.
- Financial integrity: check the daily Assets/Equity balance and all five daily roll-forwards, canonical bike IDs, exact-source Golden identity, no float columns/JSON values in financial reports, exact numerator/denominator persistence, and the five representative roles. For selected representatives, replay with full daily capture and compare the entire financial fingerprint plus daily partner reinvestment balances.
- Population reporting: write both ACTIVE_ONLY and ALL_TRIALS_CARRY_FORWARD as separately named populations. Preserve every statistic's exact numerator/denominator and its report display value.
- Gate transitions: evaluate the owner-approved time-uniform procedure at each approved doubling checkpoint. Declare CONVERGED only after the required three consecutive transitions across four cumulative checkpoints and the prescribed N versus N/2 precision guard. A small smoke sample cannot satisfy any production checkpoint or stability declaration.

## Dispatch gates

| Gate | Required evidence | Status |
|---|---|---|
| S5 execution | Successful completed GitHub Actions run, exit code zero, pinned model SOURCE_SHA separate from tested commit, real artifact, verified SHA-256 manifest | NOT_VERIFIED — Runs 40381756114 / 40382013569 / 40382155854 failed full pytest; Run 40383314937 was in progress and Run 40383552605 was pending at last live read |
| S5 parallel equivalence | All 100 trial rows (20 stochastic scenarios × trial IDs 1..5) in the real manifest have exact serial / 2-worker / 4-worker result and daily-slice equality | NOT_VERIFIED — no successful S5 manifest exists yet |
| S5 second pass | Five representative roles per scenario; first/second financial fingerprints and daily slices match; partner memo balances are integers | NOT_VERIFIED — driver not reached because prior runs failed pytest |
| S5 report precision | Parquet schemas contain no floating types; JSON reports contain no float values; exact fractions retained, RNG checksum stored as UInt64, and §14.7 population columns present | NOT_VERIFIED — fixes committed; final run must execute and verify outputs |
| S6 performance configuration | Select shard count and worker concurrency from the completed measured benchmark.json, not from an estimate | PENDING_S5_TIMING |
| Production Gate A/B and release | Full checkpoint evidence and independent release gates; no inference from C100 or from S5 smoke | BLOCKED_PENDING_EVIDENCE |

**Next required action:** finish and verify Run 40383552605 on the exact candidate head, or repair any remaining failing tests before another run. Only after the full pytest step, S5 driver, focused contract tests, and artifact/hash checks all succeed may the timing cells be replaced with exact integer nanoseconds and string-formatted seconds from the actual benchmark.json. If no successful artifact exists, keep the plan blocked and repair from the logged failure rather than estimating.
