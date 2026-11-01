# D2 Requirements Matrix — Number Registry
Date: 2026-11-01
Repository: yasmin977209-ux/motorcycle-simulation
Branch: tmp/d1-rebuild-20261101
Governing decision: D-2026-10-30-REFERENCE-V2.4.0 (APPROVED_BY_OWNER)

| ID | Requirement | Implementation / evidence | Disposition |
|---|---|---|---|
| D2-01 | Build deterministic registry from pinned Aggregate, Full Logging and C100 artifacts | scripts/s6_number_registry.py; pinned artifact verification in stage-d2-number-registry.yml | PASS_SCOPED |
| D2-02 | Verify artifact ZIP size, SHA-256, CRC and member integrity before parsing | verify_zip / verify_member; workflow pin checks | PASS_SCOPED |
| D2-03 | Preserve S6 and C100 identities and do not pool cohorts | Registry scope metadata; C100 marked CROSS_COHORT_DETERMINISTIC_REUSE | PASS_SCOPED |
| D2-04 | Stable unique number_id for explicit numeric entries | stable_id; duplicate-ID validation | PASS_SCOPED |
| D2-05 | Address every Daily Distribution point deterministically | D2D-{series_sha20}-{zero_based_date_offset_6_digits}; full 2,086,550-point resolution validation | PASS_SCOPED |
| D2-06 | Preserve exact numerator/denominator, reduced fractions and deterministic display rounding | Fraction / Decimal / ROUND_HALF_EVEN; per-entry and per-point validation | PASS_SCOPED |
| D2-07 | Prohibit float in serialized registry | no_floats recursive validation | PASS_SCOPED |
| D2-08 | Preserve source provenance and locators | source artifact/run/member, hashes, path, source commit, cohort and gate/evidence fields | PASS_SCOPED_WITH_LIMITATIONS |
| D2-09 | Preserve unavailable evidence without inference or zero-fill | Five accounting fields and source_run_metadata.sha256 remain MISSING_EVIDENCE | PASS_SCOPED |
| D2-10 | Unit tests cover exact arithmetic, IDs, resolver modes, invalid IDs and provenance | tests/test_s6_number_registry.py plus builder tests | PASS_SCOPED |
| D2-11 | Produce audit Markdown and canonical JSON while retaining the old local report | docs/stage_d/D2_NUMBER_REGISTRY_AUDIT.md and .json; old report nested under historical_local_report | PASS_SCOPED |
| D2-12 | Exact final HEAD and GitHub Raw byte readback for every D2 deliverable | Stage D2 workflow final validation step; run log emits URL/path, bytes, SHA-256, blob SHA-1 and commit | PASS_SCOPED |
| D2-13 | Append session, handoff and project continuity without rewriting history | docs/PROJECT_CONTINUITY.md and Stage D status/handoff | PASS_SCOPED |
| D2-14 | Preserve all governance limits; no Trials, Simulation, Monte Carlo, N expansion, backfill or zero-fill | Workflow contains pinned-source build only; explicit audit limitations | PASS_SCOPED |
| D2-15 | Preserve the original local-only audit report without recursive wrapping | original_historical_report helper, regression test and canonical audit reconciliation | PASS_SCOPED |
| D2-16 | Verify the current governing v2.4.0 Raw bytes against the owner-approved SHA-256 and confirm the owner decision on the same tested commit | Dedicated completion-workflow gate; exact Raw readback includes the governing reference and owner decision | PASS_SCOPED (pending successful revalidation run) |

## Scope boundary
D2 is a Number Registry phase, not project final acceptance. Full Logging covers 105 representative keys only. C100 Golden revalidation remains NOT_RUN. Financial Gate A remains PASS_SCOPED; production Gate A remains NOT_DECLARED; Gate B at N=2400 remains FAIL_SCOPED (10/10); Stability remains NOT_CONVERGED (0/60); N=4800 remains NOT_EXECUTED. The five historical accounting fields remain MISSING_EVIDENCE. No new Trial, Simulation, Monte Carlo, N expansion, historical backfill or zero-fill is authorized by this phase.


## Completion workflow record

- Workflow Run: 41332273796
- Triggering source SHA: 2407a8e832aa8fa01ed8951ce8f89cc8548a8dea
- Registry-containing commit: 024c71a909328cec379f3628df25981310c64fe7
- First exact-head gate passed before this documentation finalization. The final post-finalization exact HEAD and all Raw byte triples are established by the last validation step and the SUCCESS conclusion of this same workflow Run.


## Completion workflow record

- Workflow Run: 41333300530
- Triggering source SHA: a830827c4977ba9b9121903225da5c42f8ca0959
- Registry-containing commit: 50673bf094c38e8a73de2980df719df2963a3dc6
- First exact-head gate passed before this documentation finalization. The final post-finalization exact HEAD and all Raw byte triples are established by the last validation step and the SUCCESS conclusion of this same workflow Run.


## Final D2 completion proof — 2026-11-01 (append-only)

- D2 completion workflow [41333300530](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41333300530): SUCCESS. Exact final branch HEAD: `789b9017986cb240d9a82428227f6a03adee6f3c`.
- D1-D2 source/integration validation [41333300571](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41333300571): SUCCESS, 34 passed, 0 failed, 0 skipped on triggering SHA `a830827c4977ba9b9121903225da5c42f8ca0959`.
- D2 focused + artifact-backed tests in the completion run: 34 passed, 0 failed, 0 skipped.
- Full Daily resolver validation: 2,086,550 of 2,086,550 points resolved and matched exact numerator/denominator, series, date and deterministic ID; 1,000 series; 2,640 explicit entries.
- Registry-containing commit: `50673bf094c38e8a73de2980df719df2963a3dc6`. Registry: 24,137,036 bytes; SHA-256 `47e72ecae6f8c9f8cff3c8599909c42bf5e8a4ddaa3d3bceb0be764717b7b321`; Git blob SHA-1 `ba7ead51a67b244ebfcb87d35be59dbaf62fccfc`.
- Artifact [13093114758](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41333300530/artifacts/13093114758): 3,613,833 bytes; ZIP SHA-256 `6460a72442b6c51c754f47956914f8ef7302ba3fb710dc9610b6075d94424127`; downloaded and CRC-tested successfully; 10 files including registry, audit, matrix, ledger, final handoff, source, tests and workflow.
- The original historical local-only audit is now directly preserved at `historical_local_report.original_report`: 13,954 entries, `REPORTED_ONLY_LOCAL_ONLY`; no recursive nesting.
- Superseded Run 41333271314 passed its tests but failed its exact-head assertion because the branch advanced while it ran. The later exact-head source validation Run 41333300571 passed on the stable trigger SHA; the final D2 completion Run independently passed exact-head/raw readback on the resulting final commit.
- `main` remains `c6e54349a5e94f65d5aa9f83141f225d777bb474`. D2 disposition remains `PASS_SCOPED_WITH_LIMITATIONS`; D3 is NOT_STARTED.

### Final exact-head Raw evidence triples

The following 13 files were fetched from GitHub Raw at the exact final HEAD; their returned text matched the GitHub file read, and SHA-256, Git blob SHA-1 and byte size were logged by the successful completion workflow:

| Path | Bytes | SHA-256 | Git blob SHA-1 | Commit |
|---|---:|---|---|---|
| `results/number_registry.json` | 24137036 | `47e72ecae6f8c9f8cff3c8599909c42bf5e8a4ddaa3d3bceb0be764717b7b321` | `ba7ead51a67b244ebfcb87d35be59dbaf62fccfc` | `789b9017986cb240d9a82428227f6a03adee6f3c` |
| `docs/stage_d/D2_NUMBER_REGISTRY_AUDIT.json` | 5600 | `22b7378b9e3dd94b963df22fcd9cf0233ef9eed2f47f446c6387deae3ad96526` | `67117a987887589fe6e120653e200b2e1610eaf4` | `789b9017986cb240d9a82428227f6a03adee6f3c` |
| `docs/stage_d/D2_NUMBER_REGISTRY_AUDIT.md` | 10680 | `656a0f928548350b5016501fba89633c0f5f374e8e7f9ed9b89054dd4cd7dc24` | `5cc256aa4e3835f4745da3e64b0560755a48fe22` | `789b9017986cb240d9a82428227f6a03adee6f3c` |
| `docs/stage_d/D2_NUMBER_REGISTRY_AUDIT_LIVE_2026-11-01.json` | 4247 | `6e53fa8cf311d8b3f70baf15ab11d85fa1352c3655b929e2893b68180da07f1c` | `a369c90a12894e2665ad0ede6b40e16041fe101e` | `789b9017986cb240d9a82428227f6a03adee6f3c` |
| `docs/stage_d/D2_REQUIREMENTS_MATRIX_2026-11-01.md` | 4429 | `8c41683fc770c0daceaf7d8908a334b0f0d5044a4961be9cb678639c8d4b854c` | `18165a0af650d769fa41fbb99777bd52d5113894` | `789b9017986cb240d9a82428227f6a03adee6f3c` |
| `docs/stage_d/D2_REMOTE_EVIDENCE_LEDGER_2026-11-01.md` | 3667 | `0dd6ce6c738157c7f307d1ed60fe748d4f8664bd7f43f04aa100b47140d221a7` | `9af5bd2df97acf62adcec717e76de145750a64d4` | `789b9017986cb240d9a82428227f6a03adee6f3c` |
| `docs/stage_d/D2_FINAL_HANDOFF_ADDENDUM_2026-11-01.md` | 4147 | `00fed131d19512fd632622a6410dad872616b565550a2dfb08e8214eb2471187` | `e5ffbd15916f0a01fa725b9f635290416d69b40f` | `789b9017986cb240d9a82428227f6a03adee6f3c` |
| `scripts/s6_number_registry.py` | 41080 | `6eac6ecdcf8e2bf169f81549284613982aeb6d2539b71feb16477eccf09bc3a3` | `af0f8585940ae9208b43e7181e5562f1912816d2` | `789b9017986cb240d9a82428227f6a03adee6f3c` |
| `tests/test_s6_number_registry.py` | 7254 | `70be1accbf90516a1ba7045549b0144899fac22d757db4502549e89b15af7163` | `2fe03aa5f701fb844e5ea0cd9fa3e88321b9729e` | `789b9017986cb240d9a82428227f6a03adee6f3c` |
| `.github/workflows/stage-d2-number-registry.yml` | 22077 | `9608c01704519756dda4eb529457c15c8bb5e3d7637f7151327137c887d2dcd0` | `8dd7f71613bacc014fb12fc198e37197dc8349d1` | `789b9017986cb240d9a82428227f6a03adee6f3c` |
| `docs/PROJECT_CONTINUITY.md` | 470193 | `78587cacf540384c3eaf1e3445af0132c229b501c5d834810b9b21d80d9e5d5c` | `c0e7f6671670779442010556505ab6a791210e32` | `789b9017986cb240d9a82428227f6a03adee6f3c` |
| `docs/stage_d/STAGE_D_SESSION_STATUS_2026-11-01.md` | 24104 | `a675793335bb3bd833f58a0549fd5f76c0ef747b690d6086057bfcdce3ec592e` | `04637bd59a591cf74a7d71a76e2c1defbec25c3e` | `789b9017986cb240d9a82428227f6a03adee6f3c` |
| `docs/stage_d/STAGE_D_CONTINUITY_HANDOFF_2026-11-01.md` | 11528 | `44eba10c65c6ac4476a8f87ddde9aebe373d71e9d370548456bfad0e0bf7b6ce` | `69d04763de30685303a970220b96e04bce1e8ba5` | `789b9017986cb240d9a82428227f6a03adee6f3c` |



## Completion workflow record

- Workflow Run: 41334194323
- Triggering source SHA: 12d1d861cf9eb5022fb916f2b7d9a0b702badf1f
- Registry-containing commit: d33261154018e2710bd797dec5e5bb6b9981a5da
- First exact-head gate passed before this documentation finalization. The final post-finalization exact HEAD and all Raw byte triples are established by the last validation step and the SUCCESS conclusion of this same workflow Run.


## Completion workflow record

- Workflow Run: 41334997604
- Triggering source SHA: 8eb5da55fc9036f25e420dbd43ed925567ef7c2b
- Registry-containing commit: f339bd063e2912b2d9b5afaec7d4ce9e24a6cbc6
- First exact-head gate passed before this documentation finalization. The final post-finalization exact HEAD and all Raw byte triples are established by the last validation step and the SUCCESS conclusion of this same workflow Run.
