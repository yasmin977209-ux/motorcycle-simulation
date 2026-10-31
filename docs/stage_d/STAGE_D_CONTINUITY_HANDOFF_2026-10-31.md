# Stage D continuity handoff — 2026-10-31

**Repository:** `yasmin977209-ux/motorcycle-simulation`  
**Authorized work branch:** `tmp/cp-v240-stage-d-s6-deliverables-20261030`  
**Branch HEAD at handoff creation:** `6bfe3e50ec9d87c3fd0050e23895c78544aca9db`  
**main:** `c6e54349a5e94f65d5aa9f83141f225d777bb474` (unchanged)  
**Classification:** `T2_INTERIM / NOT_FINAL_BLOCKED`

This addendum is the current handoff for the D0-D2 continuation. It supplements, and does not rewrite, the historical `docs/PROJECT_CONTINUITY.md`.

## 1. Current stage dispositions

| Stage | Disposition | What is proven | What is still missing |
|---|---|---|---|
| D0 | `COMPLETE / PASS_SCOPED_WITH_LIMITATIONS` | Three pinned GitHub artifacts downloaded again from GitHub; byte SHA-256 and size match; ZIP CRC/path checks pass; D0 audit and closure documents have live GitHub links and remote-byte hashes | Parquet schema/row parsing remains limited unless run with a Parquet reader; 48K historical daily accounting gap remains |
| D1 | `BLOCKED / REPORTED_ONLY` | Local extracted source tree; local compileall pass; 27 local unit tests passed; local Builder integration produced 125 role assignments, 105 unique keys and 105 manifest resolutions | Source modules, tests and workflow have not been committed individually to GitHub; no exact-head GitHub Stage D run |
| D2 | `BLOCKED / REPORTED_ONLY` | Local Number Registry has 13,954 entries, 13,946 VERIFIED_LOCAL, 8 REPORTED_ONLY, 10 unavailable-evidence records, 1 missing source digest, 0 duplicate IDs and 0 float values | The registry file itself is local only; no remote GitHub file URL/SHA-256/containing commit triple; no exact-head GitHub test run |
| D3-D6 | `NOT_STARTED / NOT_VERIFIED` | No claim of completion | Excel, DOCX, ZIP bundle, SHA256SUMS, independent Post-Write Audit and exact-head delivery validation |

## 2. D0 remote evidence

The three pinned artifacts were downloaded again from GitHub Actions and rehashed from the downloaded remote bytes:

| Input | Artifact / Run | Tested SHA | Size | SHA-256 |
|---|---:|---|---:|---|
| S6 N=2400 aggregate | 12852969854 / 40773412377 | `4f2f2cc16d0cb5125262088704febccbae6f50ed` | 9,357,996 | `ec05a69ae8968585decf83cf0716d56c264f47f86187cfd3cf53b11f52ca2e54` |
| S6 Full Logging | 12998778418 / 41098699740 | `e3c2098df9fc5dbc126eb1e77ad35c493ff3ac70` | 310,827,203 | `403371cc8eb12880dda05529b4c83dd675bfa609e8680c09d35efa729c5b5aeb` |
| C100 reuse | 12630457193 / 40263424595 | `24050f15bc7eb3097e20f76785a45c5d177643dd` | 361,733 | `c977d1cbb5204919eadc72358533f77cdbbc239902bcd6f921bf1a915a716e79` |

- [D0 Remote Evidence Ledger](D0_REMOTE_EVIDENCE_LEDGER_2026-10-31.md) — remote content SHA-256 `4ba3a30daeedaa200a6e78b96e4787ee69d23a34ef5f3325602563a34008ad3d`, Git blob SHA-1 `2b008cb1bf71cfce6bd27172c6673e8ac44d0562`, containing commit `89e66beca2b5320c9b5c383fd4c8585fa3be04b9`.
- [D0 Repository Closure](D0_REPOSITORY_CLOSURE.md) — remote content SHA-256 `e9f6a5d49460ab55f15add7ea7ce31244494639712d6bd93801610d847dfb1c5`, Git blob SHA-1 `783170d66f387b946a5b495a836d976377bbb8a1`, containing commit `66ca5c7e5310a0bf9ba37564ce6e94851c790b37`.
- [D0 Input Audit Markdown](D0_INPUT_AUDIT.md) — remote SHA-256 `1064e81dd98ddaefd443389a5bbc6d53fc1052903328d533839da84a16f705a0`, blob `7dcdcd9fbc7244f9cb98bdb42ea889abc9899950`, containing commit `cd97dca1f982f9d9220bd335b478c085ec85c679`.
- [D0 Input Audit JSON](D0_INPUT_AUDIT.json) — remote SHA-256 `abe8482b44b78de950c33c9b1b38480e90e08b2563f184acf70695036b17aa80`, blob `02e250c9b3ac493e7ff9543c2c8ebe185a319801`, containing commit `d087e4eb951ced0efee4c910b690c712ab26a126`.

For the remote repository documents, SHA-256 was calculated from GitHub-fetched UTF-8 content and the Git blob SHA-1 was independently recomputed and matched the GitHub blob ID.

## 3. Local-only D1/D2 work — do not call this GitHub-published

The original source ZIP is only a transport container and should not be committed as a final deliverable. Its 15 extracted members are listed below with SHA-256 values calculated from the extracted local bytes. These hashes are local evidence only until the individual files are committed and read back from GitHub.

| Extracted file | Local bytes | Local SHA-256 |
|---|---:|---|
| `scripts/s6_deliverables_builder.py` (patched continuity pins) | 22,629 | `c3ab20c81da559f7c712e05302b1cda5990bdf05ebe2456d2bccd713a8bfcabe` |
| `scripts/s6_deliverables_model.py` | 3,209 | `568c5c52be1c4399a849f617d919371126320af59aea7aa5369849d445f25891` |
| `scripts/s6_artifact_reader.py` | 10,182 | `def740f8bfcbebafc4a45dc2425b18c3c56e3bc2ba67dc5a7a3af0eb81e693f2` |
| `scripts/s6_manifest_resolver.py` | 5,143 | `f10fbcccb35445a1866d1ce0fed1d9da9c9cdd307e01507f13dea1d1f34c3d01` |
| `scripts/s6_number_registry.py` | 50,187 | `b1e6ad46e6bbaf96bcc426eedd823f5884ba9307b2eb2809c464ee54e738feef` |
| `scripts/s6_validate_representatives.py` | 7,669 | `4af0bdd060fe96680508abf7163ebd1a8367d186f7af06e002b3fa319ed8a213` |
| `tests/test_s6_deliverables_builder.py` | 8,529 | `7bd595fedbb27b79c53319881a93d2a069f6f34aff6f8140f78bd31c64f26407` |
| `tests/test_s6_number_registry.py` (patched continuity pins) | 9,661 | `4c179fa98ce06ea439be9abb1e4ee062d1eeaea1a17e50910240ce4b8628f079` |
| `.github/workflows/stage-d-deliverables-validation.yml` | 1,158 | `5b089da7946bf70533e6f873241b13e37473cb526b80b5c4afae2f528d3980fa` |
| `docs/stage_d/D0_REPOSITORY_CLOSURE.md` (old bundled copy; do not overwrite live corrected closure) | 3,323 | `45487b8cb6cd13de01d98ed28c02e23cd9a9683e994beef216b41661c369a5e1` |
| `docs/stage_d/D1_BUILDER_DESIGN.md` | 8,921 | `510e4b447ddae15551115f33ff087911f0cda291cb2637f1f2021bc8cc54d922` |
| `docs/stage_d/D1_BUILDER_AUDIT.json` | 3,581 | `6aaaed609e958d5b760fefab668996ca1874b55ba1f81fcda4dbd6b0bd32983f` |
| `docs/stage_d/D1_REPOSITORY_CLOSURE.md` | 2,836 | `3439b9c7fbc71511e9df939ac597010af9b1b42dbb1cec996cffe3c8fb00a361` |
| `docs/stage_d/D2_NUMBER_REGISTRY_AUDIT.md` | 8,326 | `f2f46a2c37d335887ed2e12af50eecc4949b8ceea02082f0af55667c104fe683` |
| `docs/stage_d/D2_NUMBER_REGISTRY_AUDIT.json` | 4,912 | `de940ad23227ebbbc3557e30c12413d6befed86449797a320c816ca5a2a58610` |

The source archive itself is `D1_D2_S6_BUILDER_SOURCE_BUNDLE.zip`, 50,734 bytes, local SHA-256 `caa5d6d72cdc8588de104f24aa23499e85912921bce9a509e27e10e909d74dc6`. It is intentionally not a final repository member.

Local generated outputs:
- `S6_D1_shared_model.json`: 4,387,332 bytes; local SHA-256 `3c484ddead389e43a4da778a22e233448786ae09869e5a6737b9f53a3655b3a7`; 125 role assignments, 105 unique keys, 105 manifest resolutions, all 105 normalized statuses `NOT_VERIFIED`.
- `S6_D2_number_registry.json`: 22,781,475 bytes; local SHA-256 `53ece080e0eeea1feefbdac3727997deece17670bff4ac8539ea01562a12af73`; 13,954 entries, 13,946 `VERIFIED_LOCAL`, 8 `REPORTED_ONLY`, 10 unavailable evidence records, 1 missing source digest, 0 duplicate IDs, 0 floats.
- `D0_trial_manifest_reconciliation_105.csv`: 83,949 bytes; local SHA-256 `e2653552868606cbf905c84c379a16fb63be3972ce2426e2a8cee2a9a9b153e7`.
- `01_EXECUTIVE_AND_CONTINUITY_REPORT_AR-1.md`: 22,715 bytes; local SHA-256 `01eb871fd9356e2c2ff6cb40d9632f64f5b3f7cf855788c53c63665ec6b2c16f`.

Local validation performed:
- `python -m compileall -q scripts tests`: passed.
- `python -m pytest -q`: 27 passed.
- Builder integration on pinned local artifacts: 125 assignments, 105 unique keys, 105 manifest resolutions; normalized status remains `NOT_VERIFIED`.
- No Excel, DOCX or delivery ZIP was generated.
- No Trial, Simulation, Monte Carlo or N=4800 was run.

The local Builder and test source were patched to use the current live continuity-document hashes:
- continuity SHA-256 `b844682d2a600814fdd65dda6c287160ed46d38af4fbf557c57bf88e96d80be4`
- Git blob SHA-1 `abbc4909feacba26055d0c6db703d0ec5b963ea5`

The bundled D1/D2 docs and pre-generated JSON outputs contain earlier source pins and must be regenerated or corrected; do not publish them unchanged.

## 4. Transfer blocker and no-repeat solution

The ZIP is not required on GitHub. The required final repository state is the extracted individual source files, tests, workflows, and generated JSON outputs.

The current chat environment can:
- read/write small UTF-8 files through the GitHub connector;
- download GitHub Actions artifacts into the local analysis environment;
- fetch repository text and calculate SHA-256 from the remote-fetched bytes.

The current chat environment does **not** expose a direct filesystem-to-GitHub upload bridge for arbitrary local files in `/mnt/data`. GitHub Contents API write tools accept complete text content, not a local file path or a local attachment ID. Therefore the local 50KB source archive and 22.8MB registry have not been transferred. A temporary write-enabled bootstrap workflow was explored but removed before any trigger; it is not present on the branch.

Do not claim D1/D2 source publication. The next safe transfer options are:
1. Use a one-time local Git clone/import script (the script should extract the source container, apply the current continuity pins, regenerate shared model and registry from the three GitHub artifacts, commit individual files to this authorized branch, and calculate remote readback hashes); or
2. Use an approved file-transfer mechanism that exposes the local extracted files to GitHub Actions.

After the one-time import, all future chats should use GitHub only; no repeated artifact or source-package uploads should be necessary. The three large input ZIPs remain immutable GitHub Actions artifacts and can be downloaded by their pinned IDs in CI.

## 5. Non-negotiable project constraints

- Governing decision v2.4.0 SHA-256: `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`.
- S6 historical execution reference v2.3 remains separate from current governing reference v2.4.0.
- S6 source/cohort/seed remain unchanged.
- C100 remains `CROSS_COHORT_DETERMINISTIC_REUSE`; never mix it statistically with S6.
- Stage 12/13 remains separate historical lineage.
- Gate A financial fingerprints: `PASS_SCOPED` only.
- Production-wide Gate A: `NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS`.
- Gate B N=2400: `FAIL_SCOPED`, 10 PASS / 10 FAIL.
- Stability: `NOT_CONVERGED`, 0/60 transitions.
- N=4800: `NOT_EXECUTED`, not authorized.
- Do not backfill the five missing accounting fields.
- No main changes, PR, merge, release, Trial, Simulation, Monte Carlo, or final acceptance.

## 6. Next action

D0 is closed. D1/D2 remain blocked until the extracted files are committed individually and fetched back from GitHub with the required URL + remote-byte SHA-256 + containing commit triple. Do not begin D3 until D1/D2 are closed.


## 7. Live repository tree correction — verified after initial handoff draft

A recursive Git tree read at branch HEAD `0e4ecf25d868f2a77febffbb0422f6c1dd4c2465` found three S6 modules already present, but their remote SHA-256 values do **not** match the corresponding local D1/D2 source-bundle files. They must not be silently treated as the same source or overwritten without a source-level diff.

| Existing GitHub file | Remote SHA-256 | Git blob SHA-1 | Containing commit | Corresponding local D1/D2 source SHA-256 | Comparison |
|---|---|---|---|---|---|
| `scripts/s6_artifact_reader.py` | `c61b30efd2e9cf10ef64bace5d919afc44dc57049ae35e20bac8e855d9b328ba` | `35e644e22557eb6f3449571190c1c31e2af3d461` | `2ef20e9634d346d3b5a263f474a613415b47b996` | `def740f8bfcbebafc4a45dc2425b18c3c56e3bc2ba67dc5a7a3af0eb81e693f2` | `CONFLICTED` |
| `scripts/s6_deliverables_model.py` | `9d7bd49178d362d988cbca1d78d6736b3cdeab9bcb39435f5163729e5f336da7` | `670c10d39adcc732fe464437c1bf02f451b76f26` | `15e5a49fc1ff96d7106506103e1d35ee164879e0` | `568c5c52be1c4399a849f617d919371126320af59aea7aa5369849d445f25891` | `CONFLICTED` |
| `scripts/s6_manifest_resolver.py` | `09396173a7ea7cddbce47d892580e9393b271b84b13558f554c920147fdeae19` | `55ba5e5f0657d2b5337af84eff6a01e3749f5491` | `61532b9230f3162eb2f6cb0fa0da2ddbfe1a0dd9` | `f10fbcccb35445a1866d1ce0fed1d9da9c9cdd307e01507f13dea1d1f34c3d01` | `CONFLICTED` |

The following D1/D2 files were confirmed absent from the live branch tree at that check:
- `scripts/s6_deliverables_builder.py`
- `scripts/s6_number_registry.py`
- `scripts/s6_validate_representatives.py`
- `tests/test_s6_deliverables_builder.py`
- `tests/test_s6_number_registry.py`
- `.github/workflows/stage-d-deliverables-validation.yml`
- `results/shared_model.json`
- `results/number_registry.json`

The existing D1/D2 documentation files are present, but their prior statuses remain non-closing evidence. The live tree correction overrides any broad statement above that all three existing modules were absent. The current accurate state is: 3 existing but content-conflicted modules; 3 missing core modules; 2 missing D1/D2 test modules; the original bundled workflow `stage-d-deliverables-validation.yml` is absent; the new persistent `stage-d-d1-d2-validation.yml` is present; generated shared model and Number Registry are missing. The canonical v2.4.0 normative reference text is also not yet present in GitHub; only the owner decision document is present.

No source overwrite was performed. No workflow was dispatched. The temporary write-enabled source-import workflow was deleted before any trigger.


## 8. One-time source and governance-text import path now published on GitHub

To avoid repeated uploads in future chats, two repository tools are now available:

1. `scripts/import_stage_d_sources.py` — one-time local import helper. It verifies four already-provided input archives by SHA-256:
   - D1/D2 source container: 50,734 bytes, SHA-256 `caa5d6d72cdc8588de104f24aa23499e85912921bce9a509e27e10e909d74dc6`.
   - v2.4.0 governing-reference archive: 14,507,701 bytes, SHA-256 `efb6a663a2fc63ac5c1f052048b3dfc945e233df9810d4fe0b21b892c533e52c`.
   - Historical source pack: 366,034 bytes, SHA-256 `4facbc9ed00cbbbaede83bfc65b8cdc8f0b335eabe13579f185b95a12a46ce5a`.
   - D0 local text evidence (105-manifest reconciliation CSV + executive continuity report): 22,706 bytes, SHA-256 `b155d74bca7d16970dea06f77b876b2a97bcf6d240d21028234da07109a36fd2`.

   It extracts the six S6 source modules and two test modules as individual files; extracts the text/Markdown/JSON/CSV files from the v2.4.0 and historical source archives, including the nested owner starter pack and quarantined v2.3.1 text; does not commit any ZIP or binary artifact archive; verifies the exact governing reference SHA-256 `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`; preserves v2.3 as historical and v2.3.1 as quarantined; writes `docs/governance/ARCHIVE_IMPORT_MANIFEST.json`; patches the current continuity pins; commits each extracted file individually; and pushes only the authorized Stage D branch.

2. `.github/workflows/stage-d-d1-d2-validation.yml` — persistent GitHub Actions workflow. It triggers when the eight source/test files are pushed (or can be dispatched on the authorized branch), downloads the three pinned large artifacts directly from GitHub, verifies their remote bytes, installs pytest and PyArrow, runs the tests, builds the shared model and Number Registry, validates the frozen representative mapping, commits the generated JSON outputs and audit documents, reads the committed files back from GitHub to compute remote SHA-256 and Git blob SHA-1, records the evidence ledger, reruns tests on the exact final commit, and uploads the evidence artifact. Its remote-readback step also includes every text file listed in the archive import manifest and guards the canonical v2.4.0 reference hash.

The four input ZIPs are containers only and are not final repository deliverables. The importer writes extracted files into GitHub; the large aggregate, Full Logging and C100 data remain immutable GitHub Actions artifacts and are downloaded automatically by the workflow.

**Not yet executed:** the helper has not been run against a local clone, and the new workflow has not been triggered. The v2.4.0 normative reference and the extracted governance text archive are therefore not yet on GitHub. The six source modules/two tests and generated model/Number Registry are also not yet fully published. D1/D2 remain `BLOCKED / REPORTED_ONLY` until the one-time import is executed and the workflow run completes with remote-byte readback evidence.

One-time command from a clean local clone of the authorized branch, after authenticating Git push credentials and using the four existing local archive files:

```bash
python scripts/import_stage_d_sources.py \
  --source-zip /path/to/D1_D2_S6_BUILDER_SOURCE_BUNDLE.zip \
  --governing-reference-zip /path/to/MOTORCYCLE_SIMULATION_GOVERNING_REFERENCE_V2.4.0_CANDIDATE_2026-10-30.zip \
  --historical-source-pack-zip /path/to/MOTORCYCLE_SIMULATION_SOURCE_PACK.zip \
  --local-evidence-zip /path/to/STAGE_D_LOCAL_TEXT_EVIDENCE_2026-10-31.zip \
  --apply
```

This is a one-time import only. Future chats should use GitHub and the pinned Actions artifacts; they should not need these archives attached again.


## Corrected continuity and D0 remote triples — 2026-10-31

- Current docs/PROJECT_CONTINUITY.md: SHA-256 b844682d2a600814fdd65dda6c287160ed46d38af4fbf557c57bf88e96d80be4; Git blob SHA-1 abbc4909feacba26055d0c6db703d0ec5b963ea5; containing commit 36e186a2f5d2dbf2d67749ed5a75a3912f0b9f5f; 445,430 bytes. Its authority block now correctly names v2.4.0 225de... as current governing reference and ee277... as Stage 12/13 historical only.
- Current D0 Repository Closure: SHA-256 e9f6a5d49460ab55f15add7ea7ce31244494639712d6bd93801610d847dfb1c5; Git blob SHA-1 783170d66f387b946a5b495a836d976377bbb8a1; containing commit 66ca5c7e5310a0bf9ba37564ce6e94851c790b37.
- Current D0 Remote Evidence Ledger: SHA-256 4ba3a30daeedaa200a6e78b96e4787ee69d23a34ef5f3325602563a34008ad3d; Git blob SHA-1 2b008cb1bf71cfce6bd27172c6673e8ac44d0562; containing commit 89e66beca2b5320c9b5c383fd4c8585fa3be04b9.
- The former continuity digest 745872... and historical-reference mislabel in section 2 are superseded. Importer and workflow now calculate continuity digests dynamically; no fixed digest should be manually copied into a future source build.


## Final SHA-256 validation note — 2026-10-31

The intermediate continuity digest 5c0dbe96806f8a7a268b4516eee9cb523fb83268429c528612af7ca0ad0780d6 was superseded after the SHA-256 implementation was checked against both the standard abc vector and the 1,000,000-byte a vector. The verified current remote SHA-256 is b844682d2a600814fdd65dda6c287160ed46d38af4fbf557c57bf88e96d80be4 for 445,430 bytes. The Git blob SHA-1 abbc4909feacba26055d0c6db703d0ec5b963ea5 and containing commit 36e186a2f5d2dbf2d67749ed5a75a3912f0b9f5f are unchanged.
