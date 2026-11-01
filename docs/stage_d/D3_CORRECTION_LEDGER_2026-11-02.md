# D3 Correction Ledger — 2026-11-02

## Scope and disposition

Append-only correction record for the D3 candidate publication produced by Actions Run `41352075552`. This record corrects stale fingerprints and an incorrect reference-copy classification. It does not rebuild or modify either workbook, does not change the governing reference, does not promote D3, and does not authorize D4.

## Correct published workbook identities

The earlier `D3_LIVE_REVIEW_AUDIT_2026-11-02.md` values were stale and came from the earlier candidate run. The current published workbook identities, as recorded in the D3 remote evidence ledger, are:

| Path | Bytes | SHA-256 | Git blob SHA-1 | Output commit |
|---|---:|---|---|---|
| `deliverables/النتائج_الكاملة_AR.xlsx` | 27,734,273 | `914da4091c45114f3a61a5c847c0697832956b44a134116fd77e45fb9d39b461` | `056b7f482bbb84583526f093ae886e13b8c01356` | `3f063c62fbb0ea7e62f0882d709371856d071bef` |
| `deliverables/Full_Results_EN.xlsx` | 27,722,355 | `89712da93a43af7b03d69d516348e9c7e76c3374702d3d0e56418c5704e6f191` | `a01c1f4061da731de24fcc8d061113bb195e65b1` | `3f063c62fbb0ea7e62f0882d709371856d071bef` |

No workbook rebuild or workbook-byte modification was performed for these corrections.

## Governing reference repository copy

The prior claim that `docs/governance/MOTORCYCLE_SIMULATION_GOVERNING_REFERENCE_V2.4.0.md` was a conflicting 269,253-byte candidate is withdrawn. The live tree records 401,397 bytes and Git blob SHA-1 `9fe43bfbb2cbfd2bb7f7010866e7469506d22c33`, matching the approved Gist blob identity. This is not by itself the required Raw-byte proof. The exact repository Raw bytes must match SHA-256 `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`, 401,397 bytes, and the recorded Git blob SHA-1 before the repository copy may be called `VERIFIED_LIVE`.

## Validation hardening

- `scripts/s6_excel_export.py::compare` now fails closed when paired worksheets have different dimensions, row counts, or row widths; this prevents `zip()` from silently ignoring trailing worksheet cells.
- `tests/test_s6_excel_export.py` includes a regression test for a trailing-row dimension mismatch.
- The two published XLSX files were not regenerated.

## No-rebuild exact-head workflow

Added `.github/workflows/d3-published-output-verification.yml`. It runs on pushes to `tmp/d1-rebuild-20261101` and manual dispatch. It checks out the exact triggering SHA, asserts exact HEAD, runs the focused exporter regression tests, then downloads committed Raw files at that exact SHA and verifies SHA-256, byte count, and Git blob SHA-1 for both workbooks, D3 audit JSON, manifest, build report, Number Registry, and repository copy of the governing reference. It does not build, rewrite, or upload workbooks.

Workflow file commit: `8ebbd4e730f9468cd205608d84e2cb63ab862c1b`.

## Preserved gates and limitations

- D3 remains `BLOCKED_MISSING_EVIDENCE`; no D4.
- Financial Gate A remains `PASS_SCOPED` only.
- Production Gate A remains `NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS`.
- Gate B N=2400 remains `FAIL_SCOPED (10/10)`; Stability remains `NOT_CONVERGED (0/60)`; N=4800 remains `NOT_EXECUTED`.
- Full Logging remains representative 105 keys only; normalized 105/105 remains `NOT_VERIFIED_105_OF_105`; C100 Golden revalidation remains `NOT_RUN`.
- The five missing accounting fields remain `MISSING_EVIDENCE` and must not be inferred or zero-filled.
- No Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, identity change, main update, merge, or Release was performed.

## Evidence status

The correction text and workflow file are committed. The new workflow's success and its final Raw readbacks must be established from the Actions run on the final correction HEAD. Until then, these additional checks are `NOT_RUN`, not `PASS`.


## D3 pre-cutoff source-processing incident — 2026-11-02 (append-only)

- The D3 completion workflow run 41358971225 was started against three pinned source runs whose GitHub metadata dates are earlier than the project cutoff 2026-10-31:
  - Aggregate run 40773412377: created 2026-10-28T21:36:57Z; artifact 12852969854.
  - Full Logging run 41098699740: created 2026-10-30T17:25:30Z; artifact 12998778418.
  - C100 run 40263424595: created 2026-10-26T03:18:29Z; artifact 12630457193.
- The workflow did download and read those source artifact contents before the cutoff rule was enforced. This was an execution error. Its content-derived temporary output is quarantined and MUST NOT be used as D3 evidence.
- The workflow was cancelled at 2026-11-01T22:52:26Z. Cancellation workflow run 41359264888 completed successfully. The cancelled run has no published Actions artifacts, made no repository commit, did not publish workbooks/manifests, and did not change the D3 candidate deliverables.
- The D3 completion workflow is now disabled; its orchestration script fails closed. The artifact reader also rejects all currently pinned pre-cutoff source runs before opening their archives.
- The 17 D3-focused regression tests passed in the cancelled run, but that test result is not a D3 gate pass and does not validate any pre-cutoff source content.
- No D3 status promotion is made. D3 remains BLOCKED_MISSING_EVIDENCE; D4 remains NOT_STARTED.
