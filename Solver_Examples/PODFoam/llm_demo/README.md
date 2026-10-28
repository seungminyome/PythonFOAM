# PODFoam callback to a local vision-language model

At a chosen time step, PODFoam sends a numerical summary and an image of its
velocity and pressure fields to Gemma 4 E2B. PythonFOAM provides the callback;
llama.cpp serves the model locally on the CPU. The callback saves a structured
reply, then returns control to the solver. Model output does not change U, p,
solver settings or control algorithms.

The callback can be synchronous (the solver waits for the reply or the
deadline; the October 17 measurements) or asynchronous (`LLM_ASYNC=1`: the
solver keeps stepping and the reply is recorded when it arrives). Three
request modes exist: `observe` (numbers plus the same-step image, the original),
`describe` (one image, a description and the positions of the extrema) and
`sequence` (several images along the run, how the flow changes).
Results: [October 17 report](../../../docs/results.md),
[October 20 report](../../../docs/results-20261020.md),
[12B paired replay](../../../docs/results.md#same-replay-with-gemma-4-12b-on-a-gpu-2026-10-19),
[October 22 picture test](../../../docs/results-20261022.md),
[October 22 v2 pictures from the running solver](../../../docs/results-20261022-live.md).

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
never sees solver storage directly. In a parallel run the mesh and the
fields are gathered to the master rank (`PythonGather.H`, cells in rank
order) and only the master calls `mesh_func` and `analysis_func`; the POD
snapshot and SVD stay per rank as before. Tested on 2 ranks on 2026-10-27
([report](../../../docs/results-20261027.md#mpi-and-the-pod-files)).

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
time loop. `LLM_IMAGE_XRANGE="x0,x1"` (and `LLM_IMAGE_YRANGE`) plot only that
window in metres; the colour range then spans the cells inside the window and
the request says which range was plotted.

## Request modes

| `LLM_MODE` | Sent | Asked for | Reply fields |
|---|---|---|---|
| `observe` (default) | numeric summary (+ image) | observations | `observations`, `possible_interpretation`, `checks` |
| `describe` | step, time, plotted ranges + one image | describe the snapshot; where are the fastest flow and the lowest pressure, as percent of the plotted x and y ranges | `flow_description`, `fastest_flow_x_percent`, `fastest_flow_y_percent`, `lowest_pressure_x_percent`, `lowest_pressure_y_percent`, `uncertainties` |
| `sequence` | steps and times + 2 to 6 images in time order | how the flow changes from the first image to the last | `change_description`, `max_speed_trend`, `min_pressure_trend`, `fastest_flow_region`, `uncertainties` |

In `describe` mode the text carries no field values and no positions: the
extrema have to be read from the picture and its colour bars. In `sequence`
mode frames are captured at `LLM_SEQUENCE_STEPS` (for example `250,750,1250`)
by a forked renderer at each of those steps, and one request with all frames
goes out at the last one. The earlier frames go to `llm_observation/step-XXXXXX/`;
the frame of the last step is `llm_observation/` itself. The trend words are a
fixed vocabulary (peak speed `increasing`, `decreasing`, `roughly_constant`,
`cannot_tell`; pressure minimum `more_negative`, `less_negative`,
`roughly_constant`, `cannot_tell`; fastest spot `same_place`, `moves`,
`cannot_tell`) so that answers can be scored against the saved arrays.
The reply schema is enforced by the server (`response_format`, JSON schema
with integer ranges and enums) and checked again by the client.

## Asynchronous requests

With `LLM_ASYNC=1` the request step only forks the worker and returns (a few
milliseconds). Every later step polls the worker's pipe without blocking; when
the reply arrives it is written with `arrived_at_step`, and a `response_after`
marker goes to the solver log. A worker that passes its deadline is killed by
the same polling. At most `LLM_ASYNC_MAX_PENDING` requests are in flight
(default 1); a request that would exceed it is skipped and logged. At the last
step (the solver passes `end_time_s`; `LLM_FINAL_STEP` overrides) a request
that is still pending is waited for until its own deadline
(`LLM_ASYNC_END=wait`, default) or left running (`LLM_ASYNC_END=detach`; the
worker then still writes `llm_response.json` by itself).

`POD_SUITE=async ./llm_demo/run_demo.sh` runs the five asynchronous cases on a
longer run (`LLM_LONG_STEPS`, default 3000 steps of `LLM_LONG_DT` = 5e-7 s,
fields and SVD modes written every `LLM_LONG_WRITE` = 250 steps, request at
`LLM_LONG_STEP` = 250, sequence frames at `LLM_LONG_SEQUENCE_STEPS` =
250,750,1250) and checks them with `verify_async.py`:

| Case | Mode | Model request | Expected |
|---|---|---|---|
| `async-no-llm` | sequence | Off (frames rendered) | baseline fields and frames |
| `async-describe` | describe | On | `ok`, reply arrives while the solver runs |
| `async-sequence` | sequence | On | `ok`, three frames in one request |
| `async-server-error` | describe | closed port | `error`, found by polling |
| `async-timeout` | describe | trickling fixture | `timeout`, killed by polling |

`verify_async.py` checks that every written time directory is identical to
the baseline, that the frames' arrays equal the written fields and the
baseline's frames, that the request step took under 0.5 s, that every step
other than the request, arrival and last steps took under 1 s, and that the
reply (or error) was recorded with its arrival step. For the sequence case it
also checks the image hashes in the request body. `LLM_LONG_CASES=async-no-llm`
runs only the baseline, which is a way to capture frames without a model
request; the llama-server must still be running with the model loaded,
because the runner checks it before the first case.

## v2 pictures from the solver (`LLM_IMAGE_STYLE=v2`)

`LLM_IMAGE_STYLE=v2` makes `describe` and `sequence` requests send the
pictures of the 2026-10-22 picture-reading test instead of `state.png`: one
1024×576 PNG per field (|U|, then p), both axes in percent of the plotted
range with a grid line every 10 %, a colour bar labelled at five values
(`readable_image.py`). The default is `v1`, which keeps the solver's
behaviour of 2026-10-13 to 2026-10-20 byte for byte. `observe` always sends
the v1 picture; `observe` with v2 is refused.

- Every v2 frame is a folder `llm_observation/step-NNNNNN/` with
  `fields.npz`, `U.png`, `p.png` and `readable-metadata.json`, written last;
  the request step's frame too. A folder that is already there (a rerun in the
  same case folder; step numbers restart with each solver process) is never
  overwritten and never sent: the capture or the request is refused instead.
- The request is built by `readable_request.py`, the same functions the
  picture test uses: `describe_v2_payload` and, for sequences,
  `sequence_v2_payload` with each image on its own colour scale (the v2own
  prompt). A v2 sequence takes two or three steps (six images at most). The
  requests always carry `max_tokens` 320, seed 20261021 and
  `cache_prompt: false`; `LLM_MAX_TOKENS` must then be unset or 320.
  `test_picture_test.GoldenV2RequestTests` pins the bytes of the published
  2026-10-22 requests, and `verify_async.py` checks that each live body equals
  the builder applied to the frame on disk, byte for byte.
- A v2 describe request sends no SVD summary, so the callback keeps no
  snapshot window and computes none; the request step can be late in a long
  run without the worker slowing down.
- The plotted range is `LLM_IMAGE_XRANGE`/`LLM_IMAGE_YRANGE` or the whole
  domain. v2 needs a 2D case in the x-y plane with one polygon per cell (no
  raster fallback).
- Use a server context of 4096 tokens and batch/ubatch 512, as in the
  picture test: a three-time v2 sequence has about 2,200 prompt tokens.

`LLM_KILL_JOIN_S` (default 0.1 s since 2026-10-27, before 0.02 s; up to 2 s) is how long a killed worker
may take to be reaped. Reaping takes longer the more memory the child maps:
about 16 ms for 200 MB and 38 ms for 500 MB on the MedicineBow nodes, where a
worker forked from a 0.5 GB solver is not reaped within 0.02 s; there the
jobs use 0.2 s.

### Starting from a developed flow

`LLM_LONG_START=<time directory>` makes every case of the asynchronous suite
start from that state of an earlier run on the same mesh (the mesh files are
compared by hash) instead of t = 0: its fields are copied, `uniform/` is left
out so the time index restarts, and the end time is the start time plus
`LLM_LONG_STEPS` × `LLM_LONG_DT`. Step numbers in the callback count from the
start. `LLM_LONG_FIXTURE_DEADLINE_S` (default 4) is the callback deadline of
the refused and stalled cases. For such runs `verify_async.py` also checks
that the start files are the recorded ones in every case and that the Courant
number stays below 1.

### Several describe requests in one study (`run_live_sweep.py`)

The suite sends one describe request, in one plotted window. With a fixed
window the answer is often in about the same place, so one fixed answer
scores well. `run_live_sweep.py <suite run> <PODFoam> <output>` runs, after a
v2 suite, one more case per request step R (every 500 steps by default), each
from the same start state, with a describe request at R in a window placed at
random around the fastest cell of the baseline's written state at R (the
rule of `window_test.py`). It checks that each answer arrived while the solver
kept stepping, that each request body is the tested builder applied to the
frame, and that each frame's arrays equal the baseline's written fields at R;
it scores the answers and the one fixed answer that would do best over all
of them (`sweep-summary.json`).

### A request every N steps (`LLM_ANALYSIS_EVERY`)

`LLM_ANALYSIS_EVERY=N` (describe with v2 pictures) sends a describe request
at `LLM_ANALYSIS_STEP` and every N steps after it, as long as fewer than
`LLM_ASYNC_MAX_PENDING` requests are pending; a step that finds the limit
reached is skipped and recorded. Each request writes the usual files
(`llm_request.json`, `llm_request_body.json`, `llm_response.json`,
`llm_result.json`, the raw reply) in its own `llm_requests/step-NNNNNN/`, and
the last step writes `llm_requests/index.json` (step, status, arrival step,
model time, solver stall). `run_periodic.py <suite run> <PODFoam> <output>`
runs such a case and its twin without requests from a v2 suite's baseline
staging, compares every written file, checks each body against the builder
and each frame against the written fields, scores the answers and records
wall time, memory (RSS and PSS of the solver tree, sampled every 0.5 s) and
the bytes each request moved over the worker pipe (`ipc_bytes_received` in
the result); `hpc/periodic_v2.slurm` runs it on a GPU node.

### Trend test on a developed flow (`sequence_test.py`)

`sequence_test.py build --states <case> --centres <fields.npz> --old-manifest
... --output <set>` takes triples of saved states (gaps of 2000, 4000 and
6000 steps by default), places one random window around the fastest cells of
each triple (the window rule above, every fastest cell inside the margin) and
keeps `--count` triples so that the nine (speed trend, pressure trend)
classes of the answer key are as evenly filled as the states allow. Five sets
of the same triples: `dev-sequence-v1` (the solver's two-panel pictures, the
2026-10-20 prompt), `dev-sequence-v2own` (one picture per field, each on its
own colour scale, the 2026-10-22 prompt), `dev-sequence-v2own-t` (the same
with the answer key's thresholds stated in the prompt: 2 % for the trends,
5 % of the plotted range for the spot), `dev-sequence-v2own-tn` (the same
plus each time's maximum |U| and minimum p from the arrays in the note) and
`dev-sequence-numbers` (that note and the fastest cell's position, no
pictures). `readable_request.sequence_v2_payload(..., thresholds=True,
numbers=..., images=False)` builds them; with the defaults it still gives the
2026-10-22 bodies byte for byte. `--dt` (here and in `window_test.py`) is
the time step the state names are divided by, for runs with another step;
`--y-span` sets the range of window heights in metres. Run on 2026-10-27
([report](../../../docs/results-20261027.md#reading-change-between-snapshots)).

### Random-window picture test (`window_test.py`)

`window_test.py build` draws saved states of a run (any time directories;
`--first-step`, `--describe-every`, `--last-step` in steps of 5e-7 s) several
times each, with the plotted window placed at random around the fastest cell:
the cell at least 15 % from every edge, at least 200 cells inside, a height
of 0.03 to 0.114 m and a width of 1.5 to 4 heights. It writes the
`flow-window-v1` and `flow-window-v2` sets; `check`, `run` and `report` work
as in `picture_test.py`, with the fixed-answer score taken as one answer for
the whole set. `hpc/window_test.slurm` runs a set on a GPU node.

## Replaying saved frames (describe and sequence)

`snapshot_runner.py` sends saved frames (directories with `state.png`,
`fields.npz`, `image-metadata.json`) through the describe or sequence prompt
and scores the answers against the arrays:

```bash
python3 snapshot_runner.py --mode describe --frames RUN/async-no-llm/llm_observation/step-000250 \
    RUN/async-no-llm/llm_observation/step-000750 RUN/async-no-llm/llm_observation \
    --output /tmp/describe-replay --repeats 3 --execute
python3 snapshot_runner.py --mode sequence --frames RUN/async-no-llm/llm_observation/step-000250 \
    RUN/async-no-llm/llm_observation/step-000750 RUN/async-no-llm/llm_observation \
    --output /tmp/sequence-replay --repeats 3 --execute
```

`RUN` is a `pod-llm-async.XXXXXX` folder. With the published frames
(`docs/evidence/2026-10-20/pod-llm-async.pp7agC` for the whole domain, and
`pod-llm-async.8YC6bG` with `step-000250`, `step-001250` and `llm_observation`
for the window) the commands rebuild all 24 October 20 replay requests byte
for byte (defaults: seed 20261020 for the first repeat and one more for each
further repeat, `--max-tokens` 320). Without `--execute`
they only prepare the requests and the reference values.

For `describe` the score is the distance between the answered percent position
and the true cell of the maximum speed (and the minimum pressure) inside the
plotted window, in percent of the plotted ranges and in metres. For `sequence`
the answered trend words are compared with the trends of the saved extrema
(relative change above 2 % counts as a trend; the fastest spot "moves" when
its position changes by more than 5 % of the plotted range). Reference values
are written to `ground_truth.private.json` and never sent to the model.

## Picture-reading test (several models, two picture styles)

`picture_test.py` builds a fixed set of requests about saved pictures, sends
it to one server and scores the answers against a key the model does not
see. The pictures come in two styles: v1 as the callback draws them
(`pod_image.py`) and v2 drawn by `readable_image.py` (one field per picture,
axes in percent with a grid line every 10 %, colour bar labelled with five
values from the minimum to the maximum). `foam_fields.py` reads the saved
OpenFOAM states (ASCII only).

```bash
# from the repository root; --states is a PODFoam case run without model requests
# (the arguments of the 2026-10-21 set, 308 requests; without --sequence no flow-sequence sets)
python3 Solver_Examples/PODFoam/llm_demo/picture_test.py build --states <case> \
    --centres docs/evidence/2026-10-20/pod-llm-async.pp7agC/async-no-llm/llm_observation/step-000250/fields.npz \
    --oct17 docs/evidence/2026-10-17/ablation --oct20 docs/evidence/2026-10-20/replay \
    --describe-every 500 --last-step 6000 \
    --sequence 250,750,1250 --sequence 250,1250,2750 --sequence 1250,2250,3250 \
    --sequence 2250,3250,4250 --sequence 3250,4250,5250 --sequence 4500,5250,6000 \
    --sequence 5000,5500,6000 --output <test set>             # matplotlib needed
cd Solver_Examples/PODFoam/llm_demo
python3 picture_test.py check --test-set <test set>        # every request and the key against the manifest
python3 picture_test.py run --test-set <test set> --model <alias> --endpoint <url> --output <run folder>
python3 picture_test.py report <run folder> [<run folder> ...] --output report.md
```

The arguments of the 2026-10-21 build are recorded as `build_args` in its
[manifest](../../../docs/evidence/2026-10-22-picture-test/test-set/manifest.json).

The set of 2026-10-21, how it is built and the cluster job that ran it on
seven models are described in [hpc/README.md](hpc/README.md#picture-reading-test-run-2026-10-22);
the results are in the [October 22 report](../../../docs/results-20261022.md).

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
`LLM_MAX_TOKENS` (up to 192 for `observe`, 320 for the other modes), `LLM_MODE`, `LLM_ASYNC`, `LLM_SEQUENCE_STEPS`, `LLM_ASYNC_MAX_PENDING` (1 to 8), `LLM_ASYNC_END`, `LLM_FINAL_STEP`, `LLM_IMAGE_XRANGE`, `LLM_IMAGE_YRANGE`, `POD_SUITE` (`async` for the long asynchronous suite), and for that suite `LLM_LONG_STEPS`, `LLM_LONG_DT`, `LLM_LONG_WRITE`, `LLM_LONG_STEP`, `LLM_LONG_SEQUENCE_STEPS`, `LLM_LONG_CASES`.

`run_demo.sh` sets `LLM_MAX_TOKENS=192` for every mode unless it is already
set, so the October 20 in-solver describe and sequence requests used 192 (the
replays used 320). The runners set some variables per case. The synchronous
runner sets `LLM_ENABLED` and `LLM_IMAGE_INPUT` and passes `LLM_ANALYSIS_STEP`
through (default 5). The asynchronous runner sets `LLM_ENABLED`,
`LLM_IMAGE_INPUT` (always 1), `LLM_ASYNC`, `LLM_MODE`, `LLM_ANALYSIS_STEP`
(from `LLM_LONG_STEP`) and `LLM_SEQUENCE_STEPS` (from
`LLM_LONG_SEQUENCE_STEPS`) and ignores `LLM_FINAL_STEP`, so use the
`LLM_LONG_*` variables there.

`run_cases.py` checks that the server behind `LLM_ENDPOINT` is the process
recorded in `$POD_LLM_RUNTIME/server.pid`. If the server was started from a
different runtime directory, point `POD_LLM_RUNTIME` at that directory.

To repeat the measurements with Gemma 4 12B on a cluster GPU, see
[hpc/README.md](hpc/README.md). The paired replay has been run this way on an
NVIDIA A30 ([records](../../../docs/evidence/2026-10-19-12b/README.md)).

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
python3 -m unittest test_llm_client test_callback test_ablation_runner test_async -v
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
the runner alternates which condition goes first). The October 19 12B replay
used the same requests with only `model` changed. Keep the server build,
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

Observe requests (with and without the image) include a componentwise SVD
summary of the velocity snapshots collected so far: singular values and their
fractions, no spatial modes. Describe and sequence requests send no SVD
summary. `leading_energy_fraction` is sigma_1 squared over the sum of squared
singular values, the leading pattern's share of the snapshot matrix (99.997 %
for Ux at step 5 of the October 17 and 19 runs). The matrices are uncentered
and unweighted. This is a data summary, not a physical energy or an accuracy
measure, and whether it helps the model has not been tested.

The normal worker deadline is 120 s. The deliberate failure cases use 4 s with
a 4.27 s acceptance limit that includes cleanup.
