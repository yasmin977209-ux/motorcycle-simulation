# Tri-Hash Preservation Ledger — 2026-11-07

## Authority and scope
Repository: `yasmin977209-ux/motorcycle-simulation`  
Branch observed before this commit: `fa55d396b3f0d5af78a9086e3b481e2f925c112d`  
Main read-only: `01a6f79eedc522bb734ed9c5ea31beee581f2468`  
Target inventory: 72 objects.

## Object inventory and metadata reconciliation

| Group | Target | Live inventory | Disposition |
|---|---:|---:|---|
| OneDrive S6 | 20 | 20 | Metadata recorded as MATCH |
| OneDrive D3-S | 23 | 23 | 22 metadata MATCH; D3S-010 NOT_COMPARABLE |
| OneDrive Multipart | 20 | 20 | 20 NOT_COMPARABLE; no comparable source hash |
| Dropbox | 9 | 9 | 9 previously reported MATCH; current content_hash not returned |

**Authoritative detailed count:** 51 MATCH / 21 NOT_COMPARABLE / 0 MISMATCH / 0 MISSING. The earlier 72/72 metadata-match summary is preserved as a historical claim but is not supported by the detailed per-object reconciliation.

### Current metadata recheck
- 42 OneDrive QuickXorHash values were re-read and matched the same-algorithm recorded reference.
- 21 OneDrive items remain NOT_COMPARABLE because a comparable source reference hash is absent (D3S-010 plus 20 multipart wrappers).
- 9 Dropbox items were re-listed and their identities/sizes rechecked; the connected metadata action did not return Dropbox content_hash in this session, so the 9 hash matches remain REPORTED_ONLY from the earlier reconciliation.
- OneDrive rescue root: 73 items; D3-S transport folder: 23 items; Multipart folder: 21 entries (20 wrappers plus the D3-S folder); Dropbox rescue root: 10 entries (9 target files plus the secondary mirror folder).

## Evidence states

| Evidence dimension | Current result |
|---|---|
| PROVIDER_METADATA_MATCH | 51 recorded; 42 OneDrive matches rechecked live, 9 Dropbox hashes not rechecked |
| RAW_BYTE_HASH_MATCH | NOT_RUN for all 72 |
| READBACK_VERIFIED | NOT_RUN for all 72 |
| RESTORE_VERIFIED | NOT_RUN for all 72 |
| MISSING | 0 in the recorded 72-object inventory |
| MISMATCH | 0 in the recorded 72-object inventory |
| NOT_TESTED / NOT_COMPARABLE | 21 not comparable; all raw byte hash and restore checks not run |
| Two independent durable failure domains | NOT_PROVEN |
| E2 Replay 20 transfer | NOT_TRANSFERRED |
| Global Preservation Gate | BLOCKED |

Metadata equality, raw-byte SHA-256 equality, readback, restore and failure-domain independence are separate proofs. None may be inferred from another.

## Additional exact-head evidence copied to OneDrive
Destination: `/Motorcycle-Simulation-Rescue-2026-11-05`

| GitHub Artifact | Run | Bytes | GitHub SHA-256 | OneDrive item ID | Raw download after upload |
|---|---:|---:|---|---|---|
| 13588455375 | 42407443575 | 4,012 | `5c19eb9fd5454d923260a2f9b8e94c8d932e7818fcfaee1fb9f9ea3f0de8497a` | `893D06C344EA996B!sed35022491b34b18a8c13cfb67c50fb8` | Downloaded; SHA-256 not computed; restore NOT_RUN |
| 13587862179 | 42407443567 | 6,325 | `aa974d58122ac02e35f30c24cdbd738be65f63be8919d00e8153719ed30cad45` | `893D06C344EA996B!sff8b473e3e374dd79b4a613872e4fd88` | Downloaded; SHA-256 not computed; restore NOT_RUN |
| 13587689091 | 42407443585 | 10,545 | `174fc4e225186d9619db405cb7c952dfe659bb72aeb8b0b7fa3f9f8e168ea922` | `893D06C344EA996B!se3621bff3b9e4a54b2f810b2bedaf5db` | Downloaded; SHA-256 not computed; restore NOT_RUN |
| 13586354284 | 42403657899 | 8,217 | `2bbd2edb3a948891c1da376079b93b6b3bbdb6d0a7149ec3859a62e81f2a20f1` | `893D06C344EA996B!s76f9eaccaae1430f93e98c0b2f3992b7` | Present; raw download requested; SHA-256 not computed; restore NOT_RUN |

D5 Artifact 13582441423 (519,117,017 bytes) was downloaded from GitHub, but OneDrive upload was blocked by the connector's 104,857,600-byte file-source limit. Dropbox write was not performed; exact destination and filename confirmation is required by the connected upload workflow.

## Fingerprint fields
For each object, keep these fields independent:
- `Git_Commit_SHA`: commit containing a repository file; not a content hash.
- `Git_Blob_SHA1`: Git blob object identifier.
- `SHA256`: SHA-256 computed from the actual bytes.
- `Exact_Size_Bytes`: byte length of the actual bytes.

No field is inferred from another. No provider metadata hash is relabeled as SHA-256.

## Current gate
`Global_Preservation_Status=BLOCKED`. Do not promote to PASS until all 72 objects have exact source-to-backup raw-byte SHA-256 comparisons, ZIP CRC/structure checks where applicable, actual restore tests, and independently evidenced failure domains. E2 Replay 20 remains a separate untransferred scope.
