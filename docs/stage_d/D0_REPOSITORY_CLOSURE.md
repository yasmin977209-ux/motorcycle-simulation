# D0 Repository Closure — Stage D / S6

**Status:** `D0_REPOSITORY_CLOSED / PASS_SCOPED_WITH_LIMITATIONS`  
**Classification:** `T2_INTERIM / NOT_FINAL_BLOCKED`  
**Live pre-update HEAD:** `61532b9230f3162eb2f6cb0fa0da2ddbfe1a0dd9`  
**main:** `c6e54349a5e94f65d5aa9f83141f225d777bb474`

## Current live evidence
- D0 Markdown blob SHA-1: `7dcdcd9fbc7244f9cb98bdb42ea889abc9899950`; content SHA-256: `94fce3d6c4a4713ed393370aa66ad40778b7c62129ebb7c8de56a67467b36173`.
- D0 JSON blob SHA-1: `02e250c9b3ac493e7ff9543c2c8ebe185a319801`; content SHA-256: `48c09485d9562188368d16f2f457a0d0908de5655fcde84dcf154f61d8ba44e2`.
- Continuity blob SHA-1: `3f05f706cca1d14ae9326cf5519f4271b050e5e3`; content SHA-256: `bf6f157c26a2072ccb5c5df4b73e1e03332e4c51439772a7c53f00a9e7747caf`.

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
