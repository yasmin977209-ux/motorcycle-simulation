# R4 — Stage 13 exact MaxCase partner memo-balance recovery

**Date:** 2026-10-24  
**Disposition:** PASS_RECOVERY / FINAL_ACCEPTANCE_BLOCKED  
**Scope:** Re-run only ten previously selected canonical Trial IDs to recover their daily Partner 1 and Partner 2 memo-balance state, then compare each replay to the pinned historical Trial fingerprint and all common Stage 12 daily fields. This is a recovery evidence artifact, not a Stage 12 rewrite and not a workbook acceptance.

## Authority, identity, and exact scope

The user explicitly delegated the project work on 2026-10-24, including this bounded replay of the same already-selected Trial IDs. No new Trial IDs were created. Every replay used SOURCE_SHA=f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b, master_seed=20270101, and the existing deterministic RNG implementation. The 12 engine/accounting identity files were checked byte-for-byte using their canonical Git blob SHA-1 identities at SOURCE_SHA; all matched.

The immutable source audit was run 40038112945, artifact 12537818827, ZIP SHA-256 88abdc9e0ce4097df044280b517f08b1595642476c8d596ac13fc128b88092b3. Its paired JSON files were separately pinned to:
- stage13_maxcase_source_audit.json: b9ba0ff23b3dfd42abd7436b7935017f15ba8cbaf5198d8e31093a56441fb951
- stage13_maxcase_daily_payloads.json: 096a85448ff5c7ece0648739fdc4ccad499763f1862467751983e0152f8e8c7d

Recovery implementation is commit d80b91579bdfda6277f630ece764777261df2059, tested in [Run 40050459020](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40050459020). That exact recovery run returned PASS, replayed 10/10 Trials, recovered 21,575 daily rows, reported zero source Trial fingerprint mismatches and zero daily common-field mismatches, and uploaded artifact [12542814312](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40050459020/artifacts/12542814312). The ZIP SHA-256 is 85e0d747044910d8d9837085b3a221a7459feb418eb78776ae3b4f1a31f5db68; the recovery JSON inside it has SHA-256 c477e390a5b0b9c8c35a3d5474e5b359056e59d1f2254395e589af4621982006.

## Exact replay results

| Scenario | Selected Trial ID | Daily rows matched | Recovered final P1 memo balance | Recovered final P2 memo balance | Trial SHA-256 match |
|---|---:|---:|---:|---:|---|
| C085_G030 | 53 | 2,198 | 134,983,800 | 111,982,200 | PASS |
| C070_G100 | 106 | 2,202 | 134,975,750 | 111,822,750 | PASS |
| C070_G050 | 544 | 2,200 | 134,942,150 | 111,808,350 | PASS |
| C070_G030 | 429 | 2,200 | 134,847,650 | 111,767,850 | PASS |
| C070_G000 | 165 | 2,202 | 134,961,050 | 111,816,450 | PASS |
| C050_G100 | 172 | 2,233 | 194,263,300 | 136,919,700 | PASS |
| C050_G070 | 7 | 2,222 | 182,205,310 | 129,723,990 | PASS |
| C050_G050 | 543 | 2,232 | 180,065,900 | 128,339,100 | PASS |
| C050_G030 | 122 | 2,231 | 175,992,810 | 126,905,490 | PASS |
| C030_G000 | 199 | 1,655 | 5,323,850 | 9,925,650 | PASS |
| **Total** | **10 exact IDs** | **21,575** | — | — | **10/10** |

For each selected Trial, acceptance required (1) exact equality of the computed TrialResult SHA-256 with the Stage 7/Stage 10 golden stored in the audit, (2) exact matching of its audited outcome summary, (3) a day-for-day comparison of all 12 fields already present in the selected Stage 12 payload, (4) contiguous calendar dates ending on the audited final close date, and (5) integer, nonnegative memo-balance values on every replayed day. All ten Trials passed all checks.

## Data integrity and exclusions

- historical_dataset_modified=false; no canonical Stage 12 Parquet was written or replaced.
- source_artifacts_modified=false; the original audit/payload ZIP and JSON bytes were only read.
- No SOURCE_SHA, seed, RNG, scenario, Trial ID, or canonical selection was changed.
- This was ten exact single-Trial replays only. It was not a Monte Carlo expansion or Gate B checkpoint.
- No production workbook was built.
- This CP does not resolve the independent C050_G000 Stage 9A manifest/representative-inventory provenance mismatch. It also does not implement or pass the production Gate A/governance provider, the adaptive/time-uniform statistical acceptance gate, or the final seven-file release gate.

## Next bounded integration CP

The recovery artifact is now a verified candidate source for Stage 13, but its provenance is a deterministic replay bound to the canonical golden fingerprint and historical daily ledger—not one of the existing Stage 9A representative-role archives. The next CP must add a separately typed loader path for this recovery artifact, validate its run/artifact digest and per-scenario/Trial/date/fingerprint binding, and then re-run the focused synthetic checks and fixture-first full test inventory. Final acceptance must remain blocked until the separate C050_G000 provenance, Gate A authority, statistical inference, and release-gate blockers are resolved.


## R4 addendum — Stage 13 replay-loader integration and complete regression — 2026-10-24

The separately typed `stage13-maxcase-replay-recovery-v1` source path is now wired into `scripts/excel_builder.py` on the Draft PR branch. It is bound to the independently verified recovery artifact, the pinned original source-audit pair, the canonical source identity, the exact selected Trial IDs and fingerprints, all 21,575 recovered daily rows, and day-for-day equality of every common Stage 12 field. The original legacy builder signatures remain unchanged.

### Exact-head verification

- Focused integration Run [40051177942](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40051177942), exact head `bc892fcbca42d8b0658ae59ecb953dc4a4f27ea1`: **80 passed, 0 failed in 22.74s**. Evidence artifact `12543332469`, ZIP SHA-256 `f2af7dfb4784cfbc653ee97e135321c763a22a8c38a91b1106e5bdc4310eb142`.
- Fixture-first full regression Run [40051177999](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40051177999), exact head `bc892fcbca42d8b0658ae59ecb953dc4a4f27ea1`: **464 passed, 1 skipped, 0 failed in 421.43s**. The one skip is Test 158 (`ADJUDICATION`, `K_TEST`) as prescribed by the accepted inventory. Evidence artifact `12543867025`, ZIP SHA-256 `7bd534803d5209cc6bd1330ec964db46a5be21c8099af893696e1fe4d53eb19f`.
- Full-suite source identity artifact confirms:
  - `scripts/excel_builder.py` blob `648ac92cda5bd111fc429246f2e7e638053726d2`
  - `scripts/stage13_assemble.py` blob `ab660e03796fe87661a63fb338be2597ca41e567`
  - `tests/test_stage13_maxcase_audit_loader.py` blob `0b88ae41a4ab661803043d9b0bd8e8ddcf61bc84`
  - recovery contract test blob `6eb4446f5b7ad86bf3cfbd1d7ab6621cd9f4a4ba`
  - Stage 9A manifest blob still `e796fa2443493b607f1f9c60b58eb63607959c26`
  - Stage 11 dataset identity blob still `72a481d509d39820fba78732724fde4fa9f25134`.

### Scope and release boundary

This closes the **Stage 13 loader/integration CP** with code, focused, and complete regression evidence for the exact tested head. It does not change `main`, merge a PR, rewrite canonical Stage 12 data, build a production workbook, run an expansion Trial/Monte Carlo/Checkpoint, or release the project.

The recovered memo balances are now a verified Stage 13 input for the ten previously missing selected-Trial scenarios. The final-delivery status remains `NOT_FINAL_BLOCKED`: the independent C050_G000 representative-inventory provenance conflict and the project-level Golden governance / statistical-inference / release gates remain unresolved. Passing this CP must not be interpreted as Gate A, Gate B, or final delivery acceptance.
