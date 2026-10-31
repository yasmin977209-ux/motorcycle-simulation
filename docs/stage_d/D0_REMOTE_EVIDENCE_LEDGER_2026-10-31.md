# D0 Remote Evidence Ledger — 2026-10-31

**Scope:** D0 pinned-input verification and repository evidence closure only.  
**Classification:** `T2_INTERIM / NOT_FINAL_BLOCKED`.  
**Repository:** `yasmin977209-ux/motorcycle-simulation`.  
**Branch:** `tmp/cp-v240-stage-d-s6-deliverables-20261030`.  
**Branch HEAD observed before this ledger commit:** `fa349360e08bbf8dca83dbd65e4c7abe9d2ddd7d`.  
**main observed:** `c6e54349a5e94f65d5aa9f83141f225d777bb474`.

## 1. Three pinned GitHub Actions artifacts — downloaded again from GitHub

All three artifacts were downloaded in this session through the GitHub Actions artifact download endpoint, then SHA-256 was recalculated from the downloaded ZIP bytes. ZIP CRC test passed; duplicate member names, unsafe paths, and symlink members were all zero.

| Input | Artifact / Run | Run tested SHA | Remote artifact URL | Bytes | SHA-256 of downloaded remote bytes | ZIP members | CRC / paths |
|---|---:|---|---|---:|---|---:|---|
| S6 N=2400 aggregate | 12852969854 / 40773412377 | `4f2f2cc16d0cb5125262088704febccbae6f50ed` | https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40773412377/artifacts/12852969854 | 9,357,996 | `ec05a69ae8968585decf83cf0716d56c264f47f86187cfd3cf53b11f52ca2e54` | 7 | PASS; 0 duplicates, 0 unsafe paths, 0 symlinks |
| S6 representative Full Logging | 12998778418 / 41098699740 | `e3c2098df9fc5dbc126eb1e77ad35c493ff3ac70` | https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41098699740/artifacts/12998778418 | 310,827,203 | `403371cc8eb12880dda05529b4c83dd675bfa609e8680c09d35efa729c5b5aeb` | 1,578 | PASS; 0 duplicates, 0 unsafe paths, 0 symlinks |
| C100 deterministic reuse | 12630457193 / 40263424595 | `24050f15bc7eb3097e20f76785a45c5d177643dd` | https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40263424595/artifacts/12630457193 | 361,733 | `c977d1cbb5204919eadc72358533f77cdbbc239902bcd6f921bf1a915a716e79` | 9 | PASS; 0 duplicates, 0 unsafe paths, 0 symlinks |

For each Run, GitHub API returned `status=completed`, `conclusion=success`, and the artifact ID, name, size, and download URL above. The tested SHA is the producing commit, not the current Stage D branch commit.

## 2. D0 repository files — remote-byte SHA-256

The following files were fetched from the live Stage D branch using GitHub Contents API. SHA-256 was calculated from the fetched UTF-8 content bytes. The Git blob SHA-1 was independently recomputed using the Git blob header and matched GitHub's returned blob SHA-1, validating the byte representation used for the SHA-256 calculation.

| File | GitHub URL | Git blob SHA-1 | Remote content SHA-256 | UTF-8 bytes | Containing commit |
|---|---|---|---|---:|---|
| `docs/stage_d/D0_REPOSITORY_CLOSURE.md` | https://github.com/yasmin977209-ux/motorcycle-simulation/blob/tmp/cp-v240-stage-d-s6-deliverables-20261030/docs/stage_d/D0_REPOSITORY_CLOSURE.md | `0aab322a45e26aee0bc9adb4d3c784681ae1d7cd` | `3840185213f646bb215deaba2bfb509bc8bba1ce570703e0b8cb51ec39fb5f7b` | 3,494 | `fa349360e08bbf8dca83dbd65e4c7abe9d2ddd7d` |
| `docs/stage_d/D0_INPUT_AUDIT.md` | https://github.com/yasmin977209-ux/motorcycle-simulation/blob/tmp/cp-v240-stage-d-s6-deliverables-20261030/docs/stage_d/D0_INPUT_AUDIT.md | `7dcdcd9fbc7244f9cb98bdb42ea889abc9899950` | `ad1ae34568f06f088c1de203baa4af242e6127721783aeeb802eb8812a29c6a9` | 28,171 | `cd97dca1f982f9d9220bd335b478c085ec85c679` |
| `docs/stage_d/D0_INPUT_AUDIT.json` | https://github.com/yasmin977209-ux/motorcycle-simulation/blob/tmp/cp-v240-stage-d-s6-deliverables-20261030/docs/stage_d/D0_INPUT_AUDIT.json | `02e250c9b3ac493e7ff9543c2c8ebe185a319801` | `bf8ba80a1d25352a63333a199c90a9974b59ffcf5230af63dc63d98cb0130a8d` | 13,243 | `d087e4eb951ced0efee4c910b690c712ab26a126` |
| `docs/PROJECT_CONTINUITY.md` | https://github.com/yasmin977209-ux/motorcycle-simulation/blob/tmp/cp-v240-stage-d-s6-deliverables-20261030/docs/PROJECT_CONTINUITY.md | `abbc4909feacba26055d0c6db703d0ec5b963ea5` | `b844682d2a600814fdd65dda6c287160ed46d38af4fbf557c57bf88e96d80be4` | 445,430 | `36e186a2f5d2dbf2d67749ed5a75a3912f0b9f5f` |
| `docs/governance/D-2026-10-30-REFERENCE-V2.4.0.md` | https://github.com/yasmin977209-ux/motorcycle-simulation/blob/tmp/cp-v240-stage-d-s6-deliverables-20261030/docs/governance/D-2026-10-30-REFERENCE-V2.4.0.md | `58f89bc016523f1350345428b4a224ac42a8b130` | `417c8838c4f70d8571938af89f1b34ec7e680dceaae8a594e242d55d1e94778c` | 3,527 | `bba6dd275956da60995c4da99398bd992ee5e1c5` |

## 3. D0 data-boundary results retained

- S6 identity: source `da1a9ea9b5cd789c944de3f07b08395bb67c49e7`, cohort `s6-v23-da1a9ea9`, seed `20270101`.
- C100 identity: source `965281d52441cd0d4b744e211c9f68ee4cdc3753`, cohort `c100-v23-s4-20261026-965281d5`, classification `CROSS_COHORT_DETERMINISTIC_REUSE`.
- Stage 12/13 source `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b` remains a separate historical lineage.
- Representative mapping: 125 assignments, 105 unique keys (100 S6 + 5 C100).
- Full Logging scope: 105 representative keys only. Prior Stage C audit records 216,253 daily rows, 24,545,842 events, 1,297,518 roll-forward checks, zero recorded balance/roll-forward mismatches, and 14 integer accounting fields across representative daily rows.
- Aggregate Parquet schemas/rows remain `MISSING_EVIDENCE` for independent parsing in this runtime; do not infer them from file hashes.
- Historical 48K daily ledgers and five accounting fields remain `MISSING_EVIDENCE`: `Accounts_Receivable`, `Accumulated_Depreciation`, `Gross_Bike_Assets`, `Guarantee_Claim_Receivable`, `Total_Assets`.
- Preserve all open `K_SPEC` conflicts and original manifest statuses.

## 4. D0 disposition

D0 is closed as an input-verification/preflight stage with scoped limitations: `COMPLETE / PASS_SCOPED_WITH_LIMITATIONS`. This is not full production accounting acceptance, not project final acceptance, and not permission to synthesize missing data. D1 may proceed only within the source-bounded rules and only after the D1 source files and tests are actually published and exact-head validated.

## 5. Explicitly not done

No Stage D workflow was run in this verification pass. No Trial, Simulation, Monte Carlo, N=4800, PR, merge, Release, or main update occurred.


## Hash correction note — 2026-10-31

A subsequent independent SHA-256 implementation was validated against the standard `abc` test vector and the Git blob SHA-1 of each fetched file. This revision corrects four remote-content SHA-256 values above; the previous values were erroneous and must not be used. Git blob SHA-1 values, file URLs, sizes and containing commits remain unchanged. The current D0 closure file is a later revision than the historical closure row above; its current triple is recorded in the session status handoff.


## Correction: continuity digest — 2026-10-31

The live GitHub file docs/PROJECT_CONTINUITY.md was fetched again and SHA-256 was computed from its 444,746 UTF-8 bytes. The correct value is 7458723582ba50454ff80bacb4132afacf76035de9db0907da0145d86ed20f74; its Git blob SHA-1 remains b956ebee141e3e9d625114973a0693506454b117. The previous value d9ade8e347b1b0bec7a9a60e35ca05ae2a8374c51a7ba5f7da494bd5b66c7d78 is superseded and invalid. This correction records the verified state before the subsequent canonical-reference text correction; the later continuity version and its new digest are recorded in the current row above.


## Correction: canonical governing-reference identity — 2026-10-31

The authority block in docs/PROJECT_CONTINUITY.md was corrected to identify v2.4.0 SHA-256 225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b as the current governing reference, and to identify ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479 as Stage 12/13 historical lineage only. The corrected continuity file is 445,430 bytes, remote SHA-256 b844682d2a600814fdd65dda6c287160ed46d38af4fbf557c57bf88e96d80be4, Git blob SHA-1 abbc4909feacba26055d0c6db703d0ec5b963ea5, containing commit 36e186a2f5d2dbf2d67749ed5a75a3912f0b9f5f. The S6 historical execution reference remains v2.3 SHA-256 e5efaf0874384e8248c339ca10e248ea9e17e9f0882153b4ef88bc955b91d53f.


## SHA-256 implementation correction — 2026-10-31

The intermediate value 5c0dbe96806f8a7a268b4516eee9cb523fb83268429c528612af7ca0ad0780d6 is superseded. The current continuity file SHA-256 is b844682d2a600814fdd65dda6c287160ed46d38af4fbf557c57bf88e96d80be4, computed from the fetched 445,430 UTF-8 bytes using an implementation validated against both the SHA-256 abc vector and the 1,000,000-byte 'a' vector. Git blob SHA-1 and containing commit are unchanged.
