# REV5 Prompt Library Merge Audit — 2026-11-05

Repository: `yasmin977209-ux/motorcycle-simulation`  
Branch: `tmp/d1-rebuild-20261101`  
Pre-update HEAD: `a4d120bb65360dfa1fbeb8e4600b1fc773411bdf`  
REV5 creation commit: `28367e7edbe16c5555daa3a65dab78ce9ac547e9`

## 1. Source versions inspected

The four source libraries were read from the live working branch. Their Git tree identities at REV5 commit are:

| Version | Path | Git blob SHA-1 | Git tree size |
|---|---|---|---:|
| REV1 | [PROJECT_PROMPT_LIBRARY_AR_2026-11-01.md](PROJECT_PROMPT_LIBRARY_AR_2026-11-01.md) | `018f6196de97856ab1326b371f61fae5d9d14b03` | 64,922 |
| REV2 | [PROJECT_PROMPT_LIBRARY_AR_2026-11-01_REV2.md](PROJECT_PROMPT_LIBRARY_AR_2026-11-01_REV2.md) | `3567c30d929be6b67a2eee0a684f88d4941e749c` | 72,209 |
| REV3 | [PROJECT_PROMPT_LIBRARY_AR_2026-11-05_REV3.md](PROJECT_PROMPT_LIBRARY_AR_2026-11-05_REV3.md) | `b9e34a3c9440b5a179b3fedfd6df68ec77d665cc` | 100,131 |
| REV4 | [PROJECT_PROMPT_LIBRARY_AR_2026-11-05_REV4.md](PROJECT_PROMPT_LIBRARY_AR_2026-11-05_REV4.md) | `1c0eeb136f21a7dbb73242435e02cfe727a2df7d` | 134,993 |

The source versions remain in Git history and were not overwritten or deleted.

## 2. Consolidation decisions

- REV1 supplied the foundational stage prompts and execution sequence.
- REV2 supplied the improved governance hierarchy, evidence requirements, builder/registry and deliverable checks.
- REV3 supplied current-state recovery, artifact retention priorities, C-based workbook partition plan and E3 readiness separation.
- REV4 supplied the zero-gap hard stop, scoped-vs-complete closure semantics, Global Preservation Gate, D3 scenario sub-gate and E3–E6 locks.
- REV5 consolidates these into one operational contract, full phase prompts D0–D6/E0–E6, shared evidence/report schemas, owner-authority controls and one-stage-at-a-time dispatch.

## 3. Conflict resolutions

1. Stale HEADs and stage snapshots are historical; all sessions must re-fetch branch/main refs.
2. `PASS_SCOPED` and `PASS_SCOPED_WITH_LIMITATIONS` do not permit stage transition.
3. D3 partitioning is an obligatory sub-gate `D3-S` inside D3, not a new major phase; this preserves D0–D6/E0–E6 ordering.
4. Ten derived workbooks are required (five per language); each C partition includes all five G levels and the complete 25-scenario coverage must be asserted from actual workbook bytes and manifest mapping.
5. The source workbooks are about 27.7 MB each, below the 100 MB single-file threshold; partitioning is for delivery organization and does not solve Actions artifact expiry.
6. Original historical evidence, forensic audit and replay reconstruction remain separate. Replay cannot fill historical accounting gaps.
7. The owner may send a phase name as the only routine command, but this does not waive owner-only decisions, physical phone-copy limitations or external storage authorization.

## 4. REV5 scope and non-actions

REV5 changes operational instructions and documentation only. It does not change v2.4.0, business rules, thresholds, SOURCE_SHA, cohort_id, MASTER_SEED, Trial identity, historical artifacts/manifests, simulation results or acceptance verdicts. It does not authorize Trials, Simulation, Monte Carlo, N expansion, backfill, zero-fill, main writes, merge, force-push, Release or final acceptance declarations.

## 5. REV5 remote evidence

- File: [PROJECT_PROMPT_LIBRARY_AR_2026-11-05_REV5.md](PROJECT_PROMPT_LIBRARY_AR_2026-11-05_REV5.md)
- GitHub URL: https://github.com/yasmin977209-ux/motorcycle-simulation/blob/tmp/d1-rebuild-20261101/docs/stage_d/PROJECT_PROMPT_LIBRARY_AR_2026-11-05_REV5.md
- Git blob SHA-1: `2c8d8595c69251e80b050013f856417e9cf77ba0`
- SHA-256 of fetched remote text bytes: `090f7c36b83308bd0d54054de913dc0df707bd214fcd3cf9a31cc939e01ea2a2`
- UTF-8 size: 52,364 bytes
- Containing commit: `28367e7edbe16c5555daa3a65dab78ce9ac547e9`

The file was re-fetched from GitHub after creation. SHA-256 was computed from the fetched text's UTF-8 bytes; the blob SHA-1 and containing commit were independently read from GitHub's Git tree/commit APIs.

## 6. Remaining work

- Append REV5 references to project continuity, session status and handoff.
- Re-read those updated files from GitHub and verify their hashes/commits.
- Verify exact final branch HEAD and combined status.
- Keep `main` unchanged.
- Do not claim phase gap-free closure from this library update; each phase still requires its own execution and evidence.
