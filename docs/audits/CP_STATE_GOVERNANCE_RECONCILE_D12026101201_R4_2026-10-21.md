# R4 — Reconcile state governance metadata for D-2026-10-12-01 — 2026-10-21

## Scope

- Base/main HEAD: `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`.
- Candidate branch: `tmp/cp-state-governance-reconcile-20261021`.
- Classification: `K_STATE / DOCUMENTED DECISION METADATA ONLY`.
- Source decision: `docs/governance/DECISIONS_LOG.md` at base blob `df4910e6a86bcce84f6b71d6d260913800474f95`, section D-2026-10-12-01, approved on 2026-10-12.
- Target file: root `state.json`, base blob `2178260bb18efeb81437486f13b6d10cf5e85936`.

## Read-only finding

The state blocker list says D-2026-10-12-01 is present in the decision log and referenced by CP-C, but it is absent from `state.governance_decisions`. The decision itself is explicit and approved; this CP copies only a concise structured index of the existing decision into state. It does not write or reinterpret the decision log.

## Exact metadata to add

- topic: Gate B P50 relative-change trigger.
- scope: each of the 20 non-C100 scenarios; C100 excluded.
- method: linear P50 of Final_Net_Project_Equity over trial IDs 1..N.
- checkpoints compared: adjacent 300→600 and 600→1200 only.
- formula: 100 * abs(P50_new - P50_previous) / abs(P50_previous).
- trigger: strictly greater than 5.0% requires PRELIMINARY_STABLE and next N=2400 for that scenario; exactly 5.0% is not a trigger.
- near-zero denominator: if abs(previous P50) < 1e-6, use absolute difference < 1 currency unit as the comparison; this is separate from Gate B CI near-zero handling.
- status: approved / normative definition only.

## Exclusions

No changes to statistical computation or executable code, checkpoint outcomes, `SOURCE_SHA`, seed/RNG, trial IDs, cohort, Parquet, artifacts, manifest, workflows/tests, other gates, delivery status, or historical reports. This candidate-only state entry does not change `state.sha`: that field is a parent-state commit pointer and must not be equated with the branch HEAD.

## Verification

- Parse updated state as JSON.
- Confirm existing governance entries and all other top-level state values remain unchanged.
- Compare candidate against base and confirm only this R4, `state.json`, and the continuity record change.
- `main` remains unchanged; no workflow, trial, checkpoint, merge, or release is run.

## Disposition

`PENDING_STATIC_READBACK`. This reconciles an approved decision's metadata index only; it is not new authority to alter Gate B policy, nor evidence that Gate A or overall delivery has passed.


## Static read-back result

- `state.json` updated on the candidate branch; prior blob `2178260bb18efeb81437486f13b6d10cf5e85936`; final blob after decision index and stale blocker removal: `32e9d039d2df628ca367b9dd8810f8e40bc80aec`.
- Valid JSON read-back confirmed the new `governance_decisions.D-2026-10-12-01` entry, the already-approved values from DECISIONS_LOG, removal of exactly the stale governance-gap blocker, and preservation of all other open blockers.
- Preserved `state.sha` parent pointer `0b083fa472d7a11089a15137cfad16d87785689a` and `stage=12-CLOSED`; neither was rewritten. No rule, statistical computation, data or artifact changed.
- Candidate diff against base before continuity note: 3 commits ahead / 0 behind; only this R4 and `state.json` changed. Main state blob remains `2178260bb18efeb81437486f13b6d10cf5e85936`; main HEAD remains `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`.
- Disposition: `PASS_STATIC_STATE_RECONCILIATION_CANDIDATE_ONLY`. The other six blockers remain open; this does not accept overall delivery.
