# Preservation and Recovery Status — 2026-11-07
**Repository:** `yasmin977209-ux/motorcycle-simulation` | **Branch:** `tmp/d1-rebuild-20261101` | **Pre-update HEAD:** `cd38117740c1577627fdebeb1ce9600019a5d338`

## Purpose
Separate the evidence already proven from provider-byte recovery, restore tests, retention and independent failure-domain requirements. Do not use the word "restored" for metadata-only matches.

## Verified
1. Stage A computed SHA-256, QuickXorHash and Dropbox content_hash from raw GitHub Actions Artifact ZIP bytes for 72 unique artifacts.
2. Stage A Artifact: 13557202516; Run 42330906466; Job 128276958747; tested SHA `cef3572d3ce49545cc44739324929685208245a7`; 11,125 bytes; SHA-256 `a785c6bc51f9427c9e728a94797829eb4cf83ab33fc6509e1e49a6a1044d3b25`.
3. Stage B compared provider metadata using matching algorithms and sizes:
   - OneDrive S6: 20/20 QuickXorHash + size.
   - OneDrive D3-S: 23/23 QuickXorHash + size.
   - OneDrive multipart D1/D3/D5: 20/20 QuickXorHash + size.
   - Dropbox rescue packages: 9/9 content_hash + size.
   - Total 72/72 metadata matches; 0 mismatches, 0 not-comparable in latest reconciliation.
4. D3-S transport transfer record states 23/23 wrapper objects and sizes present in OneDrive; these are GitHub Artifact ZIP wrappers containing parts/sidecars, not proof that standalone extracted .bin/.json files were restored to OneDrive.
5. Dropbox rescue root inventory contains nine core package ZIPs. Same-service secondary mirror is not an independent failure domain.

## Not proven / still open
- Provider raw-byte downloads from OneDrive and Dropbox followed by independent SHA-256 recomputation: NOT_RUN in this evidence chain.
- Full provider-side reassembly and restore test for S6/D3-S/multipart objects: NOT_RUN.
- E2 Replay 20 scenario archives: NOT_TRANSFERRED; this is a separate set from the 20 S6 archives.
- Two independent durable failure domains for every required artifact: NOT_PROVEN.
- Full restore test from independent storage: NOT_PROVEN.
- Retention beyond current artifact expiry windows: must be verified by live metadata, not inferred from prior listing.

## Correct interpretation
- Stage A proves raw GitHub Artifact bytes and computes three hashes on those bytes.
- Stage B proves provider metadata matches those computed hashes by algorithm and size.
- Stage B is not a provider raw-byte readback, not a restore, and not a proof of independent failure domains.
- Global Preservation Gate remains BLOCKED independently before E3. Under the owner-approved REV6 scope correction it does not block D3/D4/D5/D6.

## Recovery checklist for the next authorized work
- Recheck live OneDrive/Dropbox objects and exact item IDs; do not reuse stale IDs without confirming.
- Download provider bytes where connector permissions allow; calculate SHA-256 on downloaded bytes; compare to Stage A manifest.
- Reassemble multipart objects from verified raw parts and compare total byte count/SHA-256; validate ZIP CRC and required members; open XLSX/DOCX as applicable.
- Transfer the separate E2 Replay 20 archives and verify them independently.
- Establish two independent durable failure domains and perform a restore test from each required retained copy.
- Record source identity, provider object ID, byte count, SHA-256, hash algorithm, retrieval timestamp, restore result, and artifact retention/expiry. Preserve all historical records append-only.

No main writes, Trial/Simulation/Monte Carlo, N expansion, backfill, zero-fill, identity changes or historical artifact mutation are authorized by this status note.
