# PODFoam callback to a local vision-language model

At a chosen time step, PODFoam sends a numerical summary and an image of its
velocity and pressure fields to Gemma 4 E2B. PythonFOAM provides the callback;
llama.cpp serves the model locally on the CPU. The callback saves a structured
reply, then returns control to the solver. Model output does not change U, p,
solver settings or control algorithms.

The callback is synchronous: the solver waits for the reply or the deadline.
Results are in the [October 17 report](../../../docs/results.md).

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

`verify_demo.py` checks that the residuals, Courant numbers and continuity
values in the telemetry match the solver log, that the callback returned before
step 6 and within its deadline plus cleanup allowance, and that all 45 saved
field files are identical to the baseline.

For image cases, it also checks that `fields.npz` matches `5e-07/U` and `p`,
that the PNG matches the image encoded in the request, and that the request
text matches the saved summary. It prints `PASS` when all checks pass.
`pack_run.py` then packs sources, run records, requests and replies into
`run-archive.tar.gz`, without intermediate time steps. The complete October 17
run is a [release asset](../../../docs/evidence/2026-10-17/README.md#complete-run).

Unit tests (no model needed):

```bash
cd Solver_Examples/PODFoam/llm_demo
python3 -m unittest test_llm_client test_callback test_ablation_runner -v
```

## Replaying a saved state with and without the image

The two live requests in the demo use different prompts, so they cannot tell
you what the image adds. `ablation_runner.py` takes one saved step and sends
two requests that differ only in the PNG:

| Condition | Question and numerical summary | PNG |
|---|---|---|
| `numeric_only` | Same frozen text | Omitted |
| `numeric_plus_image` | Same frozen text | Included |

Same instructions, model, seed and sampling settings within a pair. Both
conditions get the image ranges and domain extents from the summary. The true
maximum-speed location is computed from the saved arrays and used only for
scoring. Before building requests the runner checks that the PNG, its metadata,
the arrays and the summary belong together.

Prepare the requests from the published October 17 snapshot without talking
to a server (run from `llm_demo`):

```bash
python3 ablation_runner.py \
  --case ../../../docs/evidence/2026-10-17/pod-llm-demo.LRfJBN/fixed-pod \
  --output /tmp/pod-ablation-preview \
  --repeats 3 --seed 20261017
```

Use a fresh output directory each time. Any run's `fixed-pod` directory works
as `--case`. With the server up, send the three pairs:

```bash
python3 ablation_runner.py \
  --case ../../../docs/evidence/2026-10-17/pod-llm-demo.LRfJBN/fixed-pod \
  --output /tmp/pod-ablation-measured \
  --repeats 3 --seed 20261017 --timeout-s 120 --execute
```

The October 17 [manifest](../../../docs/evidence/2026-10-17/ablation/manifest.json)
records the original requests and order (seeds 20261017, 20261018, 20261019;
the runner alternates which condition goes first). Keep the server build,
weights, projector, thread count and context size fixed between runs and note
them with `--server-note`.

Each request saves its body, reply, hashes, status and metrics:

- **Location:** an x-only answer gets an x-axis error; two axes give a
  projected distance; all three give a 3D distance. Missing or ambiguous
  coordinates remain unscored. The summary includes scoring coverage.
- **Claim checks:** a few rules look for misquoted numbers and unsupported
  assertions. They miss a lot; the October 17
  [answer review](../../../docs/evidence/2026-10-17/independent-ablation-review.json)
  lists what they missed, so read the answers too.
- **Time:** `replay_callback_wall_s` covers sending a prepared request,
  waiting, evaluating and saving the result. HTTP/client wait is also logged
  separately. The replay does not rerun the solver, SVD or image rendering.
  If a matching solver log is present, `original_cpp_callback_wall_s` records
  that earlier callback time separately.

Replays test the model, not the solver hookup. For that, run the five-case
demo and `verify_demo.py`.

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
