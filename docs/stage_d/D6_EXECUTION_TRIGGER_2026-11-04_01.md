# D6 execution trigger — 2026-11-04

This append-only trigger requests the D6 Independent Post-Write Audit workflow to execute the currently committed auditor and tests on this branch.

- Trigger scope: execute only the existing immutable D5 Artifact 13264003231 from Run 41704252218.
- Code changes immediately preceding this trigger: all DOCX text-story parts (document, headers, footers, footnotes, endnotes and comments) are checked for explicit paragraph bidi and text-run RTL flags; missing flags fail closed.
- Regression coverage: Arabic header direction, visible-text direction completeness, and missing-flag detection.
- This trigger does not authorize changing any D3/D4/D5 deliverable, manifest, reference, business rule, threshold, source/cohort/seed/Trial identity, or running any Trial/Simulation/Monte Carlo/N expansion.
- Expected workflow event: push to tmp/d1-rebuild-20261101 matching the D6 trigger path filter.
- No test result is asserted by this file; only the subsequent GitHub Actions run and exact tested SHA can establish execution evidence.
