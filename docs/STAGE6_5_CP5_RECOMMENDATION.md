# Stage 6.5 — CP5 Recommendation

## Status

CP5: PASS

- Branch: tmp/stage6.5-cp5-20261003
- CP4 source head: e47675764c195e1fbd9252279c6ab9c30a864cfb
- Analysis only: no workflow and no simulation run created by CP5.
- No production or test files modified.

## Source evidence used

| Source | Run / commit | Relevant stdout-derived data |
|---|---|---|
| CP3 | Run 37203438351 | 6000 trials; aggregate SHA c09d39cd3f79e9460d16df4fc2a6a47b6b029983e2f596de4af4009bc169a14a; max_parallel 16; max_chunk_elapsed 1488.361695994 s; wall_clock_estimate 1488.361695994 s |
| CP4 | Run 37203903230 | C050_G100: mean T True 3.3377955780000006 s; mean T False 2.8378438517999998 s; mean RSS True 118388.0 KB; mean RSS False 39411.2 KB; time reduction 14.978500465854495%; RSS reduction 66.71013954116971%; 5/5 SHA match |
| CP1 | Run 37137722603 | C085_G100: time reduction 13.804284889905377%; RSS reduction 67.6692862673% |
| Stage 6 Round 3 | Run 37131229448 | C050_G100 trial 5 = 5.379037712000013 s; C070_G100 = 4.3925 s; C030_G100 = 0.8839 s; scaling totals for 6005/7005/8005 as below |

## 1. Is 16 × 375 sufficient?

A 375-trial chunk holds:

- 16 × 375 = 6000 trials.

Therefore 16 such chunks are not sufficient for 6005, because 6005 requires 17 chunks at 375 trials/chunk. The corresponding minimum chunk counts are:

| Scenario | Total trials | Required 375-trial chunks | max-parallel | Chunk waves |
|---|---:|---:|---:|---:|
| 6005 | 6005 | 17 | 16 | 2 |
| 7005 | 7005 | 19 | 16 | 2 |
| 8005 | 8005 | 22 | 16 | 2 |

The expression 16 × 25 = 400 describes 25 scenario positions with 16 matrix/chunk positions each; it is not the number of 375-trial chunks needed for the total trial pool. Using 375 as the actual chunk size gives the 17/19/22 counts above.

### G8 theoretical wall-clock using the measured Stage 6 scaling totals

| Scenario | Stage 6 sequential seconds | G8 at 16 parallel (s) | G8 at 16 parallel (min) |
|---|---:|---:|---:|
| 6005 | 22908.192216524014 | 1431.7620135327509 | 23.862700225545847 |
| 7005 | 26722.400210854015 | 1670.150013178376 | 27.835833552972932 |
| 8005 | 30536.60820518402 | 1908.5380128240013 | 31.80896688040002 |

These are G8 theoretical lower-bound calculations. CP3 additionally demonstrated a 1488.361695994 s maximum 375-trial chunk, so discrete chunk waves can produce a materially larger wall-clock than the ideal divisible-work calculation.

## 2. Stage 7 — three workflow options

For a conservative worst-case per-scenario calculation, use the measured Stage 6 C050_G100 trial time 5.379037712000013 s.

| Option | Architecture | 6005 | 7005 | 8005 | Main risk |
|---|---|---:|---:|---:|---|
| A | 25 independent workflows; 20 concurrent GitHub jobs maximum | 53.79037712000013 min | 62.75543997333349 min | 71.72050282666684 min | 25 workflow/run IDs, fragmented artifacts and monitoring; second wave required |
| B | 1 workflow, 25 matrix jobs, max-parallel=10 | 80.68556568000018 min | 94.13315996000023 min | 107.58075424000026 min | Longer than A, but centralized and resumable |
| C | 1 direct 25-scenario matrix, small workflow | 80.68556568000018 min | 94.13315996000023 min | 107.58075424000026 min | Similar runtime to B with weaker explicit checkpoint/resume structure |

For Option B, the discrete calculation is 3 matrix waves because ceil(25/10) = 3. The G8 continuous lower bound is approximately 67.2379714 min for 6005, but the conservative atomic-job wave calculation is 80.68556568000018 min.

For Option A, the 20-concurrent limit requires two waves for 25 workflows. The conservative per-scenario wall time is based on the slowest measured C050_G100 case:

- 300 trials: 26.895188560000065 min per scenario.
- 350 trials: 31.377719986666744 min per scenario.
- 400 trials: 35.86025141333342 min per scenario.

## 3. GitHub Free concurrency and failure/restart risk

### Option A

Twenty concurrent jobs allow at most 20 of the 25 scenario workflows to run together. The remaining five form a second wave. It is the fastest of the three on the conservative model, but it creates 25 independently managed workflows and makes centralized audit, artifact collection, and restart coordination more difficult.

### Option B

One workflow owns all 25 matrix jobs. max-parallel=10 stays below the stated 20-job concurrency ceiling, leaves concurrency headroom, and gives one Run ID and one central control plane. The 360-minute workflow timeout is comfortably above the conservative 107.58075424000026-minute estimate for 8005.

The proposed resumable state.json checkpoint design also limits the cost of partial failure: completed scenario jobs can be recognized and skipped on resume rather than rerunning the completed work.

### Option C

Runtime is approximately the same as Option B when max-parallel=10, but the small direct-matrix design provides less explicit structure for checkpointing and recovery. It is therefore less attractive for the long Stage 7 execution.

## 4. Recommendation

Choose Option B: one workflow, 25 matrix jobs, max-parallel: 10, job timeout 360 minutes, with per-scenario checkpoint/resume state.

Reasons, in order:

1. It stays safely below the stated GitHub Free concurrency limit of 20.
2. Even the conservative 8005 estimate is 107.58075424000026 minutes, leaving more than 240 minutes of margin under the 360-minute timeout.
3. It keeps one central Run ID and one audit trail instead of 25 independent workflow runs.
4. It supports controlled restart/resume after partial failures.
5. CP4 confirms that disabling event logging reduces mean C050_G100 time by 14.978500465854495% and mean RSS by 66.71013954116971%, while preserving 5/5 TrialResult SHA equality. Therefore Stage 7 should use the no-event-log execution mode unless another already-approved Stage 7 rule requires event logging.

## Final CP5 decision

- Recommended architecture: Option B
- Matrix jobs: 25
- max-parallel: 10
- Timeout: 360 minutes
- Stage 7 full trial targets: 6005 / 7005 / 8005
- Stage 7 remains not started by this CP5.
