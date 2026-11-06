# Continuity Handoff — Owner Decision Hardening and D3 Preservation Gate
**Date:** 2026-11-07  
**Branch:** tmp/d1-rebuild-20261101  
**Pre-commit baseline:** 6273df9166d0b9d46b0114c798b6aece307b7262  
**Protected main:** 01a6f79eedc522bb734ed9c5ea31beee581f2468

## Resume point
The owner-approved scope decision resolves the D3/D5 workbook identity conflict and aligns D3-05..D3-12 with v2.4.0:
- canonical full EN/AR workbook outputs are Artifacts 13288779998 and 13369179742;
- 105 representative keys / 125 role assignments are the Full Logging deliverable scope;
- detailed sheets cover 25 P50 representative cases, one per scenario;
- C100 deterministic reuse is accepted for T2_INTERIM; do not launch a new Golden Trial.

The append-only effective state records D3-01..D3-18 and D3-S1/S2 as PASS_SCOPED. D3 as a phase remains BLOCKED because preservation and restore evidence are incomplete. D4 is NOT_STARTED.

## Existing exact run evidence
- D3 source Artifact 13288779998: Run 41754147172, tested SHA 3325fd961005c2c47de071d25904a748af7a21a6.
- D1 105-key size evidence: Run 42286384747, Artifact 13537657313; 105 verified keys.
- D3-S1/S2 and actual D3-18: Run 42295053851, tested SHA 86c70de8dad240283310fe3aea8d9141a6a03451.
  - D3-18 Job 128158006147.
  - EN Job 128158006443.
  - AR Job 128158006808.
  - Aggregate Job 128164769532.
  - D3-S combined Artifact 13542178172; 22 part artifacts plus restore manifest.
- D3 published-output exact-head verification: Run 42302342219 / Job 128183048784 / tested SHA 6273df9166d0b9d46b0114c798b6aece307b7262.
- D1-D2 exact-head validation: Run 42302342225 / Job 128183002595 / same tested SHA.

## Immediate next action
The new tri-hash workflow is push-triggered by the documentation/code commit. Before it can read external providers, ensure the repository has these read-only Actions secrets configured:
- ONEDRIVE_GRAPH_ACCESS_TOKEN (Microsoft Graph Files.Read / Sites.Read scope as required by the target drive)
- DROPBOX_ACCESS_TOKEN (files.metadata.read and files.content.read)

Do not paste token values into chat, source code or workflow logs. If the workflow fails because a secret is absent or expired, stop and request credential setup; do not downgrade the proof standard.

## Preservation conditions still open
- Verify all 20 S6 archives against GitHub Artifact digests.
- Verify all 20 D1/D3/D5 transport objects, sidecars and full reassembly against the original GitHub Artifacts.
- Verify all 23 D3-S objects against their GitHub artifact digests, then reassemble the 1,837,203,298-byte transport package and compare its SHA-256 and members with combined Artifact 13542178172.
- Verify the nine Dropbox core packages against Dropbox content_hash and GitHub Artifact digests.
- Transfer and verify the separate 20 E2 Replay scenario archives; they are not the 20 S6 archives.
- Prove two independent durable failure domains and successful restore for all required artifacts.

## Stop conditions
- Do not start D4 until D3 PASS_GAP_FREE and Global Preservation Gate closure are proven.
- Do not start D5 until D4 closes; do not start D6 until D5 closes.
- Do not run Test 176 or the D4 report builder ahead of D3 closure.
- No Trials, Simulations, Monte Carlo, N expansion, backfill, zero-fill, identity changes, main modification, merge, force-push or Release.
- Keep Gate B FAIL_SCOPED (10/10), Stability NOT_CONVERGED (0/60), N=4800 NOT_EXECUTED, Production Gate A NOT_DECLARED and the five missing accounting fields unchanged.

## Monitoring rule
If the tri-hash Actions run is still queued/in_progress after ten minutes of in-chat monitoring, stop polling. Report Run ID, tested Commit SHA, current status and elapsed time to the owner; await the owner's completion notice before resuming.


## Append-only correction — tri-hash initial run and repair
- Run 42307180251 / Job 128199351125 failed before remote reads: pytest could not import the scripts namespace. No provider credential check or external file download occurred.
- Corrected test discovery by adding the repository root to sys.path in tests/test_tri_hash_preservation_bridge.py. The correction commit will trigger a fresh run.
- Pre-fix SHA 9eda9580618b4f65f07a5285906613900d8f2eb7 was independently checked by D3 Run 42307180159 / Job 128199350695, D1-D2 Run 42307180254 / Job 128199350368, and Raw readback Run 42307180276 / Job 128199351164; all three succeeded.
- Await the new tri-hash run. If it passes tests and credentials, monitor up to ten minutes only; if still queued/in_progress at ten minutes, hand off to owner. If credentials are missing/expired, stop and request setup. Do not claim any provider byte verification from Run 42307180251.


## Current hard blocker — provider credentials
- The tri-hash verifier and its 4 unit tests are in GitHub. The second run passed all four tests and compiled the QuickXorHash C routine, then stopped because ONEDRIVE_GRAPH_ACCESS_TOKEN and DROPBOX_ACCESS_TOKEN repository secrets are absent/empty.
- This is not a provider hash failure; no OneDrive or Dropbox content was downloaded. No TRI_HASH_PRESERVATION_LEDGER artifact exists for Run 42307467332.
- Owner action: configure the two read-only secrets under GitHub repository Settings → Secrets and variables → Actions. Never paste token values into chat or commit them.
- Then run Actions → “Tri-hash Preservation Verification — GitHub / OneDrive / Dropbox” → Run workflow on tmp/d1-rebuild-20261101. Await the ledger artifact and inspect exact tested SHA, all three hashes, all part reassemblies, ZIP/member restore checks, and provider metadata matches.
- D3 exact output, D1-D2 and continuity raw readback succeeded on pre-final docs SHA c4e2b4aabbbb6d36045cd1a51a6a6dfe4128ce57 (Runs 42307467239, 42307467183, 42307467246 respectively). A subsequent documentation commit will trigger fresh exact-head validation.
- D3 remains BLOCKED; D4/D5/D6 are not started in this execution chain.


## Additional verifier hardening
- D1/D3/D5 multipart verification now reads source_bytes/source_sha256 from each part sidecar, checks consistency across all parts, reassembles, then downloads the exact source artifact and matches GitHub Artifact digest/size. This removes an unverified hard-coded D1 hash.
- The workflow writes an explicit BLOCKED_MISSING_PROVIDER_SECRETS JSON ledger artifact when either read-only secret is absent. It does not attempt provider reads.
- The registry hash field in the D3 closure record is corrected to NOT_VERIFIED_IN_THIS_SESSION; do not use the prior unverified literal.
- Pre-hardening exact-head validation SHA 110892985dcfffa61248918537b3da7d3e6ec28d: D3 Run 42307704095 / Job 128201134649 PASS; D1-D2 Run 42307703964 / Job 128201132997 PASS; Raw readback Run 42307704101 / Job 128201134226 PASS.
