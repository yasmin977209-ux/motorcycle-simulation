# D0 Repository Closure — Stage D / S6

**Status:** `COMPLETE / PASS_SCOPED_WITH_LIMITATIONS`  
**Classification:** `T2_INTERIM / NOT_FINAL_BLOCKED`  
**Current branch HEAD before this closure update:** `e8d26cfcbe85ceaaa44312e6821621fa2ab7f80b`  
**main:** `c6e54349a5e94f65d5aa9f83141f225d777bb474`

## D0 decision

D0 is closed as a scoped input-verification and preflight stage. The three authorized immutable GitHub Actions artifacts were downloaded again from GitHub in this session. Their SHA-256 values were recalculated from the downloaded remote ZIP bytes, sizes matched, ZIP CRC checks passed, and duplicate names, unsafe paths, and symlink members were zero.

The detailed evidence is recorded in [D0 Remote Evidence Ledger](D0_REMOTE_EVIDENCE_LEDGER_2026-10-31.md), remote content SHA-256:
`4ac7b2c3acbddc297c289586b72117b115bb2695a90538b9550bf759ab17bb18`,
Git blob SHA-1 `0ad14ec661b4823c5d3d2f1372029f4fe7e8a790`,
containing commit `4cd0aa9afcdd3ca09a9cdf9cb75d68062dae33e0`.

## Pinned remote artifacts

| Input | Artifact / Run | Tested SHA | Bytes | SHA-256 of downloaded GitHub artifact bytes |
|---|---:|---|---:|---|
| S6 N=2400 aggregate | 12852969854 / 40773412377 | `4f2f2cc16d0cb5125262088704febccbae6f50ed` | 9,357,996 | `ec05a69ae8968585decf83cf0716d56c264f47f86187cfd3cf53b11f52ca2e54` |
| Representative Full Logging | 12998778418 / 41098699740 | `e3c2098df9fc5dbc126eb1e77ad35c493ff3ac70` | 310,827,203 | `403371cc8eb12880dda05529b4c83dd675bfa609e8680c09d35efa729c5b5aeb` |
| C100 deterministic reuse | 12630457193 / 40263424595 | `24050f15bc7eb3097e20f76785a45c5d177643dd` | 361,733 | `c977d1cbb5204919eadc72358533f77cdbbc239902bcd6f921bf1a915a716e79` |

Each artifact has a GitHub Actions artifact URL in the evidence ledger and a producing Run whose tested SHA is listed above.

## D0 repository-file evidence

Remote UTF-8 contents were fetched from GitHub. SHA-256 was computed from those fetched bytes; Git blob SHA-1 was independently recomputed and matched GitHub's blob SHA-1.

| File | Remote SHA-256 | Git blob SHA-1 | Containing commit |
|---|---|---|---|
| [D0_INPUT_AUDIT.md](D0_INPUT_AUDIT.md) | `1064e81dd98ddaefd443389a5bbc6d53fc1052903328d533839da84a16f705a0` | `7dcdcd9fbc7244f9cb98bdb42ea889abc9899950` | `cd97dca1f982f9d9220bd335b478c085ec85c679` |
| [D0_INPUT_AUDIT.json](D0_INPUT_AUDIT.json) | `abe8482b44b78de950c33c9b1b38480e90e08b2563f184acf70695036b17aa80` | `02e250c9b3ac493e7ff9543c2c8ebe185a319801` | `d087e4eb951ced0efee4c910b690c712ab26a126` |
| [PROJECT_CONTINUITY.md](../PROJECT_CONTINUITY.md) | `b844682d2a600814fdd65dda6c287160ed46d38af4fbf557c57bf88e96d80be4` | `abbc4909feacba26055d0c6db703d0ec5b963ea5` | `36e186a2f5d2dbf2d67749ed5a75a3912f0b9f5f` |
| [Owner decision](../governance/D-2026-10-30-REFERENCE-V2.4.0.md) | `1076b3e876d3db1a7e6ab4473fedb22226dfda0cb499d230ba3a0c2a9652a95d` | `58f89bc016523f1350345428b4a224ac42a8b130` | `bba6dd275956da60995c4da99398bd992ee5e1c5` |
| [D0 closure](D0_REPOSITORY_CLOSURE.md) prior version | `3840185213f646bb215deaba2bfb509bc8bba1ce570703e0b8cb51ec39fb5f7b` | `0aab322a45e26aee0bc9adb4d3c784681ae1d7cd` | `fa349360e08bbf8dca83dbd65e4c7abe9d2ddd7d` |

The current D0 closure file is updated by the commit containing this revision; its new remote SHA-256 and commit are to be recorded by the post-write readback.

## Limits preserved — not cleared by D0

- Aggregate Parquet schema/row parsing remains `MISSING_EVIDENCE` unless independently run with a Parquet reader.
- Historical full daily ledgers for 48,000 trials remain `MISSING_EVIDENCE`.
- The five missing historical accounting fields remain absent: `Accounts_Receivable`, `Accumulated_Depreciation`, `Gross_Bike_Assets`, `Guarantee_Claim_Receivable`, `Total_Assets`.
- Full Logging covers 105 representative unique keys only; it does not close the 48K historical gap.
- The original pending trial-manifest statuses and all `K_SPEC` conflicts remain preserved. The D1 resolver must fail closed where independent expected byte sizes are absent.
- No inferred values, zero-fill, backfill, cohort mixing, or historical manifest mutation.

## D1 entry boundary

D1 may proceed within the pinned source boundary only. The independent Builder must not import Stage 13 selectors or run simulations. D1 is not considered closed until all source files and tests are individually committed, fetched back, SHA-256 verified from remote bytes, and validated on the exact source commit.

## Prohibited actions

No Trial, Simulation, Monte Carlo, N=4800, main update, PR, merge, or Release was performed. D0 does not grant final acceptance or statistical convergence.


## Corrected remote evidence pointer — 2026-10-31

The D0 remote evidence ledger was corrected after an independent SHA-256 implementation was validated against the standard test vector and Git blob SHA-1 readback. Use the corrected ledger triple above; superseded SHA-256 values are invalid. The closure document itself must be read back at its latest branch commit for its current SHA-256.
