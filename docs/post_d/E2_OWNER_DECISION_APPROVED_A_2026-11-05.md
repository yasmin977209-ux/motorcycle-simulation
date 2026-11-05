# E2 Owner Decision — Approved Rebuild Scope A — 2026-11-05

## Decision

- Decision: `OWNER_APPROVES_DETERMINISTIC_ACCOUNTING_REBUILD`
- Selected option: `A`
- Decision scope: approve preparation of a new, separately identified accounting-complete S6 + C100 data lineage.
- Execution authorization state: `WAIT_FINAL_OWNER_CONFIRMATION`
- Trial / Monte Carlo execution in this Preflight: `NOT_RUN`

This decision records the owner's stated rebuild direction. It does **not** waive the separately required final confirmation before any Trial, Simulation, Monte Carlo, or Golden revalidation is dispatched.

## Source identity

- Old S6 `SOURCE_SHA`: `da1a9ea9b5cd789c944de3f07b08395bb67c49e7`
- New source pin candidate: `002b74893ca9dfea864e83fecc558f2388748ffe`
- New source pin commit: https://github.com/yasmin977209-ux/motorcycle-simulation/commit/002b74893ca9dfea864e83fecc558f2388748ffe
- Repair reference commit: `a5573eb1891ed2c56b01f6c9b3ccfe9619a08358`
- New S6 `cohort_id`: `s6-v23-rebuild-20261105`
- Proposed separate C100 `cohort_id`: `c100-v23-rebuild-20261105` (must remain separate from S6)
- `MASTER_SEED`: `20270101` (unchanged)

The selected source pin is commit `002b748...`, not the shorter repair-reference commit `a5573eb`, because the current branch's model-source tree is present at `002b748...` and the subsequent branch commits through reviewed HEAD `7b6d5b66bc32d9e28b3a3acf398dfcf522787889` change documentation only. The repair-reference commit `a5573eb...` is retained as the forensic anchor for the repaired daily snapshot implementation.

## Code comparison — old S6 source vs repaired source

### `monte_carlo.py::_daily_snapshot`

The old implementation emitted a reduced daily row. The repaired implementation calls the existing `accounting.balance_sheet_snapshot(project)`, adds `daily_balance_schema_version = s6-daily-balance-v1`, and persists the complete balance projection, including:

- `Accounts_Receivable`
- `Guarantee_Claim_Receivable`
- `Gross_Bike_Assets`
- `Accumulated_Depreciation`
- `Total_Assets`

It also persists `Net_Bike_Assets`, `Total_Equity`, `Liabilities`, and `Balance_Difference`. This is a daily-output schema/persistence change; it does not itself prove that every simulated daily row balances.

### Other observed source differences

- `accounting.py`, `daily_engine.py`, `rng.py`, `entities.py`, `state_machine.py`, `dateutils.py`, and the other inspected core engine modules retain identical Git blob identities between the old source and repair-reference commit.
- `constants.py` changes the `TIME_UNIFORM_METHOD_ID` label from `V2.3_APPENDIX_E_ALPHA_SPENDING_V1` to `V2.3_14_11_4_ALPHA_SPENDING_V1`; the observed change is a method-identifier string/comment, not a financial arithmetic or RNG implementation change.
- The selected current source pin also contains the later `_run_single_trial_with_project` wrapper and `run_single_trial_full_logging` interface. Summary execution uses `log_events=False`; full logging uses `log_events=True`. This controls event-log capture. It does not change the `TrialResult` financial fields or the financial fingerprint field selection.
- `trial_fingerprint` remains based on the same financial outcome fields. The daily snapshot expansion does not enter that fingerprint payload.

### RNG and accounting interpretation

- `rng.py` has the same Git blob SHA at the old source and repair-reference commit; no RNG algorithm or draw-generation change was observed.
- `MASTER_SEED=20270101` remains fixed.
- The new `SOURCE_SHA` is included in RNG audit provenance, so the source-bound RNG audit fingerprint is expected to differ even if the underlying RNG draws and financial `trial_fingerprint` values remain identical. These two fingerprint types must not be conflated.
- The existing accounting projection calculates `Total_Assets` from cash, receivables, guarantee receivable, and net bike assets; `Total_Equity` from capital plus retained earnings; and reports `Liabilities=0`. A nonzero `Balance_Difference` must fail closed; no balancing plug, inferred value, or zero-fill is allowed.
- The repaired daily-snapshot unit test checks a newly initialized project only. It is not evidence of full-run daily balance across the proposed 48,000 S6 Trials.

## Approved scope to prepare — execution remains gated

### S6

- 20 stochastic scenarios.
- Trial IDs 1..2400 per scenario.
- 48,000 total S6 Trial identities under the new `SOURCE_SHA` and new S6 cohort.
- Preserve `MASTER_SEED=20270101`.
- Compare every new S6 financial `trial_fingerprint` one-to-one with its old same-scenario/same-Trial-ID counterpart.
- Required result: 48,000/48,000 exact matches. Any single mismatch stops the entire rebuild immediately and is reported to the owner; no D0' stage may consume a mismatched dataset.

### C100 — separate deterministic lineage

- Five deterministic C100 scenario paths: `C100_G100`, `C100_G070`, `C100_G050`, `C100_G030`, `C100_G000`.
- Proposed 300 executions per path (1,500 execution records total), under a separate C100 cohort.
- The governing reference defines C100 as deterministic with `N_unique_paths=1`; 300 repetitions of one path are not 300 independent stochastic samples.
- The available historical C100 evidence is a five-path Golden, not an established one-to-one historical set of 1,500 distinct fingerprints. Before execution, the owner must confirm that each of the 300 repeated records per path is to be compared to that path's single approved Golden fingerprint, rather than claiming 1,500 independent historical matches.
- Do not merge C100 records into the S6 cohort, S6 stochastic sample count, or S6 stability/FWER calculations.

## Immutable preservation constraints

1. Preserve the historical D0–D6 Artifacts exactly as-is, including IDs `13160434943`, `13288779998`, `13264003231`, and `13371094066`. No overwrite, replacement, relabel, deletion, or manifest mutation.
2. Create a fully separate D0'–D6' lineage and new artifacts/manifests. Never represent new outputs as historical D0–D6 artifacts.
3. Keep old S6 `SOURCE_SHA` and old cohort immutable; new source and cohorts are distinct.
4. Keep `MASTER_SEED=20270101`.
5. No business-logic, accounting-rule, timing, RNG, scenario, threshold, or reference changes are included in this authorization.
6. Any S6 financial fingerprint mismatch is an immediate stop.
7. Preserve the original historical five-field status as `MISSING_EVIDENCE`; only the new lineage may be described as complete after exact artifact-level validation.
8. No modification to `main`, no merge, no force-push, no Release, no final acceptance declaration.
9. Do not mix S6, C100, or Stage 12/13 identities or artifacts.

## Cost estimate

Planning estimate: approximately **24 hours** for the rebuild workload, before any schedule allowance for retries, artifact transfer, independent audits, Golden checks, and D0'–D6' production. This is a planning estimate, not a measured runtime guarantee. C100's 1,500 deterministic repetitions and downstream validation may add overhead.

## Preflight risks / unresolved gates

- The new S6 source pin is technically grounded in the current branch model-source tree, but its use as the execution identity must be frozen in the final run manifest and checked against the exact execution commit.
- The five new daily balance fields must be verified in every persisted daily row, with complete date/Trial coverage, no nulls, and `Total_Assets == Total_Equity` / `Balance_Difference == 0`.
- Financial fingerprint equivalence is a hypothesis supported by the code diff, not yet an execution result. It remains unproven until the owner-authorized runs complete and the full fingerprint maps are compared.
- C100's deterministic nature makes 300 repeats per path non-independent; do not present them as 1,500 independent observations.
- The prior E2 replay Run `41958935113` was already active under the earlier, narrower authorization and uses the old S6 identity/source. It is not part of this new S6+C100 lineage. Its current execution must be tracked and reported separately; this Preflight did not start or cancel it.
- Production Gate A, Gate B, Stability, and final acceptance remain unchanged until separately audited evidence supports any scoped reassessment.

## Final execution gate

`FINAL_OWNER_CONFIRMATION_REQUIRED_BEFORE_ANY_TRIAL`

No S6 Trial, C100 Trial, Simulation, Monte Carlo, N expansion, Golden revalidation, or D0'–D6' build is authorized by this document alone. Dispatch only after the owner gives a separate final confirmation that explicitly accepts:
- new source pin `002b74893ca9dfea864e83fecc558f2388748ffe`;
- S6 cohort `s6-v23-rebuild-20261105`;
- separate C100 cohort `c100-v23-rebuild-20261105`;
- C100's deterministic 300-repeat comparison contract;
- approximately 24-hour workload and fail-fast fingerprint stop rule.
