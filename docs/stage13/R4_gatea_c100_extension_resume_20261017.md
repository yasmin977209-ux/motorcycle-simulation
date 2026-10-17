# R4 — Recovery of cancelled C100 Gate A Golden extension

- Date: 2026-10-17
- CP: `CP-GATEA-C100-GOLDEN-RESUME-20261017`
- Original Run: `38991347472`, original tested head `7e0ff045eb909a121f1f8604f927642f2fad26e8`
- Continuation branch: `tmp/cp-gatea-c100-resume-20261017`
- Base main HEAD: `647c19826b90d8224ce73ef9b90c306a45e03fb0`
- Normative reference SHA-256: `ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479`

## R4 before change

| العنصر | الحالي | المرجع/القرار والفرع | النص الحاكم | الحكم |
|---|---|---|---|---|
| Original run | Run 38991347472 completed as `cancelled` after the generation step hit the 120-minute job limit. | Original workflow blob `a6c083860e1c35682ed42ecd5ce11042b64a5b48`; Run/Job evidence. | D-2026-10-17-07: exactly IDs 2..600 for five C100 scenarios; 2,995 rows. | `WORKFLOW_DEFECT`: no supported resume path; not a model assertion failure. |
| Partial artifact | ZIP 93,999 B / SHA-256 `d6b867529a8998f2230055c637209c67a4e0165b4f1ab68b62aa4cb8b223bfd6`; member SHA-256 `fa222cdf3249df19837b6cfec8dad732365df1dc43f4793e2bd9397c3451f3aa`, 1,815,129 B. | Artifact 12087982889, Run 38991347472. | Preserve completed IDs and provenance; never restart from ID 2 or rerun any completed key. | 2,048 rows validate, with 947 exact missing keys. |
| Approved baseline | 25,205 fingerprints; ordered-map SHA-256 `0fbe3aa87a253f9527953c77b0a122871c9344f75ece6c8a49da99b2a85c1ce1`. | D-2026-10-17-07; the candidate's read-only `scripts/golden_reference_provider.py` rebuilds from prior pinned Actions artifacts. | Reproduce the 25,205 map before appending C100. | Must be re-verified at runtime before any new IDs are generated. |
| Source identity | `SOURCE_SHA=f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`, producer source commit `0156c5f4272eb0ca7e32442657d0df9eaf4973d3`, seed `20270101`. | D17 and the original CP R4. | All 14 model source blobs must match; preserve RNG and scenario parameters. | Immutable source closure. |

## Bounded recovery design

1. Verify Run/branch/head, Artifact ID, archive bytes/digest and ZIP member bytes/digest.
2. Parse and re-hash all 2,048 prior records; enforce exact prefix coverage and unique scenario/trial keys.
3. Reconstruct the approved 25,205-row map from immutable existing Actions artifacts; require ordered SHA exactly `0fbe3aa87a253f9527953c77b0a122871c9344f75ece6c8a49da99b2a85c1ce1` before generation.
4. Generate only `C100_G070` IDs `253..600` (348) and `C100_G100` IDs `2..600` (599): exactly 947 keys.
5. Preserve separate provenance for records from original Run 38991347472 and the continuation Run. Recompute all record hashes, the extension map SHA and the combined 28,200-row map SHA after appending to the verified baseline.
6. Keep the temporary workflow pinned to `tmp/cp-gatea-c100-resume-20261017`, with `contents: read`, `actions: read`, a 120-minute timeout, no `workflow_dispatch`, no non-C100 trials and no checkpoint acceptance. Upload output plus progress on failure.

## Acceptance and limits

- Exact prior archive, 2,048 prior record hashes and coverage: verify at runtime.
- Baseline map: 25,205 / 25,205 records, SHA `0fbe...`: runtime reconstruction required before generating anything.
- Added records: 947 only, zero replays.
- Final C100 extension: 2,995 unique records, C100 IDs 2..600; full candidate map: 28,200 with C100 IDs 1..600.
- The emitted artifact is labelled `COMPLETE_PENDING_INDEPENDENT_ARTIFACT_AUDIT`; a successful run alone does not promote a reference. The actual ZIP/member and saved JSON must be independently inspected after upload.
- No production checkpoint, stability acceptance, main update, merge or release is in scope.
