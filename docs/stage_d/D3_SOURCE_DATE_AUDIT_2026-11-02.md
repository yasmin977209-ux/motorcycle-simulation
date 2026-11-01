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


## D3 continuation — exporter provenance guard and source-free validation (2026-11-02, append-only)

- Source-free exporter hardening is committed on the working branch: the D3 extension records the source run creation timestamp, and the workbook exporter now rejects extensions unless each source role has the pinned run date at/after the project cutoff and exact pinned artifact/run metadata. This does not make the existing pre-cutoff sources eligible.
- Added regression coverage for pre-cutoff source dates, missing dates, acceptance of synthetic post-cutoff exact-pin metadata, and rejection of mismatched artifact pins. Synthetic tests are logic fixtures only; they are not project source evidence.
- Static validation Run [41360740452](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41360740452) succeeded on tested source SHA `463a4ec53aaef3c2d4a70e1bac448efd326135a0`: compileall PASS; 19 passed / 0 skipped; no source artifacts downloaded/read; no Trial/Simulation; no D3 gate promotion.
- The workflow committed `docs/stage_d/D3_CODE_STATIC_VALIDATION_REPORT_2026-11-02.json` and verified its Raw readback at final report commit `04e3786d3ae2767e5add9c715ecd6394620b6ad0`: 659 bytes; SHA-256 `cb7f390a72d59a7a575a4430c52ee6f710f6f9e6b7bbf2189d431e2bb110bdc5`; Git blob SHA-1 `026b1e3f0b66145a9f8778e8734dd386b92d51b1`.
- D3 candidate no-rebuild verification Run [41360740382](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41360740382) and D1-D2 validation Run [41360740521](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/41360740521) succeeded on source SHA `463a4ec53aaef3c2d4a70e1bac448efd326135a0`. D1-D2 is not D3 source coverage; the no-rebuild check validates the existing candidate outputs only.
- Source-date cutoff remains `2026-10-31T00:00:00Z`; all three pinned D3 source runs remain pre-cutoff. No eligible post-cutoff D3 source artifacts were found in the reviewed inventory. D3-05 C100 daily and D3-07 through D3-13 remain `MISSING_EVIDENCE`.
- Overall D3 remains `BLOCKED_MISSING_EVIDENCE`; D4 remains `NOT_STARTED`. No source-date exception, Trial/Simulation/Monte Carlo, N expansion, source/cohort/seed change, backfill, zero-fill, main update, merge, Release or D4 work was performed.


## Full Actions inventory refresh — 2026-11-02 (append-only)

- Rechecked the live branch Actions API inventory: 373 workflow runs across four pages.
- Workflow categories include 54 D3 published-output verifications, 232 D1-D2 source validations, 7 D3 static validations, 34 D1 rebuilt-S6 source validations, and 5 D1 rebuilt-S6 builder validations. No Stage C/Trial generation, Monte Carlo, C100 Golden, Full Logging Build or S6 Aggregate Build run appears in the inventory.
- Rechecked metadata only for the three source-producing pinned runs and their artifacts: run 40773412377 / artifact 12852969854 (2026-10-28); run 41098699740 / artifact 12998778418 (2026-10-30); run 40263424595 / artifact 12630457193 (2026-10-26). All predate 2026-10-31T00:00:00Z and remain unexpired.
- No eligible post-cutoff D3 source artifact was found. No artifact archive was downloaded or opened in this refresh. The prior cancelled run 41358971225 remains excluded.
- Source-free static tests passed separately (Run 41360740452, 19 passed / 0 skipped); this does not change source eligibility or D3 gate status.
- D3 remains BLOCKED_MISSING_EVIDENCE; D4 remains NOT_STARTED.


## Final exact-head refresh — 2026-11-02

- Actions run inventory at this checkpoint: 373 runs across four pages. No Stage C/Trial Generation, Monte Carlo, C100 Golden, Full Logging Build or S6 Aggregate Build run appears.
- Exact-head D3 output verification Run 41361423337 succeeded at branch HEAD 1c2fb72359480cf861566ced5c66d744cd65c58c. This workflow reads only already-published workbook/audit/registry/reference files; it does not read source artifact archives.
- Static D3 code validation Run 41360740452 succeeded with 19 passed / 0 skipped and no source artifacts downloaded/read.
- The only three identified source-producing artifacts remain the pre-cutoff S6 aggregate (40773412377), representative Full Logging (41098699740) and C100 Golden (40263424595). Their metadata dates remain before 2026-10-31T00:00:00Z.
- No eligible post-cutoff D3 source artifact was identified. D3 remains BLOCKED_MISSING_EVIDENCE; D4 remains NOT_STARTED.
