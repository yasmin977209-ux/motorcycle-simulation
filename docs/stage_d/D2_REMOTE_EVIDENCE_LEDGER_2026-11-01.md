# D2 Remote Evidence Ledger — 2026-11-01

Repository: yasmin977209-ux/motorcycle-simulation  
Branch: tmp/d1-rebuild-20261101  
Evidence policy: a file is VERIFIED_LIVE only when its exact GitHub URL, SHA-256 from fetched Raw bytes, and containing commit are recorded. Git blob SHA-1 and byte size are supporting metadata.

## Pinned input Artifacts

| Input | Artifact ID | Size (bytes) | SHA-256 | Status |
|---|---:|---:|---|---|
| Aggregate | 12852969854 | 9,357,996 | ec05a69ae8968585decf83cf0716d56c264f47f86187cfd3cf53b11f52ca2e54 | VERIFIED_LIVE in D2 build workflow |
| Full Logging | 12998778418 | 310,827,203 | 403371cc8eb12880dda05529b4c83dd675bfa609e8680c09d35efa729c5b5aeb | VERIFIED_LIVE in D2 build workflow |
| C100 | 12630457193 | 361,733 | c977d1cbb5204919eadc72358533f77cdbbc239902bcd6f921bf1a915a716e79 | VERIFIED_LIVE in D2 build workflow |

## Existing Registry evidence (superseded by the completion run when a newer registry commit is produced)

- Registry path: results/number_registry.json
- Previous registry commit: c5e9c862c161dea89651d27e3a4eb5f5f35211ad
- Previous SHA-256: d8c701d0fc35cbd1566ebced5ccc4f40bb3dafe538d020dd7c89b1ec326c66bb
- Previous Git blob SHA-1: 824803e8543fff7c628586bd37ea6e3f706cf9ba
- Previous size: 24,137,036 bytes
- Previous validation: Run 41328486239 (SUCCESS); 22 passed / 9 skipped; source integration Run 41328814656 (SUCCESS; 31 passed).

## Completion validation
The completion workflow is configured to:
- verify the three pinned input artifacts by metadata and downloaded bytes;
- compile and run the D2 test modules;
- rebuild the deterministic registry without running any Trial or Simulation;
- validate every daily point through the indexed resolver;
- commit on the working branch;
- compare local HEAD with the remote branch HEAD;
- fetch every listed D2 deliverable from GitHub Raw and log its URL, byte count, SHA-256, Git blob SHA-1 and containing commit;
- upload the registry and complete D2 audit package only after all gates succeed.

The exact completion Run ID, final HEAD, file evidence triples and Artifact ID are emitted in that Run's logs and artifact metadata. Do not treat this ledger's pre-run state as proof of completion.


## Completion workflow record

- Workflow Run ID: 41332273796
- Triggering source SHA: 2407a8e832aa8fa01ed8951ce8f89cc8548a8dea
- Registry-containing commit: 024c71a909328cec379f3628df25981310c64fe7
- Final exact HEAD and file evidence triples are printed by the final Raw readback step of this Run; a failed Run is not accepted as evidence.


## Additional completion controls — 2026-11-01

- Regression test: `test_historical_local_report_is_unwrapped_without_loss` ensures the original 13,954-entry local-only report is preserved directly, without recursive canonical-audit nesting.
- Artifact-backed builder integration tests are configured with the three downloaded pinned ZIPs (`STAGE_D_AGGREGATE`, `STAGE_D_FULL_LOGGING`, `STAGE_D_C100`) rather than being skipped for missing local paths.
- Final readback package also includes `scripts/s6_number_registry.py`, `tests/test_s6_number_registry.py`, `.github/workflows/stage-d2-number-registry.yml`, and `D2_FINAL_HANDOFF_ADDENDUM_2026-11-01.md`.
- Continuity records are appended as raw UTF-8 bytes so existing carriage-return bytes are preserved.
