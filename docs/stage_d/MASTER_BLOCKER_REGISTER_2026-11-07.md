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
