# PODFoam observer: a local vision-language model looks at a running solver

`python_module.py` in this folder is an example module for PODFoam. At chosen
time steps it draws |U| and p, sends the pictures or the step's numbers to a
vision-language model on the same machine (llama-server), and saves the answer with
the arrays. Model output is recorded and never goes back into the solver.

## How it fits into the solver

PODFoam calls two optional functions of the case's `python_module.py`, besides
`snapshot_func` and `svd_func`:

- `mesh_func(centres, volumes, solution_d, rank, poly_points, poly_offsets,
  poly_cells[, slice_plane])`, once at start-up, if `analysis_func` exists.
- `analysis_func(state)`, after every completed step.

`state` is a dictionary with these keys:

- `schema_version`, `time_s`, `delta_t_s`, `end_time_s`, `step`, `cells`.
- `residuals`: for `Ux`, `Uy`, `Uz` and `p`, this step's `initial_first`,
  `initial_last`, `final_last`, `linear_solves` and `iterations_total`. Empty
  directions are left out, and so is U without the momentum predictor.
- `courant`: `mean`, `max` and `phase`, recomputed from the completed step's `phi`.
- `continuity`: `local`, `global`, `cumulative` and `phase`.
- `p_cells`, `u_cells`: kinematic pressure and velocity of all cells.

All arrays are copies, so Python never sees solver memory. The return value of
`analysis_func` is ignored. An exception in either function gives a warning and
the run goes on.

**Parallel runs.** The master rank gathers the mesh, U and p in rank order and alone
calls the two functions, which every rank's module must define or none. `snapshot_func`
and `svd_func` stay per rank. This example takes them from
`validation/python_module.py`, which refuses other ranks, so a parallel run needs a
copy without that check. The callback forks from the master rank, in the process that
holds MPI, for requests, frame renders and telemetry. Not every MPI stack supports fork.

**3D meshes.** A 2D case passes one polygon per cell from its first `empty` patch.
A 3D mesh has none, so `PythonSlice.H` cuts it with the plane z = `POD_SLICE_Z` and
passes one polygon per cut cell, plus `slice_plane`. A plane through mesh points is
moved off them, which the solver log says. If nothing can be cut, the solver keeps
running and v2 requests are refused.

**POD schedule.** With `podSvdInterval` at its default of 0, a module without these
functions keeps the original schedule: a write step runs the SVD instead of
collecting a snapshot, if snapshots have been collected since the last SVD. A module
with `analysis_func` gets a snapshot at every step and an SVD at write steps, or every
`podSvdInterval` snapshots if that is set.

## Pictures and requests

`LLM_IMAGE_STYLE` chooses the pictures:

- `v1`: one 640x360 PNG with |U| above p. A 3D case gets a nearest-cell raster of
  all cells.
- `v2`: one 1024x576 PNG per field, with axes in percent of the plotted range, a
  grid line every 10 % and a colour bar labelled at five values. A 3D case shows its
  slice cells.

`LLM_MODE` chooses the request:

| Mode | Sent | Reply fields |
|---|---|---|
| `observe` | The step's numbers and the v1 picture | `observations`, `possible_interpretation`, `checks` |
| `describe` | Step, time, plotted ranges and the pictures of one step | `flow_description`, `fastest_flow_x_percent`, `fastest_flow_y_percent`, `lowest_pressure_x_percent`, `lowest_pressure_y_percent`, `uncertainties` |
| `sequence` | Steps, times and the pictures of 2 to 6 steps (v2: 2 or 3) | `change_description`, `max_speed_trend`, `min_pressure_trend`, `fastest_flow_region`, `uncertainties` |

**Synchronous or asynchronous.** By default the solver waits for the reply or the
deadline. With `LLM_ASYNC=1` the request step forks a worker and returns, and each
later step polls it without blocking. A request beyond `LLM_ASYNC_MAX_PENDING` is
skipped and logged. At the last step a pending request is waited for until its
deadline (`LLM_ASYNC_END=wait`) or left running (`detach`).

**One request or every N steps.** `observe` and `describe` send one request at
`LLM_ANALYSIS_STEP`. `sequence` captures frames at `LLM_SEQUENCE_STEPS` and sends
them at the last of those steps. `LLM_ANALYSIS_EVERY=N` (`describe` with v2 only)
sends a request at `LLM_ANALYSIS_STEP` and every N steps after it.

**What stops a request.** At `LLM_CALLBACK_DEADLINE_S` the worker is killed with
SIGKILL, by the waiting callback or by a later step's poll. `LLM_CONNECT_TIMEOUT_S`
and `LLM_READ_TIMEOUT_S` bound the connection and each read. The client accepts only
local endpoints. A failure is recorded and the solver goes on.

**What is refused.** These runs exit 0, send no request and say why in
`llm_errors.jsonl` or `llm_result.json`:

- `LLM_IMAGE_STYLE=v2` with `LLM_MODE=observe`, the default mode.
- `LLM_MAX_TOKENS` other than 320 with v2.
- A rerun in a case folder that already holds a v2 frame of that step.
- A 2D case outside the x-y plane with v2.

## Quick start

You need Python 3.10 to 3.12 with numpy and matplotlib, and scipy for v1 pictures of
3D cases. The solver links to this Python, and the scripts and commands below use it:

```bash
export PYTHON=<python>                                 # default of the scripts: python3 on PATH
export PATH=$(dirname "$PYTHON"):$PATH
export LD_LIBRARY_PATH=$(dirname "$PYTHON")/../lib:$LD_LIBRARY_PATH   # if not the system Python
```

The top-level README's TensorFlow 2.1 environment is a different one: on Python 3.6 the
requirements do not install and the callback records an error. Commands
start in `Solver_Examples/PODFoam`.

**Unit tests**, with no OpenFOAM and no model:

```bash
cd llm_demo
python3 -m pip install -r requirements.txt
python3 -m unittest test_llm_client test_callback test_async
```

**The observer with no model.** Source your OpenFOAM bashrc, build and validate, and
run a copy of the validated case with requests off.

```bash
./validation/run_v2106.sh                 # ends with PASS: <run>
case=<run>/observer; mkdir $case
cp -r <run>/fixed-pod/{0,constant,system} $case/
cp llm_demo/{python_module,bounded_ipc,llm_client,pod_image,readable_image,readable_request}.py $case/
cp validation/python_module.py $case/pod_svd.py
LLM_ENABLED=0 LLM_MODE=describe LLM_IMAGE_STYLE=v2 <run>/bin/PODFoam -case $case > $case/log.PODFoam
ls $case/llm_observation/step-000005      # U.png p.png fields.npz readable-metadata.json
```

**CPU with Gemma 4 E2B.** This needs a passed validation run, a few GB of RAM and
about 5.5 GB of disk: 3.4 GB of downloads, then 1.6 GB, 229 MB and 103 MB for the
asynchronous suite, the synchronous suite and the validation. On 8 CPUs the synchronous
suite took about 2 minutes and the asynchronous one 15 to 25. The model's own licence
terms apply; see its page, which `runtime_manifest.json` names.

```bash
./llm_demo/setup_runtime.sh               # model, projector, llama.cpp b11429; checks SHA-256
python3 llm_demo/runtime.py start         # later runs reuse the server
python3 llm_demo/runtime.py standalone    # optional: one request with a synthetic plot
./llm_demo/run_demo.sh                    # five synchronous cases, then verify_demo.py
POD_SUITE=async ./llm_demo/run_demo.sh    # five asynchronous cases, then verify_async.py
python3 llm_demo/runtime.py stop
```

The prebuilt `llama-server` needs GLIBCXX_3.4.30, as on Ubuntu 22.04. On an older system
`setup_runtime.sh` stops with that message: put a newer libstdc++ on `LD_LIBRARY_PATH`
or run in an image with one, then run it again; it reuses the downloads.

**Other OpenFOAM versions.** The scripts take the version and the bashrc of an OpenFOAM
already sourced, and use v2106 with none sourced. To choose, set both variables:

```bash
export OPENFOAM_BASHRC=/opt/openfoam8/etc/bashrc POD_OPENFOAM_VERSION=8
```

Use one `POD_WORKSPACE` per version, or delete `llm-demo-work` in the workspace first.
`run_demo.sh` builds there, and a build left by another version stopped it (seen going
from v2106 to v2212; `log.build` in its run folder says `No rule to make target`).

**GPU.** For Gemma 4 12B on a Slurm GPU node see [hpc/README.md](hpc/README.md).

## Settings

All are environment variables.

| Variable | Default and meaning |
|---|---|
| `LLM_MODE`, `LLM_IMAGE_STYLE` | `observe`, `v1` |
| `LLM_ENABLED`, `LLM_IMAGE_INPUT` | Both `1`; `LLM_ENABLED=0` draws and records but sends nothing, `LLM_IMAGE_INPUT=0` sends numbers only (`observe`) |
| `LLM_IMAGE_XRANGE`, `LLM_IMAGE_YRANGE` | Plotted `low,high` in metres; whole domain |
| `POD_SLICE_Z` | Slice plane, read by the solver; middle of the z range |
| `LLM_ANALYSIS_STEP`, `LLM_ANALYSIS_EVERY` | Request step, `5`; steps between requests, unset |
| `LLM_SEQUENCE_STEPS`, `LLM_SEQUENCE_PROMPT` | Frame steps, such as `250,750,1250`; `own`, or for v2 `t` states the answer key's thresholds, `tn` also each time's extrema |
| `LLM_ASYNC`, `LLM_ASYNC_MAX_PENDING`, `LLM_ASYNC_END` | `0`, or `1`; `1`, up to 8; `wait`, or `detach` |
| `LLM_FINAL_STEP` | Step the callback treats as the last, instead of the end time; the solver goes on, and later steps get no telemetry line; unset |
| `LLM_ENDPOINT`, `LLM_MODEL` | Port 8088 on 127.0.0.1; `gemma-4-E2B-it-Q4_0-vision` |
| `LLM_MAX_TOKENS` | Reply limit, from 32: 192 for `observe`, else 320, and these are the most; v2 sends 320; `run_demo.sh` sets 192 except for the asynchronous suite with v2 |
| `LLM_CALLBACK_DEADLINE_S`, `LLM_TIMEOUT_S` | Deadline, 120 s, up to 300 s; the first wins |
| `LLM_CONNECT_TIMEOUT_S`, `LLM_READ_TIMEOUT_S`, `LLM_KILL_JOIN_S` | HTTP timeouts, 2 s, 90 s; time to reap a killed worker, 0.1 s |
| `LLM_RUN_ID`, `MPLCONFIGDIR` | Run name, case folder; matplotlib cache, `mpl-cache` in the case |
| `LLM_HTTP_PYTHON` | The running Python; client's isolated worker, not used by the callback |
| `OPENFOAM_BASHRC`, `POD_OPENFOAM_VERSION` | Bashrc and the version it reports; the sourced OpenFOAM's, else v2106 |
| `PYTHON` | Interpreter the solver links to; `python3` on `PATH` |
| `POD_WORKSPACE`, `POD_REFERENCE_RUN` | Where runs go, parent of the checkout; reference case, newest passed validation |
| `POD_LLM_RUNTIME`, `POD_LLM_PORT`, `POD_LLM_STATE` | Model files, `llm-runtime` beside the checkout; 8088; folder of `server.pid` for `hpc/start_server.sh` and `stop_server.sh`, the runtime folder (leave it unset with `runtime.py`) |
| `POD_SUITE`, `POD_GIT_RECORDS` | `sync` or `async`; git records for `pack_run.py` where git is missing |
| `LLM_LONG_STEPS`, `LLM_LONG_DT`, `LLM_LONG_WRITE`, `LLM_LONG_STEP`, `LLM_LONG_SEQUENCE_STEPS` | Asynchronous suite: 3000, 5e-7, 250, 250, `250,750,1250` |
| `LLM_LONG_CASES`, `LLM_LONG_START`, `LLM_LONG_FIXTURE_DEADLINE_S` | Its cases, all (a subset runs no checks and no archive, and ends with `Cases finished, not checked`); start state, t = 0; deadline of the failure cases, 4 s |
| `SIF`, `POD_HOST_MODULES`, `POD_ASYNC_OUT`, `HF_TOKEN`, `LLAMA_CUDA`, `GEMMA_12B_REVISION`, `CMAKE_CUDA_ARCHITECTURES`, `BUILD_JOBS`, `LLM_MODEL_FILE`, `LLM_PROJECTOR_FILE`, `LLM_CTX`, `LLM_BATCH`, `LLM_UBATCH`, `LLM_PARALLEL`, `LLM_THREADS`, `LLM_GPU_LAYERS`, `LLM_IMAGE_TOKENS`, `LLM_IMAGE_MIN_TOKENS` | GPU path, see `hpc/README.md` |
| `WM_PROJECT_VERSION`, `WM_PROJECT_DIR`, `SLURM_JOB_ID`, `SLURM_SUBMIT_DIR` | From OpenFOAM or Slurm; read only |
| `FOAM_USER_APPBIN`, `LD_LIBRARY_PATH` | The scripts point the first at the run or the workspace, so your own application folder is not written; for the second see Quick start |

## Outputs

In the case folder:

- `telemetry.jsonl`: one line per step, without the arrays. It appears complete at
  the last step; a `.tmp` left behind means it did not complete.
- `llm_request.json`, `llm_request_body.json`: readable record, exact HTTP body.
- `llm_http_response.raw`, `llm_response.json`, `llm_result.json`: raw reply, parsed
  reply, status with answer and timings.
- `llm_errors.jsonl`: the callback's own errors.
- `llm_observation/`: v1 `state.png`, `fields.npz`, `image-metadata.json`, and earlier
  sequence frames in `step-NNNNNN/`.
- `llm_observation/step-NNNNNN/`: v2 `U.png`, `p.png`, `fields.npz`,
  `readable-metadata.json` (written last).
- `llm_requests/`: with `LLM_ANALYSIS_EVERY`, a `step-NNNNNN/` folder per request and
  `index.json`.
- `python_svd_audit.npz`: snapshots and modes of the last SVD, from `pod_svd.py`.

`run_demo.sh` puts the cases in `pod-llm-demo.XXXXXX/` or `pod-llm-async.XXXXXX/` in
the workspace, with `timings.json`, the verification JSON, `summary.json` and
`run-archive.tar.gz` (sources, records, requests and replies, written fields and
`python_svd_audit.npz`, no weights; about 54 MB for the synchronous suite and 600 MB
for the asynchronous one).

## Checks

`verify_demo.py` checks five synchronous cases: model off, numbers and picture,
numbers only, connection refused, stalled server. The telemetry must match the solver
log, the callback must keep its deadline, and all written field files, 45 in a passing
run, must equal the model-off case. The picture's arrays must equal the written fields,
and the request body must carry that PNG. It expects the request at step 5, so another
`LLM_ANALYSIS_STEP` makes it fail.

`verify_async.py` checks five asynchronous cases. Every written field must equal the
baseline's, the request step must take under 0.5 s, and each reply or error must be
recorded with its arrival step. A v2 request body must equal the builder's output for
the frame on disk, byte for byte. Scores are reported, not asserted.

The unit tests are 83 tests.

## Limits

- Only positions and fixed-vocabulary words can be scored. The free text is not
  checked.
- Gemma 4 E2B does not give usable answers. Over the fork's picture tests it placed
  67 of 388 positions within 10 % of the plotted range and got 140 of 306 trend words
  right, fewer than one constant answer (176 and 195).
- Versions: the build, the bridge validation and the observer with no model (2D and
  3D, serial and 2 ranks) passed on v2012, v2106, v2212 and 8. Those observer runs used a
  developed start state, an extruded 3D case and, on 2 ranks, a `pod_svd.py` without the
  rank check, which are not in this tree. The commands above ran from the tree alone, on
  all four versions, serial and 2D.
- OpenFOAM 8 gives other fields than the openfoam.com versions in the same case (largest
  |dU| 3.11 of 37.2 m/s and |dp| 23.2 of 379 at step 100 against v2212, whose frames equal
  v2012's and v2106's). The cause was not examined, so compare results within one version.
- Runs with a model: both suites with E2B on a CPU on v2106; the asynchronous suite with
  12B on a GPU on v2212, 1000 steps from a developed state; one 12B describe request on
  each of v2012, v2106, v2212 and 8, all of them wrong by more than 10 % of the plotted range. No
  suite with a model ran on v2012 or 8. Both suites passed on all four against a stand-in
  server with a fixed reply, which reads no picture.
- Parallel runs were tested on 2 ranks only, with no model request.
- No model has read a slice picture. The only 3D mesh tested is an extruded
  hexahedral one.
- On OpenFOAM 8 two reporting limits apply (`PythonCompat.H`). A field whose solves
  stop during a run through `maxIter 0` goes on reporting its last list. With
  `moveMeshOuterCorrectors`, only the last outer corrector's solves are listed.

The experiment scripts and reports are in the fork
https://github.com/seungminyome/PythonFOAM and on its results page
https://seungminyome.github.io/PythonFOAM/.
