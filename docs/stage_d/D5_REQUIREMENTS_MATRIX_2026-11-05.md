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

- Tested source SHA: baf696af1e951cbf4a79e8a9e009c60c6b053b2d.
- Workflow Run: 41928234377.
- D5 ZIP: 519104296 bytes; SHA-256 313fa322ffbdda858efa973b5e3e264c26b55cfff0609634b0c919c33733b107.
- manifest.json: 11003 bytes; SHA-256 5896249f0c3061796229323d1c6a5e9ff05f8436b9a1915376ca15adcb2bb8c5.
- SHA256SUMS.txt: 938 bytes; SHA-256 349fc09650297bda69e274ca642fca2ce605bc101b9ba2b3c0a57e02624cf8b7.
- Artifact ID: 13369179742; size 519116689 bytes; digest sha256:80caf0567e31a6bf5397543dac8ef191b38999105dd3cedce4c3dad75b20bff1; expires 2026-12-04T22:49:30Z; retention 30 days.
- Artifact download URL: https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41928234377/artifacts/13369179742.
- Package classification: T2_INTERIM / NOT_FINAL_BLOCKED.
- Full 177-unique-test acceptance suite: NOT_RUN.
- No Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, identity change, main write, merge, Release, D6 or FINAL_ACCEPTED.
