# R4 — Gate B N=1200: cumulative historical inputs and new trial range

Date: 2026-10-12
Repository: `yasmin977209-ux/motorcycle-simulation`
Main HEAD before change: `2325b6ae6e110d9e54e614aa9b1e255be5965375`
Normative source: uploaded `المرجع_النهائي_الموحد_المعتمد.md`, SHA-256 `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`.

## R4 three-way comparison

| Item | Current main | `stage3b-preserved` (diagnostic only) | Reference / approved decision / live evidence | Judgment |
|---|---|---|---|---|
| CP/state | Main merge `2325b6ae6e110d9e54e614aa9b1e255be5965375` records N=600 as PASS_AT_N600_ONLY and next N=1200. | State points to Stage 9 and package SHA `c7429d1a31037e98201a05ed98b62c9c68118b2fda89064804d2d2cea2dfed79`; not canonical Stage 12. Nothing is copied. | Reference is the business-rule source; D-2026-10-10-01 defines doubling; D-2026-10-11-02 allows IDs 1..550 as Gate B analytic inputs only. | MATCH: N=1200 is the authorized next checkpoint; Gate B not yet complete. |
| Source identity | Source SHA `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`, code commit `0156c5f4272eb0ca7e32442657d0df9eaf4973d3`, seed `20270101`, Stage 12 Run `37964656154`. | Distinct diagnostic identity, not joinable. | Reference §§14.3–14.4 govern deterministic RNG/trial identity. | MATCH only if exact run/source/seed/scenario/trial identities and row hashes are validated. |
| IDs 1..550 | PR #33 merged N=600 input-audit tool at `d81e09b7746485bd99dee9122c55403cbc38bf3`. | No use. | Run `38174743440`, head `61ae9e2354ff37b1d4d9d13849bd6b264cf9cfa3`, passed 43/43 jobs. Historical aggregate artifact `11715099731`, digest `sha256:df47991b1e94f39c9064497df82989d60d86e88c5627405f03d428d9d9ea0ee0`, contains 20 scenarios / 11,000 rows and ordered hash map `a796c13a0e596916785e5c7af792550de28b13e4abb9a2ef2fc9255977c206b3`. | MATCH: use the exact artifact read-only; revalidate archive digest, unique IDs, metrics, trial hashes and provenance. Do not rerun. |
| IDs 551..600 | N=600 final report artifact `11715388165`, digest `sha256:67d5033a67eec27bd7a90b735c56f7f7ceff4181e32c88271dd07f39f3b8e8ae`. | No use. | N=600 Run `38174743440` has a `gateb-n600-new-<scenario>-attempt-1` artifact for each of the 20 non-C100 scenarios; each records IDs 551..600, source commit/SHA, seed, run/attempt and result hashes. N=600 ordered map SHA `dd537fe96c5a8736201441e9a620db148a0d16cadae518d2a777fbc723db395f`. | MATCH only after verifying all 20 artifacts and recomputing the N=600 cumulative map to exactly that hash. Do not rerun. |
| New IDs at N=1200 | State next is N=1200; no such result exists yet. | No authority. | N=600 to N=1200 requires only trial IDs 601..1200 per each of the 20 non-C100 scenarios: 600 per scenario / 12,000 new results. | MATCH: block new jobs until all cumulative 1..600 inputs pass identity/hash/coverage checks. |
| Statistical rule | N=600 record reports 60/60 pass at that checkpoint only. | No authority. | D-2026-10-10-01 requires Student-t 95% CI half-width < 1% of abs(mean) for three named metrics, epsilon 1, and three consecutive successful checkpoints. For abs(mean) <= 1, existing audit records UNDEFINED_BUSINESS_RULE. | MATCH: report all 60 CI points; do not infer final Gate B from N=1200 alone. |
| P50 >5% condition | Main state retains this blocker. | No authority. | D-2026-10-10-01 does not specify exact P50 percentage-change formula/denominator. | UNDEFINED_BUSINESS_RULE: report P50 values but do not invent a formula. Complete N=1200; do not stop early on this basis. |
| Branch/workflow | New branch `tmp/gateb-historical-1200-verify-20261012`; current main pinned at `2325b6ae6e110d9e54e614aa9b1e255be5965375`; existing N=600 workflow pins its own exact branch. | No workflows copied. | Project rules: exact branch pin, no wildcard, no workflow_dispatch or hidden self-dispatch, timeout-minutes inside each job. Historical Stage 7 50-trial blocks measured 24.99–26.97 seconds for one scenario; N=1200 timings must be read from actual run. | MATCH with new branch pin, preflight, separate artifact provenance, and job timeout below 35 minutes. |

## Required gates before and during N=1200

1. Confirm main is still `2325b6ae6e110d9e54e614aa9b1e255be5965375`; verify N=600 Run identity/conclusion and digests for historical aggregate and N=600 report.
2. Revalidate the 11,000 archived historical TrialResult rows (IDs 1..550) and all 20 N=600 trial artifacts (IDs 551..600); recompute the N=600 hash-map SHA and require exact `dd537fe...` equality.
3. Only after cumulative IDs 1..600 pass, run missing IDs 601..1200 per scenario using the exact source commit, source SHA, seed 20270101 and event logging disabled. Preserve run/attempt and per-result hash; restore valid completed outputs before any retry.
4. Aggregate IDs 1..1200 per each scenario, require 24,000 unique scenario/trial keys, verify 60 metric CI points and hash/provenance integrity. A statistical CI failure completes the checkpoint and requires the next doubling point; it is not a workflow identity PASS.
5. Gate A and Stage 9C/CP-D remain separate. This R4 itself changes no engine, test, workflow, state, historical dataset, or trial.
