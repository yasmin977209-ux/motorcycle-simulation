# D0 Repository Closure — Stage D / S6

**Status:** `D0_REPOSITORY_CLOSED / PASS_SCOPED_WITH_LIMITATIONS`  
**Classification:** `T2_INTERIM / NOT_FINAL_BLOCKED`  
**Live pre-update HEAD:** `61532b9230f3162eb2f6cb0fa0da2ddbfe1a0dd9`  
**main:** `c6e54349a5e94f65d5aa9f83141f225d777bb474`

## Current live evidence
- D0 Markdown: [remote file](D0_INPUT_AUDIT.md); Git blob SHA-1 `7dcdcd9fbc7244f9cb98bdb42ea889abc9899950`; remote-byte SHA-256 `dccb66a3879139867c69390323e6fec14fb0457176342d78b3e3e59e2f906190`; commit `cd97dca1f982f9d9220bd335b478c085ec85c679`.
- D0 JSON: [remote file](D0_INPUT_AUDIT.json); Git blob SHA-1 `02e250c9b3ac493e7ff9543c2c8ebe185a319801`; remote-byte SHA-256 `93f1bbc6d3d352f057d68c8f6d2beb9fb2a61737dc9a49df415a38c06d3f68eb`; commit `d087e4eb951ced0efee4c910b690c712ab26a126`.
- Continuity: [remote file](../PROJECT_CONTINUITY.md); Git blob SHA-1 `b956ebee141e3e9d625114973a0693506454b117`; remote-byte SHA-256 `19d0ff5fac286cece2dcb10d9c1c6c3468be5aa8e0a2d700e667659ff1a6b07a`; commit `126451e5466e83363bbece84992279d660c1bd0b`.

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

The D0 audit Markdown, JSON, and continuity references above were fetched from the authorized branch and SHA-256 recomputed from the returned UTF-8 bytes. The commit IDs listed beside each file were fetched independently and each commit was confirmed to contain the corresponding path. The three immutable input archive hashes and sizes remain `VERIFIED_LOCAL (prior byte audit)`; they were not redownloaded or rehashed in this documentation-only update.
