# PODFoam observer: a local vision-language model looks at a running solver

`python_module.py` in this folder is an example module for PODFoam. At chosen time
steps it draws |U| and p. It sends the pictures or the step's numbers to a
vision-language model, which is a language model that also reads images. The model
runs on the same machine in llama-server, the HTTP server of llama.cpp. The module
records each answer with the arrays. Model output never goes back into the solver.

## How it fits into the solver

The module implements PODFoam's two optional hooks, `mesh_func` and `analysis_func`.
[HOOKS.md](../HOOKS.md) describes their arguments, the keys of `state`, parallel runs,
3D slices and the POD schedule. The hooks change neither U nor p. Because this module
defines `analysis_func`, the POD step collects a snapshot at every time step. What is
particular to this example:

- `snapshot_func` and `svd_func` are taken from `validation/python_module.py`. That
  module refuses ranks other than 0, so a parallel run needs a copy without the check.
- In `observe` mode, and in `describe` with v1 pictures, the request carries an SVD
  summary of every snapshot the run collected up to the request. The module checks
  that this window holds `state["snapshot_count"]` snapshots, the count the solver
  reports.
- For requests, frame renders and telemetry, the callback forks from the master rank,
  in the process that holds MPI. Not every MPI stack supports fork.
- On a 3D mesh whose slice plane cuts nothing, the solver keeps running and v2
  requests are refused.

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
| `sequence` | Steps, times and the pictures of 2 to 6 steps, or of 2 or 3 steps with v2 | `change_description`, `max_speed_trend`, `min_pressure_trend`, `fastest_flow_region`, `uncertainties` |

**Synchronous or asynchronous.** By default the solver waits for the reply or the
deadline. With `LLM_ASYNC=1` the request step forks a worker and returns, and each
later step polls it without blocking. A request beyond `LLM_ASYNC_MAX_PENDING` is
skipped and logged. At the last step, `LLM_ASYNC_END=wait` waits for a pending request
until its deadline, and `LLM_ASYNC_END=detach` leaves it running.

**One request or every N steps.** `observe` and `describe` send one request at
`LLM_ANALYSIS_STEP`. `sequence` captures frames at `LLM_SEQUENCE_STEPS` and sends them
at the last of those steps. `LLM_ANALYSIS_EVERY=N` works only with `describe` and v2
pictures. It sends a request at `LLM_ANALYSIS_STEP` and every N steps after it.

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

You need Python 3.10 to 3.12 with numpy, matplotlib and scipy. scipy draws the
nearest-cell raster for a mesh that passes no cell polygons, as in the unit tests and
in v1 pictures of 3D cases. The solver links to this Python, and the scripts and
commands below use it:

```bash
export PYTHON=<python>                                 # default of the scripts: python3 on PATH
export PATH=$(dirname "$PYTHON"):$PATH
export LD_LIBRARY_PATH=$(dirname "$PYTHON")/../lib:$LD_LIBRARY_PATH   # if not the system Python
```

The unit tests ran on Python 3.10 and 3.12, and the solver runs of this example on
Python 3.11. The top-level README's TensorFlow 2.1 environment does not work here. On
Python 3.6 the requirements do not install, and the callback records an error. The
commands start in `Solver_Examples/PODFoam`.

**Unit tests**, with no OpenFOAM and no model:

```bash
cd llm_demo
python3 -m pip install -r requirements.txt
python3 -m unittest test_llm_client test_callback test_async
cd ..
```

**The observer with no model requests.** Source your OpenFOAM bashrc, build and
validate, and run a copy of the validated case with requests off.

```bash
./validation/run.sh                       # ends with PASS: <run>
case=<run>/observer; mkdir $case
cp -r <run>/fixed-pod/{0,constant,system} $case/
cp llm_demo/{python_module,bounded_ipc,llm_client,pod_image,readable_image,readable_request}.py $case/
cp validation/python_module.py $case/pod_svd.py
LLM_ENABLED=0 LLM_MODE=describe LLM_IMAGE_STYLE=v2 <run>/bin/PODFoam -case $case > $case/log.PODFoam
ls $case/llm_observation/step-000005      # U.png p.png fields.npz readable-metadata.json
```

**CPU with Gemma 4 E2B.** Gemma 4 is a family of open-weight models from Google, and
E2B is a small one that runs on a CPU. This path needs a passed validation run and a
few GB of RAM. Disk use and the times on 8 CPUs:

| Part | Disk | Time on 8 CPUs |
|---|---|---|
| Downloads, with llama.cpp unpacked | 3.5 GB | |
| Asynchronous suite | 1.8 GB | 15 to 28 minutes |
| Synchronous suite | 381 MB | 2 to 4 minutes |
| Validation run | 100 MB | |
| Total | about 5.8 GB | |

The model's own licence terms apply. Its page is named in `runtime_manifest.json`.

```bash
./llm_demo/setup_runtime.sh               # model, projector, llama.cpp b11429; checks SHA-256
python3 llm_demo/runtime.py start         # later runs reuse the server
python3 llm_demo/runtime.py health        # optional: the server's /health reply
python3 llm_demo/runtime.py standalone    # optional: one request with a synthetic plot
./llm_demo/run_demo.sh                    # five synchronous cases, then verify_demo.py
POD_SUITE=async ./llm_demo/run_demo.sh    # five asynchronous cases, then verify_async.py
python3 llm_demo/runtime.py stop
```

The prebuilt `llama-server` needs GLIBCXX_3.4.30, which Ubuntu 22.04 has. On an older
system `setup_runtime.sh` stops with that message. Put a newer libstdc++ on
`LD_LIBRARY_PATH`, or run in an image that has one, and run the script again. It
reuses the downloads.

**Other OpenFOAM versions.** The scripts use the OpenFOAM that is already sourced, and
v2106 when none is. To choose a version, set both variables:

```bash
export OPENFOAM_BASHRC=/opt/openfoam8/etc/bashrc POD_OPENFOAM_VERSION=8
```

Use one `POD_WORKSPACE` per version, or delete `llm-demo-work` in the workspace first.
`run_demo.sh` builds there, and a build left by another version stopped it when going
from v2106 to v2212. `log.build` in its run folder said `No rule to make target`.

**GPU.** For Gemma 4 12B on a Slurm GPU node see [hpc/README.md](hpc/README.md).

## Settings

All are environment variables.

| Variable | Default and meaning |
|---|---|
| `LLM_MODE`, `LLM_IMAGE_STYLE` | `observe`, `v1` |
| `LLM_ENABLED`, `LLM_IMAGE_INPUT` | Both `1`. `LLM_ENABLED=0` draws and records but sends nothing; `LLM_IMAGE_INPUT=0` sends numbers only, in `observe` mode |
| `LLM_IMAGE_XRANGE`, `LLM_IMAGE_YRANGE` | Plotted `low,high` in metres; whole domain |
| `POD_SLICE_Z` | Slice plane, read by the solver; middle of the z range |
| `LLM_ANALYSIS_STEP`, `LLM_ANALYSIS_EVERY` | Request step, `5`; steps between requests, unset. Both count OpenFOAM time indices, `state["step"]`, which a restart continues |
| `LLM_SEQUENCE_STEPS`, `LLM_SEQUENCE_PROMPT` | Frame steps as time indices, such as `250,750,1250`; prompt `own`, or for v2 `t`, which states the answer key's thresholds, and `tn`, which also states each time's extrema |
| `LLM_ASYNC`, `LLM_ASYNC_MAX_PENDING`, `LLM_ASYNC_END` | `0`, or `1`; `1`, up to 8; `wait`, or `detach` |
| `LLM_FINAL_STEP` | Time index the callback treats as the last, instead of the end time; the solver goes on, and later steps get no telemetry line; unset |
| `LLM_ENDPOINT`, `LLM_MODEL` | Port 8088 on 127.0.0.1; `gemma-4-E2B-it-Q4_0-vision` |
| `LLM_MAX_TOKENS` | Reply limit, from 32 up to the default, which is 192 for `observe` and 320 otherwise. v2 sends 320. `run_demo.sh` sets 192 except for the asynchronous suite with v2 |
| `LLM_CALLBACK_DEADLINE_S`, `LLM_TIMEOUT_S` | Deadline, 120 s, up to 300 s; `LLM_TIMEOUT_S` counts only when `LLM_CALLBACK_DEADLINE_S` is unset |
| `LLM_CONNECT_TIMEOUT_S`, `LLM_READ_TIMEOUT_S`, `LLM_KILL_JOIN_S` | HTTP timeouts, 2 s, 90 s; time to reap a killed worker, 0.1 s |
| `LLM_RUN_ID`, `MPLCONFIGDIR` | Run name, case folder; matplotlib cache, `mpl-cache` in the case |
| `LLM_HTTP_PYTHON` | Python of the client's isolated worker, by default the running Python; the callback does not use it |
| `OPENFOAM_BASHRC`, `POD_OPENFOAM_VERSION` | Bashrc and the version it reports; the sourced OpenFOAM's, else v2106 |
| `PYTHON` | Interpreter the solver links to; `python3` on `PATH` |
| `POD_WORKSPACE`, `POD_REFERENCE_RUN` | Where runs go, parent of the checkout; reference run, the newest passed validation run in `validation/runs/` or the workspace |
| `POD_LLM_RUNTIME`, `POD_LLM_PORT`, `POD_LLM_STATE` | Model files, `llm-runtime` beside the checkout; 8088; folder of `server.pid` for `hpc/start_server.sh` and `stop_server.sh`, the runtime folder; leave it unset with `runtime.py` |
| `POD_SUITE`, `POD_GIT_RECORDS` | `sync` or `async`; git records for `pack_run.py` where git is missing |
| `LLM_LONG_STEPS`, `LLM_LONG_DT`, `LLM_LONG_WRITE`, `LLM_LONG_STEP`, `LLM_LONG_SEQUENCE_STEPS` | Asynchronous suite: 3000, 5e-7, 250, 250, `250,750,1250` |
| `LLM_LONG_CASES`, `LLM_LONG_START`, `LLM_LONG_FIXTURE_DEADLINE_S` | Its cases, all; a subset runs no checks, makes no archive and ends with `Cases finished, not checked`; start state, t = 0; deadline of the failure cases, 4 s |
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
- `llm_observation/step-NNNNNN/`: v2 `U.png`, `p.png`, `fields.npz` and
  `readable-metadata.json`, which is written last.
- `llm_requests/`: with `LLM_ANALYSIS_EVERY`, a `step-NNNNNN/` folder per request and
  `index.json`.
- `python_svd_audit.npz`: snapshots and modes of the last SVD, from `pod_svd.py`.

`run_demo.sh` puts the cases in `pod-llm-demo.XXXXXX/` or `pod-llm-async.XXXXXX/` in
the workspace, with `timings.json`, the verification JSON, `summary.json` and
`run-archive.tar.gz`. The archive holds the sources, records, requests and replies,
the written fields and `python_svd_audit.npz`, but no weights. It is about 97 MB for
the synchronous suite and 640 MB for the asynchronous one.

## Checks

`verify_demo.py` checks five synchronous cases: no model requests, numbers and
picture, numbers only, connection refused, stalled server. The telemetry must match
the solver log, and the callback must keep its deadline. All written field files must
equal those of the same run with no model requests. A passing run has 45 of them. The
picture's arrays must equal the written fields, and the request body must carry that
PNG. The script expects the request at step 5, so another `LLM_ANALYSIS_STEP` makes
it fail.

`verify_async.py` checks five asynchronous cases. Every written field must equal that
of the run with no model requests. The request step must take under 0.5 s. Each reply
or error must be recorded with the step at which it arrived. A v2 request body must
equal the builder's output for the frame on disk, byte for byte. Scores are reported,
not asserted.

There are 85 unit tests.

## Limits

- Only positions and fixed-vocabulary words can be scored; the free text is not
  checked.
- Gemma 4 E2B does not give usable answers: in the author's picture tests it was right
  less often than a constant baseline, which gives one fixed answer every time.
- Results from OpenFOAM 8 and from the openfoam.com versions differ in the same case,
  so compare results within one version.
- Some runs under "Versions and runs" used a developed start state, an extruded 3D
  case or, on 2 ranks, a `pod_svd.py` without the rank check. These are not in this
  tree.
- The commands above ran in order with this code on v2106, serial and in 2D, the
  suites with Gemma 4 E2B.
- No observer run used more than 2 ranks.
- The only 3D mesh tested is an extruded hexahedral one.
- On OpenFOAM 8, `residuals` can hold an earlier time step's list for a field, or only
  the last outer corrector's solves. [HOOKS.md](../HOOKS.md) gives the conditions.

### Picture tests

| Test | Gemma 4 model | Right | Constant baseline |
|---|---|---:|---:|
| Positions within 10 % of the plotted range | E2B | 67 of 388 | 176 |
| Trend words | E2B | 140 of 306 | 195 |
| Fastest flow, 24 solver frames | 12B | 21 | 24 |
| Fastest flow, 48 random windows | 12B | 39 | 11 |
| Fastest flow, all 72 slice pictures | 12B | 60 | 27 |
| Lowest pressure, 24 solver frames | 12B | 24 | 24 |
| Lowest pressure, 48 random windows | 12B | 47 | 8 |
| Lowest pressure, all 72 slice pictures | 12B | 71 | 29 |

The observer drew 24 slice frames of the extruded 3D case in the solver. Another 48
pictures, in random windows, were drawn afterwards from those frames' slice arrays
with the same renderer. 12B read all of them outside the solver.

On the solver frames the constant baseline was right every time and beat 12B on the
fastest flow. The model's lead over the baseline comes from the random windows. The
baseline takes the best single answer for each set: the solver frames, the random
windows and all 72 pictures, so the rows of the two parts do not add up to the totals.

This test shows that the slice path works. It does not show that the model reads flow
that varies in z, because the four slices barely differ. On the solver frames their
answer-key positions of the fastest flow and the lowest pressure are the same at five
of the six steps and at most 1.8 % of the plotted range apart at step 250.

### Versions and runs

Every run below passed its checks. These ran with this code:

| Run | Versions |
|---|---|
| Build of every commit, bridge validation | v2012, v2106, v2212, 8 |
| The commands above, both suites with E2B on a CPU | v2106 |
| Asynchronous suite, 12B on a GPU, 1000 steps from a developed state | v2212 |
| A 12B request from a 2-rank run of the 2D case, sent from rank 0 only | v2212 |
| The 3D case with no model requests, serial | v2212, 8 |

An earlier version of this example ran these on October 30 and November 1:

| Run | Versions |
|---|---|
| Runs with no model requests, 2D and 3D, serial and on 2 ranks | all four |
| Both suites, a stand-in server with a fixed reply that reads no picture | all four |
| Asynchronous suite, 12B on a GPU, 1000 steps from a developed state | v2012, v2212, 8 |
| Asynchronous suite, 12B on a GPU, the 6000-step default | v2212 |
| A 12B request from a 2-rank run of the 2D case, sent from rank 0 only | v2212, 8 |

With that earlier version, one 12B `describe` request on each of the four versions
was wrong by more than 10 % of the plotted range.

### Why OpenFOAM 8 differs

OpenFOAM 8 applies the `relaxationFactors` of `Run_Case`, `p 0.9` and `U 0.9`, with
one outer corrector. The openfoam.com versions look only for `pFinal` and `UFinal`
there and do not apply them. The frames of v2012 and v2106 equal those of v2212.

| At step 100 | U, m/s | p, m²/s² |
|---|---|---|
| Largest difference, OpenFOAM 8 against v2212 | 3.11 | 23.2 |
| The same, OpenFOAM 8 without that block | within 0.0001 | within 0.0005 |
| v2212: peak speed and range of p | 37.2 | 379 |

Records of the author's runs: https://github.com/seungminyome/PythonFOAM (`docs/`).
