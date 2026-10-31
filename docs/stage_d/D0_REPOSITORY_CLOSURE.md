# D0 Repository Closure — Stage D / S6

**Status:** `REPORTED_ONLY / D0_REMOTE_SHA256_REVALIDATION_PENDING`  
**Classification:** `T2_INTERIM / NOT_FINAL_BLOCKED`  
**Live pre-update HEAD:** `61532b9230f3162eb2f6cb0fa0da2ddbfe1a0dd9`  
**main:** `c6e54349a5e94f65d5aa9f83141f225d777bb474`

## Current live evidence
- D0 Markdown: [remote file](D0_INPUT_AUDIT.md); Git blob SHA-1 `7dcdcd9fbc7244f9cb98bdb42ea889abc9899950`; remote-byte SHA-256 `NOT_RECOMPUTED_UNDER_VERIFIED_HASH_IMPLEMENTATION`; commit `cd97dca1f982f9d9220bd335b478c085ec85c679`.
- D0 JSON: [remote file](D0_INPUT_AUDIT.json); Git blob SHA-1 `02e250c9b3ac493e7ff9543c2c8ebe185a319801`; remote-byte SHA-256 `NOT_RECOMPUTED_UNDER_VERIFIED_HASH_IMPLEMENTATION`; commit `d087e4eb951ced0efee4c910b690c712ab26a126`.
- Continuity: [remote file](../PROJECT_CONTINUITY.md); Git blob SHA-1 `b956ebee141e3e9d625114973a0693506454b117`; remote-byte SHA-256 `NOT_RECOMPUTED_UNDER_VERIFIED_HASH_IMPLEMENTATION`; commit `126451e5466e83363bbece84992279d660c1bd0b`.

## Immutable D0 inputs rechecked locally

| Input | Artifact | Run | Bytes | SHA-256 |
|---|---:|---:|---:|---|
| S6 N=2400 aggregate | 12852969854 | 40773412377 | 9,357,996 | `ec05a69ae8968585decf83cf0716d56c264f47f86187cfd3cf53b11f52ca2e54` |
| Representative Full Logging | 12998778418 | 41098699740 | 310,827,203 | `403371cc8eb12880dda05529b4c83dd675bfa609e8680c09d35efa729c5b5aeb` |
| C100 deterministic reuse | 12630457193 | 40263424595 | 361,733 | `c977d1cbb5204919eadc72358533f77cdbbc239902bcd6f921bf1a915a716e79` |

All three local byte hashes and sizes match; ZIP CRC, duplicate member/path and traversal checks pass.

## Limitations preserved
- Full Logging covers 105 representative keys only, not all 48,000 historical trials.
- Five historical accounting fields and the full historical 48K daily ledger remain `MISSING_EVIDENCE`.
- Parquet schemas/rows were not parsed in the current runtime.
- SHA/fingerprint checks for 105 manifests match, but independent expected byte sizes are absent; all 105 normalized statuses remain `NOT_VERIFIED`; original pending states remain unchanged.
- Preserve all open `K_SPEC` conflicts, including document status, historical reference hash, trial manifest status and S6 code mapping.

**Disposition:** D0 is closed at the pinned-input audit and repository-documentation level only. It is not full production accounting acceptance or final project acceptance. No Trial, Simulation, Monte Carlo, N=4800, main update, PR, merge or Release was performed.


## Remote-byte verification update — 2026-10-31

The D0 audit Markdown, JSON, and continuity references were fetched from the authorized branch and their Git blob SHA-1 values and containing commits were verified. A reliable SHA-256 recomputation from their remote bytes was not completed in this update; therefore these references do not satisfy the owner's three-part evidence gate. The three immutable input archive hashes and sizes remain `VERIFIED_LOCAL (prior byte audit)` only; they were not redownloaded or rehashed in this documentation-only update. D0's earlier scoped audit conclusion is retained as historical evidence, but is not re-declared PASS under the new remote-SHA-256 rule.
