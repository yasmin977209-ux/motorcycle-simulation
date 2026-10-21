# R4 — Clean current-main Stage 13 assembler integration — 2026-10-22

## Scope

- Exact current `main` base HEAD: `7621ddefe6c971e9eb231eb2a987519c86a2cb51`.
- Candidate branch: `tmp/cp-stage13-clean-current-main-20261022`.
- Classification: `K_CODE + K_TEST + K_WORKFLOW`, branch-only; synthetic/contract verification.
- Purpose: add the missing Stage 13 assembler/entrypoint to a clean descendant of current main, preserve the canonical manifest byte-for-byte, and test against synthetic data only.

## Current-main facts

- Current main still lacks `scripts/stage13_assemble.py` and `scripts/stage13_maxcase_source_audit.py`.
- Current main canonical manifest blob: `e796fa2443493b607f1f9c60b58eb63607959c26`. This is immutable in this CP.
- Approved architecture decision D-2026-10-10-04 specifies `scripts/excel_builder.py` as orchestrator and `scripts/stage13_assemble.py` as the Stage 13 assembler.
- Existing read-only R4 reports identify an unresolved `C050_G000` provenance conflict: manifest artifact `11503191706` is from Run `37660610243`, while manifest enrichment Run is `37662891608` and matching-run artifact is `11503510055`. The archive metadata differs in `log_events`. Do not silently substitute the artifact ID or rewrite the manifest.
- The source-audit tests explicitly check that inventory/run identity mismatches are reported. The canonical manifest stays at blob above even though the conflict remains open.
- Representative daily payloads lack Partner 1/2 reinvestment memo balances for MaxCase in the 20 non-C100 scenarios. The candidate must preserve explicit pending markers; it must not infer values from Cash/Equity, use zero, or build a production delivery from incomplete data.
- A prior candidate with these source blobs passed 54 focused synthetic/compatibility tests on Run `39677426514`, SHA `e7616f7e34945286856fd665ad0489dbc73378fe`. This historical pass is useful but will not be used instead of rerunning on this clean current-main descendant.

## Reviewed candidate source blobs to port

| Path | Previously reviewed blob |
|---|---|
| `scripts/stage13_assemble.py` | `47fc1828dfb0d298aa4528f58b558bf012882076` |
| `scripts/excel_builder.py` | `c5db5f1113294224d371e98bab2edd7b015a30d2` |
| `scripts/stage13_maxcase_source_audit.py` | `f7835b5a6f2584f9a0679a496b565a5a229f6b4c` |
| `tests/test_stage13_assembler.py` | `d4c0f8c52da53cb3ad50994e71632c04502ff873` |
| `tests/test_stage13_maxcase_pending_fields.py` | `182c7e0ec62e6f48a1fce2d2c4d6bb692e76bce4` |
| `tests/test_excel_builder_adaptive_mode.py` | `1c3b0a37d3643c2fd45270a63df61b8525b36d5f` |
| `tests/test_excel_builder_legacy_compat.py` | `968006169c4b46408269fb954c4714e561065f31` |

## Validation design

A candidate-only push workflow will:
1. Checkout the exact commit SHA.
2. Install repository requirements.
3. Compile only the Stage 13 modules.
4. Run only the synthetic/compatibility test files listed above plus the pre-existing `tests/test_excel_builder_precision.py`.
5. Never download canonical production artifacts, build a production workbook, write the Stage 9A manifest, execute a simulation, or generate trials/checkpoints.

## Acceptance boundaries

A passing run demonstrates the synthetic contract only. It does not resolve C050 provenance, supply missing partner memo balances, establish Gate A or overall stability, or accept the seven-file delivery. No merge/release is implied by a focused pass.

## Explicit exclusions

No direct main write, no canonical manifest/identity mutation, no SOURCE_SHA/seed/RNG/cohort/trial changes, no historical data/artifact edits, no production workbook build, no Monte Carlo, Trial, or Checkpoint, and no attempt to manufacture missing daily balances.

## Status

`PENDING_CURRENT_MAIN_STATIC_READBACK_AND_EXACT_SHA_CI`.
