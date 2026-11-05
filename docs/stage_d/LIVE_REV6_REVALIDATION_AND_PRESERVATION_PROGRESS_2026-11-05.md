# Live REV6 Revalidation and Preservation Progress — 2026-11-05

## Live baseline
- Repository: `yasmin977209-ux/motorcycle-simulation`
- Branch: `tmp/d1-rebuild-20261101`
- HEAD before this report: `e5d796a62268d9caa6af272566b6c5f88b7c8ca6` (created by the E2 replay addendum in this session; re-read branch ref after all writes).
- Main: `01a6f79eedc522bb734ed9c5ea31beee581f2468` (read-only; unchanged).

## Live REV6 and governing authority
- REV6: `docs/stage_d/PROJECT_PROMPT_LIBRARY_AR_2026-11-05_REV6.md`, Git blob `22ad6f50dbe32226f2753d4e4e9af902984dc765`, 101,383 bytes. Owner's supplied SHA-256 is `b7d88fbda6426a330c25e65f66e3c9c99b8ce86543742c568ec5df17ac635243`; the live REV6 review audit records this as recomputed from GitHub Base64-decoded bytes and identifies containing commit `5377790ed17392d142824faddde4a6357c8fd27e`.
- Governing reference v2.4.0 owner decision remains `APPROVED_BY_OWNER`; current governing SHA-256 `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`. Historical v2.3 execution SHA-256 remains separate: `e5efaf0874384e8248c339ca10e248ea9e17e9f0882153b4ef88bc955b91d53f`.
- The v2.4.0 payload header still says PROPOSED; the owner decision controls. No reference bytes were changed.

## Exact-HEAD workflow evidence
At exact branch HEAD `7d7f145c082012d0ddcc9f3c598a9db8fccbee95`:
- D0-D4 final validation Run `42088305776`, Job `127459978932`: SUCCESS; registry and DOCX readback, five DOCX tests passed, final Raw readback and exact-head assertion succeeded. Artifact `13442739373`, 6,322 bytes, SHA-256 `f77a02798fda3988e8944831eb1ca6464e1b6e9b098d8d329d34986107181931`.
- D1-D2 source validation Run `42088305764`, Job `127459281022`: SUCCESS; pinned source artifact metadata/ZIP bytes verified and 34 tests passed. This does not establish the requested 105-key trial_manifest/post_write_audit expected byte-size extraction or D1 gap-free status.
- D3 published-output verification Run `42088305983`, Job `127459282564`: SUCCESS; committed D3 outputs/evidence Raw readback succeeded. This does not execute D3-S.
- All three runs tested the same exact SHA above. Their success is scoped evidence only; it does not imply D0-D3-S gap-free closure.

## Dropbox preservation work performed
- Resolved the rescue folder via Dropbox namespace path `ns:927723726//Motorcycle-Simulation-Rescue-2026-11-05`; root listing returned exactly nine files, 1,375,253,616 bytes, no pagination.
- Download-link metadata supplied Dropbox content_hash values for all nine files, but this session did not obtain their ZIP bytes; therefore GitHub Artifact SHA-256 comparison and independent ZIP CRC/member restore tests remain NOT_RUN.
- Copied three large existing archives into `/Motorcycle-Simulation-Rescue-2026-11-05/secondary_verified_mirror/`: Artifact 13288779998 (535,567,142 bytes), Artifact 13369179742 (519,116,689 bytes), and Artifact 12998778418 (310,827,203 bytes). Dropbox copy operations succeeded. Source and mirror sizes and Dropbox content_hash values matched for each pair. Dropbox content_hash is not the requested GitHub ZIP SHA-256; this is not a ZIP Restore Test. The two paths remain within the same Dropbox account/service and do not independently prove provider-level failure-domain separation.
- E2 Run 41958935113's aggregate and 20 scenario artifacts are not yet present in Dropbox. The current Dropbox connector supports Dropbox-to-Dropbox copy and file-parameter uploads, but no direct GitHub Artifact-to-Dropbox transfer in this session. No claim of E2 archive rescue is made.

## E2 old-identity replay append-only reconciliation
- Added `docs/post_d/E2_OLD_IDENTITY_REPLAY_RECONSTRUCTION_ADDENDUM_2026-11-05.json` in commit `e5d796a62268d9caa6af272566b6c5f88b7c8ca6`.
- Live Run `41958935113` completed SUCCESS. The 20 scenario jobs and aggregate job `127088943738` all succeeded. Aggregate report: `PASS_SCOPED_REPLAY_RECONSTRUCTION`, 48,000 Trial identities, 98,323,918 replay daily rows; aggregate Artifact `13393273763`.
- Model execution source was `a23ba71f48487f3ebead99bc30039b14ef9b7609`, old SOURCE_SHA `da1a9ea9b5cd789c944de3f07b08395bb67c49e7`, old cohort `s6-v23-da1a9ea9`, seed `20270101`. Workflow HEAD `002b74893ca9dfea864e83fecc558f2388748ffe` is not the model execution source.
- Replay is not original historical evidence. The five historical accounting fields remain MISSING_EVIDENCE; Production Gate A remains NOT_DECLARED; final acceptance NOT_GRANTED. No new S6+C100 lineage was run.

## D0-D3-S current blockers
1. D0/D1: the 105-key manifest resolver issue is not proven closed by the current exact-HEAD workflow. Required extraction of exact byte sizes for `trial_manifest.json` and `post_write_audit.json` from Full Logging Artifact 12998778418 and key-by-key identity/hash/size comparison remains NOT_RUN in the evidence inspected here. Do not infer values.
2. D2: live registry file is present at `results/number_registry.json`; 24,137,036 bytes, Git blob `8cf17de488c623f96c1961ca91d682fbbc7733d6`, SHA-256 `743ffcced8de09a766870f201c352aabcf5789c43c84bfeae654a939700e4f87`. Prior audited counts are 2,640 entries and 2,086,550 daily points; the exact-HEAD validation is not a substitute for full fresh schema/lineage audit.
3. D3 source conflict: the owner task names original workbook sizes about 27.7 MB each; live D3 Artifact 13288779998 acceptance manifest records the two workbook members as 259,442,692 and 259,444,534 bytes. This discrepancy must be resolved from the exact source Artifact bytes before partitioning; no mapping or source size is assumed.
4. D3-S: no ten-partition output, language-specific manifest, 185-sheet mapping, 25/25 scenario coverage proof, or reassembly/equivalence test is present in the inspected live tree. D3-S remains NOT_RUN and D3 cannot be promoted to gap-free.
5. D3-18: D3 acceptance JSON top-level `d3_18=PASS_SCOPED` conflicts with `d3_requirement_statuses["D3-18"]="NOT_RUN"`; preserve and reconcile append-only after a real requirement invocation.
6. Preservation: exact Dropbox SHA-256 comparisons, ZIP CRC/member checks, restore tests, Git permanent archive copies for all eligible sub-100-MiB files, E2 artifact transfer, and verified independent failure-domain evidence remain incomplete.

## Gate disposition and safety
- Global Preservation Gate: BLOCKED.
- D0-D6: existing scoped records remain PASS_SCOPED_WITH_LIMITATIONS; no stage promoted to PASS_GAP_FREE.
- E2 old replay reconstruction: PASS_SCOPED_REPLAY_RECONSTRUCTION only. E2 original historical accounting gate remains BLOCKED.
- E3-E6: NOT_STARTED.
- Preserve Financial Gate A PASS_SCOPED only; Production Gate A NOT_DECLARED; Gate B N=2400 FAIL_SCOPED (10/10); Stability NOT_CONVERGED (0/60); N=4800 NOT_EXECUTED; Full Logging 105 representative keys only.
- No main write, merge, Release, Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, identity/seed/cohort/source change, or historical Artifact/manifest mutation occurred.

## Next permitted work
- Run a GitHub Actions workflow on a future exact branch HEAD to extract and compare all 105 manifest byte-size/identity records from the immutable Full Logging Artifact.
- Resolve the original workbook-size/source conflict from exact Artifact bytes; then D3-S may proceed only when D0/D1/D2 entry gates are met under REV6.
- Complete exact-byte Dropbox hash/restore work and authorized E2 artifact transfer; do not mark the Preservation Gate closed until all evidence is present.
- Keep main read-only and stop before D4 progression until D3 and D3-S are proven closed.
