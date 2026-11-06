# R4 — Historical Gate B input and N=300 audit

Date: 2026-10-11
Scope: read-only verification of owner-authorized historical trial IDs 1..300 as Gate B analytical inputs. No simulation or trial execution, no edits to historical results/metadata/fingerprints, and no product engine/RNG/test changes.

| Item | Current main | stage3b-preserved | Binding reference / approved decision / actual source | Judgment |
|---|---|---|---|---|
| Statistical policy | main HEAD 94b6ea49715c9f845be83b6f106b26c253bf0506 contains D-2026-10-10-01 and D-2026-10-11-01. | HEAD 2e3aa381d833fe430d2aec42e98dd0d29918c3bf is diagnostic only. | D-2026-10-10-01 requires N=300 then doubling; Gate B uses 95% Student-t CI half-width <1% of absolute mean for three named metrics, three consecutive successful points. D-2026-10-11-01 authorizes only historical IDs 1..300 analytically. | MATCH for N=300 input scope; not a final Gate B pass. |
| Identity bridge | Stage 12 Run 37964656154 metadata says source SHA f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b, seed 20270101, historical +50/550 policy. | No current data identity authority. | Stage 7 Run 37225915321 stores TrialResult rows and per-trial SHA-256 fingerprints. Stage 12 Parquet stores result_sha256 per daily row. This audit requires exact equality of all 300 trial fingerprints per scenario, source/seed/schema identity, and Stage12 file SHA matching CP12-C report. | MATCH only if all 6,000 authorized trial inputs validate. |
| Near-zero CI handling | D-2026-10-10-01 states CI_ABSOLUTE_EPSILON=1 near zero. | No accepted fallback found. | The binding text does not specify the exact near-zero inequality. | UNDEFINED_BUSINESS_RULE if abs(mean) <= 1; validator records raw CI and holds rather than guesses. |
| N=600 continuation | The historical Stage 12 dataset includes IDs 1..550 under the old +50/550 policy. | Not authoritative. | D-2026-10-11-01 only expressly authorizes analytical reuse of IDs 1..300. Future policy requires N=600, but completed trials may not be rerun. | UNDEFINED_BUSINESS_RULE: determine how to compose N=600 without unauthorized reuse of IDs 301..550 or rerunning completed IDs. This point is HOLD. |
| Workflow | No full Stage12-to-Stage7 fingerprint-bridge audit exists on main. | No preserved code used. | Exact branch pin, push-only, read-only contents/actions permissions, 30-min job timeouts, no workflow_dispatch/self-dispatch; no engine execution. | DEVIATION resolved by isolated analysis workflow. |

The workflow only downloads published artifacts and calculates N=300 intervals from existing TrialResult rows. It preserves row-level provenance and never modifies or resumes historical data. N=300 is one checkpoint only; this workflow does not prove Gate A or final three-checkpoint Gate B stability.

## Verified N=300 checkpoint result — Run 38161608184

**Run:** https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/38161608184  
**Audit branch head tested:** `78ecff0a209c138b32f1ecf1cdb3260614b1e926`  
**Combined report artifact:** `gateb-historical-300-n300-report`, artifact ID `11710986152`, SHA-256 `70bee5672a42603ad5a6f83d4ecf2deaec8f6dc453ce693b3507a8161fb3ff38`.

| Gate | Result | Evidence |
|---|---|---|
| Historical source/parameter compatibility | PASS | All 20 scenario workers validated Stage 7 to Stage 12 input identity |
| Historical trial fingerprint bridge | PASS | Exact SHA-256 match for each authorized `trial_id=1..300`; Stage 12 Parquet file SHA matched CP12-C `content_sha256` |
| Completeness / unique keys | PASS | 20/20 scenarios; 6,000/6,000 authorized historical trial results; 60/60 requested metric CI rows present |
| Gate B at N=300 | **PASS at this checkpoint only** | All 60 Student-t 95% half-width comparisons passed `half_width < 0.01 × abs(mean)`; no near-zero branch was triggered |
| Final Gate B / three consecutive checkpoints | **NOT ESTABLISHED** | N=600 and N=1200 are not yet evaluated under the new policy |
| Gate A | **NOT ESTABLISHED** | Independent golden/reference comparison still required |

The report status is `PASS_AT_N300_ONLY`, and its overall field explicitly says `NOT_ESTABLISHED_BY_N300_ALONE`. This is not a Gate B PASS.

### N=600 hold — unresolved scope boundary

The authorized analytical reuse scope currently names only historical `trial_id=1..300`. The historical data source also contains completed IDs `301..550` under `+50/550`. Reusing those IDs as inputs to the new policy is not expressly covered by D-2026-10-11-01, while rerunning completed trials is prohibited. No policy has been inferred for forming N=600 without either unauthorized reuse or rerunning IDs.

Classification: **UNDEFINED_BUSINESS_RULE**. Hold N=600 and later cumulative checkpoint calculations until the governing decision unambiguously specifies how completed IDs 301–550 may be handled. No trials were executed by this audit, and historical data/metadata/fingerprints were not modified.

The combined report preserves row-level scenario/trial fingerprint provenance and contains all actual N=300 means, sample standard deviations, t-critical values, half-widths, limits, and statuses. 

