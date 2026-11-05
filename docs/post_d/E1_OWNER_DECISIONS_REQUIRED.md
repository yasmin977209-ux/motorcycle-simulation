# E1 — Owner Decisions Required
Date: 2026-11-05
Repository: `yasmin977209-ux/motorcycle-simulation`
Branch: `tmp/d1-rebuild-20261101`
Baseline HEAD: `3c11c11cbe71bdf6e0ca3f1499853b13a7ffde59`

## Purpose
This register separates factual/documentary reconciliation from choices that require the project owner's explicit approval. E1 does not exercise any of the approvals below.

## Decisions and approvals

| ID | Matter | Current authoritative state | Decision required only if | Options / impact | E1 disposition |
|---|---|---|---|---|---|
| OD-E1-01 | Governing reference v2.4.0 header | Owner decision `D-2026-10-30-REFERENCE-V2.4.0` is `APPROVED_BY_OWNER`; approved digest is `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b` | The owner wants the normative reference bytes/header edited, reissued, or replaced | A: preserve bytes and append a clarifying governance note (no rule change); B: authorize a separately versioned reference correction. B requires explicit scope, new digest and effective date. | Existing decision already governs. No new approval required for factual reconciliation; no reference bytes changed. |
| OD-E1-02 | D3-18 acceptance interpretation | Requirement-level `D3-18=NOT_RUN`; D3 package top-level result remains scoped | Any attempt is made to change D3-18 to PASS or claim the requirement was executed | A: keep NOT_RUN until exact requirement invocation/evidence; B: owner may define a separate acceptance route, but cannot retroactively claim an unrun test passed. | Keep NOT_RUN. No promotion requested or performed. |
| OD-E1-03 | D5/D6 provenance identities | D5 tested SHA `baf696af1e951cbf4a79e8a9e009c60c6b053b2d`; publication-evidence commit `4c6a84b10ac78b6067175d0eafa149f3f12dbc2a`; D6 tested SHA `48ae9fbf5a7264834a523504706a7c04b654061b` | A historical manifest/artifact is to be modified or replaced | Preserve and clarify field semantics in a new append-only record; changing historical Artifact/manifest requires separate owner authorization. | Record identities separately; no historical mutation. |
| OD-E1-04 | N=4800 / additional Trials / Monte Carlo | `N=4800 NOT_EXECUTED`; Gate B remains failed at N=2400 and stability not converged | Any new simulation, Trial, Monte Carlo, or N expansion is proposed | Owner must explicitly approve purpose, scope, scenario set, N, Trial identity, seed, resource/cost, stop conditions and post-run audit. | Not authorized or run. |
| OD-E1-05 | Five missing 48K accounting fields | `MISSING_EVIDENCE`: `Accounts_Receivable`, `Accumulated_Depreciation`, `Gross_Bike_Assets`, `Guarantee_Claim_Receivable`, `Total_Assets` | Backfill, reconstruction from non-original proxies, or any inference is proposed | Only original preserved source evidence may be searched/reused without changing history. Any backfill or estimate requires a separate explicit owner decision and cannot be presented as historical fact. | No backfill, inference, or zero-fill. |
| OD-E1-06 | Reference/business-rule or threshold change | v2.4.0 plus applicable approved amendments/decisions govern | A code change would alter business rules, accounting, RNG, statistical thresholds, or inference method | Owner must issue a scoped decision and identify effective reference/version, digest, affected identities and migration policy. | No such change in E1. |
| OD-E1-07 | Historical Artifact/manifest mutation, main, merge, Release | Existing artifacts and main history are preserved; no release declared | Any mutation/deletion, main write, merge, force-push, release, or final-acceptance declaration is proposed | Separate explicit owner approval required for each restricted action. | None performed. |

## K_SPEC / UNDEFINED_BUSINESS_RULE
E1 did not invent or resolve a business rule. Any ambiguity discovered in later stages must be tied to the exact reference clauses and logged as `K_SPEC / UNDEFINED_BUSINESS_RULE`, with alternatives and impact, before owner approval. No statistical alpha budget, precision threshold, accounting inference, or business-rule fallback is introduced here.

## Status
- E1 documentary reconciliation: `PASS_SCOPED`.
- New owner decisions required to finish this factual reconciliation: none identified.
- Restricted future actions remain unapproved unless separately authorized.
- E2 and later stages: `NOT_STARTED`.
