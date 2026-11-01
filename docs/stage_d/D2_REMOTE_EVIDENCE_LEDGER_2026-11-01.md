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


## Completion workflow record

- Workflow Run ID: 41333300530
- Triggering source SHA: a830827c4977ba9b9121903225da5c42f8ca0959
- Registry-containing commit: 50673bf094c38e8a73de2980df719df2963a3dc6
- Final exact HEAD and file evidence triples are printed by the final Raw readback step of this Run; a failed Run is not accepted as evidence.


## Final D2 completion proof — 2026-11-01 (append-only)

- D2 completion workflow [41333300530](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41333300530): SUCCESS. Exact final branch HEAD: `789b9017986cb240d9a82428227f6a03adee6f3c`.
- D1-D2 source/integration validation [41333300571](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41333300571): SUCCESS, 34 passed, 0 failed, 0 skipped on triggering SHA `a830827c4977ba9b9121903225da5c42f8ca0959`.
- D2 focused + artifact-backed tests in the completion run: 34 passed, 0 failed, 0 skipped.
- Full Daily resolver validation: 2,086,550 of 2,086,550 points resolved and matched exact numerator/denominator, series, date and deterministic ID; 1,000 series; 2,640 explicit entries.
- Registry-containing commit: `50673bf094c38e8a73de2980df719df2963a3dc6`. Registry: 24,137,036 bytes; SHA-256 `47e72ecae6f8c9f8cff3c8599909c42bf5e8a4ddaa3d3bceb0be764717b7b321`; Git blob SHA-1 `ba7ead51a67b244ebfcb87d35be59dbaf62fccfc`.
- Artifact [13093114758](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41333300530/artifacts/13093114758): 3,613,833 bytes; ZIP SHA-256 `6460a72442b6c51c754f47956914f8ef7302ba3fb710dc9610b6075d94424127`; downloaded and CRC-tested successfully; 10 files including registry, audit, matrix, ledger, final handoff, source, tests and workflow.
- The original historical local-only audit is now directly preserved at `historical_local_report.original_report`: 13,954 entries, `REPORTED_ONLY_LOCAL_ONLY`; no recursive nesting.
- Superseded Run 41333271314 passed its tests but failed its exact-head assertion because the branch advanced while it ran. The later exact-head source validation Run 41333300571 passed on the stable trigger SHA; the final D2 completion Run independently passed exact-head/raw readback on the resulting final commit.
- `main` remains `c6e54349a5e94f65d5aa9f83141f225d777bb474`. D2 disposition remains `PASS_SCOPED_WITH_LIMITATIONS`; D3 is NOT_STARTED.

### Final exact-head Raw evidence triples

The following 13 files were fetched from GitHub Raw at the exact final HEAD; their returned text matched the GitHub file read, and SHA-256, Git blob SHA-1 and byte size were logged by the successful completion workflow:

| Path | Bytes | SHA-256 | Git blob SHA-1 | Commit |
|---|---:|---|---|---|
| `results/number_registry.json` | 24137036 | `47e72ecae6f8c9f8cff3c8599909c42bf5e8a4ddaa3d3bceb0be764717b7b321` | `ba7ead51a67b244ebfcb87d35be59dbaf62fccfc` | `789b9017986cb240d9a82428227f6a03adee6f3c` |
| `docs/stage_d/D2_NUMBER_REGISTRY_AUDIT.json` | 5600 | `22b7378b9e3dd94b963df22fcd9cf0233ef9eed2f47f446c6387deae3ad96526` | `67117a987887589fe6e120653e200b2e1610eaf4` | `789b9017986cb240d9a82428227f6a03adee6f3c` |
| `docs/stage_d/D2_NUMBER_REGISTRY_AUDIT.md` | 10680 | `656a0f928548350b5016501fba89633c0f5f374e8e7f9ed9b89054dd4cd7dc24` | `5cc256aa4e3835f4745da3e64b0560755a48fe22` | `789b9017986cb240d9a82428227f6a03adee6f3c` |
| `docs/stage_d/D2_NUMBER_REGISTRY_AUDIT_LIVE_2026-11-01.json` | 4247 | `6e53fa8cf311d8b3f70baf15ab11d85fa1352c3655b929e2893b68180da07f1c` | `a369c90a12894e2665ad0ede6b40e16041fe101e` | `789b9017986cb240d9a82428227f6a03adee6f3c` |
| `docs/stage_d/D2_REQUIREMENTS_MATRIX_2026-11-01.md` | 4429 | `8c41683fc770c0daceaf7d8908a334b0f0d5044a4961be9cb678639c8d4b854c` | `18165a0af650d769fa41fbb99777bd52d5113894` | `789b9017986cb240d9a82428227f6a03adee6f3c` |
| `docs/stage_d/D2_REMOTE_EVIDENCE_LEDGER_2026-11-01.md` | 3667 | `0dd6ce6c738157c7f307d1ed60fe748d4f8664bd7f43f04aa100b47140d221a7` | `9af5bd2df97acf62adcec717e76de145750a64d4` | `789b9017986cb240d9a82428227f6a03adee6f3c` |
| `docs/stage_d/D2_FINAL_HANDOFF_ADDENDUM_2026-11-01.md` | 4147 | `00fed131d19512fd632622a6410dad872616b565550a2dfb08e8214eb2471187` | `e5ffbd15916f0a01fa725b9f635290416d69b40f` | `789b9017986cb240d9a82428227f6a03adee6f3c` |
| `scripts/s6_number_registry.py` | 41080 | `6eac6ecdcf8e2bf169f81549284613982aeb6d2539b71feb16477eccf09bc3a3` | `af0f8585940ae9208b43e7181e5562f1912816d2` | `789b9017986cb240d9a82428227f6a03adee6f3c` |
| `tests/test_s6_number_registry.py` | 7254 | `70be1accbf90516a1ba7045549b0144899fac22d757db4502549e89b15af7163` | `2fe03aa5f701fb844e5ea0cd9fa3e88321b9729e` | `789b9017986cb240d9a82428227f6a03adee6f3c` |
| `.github/workflows/stage-d2-number-registry.yml` | 22077 | `9608c01704519756dda4eb529457c15c8bb5e3d7637f7151327137c887d2dcd0` | `8dd7f71613bacc014fb12fc198e37197dc8349d1` | `789b9017986cb240d9a82428227f6a03adee6f3c` |
| `docs/PROJECT_CONTINUITY.md` | 470193 | `78587cacf540384c3eaf1e3445af0132c229b501c5d834810b9b21d80d9e5d5c` | `c0e7f6671670779442010556505ab6a791210e32` | `789b9017986cb240d9a82428227f6a03adee6f3c` |
| `docs/stage_d/STAGE_D_SESSION_STATUS_2026-11-01.md` | 24104 | `a675793335bb3bd833f58a0549fd5f76c0ef747b690d6086057bfcdce3ec592e` | `04637bd59a591cf74a7d71a76e2c1defbec25c3e` | `789b9017986cb240d9a82428227f6a03adee6f3c` |
| `docs/stage_d/STAGE_D_CONTINUITY_HANDOFF_2026-11-01.md` | 11528 | `44eba10c65c6ac4476a8f87ddde9aebe373d71e9d370548456bfad0e0bf7b6ce` | `69d04763de30685303a970220b96e04bce1e8ba5` | `789b9017986cb240d9a82428227f6a03adee6f3c` |



## Completion workflow record

- Workflow Run ID: 41334194323
- Triggering source SHA: 12d1d861cf9eb5022fb916f2b7d9a0b702badf1f
- Registry-containing commit: d33261154018e2710bd797dec5e5bb6b9981a5da
- Final exact HEAD and file evidence triples are printed by the final Raw readback step of this Run; a failed Run is not accepted as evidence.


## Governing reference and owner-decision verification gate — 2026-11-01

- D2 completion workflow now fetches the v2.4.0 normative Markdown from GitHub Raw at the exact triggering SHA and checks its 401,397-byte size and owner-approved SHA-256 `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`.
- The same gate fetches `docs/governance/D-2026-10-30-REFERENCE-V2.4.0.md` from that SHA and requires decision ID `D-2026-10-30-REFERENCE-V2.4.0`, status `APPROVED_BY_OWNER`, and the same digest.
- Both governing-reference and owner-decision files are also added to the final exact-HEAD Raw byte readback list. The gate must succeed in the latest completion run before D2 is reconfirmed.


## Completion workflow record

- Workflow Run ID: 41334997604
- Triggering source SHA: 8eb5da55fc9036f25e420dbd43ed925567ef7c2b
- Registry-containing commit: f339bd063e2912b2d9b5afaec7d4ce9e24a6cbc6
- Final exact HEAD and file evidence triples are printed by the final Raw readback step of this Run; a failed Run is not accepted as evidence.


## Final Raw readback list correction — 2026-11-01 (append-only)

- The preceding run 41334997604 successfully verified the governing reference bytes and owner decision at its triggering SHA, but inspection showed that the two paths had been inserted into the pre-finalization Raw list rather than the final post-documentation Raw list.
- The D2 workflow now includes both paths in the final exact-HEAD Raw list and promotes D2-16 from pending to `PASS_SCOPED` only in its finalizer after the verification run is successful.
- A fresh full D2 run is required; the prior successful run remains valid for the 13 D2 outputs but is not used alone to claim D2-16 final-head readback.


## Completion workflow record

- Workflow Run ID: 41335321803
- Triggering source SHA: 8f876e4b4901e4a62ac250820f97e3874e18bd67
- Registry-containing commit: cc94985454d6e5971947e53c8e0a2782ad2de12d
- Final exact HEAD and file evidence triples are printed by the final Raw readback step of this Run; a failed Run is not accepted as evidence.
