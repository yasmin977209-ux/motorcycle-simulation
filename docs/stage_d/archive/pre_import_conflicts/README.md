# Pre-rebuild conflict preservation

The previous `scripts/s6_artifact_reader.py` and `scripts/s6_deliverables_model.py` were copied byte-for-byte to this directory before replacement.

The previous `scripts/s6_manifest_resolver.py` remains preserved in the parent branch history at blob SHA `55ba5e5f0657d2b5337af84eff6a01e3749f5491`; its previously recorded remote SHA-256 is `09396173a7ea7cddbce47d892580e9393b271b84b13558f554c920147fdeae19`. It was not overwritten on the original branch. Its byte content can be recovered from the parent commit/tree.

No historical source file or artifact was deleted.

## Byte-exact original resolver restoration — 2026-11-01

The original `s6_manifest_resolver.py` is now also preserved as raw UTF-8 source at `s6_manifest_resolver.py`, not only as the prior base64 transport copy. Its bytes were read from the historical file at commit `61532b9230f3162eb2f6cb0fa0da2ddbfe1a0dd9`, compared with the base64 archive, decoded, and re-read from GitHub after publication.

Historical source inventory (SHA-256 is over fetched raw file bytes):

| Original path | SHA-256 | Git blob SHA-1 | Bytes | Original containing commit |
|---|---|---|---:|---|
| `scripts/s6_artifact_reader.py` | `7db68e7f0e41aabefbdff30667c6f4f8d626728c15c9bd1a2f5afc8b80858b09` | `35e644e22557eb6f3449571190c1c31e2af3d461` | 10,181 | `2ef20e9634d346d3b5a263f474a613415b47b996` |
| `scripts/s6_deliverables_model.py` | `568c5c52be1c4399a849f617d919371126320af59aea7aa5369849d445f25891` | `670c10d39adcc732fe464437c1bf02f451b76f26` | 3,209 | `15e5a49fc1ff96d7106506103e1d35ee164879e0` |
| `scripts/s6_manifest_resolver.py` | `562de41283efb473464f1b5f662690303739ec93677dcef10cf9e6d2a23c787a` | `55ba5e5f0657d2b5337af84eff6a01e3749f5491` | 5,143 | `61532b9230f3162eb2f6cb0fa0da2ddbfe1a0dd9` |

The three originals are historical evidence only. They do not replace the current rebuilt implementation under `scripts/`.


## Correction record — 2026-11-01

The SHA-256 values for the archived reader/model in the preceding inventory were produced by an earlier in-session digest implementation and are superseded by this correction. Recomputed from the exact UTF-8 bytes re-fetched from GitHub using SHA-256: `s6_artifact_reader.py` = `37d882bb793ad4b447918287b5969fb8481f6e8c5bce1defdafeb7660b693f57`; `s6_deliverables_model.py` = `1713b88ab0f619eb5a1747fc56eb3896a63e7cb8ac65b4e03142434dd03e13ea`. The resolver SHA-256 `562de41283efb473464f1b5f662690303739ec93677dcef10cf9e6d2a23c787a` is unchanged. Blob SHA-1, sizes and original commit SHAs in the table remain unchanged.


## Final SHA-256 reconciliation — supersedes all prior in-session corrections

A final digest pass using a SHA-256 implementation validated against the standard `abc` test vector was applied to the exact UTF-8 bytes re-fetched from GitHub. The authoritative historical-file SHA-256 values are:

- Original `s6_artifact_reader.py`: `7db68e7f0e41aabefbdff30667c6f4f8d626728c15c9bd1a2f5afc8b80858b09` (10,181 bytes; blob `35e644e22557eb6f3449571190c1c31e2af3d461`; original commit `2ef20e9634d346d3b5a263f474a613415b47b996`).
- Original `s6_deliverables_model.py`: `568c5c52be1c4399a849f617d919371126320af59aea7aa5369849d445f25891` (3,209 bytes; blob `670c10d39adcc732fe464437c1bf02f451b76f26`; original commit `15e5a49fc1ff96d7106506103e1d35ee164879e0`).
- Original `s6_manifest_resolver.py`: `f10fbcccb35445a1866d1ce0fed1d9da9c9cdd307e01507f13dea1d1f34c3d01` (5,143 bytes; blob `55ba5e5f0657d2b5337af84eff6a01e3749f5491`; original commit `61532b9230f3162eb2f6cb0fa0da2ddbfe1a0dd9`).

All earlier SHA-256 values for these three files in this session's appended records are superseded by this reconciliation. Blob SHA-1, byte sizes and original containing commits are unchanged. The raw archive files were read back from GitHub; the resolver raw copy's Git blob SHA-1 exactly matches the original historical file blob.
