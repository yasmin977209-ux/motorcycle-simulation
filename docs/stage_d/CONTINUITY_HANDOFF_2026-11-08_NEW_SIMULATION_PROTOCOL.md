# Continuity Handoff — New Simulation Protocol — 2026-11-08

## Resume point
- Repository: `yasmin977209-ux/motorcycle-simulation`
- Documentation branch: `docs/new-simulation-protocol-20261108`
- Branch base: `tmp/d1-rebuild-20261101` at `f2ffb9743c8b9aff9fd9d4cadcdb5484e6069866`
- Protocol commit at handoff preparation: `48f29a32183a0a5fe3e1496215f7a099f75ada22`
- Protected `main` baseline: `1d67cd56d326a9c42f7ecf324fa284dcc129acd4`; read-only.
- Protocol file: `docs/experiments/NEW_SIMULATION_EXPERIMENT_PROTOCOL_2026-11-08.md`
- Session status: `docs/stage_d/SESSION_STATUS_2026-11-08_NEW_SIMULATION_PROTOCOL.md`

## Current disposition
`PREPARATION_ONLY — NOT_AUTHORIZED_FOR_EXECUTION`.

No Trial, Simulation, Monte Carlo, Golden revalidation, N expansion, or D0'–D6' execution has been dispatched by this work. No workflow was run. No historical evidence, manifest, source identity, main branch, or Release was modified.

## Key boundaries
1. D0 historical remains `BLOCKED / MISSING_EVIDENCE`; the new lineage cannot repair or rewrite old D0 evidence.
2. E2 rebuild preparation is not final execution authorization. The decision document says `WAIT_FINAL_OWNER_CONFIRMATION`.
3. S6 proposed scope: 20 scenarios × 2,400 Trial IDs = 48,000; new cohort `s6-v23-rebuild-20261105`; seed `20270101`.
4. C100 proposed scope: five deterministic paths × 300 repetitions; new cohort `c100-v23-rebuild-20261105`; the comparison contract requires explicit owner confirmation.
5. Candidate source pin `002b748...` must be distinguished from Workflow HEAD and verified as the intended Model SOURCE_SHA before use.
6. The exact approved v2.4.0 bytes must be recovered and SHA-256 verified; the repository copy inspected in this session has a conflicting proposed-status header.
7. The E2 old-identity replay Run `41958935113` is not evidence of execution of the new S6/C100 lineage.

## Resume sequence
- Re-read live branch and main refs, PRs, relevant E2 decision, governing reference decision, workflows, Actions and Releases.
- Complete PF-01..PF-11 in the protocol; document unresolved gates without guessing.
- Obtain independent preflight review.
- Present the exact verified identity, workload, comparison contract, resource estimate, and stop rules to the owner.
- Wait for explicit final confirmation matching protocol section 14.
- Only after confirmation may the separately authorized execution workflow be considered.

## Stop conditions
Do not dispatch any Trial/Simulation/Monte Carlo before final owner confirmation. Do not modify main, merge PRs, publish Releases, change business rules/thresholds/identities, mutate historical artifacts/manifests, backfill or zero-fill missing historical accounting fields, or claim final acceptance.


## Final remote readback correction — 2026-11-08
- Final branch HEAD is `880c2f6f04967dc7b95f86f2ba7aaabe3af9c31b` (the protocol's original file-creation commit is `48f29a32183a0a5fe3e1496215f7a099f75ada22`).
- Draft PR #83 is open and unmerged: https://github.com/yasmin977209-ux/motorcycle-simulation/pull/83. Base remains the working branch, not `main`.
- Diff is 4 files / 385 additions / 0 deletions. Main remains `1d67cd56d326a9c42f7ecf324fa284dcc129acd4`.
- No Actions run was associated with the final head; no workflow dispatch occurred.
- Git blob SHA readback is recorded in the session status. Raw-byte SHA-256 was not calculated; do not claim `VERIFIED_LIVE`.
- This is a documentation-only proposal. Do not dispatch execution without final owner confirmation after PF-01..PF-11.
