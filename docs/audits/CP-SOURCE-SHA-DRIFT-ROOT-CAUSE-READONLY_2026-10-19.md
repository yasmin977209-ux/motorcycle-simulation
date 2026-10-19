# CP-SOURCE-SHA-DRIFT-ROOT-CAUSE-READONLY — 2026-10-19

## Disposition

**Root cause isolated to a merged 11-line compatibility adapter; strict SOURCE_SHA preflight still blocks the current main tree. No pin change or bypass is authorized.**

## Live identities

- Main HEAD: `647c19826b90d8224ce73ef9b90c306a45e03fb0`
- Main `state.json` blob: `2178260bb18efeb81437486f13b6d10cf5e85936`
- State source pin: `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`
- Pinned `daily_engine.py` blob at source SHA: `6c4496c3e9a9b41668c3d93063ad31d96df5f878` (1,162 lines; 37,592 characters).
- Main `daily_engine.py` blob: `0d17d1923fbf95ba7f3e4b6ae695bfbf80f85964` (1,173 lines; 37,914 characters).
- The content diff has 11 insertions and zero deletions. A longest-common-subsequence comparison confirmed one contiguous addition and no other line changes.

## R4 — evidence versus controlling identity contract

| Item | Current evidence | Governing contract / evidence | Ruling |
|---|---|---|---|
| `SOURCE_SHA` | Main pins `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`; main engine blob differs from the blob at that commit. | `.github/workflows/stage7-full-run.yml` main blob `4bb3b8df6742f51087b45eed1b9200468f12ac60` explicitly executes `git diff --quiet "${SOURCE_SHA}" HEAD -- "${MODEL_FILES[@]}"`; on any byte difference it prints `MODEL_SOURCE_DRIFT_DETECTED` and exits nonzero. | `SOURCE_SHA_DRIFT` remains real under the current strict contract. A semantic-equivalence observation cannot override the byte-identity gate. |
| Exact difference | At main `daily_engine.py` lines 137–145 only, there are 11 added lines: Arabic comment and `_create_contract(project, bike, contract_type, current_date)` adapter returning `_new_contract(project, bike, contract_type, current_date)`. No pre-existing line was edited or removed. | GitHub commit `07cfb2ec122d6ae5bb60b81680b3b8b5b5047116`, message `CP-3B: close 7 pytest defects (adapter + 3 test fixes)`, is the only later commit touching `daily_engine.py` in the file history checked. It adds exactly this adapter (+11/−0). | Proven root cause: a compatibility API addition merged with PR #40, not a newly discovered edit to existing engine logic. This does not assert end-to-end trial output equivalence for all model inputs. |
| Merge provenance | PR #40 is closed and merged; squash/merge commit `07cfb2ec122d6ae5bb60b81680b3b8b5b5047116` on 2026-10-12. PR #41 subsequently merged state-only reconciliation at `12b4076c8bdaecedccfec2a3c466e8403789b7ee`. | PR #40 scope was CP-3B: add the missing historical private adapter and repair three old test contracts; production accounting paths were stated unchanged. | The difference is intentional and already merged, but the retained source pin still refers to pre-adapter bytes. A new identity choice requires explicit scoped owner authorization. |
| Existing test evidence | Run `38314258251`, event `push`, tested candidate SHA `3e01bf1f8a8155cff81f25f933d2d4b210336870`, conclusion `success`; log has exact result `370 passed, 1 skipped, 1 warning in 427.38s`, `EXIT_CODE=0`. Artifact `11776147957`, ZIP SHA-256 `b1418edc0128774d47810571c9fe38397aa2338d6d76609d33b9ca1519f9b363`. | At that tested SHA, the `daily_engine.py` blob is exactly `0d17d1923fbf95ba7f3e4b6ae695bfbf80f85964`, identical to current main; the test-file blob `5826e693ad118838c648696291b20bbea3f2ad0b` also matches current main. | The successful full pytest result covers the merged CP-3B source/test blobs at that tested SHA. It is test-suite evidence, not a new canonical-trial replay, not proof of all numerical results unchanged, and not a waiver of the Stage 7 strict source gate. |
| Workflow behavior | Stage 7 production workflow is still pinned to `SOURCE_SHA=f3af...` and strict byte comparison remains in place. | Main workflow blob `4bb3b8df6742f51087b45eed1b9200468f12ac60`. | Stage 7 source preflight will reject the current main model-file set until a scoped owner decision establishes the approved identity policy. No preflight was run in this CP. |

## Exact addition observed

```python
# Adapter للتوافق التاريخي فقط؛ لا يضيف منطقاً لإنشاء العقد.
def _create_contract(
    project: Project,
    bike: Bike,
    contract_type: ContractType,
    current_date: date,
) -> Contract:
    """واجهة توافق تاريخية — تُفوّض إلى _new_contract."""
    return _new_contract(project, bike, contract_type, current_date)
```

The adapter preserves the underlying `_new_contract` implementation and exposes a compatibility name consumed by `tests/test_stage3_path_integration.py`. It changes the Python module byte identity, which is sufficient to trigger the current strict comparison even though there are no edited/deleted lines in the old file.

## Status and blocked decision

- Classification: `SOURCE_SHA_DRIFT / INPUT_IDENTITY_DECISION_REQUIRED`.
- Proven cause: compatibility API addition from merged CP-3B PR #40.
- Proven test result: CP-3B Run `38314258251` passed full raw pytest at exact tested SHA `3e01bf1f8a8155cff81f25f933d2d4b210336870` and matching engine/test blobs.
- Not proven: equality of every canonical Monte Carlo output under the old and current source identities; compatibility of historical Parquet/golden datasets with a newly widened source identity; successful current Stage 7 preflight.
- No production Workflow, Monte Carlo, Trial, checkpoint or CLI was run; no source, pin, state, data, seed/RNG, test, workflow, main, PR or Release changed.

Two possible resolution classes require separate owner instruction and are intentionally not selected here: (1) keep the existing source identity and define a narrowly scoped, reviewed treatment of this compatibility-only module API difference; or (2) approve a new source identity and explicitly specify the evidence required to keep prior datasets/golden trials separate or prove valid compatibility. Neither can be inferred from the existing adapter merge alone.

**Overall project status remains `FINAL_DELIVERY_BLOCKERS_OPEN`.** The Gate A provider and other recorded blockers remain unchanged.

## Next permitted action

Request a separate, explicit owner decision defining how this merged compatibility-only addition should be represented in the Stage 7 source identity policy. Until that decision, keep strict preflight fail-closed and do not start any new Stage 7 production work.
