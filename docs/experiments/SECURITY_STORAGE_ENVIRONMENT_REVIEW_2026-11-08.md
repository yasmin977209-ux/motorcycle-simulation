# Security, storage, and environment evidence — 2026-11-08

## Storage verification — scoped C100 archive

Artifact: `artifact-12630457193-C100-reuse.zip`

- Dropbox path: `/Motorcycle-Simulation-Rescue-2026-11-05/artifact-12630457193-C100-reuse.zip`
- Dropbox size: 361,733 bytes
- Dropbox `content_hash`: `c610607220ae27e71c2e64e0cfd897b305b6558d3612c97fb112e4f2fd1d1f22`
- OneDrive drive ID: `893d06c344ea996b`
- OneDrive item ID: `893D06C344EA996B!scc7a41da59d94765a85ccce622171948`
- OneDrive QuickXorHash: `FzwoGgv29tNjrGAci0F+eBp16ZM=`
- OneDrive raw-read SHA-256: `c977d1cbb5204919eadc72358533f77cdbbc239902bcd6f921bf1a915a716e79`
- OneDrive raw-read size: 361,733 bytes
- Dropbox content hash recomputed from the OneDrive-restored bytes: `c610607220ae27e71c2e64e0cfd897b305b6558d3612c97fb112e4f2fd1d1f22` — exact match.

Restore validation on the OneDrive raw bytes:
- ZIP integrity: `No errors detected in compressed data`.
- Extracted files: 9.
- Restored Golden SHA-256: `39950d91c3b40b11bea0997b8504ac932a57bcc0ef8e0c51e12d031342a53327`.
- Restored manifest SHA-256: `2097284d77ead6b00492bf75830d09aeef8dbde4aaa1c15dae6a877dc7e9ff04`.

### Storage verdict

`PASS_SCOPED_ONE_DRIVE_RESTORE_AND_CROSS_PROVIDER_HASH_MATCH`.

This is not a full two-provider restore test: the OneDrive bytes were actually fetched and extracted; Dropbox's server-side content hash matched those bytes, but the Dropbox raw download itself was not completed in this session. The full rescue folders were not restored. The Dropbox `secondary_verified_mirror` remains inside the same provider and is not a separate failure domain. Do not upgrade the overall storage gate to PASS.

The earlier OneDrive 403 readback problem is resolved for this specific item; it is not evidence that every OneDrive item is readable.

## Gitleaks security scan

- Gitleaks version: `8.30.0`.
- PR-diff scan: `no leaks found`.
- Full reachable Git history scan: 3,534 commits, approximately 222.38 MB scanned.
- Findings: 9, all rule `generic-api-key`.
- No secret value was printed or included in this report.

Finding metadata only:

| File | Line | Finding rule | Commit |
|---|---:|---|---|
| `docs/PROJECT_CONTINUITY.md` | 2670 | generic-api-key | `21fa1e9762bbe022833428dd61983dbc853134c9` |
| `docs/stage_d/D1_REBUILD_CLOSURE_2026-11-01.md` | 27 | generic-api-key | `21fa1e9762bbe022833428dd61983dbc853134c9` |
| `docs/stage_d/D1_CORRECTIVE_EVIDENCE_ADDENDUM_2026-11-01.md` | 92 | generic-api-key | `21fa1e9762bbe022833428dd61983dbc853134c9` |
| `docs/stage_d/D1_REMOTE_EVIDENCE_LEDGER_2026-11-01.md` | 68 | generic-api-key | `21fa1e9762bbe022833428dd61983dbc853134c9` |
| `docs/stage_d/D1_REFERENCE_PUBLICATION_ATTEMPT_2026-11-01.md` | 201 | generic-api-key | `21fa1e9762bbe022833428dd61983dbc853134c9` |
| `docs/stage_d/STAGE_D_CONTINUITY_HANDOFF_2026-11-01.md` | 14 | generic-api-key | `21fa1e9762bbe022833428dd61983dbc853134c9` |
| `docs/stage_d/D1_REPOSITORY_CLOSURE.md` | 57 | generic-api-key | `21fa1e9762bbe022833428dd61983dbc853134c9` |
| `docs/stage_d/STAGE_D_SESSION_STATUS_2026-11-01.md` | 92 | generic-api-key | `21fa1e9762bbe022833428dd61983dbc853134c9` |
| `docs/continuity/SESSION_OUTPUTS.jsonl` | 91 | generic-api-key | `93efa6edb2bf68567e4a5e561380ba65b9b3dbcc` |

These are unclassified scanner findings, not confirmed credentials. Do not silently allowlist or rewrite history. A reviewer must determine whether each is a dummy/example or a live credential. Rotate any confirmed live credential through its issuing service and record the rotation without exposing its value. Historical files/commits were not modified.

## Runtime lock

- Python: CPython 3.11.18.
- Runner label: `ubuntu-24.04` (mutable hosted image).
- Packages: 15 exact packages.
- Hash lock: `requirements-lock-py311-hashed.txt`.
- Hash-lock SHA-256: `074944b6a48090723f51a1f25e0d9dcf5e29f3a5df025b064bef485c2daa6fbf`.
- Wheel hashes are for the CPython 3.11.18 / ubuntu-24.04 x86_64 environment only.
- Safe workflow regenerated the 15 hashes and diff-checked them against the committed lock successfully.
- `pip-audit` result: pending latest security workflow run.

The lock pins package artifacts; it does not pin the hosted runner image or the dependency-audit tool's own transitive dependencies.

## Execution workflow safety

The manual workflow is not a push/PR-triggered simulation. It requires:
- selected workflow branch HEAD separately pinned from model-source SHA;
- model source checked out under `execution-source`;
- exact model source SHA `ac0d009aa004976009ed01e97f96d019945e9ad6`;
- environment `s6-simulation-execution`;
- `S6_EXECUTION_ENVIRONMENT_LOCKED=true`;
- exact source, workflow HEAD, cohort, and N approval variables;
- `S6_OWNER_EXECUTION_DECISION_ID` secret equal to the dispatch decision ID.

The environment has not been configured/verified with required reviewers. The workflow has not been dispatched. No Trial or Simulation has run.
