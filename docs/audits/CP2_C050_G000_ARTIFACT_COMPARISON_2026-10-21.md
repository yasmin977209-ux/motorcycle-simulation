# CP2 — C050_G000 artifact provenance comparison — 2026-10-21

**Disposition:** `CONFLICTED / OWNER DECISION REQUIRED`. Read-only comparison. Neither artifact is accepted as Golden. No manifest, source, data, Parquet, Gate A code, or historical trial was changed; no new workflow or simulation was run.

## Live repository evidence

- Main HEAD: `6a218ebe0fccf210ec18f3552b141afbdd1a49ef`.
- Main manifest `docs/stage9a/dataset_manifest.json` blob: `e796fa2443493b607f1f9c60b58eb63607959c26`.
- Stage 13 candidate manifest blob: `ec0d4749f86c6f81d743dbb071f92e9f0eddef3d`.
- Both manifests record global manifest SHA `892da438955160bb59aff3046271402f57bdd61a4abb35f41db7188f61346ff6`, source SHA `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`, official source Run `37225915321`, and identical block fingerprints.
- Main maps Artifact `11503191706` to `enrichment_run_ids.C050_G000=37662891608`. The Artifact API says Artifact `11503191706` actually belongs to Run `37660610243`: the main artifact/run pairing conflicts.
- Candidate manifest maps Artifact `11503510055` to Run `37662891608`, matching the Artifact API.

## Producer Runs

| Field | V2 | V3 |
|---|---|---|
| Enrichment Run | [37660610243](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/37660610243) | [37662891608](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/37662891608) |
| Conclusion | success | success |
| Event head SHA | `43e320abb79c3db82bdb70b8c6dece883ea7676d` | `6128b22864bb171ba49ec15dbb42439a6513c30c` |
| Effective enrichment-control checkout | branch `tmp/stage9a-06-enrich-20261007`, commit `b4a88a117fa7d7fcdc7718d6a475699e3e8ac47e` | branch `tmp/stage9a-06-enrich-20261007-v3`, commit `6128b22864bb171ba49ec15dbb42439a6513c30c` |
| Artifact ID | `11503191706` | `11503510055` |
| Size | 17,786,146 bytes | 17,787,110 bytes |
| ZIP digest (API and local SHA-256 agree) | `f575044fb6a50cb5ed71d6303c40bd77841a6d38b633c105e560a4731e0a94f9` | `111eb7a2abd7b85625a02c55ee6f3140a14644ef253141bfdc3f8fc5ae4c287d` |
| Artifact status | non-expired; downloaded/read back | non-expired; downloaded/read back |

**Important producer provenance:** the V2 workflow logs explicitly show it checked out the control branch without the `-v2` suffix and logged commit `b4a88a...`; its `scripts/stage9a_enrich.py` blob is `e92381ddebef4c8792702e4d8a6aba6ef67b0614`. V3 checked out commit `6128b...`, where `scripts/stage9a_enrich.py` blob is `dfb27e7623f42e9ef1d81f3d6752ddd3de269d8d`. Both jobs then checked out the same pinned source SHA `f3af4f...`, used official source Run `37225915321`, and processed `C050_G000`, 450 trials.

## Exact inner-file comparison

Both ZIPs contain one `C050_G000.tar.gz`, each with eight files. Seven files are byte-identical:

| Inner file | Size | SHA-256 |
|---|---:|---|
| `daily_distribution.parquet` | 137,290 | `caf8de98e7e907b01cb87ee2cfc879293a3acb740290f0d2a8ab6867ebb13cd3` |
| `trial_results.parquet` | 28,825 | `09c223d8348f93a5c5e9246a409614d6345a76b224ff65f865c6bdbaea5fbbe8` |
| `trial_fingerprints.json` | 35,824 | `82cb7a2725944edc3b749bcc722d22040459baac2db6c68f3c0ddde98b0db8f6` |
| `representatives/Loss.json` | 314,218,180 | `34be00c541604e6bb13e80b3e10ae6f95109bdc3ce76d64661f58f81f484164c` |
| `representatives/P10.json` | 332,102,108 | `3191b3def023762e42e23d9a8a73235e5e78b94757d17b691f19f4e37ab477d5` |
| `representatives/P50.json` | 342,536,957 | `5b377dbd4868cbb165a6925916051c375ad0c031636224e3b08560196656b3e8` |
| `representatives/P90.json` | 356,570,015 | `7742dccd6ac8433542cb577e583310891b07104fb2af895a663705d70c2886c4` |

The **only differing inner file** is `scenario_metadata.json`:
- V2: 887 bytes; SHA-256 `21e2f33603e21346ae84873f372d39e301f399a0f449eb5db8e195e742d51735`; `log_events: true` (Boolean).
- V3: 911 bytes; SHA-256 `a143c3fb7f2cee8ab625b0beb40295ede2c5879975d08f455e59b85406004cab`; `log_events: "representative_trials_only"` (string).

All other parsed metadata values match: scenario `C050_G000`, collection probability 0.5, recovery 0, 450 trials, source SHA `f3af4f...`, official source run `37225915321`, 2,235 daily rows, date range 2027-01-01 to 2033-02-12, fingerprint reconciliation 450/450, identical representative IDs, and four identical official block fingerprints. This establishes byte identity for the stored data/representative files; it does not in itself select the authoritative Artifact.

## Additional metadata-contract conflict

Current `main/scripts/stage13_gatea_fingerprint_bridge.py`, blob `177eba71e3517ccb123c179fac6cb361127f92c1`, function `validate_block()`, requires `meta.get("log_events") is False`. Neither candidate metadata passes that predicate: V2 is Boolean True; V3 is the string `"representative_trials_only"`.

This is a distinct contract inconsistency, not proof that the identical Parquet data are wrong. No validator, metadata, or manifest change was made.

## Owner choice required

1. **V3 for manifest provenance:** it matches manifest Run `37662891608` and producer/control SHA `6128b...`; core data files are identical to V2. Gate A still cannot pass until the metadata contract is reconciled.
2. **V2 for full event-logging semantics:** it belongs to Run `37660610243` and effective control code `b4a88...`; choosing it requires correcting the manifest artifact/run pairing and resolving the same bridge check.
3. **Keep blocked until the contract is decided:** retain `CONFLICTED / PENDING_APPROVAL` and decide the intended meaning/type of `log_events` before binding either artifact to production Gate A.

**Recommendation:** keep the acceptance state at option 3. V3 is the stronger provenance candidate for manifest linkage only, but do not select it as canonical or change the manifest without the owner’s choice and a separate resolution of the `log_events` contract.

No manifest, source identity, Parquet, historic data, production workflow, or Gate A code was changed. No Monte Carlo, Trial, Checkpoint, Golden expansion, or new workflow was run. Delivery remains `NOT_ACCEPTED`; Release remains `BLOCKED`.
