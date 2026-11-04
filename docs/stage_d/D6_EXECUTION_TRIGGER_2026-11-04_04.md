# D6 execution trigger — 2026-11-04 / isolated DOCX rendering and exact session readback

Run the independent D6 post-write audit against the current branch HEAD and the immutable published D5 Artifact pinned in the existing D5 preflight record.

This execution includes only technical audit-harness corrections:
- Render each DOCX in a separate LibreOffice process, with an isolated user profile and a 120-second per-file timeout. Preserve per-file outcomes and continue after an individual rendering failure.
- Bind the D6 session-record path exactly to the current GitHub Actions Run ID for commit, Raw readback, and audit Artifact publication. Never select a session record by an unordered glob.
- Trigger the audit on changes to its workflow, auditor, tests, or explicit trigger record.

No historical D3/D4/D5 artifact, manifest, workbook, report, business rule, threshold, source/cohort/seed identity, or Trial record is changed. No Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, main write, merge, Release, or final-acceptance declaration is authorized.

A known financial mismatch in the immutable D5 package remains a blocking finding. This run must report it honestly; it must not suppress, round, tolerance-match, or repair the published artifact in place. This trigger does not declare D6 closed.
