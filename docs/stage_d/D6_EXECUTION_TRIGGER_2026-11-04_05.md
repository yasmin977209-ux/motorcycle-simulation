# D6 execution trigger 05 — LibreOffice profile URI correction

Date: 2026-11-04
Base HEAD: 95410a3111c440b95c68208dcda0264913aeb981
Scope: D6 audit harness only.

The prior D6 run recorded five independent LibreOffice render timeouts. Inspection of the exact tested source found that the per-file profile argument used a relative URI of the form `file://d6_rendered/lo-profile-00`, which treats the first path segment as a URI authority rather than an absolute local file path. This trigger corrects the profile to a created absolute path encoded with `Path.resolve().as_uri()`, and resolves the output directory and DOCX paths before invoking LibreOffice.

Regression coverage asserts absolute `file:///` profile URIs and existing isolated profile directories, while retaining per-file timeout isolation and continuation behavior.

No D5/D4/D3 deliverable, manifest, historical Artifact, financial value, business rule, threshold, source/cohort/seed/Trial identity is changed. No Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, main write, merge, Release or final-acceptance declaration is authorized. The separate financial mismatch findings remain unresolved and are not waived by this harness correction.
