# Bootstrap & Preservation Recovery — Current Revalidation
Date: 2026-11-06 (UTC)

## Exact Git state

- Repository: `yasmin977209-ux/motorcycle-simulation`
- Branch: `tmp/d1-rebuild-20261101`
- Exact branch HEAD: `f8fa6fac488fc23f2cb28a35a1110070f2a1e692`
- Exact `main` HEAD (read-only): `01a6f79eedc522bb734ed9c5ea31beee581f2468`
- Compare status: `diverged`; ahead `1025`; behind `2`; merge base `c6e54349a5e94f65d5aa9f83141f225d777bb474`.
- Branch ref: https://api.github.com/repos/yasmin977209-ux/motorcycle-simulation/git/ref/heads/tmp/d1-rebuild-20261101
- Commit: https://github.com/yasmin977209-ux/motorcycle-simulation/commit/f8fa6fac488fc23f2cb28a35a1110070f2a1e692
- Main ref: https://api.github.com/repos/yasmin977209-ux/motorcycle-simulation/git/ref/heads/main

The branch advanced six documentation commits beyond `0e491a7eb9977654652c32e937c88ac643b2b68d`; the current HEAD above is re-read from the live Git ref. The prior addendum's `0e491a7...` is retained as a historical checkpoint only and is superseded by this current revalidation. No changes to main, merge, rebase, force-push or history rewrite were made.

## Governing files — exact Raw byte pins at current HEAD

| File | Bytes | Git blob SHA-1 | Raw SHA-256 |
|---|---:|---|---|
| `docs/governance/MOTORCYCLE_SIMULATION_GOVERNING_REFERENCE_V2.4.0.md` | 401,397 | `9fe43bfbb2cbfd2bb7f7010866e7469506d22c33` | `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b` |
| `docs/stage_d/PROJECT_PROMPT_LIBRARY_AR_2026-11-05_REV6.md` | 101,383 | `22ad6f50dbe32226f2753d4e4e9af902984dc765` | `b7d88fbda6426a330c25e65f66e3c9c99b8ce86543742c568ec5df17ac635243` |
| `docs/governance/OWNER_MASTER_BLOCKER_REMOVAL_2026-11-05.md` | 8,102 | `a3730d425729c94f9615676608ce3584fa7e68ef` | `0972af87d092546bc0afcd743740570f051dbabce1655cbfd8d006c01a12a323` |
| `docs/stage_d/OWNER_DECISION_DROPBOX_STORAGE_PROVIDER_2026-11-06.md` | 3,185 | `63ac6f028e39c58aee1b94e190ca11947982229c` | `04befab3ba0667c863fe20a37cce56b5b227fbead76da13b9f00e8fcec2071fd` |

Raw URLs are pinned to commit `f8fa6fac488fc23f2cb28a35a1110070f2a1e692`; hashes were recomputed from fetched UTF-8 Raw bytes. Current governing reference remains v2.4.0 under `D-2026-10-30-REFERENCE-V2.4.0`, `APPROVED_BY_OWNER`. Keep the historical execution reference v2.3 separate.

## Actions, PRs and Releases

- Run [42136073091](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42136073091), Stage D1-D2 Source Validation, tested exact SHA `f8fa6fac488fc23f2cb28a35a1110070f2a1e692`: `success`; Artifact `13466346209`, 10,545 bytes, API digest `sha256:8fb271aab509dca12b3bd79c6ce71551f3aec0dbcac54addb95a2df8836ba796`.
- Run [42136073042](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/42136073042), D3 Published Output Exact-HEAD Verification, tested exact SHA `f8fa6fac488fc23f2cb28a35a1110070f2a1e692`: `success`; no artifact returned. This does not close D3-S1/S2 or D3 parent.
- Branch Actions query: no `queued` or `in_progress` runs.
- Historical long runs `42094642530` and `42099529400` were not restarted.
- No open PR uses this working branch as its head; existing unrelated PRs were left untouched. No Releases are published.

## Original S6 evidence recoverability

- Original source Run [40731224990](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/40731224990) currently returns 20 unexpired scenario Artifacts, total **1,531,244,201 bytes**. They are indexed in [S6 original source artifact recovery inventory](S6_ORIGINAL_SOURCE_ARTIFACT_RECOVERY_INVENTORY_2026-11-06.json).
- Their source execution commit is `a23ba71f48487f3ebead99bc30039b14ef9b7609`; source identity recorded in the inventory remains `source_sha=da1a9ea9b5cd789c944de3f07b08395bb67c49e7`, `cohort_id=s6-v23-da1a9ea9`, `master_seed=20270101`, 20 stochastic scenarios, trial IDs 1..2400 per scenario.
- Artifact expiry window: `2026-11-27T17:23:02Z` to `2026-11-27T18:57:55Z`. API metadata says unexpired at this recheck. The parent workflow is `failure`; 20 scenario jobs are individually recorded as successful in the historical independent audit. Do not promote parent status.
- Dropbox rescue root still lists nine files; its three secondary copies remain in the same Dropbox failure domain. The root/mirror metadata does not prove GitHub-to-Dropbox byte equality.
- A prior upload of a 130,319,892-byte E2 artifact failed with `RESOURCE_EXHAUSTED / INSUFFICIENT_SPACE`. No retry was made. The S6 original 1.531 GB set and E2 replay 3.858 GB set are absent from the Dropbox rescue folder.
- SharePoint/OneDrive is not connected. A second-provider connector was suggested, but no provider connection or upload was authorized/performed. Therefore the preservation blocker remains capacity + independent failure domain.

### What is recoverable, and what is not

The 20 original S6 ZIP artifacts are still downloadable from GitHub Actions at this recheck, subject to the expiry dates above. This is recoverability, **not off-platform preservation**. A GitHub artifact download tool is available, but Dropbox's upload tool accepts only files supplied as conversation attachments; it does not accept a connector-local GitHub artifact file reference as a source. The existing Dropbox upload failure proves the current target cannot accept the known 130 MB test upload. Thus no transfer was attempted.

The original S6 serialized daily projection has already been found to omit the five protected fields: `Accounts_Receivable`, `Accumulated_Depreciation`, `Gross_Bike_Assets`, `Guarantee_Claim_Receivable`, `Total_Assets`. Recovering these ZIPs preserves the original evidence that exists; it does not recreate the missing original full-balance ledgers. Those fields remain `MISSING_EVIDENCE`; no replay, inference, zero-fill or backfill is substituted.

## Current phase dispositions

- D0–D2: `PASS_SCOPED_WITH_LIMITATIONS`.
- D3: not closed. D3-18: `PASS_SCOPED` only; D3-S1/S2 not closed.
- D4–D6: historical `PASS_SCOPED_WITH_LIMITATIONS` only.
- E0/E1: `PASS_SCOPED`.
- E2 Original Accounting: `BLOCKED`.
- E2 Replay: `PASS_SCOPED_REPLAY_RECONSTRUCTION` only.
- E3–E6: `NOT_STARTED`.
- Global Preservation: `BLOCKED / PERMANENT_RETENTION_NOT_COMPLETE`.

## Next permissible action

Connect/authorize an independent storage provider with sufficient capacity, or provide a supported file-upload path for the GitHub connector-local downloads. Then preserve the 20 original S6 artifacts before expiry, separately preserve the 21 E2 replay artifacts with replay labels, and perform byte SHA-256 comparison, ZIP CRC/member inventory, manifest review and restore tests. Do not restart the prior long D3-S workflow. Do not start D4 before D3 is fully closed. No Trials, Simulation, Monte Carlo, N expansion, importer/backfill, protected-field reconstruction, identity/rule/reference change, main write, merge or Release was performed.
