# CP — Stage 13 strict Trial-ID type correction — 2026-10-19

## R4 linkage and change boundary
The pre-change R4 was recorded and read back before editing: `docs/audits/R4-STAGE13-STRICT-TRIAL-ID-TYPE-2026-10-19.md`, commit `7e567c6baad21ba6e2ec5ea1cb106bf75559e115`, blob `e75f2daa1721160f9d608e0160931c85bd0c7d40`.

- Candidate branch: `tmp/cp-stage13-excel-compat-20261017`
- Before: HEAD `52a7c3b9a4151ab26968b55287e518c590426ba6`; assembler blob `8bb785606bc268cd1ad8671518bfa96e3d009794`.
- After: HEAD `250b855c9ad97875c92e3dc682e6e2f7b2071a2a`; assembler blob `71e05034bafb551aea2949adc94013e8bb23d239`.
- Main remains `7c41ac64c4b599f4e1d6a50be055f82cdd87a7b5`; `scripts/stage13_assemble.py` remains absent from main.
- Exact compare of before/after candidate heads reports only `scripts/stage13_assemble.py` changed. Test blob remains `976ebc8365db7f2380f15317c677990e34a1269c`; no test or Workflow file changed.

## Code correction
The validator now requires `type(summary.get("trial_id")) is int` and `type(daily_row.get("trial_id")) is int` before comparing either value with the selected expected ID. This closes Python equality coercion where `True == 1` and `1.0 == 1`. Existing stable mismatch errors are retained. A separate isolated predicate check accepted integer 1 and rejected bool True, float 1.0, string "1", integer 2, and None.

## Verification limits
GitHub Actions query for exact new head `250b855c9ad97875c92e3dc682e6e2f7b2071a2a` returned zero runs. This CP performed source read-back and exact before/after file-scope verification only; no repository pytest, AST/compile check, Workflow, CLI, workbook, Monte Carlo, Trial, or Checkpoint ran. Therefore the code change is `STATIC_READBACK_VERIFIED / RUNTIME_VALIDATION_PENDING`, not PASS.

The change does not resolve the separate Stage 13 input blockers: the C050_G000 manifest/artifact digest mismatch and the missing MaxCase role in the published four-role package contract. No source/data/Parquet, manifest, trial ID assignment, seed/RNG, sampling, cohort, reference, state, main, Release, or historical artifact was changed. Candidate is not merged and PR #46 remains draft/unmerged.
