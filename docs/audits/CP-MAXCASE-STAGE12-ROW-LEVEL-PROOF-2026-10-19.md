# CP — MaxCase selection and Stage 12 daily row proof

Date: 2026-10-19
Status: **PASS_ROW_LEVEL_MAXCASE_AND_DAILY_COMPLETENESS** for this read-only verification only. This does not mark Stage 13 or delivery PASS.

## Identity and evidence

- Verifier workflow run: [39309810806](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39309810806), conclusion `success`, tested SHA `23162f417dba32192f1ec2a8d34b1d5bc461bc9a`.
- Evidence artifact: ID `12215292742`, name `cp-maxcase-stage12-readonly-evidence`, ZIP size 26,049 bytes, SHA-256 `280574a3ce8929a97b8f961a99f1b69ccf342c8a3dbe4895e35756807da4a3ed`. [Artifact](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/39309810806/artifacts/12215292742).
- JSON evidence member: 156,494 bytes, SHA-256 `5177085429b5a0702f8808d8cc2f65936da8e6504deec6a43ad19f149465e768`; Markdown evidence member: 2,664 bytes, SHA-256 `fabd36348372599f18263bda25ad6d4608b798a06d26ee541c5936584ad475d9`.
- Stage 7 run `37225915321`, head `e0b2fab6710833774937d778097363d7a8ee8e59`, conclusion `success`.
- Stage 10 run `37709936740`, head `ca73f2df37baacebbcad965fc5f433f129675820`, overall conclusion `failure`; the exact canonical `bench-{scenario}-1` jobs for all 25 scenarios were verified `success`. The aggregate Stage 10 failure is preserved and is not relabelled PASS.
- Stage 12 run `37964656154`, head `0156c5f4272eb0ca7e32442657d0df9eaf4973d3`, conclusion `success`.
- Source SHA `f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b`; master seed `20270101`; schema `stage12-daily-accounting-v1`; Stage 9A manifest global SHA-256 `892da438955160bb59aff3046271402f57bdd61a4abb35f41db7188f61346ff6`; Stage 12 global SHA-256 `7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44`.
- Exact main report blobs: manifest `e796fa2443493b607f1f9c60b58eb63607959c26`, roll-forward `6084e8f68fa649fcf0726daa04f41ae9b0636706`, closure `81bc3cd9c7666487b69b644dcc3291d0547c8e8b`.

## Proof criteria and result

- 25/25 scenarios, 11,005/11,005 canonical TrialResult rows, and 22,546,465/22,546,465 Stage 12 daily rows were read and checked.
- Every source block's TrialResult rows matched its official `per_trial_sha256`; Stage 7 block fingerprints matched the official Stage 9A manifest where defined; Stage 10's 451–550 block matched its metadata with the narrowly documented in-memory suffix parser for the known `\\n` serialization defect.
- Every Stage 12 Parquet member SHA-256 matched both existing Stage 12 validation reports. Schema and embedded identity matched; trial IDs were unique and contiguous; every trial's daily dates were contiguous from 2027-01-01 with no duplicate/missing day; `result_sha256` was constant within each trial.
- For each selected MaxCase, the official summary fingerprint matched the selected Stage 12 trial's `result_sha256`; selected daily row count/date span is shown below.
- Selection rule applied exactly: highest positive `Final_Net_Project_Equity`; ties choose the smallest integer `trial_id`. No scenario returned `UNDEFINED_BUSINESS_RULE`.
- No Trial/Monte Carlo/checkpoint/replay was run; no source, seed, RNG, dataset, Parquet, golden, main, state, or assembler was changed.

## Scenario-by-scenario selected MaxCase evidence

| Scenario | Canonical trials | MaxCase trial_id | Final_Net_Project_Equity (SAR) | Selected daily rows | Date span | Stage 7 artifact | Stage 10 artifact | Stage 12 artifact | Stage 12 member SHA-256 |
|---|---:|---:|---:|---:|---|---:|---:|---:|---|
| C100_G100 | 1 | 1 | 209671000 | 2198 | 2027-01-01 → 2033-01-06 | 11312276587 | — | 11632649937 | `b2965dd4e2426631dcb503012817c63fe206c61e9f054d95c49716e1e3c448ae` |
| C100_G070 | 1 | 1 | 209671000 | 2198 | 2027-01-01 → 2033-01-06 | 11311843040 | — | 11633660943 | `cfb67a65f99a548d0175f15290d0f446c79c07008ffaa6fd3ab931e63aa8cbaa` |
| C100_G050 | 1 | 1 | 209671000 | 2198 | 2027-01-01 → 2033-01-06 | 11311992664 | — | 11633475828 | `848ea1bc628c286be4f57d6dc807e2c398ab5d45fada7e5cfdf86db9652d3db1` |
| C100_G030 | 1 | 1 | 209671000 | 2198 | 2027-01-01 → 2033-01-06 | 11312320486 | — | 11633915162 | `51533c10feaddd6124796dee76280662f0c4e79a2bc3cbb7c14acf27436e1c96` |
| C100_G000 | 1 | 1 | 209671000 | 2198 | 2027-01-01 → 2033-01-06 | 11312176891 | — | 11633515803 | `df1797e95324433c0db4d450056ca1e5f7e16f1acf6279b8fd83dae275669e52` |
| C085_G100 | 550 | 439 | 209893000 | 2200 | 2027-01-01 → 2033-01-08 | 11312088905 | 11521762421 | 11633202857 | `200645be63674cb2c65bff0bfb89ddc00bdfab9a3cda5e5e5b8d93ba7e23e43a` |
| C085_G070 | 550 | 464 | 209888500 | 2201 | 2027-01-01 → 2033-01-09 | 11313126058 | 11521561571 | 11634340863 | `61d7a844865d47545d23f84fa71e51491c658e5293be490a5c97992374d3fc93` |
| C085_G050 | 550 | 207 | 209877500 | 2198 | 2027-01-01 → 2033-01-06 | 11313071154 | 11521822235 | 11634412024 | `104687ab9d841da2b4360477e390839a414733829f4513cbf98db69655674772` |
| C085_G030 | 550 | 53 | 209880000 | 2198 | 2027-01-01 → 2033-01-06 | 11313066122 | 11521941330 | 11633238307 | `e5b8a3efe0cf78b8d98896507c4cd97db3f2910f332f73a97f16df4e996d7c54` |
| C085_G000 | 550 | 408 | 209888000 | 2203 | 2027-01-01 → 2033-01-11 | 11312590249 | 11521931777 | 11633978084 | `f77beafdcfe43132faa00abab80141f8bf6153fbf35efacfe282d38f0c6ddf38` |
| C070_G100 | 550 | 106 | 209806500 | 2202 | 2027-01-01 → 2033-01-10 | 11312239690 | 11520898788 | 11634076431 | `90fd4f7102a7741d361f29726700ee87516cfa7e05543d5f3537d0cbfa41b238` |
| C070_G070 | 550 | 441 | 209749500 | 2198 | 2027-01-01 → 2033-01-06 | 11312294476 | 11521812497 | 11633473363 | `51a39d399667b69691f574f6fe56ddebba9c86d556c2835c192873fe40be5cf5` |
| C070_G050 | 550 | 544 | 209748500 | 2200 | 2027-01-01 → 2033-01-08 | 11313185526 | 11520854203 | 11634486809 | `b4463fbf1885dd04b26453e0842a1c6ad433043c05f61c206561f9eb171a5213` |
| C070_G030 | 550 | 429 | 209621500 | 2200 | 2027-01-01 → 2033-01-08 | 11312915385 | 11522130280 | 11633882202 | `3c499fbfbc1f6caa28e6617134d2b09e956813422f51ae7908e22c6aa8eed4a6` |
| C070_G000 | 550 | 165 | 209787500 | 2202 | 2027-01-01 → 2033-01-10 | 11312109145 | 11522130563 | 11633054556 | `3f6543a6f4cc2ed97274ab41164c87077305f53060a53a99b3eb73654ead3644` |
| C050_G100 | 550 | 172 | 348013800 | 2233 | 2027-01-01 → 2033-02-10 | 11312766984 | 11521718148 | 11633813338 | `81b6e72e588964d54b33f9951f25c8a5c8ec9e458b1c7287c0f130efca7b460c` |
| C050_G070 | 550 | 7 | 329546000 | 2222 | 2027-01-01 → 2033-01-30 | 11312963284 | 11522185658 | 11633956636 | `08659990ead7a7da5a275d4496479bfc81badad820652dc6ba0a0765b42a7c82` |
| C050_G050 | 550 | 543 | 324213800 | 2232 | 2027-01-01 → 2033-02-09 | 11312971843 | 11521917867 | 11633538351 | `f4531eebeb1f30e0160b47229d50d1177a9a2f72007f5b8cd3d0234a46e112c6` |
| C050_G030 | 550 | 122 | 316720350 | 2231 | 2027-01-01 → 2033-02-08 | 11313227800 | 11521967872 | 11633891917 | `defeb970853ee9ebcd7af349cc902404996ecff250a23bb5c7e1f3686849c983` |
| C050_G000 | 550 | 60 | 308412450 | 2235 | 2027-01-01 → 2033-02-12 | 11312813109 | 11521429557 | 11634501915 | `6beecb837a3c6b71f34aedbeb958e8dd176cce3d60b2dfa1b95ee9bd57e6a380` |
| C030_G100 | 550 | 280 | 101923650 | 1669 | 2027-01-01 → 2031-07-27 | 11313136372 | 11521453747 | 11633731337 | `a2e01d1db937216f2121e5dbf554c8371af23754cc60e22848b20c4ad700b702` |
| C030_G070 | 550 | 134 | 71289450 | 1703 | 2027-01-01 → 2031-08-30 | 11313072117 | 11522086062 | 11634295127 | `77be80edb5d5ab71dbe8faeab52b3ffb88098f25176aff6f4112f2f5d19f1a0c` |
| C030_G050 | 550 | 366 | 56978100 | 1704 | 2027-01-01 → 2031-08-31 | 11313056625 | 11521568447 | 11634060847 | `aec638c6313f602148bf5fefaaa9885f5a9b9abd46ad0467f83292b6680d99c4` |
| C030_G030 | 550 | 233 | 42228800 | 1665 | 2027-01-01 → 2031-07-23 | 11313116830 | 11522066499 | 11633466266 | `2b95f26624abb6c4f3a7145e457c3f2f8764a9d037e2de326a9dd768d42d40c9` |
| C030_G000 | 550 | 199 | 28604150 | 1655 | 2027-01-01 → 2031-07-13 | 11313086528 | 11521927219 | 11634020857 | `b89d0fffcd98465aa9891e76c84559c466706643cbece02967b12bae2d96e85d` |

## Disposition

Row-level selection and daily completeness are proven for this CP. This evidence is not Gate A production execution, does not erase the historical Stage 10 aggregate failure, and does not prove the remaining Stage 13/delivery gates. The next step is a follow-up R4 for the minimal candidate-only assembler integration, before any code edit.
