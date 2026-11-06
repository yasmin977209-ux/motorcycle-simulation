# Bootstrap & Preservation Recovery Addendum — 2026-11-06

## Exact live state
- Repository: yasmin977209-ux/motorcycle-simulation
- Working branch: tmp/d1-rebuild-20261101
- Verified branch HEAD: 0e491a7eb9977654652c32e937c88ac643b2b68d
- main HEAD (read-only): 01a6f79eedc522bb734ed9c5ea31beee581f2468
- Compare: diverged; ahead 1019 / behind 2; merge base c6e54349a5e94f65d5aa9f83141f225d777bb474
- No branch workflow is queued or in_progress. No workflow was dispatched or restarted.

## Governing files verified from Raw bytes at this branch HEAD
- v2.4.0 reference: 401397 bytes; SHA-256 225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b; blob 9fe43bfbb2cbfd2bb7f7010866e7469506d22c33.
- Prompt library REV6: 101383 bytes; SHA-256 b7d88fbda6426a330c25e65f66e3c9c99b8ce86543742c568ec5df17ac635243; blob 22ad6f50dbe32226f2753d4e4e9af902984dc765.
- Owner master authorization and Dropbox decision were also read and Raw-hashed; the owner decisions remain unchanged.

## Current stage dispositions
- D0–D2: PASS_SCOPED_WITH_LIMITATIONS.
- D3: not closed. D3-18: PASS_SCOPED only. D3-S1/S2: not closed.
- D4–D6: historical PASS_SCOPED_WITH_LIMITATIONS only.
- E0/E1: PASS_SCOPED.
- E2 original accounting: BLOCKED.
- E2 replay: PASS_SCOPED_REPLAY_RECONSTRUCTION only.
- E3–E6: NOT_STARTED.
- Global Preservation: BLOCKED / PERMANENT_RETENTION_NOT_COMPLETE.
- The five protected accounting fields remain MISSING_EVIDENCE.

## Actions
- Run 42132551554 succeeded on exact HEAD 0e491a7eb9977654652c32e937c88ac643b2b68d; Artifact 13463952156.
- Run 42132551476 succeeded on the same exact HEAD; D3 published-output verification only, not D3-S closure.
- Historical long D3-S runs 42094642530 and 42099529400 were not restarted.

## Preservation findings
- Dropbox rescue root has nine files totaling 1,375,253,616 bytes.
- D3 Artifact 13288779998, D1 Artifact 12998778418 and D5 Artifact 13369179742 have matching Dropbox content_hash and sizes between root and secondary_verified_mirror. These are same-provider copies; content_hash is not GitHub Artifact SHA-256.
- No Dropbox raw-byte SHA-256, ZIP CRC/member audit or restore test has been performed.
- A 130,319,892-byte upload test for E2 Artifact 13385547304 failed with RESOURCE_EXHAUSTED / INSUFFICIENT_SPACE; no retry was attempted.
- Original S6 Run 40731224990 still has 20 unexpired scenario Artifacts totaling 1,531,244,201 bytes, absent from Dropbox; they expire 2026-11-27 between 17:23:02Z and 18:57:55Z. The parent run conclusion is failure while the 20 scenario jobs individually succeeded. These original artifacts contain the reduced daily projection; they do not restore the five missing full-balance fields.
- E2 Replay Run 41958935113 still has 21 unexpired Artifacts totaling 3,858,228,566 bytes, absent from Dropbox. They are replay reconstruction, not original accounting evidence.
- Artifact 13364064483 (Run 41916830283; 4,814 bytes; GitHub metadata digest sha256:fd5517de84bdb99a2a1e77068d471bea0cdce5de2145ed6f16c336e376b06b99; expiry 2026-12-04T21:32:18Z) exists in Dropbox root at /Motorcycle-Simulation-Rescue-2026-11-05/artifact-13364064483-D4-evidence.zip but was omitted from the previous retention inventory. This is an append-only correction; byte readback remains NOT_RUN.
- SharePoint was suggested as a possible independent provider but is not connected; no transfer was attempted. Resolve capacity or explicitly authorize/connect a second provider before copying.

## Next steps
1. Preserve the 20 original S6 artifacts before their 2026-11-27 expiry.
2. Preserve the 21 E2 replay artifacts separately, without relabelling them as original.
3. Verify all Dropbox copies against GitHub byte digests; inspect ZIP CRC/member manifests and run restore tests.
4. Add the append-only correction for Artifact 13364064483 to the retention inventory.
5. Keep D3-S1/S2 on hold; do not restart the prior long workflow without owner instruction.
6. Do not begin D4 before D3 is fully closed. Do not run Trials, Simulation, Monte Carlo or N expansion.

This record does not declare any parent stage closed and does not modify historical artifacts, manifests, business rules, identities, thresholds, main, or Releases.
