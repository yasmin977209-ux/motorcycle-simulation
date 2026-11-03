

## D3 owner decision and Artifact acceptance — 2026-11-03 (append-only)

- Owner explicitly accepted GitHub Actions Artifact 13160434943 as the final immediate D3 workbook delivery mechanism in place of Git LFS.
- Independent acceptance Run 41682389098 tested commit a05d71adb3d45140ebc07f523dad2569e560c7c4; source Run 41480650491, source SHA 2f3cb05bf668cd003cdb5bcb121d2217d629d9f1.
- Artifact: 535358202 bytes; SHA-256 513f2a2edab7083c4f36d0e655de6b8a939403f67b51cf0d0d65d4e51f437b04; expiry 2026-12-02T16:56:31Z.
- Arabic and English workbook byte sizes and SHA-256 fingerprints, ZIP CRC, XLSX CRC, 185-sheet structure, zero formula cells and zero Excel error cells independently verified.
- D3-18: PASS_SCOPED. Overall D3: PASS_SCOPED_WITH_LIMITATIONS. Existing scoped limitations and upstream gate states remain unchanged. D4 NOT_STARTED; FINAL_ACCEPTED NOT_DECLARED.
- Git LFS is not required under the owner decision; no LFS upload or paid transfer was made.
- Retention warning: this Actions Artifact is temporary and expires at the date above; this is not permanent archival.
- No Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, identity change, main write, merge, Release or final acceptance occurred.


## D4 DOCX report build — 2026-11-03 (append-only)

- Triggering tested SHA: e39549034af3ce360cab3e57b120bf6ef47d88bc; workflow Run: 41691787043.
- D3 was revalidated closed as PASS_SCOPED_WITH_LIMITATIONS before D4 began.
- Five required DOCX reports generated from the pinned Number Registry and approved v2.4.0 reference only.
- Arabic RTL and English LTR properties checked; both executive summaries rendered and page-count checked at two-to-three pages.
- Every displayed registry value carries number_id; missing metrics remain MISSING_EVIDENCE. The five historical accounting fields were not inferred or zero-filled.
- Mandatory section 17.3 disclosures included; no market assumptions, Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, identity change, main write, merge, Release or final acceptance.
- D4 disposition: PASS_SCOPED_WITH_LIMITATIONS, subject to final commit/readback evidence in D4 build report. D5 not started. FINAL_ACCEPTED remains NOT_DECLARED.


## D4 DOCX report build — 2026-11-03 (append-only)

- Triggering tested SHA: 13a23122e44240760b461df9d269509218592fd3; workflow Run: 41692077060.
- D3 was revalidated closed as PASS_SCOPED_WITH_LIMITATIONS before D4 began.
- Five required DOCX reports generated from the pinned Number Registry and approved v2.4.0 reference only.
- Arabic RTL and English LTR properties checked; both executive summaries rendered and page-count checked at two-to-three pages.
- Every displayed registry value carries number_id; missing metrics remain MISSING_EVIDENCE. The five historical accounting fields were not inferred or zero-filled.
- Mandatory section 17.3 disclosures included; no market assumptions, Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, identity change, main write, merge, Release or final acceptance.
- D4 disposition: PASS_SCOPED_WITH_LIMITATIONS, subject to final commit/readback evidence in D4 build report. D5 not started. FINAL_ACCEPTED remains NOT_DECLARED.


## D4 DOCX report build — 2026-11-03 (append-only)

- Triggering tested SHA: 17696ec48557a33f2c231634ba25f26cf831800e; workflow Run: 41694460895.
- D3 was revalidated closed as PASS_SCOPED_WITH_LIMITATIONS before D4 began.
- Five required DOCX reports generated from the pinned Number Registry and approved v2.4.0 reference only.
- Arabic RTL and English LTR properties checked; both executive summaries rendered and page-count checked at two-to-three pages.
- Every displayed registry value carries number_id; missing metrics remain MISSING_EVIDENCE. The five historical accounting fields were not inferred or zero-filled.
- Mandatory section 17.3 disclosures included; no market assumptions, Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, identity change, main write, merge, Release or final acceptance.
- D4 disposition: PASS_SCOPED_WITH_LIMITATIONS, subject to final commit/readback evidence in D4 build report. D5 not started. FINAL_ACCEPTED remains NOT_DECLARED.


## D0-D4 consolidated live closure — 2026-11-03 (append-only)

- D0 PASS_SCOPED_WITH_LIMITATIONS: three pinned artifacts 12852969854, 12998778418 and 12630457193 downloaded and size/SHA-256 verified in Run 41694461194.
- D1 PASS_SCOPED_WITH_LIMITATIONS: Run 41694461194 compiled six source modules and two test modules, passed 34 artifact-backed tests, and passed exact tested-head assertion on 17696ec48557a33f2c231634ba25f26cf831800e.
- D2 PASS_SCOPED_WITH_LIMITATIONS: Registry 2,640 entries, 1,000 series, 2,086,550 daily points; registry SHA-256 743ffcced8de09a766870f201c352aabcf5789c43c84bfeae654a939700e4f87.
- D3 PASS_SCOPED_WITH_LIMITATIONS: Artifact 13160434943 accepted in Run 41682389098; exact-head Run 41694461171 passed 36 tests and 35 Raw readbacks.
- D4 PASS_SCOPED_WITH_LIMITATIONS: Run 41694460895 generated five DOCX; both summaries were 3 pages; 5 tests passed; 13 Raw readbacks and exact output HEAD passed at c0bfcbadac8d90932d52eb4ecaec2e72e6b4b909. Evidence Artifact 13260326514.
- The final exact-head validation workflow and the dedicated D1-D2/D3 workflows are triggered by the consolidated documentation commits. Do not treat the final combined closure as exact-head validated until all three runs succeed on the same SHA.
- Preserve all fixed findings: financial Gate A PASS_SCOPED; production Gate A NOT_DECLARED; Gate B N=2400 FAIL_SCOPED (10/10); Stability NOT_CONVERGED (0/60); N=4800 NOT_EXECUTED; Full Logging 105 representative keys only; C100 Golden NOT_RUN; five historical accounting fields MISSING_EVIDENCE.
- D5 NOT_STARTED; wait for explicit owner instruction. FINAL_ACCEPTED NOT_DECLARED. No Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, identity change, main write, merge or Release.


## D5 package publication — 2026-11-03 (append-only)

- Workflow Run 41704252218; tested source SHA 4aa8172c829f1545e4509f5196cd2a23e24ec0ad; publication commit 4aa8172c829f1545e4509f5196cd2a23e24ec0ad.
- D5 package ZIP: 519102426 bytes; SHA-256 300720a318864fb3969a8813a76c65473be3c8648bea7fb359de23230a8ff4f5; 8 members; reopened, exact inventory and CRC PASS.
- manifest SHA-256 db41532d87791da707a512e65a689ddad2066bb8bfceead53633a18fd66710c7; external SHA256SUMS SHA-256 1354c8e8283ac6fd14b8345153f5fb61d16190d959eaa6a474be8eecc4a18a5f (10 entries).
- New GitHub Actions Artifact ID 13264003231; size 519115272; digest sha256:7da3dc1bba9972854536b3615f567029e66a0988e90c79da2a555b10b85b9fe5; downloaded ZIP SHA-256 7da3dc1bba9972854536b3615f567029e66a0988e90c79da2a555b10b85b9fe5; expires 2026-12-03T19:37:05Z; retention 30 days.
- Independent download by exact Artifact ID matched metadata digest/size, exact outer inventory, CRC and every payload byte.
- Classification remains T2_INTERIM / NOT_FINAL_BLOCKED; D5 scoped package integrity only. Full 177-unique-test acceptance suite NOT_RUN; final acceptance NOT_DECLARED.
- No Trial/Simulation/Monte Carlo/N expansion/backfill/zero-fill/identity change/main write/merge/Release/D6.


## Final D0-D5 review and new-chat handoff — 2026-11-03 (append-only)

- Live baseline before this handoff documentation: branch `tmp/d1-rebuild-20261101` HEAD `5fad8f563d9db3ac572e1198c4c1eaa6b2ea4d42`; `main` remains `c6e54349a5e94f65d5aa9f83141f225d777bb474`.
- D0-D5 dispositions remain scoped: D0-D4 `PASS_SCOPED_WITH_LIMITATIONS`; D5 `PASS_SCOPED_WITH_LIMITATIONS`. This is not project final acceptance. D6 has not started.
- D5 publication: Run `41704252218`, source/tested SHA `4aa8172c829f1545e4509f5196cd2a23e24ec0ad`, Artifact `13264003231`, 519,115,272 bytes, digest `sha256:7da3dc1bba9972854536b3615f567029e66a0988e90c79da2a555b10b85b9fe5`, expiry `2026-12-03T19:37:05Z`. Inner D5 ZIP: 519,102,426 bytes, SHA-256 `300720a318864fb3969a8813a76c65473be3c8648bea7fb359de23230a8ff4f5`, exactly eight members. manifest SHA-256 `db41532d87791da707a512e65a689ddad2066bb8bfceead53633a18fd66710c7`; external SHA256SUMS SHA-256 `1354c8e8283ac6fd14b8345153f5fb61d16190d959eaa6a474be8eecc4a18a5f` (10 entries).
- D5 workflow tests: `5 passed`, with one Python zipfile warning caused by the test intentionally inserting a duplicate `manifest.json` to verify rejection. Artifact was independently downloaded by exact ID and checked for metadata size/digest, exact outer inventory, CRC, and byte equality of the three payloads. Job log ended with `D5_PUBLICATION_EXACT_FINAL_HEAD_PASS 5fad8f563d9db3ac572e1198c4c1eaa6b2ea4d42` and Raw readback triples for eight paths.
- Important field interpretation: `D5_PACKAGE_PREFLIGHT_2026-11-03.json` records `publication_commit_sha=4aa8172...` because workflow code assigns the triggering `github.sha`; this is the workflow source/tested SHA, not the later commit that contains publication evidence. The actual evidence/continuity commit is `5fad8f563d9db3ac572e1198c4c1eaa6b2ea4d42`. Do not silently rewrite the old field; this note clarifies it.
- Compare `00dfa15934780271a9be98d55d4cdd83f10e3740...5fad8f563d9db3ac572e1198c4c1eaa6b2ea4d42`: 10 commits, with changes limited to D5 workflow/script/tests and append-only D5 documentation/status. No D0-D4 implementation or deliverable paths changed in this delta. D0-D4 final consolidated gate run `41697223043` passed on `00dfa15934780271a9be98d55d4cdd83f10e3740`; later D1-D2 Run `41704252084` and D3 exact-head Run `41704252069` passed on `4aa8172...`. Thus do not claim a single all-stage CI run tested every D0-D5 component on 5fad; D5 itself has exact-final-head readback on 5fad, and D0-D4 evidence remains unchanged in the compare delta.
- Governing reference v2.4.0 remains owner-approved; SHA-256 `225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b`, 401,397 bytes. Historical S6 execution reference v2.3 remains distinct. v2.3.1 remains closed/unapproved.
- Project-wide findings preserved: Financial Gate A `PASS_SCOPED`; Production Gate A `NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS`; Gate B at N=2400 `FAIL_SCOPED (10/10)`; Stability `NOT_CONVERGED (0/60)`; N=4800 `NOT_EXECUTED`; Full Logging is 105 representative keys only; C100 Golden `NOT_RUN`; five accounting fields remain missing and must not be inferred or zero-filled.
- No Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, identity change, main write, merge, Release, `FINAL_ACCEPTED`, `P17_FINAL_ACCEPTED`, `P18_RELEASED`, or `CONVERGED` occurred.
- New canonical handoff: `docs/stage_d/D0_D5_FINAL_HANDOFF_2026-11-03.md`. New chat must read it and the live prompt library REV2 before any action. D6 is eligible to start only after new chat independently revalidates D0-D5 and the D5 Artifact; use D6 Post-Write Audit prompt from the live library. D6 does not mean P17 acceptance or final acceptance.
