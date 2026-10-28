# October 28 evidence: the callback's telemetry without a history, computed trend words

Slurm job 24929555 on MedicineBow (University of Wyoming), CPU partition `mb`,
node mbcpu-010, 4 cores, 12 min 15 s: PODFoam in OpenFOAM v2212 (Apptainer
image `of2212.sif`) with the Python callback of `main` (`2ed6da2`, copied in
[callback-main/](callback-main/python_module.py)) and of the branch
`callback-telemetry-trends` (`16d665e`), on the same case with the same
settings. The changes are described in
[llm_demo/README.md](../../../Solver_Examples/PODFoam/llm_demo/README.md#telemetryjsonl).

## What ran

| Case | Callback | Request |
|---|---|---|
| `describe-main`, `describe-new` | main, branch | describe at step 100 |
| `sequence-main`, `sequence-new` | main, branch | sequence with frames at steps 100, 150 and 200 |
| `sequence-tn-new` | branch | the same sequence with `LLM_SEQUENCE_PROMPT=tn` |
| `par2-describe-main`, `par2-describe-new` | main, branch | describe at step 100, 2 MPI ranks (scotch) |

Every case: the staged step case of job 24757460
(`pod-llm-async.UM1RyJ/async-no-llm`: `0/`, `constant/`, `system/`, the start
state `0.1/` and its `pod_svd.py`), a 2D backward-facing step with 20,540
cells and a developed flow; 1,250 steps of 5e-6 s from t = 0.1 s; fields and
POD modes written every 250 steps; `LLM_ENABLED=0` (frames drawn, request body
built and written, nothing sent); `LLM_ASYNC=1`; `LLM_IMAGE_STYLE=v2`; plotted
window x 0 to 0.12 m, y 0 to 0.04 m; one BLAS thread; the same `LLM_RUN_ID`
for main and branch (`callback-check/<case>`). The other callback modules were
the branch's, which equal main's. PODFoam was built from the branch (its C++
equals main's) by `validation/run_v2106.sh`; the bridge validation passed. The
2-rank cases changed the rank check of their `pod_svd.py`, as the October 27
MPI test did. [callback_check.sbatch](callback_check.sbatch) is the job.

## Results

| Check | Result |
|---|---|
| Files, describe pair | 105 files of the written time directories, 4 frame files, the request body, `python_svd_audit.npz`, `telemetry.jsonl` and 26 input files identical; none only in one run, none differing |
| Files, sequence pair | the same, with 12 frame files |
| Files, 2-rank pair | 234 files of the processor directories, 4 frame files, the request body, `telemetry.jsonl` and 26 input files identical; `python_svd_audit.npz` not compared (below) |
| `telemetry.jsonl` | 1,250 lines in every run, identical between main and branch in all three pairs; no `telemetry.jsonl.tmp` left. The branch printed `PYTHON LLM telemetry lines=1250 appends=3 failed_appends=0 file=telemetry.jsonl` in each of its four runs |
| Solver log | 18,761 solver lines (residuals, Courant numbers, continuity errors, times, POD snapshot and SVD lines) identical in order in each serial pair; the 20,016 of the 2-rank pair identical as sorted lists, not in order |
| Records | `llm_request.json`, `llm_response.json`, `llm_result.json` differ only in timestamps, process ids, wall times, the arrival step and the pipe counts; the branch adds `computed_trends` to the sequence run's `llm_result.json` and `llm_response.json`, not to `llm_request.json` |
| Computed trends (`sequence-new`) | `increasing` (largest \|U\| 37.21 to 38.14 m/s, +2.44 %), `more_negative` (lowest p −335.04 to −376.20 m²/s², −10.9 %), `moves` (6.92 % of the plotted range); equal to `snapshot_runner.sequence_truth` of the three frames. No `computed_trends_agreement`: no model answered |
| `tn` form (`sequence-tn-new`) | the body (667,051 bytes) equals `readable_request.sequence_v2_payload(..., thresholds=True, numbers=...)` of its frames byte for byte, with the `tn` system prompt; its frames equal `sequence-new`'s byte for byte; the note gave 37.2103, 38.0911, 38.1414 m/s and −335.039, −367.852, −376.195 m²/s² |
| Default sequence body | equals the 2026-10-22 builder (`own_ranges=True`, nothing else) applied to the frames |
| Callback wall time per step | median 0.079 to 0.107 ms with main, 0.163 to 0.217 ms with the branch, which encodes each step's line in the solver process; steps 500 and 1,000 (appends) 13.7 to 22.0 ms with the branch; the last step 53 to 57 ms with main, 20 to 23 ms with the branch (`POD analysis callback returned` lines of the solver logs) |
| [memory.py](memory.py), 24,000 states | Python heap after the last of the 24,000 recorded states of the October 27 periodic run: 31.685 MiB with main (1.351 KiB per state), 0.067 MiB with the branch (peak 0.515 MiB); the last step, which writes `telemetry.jsonl`: 0.699 s with main, 0.023 s with the branch; median of the other steps 20 µs and 46 µs; steps 500, 1,000 and 1,500 (appends) 9.1, 9.2 and 11.6 ms, the slowest step other than the last 16.6 ms (step 19,000, an append); both versions wrote the recorded file (19,864,369 bytes) again byte for byte. Python 3.11.16 |
| Unit tests | 107 passed (`test_llm_client test_callback test_ablation_runner test_async test_picture_test`) |
| `verify_async.py` of the branch on the October 22 suite (`pod-llm-async.UM1RyJ`) | PASS |

The comparison ran twice. In the job, [compare.py](compare.py) reported FAIL
for the 2-rank pair: it compared that log in order and
`python_svd_audit.npz` byte for byte. Both differences come from the two
ranks, not from the callback: both processes print to one log in an order
that changes from run to run, and the test's POD module has both ranks save
`python_svd_audit.npz` to the same path at the same time, so the file is
unreadable in both runs (zip CRC errors). compare.py was changed to compare
a parallel log as sorted lists and to record the audit file (readable or not,
hash) without comparing it, and was run again on the same folder (Slurm job
24929607, mbcpu-006): PASS. Both results are here.

## Not tested

- No model answered (`LLM_ENABLED=0`), so these runs have no
  `computed_trends_agreement`; `test_async.ComputedTrendTests` checks it
  against a local test server.
- Appends that fail, are killed or are given up, and a state that cannot be
  encoded, are tested in unit tests only, not in a solver run; no disk
  failure or full disk.
- The solver runs had 1,250 steps; the 24,000-step figures come from
  memory.py's replay of recorded states, without a solver.
- One run per case on one CPU node; append times on the GPU nodes of the
  earlier runs are not measured. Two ranks only.

## Files

| Path | What it contains |
|---|---|
| `callback-main/python_module.py` | `main`'s callback at `2ed6da2`, run in the `-main` cases and loaded by `test_callback.TelemetryTests` |
| `callback_check.sbatch` | The job script |
| `compare.py`, `comparison.json` | The comparison above (rerun, job 24929607) and its result |
| `comparison-in-job.json` | compare.py's first result, in the job: FAIL for the 2-rank pair, as explained above |
| `memory.py`, `memory.json` | The 24,000-state replay, both versions, with and without tracemalloc |
| `callback-check-24929555.out` | The job's output |
| `validation.log` | The bridge validation's output |
| `unit-tests.log` | The unit tests' output in the job |
| `verify-oct22-suite.json` | `verify_async.py`'s report on the October 22 suite |
| `sequence-new/llm_result.json`, `sequence-tn-new/llm_result.json` | The branch's sequence results with `computed_trends` (and `sequence_prompt`) |
| `describe-main/log.PODFoam.gz`, `describe-new/log.PODFoam.gz` | Solver logs of the serial describe pair (gzip copies) |
| `HEAD`, `git-status.txt`, `changes.patch` | The worktree's state when the job started (clean, `16d665e`) |
| [manifest.json](manifest.json) | Origins, sizes and hashes of the files here |

## Notes

- The unit tests ran at the end of the job from the worktree. By then it had
  one change made while the job ran (the tolerance of the budget check in
  `test_async.py`, committed with this folder); the code under test was
  `16d665e`'s.
- The run folder with every file (1.1 GB) stays on the cluster:
  `/cluster/medbow/gscratch/syome/github_repos/pod-callback-20261028/run-24929555`.
- The records contain cluster paths and process ids as provenance.
