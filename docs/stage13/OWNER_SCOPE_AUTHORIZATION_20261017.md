# CP Stage 13 — scoped owner authorization record

- Date: 2026-10-17
- Branch: \`tmp/cp-stage13-excel-compat-20261017\`
- R4 baseline commit: \`7b5c31fe4b2a11c09cc515d28c7c3541c747895b\`
- Required \`main\` base: \`647c19826b90d8224ce73ef9b90c306a45e03fb0\`
- Normative reference SHA-256: \`ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479\`

## Explicitly authorized scope

The user explicitly requested a temporary, read-only test workflow pinned to this exact branch for Stage 13 and synthetic Excel compatibility tests, followed by inspection of the run and artifact. This later instruction expands only the test-execution mechanism from the R4 document's initial pending/blocked state.

The workflow is constrained to:
- a \`push\` trigger on \`tmp/cp-stage13-excel-compat-20261017\` with path filters for this bounded CP;
- \`permissions: contents: read\`, a job timeout, and no \`workflow_dispatch\`;
- focused synthetic tests and a synthetic demo workbook only;
- an evidence artifact containing pytest output, the synthetic workbook, audit JSON, and scope metadata;
- no Monte Carlo, no production or historical dataset, no RNG/seed/sampling/source identity changes, no edits to \`main\`, and no merge/release.

After the run and artifact have been inspected, the temporary workflow file is to be removed by a commit on this branch, leaving the branch itself intact. Artifact/run evidence remains the record of the execution; no PASS is allowed until the workbook and archive contents are independently inspected.
