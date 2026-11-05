# CP-GOV-REFERENCE-CHECKPOINT-ACCOUNTING-GOLDEN-FULLSUITE — 2026-10-29

## Executive disposition

**Scoped review passed; overall production inference and final delivery remain blocked.**

- Main baseline at review start: c6e54349a5e94f65d5aa9f83141f225d777bb474.
- Exact candidate tested: 35a3d2a9fa4820e35873deedd83c73ddccd1bdd5.
- PR #78 remains open as Draft; it was not merged. Main state.json stayed byte-identical with blob 6d94e0699e5380b4ecc184203d0c5ad6a4a8fb66.

## 1. Authoritative reference conflict

Raw-byte SHA-256 was recomputed from the Library objects, not inferred from extracted snippets.

| Exact file | Bytes | SHA-256 | Current disposition |
|---|---:|---|---|
| المرجع_النهائي_الموحد_المعتمد.md | 271,496 | ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479 | Effective reference pinned in the current source/governance lineage |
| المرجع_النهائي_الموحد_v2.3-إعادة_صياغة(1).md | 381,559 | e5efaf0874384e8248c339ca10e248ea9e17e9f0882153b4ef88bc955b91d53f | Separate, unadopted draft |

The e5ef hash is valid for the v2.3 rewrite, but not for the filename that main pins as the official original reference. The v2.3 header calls itself both “approved and operative” and “draft for adoption,” and introduces changed RNG/source identity plus new tests through 192. No effective-main decision adopts that document. Under the existing governance and reference pins, ee277 remains effective for the present implementation; v2.3 cannot close K_SPEC or substitute a new Golden lineage without a separate adoption decision and source-identity review.

## 2. Checkpoint contract

D-2026-10-10-01 governs the schedule for new execution: 300 → 600 → 1200 → 2400 → 4800 → …, no fixed cap, completed IDs never rerun; +50 is a legacy compatibility constant only. The later approved IUT reconciliation requires four cumulative points and three successful adjacent transitions for final SCENARIO_STABLE. Current constants, run_batch.py, scripts/stage7_stability.py and tests/test_stage7_authoring.py match that four-point/three-transition contract. The earlier audit sentence saying the current window accepts only three history entries is stale and is corrected by an append-only addendum below. The P50 >5% rule is a separate preliminary continuation trigger, not a replacement for the IUT final window.

## 3. Full accounting-balance evidence

docs/stage12/roll_forward_validation.json, blob 6084e8f68fa649fcf0726daa04f41ae9b0636706, records overall_result PASS for 25 scenarios, 11,005 trials and 22,546,465 daily rows. The recorded cash, receivables, gross assets, accumulated depreciation, net assets, equity, equity equation, asset components, zero liabilities, Balance_Difference matching/zero, source/scenario/seed identity checks each checked 22,546,465 rows with zero violations and no examples. Trial-ID sequence checked 10,980 rows with zero violations; date continuity, opening balance continuity and constant result fingerprint each checked 22,546,440 adjacencies with zero violations.

This establishes full recorded accounting-rollforward and balance equality coverage for the Stage 12 canonical cohort. It is not a fresh re-materialization of all 22.5 million rows during this CP, and it does not rewrite the historical Stage 9C overall PARTIAL disposition or imply final workbook acceptance.

## 4. Independent Golden evidence and scope

D-2026-10-24-01 permits read-only use of the exact pinned Golden map for integrity checks. The historical independent bridge run 38169163565 completed successfully with 27/27 jobs: 11,005/11,005 exact trial fingerprints, 22,546,465/22,546,465 daily rows and zero mismatches. The rehashed Stage 12 and source-Golden maps matched the official SHA-256 7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44. Artifact 11713395913; ZIP SHA-256 e00afa6a5d5ddbc8f84b5e225755535818460ec016d211fad0d1d2a210cfd996.

The authorized map covers 24,005 base fingerprints and a separate 1,200-ID extension for C030_G030, IDs 1201–2400, giving 25,205 fingerprints combined. Other 19 non-C100 scenarios remain unsupported above ID 1200. This is a source/identity validation of the existing canonical cohort and bounded map, not a production Gate A PASS for new future trials, and not statistical acceptance.

## 5. Missing test data and full-suite outcome

The earlier candidate workflow run 40543690736 failed with 5 failed, 512 passed, 1 skipped, 1 warning. Four failures were caused by absent generated Stage 5 test fixtures: worker_equivalence_manifest.json (test 127), trials_summary.parquet and selection/role payloads (tests 159–160), and daily_distribution.parquet (test 161). The fifth failure was a CalledProcessError from the Python-hash-seed subprocess; the old log does not preserve the child's inner stderr, so its exact original exception should not be invented.

The PR branch workflow was corrected to generate temporary fixtures from the accepted fixture-first Stage 5 logic and to set PYTHONPATH=. for the complete test command. The fixture step performs one deterministic C100_G100 trial and a three-trial C070_G100 serial-vs-parallel worker equivalence check for workers 2 and 4; these are bounded test fixtures in the CI runner, not an adaptive production Monte Carlo cohort.

Final evidence on the exact candidate SHA 35a3d2a9fa4820e35873deedd83c73ddccd1bdd5:

| Run | Status | Evidence |
|---|---|---|
| PR workflow 40797229996 | SUCCESS | https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40797229996 |
| Push workflow 40797224205 | SUCCESS | https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40797224205 |
| Focused R4 regression | 1 passed | job 123196536411 |
| Full test inventory | 517 passed, 1 skipped, 1 warning, 0 failed; 336.12 seconds | job 123196536411 |

The one skip is Test 158, explicitly marked K_TEST / ADJUDICATION and excluded from the effective acceptance count. The one non-blocking warning is the invalid escape sequence in scripts/stage13_assemble.py:346. Historical failed runs remain preserved; the passing exact-head run does not rewrite those historical records.

## 6. Remaining blockers and acceptance boundary

docs/stage7/statistical_execution_gate.json remains BLOCKED_FOR_IMPLEMENTATION. The financial-mean K_SPEC still lacks a proved finite support or approved quantified tail/moment bound and an accepted time-uniform interval procedure; quantile and loss-probability methods are not integrated into the production decision path; production P90_Held_Assets identity/completeness acceptance remains missing; and C030_G030 / P90_Final_Cash N=300→600 remains FAILED_NOT_REQUALIFIED. The v2.3 draft itself calls for coverage acceptance through test 192; the current successful pytest inventory does not mean test 192 or production statistical inference passed.

No production adaptive Monte Carlo, new production checkpoint, Golden extension, final workbook acceptance or Release was performed by this CP. Keep all production/stability/final-acceptance flags false and preserve main and main/state.json.

## 7. Exact files reviewed

- docs/stage7/statistical_execution_gate.json — blob a3324db6b4edecb35b28d22bf2b74e1b32370dca.
- docs/stage12/roll_forward_validation.json — blob 6084e8f68fa649fcf0726daa04f41ae9b0636706.
- docs/governance/DECISIONS_LOG.md — blob 6434c5865ec7e8244aeae5ef8b7ea577fb8cf790 before this reconciliation.
- docs/PROJECT_CONTINUITY.md — main blob bbd9d69440b7b84e0a77a5ddc0a6e59140b95566 before this append.
- PR #78 and exact tested head 35a3d2a9fa4820e35873deedd83c73ddccd1bdd5.
