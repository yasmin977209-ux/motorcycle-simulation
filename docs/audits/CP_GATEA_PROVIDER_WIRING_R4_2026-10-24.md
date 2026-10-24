# CP Gate A Golden provider wiring and checkpoint coverage — R4 2026-10-24

Base main: `7621ddefe6c971e9eb231eb2a987519c86a2cb51`. Candidate branch: `tmp/cp-gatea-provider-wire-20261024`.

## Scope

Wire the existing read-only, digest-pinned Golden map into the actual Stage 7 embedded orchestrator. The preflight validates the provider once and publishes a same-run cache; each worker verifies schema, source, seed, decisions, coverage, sub-map hashes, full-map hash and reference ID before it uses scenario state. This CP changes no source model, seed/RNG, trial identity, historical data or state refs, and runs no production Trial/Checkpoint/Monte Carlo.

## Golden scope that evidence supports

This reuses provider blob `4bd0e706cf636755509484e41bed148fe0ebb8bf` from the previously verified candidate. Its 25,205 fingerprints represent:
- 20 non-C100 scenarios, trial IDs 1..1200;
- five C100 scenarios, trial ID 1 each;
- C030_G030, trial IDs 1201..2400 in addition to 1..1200.

All N=300/600/1200 checks are covered; C100 is a deterministic n=1 special case. N=2400 is supported only for C030_G030. The workflow must block the remaining non-C100 scenarios before generating IDs 1201..2400, until their own exact-golden extension evidence is verified. This CP intentionally never derives golden hashes from the actual run being evaluated.

## Gate semantics

Every non-C100 checkpoint compares each actual TrialResult SHA-256 with the corresponding pinned Golden value. Missing coverage or unverified provider blocks; hash mismatch or source/master-seed mismatch fails. The loop stops immediately after non-PASS Gate A. C100 trial 1 must match its Golden SHA as well as the existing independent trial ID/seed check. The provider cache is produced by preflight and is not treated as a new authority: its source runs, artifact IDs, artifact SHA-256 values and map hashes are revalidated before serialization.

## Verification

A candidate-only workflow loads the real pinned artifacts and performs a cache round-trip, exact coverage checks, YAML parse, compile and deterministic tests. It never invokes the production Stage 7 workflow. Status: `PENDING_PROVIDER_CI`; production acceptance is not asserted by static tests alone.


## Authority reconciliation — blocking finding (2026-10-24)

**Provider integrity CI:** PASS on latest Run [40031544345](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40031544345), exact tested SHA `9435384d1ffdbda3dc8ba759994d981314e34acf`: **79 passed in 1.32s**; the immutable artifact map/cache round-trip, source/seed/map identity, supported coverage, workflow YAML and compile checks all passed. The verifier also emitted the separate `BLOCKED_GOVERNANCE_AUTHORITY` disposition.

**Production authority:** `BLOCKED_GOVERNANCE_AUTHORITY`. Current `main` `docs/governance/DECISIONS_LOG.md` is blob `df4910e6a86bcce84f6b71d6d260913800474f95` and does not contain `D-2026-10-14-01` or `D-2026-10-15-10`. The candidate log copies inspected at `tmp/cp-golden-provider-20261014` (blob `d6a7ecd15e7335800dc8b2865e0a4fef6d5e9c70`) and `tmp/cp-gatea-c030-n2400-20261015` (blob `6104378f40791c95331b615cf511a0f38de759df`) contain a `NaNNaN...` corruption inside the D-2026-10-14-01 section, so those copies are not suitable as a verbatim authority source. D-2026-10-15-10 exists on the candidate branch but cannot independently repair its corrupt predecessor.

The code now separates map-integrity verification from governance authority. The production Stage 7 preflight refuses to publish the provider artifact or start matrix workers unless both required decision sections are present and required scope/artifact terms validate; it emits `GATE_A_GOVERNANCE_AUTHORITY_BLOCKED` otherwise. The read-only verifier reports map integrity independently and never turns current authority blockage into a production PASS.

**Required review:** restore the complete, uncorrupted, formally approved decision text into effective governance via an explicitly reviewed change. Do not reconstruct omitted normative text from hashes, and do not merge this draft just because candidate CI passes. The separate D-2026-10-17-07 C100 extension is out of scope; this provider intentionally retains C100 trial ID 1 only.
