# D5 Requirements Matrix — 2026-11-03

Overall: PASS_SCOPED_WITH_LIMITATIONS — package published and remote readback verified.

| Requirement | Status | Evidence |
|---|---|---|
| D5-01 Exact approved D3 Artifact ID/bytes/SHA-256 | PASS | D3 Artifact 13288779998 independently downloaded and byte-verified. |
| D5-02 Governing reference identity | PASS | Pinned immutable Gist bytes and SHA-256 verified. |
| D5-03 Two Excel workbooks | PASS | Exact expected sizes/SHA-256 and 185 sheets per workbook. |
| D5-04 Five DOCX reports | PASS | Exact D4 sizes/SHA-256; each archive reopened and parsed. |
| D5-05 Number Registry external resource | PASS | Exact pinned bytes and SHA-256 verified. |
| D5-06 Eight-member ZIP and safe paths | PASS | ZIP reopened; seven deliverables plus manifest; exact inventory and CRC passed. |
| D5-07 SHA256SUMS coverage | PASS | ZIP + manifest + seven deliverables + external Number Registry; 10 entries. |
| D5-08 Publish D5 Artifact | PASS | New GitHub Actions Artifact published with 30-day retention. |
| D5-09 Remote readback | PASS | Artifact downloaded by exact ID; outer digest, size, inventory, CRC and all three payload byte streams matched. |

## Verified fingerprints

- Tested source SHA: c757126ac27e8f6606f38b14324119cc22604858.
- Workflow Run: 42393413807.
- D5 ZIP: 519104624 bytes; SHA-256 f7004da675f2af8d3201ed1b51d5106b890fe521ab66e198c635be414e5421c7.
- manifest.json: 11003 bytes; SHA-256 a291a886fc6973f1f747cc74c98b0b8a25b01a7f96e32048c4c345c1d19484eb.
- SHA256SUMS.txt: 938 bytes; SHA-256 7c76cef416a08b6864e2b1a1c2e4159023e72cb0326793887cceb143d4ce0421.
- Artifact ID: 13582441423; size 519117017 bytes; digest sha256:ae84c0e9c27d5a0be7c5c37ec1f923676745013b86e3fd528178d830df61d0cc; expires 2026-12-07T16:54:42Z; retention 30 days.
- Artifact download URL: https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42393413807/artifacts/13582441423.
- Package classification: T2_INTERIM / NOT_FINAL_BLOCKED.
- Full 177-unique-test acceptance suite: NOT_RUN.
- No Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, identity change, main write, merge, Release, D6 or FINAL_ACCEPTED.
