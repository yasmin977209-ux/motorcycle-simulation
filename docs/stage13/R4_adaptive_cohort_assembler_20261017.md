# R4 — Stage 13 adaptive per-scenario cohort assembler
Date: 2026-10-17
CP: CP-STAGE13-ADAPTIVE-ASSEMBLER-20261017
Base branch: tmp/cp-stage13-assembler-20261014
Base commit: e92539b7c76629fa306428289a211493c75ad033
Base main HEAD recorded by the prior Stage-0 audit: 647c19826b90d8224ce73ef9b90c306a45e03fb0
Normative reference SHA-256: ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479
Owner approval: Direct user approval “نعم” on 2026-10-17 for modifying/adding the Stage 13 tests in this narrowly scoped CP; main and workflow files must remain untouched.

## Scope and explicit exclusions
Implement a fail-closed Stage 13 assembler mode for a variable-size, per-scenario cohort selected by the approved first-passing-checkpoint policy. Add synthetic unit tests, and correct the README sheet-count field. No production Monte Carlo, no trial generation, no historical data/Parquet mutation, no threshold or identity change, no workflow edits, no main change, no merge/PR/Release, and no final-delivery approval.

## R4 — before change

| العنصر | الحالي | المرجع/القرار والفرع | النص الحاكم | الحكم |
|---|---|---|---|---|
| Adaptive cohort mode | _validate_mode_and_identity accepts only canonical, sample, demo in tmp/cp-stage13-assembler-20261014, scripts/stage13_assemble.py blob f124a9d3bbf101aaec005486c17fb28d0eec5a8a. | Approved per-scenario checkpoint policy recorded in tmp/cp-stability-policy-impl-20261017/docs/governance/DECISIONS_LOG.md, D-2026-10-17-04/-05/-06, plus direct user approval of this CP. | “The per-scenario checkpoint sequence is N=300, 600, 1200, 2400, 4800, 9600, ...”; “N=300 is coverage only”; stop at the first eligible passing transition and record stable_at_n. | K_CODE — no adaptive cohort contract exists in the assembler. |
| Fixed-size modes | Current canonical mode requires 11,005 IDs and sample mode 625 IDs (26..50); other counts can be inferred as demo by scripts/excel_builder.py when mode is omitted. | D-2026-10-10-04 architecture decision; D-2026-10-12-02 keeps the 625 sample distinct from the canonical 9,005-row CP-D source; D-2026-10-17-06 establishes per-scenario adaptive N. | Existing fixed cohorts remain distinct; adaptive final scope is the sum of per-scenario accepted stopping counts, not a hard-coded total. | K_CODE — add an explicit adaptive mode and never infer an unrecognized production count as demo. |
| Stability assertion | write_scenario_matrix defaults a missing final_status to the literal stable. | D-2026-10-17-04/-05/-06 and the owner-approved first-passing policy. | One passing gate does not imply overall stability; status must be based on explicit Gate A, applicable Gate B, and seven-metric §2.5 evidence. | K_CODE — remove the implicit stable default; adaptive input must carry explicit passed-gate and checkpoint evidence. |
| Cohort identity | General validation checks source SHA, scenario set, key uniqueness, and optional total count; it does not enforce an adaptive per-scenario stop count/history or recompute the ordered fingerprint map. | Normative reference SHA above; SOURCE_SHA=f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b, MASTER_SEED=20270101; owner-approved decisions D-2026-10-17-04/-05/-06. | Preserve source, seed, RNG/sampling/schema identity, exact trial IDs, fingerprints, and each checkpoint result; no completed trial may be rerun/relabelled. | K_CODE — adaptive acceptance must fail closed if identity, coverage, history, or fingerprints are missing/mismatched. |
| Excel README provenance | write_readme is called while the workbook has only one sheet and writes Excel sheets=1 before the other 184 sheets are created. | Reference §15.2: 185 sheets is the sole approved worksheet count; 10 global sheets + 175 scenario sheets. | The delivery must contain all 185 sheets and their correct names/order; provenance fields must not misstate the emitted workbook. | K_CODE — write actual workbook sheet count after all sheets are created, then verify saved value. |
| Test scope | Existing tests validate fixed canonical/sample modes and a synthetic demo; they do not validate an adaptive cohort manifest. | Current user's explicit “نعم” authorizes only modifications/additions needed for Stage 13 tests within this CP. | Add regression coverage for valid heterogeneous stop counts and all fail-closed cases without running Monte Carlo. | Authorized narrowly. No workflow/test-runner workflow change is authorized. |

## Proposed adaptive contract (new explicit input contract, not a business-rule change)
- Mode name: adaptive.
- manifest.cohort_id = "STAGE13_ADAPTIVE_STABLE_PER_SCENARIO_V1".
- Preserve the existing source identity: source_sha=f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b, master_seed=20270101, and require explicit non-empty schema_version, rng_identity, sampling_policy, aggregate ordered-map SHA-256, source/run provenance, scenario metadata, and total count.
- Each of the 25 scenario entries must explicitly declare final_status="SCENARIO_STABLE", stable_at_n, Gate A status, Gate B status, §2.5 status, and an ordered checkpoint history. Every final entry must provide seven-metric transition evidence for the immediately preceding actual checkpoint and current checkpoint; N=300 is COVERAGE_ONLY, never a §2.5 PASS.
- Accepted stable counts follow 600, 1200, 2400, 4800, 9600, ...; no 300 stop and no skipped doubling checkpoint. Per scenario, input trial IDs must be exactly 1..stable_at_n with unique keys and valid per-result SHA-256. The complete ordered scenario/trial fingerprint map must recompute to the declared aggregate hash.
- The adaptive contract requires explicit success of Gate A, Gate B, and the seven-metric §2.5 transition. It does not decide whether a real production cohort has passed those gates; it only verifies the submitted evidence structure and identities. Missing, non-finite, contradictory, or unrecognized evidence is rejected.
- Fixed canonical, sample, and demo modes remain separate; this CP must not reinterpret or merge their cohorts.

## Acceptance/tests for this CP
1. Validate the source SHA and required cohort identity/provenance fields.
2. Validate exactly 25 scenario metadata entries, explicit status and stop count per scenario, 300 coverage-only followed by contiguous doubling history to the final count, all seven metric checks, and explicit Gate A/Gate B/§2.5 success.
3. Reject N=300 as stable, unsupported/non-doubling count, missing statuses/history, a failed final transition, a skipped/altered checkpoint, mismatched trial IDs, duplicates, missing/invalid result hashes, total-count mismatch, or aggregate ordered-map SHA mismatch.
4. Exercise adaptive workbook assembly with synthetic data only; verify 185 worksheets, heterogeneous stop counts are reflected in scenario summaries, README reports 185, and no Excel errors/formulas appear.
5. Preserve all existing historic failures and existing canonical/sample behavior. Do not execute simulations or alter workflow files.
6. Inspect final diff and content after changes. Because this environment's container cannot resolve GitHub directly, if no approved branch-pinned execution path can run the focused pytest suite without modifying a workflow, record that test gate as PENDING/BLOCKED rather than claiming PASS. Do not work around this by changing a workflow.

## Current status before code changes
- Implementation/test evidence: PENDING.
- Production stability and delivery: BLOCKED by separate project gates.
- No production execution authorized by this R4.


## R4 implementation-detail addendum (contract clarification only)

This addendum records evidence-binding details made explicit while implementing the previously approved scope. It does not change reference thresholds, business rules, source identity, or the approved scope.

1. The computed ordered fingerprint map must match both the cohort's declared ordered map SHA-256 and the Gate A report's ordered-map SHA-256. A Gate A PASS for a different trial map is not acceptable.
2. Gate A, Gate B, and §2.5 evidence each carry a non-empty reference plus a well-formed SHA-256 digest. The final per-scenario references/digests must equal those in the final checkpoint entry.
3. Each §2.5 metric record includes old/new finite numeric values and a status. The assembler recomputes the status using the unchanged strict <1% relative rule and the <1 currency unit absolute fallback when |old| < 1e-6. The reported status must equal that calculation for each of the seven named metrics.
4. For each non-C100 scenario, Gate B P50 evidence at N=600 and N=1200 must link exactly to the P50 of the immediately previous and current checkpoint in the recorded history. The approved strict >5% continuation rule and the near-zero absolute fallback are re-evaluated; a triggered scenario cannot stop before N=2400.
5. For C100 scenarios, the adaptive input must separately reference the approved deterministic-equivalence evidence. That metadata reference does not turn this assembler into an independent Gate A artifact reader, and the assembler does not claim that production gates passed merely because a reference string exists.

## Post-change execution status (focused synthetic test gate)

- Adaptive code and synthetic regression tests remain candidate-branch changes only.
- Focused workflow Run `38995349182` completed successfully on tested HEAD `3fdcdf8d006eff8f4a8fabb9ea2feb5c70c81633`. The actual downloaded evidence ZIP was inspected: `pytest.log` reports `25 passed in 10.98s`; JUnit XML records 25 tests, 0 failures, 0 errors, 0 skipped; `PY_COMPILE=PASS` and `PYTEST_EXIT_CODE=0`.
- Artifact `12085749809` (`stage13-adaptive-test-evidence-38995349182`) reports 3,787 bytes and `sha256:3a77d5f85385380abebece7811decdf87749dfee77a001b9fac3e26aede71c1c`. The downloaded ZIP is exactly 3,787 bytes and its independently computed SHA-256 matches the GitHub artifact digest. The seven SHA-256 fingerprints in `input_sha256.txt` independently match the corresponding files read from the exact tested branch; the manifest confirms synthetic fixtures only, `SOURCE_SHA=f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`, `master_seed=20270101`, and `main_modified=false`.
- These tests establish only the focused synthetic regression gate for this candidate HEAD. They do not prove a production Gate A provider is connected, that production Gate A/Gate B passed, that overall stability is established, or that final deliverables are accepted.
- After the evidence was collected and inspected, the owner-approved temporary workflow `.github/workflows/cp-stage13-adaptive-tests.yml` was removed on this candidate branch by commit `99e2f13da1f42019bc7d7e20734e64ac3b63fe46`. The run and artifact are retained.
- No production simulation, trial generation, source/RNG/seed change, historical dataset edit, main edit, merge, or Release was performed.

## R4 addendum — Gate B P50 continuation-order fix and temporary test workflow

**Recorded:** 2026-10-17
**Owner approval:** The user explicitly replied “نعم” to creating a temporary, branch-pinned workflow to execute the focused synthetic Stage 13 test suite. This later approval changes only the prior “no workflow edits” exclusion for the single test workflow described here. It does not authorize merging, editing `main`, running production simulations, generating trials, changing golden/source/seed/RNG/sampling policy, or releasing deliverables.

### Finding before change

Static review of `scripts/stage13_assemble.py` found that the non-final “first passing checkpoint” guard ran before the Gate B P50 continuation rule. When Gate A, Gate B, and the seven §2.5 metrics passed at N=600 but the approved P50 rule required continuing to N=2400, the guard could reject the allowed continuation as `ADAPTIVE_STOPPED_AFTER_FIRST_PASS_VIOLATION` before recording that continuation was mandatory. This is a **K_CODE** finding based on the exact control-flow ordering (pre-change lines 898–925 of blob `72b0a7d7db17be0d270a486f87c070ea4a2776c5`), not a runtime test result.

### Authorized bounded fix

1. Evaluate and validate the P50 trigger for the current eligible checkpoint before applying the early-stop guard.
2. Preserve the trigger across later checkpoints; while N=2400 is mandated by a prior trigger, an otherwise passing N=600 or N=1200 checkpoint is not an eligible stopping point.
3. Keep the approved strict >5% relative-change trigger and near-zero absolute fallback unchanged; no threshold or business rule changes.
4. Add synthetic regression coverage for a P50 trigger at N=600, no trigger at N=1200, and the required N=2400 continuation. Synthetic data only.

### Temporary test workflow contract

- Exact workflow path: `.github/workflows/cp-stage13-adaptive-tests.yml`.
- Exact branch pin for both trigger and checkout: `tmp/cp-stage13-adaptive-assembler-20261017`; path-filtered push trigger only.
- Read-only GitHub token permissions (`contents: read`); no `workflow_dispatch`, self-dispatch, production/data credentials, or write permissions.
- Every job has an explicit timeout; run only Python compilation and focused synthetic pytest tests for the Stage 13 assembler/Excel adaptive path.
- Upload bounded audit evidence (tested HEAD/file hashes, Python/package versions, pytest log and JUnit XML); inspect run/job results and the actual downloaded artifact before assigning PASS.
- Do not generate Monte Carlo trials, access production data, or change source SHA, master seed, RNG, sampling policy, historical records, or the normative reference.
- The workflow is temporary and branch-pinned. After collecting and independently inspecting evidence, remove the workflow file from the candidate branch via a reviewed commit; retain the branch and all test evidence. Do not modify any other workflow.

### Acceptance and fail-closed dispositions

- Focused tests must pass on the exact tested HEAD.
- Independently inspect the test artifact contents, head identity, checksums and byte size, and verify that only the synthetic test scope ran.
- If the Run does not complete or its artifact cannot be inspected, record PENDING/BLOCKED; no PASS by absence of a reported failure.
- This CP does not authorize or imply updating/merging `main`. Any later main update requires separate R4 review of the final tested diff and independent evidence review.
