# D3-S OneDrive Transfer Reconciliation — 2026-11-07

## Scope and source identity

- Repository: `yasmin977209-ux/motorcycle-simulation`
- Branch: `tmp/d1-rebuild-20261101`
- Source branch HEAD / D3-S tested SHA: `86c70de8dad240283310fe3aea8d9141a6a03451`
- Protected `main` at preflight: `01a6f79eedc522bb734ed9c5ea31beee581f2468` (read-only; not modified).
- Workflow: [Run 42295053851](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42295053851), completed `success`, all four jobs successful.
- OneDrive destination: [D3-S-Run-42295053851](https://onedrive.live.com?cid=893D06C344EA996B&id=893D06C344EA996B!s0f3055f9ce89404c9ef34c7dd004f187)
- Parent: [Multipart-D3-D5-Transport-2026-11-06](https://onedrive.live.com?cid=893D06C344EA996B&id=893D06C344EA996B!s83634f573f994ab7a28ca1eda69683e4)

## Transfer result

- GitHub Actions transport artifacts: 22 part artifacts (`D3S-000` through `D3S-021`) plus one restore-manifest artifact.
- OneDrive readback inventory: 23/23 matching file items found; 23/23 sizes equal the GitHub artifact `size_in_bytes`.
- Aggregate uploaded wrapper bytes: 1,394,763,799.
- Each OneDrive file is the corresponding GitHub Actions artifact ZIP wrapper (`.transport.zip`), which contains the `.bin` part and its JSON sidecar; the manifest is also retained as its Actions ZIP wrapper. The raw `.bin` and `.json` members have **not** been extracted into standalone OneDrive files.
- OneDrive Graph metadata exposes `quickXorHash` for these objects, not `sha256Hash`. A raw-file fetch for `D3S-000.transport.zip` returned a file reference, but the connector did not expose the bytes/hash to the available local hashing runtime. Therefore no OneDrive raw-byte SHA-256 comparison is claimed.
- No remote extraction/reassembly or ZIP CRC/member validation was performed on OneDrive copies. Do not classify the OneDrive byte integrity or restore as VERIFIED_LIVE.

## Per-object inventory

| GitHub artifact | Artifact ID | GitHub bytes | GitHub artifact SHA-256 | OneDrive item ID | OneDrive bytes | OneDrive QuickXorHash |
|---|---:|---:|---|---|---:|---|
| OD-Multipart-D3S-000 | 13542313112 | 57217992 | `sha256:1aa27611a6e2bc9bc2e27b9aeccef291d136778f32e92591a6976a7a0d421780` | 893D06C344EA996B!s97137c4103fc414e8851d1cd7675acc2 | 57217992 | `D7y4667MEMbFUwq6J1NSk1YDhNE=` |
| OD-Multipart-D3S-001 | 13542996274 | 67211575 | `sha256:93188555431dd0fb9c74894aac586d72fa664049ddafb6a79448c7a74212426f` | 893D06C344EA996B!s6e6b3e1f5f1445baa784af5f1b4baf02 | 67211575 | `EqpzygJWsq4iHhFjrEygDGIVU1s=` |
| OD-Multipart-D3S-002 | 13542377114 | 58714094 | `sha256:de1abb632076a090ea2a814aafc12fa2d2ac08949b473092d5021432bfe824eb` | 893D06C344EA996B!s69a9094425ed4c46b66c41db7967bab3 | 58714094 | `Cn6hIMJUkbFqJI1JGp0o/RdepfM=` |
| OD-Multipart-D3S-003 | 13541793113 | 67417342 | `sha256:bc61eb345443ece7ecfbceada2afde5123b92369c36db3d13320a1ccb46337e8` | 893D06C344EA996B!sccecab35a3ff496086004947916ca4b4 | 67417342 | `TYkLEsnd7ADiAIhvrbVPcKUQKf4=` |
| OD-Multipart-D3S-004 | 13541323505 | 59379753 | `sha256:e4a29198b5def10fb7438c6745ef36c4ce738ad11708fcb0735b76e7dcd7ade7` | 893D06C344EA996B!sf98a2e19908d4147aa64b96ff1f4de60 | 59379753 | `3ZjKZviChrfZJIyXheag8tKDgGo=` |
| OD-Multipart-D3S-005 | 13541753217 | 67845297 | `sha256:4e9b86df84324469c4e6a3ee932105ed1e09e7cb59c59d17401fc44863a93832` | 893D06C344EA996B!s52698bfe03da4635bec80fa74e45ce50 | 67845297 | `pONMsd4RKIWBZ/vRnQ1vpXBueQ4=` |
| OD-Multipart-D3S-006 | 13542377163 | 58572528 | `sha256:a9173175c6744a821872839c6baa84ce4678b866c5cfa4df116810d5ad6c4fa7` | 893D06C344EA996B!s98803307cbc6453c9ff5e4c8a1070c55 | 58572528 | `KPC0rHtON/0eaiP50aFysvhy6hI=` |
| OD-Multipart-D3S-007 | 13542486944 | 68307733 | `sha256:cd0580218394830c116a4e8777c318273e57291e40c53ad7a39fd397618cd6f7` | 893D06C344EA996B!s0370ba78546c43c8abeee3e5c924e0e7 | 68307733 | `4u/cfW51d1DHb8iTUJyXrtbHYvI=` |
| OD-Multipart-D3S-008 | 13541858064 | 64665290 | `sha256:7c7ca105a0e633bca30fac810600345fb2ecf06bd4131f0443f5eb27b6391ef0` | 893D06C344EA996B!s06b9e40ba1a0447d82fe8400d7fe97a6 | 64665290 | `NJZOdhgC5NoLx0hnoUVZDtZe6FI=` |
| OD-Multipart-D3S-009 | 13541629124 | 62230086 | `sha256:1fd452d5a680830e07057ad00991205b0822e3286b55b4854daf8f7f51513468` | 893D06C344EA996B!s76fc1880173b42aba949e9b9ea0aa662 | 62230086 | `BaGRWx4/8rzdmIIjz3cin6Gy42I=` |
| OD-Multipart-D3S-010 | 13541174824 | 68156823 | `sha256:66f2a87e103fc561af36984bd290b6dae8824b2769c33215d8c353a783ff9b0a` | 893D06C344EA996B!s707b7d1d6fbf499d9c5261d5d7ddbf32 | 68156823 | `zN3KmSLjCxkOm7anJwFpTjrdtq0=` |
| OD-Multipart-D3S-011 | 13541898760 | 58402523 | `sha256:715744e863fdec97bfc8ec494d08c4e858107f2ddebc334854e3d961533ecb9d` | 893D06C344EA996B!s1d6acf51fe194d579be79d9d519d57b8 | 58402523 | `E2tVCNnPuEgO7qBb5DV6Sa1Z9I4=` |
| OD-Multipart-D3S-012 | 13543020271 | 67644647 | `sha256:9d04c41180801e8a3574e10f87af9c152cce30b6403c2bc276ccd5b876cde63c` | 893D06C344EA996B!s6860c9e0744743b8afd9ad17203f36f7 | 67644647 | `YA0MW/V5N9f8X3+gnhkTVPxnVio=` |
| OD-Multipart-D3S-013 | 13541389295 | 58261500 | `sha256:4c4db9a372d9d951a55517ef9694cb70a61ff9588f9a9e20f3cb9ff3950747e2` | 893D06C344EA996B!sb0c52119f0854c849f8de8e917f659f1 | 58261500 | `Iyh873FVCYAu+ZxNZBg/0zlhjBI=` |
| OD-Multipart-D3S-014 | 13541484157 | 67317831 | `sha256:463d5b6ffbf84a268c5fff31f2b838ae0e2d4a6ce1cf877c0b4ccc55e9efa999` | 893D06C344EA996B!s762333061c0a4ec9b78e45618a950b0a | 67317831 | `7EJeDrhbRLO0yCSsi1mKJCaHzHg=` |
| OD-Multipart-D3S-015 | 13541414258 | 59464551 | `sha256:86090faac3b01fbcb84369ea5cc5950994003c9b07a9eda877fe6b619f21cb5d` | 893D06C344EA996B!s2f330aa303dc44d980e5ab13583eae87 | 59464551 | `LWI0Z59x1m2a9FrVL1o8kPC8ldg=` |
| OD-Multipart-D3S-016 | 13543015359 | 67750629 | `sha256:c8742725d5ad0977994942d2634c4354b4b87fdfb4ba3c2520788ec4b1f3e3ec` | 893D06C344EA996B!se7f0e272bcc646a2a3f9ca3aabc36447 | 67750629 | `MPZ8xg+lFsZ6iQozsbJRUXKTH58=` |
| OD-Multipart-D3S-017 | 13541484188 | 58730422 | `sha256:80650744bdff7e5363d6379238f1c9bee3f17854737089554ce60f8a6c670343` | 893D06C344EA996B!sf0f0e8ff8dca49859001fc22b41abbde | 58730422 | `NRNGiuhlfTBwMQODYtj3zLdZtmE=` |
| OD-Multipart-D3S-018 | 13543105044 | 68117429 | `sha256:77d078c6884e113143094ad4b5f862023ac5ecee475b8dc88f2091da8a8d5c20` | 893D06C344EA996B!s3012bf01092f49d583684c8013086105 | 68117429 | `b/wzU7xagaSYvmGR1B+pPMbL918=` |
| OD-Multipart-D3S-019 | 13541988784 | 63254501 | `sha256:8d39b231df94ae5ee0f48e4f6d653f942494b5f98414425c9937bf63c0cd3cf9` | 893D06C344EA996B!s4da40b593ff54854ad346a9f8e293983 | 63254501 | `Xbq0aWClLhR9aw5/hzb+wn7AL1M=` |
| OD-Multipart-D3S-020 | 13541569332 | 63626242 | `sha256:ab3c0cab8463ee78fc5460a92bc49353b99d7042fa5ab036cadeaa4f56504820` | 893D06C344EA996B!scb62af5af7b8478e9a94df66ddb1dd7c | 63626242 | `NZ9KJ4frwvdsgnR16ietqiTdWzM=` |
| OD-Multipart-D3S-021 | 13542691802 | 62471932 | `sha256:54b721721b6af65605e6ed9c4dcae4d72a5da45d05f28201e61ce3cb69e48bc7` | 893D06C344EA996B!se856dee64a3a4b4b9bc2194b97f327fb | 62471932 | `vKZ0oE5qI8hFXclchNZ0R+kK9LU=` |
| OD-Multipart-D3S-Restore-Manifest | 13542068569 | 3079 | `sha256:57a1bd1b78507b577284a3b2ab6610524fdbcd558a898bff11bd63e0b1bbce53` | 893D06C344EA996B!se605e3eb0e8e4f3cb9ee4e02a010236a | 3079 | `hC+dKIVINUoFZXdDa+MUwSS0J64=` |

## D3-S engineering evidence from Run 42295053851

- Source artifact `13288779998` was downloaded by the workflow and its raw SHA-256/size and ZIP CRC matched the pinned source: 535,567,142 bytes; SHA-256 `e49b206d8d80034b1dc0cb284bfee76d81f9e9759e2459b1608fad2f5c933ffe`.
- EN and AR each produced five C partitions, 45 sheets per partition (10 shared/support sheets plus 35 scenario sheets), covering all 25 C×G scenario IDs exactly once per language.
- Each language reassembled to 185 sheets; 185/185 original worksheet XML parts and corresponding relationship parts were byte-identical; sharedStrings, styles, workbook.xml, workbook relationships and content-types were checked; ZIP CRC passed and openpyxl reopened the reassembled workbook.
- EN reassembly: 260,883,301 bytes; SHA-256 `5dc9beb7a81f7b6bd18cd68de1635d98c33a4bc0c5b85bac3207f62ed4d381f3`.
- AR reassembly: 260,885,226 bytes; SHA-256 `c61de96ed66be22483777340fa070745111204efd36aad63e834a25912430a19`.
- The pre-upload transport package was 1,837,203,298 bytes, SHA-256 `80e15d07873b51b0c1d1ff653546025a642361de26dbd57ef876a23c4cacc0f0`; 22 parts; the workflow's source-side raw reassembly check was `PASS_RAW_BYTES_EXACT`. This is not a OneDrive readback/reassembly result.
- D3-18 actual invocation: job `128158006147`, `PASS_SCOPED`, five Raw-read files, tested SHA above. The invocation recorded:
  - `Full_Results_EN.xlsx`: 27,722,355 bytes; SHA-256 `89712da93a43af7b03d69d516348e9c7e76c3374702d3d0e56418c5704e6f191`; blob `a01c1f4061da731de24fcc8d061113bb195e65b1`.
  - `النتائج_الكاملة_AR.xlsx`: 27,734,273 bytes; SHA-256 `914da4091c45114f3a61a5c847c0697832956b44a134116fd77e45fb9d39b461`; blob `056b7f482bbb84583526f093ae886e13b8c01356`.
  - `D3_BUILD_AUDIT.json`: 9,137 bytes; SHA-256 `422ee932594f8869cf4d0c5b5af76d18579219c47defee74f340197f21d702b5`; blob `32f8151d8d0aeaeec06e8fb25e62c273929c67ee`.
  - `D3_MANIFEST.json`: 6,249 bytes; SHA-256 `45777f4e446da0290847a78e20c964361853fdb69413503ba1febca08d08550c`; blob `e5390f37e8cf9d23d75d95c685912fa5a332ee66`.
  - `D3_18_INVOCATION_RECONCILIATION_2026-11-05.json`: 1,799 bytes; SHA-256 `df93d2143f2d8457f8100fe6cb5c661e49f86a179cc422d4f732381974ab556e`; blob `f292026738551d189b3a80c4861d8cdb1b5d5575`.

## Remaining D3 blockers and documentary reconciliation

The live `deliverables/D3_BUILD_AUDIT.json` and `deliverables/D3_MANIFEST.json` at this tested SHA continue to state `d3_gate_status=BLOCKED_MISSING_EVIDENCE`, and list D3-18 as `NOT_RUN`. The actual D3-18 invocation above is newer, scoped execution evidence; it does not silently rewrite those historical files. Record the mismatch as an append-only correction, not as a retroactive edit.

- D3-05: `PASS_SCOPED_WITH_LIMITATIONS`; C100 deterministic daily reuse (5 scenarios × 2,198 rows) only; C100 Golden revalidation `NOT_RUN`.
- D3-06: `PASS_SCOPED_WITH_LIMITATIONS`; 105 representative keys / 125 role assignments only; normalized Full Logging remains `NOT_VERIFIED_105_OF_105`, not 48,000-trial full logging.
- D3-07..D3-12: `PASS_SCOPED_WITH_LIMITATIONS` for 25 selected representative P50 cases per respective ledger, not full-cohort detail.
- D3-13: `PASS_SCOPED` for 49,500 source-backed close dates across 25 scenarios.
- D3-14..D3-16: `PASS_SCOPED`; D3-17: `PASS_SCOPED_WITH_LIMITATIONS`.
- D3-18: actual test invocation `PASS_SCOPED` on Run 42295053851; current audit/manifest status fields remain `NOT_RUN` and require append-only reconciliation.
- Five historical full-48K accounting fields remain `MISSING_EVIDENCE`: `Accounts_Receivable`, `Accumulated_Depreciation`, `Gross_Bike_Assets`, `Guarantee_Claim_Receivable`, `Total_Assets`. No inference, zero-fill or backfill was performed.
- Financial Gate A remains `PASS_SCOPED`; Production Gate A `NOT_DECLARED`; Gate B N=2400 `FAIL_SCOPED (10/10)`; Stability `NOT_CONVERGED (0/60)`; N=4800 `NOT_EXECUTED`.

## Gate disposition

- D3-S on GitHub: `PASS_SCOPED` only.
- OneDrive upload inventory and size readback: `REPORTED_ONLY` for integrity; exact object presence and size match do not equal raw-byte SHA-256 proof.
- OneDrive SHA-256 readback / remote ZIP CRC / member hashes / restore: `MISSING_EVIDENCE`.
- Overall D3: `BLOCKED_MISSING_EVIDENCE`; not `PASS_GAP_FREE`.
- Global Preservation Gate: `BLOCKED / PERMANENT_RETENTION_NOT_COMPLETE`. Requirements in REV6 §17.11 include two independent durable destinations, raw SHA-256 readback for each, and restore tests. The new D3-S files currently have only the OneDrive copy; the existing Dropbox rescue set is not a second verified copy of these 22 D3-S transport objects.
- D4: `NOT_STARTED`; do not start until D3 is independently proven `PASS_GAP_FREE` and all required preservation gates are met.

## Next permitted actions

1. Obtain a supported OneDrive raw-byte readback path that exposes bytes to a hashing/reassembly runtime; hash all 22 parts and the manifest against source digests, extract the ZIP wrappers, compare each inner `.bin`/JSON sidecar against manifest records, reassemble the 1,837,203,298-byte transport package and verify its SHA-256 and ZIP CRC.
2. Add the 23 objects to an independently authorized second durable provider and repeat byte-level readback/restore.
3. Resolve D3's source-evidence limitations only from authorized original sources; do not invent the five missing accounting fields or expand the scope.
4. Reconcile D3-18 `NOT_RUN` in the current audit/manifest via an append-only correction referencing the exact invocation above; preserve the existing files unchanged.

No D4 work, Trial, Simulation, Monte Carlo, N expansion, identity change, backfill, zero-fill, main write, merge, force-push, Release or final acceptance was performed.
