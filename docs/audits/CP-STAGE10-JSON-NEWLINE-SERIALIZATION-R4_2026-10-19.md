# CP-STAGE10-JSON-NEWLINE-SERIALIZATION — R4 before source fix — 2026-10-19

## R4 identity
- Current main HEAD: `7c41ac64c4b599f4e1d6a50be055f82cdd87a7b5`
- Current `scripts/stage10_benchmark.py` blob: `d54602982b6422939955ca841a251ecd250b4139`
- Historical benchmark Run: `37709936740`, branch `tmp/stage10-bench-20261008`, source code head `ca73f2df37baacebbcad965fc5f433f129675820`.
- Real benchmark artifact ID: `11522066499`, name `stage10-bench-C030_G030-1`; artifact SHA-256 `bfd36514099caf0254f18843bd44c410ef430708ec05d16784812cca16181cec`; 67,917 bytes.

## Finding

The source's `write_json` is line 72:

```python
def write_json(path,d): Path(path).write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True)+"\\n",encoding="utf-8")
```

The suffix in the Python source is `"\\n"` (literal backslash plus n at runtime), not `"\n"` (a real newline). Physical archive inspection confirms that the Stage 10-produced `block_451_550_metadata.json`, `metrics.json`, and `resume_descriptor.json` each end in the literal bytes `b'\\n'` after the closing brace. `json.loads` fails with `JSONDecodeError: Extra data`; after stripping only those two trailing literal characters, parsing succeeds. SHA-256 of the three members:
- `block_451_550_metadata.json`: `67f3bff72a145f1060bb1c974d5daec74dac89de652170f90947e52e82ba90b7` (7,815 bytes)
- `metrics.json`: `d9786ecaeb9f23445f35520ad5a118553ad3ce68d94ada5a952560d149e2d0ce` (13,764 bytes)
- `resume_descriptor.json`: `f80ab39d0c554d28a770ca83e08882aa955a2f609e3d65d0891e48f499139b01` (9,608 bytes)

The archive also contains a copied baseline `block_1_300_metadata.json` and Stage 10 block metadata for the 301–450 range that parse successfully, distinguishing the newly written malformed JSON files from copied historical baseline files. The archive includes only Parquet result blocks, metadata, metrics, and a resume descriptor; no individual daily accounting payload exists there, so it cannot supply Stage 13's missing MaxCase daily rows.

## R4 classification and minimal correction

- Classification: `K_CODE / SERIALIZATION_FORMAT_DEFECT`.
- Impact: tools that parse the newly generated metadata/metrics/resume JSON as one JSON document reject those artifact members. This is a confirmed format defect in the inspected Stage 10 artifact, not a claim that trial result values themselves are corrupted.
- Minimal candidate-only correction: change the `write_json` suffix from a literal backslash-n to an actual newline, i.e. `json.dumps(...)+ "\n"`. No other algorithm, trial, fingerprint, data or policy changes.
- Acceptance: one JSON object plus optional real trailing newline; `json.loads` succeeds for the serialized bytes; write/read-back preserves object equality; no change to payload values or SHA/fingerprint fields.
- Boundary: source file only on a new temporary candidate branch based on current main. Do not edit `main`, tests, workflows, historical artifacts, Trial IDs, source/seed/RNG/policy, or regenerate Stage 10 outputs. No Stage 10 workflow, Monte Carlo, Trial, or Checkpoint will be run.

## Execution status
This is R4 evidence recorded before the source edit. The historical artifacts remain unchanged and malformed; this change will only correct serialization for future use. Static inspection is established; no project test or workflow was run here.
