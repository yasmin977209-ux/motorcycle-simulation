# CP — Stage 13 representative payload coverage: read-only contract audit

**Date:** 2026-10-19  
**Mode:** R4/read-only data-contract inspection. No source, data, test, Workflow, or workbook changes.

## Live evidence

- Main HEAD before the accidental report commit: `647c19826b90d8224ce73ef9b90c306a45e03fb0`; current observed main HEAD after that one-file commit is `b70cc0b7517b4f5f8a559b035bea166059b269ea`.
- Main `docs/stage9a/dataset_manifest.json` blob `e796fa2443493b607f1f9c60b58eb63607959c26`: `total_trials=9005`, `total_representatives=100`, 25 scenario keys, source SHA `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`.
- Main `scripts/excel_builder.py` blob `50115a2fea5812727e0e5a8bfbb07e1f853f026b`, `write_representatives` reads only `P10`, `P50`, `P90`, and `Loss` payloads for each scenario. This is four roles × 25 = 100, matching the manifest count.
- Candidate `tmp/cp-stage13-excel-compat-20261017` HEAD `4fa2c633162b0134a48cfc2ccbf2b6b948108ae0`, assembler blob `7561f73340ac45b0f4ab71b677c33b771eac008b`, builder blob `8dec3578a8221a6b12fb0915103cb09664f20a96`.
- Candidate `load_dataset` attempts five role payloads for every non-demo scenario, including `Max Case`; when a scenario has nonempty trial rows, a missing role causes load failure. Candidate `_validate_representatives` likewise requires payload and daily rows for all five roles.

## R4 / contract assessment

The candidate implements the later normative decision D-2026-10-10-03 to add the fifth `Max Case` role, while the source dataset manifest and legacy builder are shaped for four roles. The main manifest is not an inventory of the actual per-scenario archive members, so `total_representatives=100` alone does **not** conclusively prove the archive lacks `Max Case` JSONs. The source package/archives and their identities were not available to inspect through the current GitHub file path, and no canonical dataset was downloaded, rewritten, or rebuilt in this CP.

Disposition: **`MISSING_EVIDENCE / POSSIBLE_SOURCE-CONTRACT_MISMATCH`**, not a proven runtime failure. Canonical Stage 13 acceptance remains blocked until the actual source package verifies that all 25 × 5 role payloads exist with expected summary/trial IDs and daily records, or a separately approved, identity-preserving derivation path produces the required fifth role using existing trusted evidence. Do not reduce the five-role requirement to match the old manifest; do not invent daily payloads or rerun trials.

## Constraints / next step

No canonical workbook was built; no pytest, CLI, production workflow, Monte Carlo, Trial, Checkpoint, or new artifact was run. No source SHA, seed/RNG, sampling, cohort, trial ID, historical data/Parquet, or reference changed. `state.json` blob remains `2178260bb18efeb81437486f13b6d10cf5e85936`, with `12-CLOSED / FINAL_DELIVERY_BLOCKERS_OPEN`. No PR was merged/closed and no Release was created. The candidate's runtime test authorization remains conflicted; the older Run `38995349182` applies only to its older SHA and does not verify current HEAD.

Next permitted step is an existing-input inventory: obtain/read the exact canonical enrichment artifact and hash, enumerate its members, count representative payloads by scenario/role, compare each summary `trial_id` to the approved representative assignments and the trial result cohort, and record missing daily records. No rebuilding or data mutation is required for that inventory.

## Note on repository write boundary

An earlier attempt to save this audit omitted the target branch argument and unexpectedly created this file on `main` in commit `b70cc0b7517b4f5f8a559b035bea166059b269ea`. The before/after compare returned exactly one added path (this audit file); `main/state.json` blob is unchanged. This was an unintended write. No additional action on `main` will be taken absent the separately required owner authorization to remove/revert that single documentation file.

## Addendum — source-package role count confirmed in main deviation record

A subsequent read of main `docs/stage9a/DEVIATIONS.md` (blob `ac8fb3e2dc65816bb2329aab19d4fe3c88d885d6`), line 25, states literally: “The enriched scenario artifact contains `trial_results.parquet`, `daily_distribution.parquet`, four representative JSON payloads, and fingerprints; it does not contain an individual daily accounting ledger for all trials.” This moves the fifth-role finding from merely a count-based possibility to a **documented source-contract gap**: the approved Max Case role was added after the artifact package contract that contains four representative payloads.

Candidate `load_dataset` iterates `P10`, `P50`, `P90`, `Loss`, and `Max Case`; missing payloads for a populated non-demo scenario are fatal, and representative validation also requires a nonempty daily record. The current source package description expressly supplies only four representative payloads. The candidate therefore cannot claim complete canonical five-role input coverage from the documented enriched package contract as-is. This is a source/input-contract mismatch, not proof that a particular artifact byte stream has been opened in this session; no zip containing the 25 current enriched packages was available for member-level enumeration.

**Updated disposition:** `INPUT_CONTRACT_MISMATCH_DOCUMENTED / MAX_CASE_PAYLOAD_MISSING_FROM_SPECIFIED_FOUR-ROLE-PACKAGE_CONTRACT / CANDIDATE_CANONICAL_BUILD_NOT_VERIFIED`. The approved fifth role must be produced from an identity-matched, already-authorized source of the selected trial's summary and full daily accounting, or a separately approved data-contract decision. No representative trial IDs are changed, no missing daily rows are synthesized, and no historical trials are rerun here. The Stage 13 candidate's exact-branch workflow authorization conflict remains in force.

## Artifact-level verification — all 25 canonical enriched packages opened read-only

This addendum replaces the earlier “source package was not available to inspect” gap. The exact 25 artifact IDs in main `docs/stage9a/dataset_manifest.json` blob `e796fa2443493b607f1f9c60b58eb63607959c26` were downloaded using the read-only GitHub Actions Artifact API and compared to their manifest scenario mapping. No artifact content was modified and no workflow/trial was started. All 25 outer ZIPs opened; every archive contains the scenario-matching `.tar.gz`; every inner tar was readable and had 10 entries. Each yielded the same four representative JSON roles, plus `trial_results.parquet`, `daily_distribution.parquet`, `trial_fingerprints.json`, and `scenario_metadata.json`. None contains a fifth Max Case JSON or individual full daily-accounting ledger.

The first archive `C030_G030` also independently matches earlier canonical evidence: outer ZIP SHA `9331c726560471f3092b2c61893a7ad87f3bafed363217249b6f4a992c029c07`; inner TAR SHA `a2403a9175ef85ec30663fbdb7ecd322c88beaf9672e1b73b30488312cd4aa10`.

| Scenario | Manifest artifact ID | Outer ZIP SHA-256 | Inner TAR SHA-256 |
|---|---:|---|---|
| C030_G000 | 11498686202 | `6e3ac626f51e9bc69579a231d2717b328f1d7db186279f102a64c993d1ac4d6e` | `00b32a9cf4851dd6cb49a201bb1118f37bb0b9892cf24c252ab2e458e5261399` |
| C030_G030 | 11497409735 | `9331c726560471f3092b2c61893a7ad87f3bafed363217249b6f4a992c029c07` | `a2403a9175ef85ec30663fbdb7ecd322c88beaf9672e1b73b30488312cd4aa10` |
| C030_G050 | 11498069095 | `ee01014a40a60f23bdb815fcd7f19a1e472ed8256916ed21eae4ad43ff8d03bf` | `622441467daaba9be03b3d37b59d662ffa2aa2f9fb07949a3fab0c895a4a0448` |
| C030_G070 | 11498204610 | `bfe9467b74977778c33b29bf51f20278097585028d5574f3c282ad403e6300f6` | `87024e27e9809872e5a2a9a75690b8916db64284e665f917e461fa1c000f97e2` |
| C030_G100 | 11498980727 | `34352f4872824d94edbb0cb5669a42f2f416b2f9be9ee2756d84a63ec608e9dc` | `949892496781fe29312266a529d11cdacabfae10c8f60be4f0512ab38837a595` |
| C050_G000 | 11503191706 | `f575044fb6a50cb5ed71d6303c40bd77841a6d38b633c105e560a4731e0a94f9` | `19878404d3cb0f7c91dd69e7cd09a79b5267b96b5b91ed0f7bb24d37b4c6e892` |
| C050_G030 | 11499677773 | `f948c1c254c5df8430126c36316d8eb29b935e11d8521afa609b0b180042162f` | `129ee06ca9fe818a6526bd985ab189f6ddc30a0ef3955319c08e29b9f75a6d5b` |
| C050_G050 | 11502991608 | `572275afb436fc20fc5606b27379d093296012a6ff427c29ee22ddd786b2b1c1` | `6780e2dc0343be778afe13dc2f1f3e1d609b5ca1c2bf32fe984caeb7f9d5b153` |
| C050_G070 | 11503357996 | `c4a3487ad69c00d68cad7f04b138ebf005b5d2df92d988c20cc941ffb2c8ead6` | `f8f6885f57a7bef0e896e0bcb5c346d4ced504cac7fa954688f02287d29b4019` |
| C050_G100 | 11503961628 | `5c76239f5072d1fdb12af98413812a42df204df3e80a7d853f48aaca0574e866` | `2563d004a216baa60a51afa9dba6ac9551aaf6e5ffccc66f6cfe1dc3f95b7703` |
| C070_G000 | 11500301100 | `285a9a1ac27fc68685842539871cbc5c6e59599c38ceb9795d483b09cc65fb42` | `84da417ae078a3c6c815d7df889be2c18c7af5fabd457c58082647b8fa5ef6c1` |
| C070_G030 | 11499331345 | `67550dc7d33f4462fdbe07c10cb0e473907ad003145438e7f901d1a4cd072823` | `14a3a51685df7d09f78b970c083645ae960da7fd1d183139c18b1ce5b25c51a5` |
| C070_G050 | 11498901762 | `a072fbfda165c1a2bb8b67db61dca22da1f09fe6232741aa4d0164bc6097d0b1` | `920331e9896847ae7bba47fafc626135ac766a7a1c8be3d59f2cc77d5eb67dc2` |
| C070_G070 | 11499668344 | `5a59d72fee4bac2d39a9e607cef479b6827422f693332fe260432d9d8501138d` | `af5d4395bd319849845a5d986cd543dfe469f292c9d4735fecdde54156bff590` |
| C070_G100 | 11499938620 | `a9f44e74051fcbc6fb64525cae6b7dc3626fbee27b2d600f4bd14e0ed1d167d5` | `a7de7950f3e460816117885c0255c867670130a4b7ca83cf37027187e916b768` |
| C085_G000 | 11499442661 | `f58ff1147a581da08c329bcb0057d8f243871edacd8a994fd4f72e5ddc95d3e6` | `d61c125c4dc829720b207c36b7a3206fa58ac2ea57dec71b4fd4dfb2d1898802` |
| C085_G030 | 11499958237 | `96445d3d6f9ab901b114a262c0349274964793e6ec9979057285eb0c58a4d0aa` | `ef4bc299db5c77bbe35ea5239c1eab7f384425d7a178d1f36598736515616c4b` |
| C085_G050 | 11498784380 | `92aa2c3a498c3c2cb1c731fabc7bc0ed86cf6d541f6396f4daa3ec904238ec44` | `37e2f4bc8e8517fd635ae7179d0ed7b701210cde9e6f2cf30e20a8daa26ae4b7` |
| C085_G070 | 11498798098 | `62646de661459bbafc51d0c7427a6a837f4ea8a304c402d8ecb4509bbae026a0` | `cd185a65087a214da46cafb8b490f3fbf4552b1d6c29af2aad79abed1934f61f` |
| C085_G100 | 11499553926 | `c6a1e11f8c7e749b2a8ee38e393ec2e86ae306d57b570bb3cb49d3a96c1c76a6` | `21e2b914ce3da1bc477ab9c76f6e60dce3c28097e9c9cd3ba6fe0c62400c88ae` |
| C100_G000 | 11496939782 | `fc888978f92ed963c35774cb471dedd93d71ecc335c6fe1b765d897468821c16` | `1d6d1927cb138b6914fe811f9a5110c165c03ff8e028422b800ddc704f227686` |
| C100_G030 | 11497898524 | `66aee1cdd7829c25c8b5800b74a69a241eeddee6b90e657c23e0ccd68049ec12` | `fe8f8ae4f30653627119c70cbf8a9ef3e9828931b1b1ffc3450156853c679366` |
| C100_G050 | 11497164787 | `61a90c9b0ca28ad7dc2943412822f3df99f4f5797bbb460343194cf5e28aadd8` | `ff5ecb311b4b4113acabe562a46b760e32c29d10097dd209c462897e930cb9bd` |
| C100_G070 | 11497369182 | `3e6fccb33b4892f2b1f46b91d3781e4723d3914e9273f6e71bd605fc3895db3f` | `b3a6cfdace20c522a0a03adfddc315093293fce62842ff66543648da74d11c1f` |
| C100_G100 | 11498636066 | `05a2c44bcd2f4af5ef613ba2f97ba7d7f6fa289404552394df6952f0a65f680d` | `d578a074b78e72778d75e73924a65d6c04b02644c9d37217c0dff7c9d6a33d0a` |

### Formal conclusion from the 25-package inventory

- Verified package count: 25/25 manifest-listed scenario artifacts; every artifact ID matched the manifest mapping used for download.
- ZIP and inner TAR readability: 25/25 passed; all 25 inner TARs contain 10 entries and a scenario-specific archive name.
- Trial data/identity support members: `trial_results.parquet`, `daily_distribution.parquet`, `trial_fingerprints.json`, and `scenario_metadata.json` are present in 25/25.
- Representative role coverage: exactly four JSON roles `P10`, `P50`, `P90`, `Loss` in 25/25; no `Max Case` payload in any package.
- The archive member `daily_distribution.parquet` is not an individual full daily-accounting ledger for every trial; this remains explicitly stated in `docs/stage9a/DEVIATIONS.md` and `docs/stage9c/STAGE9C_REPORT.md`.

Accordingly, the candidate's five-role canonical Stage 13 input contract is **PROVEN INCOMPATIBLE with the 25 currently published enriched artifacts**. This is now `INPUT_CONTRACT_MISMATCH / BLOCKED`, not merely missing evidence. A valid correction must be owner-approved and identity-preserving, using trusted existing trial rows plus a complete approved daily accounting source to generate the fifth representative role, or an explicit governance decision must revise the contract. This audit authorizes neither derivation nor a change to D-2026-10-10-03. No trial was rerun and no source artifact was changed.

