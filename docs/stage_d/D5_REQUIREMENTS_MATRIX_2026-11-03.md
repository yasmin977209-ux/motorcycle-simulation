# D5 Requirements Matrix — 2026-11-03

Overall: PASS_SCOPED_WITH_LIMITATIONS — package published and remote readback verified.

| Requirement | Status | Evidence |
|---|---|---|
| D5-01 Exact approved D3 Artifact ID/bytes/SHA-256 | PASS | D3 Artifact 13160434943 independently downloaded and byte-verified. |
| D5-02 Governing reference identity | PASS | Pinned immutable Gist bytes and SHA-256 verified. |
| D5-03 Two Excel workbooks | PASS | Exact expected sizes/SHA-256 and 185 sheets per workbook. |
| D5-04 Five DOCX reports | PASS | Exact D4 sizes/SHA-256; each archive reopened and parsed. |
| D5-05 Number Registry external resource | PASS | Exact pinned bytes and SHA-256 verified. |
| D5-06 Eight-member ZIP and safe paths | PASS | ZIP reopened; seven deliverables plus manifest; exact inventory and CRC passed. |
| D5-07 SHA256SUMS coverage | PASS | ZIP + manifest + seven deliverables + external Number Registry; 10 entries. |
| D5-08 Publish D5 Artifact | PASS | New GitHub Actions Artifact published with 30-day retention. |
| D5-09 Remote readback | PASS | Artifact downloaded by exact ID; outer digest, size, inventory, CRC and all three payload byte streams matched. |

## Verified fingerprints

- Tested source SHA: 4aa8172c829f1545e4509f5196cd2a23e24ec0ad.
- Workflow Run: 41704252218.
- D5 ZIP: 519102426 bytes; SHA-256 300720a318864fb3969a8813a76c65473be3c8648bea7fb359de23230a8ff4f5.
- manifest.json: 11456 bytes; SHA-256 db41532d87791da707a512e65a689ddad2066bb8bfceead53633a18fd66710c7.
- SHA256SUMS.txt: 938 bytes; SHA-256 1354c8e8283ac6fd14b8345153f5fb61d16190d959eaa6a474be8eecc4a18a5f.
- Artifact ID: 13264003231; size 519115272 bytes; digest sha256:7da3dc1bba9972854536b3615f567029e66a0988e90c79da2a555b10b85b9fe5; expires 2026-12-03T19:37:05Z; retention 30 days.
- Artifact download URL: https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41704252218/artifacts/13264003231.
- Package classification: T2_INTERIM / NOT_FINAL_BLOCKED.
- Full 177-unique-test acceptance suite: NOT_RUN.
- No Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, identity change, main write, merge, Release, D6 or FINAL_ACCEPTED.
