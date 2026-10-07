# STAGE9A_EVIDENCE

## Product evidence

- Stage 9A build Run ID: `37671448546`
- run_head_sha: `5e25a94743f44554093934c57404c0b168e69651`
- Final build branch_head_sha before canonicalization: `16f52cd940164a37292e095e4b74fd9bd084f69b`
- Excel SHA-256: `0fb325fc9e196a534ba8ab7484dcfd0541cefd3a2ca37c3b6f930e3215f62f6d`
- Global Manifest SHA-256: `892da438955160bb59aff3046271402f57bdd61a4abb35f41db7188f61346ff6`
- Workbook sheets: 185
- Excel errors: 0
- Formula cells: 0
- Scenarios: 25
- Trials: 9005
- Representatives: 100
- Acceptance inventory: 163
- Acceptance PASS: 162
- Acceptance FAIL: 0
- Acceptance EXCLUDED: 1
- Excluded test: Test 158 under the recorded override

## Provenance sources

- Stage 7 Run ID: `37225915321`
- Stage 7 run_head_sha: `e0b2fab6710833774937d778097363d7a8ee8e59`
- Stage 7 source_sha: `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`
- Final build branch manifest blob SHA: `e796fa2443493b607f1f9c60b58eb63607959c26`
- Final manifest commit SHA before canonicalization: `16f52cd940164a37292e095e4b74fd9bd084f69b`

## Canonical closure target

Stage 9A canonicalization consists of:
1. permanent R4 record;
2. canonical `excel_builder.py`;
3. canonical `openpyxl` dependency;
4. corrected `Stage9A_Report.json` provenance;
5. explicit deviations record.

This file distinguishes product evidence from procedure/provenance evidence.

## CP-MEGA-FORENSIC-CLOSURE-9ABC-V6 — Canonical Manifest Determination

### Determination
- Final workbook embedded manifest SHA-256: `892da438955160bb59aff3046271402f57bdd61a4abb35f41db7188f61346ff6`.
- Artifact `stage9a-final-output` contains the same manifest identity; the archived `manifest_final.json` recomputes to the same `892da438...` using the workflow-defined `stage7_manifest_v1:` canonical hashing procedure.
- The archived artifact manifest Git blob SHA is `e796fa2443493b607f1f9c60b58eb63607959c26`.
- The later build-branch manifest at `tmp/stage9a-10-build-20261007` has blob SHA `0cef8b9d9bab6263707ea35c5c4478afd0778cb4` and declares `global_manifest_sha256 = 8796b86a65e68d35b11a9a81fea1a9f556b394cc2dcf5100fc4feffc606cdbc4`.
- The `8796...` manifest is byte-distinct from the archived `892...` manifest and was introduced by the later build commits `c2b6da82d60fe56f5416850857f5dcc3d78677ac` and `25cd61505abec2d4dcfe39e4bc83871e41c45eba`.
- The final Excel does not reference `8796...`; its embedded manifest reference is `892...`.

### Canonical result
**CANONICAL MANIFEST SHA-256 = `892da438955160bb59aff3046271402f57bdd61a4abb35f41db7188f61346ff6`.**

The later `8796...` identity is retained as forensic provenance of the temporary build branch and is not treated as the canonical product manifest because it is not the identity embedded in the produced Excel artifact.

