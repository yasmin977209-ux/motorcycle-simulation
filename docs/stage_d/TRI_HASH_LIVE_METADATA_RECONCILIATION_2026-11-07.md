# Tri-hash live metadata reconciliation — 2026-11-07

## Record identity
- Repository: `yasmin977209-ux/motorcycle-simulation`
- Working branch: `tmp/d1-rebuild-20261101`
- Branch HEAD observed before this record: `c56cf4f13415b4e3310353aa3454633d67932d15`
- Protected main observed read-only: `01a6f79eedc522bb734ed9c5ea31beee581f2468`
- GitHub raw reference: Run [42312819156](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42312819156), Artifact `13549572312`; manifest SHA-256 `a41af27f36dedc1e2122715d37a7c0fc7ab60dddf8cbc15c48b33764a5d84fc1`; tested SHA `c47eef26a2f13c40b02853d6dcf6fe81ab2834f4`.
- Manifest disposition: `PASS_GITHUB_RAW_HASHING_ONLY`; provider reads `NOT_PERFORMED_BY_DESIGN`. It contains 53 raw GitHub artifacts and provides SHA-256, QuickXorHash and Dropbox content_hash for 20 S6 artifacts, 21 D3-S parts + restore manifest, and 9 Dropbox source artifacts. It does not include a QuickXorHash reference for D3S-010 or the D1/D3/D5 transport wrappers.

## Live inventory and classifications

| Source/group | Live objects | MATCH | NOT_COMPARABLE | MISMATCH | MISSING | ERROR |
|---|---:|---:|---:|---:|---:|---:|
| Dropbox rescue root | 9 files | 9 | 0 | 0 | 0 | 0 |
| OneDrive S6 in rescue root | 20 | 20 | 0 | 0 | 0 | 0 |
| OneDrive D3-S folder | 23 | 22 | 1 | 0 | 0 | 0 |
| OneDrive D1/D3/D5 transport folder | 20 | 0 | 20 | 0 | 0 | 0 |
| **Total unique live objects** | **72** | **51** | **21** | **0** | **0** | **0** |

These MATCH values mean equality of the same provider hash algorithm and the same GitHub raw artifact object: Dropbox `content_hash` ↔ manifest `dropbox_content_hash_hex`; OneDrive `file.hashes.quickXorHash` ↔ manifest `quickxorhash_base64`. No cross-algorithm comparisons were used. These are provider-metadata hash matches, not a claim that this session downloaded every OneDrive object and independently recomputed its raw-byte SHA-256.

### Dropbox — same-algorithm content_hash comparison

Live folder: `/Motorcycle-Simulation-Rescue-2026-11-05` (9 files; the `secondary_verified_mirror` subfolder is excluded from the unique-file count). Each value below matched the same artifact's `dropbox_content_hash_hex` in the GitHub raw manifest.

| File | Bytes | Live content_hash | GitHub artifact ID | Result |
|---|---:|---|---:|---|
| artifact-13382253631-D0-D4-evidence.zip | 5698 | `a81f39f1649a35b683d62d907e73b7335576aa2ca5806993213425f57a4f48eb` | `13382253631` | MATCH |
| artifact-13364064483-D4-evidence.zip | 4814 | `291b6e9a95f82097feda00f281f974703dfac8b2ff9b4647d1eeadae69db74d4` | `13364064483` | MATCH |
| artifact-13288779998-D3-workbook.zip | 535567142 | `4f826787e7f1ae76a373725971705798103db4af5e85cbd4717432436bcbd713` | `13288779998` | MATCH |
| artifact-13371094066-D6-audit.zip | 6635 | `e597182d02707d031adea5bd0455d4bfbdc2ab94d7dfcfd113edddd357c2cc14` | `13371094066` | MATCH |
| artifact-12998778418-D1-Full-Logging.zip | 310827203 | `16131e26731bc05bb30097690487a7076fbf07c6cb416067bceda196dd7c92d8` | `12998778418` | MATCH |
| artifact-13373853115-D0-D4-evidence.zip | 5706 | `c6810d3a4ac5b364c034a8a7d1a179cfc89ca5d105c1767d5a9f8d5769f62c8b` | `13373853115` | MATCH |
| artifact-13369179742-D5-T2-INTERIM.zip | 519116689 | `96a585387c9b66976f4057ef38181615c535b99dbb5a46327d9ec40f5a25f86d` | `13369179742` | MATCH |
| artifact-12852969854-D0-aggregate.zip | 9357996 | `5bf84443318b9a4f671ee75b93067afdd97f92b89f1ab3610145f6becd96204a` | `12852969854` | MATCH |
| artifact-12630457193-C100-reuse.zip | 361733 | `c610607220ae27e71c2e64e0cfd897b305b6558d3612c97fb112e4f2fd1d1f22` | `12630457193` | MATCH |

### OneDrive S6 — same-algorithm QuickXorHash comparison

Live rescue folder item ID: `893D06C344EA996B!s0a781736638d4c6fac434b1ff2bb1b9a`. All 20 observed QuickXorHash values and sizes matched their corresponding GitHub raw manifest entries for S6 Run `40731224990`.

| File | Bytes | Live QuickXorHash (= reference) | OneDrive item ID suffix | Result |
|---|---:|---|---|---|
| s6-n2400-C030_G000-40731224990.zip | 48678427 | `RBlf5A7hVulszHjXoNNbwnOSAZI=` | `sf826a6885dba4c1da2ec4ddd615680c6` | MATCH |
| s6-n2400-C030_G030-40731224990.zip | 51887261 | `P3/tLZsQSjic5EV0LhnmEEiZpg8=` | `s2b795dd6494749f08960d5e1bc8ea6b1` | MATCH |
| s6-n2400-C030_G050-40731224990.zip | 52997909 | `awz+6j0ol2ugT/+97y8n6ex3Ck0=` | `sf412ecb37e8941e08750334c83b19054` | MATCH |
| s6-n2400-C030_G070-40731224990.zip | 54426987 | `OO81LfVQBD4VFR6zP1k5g32QWiI=` | `sdedbb152ff5b4a06a3106616c48d7e41` | MATCH |
| s6-n2400-C030-G100-40731224990.zip | 55280954 | `XM9gMggcQQOrOC8AMJW/wtJwjL4=` | `s324aff744f104b69bd55c776cfd883d5` | MATCH |
| s6-n2400-C050_G000-40731224990.zip | 94849558 | `5kiQ68pNf1z2uVl/J5vR/a3w7wQ=` | `s1df7f8e8c37d4e0aa659c01ed9aa32e0` | MATCH |
| s6-n2400-C050_G030-40731224990.zip | 97589544 | `OpD5RWAZVQYC7z+zMbEZtIatnVk=` | `s3efcb65cbc214dbea4ff8b103389bce1` | MATCH |
| s6-n2400-C050_G050-40731224990.zip | 96741246 | `rrQ0l3PS7V/2QvC9KztFm5p1e/0=` | `s7045c68b82e34350b4cf733a1de03269` | MATCH |
| s6-n2400-C050_G070-40731224990.zip | 97639363 | `TVx9o2dnIe/NkCdxSxysNfl76LQ=` | `s96fd9594fc1e4dec8acf063df5bc3ac8` | MATCH |
| s6-n2400-C050-G100-40731224990.zip | 95527693 | `dUzY4ivqjEF+mlzJyZS3aIAI/Mg=` | `s8843aa53925f4a428b39b38611683f8c` | MATCH |
| s6-n2400-C070_G000-40731224990.zip | 82775948 | `HnfokRLFDhgE4dEU+lM/ZGocSqQ=` | `s00677665099943b9b0da82d5c5f31ba5` | MATCH |
| s6-n2400-C070_G030-40731224990.zip | 82776343 | `vPJuFKxFoJLbGoHbkZfnRHRgrK4=` | `sd566ca3617c546d89253e4fa2552dc9a` | MATCH |
| s6-n2400-C070_G050-40731224990.zip | 82776739 | `CKwMjz6P8jdzpCp4v6l20ZtLhKU=` | `s6d7ccf605d4e4eafb7aacdc810628d62` | MATCH |
| s6-n2400-C070_G070-40731224990.zip | 82776281 | `hZLUYmgWhIjOqrxKE3lAXNStz+c=` | `sb9ccf05b6224470caa8f129a0a889308` | MATCH |
| s6-n2400-C070-G100-40731224990.zip | 82683835 | `v9ZVWPzPHYjdFXz9OQiWO4C7veo=` | `s0a89154654764109afc48d7a4c671327` | MATCH |
| s6-n2400-C085_G000-40731224990.zip | 74384364 | `+9ar+aRzHvcZcBuNj3DdiTSuP6g=` | `s1d4e547952b846fcac45e4ac795c5abb` | MATCH |
| s6-n2400-C085_G030-40731224990.zip | 74384375 | `+tNW8W4iGh9KSgYNl6YWgl4fFW0=` | `s46fda59eca0c45fa8a7716c692d3396b` | MATCH |
| s6-n2400-C085_G050-40731224990.zip | 74384698 | `0eOEQC9IfBOlvdImheBpaiLXF7M=` | `s60ebfce2d80742a1895dab85f4c845a8` | MATCH |
| s6-n2400-C085_G070-40731224990.zip | 74384935 | `oJm20NnNb4BzgnTzcNKHPO8HT/M=` | `scf00a013d394466fb5c194299714b18b` | MATCH |
| s6-n2400-C085-G100-40731224990.zip | 74297741 | `rmvoh3zzYWsb1ZHm8gyuS5G+jGQ=` | `s44c812476e804073969e0111941679ab` | MATCH |

### OneDrive D3-S — same-algorithm QuickXorHash comparison

Live folder: [D3-S-Run-42295053851](https://onedrive.live.com?cid=893D06C344EA996B&id=893D06C344EA996B!s0f3055f9ce89404c9ef34c7dd004f187). 22 objects have a same-algorithm reference in the raw manifest (21 part artifacts plus the restore-manifest artifact). D3S-010 is present, but the manifest has only its GitHub SHA-256 metadata, not a QuickXorHash reference; it is therefore NOT_COMPARABLE.

| File | Bytes | Live QuickXorHash | OneDrive item ID suffix | Result |
|---|---:|---|---|---|
| D3S-000.transport.zip | 57217992 | `D7y4667MEMbFUwq6J1NSk1YDhNE=` | `s97137c4103fc414e8851d1cd7675acc2` | MATCH |
| D3S-001.transport.zip | 67211575 | `EqpzygJWsq4iHhFjrEygDGIVU1s=` | `s6e6b3e1f5f1445baa784af5f1b4baf02` | MATCH |
| D3S-002.transport.zip | 58714094 | `Cn6hIMJUkbFqJI1JGp0o/RdepfM=` | `s69a9094425ed4c46b66c41db7967bab3` | MATCH |
| D3S-003.transport.zip | 67417342 | `TYkLEsnd7ADiAIhvrbVPcKUQKf4=` | `sccecab35a3ff496086004947916ca4b4` | MATCH |
| D3S-004.transport.zip | 59379753 | `3ZjKZviChrfZJIyXheag8tKDgGo=` | `sf98a2e19908d4147aa64b96ff1f4de60` | MATCH |
| D3S-005.transport.zip | 67845297 | `pONMsd4RKIWBZ/vRnQ1vpXBueQ4=` | `s52698bfe03da4635bec80fa74e45ce50` | MATCH |
| D3S-006.transport.zip | 58572528 | `KPC0rHtON/0eaiP50aFysvhy6hI=` | `s98803307cbc6453c9ff5e4c8a1070c55` | MATCH |
| D3S-007.transport.zip | 68307733 | `4u/cfW51d1DHb8iTUJyXrtbHYvI=` | `s0370ba78546c43c8abeee3e5c924e0e7` | MATCH |
| D3S-008.transport.zip | 64665290 | `NJZOdhgC5NoLx0hnoUVZDtZe6FI=` | `s06b9e40ba1a0447d82fe8400d7fe97a6` | MATCH |
| D3S-009.transport.zip | 62230086 | `BaGRWx4/8rzdmIIjz3cin6Gy42I=` | `s76fc1880173b42aba949e9b9ea0aa662` | MATCH |
| D3S-010.transport.zip | 68156823 | `zN3KmSLjCxkOm7anJwFpTjrdtq0=` | `s707b7d1d6fbf499d9c5261d5d7ddbf32` | NOT_COMPARABLE |
| D3S-011.transport.zip | 58402523 | `E2tVCNnPuEgO7qBb5DV6Sa1Z9I4=` | `s1d6acf51fe194d579be79d9d519d57b8` | MATCH |
| D3S-012.transport.zip | 67644647 | `YA0MW/V5N9f8X3+gnhkTVPxnVio=` | `s6860c9e0744743b8afd9ad17203f36f7` | MATCH |
| D3S-013.transport.zip | 58261500 | `Iyh873FVCYAu+ZxNZBg/0zlhjBI=` | `sb0c52119f0854c849f8de8e917f659f1` | MATCH |
| D3S-014.transport.zip | 67317831 | `7EJeDrhbRLO0yCSsi1mKJCaHzHg=` | `s762333061c0a4ec9b78e45618a950b0a` | MATCH |
| D3S-015.transport.zip | 59464551 | `LWI0Z59x1m2a9FrVL1o8kPC8ldg=` | `s2f330aa303dc44d980e5ab13583eae87` | MATCH |
| D3S-016.transport.zip | 67750629 | `MPZ8xg+lFsZ6iQozsbJRUXKTH58=` | `se7f0e272bcc646a2a3f9ca3aabc36447` | MATCH |
| D3S-017.transport.zip | 58730422 | `NRNGiuhlfTBwMQODYtj3zLdZtmE=` | `sf0f0e8ff8dca49859001fc22b41abbde` | MATCH |
| D3S-018.transport.zip | 68117429 | `b/wzU7xagaSYvmGR1B+pPMbL918=` | `s3012bf01092f49d583684c8013086105` | MATCH |
| D3S-019.transport.zip | 63254501 | `Xbq0aWClLhR9aw5/hzb+wn7AL1M=` | `s4da40b593ff54854ad346a9f8e293983` | MATCH |
| D3S-020.transport.zip | 63626242 | `NZ9KJ4frwvdsgnR16ietqiTdWzM=` | `scb62af5af7b8478e9a94df66ddb1dd7c` | MATCH |
| D3S-021.transport.zip | 62471932 | `vKZ0oE5qI8hFXclchNZ0R+kK9LU=` | `se856dee64a3a4b4b9bc2194b97f327fb` | MATCH |
| OD-Multipart-D3S-Restore-Manifest.zip | 3079 | `hC+dKIVINUoFZXdDa+MUwSS0J64=` | `se605e3eb0e8e4f3cb9ee4e02a010236a` | MATCH |

### OneDrive D1/D3/D5 transport wrappers — NOT_COMPARABLE

Live parent folder: [Multipart-D3-D5-Transport-2026-11-06](https://onedrive.live.com?cid=893D06C344EA996B&id=893D06C344EA996B!s83634f573f994ab7a28ca1eda69683e4). These 20 files are transport ZIP wrappers around part bytes and JSON sidecars. The raw GitHub manifest does not contain matching wrapper-byte QuickXorHash references. A sidecar's source-part SHA-256 cannot be compared to a wrapper QuickXorHash. No status is inferred from size.

| File | Bytes | Live QuickXorHash (no matching wrapper reference) | OneDrive item ID suffix | Result |
|---|---:|---|---|---|
| D1-000.transport.zip | 83889219 | `n/vjjY8/PAbxhX/eD1v0ewuWURc=` | `sdcb6eb6614ae45e488ce2a20a53f7b93` | NOT_COMPARABLE |
| D1-001.transport.zip | 83899694 | `RHYRlSv3jD5PupIuNnEBvDA8RLk=` | `sf82447e3cd814313834ac4aac0253ef0` | NOT_COMPARABLE |
| D1-002.transport.zip | 83893599 | `6AtKazFHxqao1U1VpVMm29Iyj8s=` | `sa27de3d527f44177b940caf8f63d16b8` | NOT_COMPARABLE |
| D1-003.transport.zip | 59016113 | `KEJfjZTNVXye1nEmyVBEjaBxVRQ=` | `s8dea9d3aa75046948cc62980b9a4427b` | NOT_COMPARABLE |
| D1-RESTORE-MANIFEST.transport.zip | 705 | `pkflwUJmbxq2jLcOy++C0cUovWg=` | `s950f231d14e74511ad7417537e3e25b0` | NOT_COMPARABLE |
| D3-000.transport.zip | 59235715 | `J2GEq3JH3BiC5KXCyTFIvA7wYtc=` | `s1e09e191b5c94f48a12f71c525ba5674` | NOT_COMPARABLE |
| D3-001.transport.zip | 67469671 | `wyiwX4JWWqehe1sXLd3X453anIc=` | `s1e071468508940bd82f77c22fc7408a5` | NOT_COMPARABLE |
| D3-002.transport.zip | 76325778 | `m5jKzPEfz9ZoiwwPa2Vy+E0/6n4=` | `s31448ef71ec745da8cc14dd72df14c92` | NOT_COMPARABLE |
| D3-003.transport.zip | 60008524 | `ICUReZl27LFEjoKOzEJ7DxDrbFQ=` | `s4b125e477ac94e5a97afa0ee317108b0` | NOT_COMPARABLE |
| D3-004.transport.zip | 67638093 | `3mEZm9rSY9HDHe2rGF4WVD3XxV4=` | `s1374ffdd1c1f4b5e8ac3be5749e5ad57` | NOT_COMPARABLE |
| D3-005.transport.zip | 75211928 | `p0Z7/QC70wckYaR04dmr+v5vuXc=` | `s687a3803748f43eb9aee442f63e56b4f` | NOT_COMPARABLE |
| D3-006.transport.zip | 30050675 | `P+1na9TURKP+mguWoxnabgFnPRs=` | `s75b954a12530483a9dc7ea52993f707f` | NOT_COMPARABLE |
| D5-000.transport.zip | 57391379 | `riekUtISBtzw42opeGBuNXdvJMc=` | `s081dfd57c0ee4b8fae421dd17850b0af` | NOT_COMPARABLE |
| D5-001.transport.zip | 67216975 | `dVfivSmIeRiLB+JpELrNWNLkw/I=` | `sc2e40a454e1e421b9ac245fdec8bf43b` | NOT_COMPARABLE |
| D5-002.transport.zip | 78394029 | `ZmxvyMyapWudsRUb63fFIO2vckw=` | `sf5a8de0db11c4433ba6d32b9eae713c4` | NOT_COMPARABLE |
| D5-003.transport.zip | 58152718 | `0MaytP6YonIJWJsFrOvo6+ofiy8=` | `s13854916999440c1a0b7a8d4473bdf95` | NOT_COMPARABLE |
| D5-004.transport.zip | 67218118 | `3yRDId89JXz/0tes5b9PEKHpQ4U=` | `sb8d9a45cce064356aaf84ca00ec55e09` | NOT_COMPARABLE |
| D5-005.transport.zip | 77566761 | `vnj+cS+7vjuXf+RMnW1U8h4z3L0=` | `s37dcda8c21f64cbfae728d3010315590` | NOT_COMPARABLE |
| D5-006.transport.zip | 14619493 | `Dc9W+oDF7N4AbZiIqS/cmjLU+H0=` | `sf33e2ff8d66b4eaca3d439e5dc5f91c6` | NOT_COMPARABLE |
| RESTORE-MANIFEST.transport.zip | 1250 | `509GNZH2MUS813DKZsBLXFE5+XE=` | `s23ca9142678043fbb7c05cc5be5b76f9` | NOT_COMPARABLE |

## Preservation / restore gate — remains BLOCKED

1. No OneDrive raw file downloads, sidecar extraction, part reassembly, raw SHA-256 recomputation, ZIP CRC/member validation or restore test were performed in this metadata-only pass.
2. The existing bridge verifier `scripts/verify_tri_hash_preservation_bridge.py` requires GitHub Actions secrets `ONEDRIVE_GRAPH_ACCESS_TOKEN` and `DROPBOX_ACCESS_TOKEN`. The latest owner handoff records prior runs stopped because these secrets were absent/empty. Do not paste credentials into source or chat.
3. S6 artifacts remain GitHub Actions artifacts with expiry window beginning 2026-11-27; their OneDrive metadata matches do not prove independent second durable retention or restore.
4. Dropbox currently contains nine core source artifacts; it does not contain the full S6 set, the 20 D1/D3/D5 transport wrappers, or all D3-S parts. The secondary mirror copies are within the same Dropbox failure domain.
5. The 20 D1/D3/D5 wrappers still require sidecar validation, exact part coverage, reassembly against source artifact SHA-256/size, and restore checks. D3S-010 needs a same-algorithm reference or a raw-byte readback route that computes QuickXorHash from the original GitHub artifact.
6. Two independent durable failure domains and successful restore for all required artifacts are not proven.

Accordingly:
- `D3 overall = BLOCKED`; `D3 PASS_GAP_FREE = false`.
- `Global Preservation Gate = BLOCKED`.
- `D4 = NOT_STARTED`; D5 and D6 new exact-head executions are not authorized until their predecessor gates close.
- Existing D4/D5/D6 historical scoped records are not promoted to current exact-head closure.
- No Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, business-rule/identity change, main write, merge, force-push or Release was performed.

## Exact-head workflow evidence observed before this append-only record
- Branch HEAD: `c56cf4f13415b4e3310353aa3454633d67932d15`; main HEAD: `01a6f79eedc522bb734ed9c5ea31beee581f2468`.
- D3 Published Output Exact-HEAD Verification Run [42313924809](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42313924809): success on `c56cf4f13415b4e3310353aa3454633d67932d15`.
- D1-D2 Source Validation Run [42313924712](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42313924712): failure on `c56cf4f13415b4e3310353aa3454633d67932d15`; job `128221793274`; GitHub artifact download for artifact `12630457193` returned HTTP 503. Two other pinned artifacts in that job were downloaded and SHA-256 verified; run remains failure.
- This record is append-only evidence; it does not close D3 or authorize D4/D5/D6.
