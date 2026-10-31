# Stage D Session Status — 2026-11-01

Repository: `yasmin977209-ux/motorcycle-simulation`  
Working branch: `tmp/d1-rebuild-20261101`  
Classification: `T2_INTERIM / NOT_FINAL_BLOCKED`.

## D1 source reconstruction
The six S6 source modules and two focused test modules were rebuilt and published individually. The importer was not run. Previous versions of the artifact reader and shared model were preserved byte-for-byte; the previous manifest resolver is preserved as exact UTF-8 base64 and remains in parent history.

Local Builder integration from the three pinned GitHub artifacts: `VERIFIED_LOCAL`; 125 role assignments, 105 unique keys and 105 trial records (100 S6 + 5 C100). All 105 normalized manifest statuses remain `NOT_VERIFIED`. Local Parquet value revalidation remains `NOT_VERIFIED` because no local Parquet reader is installed.

GitHub workflow `.github/workflows/stage-d-d1-d2-validation.yml`, Run `41244813966`, succeeded at tested commit `c17b6f68ba5b5eb585cf78ef81700a9512b6a960`: compileall passed; 10 tests passed and 8 artifact-dependent integration tests were skipped because the pinned ZIPs were not mounted in the source-only workflow. This run is not the final branch HEAD after subsequent evidence/documentation commits.

## Governing reference
The uploaded v2.4.0 archive was CRC-checked. Its normative Markdown member is 401,397 bytes and SHA-256 `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`, matching the live GitHub owner decision `APPROVED_BY_OWNER`. The complete file is locally verified but not yet present at required GitHub path `docs/governance/MOTORCYCLE_SIMULATION_GOVERNING_REFERENCE_V2.4.0.md` (`MISSING_EVIDENCE`).

## Preserved limits
S6/C100 identities and frozen selection unchanged. Full Logging remains 105 representative keys only, not 48,000 trials. Five missing historical accounting fields remain `MISSING_EVIDENCE`. No Trial, simulation, Monte Carlo, N=4800, D2 registry output, Excel or DOCX was produced. D2-D6 not started. No PR, merge, Release or main update.

D1 remains `BLOCKED` pending full reference publication, per-file remote evidence and exact-final-head validation after the remaining commits.

## Corrective continuation — 2026-11-01 (append-only)

- Live starting point revalidated: branch HEAD was `93da765f287fb28066d9c3eca4cdefdc39658d75`; main HEAD was `c6e54349a5e94f65d5aa9f83141f225d777bb474`.
- Historical versions of all three conflicting modules now have exact raw SHA-256, byte size, original Git blob SHA-1 and original containing commit recorded in `D1_CORRECTIVE_EVIDENCE_ADDENDUM_2026-11-01.md`. The old manifest resolver was restored from its base64 archival copy to raw UTF-8 and read back from GitHub; original raw bytes match the historical resolver blob.
- ZIP reader safety checks and tests were expanded for duplicate names, path traversal, Windows drive paths, dot/empty path segments, normalized names and symlinks.
- Exact-head workflow now downloads the three original pinned Actions artifacts by artifact ID, validates metadata + bytes + SHA-256, installs pyarrow and runs real Parquet-backed LossCase/MaxCase argmin/argmax integration. Prior CI runs with 8 skipped artifact tests remain historical successes only; they are not upgraded.
- Workflow run on the final commit is pending/in progress at time of this append; no PASS is claimed until the exact HEAD run and jobs complete successfully.
- v2.4.0 normative reference and v2.3/v2.3.1 historical/quarantine full text are verified in the local uploaded archive but not published/read back from GitHub. The current connector execution path cannot transfer the local archive bytes into GitHub; status remains `MISSING_EVIDENCE`.
- The 50,734-byte source bundle and Local Evidence ZIP are absent from the active runtime. Importer remains `NOT_RUN`.
- D1 disposition remains `BLOCKED`; D2–D6 not started. No Trial/simulation/Monte Carlo/N=4800, backfill, zero-fill, main change, PR, merge or Release.
- See `D1_CORRECTIVE_EVIDENCE_ADDENDUM_2026-11-01.md` for complete raw-source provenance and the exact workflow contract.


## Correction record — 2026-11-01

Hash correction (append-only): the original reader/model SHA-256 values previously appended in this session were incorrect and are superseded by the corrected values in `D1_CORRECTIVE_EVIDENCE_ADDENDUM_2026-11-01.md`: reader `37d882bb793ad4b447918287b5969fb8481f6e8c5bce1defdafeb7660b693f57`; model `1713b88ab0f619eb5a1747fc56eb3896a63e7cb8ac65b4e03142434dd03e13ea`; resolver `562de41283efb473464f1b5f662690303739ec93677dcef10cf9e6d2a23c787a`. Original blobs, sizes and commit IDs are unchanged. Earlier SHA values are superseded, not evidence.


## Exact artifact integration CI — 2026-11-01 (append-only)

Workflow Run `41249462481` passed at exact tested HEAD `7895f63ed1bb34508723d81ced956e6d77d5bda7`: compileall passed and pytest reported 26 passed, 0 failed, 0 skipped. The job downloaded the three pinned GitHub Actions artifacts by immutable IDs and verified exact metadata, byte sizes and SHA-256; it installed pyarrow and checked frozen S6 LossCase/MaxCase global argmin/argmax against the full pinned Parquet trial summary across 20 S6 scenarios. The final branch-head assertion passed. Run 17 (`41249454018`) is preserved as a failed exact-head check caused by concurrent branch advancement even though its 26 tests passed; Run 19 is the successful exact-head result. The closure addendum records this. The next documentation-only commit requires a new exact-head run. D1 remains BLOCKED on canonical full reference publication/readback and remaining evidence; no gate or project acceptance is promoted.


## Final SHA-256 reconciliation — supersedes all prior in-session corrections

A final digest pass using a SHA-256 implementation validated against the standard `abc` test vector was applied to the exact UTF-8 bytes re-fetched from GitHub. The authoritative historical-file SHA-256 values are:

- Original `s6_artifact_reader.py`: `7db68e7f0e41aabefbdff30667c6f4f8d626728c15c9bd1a2f5afc8b80858b09` (10,181 bytes; blob `35e644e22557eb6f3449571190c1c31e2af3d461`; original commit `2ef20e9634d346d3b5a263f474a613415b47b996`).
- Original `s6_deliverables_model.py`: `568c5c52be1c4399a849f617d919371126320af59aea7aa5369849d445f25891` (3,209 bytes; blob `670c10d39adcc732fe464437c1bf02f451b76f26`; original commit `15e5a49fc1ff96d7106506103e1d35ee164879e0`).
- Original `s6_manifest_resolver.py`: `f10fbcccb35445a1866d1ce0fed1d9da9c9cdd307e01507f13dea1d1f34c3d01` (5,143 bytes; blob `55ba5e5f0657d2b5337af84eff6a01e3749f5491`; original commit `61532b9230f3162eb2f6cb0fa0da2ddbfe1a0dd9`).

All earlier SHA-256 values for these three files in this session's appended records are superseded by this reconciliation. Blob SHA-1, byte sizes and original containing commits are unchanged. The raw archive files were read back from GitHub; the resolver raw copy's Git blob SHA-1 exactly matches the original historical file blob.
