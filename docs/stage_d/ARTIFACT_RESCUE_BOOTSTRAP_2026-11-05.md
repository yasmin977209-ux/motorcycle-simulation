# Live Bootstrap & Evidence Rescue Report — 2026-11-05

## Scope and baseline
- User request: live GitHub bootstrap and rescue of expiring evidence.
- Working branch: `tmp/d1-rebuild-20261101`; exact pre-write HEAD: `8177b0948081d38223a00652892930c7afb9c8d8`.
- `main` HEAD: `01a6f79eedc522bb734ed9c5ea31beee581f2468`.
- Branch comparison: diverged; ahead 970 / behind 2; merge base `c6e54349a5e94f65d5aa9f83141f225d777bb474`.
- No write, merge, release, force-push, or deletion on `main`.
- Repository tree at pre-write HEAD: 557 entries; no tracked single file exceeds 50 MiB.
- GitHub Releases API returned an empty list.
- Active-branch state.json and main/state.json are byte-identical at blob `6d94e0699e5380b4ecc184203d0c5ad6a4a8fb66`; both report `stage=12-CLOSED`. This does not replace the Stage D live status ledger.

## Governing reference verification
- Owner decision: `D-2026-10-30-REFERENCE-V2.4.0`, live status `APPROVED_BY_OWNER`.
- Governing reference path: `docs/governance/MOTORCYCLE_SIMULATION_GOVERNING_REFERENCE_V2.4.0.md`.
- Exact GitHub Raw bytes were fetched as base64 and decoded before hashing.
- SHA-256: `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b` (matches owner-declared value).
- Git blob SHA-1: `9fe43bfbb2cbfd2bb7f7010866e7469506d22c33`; size: 401,397 bytes.
- Decision file blob: `58f89bc016523f1350345428b4a224ac42a8b130`; its exact-byte SHA-256: `1076b3e876d3db1a7e6ab4473fedb22226dfda0cb499d230ba3a0c2a9652a95d`.
- Keep `current_governing_reference_sha256` separate from historical v2.3 execution reference.

## Actions artifact inventory — live metadata recheck
The 29 artifact records in `D0_D6_E0_E2_RETENTION_INVENTORY_2026-11-05.json` were re-queried by their associated workflow runs. All 29 returned `expired=false`. Metadata verification is not the same as downloading and hashing every ZIP.

Priority expiry list:
| Artifact ID | Role | Size bytes | Expiry UTC |
|---:|---|---:|---|
| 12852969854 | D0 aggregate | 9,357,996 | 2026-11-27 21:46:36 |
| 13288779998 | Owner-approved D3 workbook | 535,567,142 | 2026-12-04 02:07:02 |
| 13369179742 | D5 T2_INTERIM package | 519,116,689 | 2026-12-04 22:49:30 |
| 13371094066 | D6 post-write audit | 6,635 | 2026-12-04 23:14:36 |
| 13364064483 | D4 DOCX evidence | 4,814 | 2026-12-04 21:32:18 |
| 13373853115 | D0-D4 evidence | 5,706 | 2026-12-04 23:54:10 |
| 13382253631 | D0-D4 evidence | 5,698 | 2026-12-05 02:21:52 |
| 12998778418 | D1 Full Logging (105 representative keys) | 310,827,203 | 2027-01-28 17:25:30 |
| 12630457193 | C100 reuse artifact | 361,733 | 2027-01-24 03:18:29 |

The 20 E2 replay scenario artifacts plus aggregate remain unexpired and expire 2027-02-03 03:01:28 UTC. Their identity remains old-identity replay reconstruction; do not re-label as original preserved history.

## Download copies materialized in this ChatGPT session
The following GitHub Actions artifact ZIPs were downloaded by exact Artifact ID and materialized as temporary ChatGPT-hosted file objects:
- `12852969854` — `github-actions-artifact-12852969854.zip`
- `12998778418` — `github-actions-artifact-12998778418.zip`
- `12630457193` — `github-actions-artifact-12630457193.zip`
- `13288779998` — `github-actions-artifact-13288779998.zip`
- `13364064483` — `github-actions-artifact-13364064483.zip`
- `13369179742` — `github-actions-artifact-13369179742.zip`
- `13371094066` — `github-actions-artifact-13371094066.zip`
- `13373853115` — `github-actions-artifact-13373853115.zip`
- `13382253631` — `github-actions-artifact-13382253631.zip`

The GitHub metadata digests remain the recorded source digests; this session did not independently re-hash the downloaded ZIP bytes. ChatGPT-hosted file objects and signed URLs are temporary and are not permanent external copies. No phone storage or external archive write is claimed.

## Workflow, PR, and release check
- Exact current branch HEAD `8177b0948081d38223a00652892930c7afb9c8d8` has two completed successful workflows:
  - Run 42078525625 — Stage D1-D2 Source Validation; Job 127425089835; exact remote HEAD check and artifact integration tests succeeded.
  - Run 42078525547 — D3 Published Output Exact-HEAD Verification; Job 127425277913; exact branch/HEAD and Raw readback checks succeeded.
- These two runs do not establish D0-D4 exact-head closure, D5 final acceptance, or final project acceptance.
- Open PRs include #78, #77 and #76; none was merged by this session.
- No GitHub Release exists.

## Disposition and blocker
- Temporary download rescue: completed for the nine artifact IDs listed above.
- Permanent binary retention: `BLOCKED`. Actions artifacts expire; ChatGPT file objects/signed links are temporary. Git history contains source/text records, not these large binaries.
- Dropbox was identified as an available external archive route and a connection suggestion was presented to the owner. It is not yet connected; no upload to Dropbox or any other external storage is claimed.
- GitHub Release publication remains a protected owner decision and was not attempted.
- No phase was executed or promoted. Preserve the recorded scoped dispositions and all fixed financial/statistical limitations.

## Next safe action
After the owner connects an external storage destination (Dropbox or another approved archive), upload the exact downloaded ZIPs, re-read each remote object, compare size and SHA-256 to the GitHub artifact digest, and perform a restore/download test. Prioritize the 535.6 MB D3 and 519.1 MB D5 archives, then D1 Full Logging and D0 aggregate. Do not claim Global Preservation PASS until two independent durable copies and restore evidence exist.


## Dropbox Rescue Readback Correction — 2026-11-05T18:26:19Z (append-only)
- The owner approved Dropbox destination `/Motorcycle-Simulation-Rescue-2026-11-05/`; all nine priority GitHub Actions ZIPs uploaded with Dropbox `completed` responses.
- Fresh Dropbox folder readback returned exactly nine files (`has_more=false`), with returned sizes matching the source Artifact metadata: total 1,375,253,616 bytes (1,311.54 MiB). Full file-by-file path/size table: [ARTIFACT_RESCUE_DROPBOX_READBACK_2026-11-05.md](ARTIFACT_RESCUE_DROPBOX_READBACK_2026-11-05.md).
- The nine source artifacts were re-queried through their associated workflow runs; all nine are `expired=false`. The same run inventory returned 29/29 unexpired artifacts (9 priority + 20 E2 replay). Expiry timestamps remain active and unchanged.
- Important limitation: no ZIP extraction, independent ZIP-byte SHA-256, digest comparison against GitHub artifact digests, or restore test was performed. Dropbox listing and byte-size equality are not content-integrity proof.
- One Dropbox archive copy now exists; Global Preservation remains `BLOCKED / PERMANENT_RETENTION_NOT_COMPLETE` pending second independent durable copy, exact byte-hash comparison and restore test. No phone copy, GitHub Release, main write, merge, or stage promotion.
- Live bootstrap at 18:26Z: branch HEAD `bbb97a643ad5b1bc6137e54262ddafabae26394a`; main `01a6f79eedc522bb734ed9c5ea31beee581f2468`; diverged 971 ahead / 2 behind; merge base `c6e54349a5e94f65d5aa9f83141f225d777bb474`.
