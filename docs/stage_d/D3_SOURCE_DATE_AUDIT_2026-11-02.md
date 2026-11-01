# D3 Source-Date Eligibility Audit — 2026-11-02

## Governing cutoff

The project rule prohibits reading any source file dated before 2026-10-31. Eligibility is determined from live GitHub Actions run metadata before any artifact download or archive read.

## Metadata-only source inventory

| Source role | Artifact ID | Workflow run ID | Run created (UTC) | Source run HEAD | Eligible |
|---|---:|---:|---|---|---|
| S6 aggregate N=2400 | 12852969854 | 40773412377 | 2026-10-28T21:36:57Z | 4f2f2cc16d0cb5125262088704febccbae6f50ed | NO — pre-cutoff |
| Full Logging representative | 12998778418 | 41098699740 | 2026-10-30T17:25:30Z | e3c2098df9fc5dbc126eb1e77ad35c493ff3ac70 | NO — pre-cutoff |
| C100 deterministic reuse | 12630457193 | 40263424595 | 2026-10-26T03:18:29Z | 24050f15bc7eb3097e20f76785a45c5d177643dd | NO — pre-cutoff |

This table records metadata only. No source content from these artifacts is accepted as evidence.

## Post-cutoff search

- The live branch tree was inspected for candidate data-file paths and recent D3/Stage D Actions runs.
- D3 candidate build runs, including 41352075552 and 41354098029, returned no Actions artifacts containing new D3 source data.
- Recent exact-head publication verification run 41359344854 succeeded on branch HEAD 7aea74e774084fb7a622f411c5b1dbfad40a2d0d; it validates the already-published candidate outputs only and does not supply missing source ledgers.
- No eligible post-2026-10-31 S6 aggregate, representative Full Logging, C100 daily, bike-level ASSETS, daily ACCTG, PARTNER, GUARANTEE, CONTRACTS, or all-trial close-date source artifact was found in the searched recent run inventory.
- The committed D2 Number Registry is post-cutoff, but its scope is the previously validated 20 S6 scenarios / 1,000 daily series / 2,086,550 daily points and 105 representative keys / 1,680 numeric entries. It does not contain the missing D3 detailed source records.

## D3 gate disposition

- D3-01, D3-02, D3-03, D3-04, D3-14, D3-15, D3-16, D3-17 and D3-18 retain their existing scoped evidence statuses.
- D3-05 remains PASS_SCOPED_WITH_LIMITATIONS for the 20 S6 series only; C100 daily distributions remain MISSING_EVIDENCE.
- D3-06 remains PASS_SCOPED_WITH_LIMITATIONS for 105 representative keys / 1,680 numeric entries only; raw representative daily logs remain MISSING_EVIDENCE.
- D3-07 through D3-13 remain MISSING_EVIDENCE: P50 daily sheets, ASSETS, ACCTG, PARTNER, GUARANTEE, CONTRACTS and all-trial final close-date distribution.
- Overall D3: BLOCKED_MISSING_EVIDENCE. No transition to D4.

## Preserved limits

Financial Gate A remains PASS_SCOPED only. Production Gate A remains NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS. Gate B at N=2400 remains FAIL_SCOPED (10/10). Stability remains NOT_CONVERGED (0/60). N=4800 remains NOT_EXECUTED. Full Logging remains 105 representative keys only / NOT_VERIFIED_105_OF_105. C100 Golden remains NOT_RUN. The five missing historical accounting fields are not inferred or zero-filled.

## Cancelled processing attempt

Workflow run 41358971225 was cancelled after it had already downloaded and read the three pre-cutoff artifacts. This is recorded as a process exception, not evidence. Its content-derived temporary output is quarantined and excluded. No repository output commit or Actions artifact was published. The workflow and orchestration script are disabled/fail-closed.

D4 remains NOT_STARTED. No Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, main update, merge, PR, Release or final acceptance was performed.
