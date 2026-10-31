# D1 S6 Builder reconstruction

Status: T2_INTERIM / NOT_FINAL_BLOCKED.

The source modules are independently reimplemented against the pinned GitHub artifacts and D1 specification. No trial execution, simulation, Monte Carlo, or N=4800 is included.

The frozen representative map remains 125 role assignments and 105 unique keys (100 S6 and 5 C100). The resolver preserves original statuses and keeps normalized statuses NOT_VERIFIED when independent expected byte sizes are absent.

Current governing reference v2.4.0 remains separate from historical S6 execution reference v2.3. C100 remains CROSS_COHORT_DETERMINISTIC_REUSE. Full Logging remains limited to 105 representative keys, not 48,000 trials. Missing accounting fields are not guessed or zero-filled.

D2 registry generation, Excel, Word, and final delivery are outside this D1 reconstruction.