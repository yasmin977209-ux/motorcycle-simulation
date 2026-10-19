# CP — MaxCase existing-artifact inventory: official Stage 7 block

**Date:** 2026-10-19  
**Mode:** read-only artifact inspection; no workflow or simulation run.

## Artifact identity

- Official Stage 7 block artifact ID: `11312813109` (`C050_G000`).
- Downloaded ZIP size: 52,239 bytes.
- Local SHA-256: `b1fc0e25efe8e41226ca6082ef2fd391f7b3a8351e7c5dfdd1ca8604b098384a`.
- ZIP opened successfully.

## Exact archive members

1. `block_1_300.parquet`
2. `block_1_300_metadata.json`
3. `block_301_350.parquet`
4. `block_301_350_metadata.json`
5. `block_351_400.parquet`
6. `block_351_400_metadata.json`
7. `block_401_450.parquet`
8. `block_401_450_metadata.json`

No representative JSON, per-trial daily accounting ledger, or MaxCase payload is present in this official block artifact. The Parquet block files are trial-result data; they are not daily-row ledgers.

## MaxCase route conclusion

This independent block-package inspection corroborates the Stage 9A enriched-package audit: the currently inventoried official sources contain trial-result summaries and four representative daily payloads, but do not provide a full daily-accounting payload for an arbitrary distinct MaxCase trial.

The approved selection rule remains: highest positive `Final_Net_Project_Equity`, ties by smallest `trial_id`; if no positive value exists, `UNDEFINED_BUSINESS_RULE` and hold that scenario. Reuse of an existing payload is safe only if its summary and every daily row bind to the selected trial ID. If no such payload exists, keep the scenario blocked. Do not fabricate daily rows or rerun a completed trial without a separate explicit owner authorization.

No artifact was modified; no Parquet reader, workflow, trial, checkpoint, Monte Carlo, workbook, main/state, or Release was used/changed.
