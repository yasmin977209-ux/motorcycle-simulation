# D6 execution trigger — 2026-11-04 / dependency closure 03

Trigger the independent D6 post-write audit against the current branch HEAD and the immutable D5 Artifact 13264003231 from Run 41704252218.

The workflow now installs lxml explicitly because the independent streaming Excel auditor imports lxml for bounded-memory worksheet XML parsing. This removes reliance on incidental runner packages. DOCX directionality checks cover all supported Word text-story parts and require explicit flags on every text-bearing paragraph/run.

No historical D3/D4/D5 bytes, manifest, business rules, thresholds, identities, or Trial records are changed. No Trial/Simulation/Monte Carlo/N expansion, backfill, zero-fill, main write, merge, Release, or final-acceptance declaration is authorized.

This record requests execution only; it does not claim that the workflow started or passed. Record the actual Run ID, tested SHA, job and artifact from GitHub Actions.
