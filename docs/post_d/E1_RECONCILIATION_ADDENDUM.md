# E1 Reconciliation Addendum — 2026-11-05
Append-only clarification to `E1_GOVERNANCE_RECONCILIATION.md`.

## C13 — D3 manifest versus final acceptance record
- `deliverables/D3_MANIFEST.json` on the E1 baseline records `d3_gate_status=BLOCKED_MISSING_EVIDENCE` and `D3-18=NOT_RUN`.
- `docs/stage_d/D3_ARTIFACT_FINAL_ACCEPTANCE_2026-11-05.md` describes D3-18 as `PASS_SCOPED` for the owner-authorized Artifact 13288779998 and independent package/workbook verification.
- `docs/stage_d/D3_ARTIFACT_FINAL_ACCEPTANCE_2026-11-05.json` contains top-level `d3_18=PASS_SCOPED` while its `d3_requirement_statuses.D3-18` remains `NOT_RUN`.
- Classification: `CONFLICTED` — artifact-level scoped acceptance and requirement-level test invocation are not aligned across records.
- E1 disposition: preserve the historical manifest and all original status fields; do not infer that the historical D3-18 test was invoked. Keep requirement-level `NOT_RUN` visible alongside the scoped Artifact acceptance. No historical manifest or Artifact is edited.

## C14 — D5 publication commit field
- `docs/stage_d/D5_PACKAGE_PREFLIGHT_2026-11-05.json` records `tested_sha=baf696af1e951cbf4a79e8a9e009c60c6b053b2d` and `publication_commit_sha` with that same value.
- The D5 workflow's corrective evidence text states that the publication-evidence commit is `4c6a84b10ac78b6067175d0eafa149f3f12dbc2a`; the value `baf696...` identifies the triggering/tested SHA, not the documentation commit.
- Classification: `CONFLICTED` — field semantics in the historical preflight JSON are inaccurate/ambiguous.
- E1 disposition: keep the preflight JSON unchanged; use separate names `tested_sha` and `publication_evidence_commit_sha` in subsequent records.

## C15 — D3/D4 build identifiers (scope correction)
The initial E1 matrix item C12 was a precautionary role-separation note, not a proven value conflict. The inspected D3/D4 records use different identifiers for source run, acceptance run, build/test SHA, and publication commit. No additional direct contradiction is asserted by this addendum. Classification is reduced to `REVIEW_NOTE`; future records must label identifier roles explicitly.

## Scope and limits
This addendum does not alter governing rules, acceptance requirements, artifacts, manifests, source/cohort/seed/Trial identities, or any prior E1 record. It does not authorize E2, new Trials, Simulation, Monte Carlo, N expansion, backfill, zero-fill, or Release.
