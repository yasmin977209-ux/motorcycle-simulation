# R4 — temporary MaxCase verifier syntax correction

Date: 2026-10-19
Status: MINIMAL WORKFLOW-ONLY CORRECTION AUTHORIZED BY THE EXISTING SCOPED M5; no data or assembler change.

| Item | Current | Governing reference / decision | Exact evidence / acceptance | Judgment |
|---|---|---|---|---|
| First verifier Run | Run `39309563068`, tested SHA `457827d61960723c526ab80a04b1e040a6e42fc9`, conclusion `failure`. | Scoped M3 + M5 authorization; R4 `R4_READONLY_STAGE12_MAXCASE_VERIFIER_20261019.md`. | Literal error: `SyntaxError: no binding for nonlocal 'current' found`, inline verifier line 256; job `118255322259`. | `K_CODE`; no artifacts were read because Python failed during parse. Preserve historical FAIL. |
| Root cause | `close_trial()` is defined inside a top-level `for` loop in the inline script, not inside an enclosing function. | Python scoping semantics; workflow source blob `ef417dc2dede53924a62d6769564c3bfb432289e`. | `nonlocal` requires a binding in an enclosing function scope; these state variables are module-level names. | Confirmed syntax defect; not an artifact/data discrepancy. |
| Minimal fix | Replace the single `nonlocal current,first_day,last_day,day_count,current_hash,closed_trials,selected_daily` declaration with `global current,first_day,last_day,day_count,current_hash,closed_trials,selected_daily`. | Same inline verifier, same temporary workflow path and pinned branch. | Acceptance: Python parses and executes the read-only verifier; no engine, Trial, Monte Carlo, source, seed, data, Parquet, golden, or assembler change; exact outputs and hashes captured. | Minimal `K_CODE` correction within authorized workflow scope. |
| Scope and permissions | One temporary workflow on `tmp/cp-maxcase-ledger-verify-20261019`, `contents: read`, `actions: read`. | Explicit M3 + scoped M5 authorization. | No additional workflow, no workflow_dispatch, no write permission, no Gate A production run. | In scope. |
| Assembler | Unchanged at blob `71e05034bafb551aea2949adc94013e8bb23d239`. | Prior R4 and user's scope limits. | No assembler edit until row-level proof succeeds and follow-up R4 is recorded. | HOLD. |
