# R4 — Gate B CI near-zero limit — 2026-10-21

## CP scope

- Base `main` HEAD: `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`
- Candidate branch: `tmp/cp-gateb-ci-near-zero-20261021`
- Classification: `K_CODE`
- File to change: `run_batch.py` only.
- Objective: apply the relative confidence-interval limit when the mean is outside the normative near-zero region, and the absolute CI epsilon only inside that region.
- Excluded: stop-window policy; consecutive-checkpoint count; Confidence Sequences; tests/workflows; source SHA; seed/RNG; cohort/trial IDs; Golden; historical artifacts; `state.json`; main; production run; merge/release.

## Current code

Base blob: `0418ddea818c194a5b582df94778fa5f13a3ecc4`.

The current Gate B metric summary uses:

```python
limit = max(
    constants.CI_ABSOLUTE_EPSILON,
    constants.CI_RELATIVE_TOLERANCE * abs(mean),
)
```

This keeps an absolute one-riyal limit as a floor for all means. For example, at `mean=10`, the 1% relative limit is 0.1 but `max(1, 0.1)` returns 1, which is materially more permissive than a conditional near-zero rule.

## Authority and interpretation

- Effective `D-2026-10-10-01` in `docs/governance/DECISIONS_LOG.md` specifies a 95% Student-t CI half-width below 1% of `abs(mean)`, with `CI_ABSOLUTE_EPSILON=1` for near-zero.
- The original approved reference defines the near-zero boundary using `REFERENCE_EPSILON = 1e-6` and applies an absolute one-riyal difference only when the prior comparison value is in that near-zero region (§2.5).
- This CP maps the existing near-zero boundary to Gate B's absolute-epsilon fallback: if `abs(mean) < REFERENCE_EPSILON`, use `CI_ABSOLUTE_EPSILON`; otherwise use `CI_RELATIVE_TOLERANCE * abs(mean)`. This does not alter the declared 1% tolerance or one-riyal epsilon.
- If the owner intends a different Gate B near-zero boundary than the existing reference boundary, that would require an explicit policy decision; no new boundary is invented here.

## Minimal change

Replace only the `max(...)` expression with the conditional limit described above. Keep `stable = half_ci < limit` strict and unchanged. Do not change the three Gate B metrics, t critical values, confidence level, stopping window, thresholds, checkpoint IDs, or data.

## Acceptance criteria

1. `abs(mean) < 1e-6` uses absolute limit 1.
2. `abs(mean) >= 1e-6` uses the relative 1% limit, even if that limit is below 1.
3. Existing strict comparison `half_ci < limit` remains unchanged.
4. No repository test or workflow is modified. Validate with an uncommitted local logic probe and post-write source/diff read-back only.
5. Classification remains `PASS_SCOPED_LOCAL / NOT_CI_VALIDATED`; it is not Gate B acceptance, not a production checkpoint, and not approval of the stopping policy.

## Disposition

This is a bounded K_CODE correction under current technical delegation. It does not close Gate A/source identity, establish stability, implement CS, or accept delivery.


## Execution/read-back result

- Code commit: `200ede08bfc7d5055d04f770ae8b4d2a67ee7144`; new `run_batch.py` blob: `00ae8901af5e57799c31680fa54a06ffb7a1997c`.
- The change replaces only the `max(...)` tolerance selection; `half_ci < limit` is unchanged. Candidate compare against base `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`: 2 commits ahead / 0 behind, exactly the R4 document and `run_batch.py` changed.
- Temporary, uncommitted logic probe passed: mean 0 and ±0.999e-6 use limit 1; mean exactly 1e-6 uses the relative branch; mean 10 uses 0.1; mean -10 uses 0.1; mean 200 uses 2. Output: `PASS_SCOPED_LOCAL_LIMIT_PROBE`.
- This is not pytest, not CI, not a full `run_batch.py` integration test, and not a production Gate B run. No test/workflow was changed or triggered.
- Live `main` re-read as `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`, unchanged.
- Disposition: `PASS_SCOPED_LOCAL / NOT_CI_VALIDATED`. This corrects only the CI-limit branch and does not establish Gate A, checkpoint stopping policy, overall scenario stability, Confidence Sequences, or delivery acceptance.
