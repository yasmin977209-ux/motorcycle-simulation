# CP-STAGE10-JSON-NEWLINE-SERIALIZATION — candidate-only repair — 2026-10-19

## Result
A one-line serialization correction is saved and read back on a temporary branch. The exact Python serialization behavior was reproduced with a local pure-Python semantic check: a real newline parses successfully, while a literal backslash-n after the JSON object raises `JSONDecodeError: Extra data`. No project test suite, Workflow, Stage10 benchmark, simulation, Trial, Checkpoint or historical artifact regeneration was run.

## R4 and code identity
- Before-change R4: [CP-STAGE10-JSON-NEWLINE-SERIALIZATION-R4_2026-10-19.md](https://github.com/yasmin977209-ux/motorcycle-simulation/blob/tmp/cp-session-continuity-20261017/docs/audits/CP-STAGE10-JSON-NEWLINE-SERIALIZATION-R4_2026-10-19.md), blob `6198a981daf77d482c4cc9c2b156f5604a2cf7b3`.
- Candidate branch: `tmp/cp-stage10-json-newline-20261019`, based on main `7c41ac64c4b599f4e1d6a50be055f82cdd87a7b5`.
- Candidate HEAD after edit: `47bcd45076f9a264307a30e5cddae51855ff2a42`.
- Old blob: `scripts/stage10_benchmark.py` `d54602982b6422939955ca841a251ecd250b4139`.
- New blob after read-back: `bfa6477f94561808230f71d23d00a70e68488444`.
- Compare against current main: ahead 1 / behind 0; the sole changed path is `scripts/stage10_benchmark.py`.

## Physical evidence motivating the repair
Historical completed Run `37709936740`, candidate/source head `ca73f2df37baacebbcad965fc5f433f129675820`, artifact `11522066499` (`stage10-bench-C030_G030-1`) was downloaded read-only. The ZIP size is 67,917 bytes and SHA-256 `bfd36514099caf0254f18843bd44c410ef430708ec05d16784812cca16181cec`.

Three newly written JSON members were invalid as a single JSON document because each ended with literal backslash-n bytes:
- `block_451_550_metadata.json`: 7,815 bytes; SHA-256 `67f3bff72a145f1060bb1c974d5daec74dac89de652170f90947e52e82ba90b7`
- `metrics.json`: 13,764 bytes; SHA-256 `d9786ecaeb9f23445f35520ad5a118553ad3ce68d94ada5a952560d149e2d0ce`
- `resume_descriptor.json`: 9,608 bytes; SHA-256 `f80ab39d0c554d28a770ca83e08882aa955a2f609e3d65d0891e48f499139b01`

For all three, `json.loads` reported `JSONDecodeError: Extra data`; removing only those two literal suffix characters allowed parsing. The copied baseline metadata members parsed normally. This is a historical serialization-format failure in the inspected artifact; it does not prove that the underlying trial-result rows were corrupted.

## Correction and verification boundary
The source change is limited to `write_json` line 72: change `json.dumps(...)+ "\\n"` (literal backslash plus n at runtime) to `json.dumps(...)+ "\n"` (real newline). The read-back line now contains the real-newline escape and no longer has the double-backslash source literal. A local semantic reproducer printed `LITERAL_BACKSLASH_N_REPRODUCES_JSONDECODEERROR=Extra data` and `REAL_NEWLINE_JSON_ROUND_TRIP=PASS`.

This is a source-level correction for future outputs. The three historical artifact members were not rewritten, and no Stage10 workflow or production output was regenerated. No tests or workflows were modified. No changes were made to main, `state.json`, the reference, source SHA, seed/RNG, sampling/threshold/cohort/Trial IDs, historic Parquet, or production trial state. Main remains `7c41ac64c4b599f4e1d6a50be055f82cdd87a7b5`; main state remains blob `2178260bb18efeb81437486f13b6d10cf5e85936`, stage `12-CLOSED`, `FINAL_DELIVERY_BLOCKERS_OPEN`.

## Next validation
A focused approved test should serialize a mapping through `write_json`, assert the result has one JSON document and an optional actual trailing LF byte, and round-trip the parsed value. The existing test-workflow scope conflict still prohibits reusing or changing a workflow to execute it. The historical artifact remains malformed and must be treated as such; this CP does not repair or reclassify it.
