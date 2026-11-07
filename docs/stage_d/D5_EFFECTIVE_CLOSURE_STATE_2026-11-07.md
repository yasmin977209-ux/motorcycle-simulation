# D5 Effective Closure — 2026-11-07

**Status:** PASS_GAP_FREE — D5 scoped package integrity and publication/readback only.

## Tested execution

- Repository: `yasmin977209-ux/motorcycle-simulation`
- Branch: `tmp/d1-rebuild-20261101`
- Workflow Run: [42393413807](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42393413807)
- Job: `128465567045` — `preflight`
- Tested build SHA: `c757126ac27e8f6606f38b14324119cc22604858`
- Evidence commit: `85dfc8c385302923987f90d49a423cf79b028cd9`
- Exact final HEAD Raw Readback: PASS on `85dfc8c385302923987f90d49a423cf79b028cd9`

## D5 package

| Item | Bytes | SHA-256 |
|---|---:|---|
| D5 package ZIP | 519,104,624 | `f7004da675f2af8d3201ed1b51d5106b890fe521ab66e198c635be414e5421c7` |
| manifest.json | 11,003 | `a291a886fc6973f1f747cc74c98b0b8a25b01a7f96e32048c4c345c1d19484eb` |
| SHA256SUMS.txt | 938 | `7c76cef416a08b6864e2b1a1c2e4159023e72cb0326793887cceb143d4ce0421` |

- ZIP inventory: exactly 8 members — seven deliverables plus `manifest.json`.
- ZIP CRC and exact inventory: PASS.
- SHA256SUMS: 10 entries covering the package ZIP, manifest, seven deliverables, and external Number Registry.

## Published GitHub Artifact

- Artifact ID: `13582441423`
- [Artifact and workflow run](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42393413807)
- Outer Artifact bytes: 519,117,017
- GitHub digest: `sha256:ae84c0e9c27d5a0be7c5c37ec1f923676745013b86e3fd528178d830df61d0cc`
- Independently downloaded ZIP SHA-256: same digest
- Remote readback: PASS
- Expiry: `2026-12-07T16:54:42Z` (30-day retention)

## Tests and workflow evidence

- Command: `python -m pytest -q -rs tests/test_d5_package.py`
- Result: **5 passed, 0 failed**, one non-blocking warning from the duplicate-member negative test fixture.
- Build/reopen/verify: SUCCESS.
- Publication: SUCCESS.
- Independent Artifact download, metadata/digest/size/inventory/CRC/payload-byte comparison: SUCCESS.
- Evidence commit and remote raw readback: SUCCESS.

## D4 input reconciliation

The five D4 DOCX files were independently read from the exact GitHub branch contents and their SHA-256 values recomputed from the decoded file bytes. Their sizes match the D4 effective-closure record. The obsolete expected fingerprints in the D5 validator were corrected; no report content, accounting values, scenario identity, or simulation inputs were changed.

## Preserved project status

- Classification: `T2_INTERIM / NOT_FINAL_BLOCKED`
- Financial Gate A: `PASS_SCOPED`
- Production Gate A: `NOT_DECLARED`
- Gate B N=2400: `FAIL_SCOPED (10 PASS / 10 FAIL)`
- Stability: `NOT_CONVERGED (0/60)`
- N=4800: `NOT_EXECUTED`
- Five accounting fields: `MISSING_EVIDENCE`
- Full 177-unique-test suite: `NOT_RUN`
- D6: pending at D5 closure
- Final acceptance: `NOT_DECLARED`

## Limitations

D5 closes only the package integrity, publication, and readback scope. It does not establish D6, Global Preservation Gate, final acceptance, production readiness, or release authorization. E2 replay archive migration, independent durable copies, raw-byte readback from both storage systems, and restore drill remain open.

No Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, source identity change, main write, merge, or Release was performed.
