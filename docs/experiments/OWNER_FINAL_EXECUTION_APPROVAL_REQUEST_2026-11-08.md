# Owner final execution approval request — draft — 2026-11-08

## Decision requested

A separate, explicit owner decision is required before any new Trial. This request is for **one initial evidence-generation checkpoint only**, not final acceptance, not a production declaration, and not authorization for later N expansion.

## Exact candidate identities

- Model-source SHA: `ac0d009aa004976009ed01e97f96d019945e9ad6`
- Workflow branch: `fix/explicit-cohort-identity-20261108`
- Workflow HEAD SHA: `[INSERT FINAL PR #84 HEAD SHA AFTER ALL COMMITS]`
- PR: [#84](https://github.com/yasmin977209-ux/motorcycle-simulation/pull/84)
- S6 cohort: `s6-v23-rebuild-20261105`
- C100 cohort: `c100-v23-rebuild-20261105`
- MASTER_SEED: `20270101`
- S6 checkpoint size: `N=300 per scenario`
- C100 initial Golden size: `300 per scenario`

## Exact work the owner would authorize

1. S6: 20 approved stochastic scenarios × 300 Trials = **6,000 S6 Trials**.
2. C100: 5 approved deterministic scenarios × 300 Trials = **1,500 C100 Trials**.
3. Total initial evidence-generation scope: **7,500 Trial executions**.
4. Execute sequentially with stop-on-first-failure. No resume from partial output.
5. Preserve partial outputs as diagnostic-only artifacts; no automatic commit or publication.
6. Keep the model-source SHA and workflow HEAD separately recorded in each run's provenance.
7. Upload run outputs as workflow artifacts only. No write permission to repository contents.

## Explicit exclusions

This decision does **not** authorize:
- N=600, N=1200, N=2400, N=4800, or any later N expansion;
- additional Monte Carlo runs, retries, or re-runs after a failed run;
- changing SOURCE_SHA, cohort IDs, MASTER_SEED, thresholds, accounting rules, or model/business logic;
- changing historical evidence, deleting or rewriting history, or backfilling missing accounting fields;
- merging PR #84, modifying `main`, publishing a Release, or declaring `CONVERGED`, `FINAL_ACCEPTED`, `P17_FINAL_ACCEPTED`, or `P18_RELEASED`.

Any later checkpoint or retry requires a separate owner decision.

## Known limitations the owner must acknowledge

1. The S6 aggregator still references the pinned historical C100 reuse evidence. The newly generated C100 Golden is a separate artifact and is **not** currently consumed by the S6 aggregate. This run cannot be represented as integrated new-lineage C100/S6 acceptance.
2. Gitleaks found nine unclassified `generic-api-key` matches in reachable history. No values were exposed. The security gate remains blocked until a qualified reviewer classifies them and rotates any confirmed live credentials.
3. The storage check restored one C100 archive from OneDrive and matched its bytes to Dropbox's content hash. A direct Dropbox raw restore and full-folder restore remain outstanding.
4. The environment lock contains exact package versions and wheel hashes, but the hosted `ubuntu-24.04` image is not immutable. The dependency vulnerability audit must also pass.
5. An independent reviewer has not yet been assigned or completed review of the exact model-source SHA and final workflow HEAD.

## Preconditions before this request may be approved

- [ ] Independent reviewer signs off on the exact model-source SHA and workflow HEAD.
- [ ] Nine Gitleaks findings are classified; any confirmed credentials are rotated.
- [ ] `pip-audit` completes without unresolved vulnerabilities, or the owner explicitly accepts documented exceptions.
- [ ] Protected environment `s6-simulation-execution` is configured with required reviewers and exact variables/secrets.
- [ ] Storage restore evidence is completed or the owner explicitly accepts the scoped limitation.
- [ ] PR #84 has completed review; merge approval is separately recorded. No merge is implied by this request.

## Protected environment values to set only after approval

- `S6_EXECUTION_ENVIRONMENT_LOCKED=true`
- `S6_EXECUTION_APPROVED_SOURCE_SHA=ac0d009aa004976009ed01e97f96d019945e9ad6`
- `S6_EXECUTION_APPROVED_WORKFLOW_SHA=[FINAL PR #84 HEAD SHA]`
- `S6_EXECUTION_APPROVED_COHORT_ID=s6-v23-rebuild-20261105`
- `S6_EXECUTION_APPROVED_N=300`
- `C100_EXECUTION_APPROVED_COHORT_ID=c100-v23-rebuild-20261105`
- Environment secret `S6_OWNER_EXECUTION_DECISION_ID=[EXACT DECISION ID]`

## Owner decision record

Choose exactly one:

- [ ] **APPROVE** the exact initial evidence-generation scope above, subject to all preconditions being complete.
- [ ] **REJECT** the proposed initial evidence-generation scope.
- [ ] **RETURN FOR CHANGES** and specify the required changes.

Owner decision ID: `[TO BE ASSIGNED]`

Owner identity: `[OWNER]`

Decision timestamp (UTC): `[YYYY-MM-DDTHH:MM:SSZ]`

Approved model-source SHA: `ac0d009aa004976009ed01e97f96d019945e9ad6`

Approved workflow HEAD SHA: `[FINAL PR #84 HEAD SHA]`

Reviewer sign-off reference: `[REVIEW URL / COMMIT / REPORT]`

Owner notes / exceptions: `[NONE OR EXPLICITLY LISTED]`

**No Trial may start until the owner decision is recorded, the protected environment is configured, and all required preconditions are satisfied.**
