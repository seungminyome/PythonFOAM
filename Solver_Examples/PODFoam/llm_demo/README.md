# PODFoam callback to a local vision-language model

At a chosen time step, PODFoam sends a numerical summary and an image of its
velocity and pressure fields to Gemma 4 E2B. PythonFOAM provides the callback;
llama.cpp serves the model locally on the CPU. The callback saves a structured
reply, then returns control to the solver. Model output does not change U, p,
solver settings or control algorithms.

The callback is synchronous: the solver waits for a reply or timeout.
The [October 17 report](../../../docs/results.md) covers the latest five-case
solver test and the separate comparison with and without an image.

This extends the stock PODFoam example with an optional callback. Modules that
only define `snapshot_func` and `svd_func` keep working as before.

## How it fits into the solver

```
PythonCreate.H   startup    mesh_func(centres, volumes, solutionD, rank, cell polygons)   optional, once
PythonComm.H     each step  snapshot_func(U), svd_func(rank) at the SVD interval           as before
PythonAnalysis.H each step  analysis_func(state)                                           optional
```

`state` holds the step's time, dt, residuals from `solverPerformanceDict`
(first/last initial residual, final residual, solve and iteration counts for
Ux, Uy, p), Courant and continuity values recomputed from the completed
step's `phi`, and `p_cells`, a copy of the kinematic pressure. U of the same
step already arrived through `snapshot_func`. All arrays are copies; Python
never sees solver storage directly. The callback runs on rank 0 and is
disabled for MPI runs.

`llm_demo/python_module.py` is the callback. At one chosen step (default 5)
it forks a worker that:

1. Writes the telemetry and computes a componentwise SVD summary of the
   snapshots collected so far.
2. Renders `llm_observation/state.png` (640×360, |U| on top, p below). For 2D
   cases, the C++ side passes faces of the `empty` patch, so each cell is
   drawn as a polygon without interpolation. The underlying arrays go to
   `fields.npz`, and their SHA-256 goes into the PNG metadata.
3. POSTs the summary and PNG data URL to `/v1/chat/completions`. The response
   schema requires three string fields: `observations`,
   `possible_interpretation`, and `checks`.
4. Records the request, exact HTTP body, raw response and timings.

The parent waits on a length-framed pipe with an absolute deadline
(`LLM_CALLBACK_DEADLINE_S`, default 120 s), kills the worker if it is late,
and does no I/O of its own. Another short-lived child writes the final result
files with a 0.2 s budget. The HTTP client accepts local loopback endpoints,
limits request and response sizes, and has separate connect,
read-inactivity and whole-call timeouts.

Rendering needs matplotlib; the 3D fallback (nearest-cell raster) also needs
scipy. matplotlib is imported once at startup inside `mesh_func`, not in the
time loop.

## Running it

You need OpenFOAM v2106, Python 3 with numpy and matplotlib, a passed
[bridge validation](../validation/README.md) run (it provides the reference
case), about 3.4 GB of disk for the model files and a few GB of RAM for the
server.

```bash
cd Solver_Examples/PODFoam
./llm_demo/setup_runtime.sh            # downloads model, projector, llama.cpp b11429; checks SHA-256
python3 llm_demo/runtime.py start      # loads the model once; later runs reuse it
python3 llm_demo/runtime.py standalone # optional: one request with a synthetic plot
./llm_demo/run_demo.sh                 # builds PODFoam, runs the cases, verifies
python3 llm_demo/runtime.py stop       # when the server is no longer needed
```

Environment variables: `OPENFOAM_BASHRC`, `PYTHON`, `POD_WORKSPACE`,
`POD_LLM_RUNTIME` (model directory, default `../llm-runtime` beside the
checkout), `POD_LLM_PORT` (8088), `POD_REFERENCE_RUN` (newest passed
validation run by default), `LLM_ANALYSIS_STEP`, `LLM_IMAGE_INPUT` (1/0),
`LLM_CALLBACK_DEADLINE_S`, `LLM_CONNECT_TIMEOUT_S`, `LLM_READ_TIMEOUT_S`,
`LLM_MAX_TOKENS` (up to 192).

`run_demo.sh` builds the solver into `llm-demo-work/bin/` in the workspace,
creates `pod-llm-demo.XXXXXX` and runs five cases, each for ten steps:

| Case | Model request | Image | Expected result |
|---|---|---|---|
| `fixed-pod-no-llm` | Off | Rendered, not sent | Baseline fields |
| `fixed-pod` | On | Sent | `ok` |
| `fixed-pod-text-only` | On | Not sent | `ok` |
| `fixed-pod-server-error` | To a closed port | Sent | `error`, 4 s deadline |
| `fixed-pod-timeout` | To a trickling fixture | Sent | `timeout`, 4 s deadline |

`verify_demo.py` checks that residuals, Courant numbers and continuity values
in the telemetry match the solver log; that the callback returned before
step 6 and within its deadline plus cleanup allowance; and that all 45 saved
field files match the baseline byte for byte.

For image cases, it also checks that `fields.npz` matches `5e-07/U` and `p`,
that the PNG matches the image encoded in the request, and that the request
text matches the saved summary. It prints `PASS` when all checks pass.
`pack_run.py` then saves sources, run records, requests and responses in
`run-archive.tar.gz`. This archive omits intermediate time steps; the
[October 17 download guide](../../../docs/evidence/2026-10-17/README.md#download-the-complete-run)
links to that test's complete solver archive.

Unit tests (no model needed):

```bash
cd Solver_Examples/PODFoam/llm_demo
python3 -m unittest test_llm_client test_callback test_ablation_runner -v
```

## Controlled replay benchmark

`ablation_runner.py` compares two requests made from one saved step:

| Condition | Question and numerical summary | PNG |
|---|---|---|
| `numeric_only` | Same frozen text | Omitted |
| `numeric_plus_image` | Same frozen text | Included |

Within each pair, the requests have the same instructions, model, seed and
generation settings. Only the image content part differs. Both receive the
image ranges and domain extents recorded in the numerical summary. Reference
coordinates come from the saved arrays and are used only for scoring.
The runner checks the PNG, metadata, arrays and summary before preparing
requests.

From `llm_demo`, this example prepares requests from the published October 17
snapshot without contacting a server:

```bash
python3 ablation_runner.py \
  --case ../../../docs/evidence/2026-10-17/pod-llm-demo.LRfJBN/fixed-pod \
  --output /tmp/pod-ablation-preview \
  --repeats 3 --seed 20261017
```

Use a new output directory each time. You can also pass a saved run's
`fixed-pod` directory as `--case`. With the local server running, this example
sends the three pairs:

```bash
python3 ablation_runner.py \
  --case ../../../docs/evidence/2026-10-17/pod-llm-demo.LRfJBN/fixed-pod \
  --output /tmp/pod-ablation-measured \
  --repeats 3 --seed 20261017 --timeout-s 120 --execute
```

These are rerun examples. The [recorded manifest](../../../docs/evidence/2026-10-17/ablation/manifest.json)
lists the original requests and their execution order: pair 1 used seed
`20261017`, followed by `20261018` and `20261019`. The runner alternates
which condition goes first. Keep the server build, model weights, projector,
thread count and context size fixed, and record them with `--server-note`.

Each trial saves requests, responses, hashes, status and metrics:

- **Location:** an x-only answer gets an x-axis error; two axes give a
  projected distance; all three give a 3D distance. Missing or ambiguous
  coordinates remain unscored. The summary includes scoring coverage.
- **Grounding:** automatic rules check selected numerical claims and
  unsupported assertions. Keep their output alongside a review of the
  answers; the October 17 [response review](../../../docs/evidence/2026-10-17/independent-ablation-review.json)
  records claims these rules missed.
- **Time:** `replay_callback_wall_s` covers sending a prepared request,
  waiting, evaluating and saving the result. HTTP/client wait is also logged
  separately. The replay does not rerun the solver, SVD or image rendering.
  If a matching solver log is present, `original_cpp_callback_wall_s` records
  that earlier callback time separately.

See the report's [limitations](../../../docs/results.md#limitations) when
comparing errors, repeated answers and timings. To check the callback in
OpenFOAM itself, run the five-case demo and `verify_demo.py`; replay and unit
tests exercise different parts of the system.

## Earlier run (October 13)

`pod-llm-demo.SwwR2e` (solver revision `9ae54d0`) is described in the
[October 13 report](../../../docs/results-20261013.md) with its
[evidence](../../../docs/evidence/2026-10-13/README.md). Its image and
numbers-only requests used different instructions, so that run does not
isolate the effect of the image; the October 17 replay does.

## SVD summary

Both request types include a componentwise SVD summary of the velocity
snapshots collected so far: singular values and their fractions, no spatial
modes. `leading_energy_fraction` is sigma_1 squared over the sum of squared
singular values, the leading pattern's share of the snapshot matrix (about
99.997% for Ux in the recorded runs). The matrices are uncentered and
unweighted. This is a data summary, not a physical energy or an accuracy
measure, and whether it helps the model has not been tested.

The normal worker deadline is 120 s. The deliberate failure cases use 4 s with
a 4.27 s acceptance limit that includes cleanup.
