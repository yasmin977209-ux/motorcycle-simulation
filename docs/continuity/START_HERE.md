# START HERE — Project continuity

> **Purpose and authority boundary:** This is a navigation/index document, not the governing specification, not owner approval, and not a substitute for live GitHub reads. It does not make the continuity PR part of `main` and does not imply automatic synchronization of ChatGPT messages.

## Authority and evidence order

1. Platform permissions and documented, scoped owner authorization.
2. The one static Project Source expected in ChatGPT is the owner's merged file named exactly `المرجع النهائي الموحد المعتمد المدمج.md`. Its embedded normative reference retains the internal title `المرجع_النهائي_الموحد_المعتمد.md`; the expected SHA-256 of those original reference bytes is `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`. Do not confuse the merged-file hash with the original reference hash. The owner must verify the actual Project Sources list and Project Instructions in the ChatGPT UI; GitHub cannot confirm or alter those UI settings. The reference-byte SHA-256 documented by the owner is `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`; do not claim to recalculate it unless the original bytes are independently available.
3. Live repository evidence: current branch refs/HEADs, commits, `main/state.json`, `docs/STATE_SHA_SEMANTICS.md`, `docs/governance/DECISIONS_LOG.md`, `docs/governance/REFERENCE_AMENDMENTS.md`, PR metadata, Runs/Jobs/tested SHAs/Artifacts, manifests and report contents.
4. The append-only history and evidence links in `docs/PROJECT_CONTINUITY.md`, read from the currently verified branch associated with the continuity PR. The branch and PR identifiers below are discovery pointers, not immutable truth.
5. Supporting reports and artifacts with their own origin, scope, status, content hash and byte count.
6. Chat memory, prior-chat recollection and narrative summaries are supporting context only; they cannot replace a live read or an explicit governing rule.

## Required start-of-chat procedure

1. Confirm the repository and read current `main` HEAD from GitHub. Read `main/state.json`, `docs/STATE_SHA_SEMANTICS.md`, `docs/governance/DECISIONS_LOG.md`, and `docs/governance/REFERENCE_AMENDMENTS.md`. Resolve the meaning of `state.sha` through its semantics before comparing it with HEAD.
2. Read live metadata for PR #46 and its base/head branch. Confirm open/closed, Draft/ready, merge state, current base SHA, head SHA, and changed filenames. Then read `docs/PROJECT_CONTINUITY.md` from the verified head. If this PR or branch has moved, closed, or disappeared, rediscover the current approved continuity location; do not assume these names are permanent.
3. Read the entire continuity file or retrieve it in bounded line ranges and prove coverage through the final line. Identify the latest *complete, evidence-supported* resumption entry by timestamp plus commit lineage/read-back evidence—not by selecting the first repeated heading or simply the last date string.
4. Read each line of `docs/continuity/SESSION_OUTPUTS.jsonl` as a separate JSON object. Follow report/artifact links, but do not turn `LOCAL_ONLY`, `PENDING_READ_BACK`, or `APPROVAL_PENDING` into a success claim.
5. Read `docs/PROJECT_STATE.md` only with its own timestamp and scope. At the time this index was drafted that document was dated 2026-10-06; treat it as a historical snapshot unless a fresh read establishes a newer, approved role. It does not replace `main/state.json` or live HEAD.
6. Compare the live state with the most recent continuity entry. Report what changed, what failed, what is incomplete, what could not be read, unresolved authority conflicts, current gates/blockers, and the next *permitted* action. Do not infer a higher mode from tone or tool availability.
7. Before any edit, classify the item and prepare R4: element | current state | governing reference/decision and branch | exact controlling text | ruling. Respect the CP boundary and obtain the required separate approval.

## Status vocabulary for outputs

- `LOCAL_ONLY`: a local file exists and has not been saved to the repository or another approved durable destination.
- `SAVED`: the write operation returned a result; this alone does not prove persistence or content.
- `READ_BACK`: the file has been fetched again from the intended live GitHub branch and its content has been inspected.
- `HASH_VERIFIED`: SHA-256 was computed from the exact read-back bytes and matched the intended content/hash.
- `PENDING_READ_BACK`: a write was attempted but no successful independent read-back has yet been proved.
- `APPROVAL_PENDING`: saved as a proposal only; not adopted as a governing rule.
- `NOT_SAVED`: failure to save is established.
- `UNSAFE`: saving was intentionally not performed due to secrets, sensitive data, policy, or scope.

Never treat these states as synonyms. A file is not fully verified merely because its name exists, the connector returns success, a Workflow passes, or an Artifact is listed.

## Non-negotiable synchronization and history limits

- ChatGPT messages are not automatically synchronized to GitHub by this file. Record material decisions, failures, work products and transitions explicitly at suitable checkpoints, while preserving earlier failures and linking detailed evidence.
- Do not overwrite or delete prior history. Corrections and later verification are new dated events that reference the prior event.
- Do not write `main`, modify `state.json`, change the governing reference, merge/close PRs, delete branches, or create/modify tests/workflows unless a future explicit authorization covers the action.
- Do not run pytest, CLI, Monte Carlo, Trial, Checkpoint, Golden expansion, or production/statistical jobs unless a separate valid authorization permits it.
- If writing fails, inspect the ref and target file before any retry. If read-back fails, say `تعذر التحقق من تحديث GitHub`. Say `GitHub لم يُحدّث` only when the absence of an update is established. Never retry blindly.
- Keep the historical data identity intact: verify `SOURCE_SHA`, `master_seed`, RNG, sampling, scenario/trial IDs, schema version, manifests and fingerprints before any authorized data execution. Never mix cohorts or reuse completed trials.

## Current continuity entry points (verified on 2026-10-18; recheck every session)

- Main: `https://github.com/yasmin977209-ux/motorcycle-simulation/tree/main`.
- Continuity PR: `https://github.com/yasmin977209-ux/motorcycle-simulation/pull/46`.
- Current continuity log location at the last verified baseline: `https://github.com/yasmin977209-ux/motorcycle-simulation/blob/tmp/cp-session-continuity-20261017/docs/PROJECT_CONTINUITY.md`.
- Current output register location: `docs/continuity/SESSION_OUTPUTS.jsonl` on the same verified continuity branch; confirm it exists at the current head before using it.
- Proposed Project Instructions text for owner review: `docs/continuity/PROJECT_INSTRUCTIONS_DRAFT.md`. This file has no authority until the owner checks and applies it in ChatGPT Project Settings.

At the baseline for this CP, `main` was `647c19826b90d8224ce73ef9b90c306a45e03fb0`, the continuity branch head was `74e0f2cf0fad66d3a79bda70c47d7e6cd18668c0`, and PR #46 was Open / Draft / unmerged. These values are recorded historical identifiers, not instructions to accept the same state in a later chat.

## Independent cross-chat acceptance marker

The marker below is a non-sensitive test token. A separate ChatGPT conversation should search the live continuity branch for `CROSSCHAT_ACCEPTANCE_MARKER` and report the marker value it actually reads; do not reveal the expected value in the test prompt supplied to that conversation.

<!-- CROSSCHAT_ACCEPTANCE_MARKER: CCAT-CP-CONTINUITY-IMPLEMENTATION-01-20261018-6d3c7f29a1b84e5a -->


## Bootstrap and instruction-draft correction — 2026-10-18T22:28:00+03:00

The merged Project Source expected in the ChatGPT project is named exactly `المرجع النهائي الموحد المعتمد المدمج.md`. Names of the embedded source documents are historical/internal names, not necessarily the uploaded Project Source filename. The current proposed Project Instructions are in [PROJECT_INSTRUCTIONS_DRAFT.md](PROJECT_INSTRUCTIONS_DRAFT.md); this is still a manual owner action and is not applied by GitHub.

At every new chat, treat PR #46 and `tmp/cp-session-continuity-20261017` as discovery pointers only. Re-fetch current PR/base/head and verify the branch; then read the continuity ledger and output manifest at that live ref. If it is unavailable or ambiguous, rediscover from live GitHub evidence and stop as BLOCKED if no unique valid target can be proven. The independent marker already present in this file is reserved for a separate-chat acceptance test; do not duplicate it in the prompt or disclose its expected value elsewhere.
