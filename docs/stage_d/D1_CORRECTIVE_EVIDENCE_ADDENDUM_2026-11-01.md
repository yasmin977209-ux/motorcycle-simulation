# D1 Corrective Evidence Addendum — 2026-11-01

## Live baseline and scope

- Repository: `yasmin977209-ux/motorcycle-simulation`
- Working branch: `tmp/d1-rebuild-20261101`
- Revalidated starting branch HEAD: `93da765f287fb28066d9c3eca4cdefdc39658d75`
- Revalidated `main` HEAD: `c6e54349a5e94f65d5aa9f83141f225d777bb474` (read-only; unchanged in this session).
- Existing D1 modules/tests were retained; only a ZIP path-validation defect and missing CI artifact integration were addressed.
- Importer `scripts/import_stage_d_sources.py` was not run.

## Corrected historical conflict inventory

The three historical source files were re-read from their original GitHub commits. Raw versions are preserved under `docs/stage_d/archive/pre_import_conflicts/`; the old resolver is now restored as raw UTF-8 as well as the previous base64 archival representation.

| Original path | Original commit | Git blob SHA-1 | Bytes | SHA-256 of fetched raw bytes |
|---|---|---|---:|---|
| `scripts/s6_artifact_reader.py` | `2ef20e9634d346d3b5a263f474a613415b47b996` | `35e644e22557eb6f3449571190c1c31e2af3d461` | 10,181 | `7db68e7f0e41aabefbdff30667c6f4f8d626728c15c9bd1a2f5afc8b80858b09` |
| `scripts/s6_deliverables_model.py` | `15e5a49fc1ff96d7106506103e1d35ee164879e0` | `670c10d39adcc732fe464437c1bf02f451b76f26` | 3,209 | `568c5c52be1c4399a849f617d919371126320af59aea7aa5369849d445f25891` |
| `scripts/s6_manifest_resolver.py` | `61532b9230f3162eb2f6cb0fa0da2ddbfe1a0dd9` | `55ba5e5f0657d2b5337af84eff6a01e3749f5491` | 5,143 | `562de41283efb473464f1b5f662690303739ec93677dcef10cf9e6d2a23c787a` |

The original files are historical evidence, not active implementation. The prior base64 resolver archive is retained; the raw restored copy is independently fetched from GitHub and matches the original Git blob.

## ZIP reader correction

The current `scripts/s6_artifact_reader.py` now rejects:
- duplicate member names;
- absolute, traversal, Windows-drive, empty-segment and dot-segment paths;
- normalized path collisions;
- symlink members.

Focused tests were added for duplicate entries, path traversal, Windows paths, normalized path forms and symlinks.

## Exact-head CI correction

The previous workflow only cloned the source branch and ran tests with artifact-dependent tests skipped when ZIPs were absent. The workflow now:
1. obtains the three pinned artifacts from their original GitHub Actions artifact IDs;
2. checks artifact metadata, non-expired status, byte size and SHA-256 before use;
3. installs `pyarrow` and executes the actual Builder integration tests with all three ZIPs mounted through environment variables;
4. checks S6 `LossCase = argmin(Final_Net_Project_Equity)` and `MaxCase = argmax(Final_Net_Project_Equity)` against all rows in the pinned S6 `trials_summary.parquet`, without changing the frozen selection;
5. checks that the tested checkout is still the exact live branch HEAD.

This workflow change is a correction to validation scope, not evidence of success until its run completes at the final HEAD. A failed artifact download or Parquet assertion must remain a failed gate.

## Governing and historical references

- Live owner decision `D-2026-10-30-REFERENCE-V2.4.0` was read from GitHub and confirms `APPROVED_BY_OWNER`.
- The local v2.4.0 archive is present, CRC-checked, 14,507,701 bytes, SHA-256 `efb6a663a2fc63ac5c1f052048b3dfc945e233df9810d4fe0b21b892c533e52c`.
- Its normative Markdown member is 401,397 bytes with SHA-256 `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`.
- The complete normative v2.4.0 text is still absent from the required GitHub path `docs/governance/MOTORCYCLE_SIMULATION_GOVERNING_REFERENCE_V2.4.0.md`. The local uploaded archive is not directly writable through the available GitHub file connector in this execution environment. Therefore publication and remote readback remain `MISSING_EVIDENCE`; no local hash is represented as remote proof.
- The local archive contains v2.3 historical reference (381,559 bytes, SHA-256 `e5efaf0874384e8248c339ca10e248ea9e17e9f0882153b4ef88bc955b91d53f`) and closed unapproved v2.3.1 candidate (394,983 bytes, SHA-256 `724a22aae9bb3caf55bf9de1f27c2edba79b453585bb863b72fe7c5e04c44db0`). Their canonical historical/quarantine GitHub copies are not yet established.
- The 50,734-byte source bundle and Local Evidence archive are absent from the active `/mnt/data` inventory; neither was invented, imported or substituted.

## Preserved project limits

No Trial, simulation, Monte Carlo, N=4800, backfill, accounting-field zero-fill, D2 registry build, Excel/DOCX generation, main update, PR, merge or Release was performed. S6/C100 identities remain fixed. Full Logging remains 105 representative keys, not 48,000 trials. All 105 normalized manifest states remain `NOT_VERIFIED` where independent expected byte sizes are missing. Gate A production remains `NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS`.

## Disposition

D1 remains `BLOCKED`. Required blockers still include canonical remote publication/readback of v2.4.0 and historical/quarantine references, successful exact-final-HEAD CI with real artifacts and Parquet extreme validation, and complete per-file remote evidence for the final commit. This addendum corrects earlier stale audit statements append-only; it does not overwrite them or close D1.
