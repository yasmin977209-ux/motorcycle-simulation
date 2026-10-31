# Motorcycle Simulation — Persistent GitHub Handoff
**Snapshot date:** 2026-10-31  
**Repository:** `yasmin977209-ux/motorcycle-simulation`  
**Authorized working branch:** `tmp/cp-v240-stage-d-s6-deliverables-20261030`  
**Governing classification:** `T2_INTERIM / NOT_FINAL_BLOCKED`

## Purpose
This file is the durable entry point for any later ChatGPT conversation or engineering agent. Connect to this repository and read this file, `docs/PROJECT_CONTINUITY.md`, `docs/stage_d/D0_INPUT_AUDIT.md`, and the Stage D closure/audit files before doing work. Do not ask the owner to re-upload repository files or historical artifacts if they are already available through GitHub Actions artifacts or committed repository content.

## Authority and immutable constraints
- Governing owner decision: `D-2026-10-30-REFERENCE-V2.4.0`, approved by owner; governing SHA-256 `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`.
- Historical S6 execution reference remains v2.3; never conflate `historical_execution_reference_sha256` with `current_governing_reference_sha256`.
- S6: source `da1a9ea9b5cd789c944de3f07b08395bb67c49e7`, cohort `s6-v23-da1a9ea9`, seed `20270101`.
- C100: source `965281d52441cd0d4b744e211c9f68ee4cdc3753`, cohort `c100-v23-s4-20261026-965281d5`, always classify as `CROSS_COHORT_DETERMINISTIC_REUSE`; never pool as independent S6 trials.
- Stage 12/13 lineage source `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b` remains separate.
- Never modify `main`; no PR, merge, Release, new simulation/trial/Monte Carlo, N=4800, historical artifact mutation, speculative accounting backfill, seed/cohort/source/threshold/business-rule changes, or final acceptance/convergence/P18 claims.
- Preserve unresolved `K_SPEC` conflicts. If a business rule is missing or conflicting, stop and request owner resolution.

## Verified project baseline (historical evidence; revalidate live before relying)
- Stage B: `PASS_SCOPED`, Run `40993439735`, tested SHA `b2e7adec5be59069e8e4e18dee51d166670bb58b`, 41 passed / 1 skipped.
- Stage C: `PASS_SCOPED`, Run `41098699740`, Job `124211088430`, tested SHA `e3c2098df9fc5dbc126eb1e77ad35c493ff3ac70`, Artifact `12998778418`.
- Stage C scope: 125 role assignments, 105 unique keys (100 S6 + 5 C100), Full Logging 105/105, 216,253 daily rows, 24,545,842 events, 1,297,518 roll-forward checks, zero budget/flow mismatches, 105/105 financial fingerprint matches.
- Gate A financial fingerprint: `PASS_SCOPED` only (80/80 pairs, 90,000 comparisons, zero differences). Production-wide Gate A: `NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS`.
- Gate B at N=2400: `FAIL_SCOPED` (10 PASS / 10 FAIL). Stability: `NOT_CONVERGED` (0/60 transitions). N=4800: `NOT_EXECUTED`, unauthorized.
- The 105 Full Logging keys do not substitute for the missing 48,000-trial historical ledger and five missing accounting fields: Accounts_Receivable, Accumulated_Depreciation, Gross_Bike_Assets, Guarantee_Claim_Receivable, Total_Assets.

## Stage D scope and pinned inputs
Authorized branch only: `tmp/cp-v240-stage-d-s6-deliverables-20261030`.  
Pinned immutable inputs:
1. Aggregate Artifact `12852969854`, Run `40773412377`, SHA-256 `ec05a69ae8968585decf83cf0716d56c264f47f86187cfd3cf53b11f52ca2e54`.
2. Full Logging Artifact `12998778418`, Run `41098699740`, SHA-256 `403371cc8eb12880dda05529b4c83dd675bfa609e8680c09d35efa729c5b5aeb`.
3. C100 Artifact `12630457193`, Run `40263424595`, SHA-256 `c977d1cbb5204919eadc72358533f77cdbbc239902bcd6f921bf1a915a716e79`.

## Stage D status at this handoff
### D0
- D0 input audit and repository closure reports have been published in the Stage D branch.
- D0 disposition is `PASS_SCOPED_WITH_LIMITATIONS`, not proof that all historical data exists.
- Preserve manifest reconciliation: original 105 trial manifests are pending; sidecar/root audit indicates scoped pass; independent expected byte sizes are absent, so normalized status remains `NOT_VERIFIED` for 105/105.
- Parquet schema/row verification and value-level representative revalidation remain limited by the unavailable Parquet reader in the previous local environment.
### D1
- Local implementation was reported as 27 passing tests (10 Builder + 17 Registry), compileall pass, and integration checks for 125 assignments / 105 cohort-qualified keys.
- This is local-only evidence. The live branch's D1 closure report explicitly says `SOURCE_BUNDLE_NOT_COMMITTED`; exact-head Stage D workflow has not run.
- Existing live modules include `scripts/s6_deliverables_model.py`, `scripts/s6_artifact_reader.py`, and `scripts/s6_manifest_resolver.py`. Missing at last live check: `scripts/s6_deliverables_builder.py`, `scripts/s6_number_registry.py`, `scripts/s6_validate_representatives.py`, `tests/test_s6_deliverables_builder.py`, `tests/test_s6_number_registry.py`, `results/number_registry.json`, and `.github/workflows/stage-d-deliverables-validation.yml`.
- Therefore D1 is not repository-source-closed and not delivery-acceptance-closed. Do not generate Excel or Word until the gates are genuinely met.
### D2
- A local registry was reported at 13,954 entries (13,946 VERIFIED_LOCAL, 8 REPORTED_ONLY), 10 unavailable metrics/evidence records, one missing source digest, zero duplicate IDs, zero floats. Local SHA-256: `53ece080e0eeea1feefbdac3727997deece17670bff4ac8539ea01562a12af73`.
- Local shared model SHA-256: `3c484ddead389e43a4da778a22e233448786ae09869e5a6737b9f53a3655b3a7`.
- Local source bundle SHA-256: `caa5d6d72cdc8588de104f24aa23499e85912921bce9a509e27e10e909d74dc6`.
- These local files have not been committed to this branch. Their hashes are `REPORTED_ONLY` until byte-for-byte remote verification and a commit SHA exist. D2 is not repository-closed.
- D2 calculations use integer/Fraction exact values and Decimal HALF_EVEN for display; no financial float. The five K_SPEC conflicts remain unresolved.
### Delivery acceptance
Tests 175, 176, 179, 180, 181, 182, 183, 186 are `NOT_RUN` as an exact-head Stage D delivery suite. No Excel workbooks, five DOCX reports, eight-member ZIP, external SHA256SUMS, or independent post-write audit have been accepted.

## Mandatory evidence contract — no exceptions
Never label an output or gate PASS unless all four are recorded:
1. Canonical GitHub file URL on the authorized branch.
2. SHA-256 calculated from the bytes fetched back from GitHub after commit (not from the local source copy).
3. Commit SHA containing that exact file version.
4. Scope, test/run identity, limitations, and source lineage.

If any of the above is absent, classify the evidence `REPORTED_ONLY` or `MISSING_EVIDENCE`; do not advance a gate. A Git blob SHA-1 is not a substitute for SHA-256.

## Durable production and handoff design — eliminate local-only deliverables
Use a repository-first / CI-produced workflow:
1. Before work, read this file and live-check branch refs, exact HEAD, working tree state, continuity doc, relevant artifacts, and existing workflow runs. Record timestamp and source status.
2. Author source/config/docs directly into the authorized GitHub branch (GitHub Contents API or Git Data API); verify each write by fetching the file back. Do not create a local-only deliverable and defer its upload.
3. For binary or large outputs, do not generate them in the chat's ephemeral local filesystem. Commit the deterministic builder and a manually dispatched, branch-guarded GitHub Actions workflow first. The workflow must download only the three pinned existing artifacts, verify SHA-256 and size, run tests, generate outputs in the runner, run independent post-write audits, calculate hashes from generated bytes, then commit all deliverables and a machine-readable evidence manifest back to this same Stage D branch. Never run simulation/trials.
4. The workflow must use an explicit allow-list of paths, fail closed on unknown/unregistered number IDs, enforce exact branch and expected HEAD (lease/CAS semantics), and refuse to overwrite historical artifacts or touch main. Do not use pull_request triggers or automatic PR creation.
5. After the workflow commits, fetch every output from GitHub, recompute SHA-256 from fetched bytes, verify file URL + commit SHA + digest, then update `docs/PROJECT_CONTINUITY.md` and this handoff file with the evidence matrix. A run artifact alone is not a repository commit.
6. Keep the large registry and workbooks in the repository or in immutable GitHub Actions artifacts referenced by committed manifest. Prefer Git LFS only if explicitly configured and independently verified; do not assume it exists.
7. Every future response that creates a file must finish its GitHub commit and remote byte verification in the same response, or clearly report the write as blocked and not PASS. Never ask the owner to upload the same bundle again if it can be read from the repository or pinned Actions artifacts.

## Open K_SPEC conflicts — preserve, do not silently resolve
- `DOCUMENT_STATUS_CONFLICT`: owner decision approved while package cover/template still says pending.
- `HISTORICAL_REFERENCE_HASH_CONFLICT`: two historic Stage 12/13 reference hashes; do not choose without original file.
- `TRIAL_MANIFEST_STATUS_CONFLICT`: trial manifests pending while sidecar/root audit says pass-scoped.
- `S6-CODE-ID-MAPPING`: S6-CODE-08 is explicit; do not invent S6-CODE-09/10.
- Stage 9C old PARTIAL vs later Reaudit PASS belongs to historical Stage 12 lineage, not S6.

## Next authorized actions
1. Revalidate live branch HEAD and all relevant files; do not assume the historical HEAD.
2. Solve source transfer using direct GitHub writes. If the connector cannot transfer local binary bytes, use a user-independent repository-side build path (committed sources + guarded GitHub Actions), not repeated manual uploads.
3. Publish the missing D1 source/test files and D2 registry generator/source/tests. Then run only non-simulation exact-head validation.
4. Revalidate representative Parquet values only if a safe reader can be installed in the runner without changing source artifacts; otherwise retain `NOT_VERIFIED`.
5. Do not proceed to Excel/DOCX/ZIP or final acceptance until all required gates are evidenced. Keep all outputs `T2_INTERIM / NOT_FINAL_BLOCKED`.

## Required first message in any new conversation
"Read `docs/PROJECT_HANDOFF.md`, `docs/PROJECT_CONTINUITY.md`, and the Stage D audit/closure files from GitHub. Revalidate the live branch and remote bytes before relying on any prior status. Continue only on the authorized Stage D branch, preserve all constraints and conflicts, and do not ask me to re-upload files already present in the repository or pinned Actions artifacts."


## Latest execution checkpoint — 2026-10-31 18:02 UTC

- Authorized branch: `tmp/cp-v240-stage-d-s6-deliverables-20261030`.
- Live branch HEAD at checkpoint start: `19559159f280cef241cb8758e923ffb5a5151694`.
- `main` remains `c6e54349a5e94f65d5aa9f83141f225d777bb474`.
- D0 remains closed only as `D0_REPOSITORY_CLOSED / PASS_SCOPED_WITH_LIMITATIONS`, bounded to the pinned-input audit and repository documentation. Historical 48K accounting gaps, missing fields, Parquet limitations, and manifest conflicts remain open.
- D1 and D2 remain `BLOCKED / REPORTED_ONLY_LOCAL`: the full local source package, tests, workflow, and 13,954-entry registry are not present in the live branch. The required exact-head Actions run does not exist.
- Local source workspace identified in the prior session: `/mnt/data/d1_work`; source archive: `D1_D2_S6_BUILDER_SOURCE_BUNDLE.zip` (SHA-256 `caa5d6d72cdc8588de104f24aa23499e85912921bce9a509e27e10e909d74dc6`, 50,734 bytes). These are local evidence only and are not repository files.
- Current GitHub connector actions available in this execution expose text-content writes and Git object creation, but no direct local-filesystem-to-GitHub binary upload bridge. Do not claim source publication or D1/D2 closure until the exact local bytes are committed, fetched back from GitHub, SHA-256 hashed remotely, and tied to the commit.
- Stage D validation workflow runs on the authorized branch: none observed in the live run listing. The local workflow file is not present in the repository tree.
- Next action: establish a supported binary/source transfer path or a user-authorized upload bridge for the existing source archive; then publish source files, run only the no-simulation D1/D2 validation workflow on exact HEAD, commit generated shared model and registry, verify every committed output by remote bytes + SHA-256 + commit, and stop before D3.
- No D3–D6 work is authorized by this checkpoint. No simulation, Trial, Monte Carlo, N=4800, main update, PR, merge, or Release was performed.


## Task result — 2026-10-31 18:02 UTC (stop point)

- Latest live Stage D branch HEAD after the D0 closure provenance correction: 5c5faca3ca018816950a9034c046405bde6480f3.
- main remains c6e54349a5e94f65d5aa9f83141f225d777bb474.
- D0 closure record was corrected to use current remote-byte hashes for the D0 audit Markdown, D0 audit JSON and continuity document. The D0 closure record itself is committed at the branch HEAD and its own remote-byte SHA-256 is recorded in the response that performed this update.
- D0 remains scoped closure only; pinned artifact byte checks were from the prior local audit and were not re-downloaded in this update. The historical 48K gaps and all known conflicts remain open.
- D1/D2 were not closed. The exact source files, tests, workflow and Number Registry remain absent from the repository tree; local implementation and test claims remain REPORTED_ONLY. No Stage D Actions workflow run exists.
- The local-to-GitHub binary/source transfer is still the blocking dependency. Do not attempt D3–D6 until source publication, exact-head validation, registry generation/commit, and remote-byte SHA-256 + commit verification are complete.
- Stop condition honored: no D3–D6, Trial, Simulation, Monte Carlo, N=4800, main change, PR, merge, or Release.
