# Dropbox Evidence Rescue — Readback Correction — 2026-11-05


## Dropbox Rescue Readback Correction — 2026-11-05T18:26:19Z (append-only; supersedes only the external-archive status above)

- Owner explicitly approved creation/use of `/Motorcycle-Simulation-Rescue-2026-11-05/`.
- GitHub Actions ZIPs were downloaded by exact Artifact ID via the GitHub connector and uploaded through the Dropbox connector. Dropbox returned `status=completed` for all nine files.
- A fresh Dropbox `list_folder(recursive=false)` readback returned exactly these nine files and `has_more=false`:
  | Artifact ID | Dropbox path | Bytes |
  |---:|---|---:|
  | 12852969854 | `/Motorcycle-Simulation-Rescue-2026-11-05/artifact-12852969854-D0-aggregate.zip` | 9,357,996 |
  | 13288779998 | `/Motorcycle-Simulation-Rescue-2026-11-05/artifact-13288779998-D3-workbook.zip` | 535,567,142 |
  | 13369179742 | `/Motorcycle-Simulation-Rescue-2026-11-05/artifact-13369179742-D5-T2-INTERIM.zip` | 519,116,689 |
  | 12998778418 | `/Motorcycle-Simulation-Rescue-2026-11-05/artifact-12998778418-D1-Full-Logging.zip` | 310,827,203 |
  | 13371094066 | `/Motorcycle-Simulation-Rescue-2026-11-05/artifact-13371094066-D6-audit.zip` | 6,635 |
  | 13364064483 | `/Motorcycle-Simulation-Rescue-2026-11-05/artifact-13364064483-D4-evidence.zip` | 4,814 |
  | 13373853115 | `/Motorcycle-Simulation-Rescue-2026-11-05/artifact-13373853115-D0-D4-evidence.zip` | 5,706 |
  | 13382253631 | `/Motorcycle-Simulation-Rescue-2026-11-05/artifact-13382253631-D0-D4-evidence.zip` | 5,698 |
  | 12630457193 | `/Motorcycle-Simulation-Rescue-2026-11-05/artifact-12630457193-C100-reuse.zip` | 361,733 |
- Dropbox remote byte-count sum: 1,375,253,616 bytes (1,311.54 MiB). This is metadata/readback evidence only; ZIP contents were not extracted, and downloaded/uploaded ZIP bytes were not independently SHA-256 hashed or compared against GitHub artifact digests.
- The nine source Artifacts were re-queried live through their associated workflow runs; all nine returned `expired=false`. The same live inventory query returned 29/29 unexpired artifacts (9 priority + 20 E2 replay artifacts). This does not extend their expiry.
- Priority remaining expiries (UTC): D0 aggregate 2026-11-27T21:46:36Z; D3 workbook 2026-12-04T02:07:02Z; D5 package 2026-12-04T22:49:30Z; D4/D6 and D0-D4 evidence 2026-12-04/05; D1 Full Logging 2027-01-28T17:25:30Z; C100 reuse 2027-01-24T03:18:29Z. E2 replay artifacts expire 2027-02-03T03:01:28Z.
- Updated live GitHub bootstrap at this read: working branch HEAD `bbb97a643ad5b1bc6137e54262ddafabae26394a`; main HEAD `01a6f79eedc522bb734ed9c5ea31beee581f2468`; compare main...working branch: `diverged`, 971 ahead / 2 behind, merge base `c6e54349a5e94f65d5aa9f83141f225d777bb474`.
- Dropbox folder creation and file uploads are the only external-retention mutations. No GitHub Artifact, manifest, historical source, main ref, PR, Release, Trial, or phase status was changed. No phone copy is claimed.
- Preservation status improves from no external archive to one Dropbox archive copy, but remains `BLOCKED / PERMANENT_RETENTION_NOT_COMPLETE`: no independent second durable copy, no ZIP-byte SHA-256 comparison, and no restore test. Do not promote Global Preservation Gate.
- The prior statement in this report that Dropbox was not connected/no external upload occurred is retained as historical pre-approval status and superseded operationally by this dated correction. The original Actions expiry metadata and source digests remain unchanged.
