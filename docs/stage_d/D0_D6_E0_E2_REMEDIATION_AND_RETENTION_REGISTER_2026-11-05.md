# سجل معالجة الفجوات والاحتفاظ — D0–D6 وE0–E2 — 2026-11-05

| المرحلة | الحالة | الفجوة المتبقية |
|---|---|---|
| D0 | PASS_SCOPED_WITH_LIMITATIONS | Parquet schema/row counts غير متحقق منها في هذه الجلسة؛ source_run_metadata.sha256 والدفاتر التاريخية والحقول الخمسة تبقى غير مثبتة |
| D1 | PASS_SCOPED_WITH_LIMITATIONS | 105 normalized manifest statuses تبقى NOT_VERIFIED عند غياب expected byte sizes مستقلة |
| D2 | PASS_SCOPED_WITH_LIMITATIONS | Registry 2,640 entries / 1,000 series / 2,086,550 points؛ لا يثبت 48K detailed ledgers |
| D3 | PASS_SCOPED_WITH_LIMITATIONS | D3-18 NOT_RUN |
| D4 | PASS_SCOPED_WITH_LIMITATIONS | workflow stale references corrected; exact-head rerun pending |
| D5 | PASS_SCOPED_WITH_LIMITATIONS | Artifact مؤقت؛ full 177-test suite NOT_RUN |
| D6 | PASS_SCOPED_WITH_LIMITATIONS | Artifact مؤقت؛ historical tests 176/179/180/183 NOT_RUN |
| E0 | PASS_SCOPED | gap inventory only |
| E1 | PASS_SCOPED | documentary/governance reconciliation only |
| E2 | PASS_SCOPED | old-identity replay reconstruction PASS_SCOPED; original historical fields still missing; new lineage awaits owner confirmation |

D1-D2 Run 42048367250 and D3 Run 42048367264 succeeded on baseline `8efa2cb5d936a79dd27f649b5fd7434cced5f29f`. D0-D4 Run 42048284433 tested older `9d75852...` and is not an exact-head pass for baseline. D5 Run 41928234377 tested `baf696...`; D6 Run 41929888796 tested `48ae9fb...`; E2 old replay Run 41958935113 used old identity and workflow SHA `002b748...`.

## Permanent retention
Git history preserves source and text evidence. GitHub Actions artifacts are temporary. The full inventory of 29 artifacts, IDs, run IDs, sizes, digests and expiry dates is in `D0_D6_E0_E2_RETENTION_INVENTORY_2026-11-05.json`. Earliest expiry is D0 aggregate Artifact 12852969854 on 2026-11-27; D3/D5/D6 and D0-D4 evidence expire in December; E2 replay artifacts expire 2027-02-03. No permanent binary archive exists yet. Release needs owner decision; Box was suggested but is not connected.

Fixed gates remain unchanged: Financial Gate A PASS_SCOPED only; Production Gate A NOT_DECLARED; Gate B FAIL_SCOPED (10/10); Stability NOT_CONVERGED (0/60); N=4800 NOT_EXECUTED; Full Logging 105 keys only; 105 manifest statuses NOT_VERIFIED; C100 Golden NOT_RUN. Five accounting fields remain MISSING_EVIDENCE and are not inferred or zero-filled. E3 Acceptance Execution remains NOT_STARTED.
