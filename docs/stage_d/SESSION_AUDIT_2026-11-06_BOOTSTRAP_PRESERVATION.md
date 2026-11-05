# Live Bootstrap & Preservation Audit — 2026-11-06

Repository: `yasmin977209-ux/motorcycle-simulation`  
Working branch: `tmp/d1-rebuild-20261101`  
Live branch HEAD at review start: `cc5753e1a37db1cc0a3ee02ab2a2f21ae08e1d3f`  
Live main HEAD (read-only): `01a6f79eedc522bb734ed9c5ea31beee581f2468`  
Branch comparison: `diverged`, 1,015 ahead / 2 behind; merge base `c6e54349a5e94f65d5aa9f83141f225d777bb474`. No rebase, merge, or main write.

## 1. Governing inputs — exact-byte verification

The following files were fetched from GitHub Base64 content and SHA-256 was recomputed from decoded bytes. Each current branch tree contains these exact blobs at the review HEAD above.

| File | Bytes | Git blob SHA-1 | SHA-256 |
|---|---:|---|---|
| [REV6](https://github.com/yasmin977209-ux/motorcycle-simulation/blob/cc5753e1a37db1cc0a3ee02ab2a2f21ae08e1d3f/docs/stage_d/PROJECT_PROMPT_LIBRARY_AR_2026-11-05_REV6.md) | 101,383 | `22ad6f50dbe32226f2753d4e4e9af902984dc765` | `b7d88fbda6426a330c25e65f66e3c9c99b8ce86543742c568ec5df17ac635243` |
| [Governing v2.4.0](https://github.com/yasmin977209-ux/motorcycle-simulation/blob/cc5753e1a37db1cc0a3ee02ab2a2f21ae08e1d3f/docs/governance/MOTORCYCLE_SIMULATION_GOVERNING_REFERENCE_V2.4.0.md) | 401,397 | `9fe43bfbb2cbfd2bb7f7010866e7469506d22c33` | `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b` |
| [v2.4.0 owner decision](https://github.com/yasmin977209-ux/motorcycle-simulation/blob/cc5753e1a37db1cc0a3ee02ab2a2f21ae08e1d3f/docs/governance/D-2026-10-30-REFERENCE-V2.4.0.md) | 3,527 | `58f89bc016523f1350345428b4a224ac42a8b130` | `1076b3e876d3db1a7e6ab4473fedb22226dfda0cb499d230ba3a0c2a9652a95d` |
| [D1 105-key size evidence](https://github.com/yasmin977209-ux/motorcycle-simulation/blob/cc5753e1a37db1cc0a3ee02ab2a2f21ae08e1d3f/docs/stage_d/D1_105_MANIFEST_SIZE_EVIDENCE_2026-11-05.json) | 69,247 | `2ea998a1faeeb7ebb36208f36fc878a9c20518f7` | `8412adb32c32a000d624fbbd1ea965238dd4da4b1ef95949551e5b47bf19516f` |
| [D3-18 reconciliation](https://github.com/yasmin977209-ux/motorcycle-simulation/blob/cc5753e1a37db1cc0a3ee02ab2a2f21ae08e1d3f/docs/stage_d/D3_18_INVOCATION_RECONCILIATION_2026-11-05.json) | 1,799 | `f292026738551d189b3a80c4861d8cdb1b5d5575` | `df93d2143f2d8457f8100fe6cb5c661e49f86a179cc422d4f732381974ab556e` |
| [Owner Dropbox-provider decision](https://github.com/yasmin977209-ux/motorcycle-simulation/blob/cc5753e1a37db1cc0a3ee02ab2a2f21ae08e1d3f/docs/stage_d/OWNER_DECISION_DROPBOX_STORAGE_PROVIDER_2026-11-06.md) | 3,185 | `63ac6f028e39c58aee1b94e190ca11947982229c` | `04befab3ba0667c863fe20a37cce56b5b227fbead76da13b9f00e8fcec2071fd` |
| [Owner authorization session status](https://github.com/yasmin977209-ux/motorcycle-simulation/blob/cc5753e1a37db1cc0a3ee02ab2a2f21ae08e1d3f/docs/stage_d/OWNER_AUTHORIZATION_SESSION_STATUS_2026-11-06.md) | 1,141 | `b2d10669f1f54bf450845114db0f40225a934d2b` | `44ec863d64813a4658a76fb5779f4ce607610eb575ccd03352958b178f4ba1ce` |
| [D3-S workflow](https://github.com/yasmin977209-ux/motorcycle-simulation/blob/cc5753e1a37db1cc0a3ee02ab2a2f21ae08e1d3f/.github/workflows/d3-s-scenario-partitioning.yml) | 5,423 | `1c48dfb5b2a7ffae6de70d26a9910b58292db0c4` | `0ebecd96cc6df8fc834b6ab15a9b2f9c292f33c8114aa4cc1ae63f51db7b1af2` |

The v2.4.0 payload still contains the stale `PROPOSED` header; the explicit `APPROVED_BY_OWNER` decision controls. Current governing SHA and historical v2.3 execution SHA remain separate.

## 2. Current stage and gate disposition

| Area | Disposition | Scope / limitation |
|---|---|---|
| D0 | `PASS_SCOPED_WITH_LIMITATIONS` | Original 48K daily accounting ledgers and complete Parquet audit not established. |
| D1 | `PASS_SCOPED_WITH_LIMITATIONS` | 105 selected representative keys now have byte-size/hash reconciliation; this is not 48K Full Logging. Importer and independent full rebuild requirements remain unproven. |
| D2 | `PASS_SCOPED_WITH_LIMITATIONS` | Registry records 2,640 entries, 1,000 daily series and 2,086,550 points; it does not prove complete original ledgers. |
| D3 | Not closed | The 11/06 owner-intake status says D3 is not closed; D3-S1/S2 remain open. |
| D3-18 | `PASS_SCOPED` | Owner-authorized Artifact acceptance/readback only. Historical requirement map `NOT_RUN` is preserved; this does not close D3. |
| D3-S1 / D3-S2 | Not closed / not established | No verified ten-workbook partition plus two semantic reassembly round trips in the inspected evidence. |
| D4–D6 | Historical `PASS_SCOPED_WITH_LIMITATIONS` records | No `PASS_GAP_FREE` closure; no new execution in this review. |
| E0 / E1 | `PASS_SCOPED` | Gap inventory and documentary reconciliation only. |
| E2 original accounting gate | `BLOCKED` | Five protected fields and original 48K full-balance daily records remain `MISSING_EVIDENCE`. |
| E2 replay | `PASS_SCOPED_REPLAY_RECONSTRUCTION` | Run 41958935113 is reconstructed evidence, not original historical evidence. |
| Global Preservation | `BLOCKED / PERMANENT_RETENTION_NOT_COMPLETE` | One Dropbox provider only; no byte-level Dropbox SHA-256/restore proof; E2 replay set absent. |
| E3–E6 | `NOT_STARTED` | Entry conditions are not met. |

The 2026-11-05 D0–D6 aggregate report records scoped results for D0–D6, but the newer 2026-11-06 owner-intake status explicitly says D3 is not closed and D3-S1/S2 are not closed. The stricter REV6 gap-free gate is not promoted by the aggregate scoped report.

## 3. D1 and exact-head workflow evidence

- Run [42111210356](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42111210356), Job `127538938374`, tested SHA `bc4a45585cd23b933e2d7428bd0adde18ec4f512`: SUCCESS, 34 passed, 0 failed, 0 skipped. Artifact `13454621678`, 10,545 bytes, digest `sha256:1e000f70b2fe675b34e549d99d8f55753d16b9898c9255c169bb1a9fcb539ed5`, expires 2026-12-05T21:18:43Z.
- The committed 105-key evidence file is 69,247 bytes, SHA-256 `8412adb32c32a000d624fbbd1ea965238dd4da4b1ef95949551e5b47bf19516f`, blob `2ea998a1faeeb7ebb36208f36fc878a9c20518f7`. It reconciles actual `trial_manifest.json` and `post_write_audit.json` sizes and hashes for 105 selected keys only.
- Run [42111210352](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42111210352), Job `127538939172`, tested SHA `bc4a45585cd23b933e2d7428bd0adde18ec4f512`: SUCCESS; committed D3 outputs/evidence Raw readback. This is not D3-S execution.
- Both runs tested `bc4a455...`, not the current review-start HEAD `cc5753e...`; they are not re-labelled as exact-current-HEAD runs.

## 4. D3-S workflow inspection — no dispatch

The current workflow `.github/workflows/d3-s-scenario-partitioning.yml` was read and byte-hashed. It is configured with `permissions: actions: read, contents: read`, `timeout-minutes: 360`, and downloads exact D3 Artifact `13288779998` and D5 Artifact `13369179742`, verifies pinned ZIP/workbook hashes, partitions five C groups per language, and uploads ten workbooks plus equivalence evidence. No workflow was dispatched in this review. The earlier long-running/cancelled attempt was not queried or restarted; do not infer its state from this audit.

## 5. Live Artifact inventory and Dropbox reconciliation

Live GitHub Actions API metadata was re-read for the nine rescue-folder source Artifacts and the E2 replay set. All listed items below were `expired=false` at the time of this review.

| Artifact ID | Run ID | Bytes | GitHub Artifact SHA-256 | Expiry (UTC) |
|---:|---:|---:|---|---|
| 12852969854 | 40773412377 | 9,357,996 | `ec05a69ae8968585decf83cf0716d56c264f47f86187cfd3cf53b11f52ca2e54` | 2026-11-27 21:46 |
| 12998778418 | 41098699740 | 310,827,203 | `403371cc8eb12880dda05529b4c83dd675bfa609e8680c09d35efa729c5b5aeb` | 2027-01-28 17:25 |
| 12630457193 | 40263424595 | 361,733 | `c977d1cbb5204919eadc72358533f77cdbbc239902bcd6f921bf1a915a716e79` | 2027-01-24 03:18 |
| 13288779998 | 41754147172 | 535,567,142 | `e49b206d8d80034b1dc0cb284bfee76d81f9e9759e2459b1608fad2f5c933ffe` | 2026-12-04 02:07 |
| 13364064483 | 41916830283 | 4,814 | `fd5517de84bdb99a2a1e77068d471bea0cdce5de2145ed6f16c336e376b06b99` | 2026-12-04 21:32 |
| 13373853115 | 41937190378 | 5,706 | `e61e367e2cc0136894d0054becc45660dc4ca1a75d63eb05e3425b6a4a9a2251` | 2026-12-04 23:54 |
| 13382253631 | 41954633829 | 5,698 | `d7811702f0e8365ca888bc49ec2652877d4d451beb4a54d87e43c0a7abcae718` | 2026-12-05 02:21 |
| 13369179742 | 41928234377 | 519,116,689 | `80caf0567e31a6bf5397543dac8ef191b38999105dd3cedce4c3dad75b20bff1` | 2026-12-04 22:49 |
| 13371094066 | 41929888796 | 6,635 | `f8ed5e1f516a3a6d34086c2ef4f5fb2a84670c9907fabd503b994086426ca112` | 2026-12-04 23:14 |

Dropbox root `/Motorcycle-Simulation-Rescue-2026-11-05/` currently lists nine files, total `1,375,253,616` bytes. The three files in `secondary_verified_mirror/` (Artifacts 13288779998, 13369179742 and 12998778418) have matching size and Dropbox `content_hash` metadata to their root copies. Dropbox `content_hash` is not the GitHub Artifact SHA-256 and does not prove ZIP-byte equality or a restore test. Both folders are within the same Dropbox account/provider; they are not independent failure domains.

**Inventory correction:** the existing 29-item retention inventory omits Artifact `13364064483`, which is present in the Dropbox root and was independently re-queried live from Run `41916830283`. Preserve the historical inventory and add an append-only correction; do not silently rewrite it.

The E2 replay run `41958935113` has 20 scenario Artifacts plus aggregate Artifact `13393273763` (21 total), all unexpired through 2027-02-03T03:01:28Z. None appears in the Dropbox rescue root; Dropbox search for `e2-s6-replay` returned no matches. Scenario Artifact IDs: `13393345087, 13393166526, 13392884757, 13392656883, 13391878325, 13391877035, 13391099143, 13390253424, 13390020181, 13389748302, 13388993770, 13387718801, 13387489646, 13387039806, 13386989611, 13386247870, 13385711291, 13385547304, 13385442622, 13384613845`. Aggregate: `13393273763`.

A test upload of E2 Artifact `13385547304` (130,319,892 bytes) to the approved Dropbox root returned `RESOURCE_EXHAUSTED / INSUFFICIENT_SPACE`. A subsequent live root listing still showed nine files and no partial E2 upload. No retry was attempted. This establishes an operational capacity blocker for additional Dropbox uploads; do not assume quota or attempt a batch upload until capacity is resolved.

No Dropbox archive was byte-rehashed in this review. ZIP CRC/member checks, internal manifest/hash verification, and Restore Tests remain `NOT_RUN`. The Global Preservation Gate remains blocked.

## 6. Other bootstrap findings

- No open PR was found with `tmp/d1-rebuild-20261101` as its head. The repository has other open PRs, but none was attributed to this working branch.
- The branch is divergent from main (1,015 ahead / 2 behind). No rebase/merge is proposed.
- Main `state.json` reports Stage 12 status; that is a separate lineage and does not override Stage D/E state on the working branch.
- A complete current Releases/Tags inventory was not available through the GitHub connector actions used in this review; no absence claim is made.
- SharePoint was surfaced as an optional independent provider, but is not connected. Google Drive is unavailable (disabled by admin). No second provider was connected or written.

## 7. Fixed limits and prohibited actions preserved

Financial Gate A remains `PASS_SCOPED`; Production Gate A `NOT_DECLARED`; Gate B at N=2400 `FAIL_SCOPED (10/10)`; Stability `NOT_CONVERGED (0/60)`; N=4800 `NOT_EXECUTED`; Full Logging remains representative-only; C100 Golden remains `NOT_RUN`. The five protected accounting fields remain `MISSING_EVIDENCE` and were not inferred or zero-filled.

No new Trial, Simulation, Monte Carlo, Golden revalidation, N expansion, backfill, zero-fill, identity/business-rule/reference/threshold change, historical Artifact/manifest mutation, main write, merge, force-push, Release, or final-acceptance declaration was performed. No new long-running workflow was started or monitored.

## 8. Next permitted actions

1. Resolve Dropbox capacity or connect and explicitly authorize a genuinely independent second storage provider; then preserve the missing 20 E2 scenario Artifacts plus aggregate and perform readback/restore tests.
2. Byte-verify all nine Dropbox root copies against the exact GitHub Artifact SHA-256 pins, inspect ZIP/member manifests, and run actual restore tests.
3. Add an append-only correction for the missing Artifact 13364064483 in the retention inventory.
4. Keep D3-S1/S2 on hold until the prior long-running attempt is resolved by the owner; do not dispatch a replacement from this session.
5. Continue only authorized source-only recovery for the five original accounting fields. E2 original gate remains blocked; E3 remains not started.
