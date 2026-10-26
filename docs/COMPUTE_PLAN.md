# Compute Plan — v2.3 S6 parallel execution

**Plan status:** PREPARED_PENDING_VERIFIED_S5_RUNTIME  
**Branch scope:** tmp/s4-c100-golden-v23-20261026  
**Protected scope:** main and all historical cohorts remain untouched.  
**S4 reuse:** Reuse the pinned C100 Golden from source 965281d52441cd0d4b744e211c9f68ee4cdc3753 and Run 40263424595. Do not rerun any C100 scenario in S5 or S6.

## Evidence and timing

The S5 smoke driver was committed as 18ca260ae9d71ff83a7c9a47cbe5a494fcd5f6e1 and is configured to emit benchmark.json, worker_equivalence_manifest.json, Parquet samples, replay evidence, number_registry.json, and SHA256SUMS.txt. The workflow-run ID, terminal outcome, benchmark payload, and uploaded artifact digest were not retrievable through the available GitHub run/status interface during this plan write.

| Measurement | Evidence value | Decision |
|---|---|---|
| Serial elapsed time / trial | NOT_VERIFIED — read from results_stage5/benchmark.json in the completed S5 artifact | Do not substitute an estimate |
| Two-worker elapsed time / trial | NOT_VERIFIED — same artifact | Use only if measured exact equivalence is true |
| Four-worker elapsed time / trial | NOT_VERIFIED — same artifact | Use only if measured exact equivalence is true |
| Representative replay time | NOT_VERIFIED — same artifact | Keep replay as a separate workload |
| Source SHA / Run ID / artifact SHA-256 | SOURCE_SHA=18ca260ae9d71ff83a7c9a47cbe5a494fcd5f6e1; Run ID and artifact digest NOT_VERIFIED | No performance claim until evidence is retrieved |

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
| S5 execution | Successful completed GitHub Actions run, exit code zero, source identity, real artifact, SHA-256 manifest | NOT_VERIFIED |
| S5 parallel equivalence | All 100 trial rows in the real manifest have exact serial/parallel result and daily-slice equality | NOT_VERIFIED |
| S5 second pass | Five representative roles per scenario; first/second financial fingerprints and daily slices match; partner memo balances are integers | NOT_VERIFIED |
| S5 report precision | Parquet schemas contain no floating types; JSON reports contain no float values; exact fractions retained | NOT_VERIFIED |
| S6 performance configuration | Select shard count and worker concurrency from the completed measured benchmark.json, not from an estimate | PENDING_S5_TIMING |
| Production Gate A/B and release | Full checkpoint evidence and independent release gates; no inference from C100 or from S5 smoke | BLOCKED_PENDING_EVIDENCE |

**Next required action:** retrieve the completed S5 workflow run and its artifact, verify the artifact SHA-256 against the workflow evidence, then replace the NOT_VERIFIED timing cells with the exact integer nanoseconds and string-formatted measured seconds from benchmark.json. If no successful artifact exists, keep the plan blocked and repair from the logged failure rather than estimating.
