# Master Blocker Register — 2026-11-07

| ID | Priority | Status | Blocker |
|---|---|---|---|
| PRES-001 | P0 | BLOCKED | Provider raw-byte SHA-256 readback and restore not run. |
| PRES-002 | P0 | BLOCKED | Two independent durable failure domains not proven. |
| PRES-003 | P0 | NOT_TRANSFERRED | Separate E2 Replay 20 archives not transferred. |
| PRES-004 | P1 | NOT_COMPARABLE | D3S-010 and 20 multipart wrappers lack comparable source hashes. |
| HEAD-001 | P1 | NOT_ESTABLISHED | Exact Final Head suite not run on one SHA. |
| D0-001 | P1 | MISSING_EVIDENCE | 48K ledgers and five accounting fields missing. |
| D1-001 | P2 | NOT_RUN | Independent Builder importer and two clean rebuilds. |
| D2-001 | P2 | NOT_RUN | C100 Golden revalidation. |
| D3-001 | P1 | CONFLICTED | 72/72 summary conflicts with detailed 51/72 reconciliation. |
| D6-001 | P1 | CORRECTED_APPEND_ONLY | D6 wording conflict corrected separately. |
| D6-002 | P2 | STALE_POINTER | Root D6 pointer older than Run 42403657899. |

Configure repository Actions secrets `ONEDRIVE_GRAPH_ACCESS_TOKEN` and `DROPBOX_ACCESS_TOKEN` through GitHub Settings; never paste credentials into chat or source. No E3 until Global Preservation Gate passes.

## Live blocker updates — 2026-11-07
| ID | Status | Current evidence / action |
|---|---|---|
| PRES-001 | BLOCKED | Raw-byte SHA-256 and Restore remain NOT_RUN for all 72 objects. |
| PRES-002 | BLOCKED | OneDrive and Dropbox are separate providers/accounts; independent recovery/control domains remain NOT_PROVEN. |
| PRES-003 | NOT_TRANSFERRED | E2 Replay 20 remains separate and untransferred. |
| PRES-004 | NOT_COMPARABLE | D3S-010 plus 20 multipart wrappers lack comparable source hashes. |
| HEAD-001 | NOT_ESTABLISHED | D1/D2/D3/D4 tested fa55; D0/D5/D6 tested older SHAs; one D0-D6 final-head suite is absent. |
| RAW-001 | NOT_RUN | Previous raw-readback report had literal backslash+n; corrected workflow and negative tests await post-push run. |
| PRES-005 | BLOCKED | D5 Artifact 13582441423 download succeeded; OneDrive upload rejected 519,117,017 bytes because source-file limit is 104,857,600 bytes. |
| REV7-001 | NOT_RUN | REV7 header and unified active section corrected append-only; post-commit Raw readback pending. |

The 72/72 historical summary remains CONFLICTED with the detailed 51 MATCH / 21 NOT_COMPARABLE ledger. Do not silently promote it.


## Live reconciliation — 2026-11-08 (append-only)

Pre-C2 HEAD `3217ab43f587e468753d13952fdd16cb947259f8`; main `01a6f79eedc522bb734ed9c5ea31beee581f2468`.

D1-D2 Run 42419105795 / Job 128543480494: 37 passed on exact HEAD; Artifact 13593026097, 10,545 bytes, SHA-256 `b335be1aab68a85b0b085b018dd55272d1c3c9d18809efd61acc47b7ce1d5162`. D3 Run 42419105827 / Job 128543480974: 38 passed, 35 Raw readbacks, exact-head PASS. D6 Run 42419105855 / Job 128543481098: 49 auditor unit tests and 8 normative tests passed (175,176,179,180,181,182,183,186); Test 176 = `241 = 64 + 177 + 0`; Artifact 13592363586, 6,929 bytes, SHA-256 `cb57bb2edb5ad7f474ac5c6ab9f38add3a960325717698efe481ce23b0c95b60`. D6 disposition `PASS_SCOPED_WITH_LIMITATIONS`; Final Acceptance `NOT_ACCEPTED`.

Tri-hash Run 42416858162 is on older tested SHA `80c715d3ff489422ae2739627bb8819280ad48af`, not the pre-C2 HEAD. Artifact 13591479069: 20,502 bytes, SHA-256 `54ca0d9961b29af9fbdca5a60e491bac335485db0f34aade0fc7424e2313ba69`. Its 21 newly compared OneDrive references (D3S-010 + 20 multipart wrappers) MATCH; total 63/72 OneDrive metadata matches, 9 Dropbox reported-only, 0 mismatch, 0 not-comparable. This is metadata comparison only; raw-byte SHA-256 and restore remain NOT_RUN, E2 Replay 20 NOT_TRANSFERRED, Global Preservation BLOCKED.

D0 Run 42283741942 remains on `afbc65bae45a53ccc14fd9098014494d09ec70e3`; D4 Run 42387025927 on `1fb4898480629c0a327dbff13792d455cd205a59`; D5 Run 42393413807 on `c757126ac27e8f6606f38b14324119cc22604858`. Exact D0-D6 Final Head is NOT_ESTABLISHED. Project remains `T2_INTERIM / NOT_FINAL_BLOCKED`.
