# Stage D Session Status — 2026-11-07

Append-only status record. D0–D6 dispositions and evidence are recorded in the 2026-11-07 effective closure files.


## D5 publication record correction — 2026-11-05 (append-only)

- D5 Run 41928234377 tested source SHA: baf696af1e951cbf4a79e8a9e009c60c6b053b2d. The workflow committed publication evidence as 4c6a84b10ac78b6067175d0eafa149f3f12dbc2a; the earlier `publication_commit_sha` field and prose entry naming baf696... identify the triggering/tested SHA, not the documentation commit.
- D5 matrix path is dated 2026-11-05, but its internal title says 2026-11-03; this is a stale title only and does not change package bytes or test results.
- D5 exact-final-head Raw readback was performed at 4c6a84b10ac78b6067175d0eafa149f3f12dbc2a.

## D6 independent post-write audit — 2026-11-05 (append-only)

- Run 42403657899; tested source SHA 42922d06637b7fad1d36c412e2253423f9367f34; D5 Artifact 13582441423 from Run 42393413807.
- Disposition PASS_SCOPED_WITH_LIMITATIONS; classification T2_INTERIM / NOT_FINAL_BLOCKED.
- See docs/stage_d/D6_AUDIT_RUN_42403657899/FINAL_AUDIT.md and FINAL_AUDIT.json for check-level results and limitations.
- D6 is not P17 acceptance, FINAL_ACCEPTED, CONVERGED or release authorization.
