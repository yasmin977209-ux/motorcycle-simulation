# R4 — Stage 13 synthetic runtime verification for strict trial_id typing

**Date:** 2026-10-19  
**Mode:** bounded test-only workflow authorization reconciliation; no model/data/manifest/reference changes.

## Element | current state | authority | exact controlling scope | ruling

- **Candidate branch / tested identity:** `tmp/cp-stage13-excel-compat-20261017`, exact current HEAD before this R4 is `250b855c9ad97875c92e3dc682e6e2f7b2071a2a`; assembler blob `71e05034bafb551aea2949adc94013e8bb23d239`; test blob `976ebc8365db7f2380f15317c677990e34a1269c`. Branch compare against `250b855c9ad97875c92e3dc682e6e2f7b2071a2a` is identical.
- **Main boundary:** main HEAD `7c41ac64c4b599f4e1d6a50be055f82cdd87a7b5`; state blob `2178260bb18efeb81437486f13b6d10cf5e85936`; `12-CLOSED / FINAL_DELIVERY_BLOCKERS_OPEN`. No main writes are in scope.
- **Defect under verification:** `K_CODE` — Python equality may equate `True == 1` and `1.0 == 1`. Candidate code now checks `type(summary.get("trial_id")) is int` and `type(daily_row.get("trial_id")) is int` before equality. The correction has source read-back, but no repository runtime result exists for this exact SHA: GitHub Actions run query returned `total_count=0`.
- **Owner authorization:** `docs/stage13/OWNER_SCOPE_AUTHORIZATION_20261017.md`, blob `c0b8e5c509ef5ccc2c747504adfab89d2c3c0ee4`, on this candidate branch explicitly authorizes a temporary read-only test workflow on this exact branch, with `contents: read`, a push trigger/path filters, focused synthetic tests and a synthetic demo workbook, and an evidence artifact. It prohibits Monte Carlo, production/historical datasets, seed/RNG/sampling/source identity changes, main edits, merge and release; it also requires removal of the temporary workflow after inspecting its run/artifact.
- **Current workflow inventory:** the live `.github/workflows` directory on the authorized branch contains no Stage 13 synthetic-compatibility workflow. The temporary workflow therefore must be added under this exact authorization before the current code SHA can receive runtime verification.

## Authorized validation plan

1. Add only `.github/workflows/cp-stage13-synthetic-compat-verify.yml` on the authorized candidate branch; do not edit tests or any existing workflow.
2. Trigger only on push to `tmp/cp-stage13-excel-compat-20261017`, with path filters for this bounded Stage 13 CP. Grant only `contents: read`; use a job timeout; do not add `workflow_dispatch`.
3. Run only the focused synthetic Stage 13 tests for 185-sheet demo assembly, normative Max Case selection/no-positive-case handling, recorded representative ID rejection, plus the synthetic adaptive/legacy compatibility test files.
4. Run an additional inline check against the existing `demo_data()` fixture to verify that bool/float/string trial IDs are rejected for both summary and daily payloads. Generate one explicitly synthetic demo workbook from that fixture; verify 185 sheets, representative role labels, zero formula/error cells, and record the workbook SHA-256.
5. Upload only pytest output, the synthetic demo workbook, audit JSON, and scope metadata. Do not read or stage canonical dataset artifacts, Parquet data, production results, or historical trial payloads.
6. Query the Actions REST run list by the exact resulting `github.sha`, inspect the complete job logs and artifact, and compare artifact/workbook identity to that SHA. Report PASS only if all checks and independent artifact inspection succeed.
7. After inspection, remove this temporary workflow by a commit on this candidate branch as the owner authorization requires. Preserve the run/artifact evidence and the branch. Do not merge, close PRs, create a Release, or change main.

## Acceptance / fail-closed

- **PASS scope:** synthetic authoring/runtime validation only, tied to the exact workflow head SHA and inspected artifact SHA-256.
- **Not established by this CP:** canonical dataset acceptance, real-artifact Max Case availability, Stage 13 production build, CLI/Monte Carlo/trial/checkpoint execution, delivery acceptance, or overall project completion.
- If the workflow does not run on the exact push SHA, uses non-synthetic input, lacks artifact evidence, or cannot be inspected, retain `RUNTIME_VALIDATION_PENDING`; do not substitute an older run or claim PASS.
