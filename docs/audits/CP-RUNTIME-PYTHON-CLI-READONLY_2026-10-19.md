# P8 — Python/dependency compatibility and CLI contract (read-only R4)

**Date:** 2026-10-19  
**Mode:** Read-only diagnostic per reference P8. No code/workflow/test/reference/state/dependency edits; no CLI execution, Monte Carlo, trial, or checkpoint.  
**main HEAD:** `647c19826b90d8224ce73ef9b90c306a45e03fb0`  
**requirements.txt blob:** `81131ac1437fc652ceff21831570ce19de314b78`  
**run_batch.py blob:** `0418ddea818c194a5b582df94778fa5f13a3ecc4`  
**README.md blob:** `08d666bff504609fc26acb4523c25812c61fac6e`  
**ACCEPTANCE_PORT.md blob:** `84a974aefbfdb5de14898cf5fc7016eea0c97ed2`

## 1. R4 — dependency compatibility

The controlling project reference, chapter 19.1, says: `Python 3.9 or newer`. P8 specifically instructs checking the official support range for the requirements on main and checking the actual CI environment, without raising the declared Python minimum by inference.

Current dependency constraints on main:

```text
pytest>=9,<10
numpy>=2.3,<3
pyarrow
python-dateutil>=2.9,<3
scipy>=1.17,<2
pyyaml
openpyxl>=3.1,<4
```

Official release metadata:
- NumPy 2.3.0 supports Python 3.11–3.13; NumPy 2.1 explicitly dropped Python 3.9 support. Source: https://numpy.org/doc/2.3/release/2.3.0-notes.html and https://numpy.org/doc/2.3/release/2.1.0-notes.html
- SciPy 1.17 requires Python 3.11–3.14 and NumPy >=1.26.4. Source: https://docs.scipy.org/doc/scipy/release/1.17.0-notes.html
- pytest 9.0+ has a minimum supported Python of 3.10; pytest 8.4 was the line supporting Python 3.9. Source: https://docs.pytest.org/en/stable/backwards-compatibility.html

These ranges are a metadata contradiction with the reference's Python 3.9+ contract, not a reason to modify the reference.

### Compatibility/CI evidence matrix

| Python version | NumPy | SciPy | Other dependencies | Install result | Tests run / result |
|---|---|---|---|---|---|
| 3.9 | Requirement requests `>=2.3`, whose supported line begins at 3.11 | Requirement requests `>=1.17`, which requires 3.11+ | `pytest>=9` also requires 3.10+ | **INCOMPATIBLE BY OFFICIAL METADATA**; no Python 3.9 install attempted in this review | Not run; no claim of runtime failure log. |
| 3.10 | NumPy >=2.3 officially starts at 3.11 | SciPy >=1.17 requires 3.11+ | pytest 9+ supports 3.10+, but does not remove NumPy/SciPy incompatibility | **INCOMPATIBLE BY OFFICIAL METADATA**; not installed here | Not run. |
| 3.11 | Actual CI resolver chose NumPy 2.4.6 | Actual CI resolver chose SciPy 1.17.1 | Python 3.11.17; pytest 9.1.1; PyArrow 26.0.0; python-dateutil 2.9.0.post0; PyYAML 6.0.3; openpyxl 3.1.5 | **PASS — actual GitHub Actions install succeeded** | Stage 5 validation Run `38331528160` at exact main SHA `647c19826b90d8224ce73ef9b90c306a45e03fb0`: first broad gate `162 passed, 1 skipped in 9.58s`; subsequent named test groups passed; final log `VALIDATION_STATUS=PASS`. |
| 3.12 | Supported by current NumPy 2.x lines, subject to the resolved version | Within SciPy 1.17's declared range | Full unpinned dependency set not exercised by main CI evidence reviewed | **NOT VERIFIED** in repository CI evidence reviewed | Not run. |
| 3.13 | NumPy 2.3 official range includes 3.13 | Within SciPy 1.17 declared range | Full unpinned dependency set not exercised by main CI evidence reviewed | **NOT VERIFIED** in repository CI evidence reviewed | Not run. |
| 3.14 | Later package releases may support this Python, while minimum-range constraints allow the resolver to choose newer candidates; current main CI does not establish that combination | SciPy 1.17 supports 3.14 | Full unpinned dependency set not exercised by main CI evidence reviewed | **NOT VERIFIED** in repository CI evidence reviewed | Not run. |

Actual CI record: [Run 38331528160](https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/38331528160), event `push`, workflow `stage5-main-postround2-validation.yml`, exact tested SHA `647c19826b90d8224ce73ef9b90c306a45e03fb0`, status/conclusion `completed/success`. Job `validate` ID `115082108816`. Its log records `Successfully set up CPython (3.11.17)`, the successful install of all seven requirement entries, actual resolved versions listed above, and `VALIDATION_STATUS=PASS`. This proves the dependency set installed and the scoped validation passed on Python 3.11.17 at that SHA; it does not prove Python 3.9 support.

**R4 ruling — `K_SPEC/DEPENDENCY_CONTRACT_CONFLICT`:** main's dependency constraints contradict the reference minimum Python 3.9. Do not independently lower dependency pins, raise the reference minimum, or change Workflows. Next execution requires an explicitly scoped CP-RUNTIME decision choosing a reference-compliant set of dependency versions (and testing it on Python 3.9 and 3.11) or owner approval of a reference change. The diagnostic itself made no such change.

## 2. R4 — CLI contract

### Controlling reference text (chapter 19.4)

```bash
python run_scenario.py <collection_prob> <recovery_rate> <trials> results/
```

The surrounding source also sketches a quick run as `python run_scenario.py $P $R 10 results/` for each of 25 combinations, and says the command must not accept or implement a `max_days` cutoff.

### Actual main tree and parser

- Git tree at main SHA `647c19826b90d8224ce73ef9b90c306a45e03fb0` was fetched recursively; it was complete (`truncated=false`, 223 entries).
- Neither `run_scenario.py` at repository root nor `scripts/run_scenario.py` exists on main. The GitHub code search for `run_scenario.py` returned no matching result. `run_full_simulation.py`, `pyproject.toml`, `setup.cfg`, and `tox.ini` are also absent from that tree.
- Root `run_batch.py` exists at blob `0418ddea818c194a5b582df94778fa5f13a3ecc4`. It is explicitly described in its parser as “Stage 8 batch runner with optional Stage 7 checkpoint resume.”
- Its parser requires `--scenario`, `--trials`, and `--output-dir`; optional options are `--start-trial-id`, `--resume-from-checkpoint`, and `--master-seed`. It does not accept the reference's four positional values `<collection_prob> <recovery_rate> <trials> results/`.
- Code path: `main(argv)` → `parse_args(argv)` → `run_batch(..., source_sha=os.environ.get("SOURCE_SHA"))`. It invokes `monte_carlo.run_trials_sequentially`, writes `trials_summary.parquet`, `trials_summary.jsonl.gz`, `state.json`, and `statistics.json` under the chosen output directory, and may run additional trials. This is a checkpoint-aware batch contract, not evidence of an equivalent four-positional-argument CLI. This review did not execute it.
- `README.md` blob `08d666bff504609fc26acb4523c25812c61fac6e` does not supply a working `run_scenario.py` command. No console entry point or package metadata was found in the root tree.

| Element | Current | Reference/authority | R4 ruling |
|---|---|---|---|
| User-facing single-scenario CLI | Missing on main | Reference 19.4 requires `python run_scenario.py <collection_prob> <recovery_rate> <trials> results/` | **`WORKFLOW_DEFECT/CLI_ENTRYPOINT_MISSING`** relative to the described project contract. |
| Existing `run_batch.py` | Different named options, source-bound batch/resume behavior and artifacts | P8 expressly says its existence does not prove equivalence | Not a replacement; do not invent aliases or overload its signature without a CP-specific R4 and explicit execution permission. |
| `max_days` | No `run_scenario.py` exists to inspect; no such option was confirmed from a compatible CLI | Reference says no `max_days` parameter and no simulation cutoff in the engine | Remains **unverified for the absent entrypoint**; do not claim CLI acceptance. |
| Actual run test | None attempted, deliberately | P8 is diagnosis only; runtime CP requires separate approval before changes | No claim that parsing or running the documented CLI passed. |

## 3. Decision and next permitted action

1. Keep main `SOURCE_SHA`, model/data/history and reference untouched.
2. Keep Python minimum 3.9+ as the authoritative requirement until a proper owner decision; meanwhile the present dependency requirements must be treated as incompatible with that support claim for Python 3.9–3.10. CI proves only Python 3.11.17.
3. Record the missing CLI as a distinct code-contract defect. Before implementing, identify the reference's exact collection-probability numeric encoding, recovery-rate encoding (including percent vs fraction), accepted trial-count constraints, output artifact contract, validation/error behavior, and the smallest safe test scope from the reference and existing tests. Do not assume `run_batch.py` is equivalent.
4. Any runtime code/dependency adjustment belongs in a separately authorized CP-RUNTIME on a temporary branch with a written R4, exact-SHA tests on Python 3.9 and 3.11, and actual CLI argument/error tests. Any Workflow changes require their own explicit approval; do not change the reference to conceal the mismatch.
5. No CLI, Monte Carlo, new trials, checkpoints, production artifacts, dependency changes, tests or Workflows were run/modified during this P8 diagnosis.

**Status:** `CP-RUNTIME P8 READ-ONLY R4 COMPLETE; DEPENDENCY CONTRACT CONFLICT VERIFIED; DOCUMENTED CLI MISSING ON MAIN; PROJECT PARTIAL`.
