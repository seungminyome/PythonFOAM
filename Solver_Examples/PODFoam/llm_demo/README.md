# PODFoam in-situ observer/logger

At one time step PODFoam hands a small open-source vision-language model
(Gemma 4 E2B, Q4_0, served by llama.cpp on localhost, CPU only) a numeric
summary of the step and a picture of that step's |U| and p fields, gets a
short structured answer back, and carries on. This is a PythonFOAM callback-based
in-situ observer/logger: model output is recorded without changing U, p, solver
settings or control algorithms.
The saved connection-refusal and delayed-response tests returned control
to the solver within the tested deadline and cleanup allowance.

This is the stock PODFoam example plus an optional callback. Modules that only
define `snapshot_func` and `svd_func` keep working as before.

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
it forks a worker that

1. writes the telemetry so far and computes a componentwise SVD summary of
   the snapshots so far,
2. renders `llm_observation/state.png` (640x360, |U| on top, p below). For 2D
   cases the C++ side passes the faces of the `empty` patch, so every cell is
   painted as its own polygon, no interpolation. The arrays behind the
   picture go to `fields.npz` and their SHA-256 into the PNG metadata,
3. POSTs the summary and the PNG (data URL) to `/v1/chat/completions` with a
   JSON schema that forces three string fields: `observations`,
   `possible_interpretation`, `checks`,
4. records the request, the exact HTTP body, the raw response and timings.

The parent waits on a length-framed pipe with an absolute deadline
(`LLM_CALLBACK_DEADLINE_S`, default 120 s), kills the worker if it is late,
and does no I/O of its own; the final result files are written by another
short-lived child with a 0.2 s budget. The HTTP client only talks to
`http://127.0.0.1`, caps request and response sizes, and has separate
connect, read-inactivity and whole-call timeouts.

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
creates `pod-llm-demo.XXXXXX` and runs five cases, each the full ten steps:

| case | model request | image | expected |
|---|---|---|---|
| `fixed-pod-no-llm` | off | rendered, not sent | baseline fields |
| `fixed-pod` | on | sent | `ok` |
| `fixed-pod-text-only` | on | not sent | `ok` |
| `fixed-pod-server-error` | to a closed port | sent | `error`, 4 s deadline |
| `fixed-pod-timeout` | to a trickling fixture | sent | `timeout`, 4 s deadline |

`verify_demo.py` then checks, for every case, that the residuals in the
telemetry equal the solver log, Courant/continuity equal the log, the
callback returned before step 6, the C++-measured callback time is within
deadline plus cleanup budget, and all 45 written field files are
byte-identical to the baseline. For the image cases it also checks that
`fields.npz` equals the stored `5e-07/U` and `p`, that the PNG's hash matches
the base64 payload in the sent body, and that the JSON text in the body
equals the recorded summary. It prints `PASS` only if everything holds.
`pack_run.py` then packs sources, run records, the exact request and the raw
response into `run-archive.tar.gz` (no weights).

Unit tests (no model needed):

```bash
cd Solver_Examples/PODFoam/llm_demo
python3 -m unittest test_llm_client test_callback test_ablation_runner -v
```

## Controlled replay benchmark

`ablation_runner.py` prepares a controlled comparison from one saved step:

| Condition | Question and numeric summary | PNG |
|---|---|---|
| `numeric_only` | Same frozen text | Omitted |
| `numeric_plus_image` | Same frozen text | Included |

Both requests use the same system instructions, model, seed and generation
settings. The request bodies differ only by the image content part. Image
ranges and domain extents present in the summary remain available to both
conditions; quoting the supplied maximum speed is not a visual-reasoning score.
The saved arrays provide reference coordinates for scoring, not extra answers
for the model. The runner verifies that the PNG, metadata, arrays and summary
belong to the same saved state before preparing requests.

From this directory, prepare requests without contacting a server:

```bash
python3 ablation_runner.py \
  --case ../../../docs/evidence \
  --output /tmp/pod-ablation-preview
```

Use a new output directory for each run. The complete saved run's `fixed-pod`
case directory can also be used as `--case`. To execute three paired repeats
against an already running local model server:

```bash
python3 ablation_runner.py \
  --case ../../../docs/evidence \
  --output /tmp/pod-ablation-measured \
  --repeats 3 --seed 20261016 --timeout-s 120 --execute
```

The paired order alternates to reduce a fixed first-request advantage. A seed
is a recorded request setting, not a promise of identical server behavior.
Keep the server build, weights, projector, thread count and context size fixed
and record them alongside a real benchmark. Repeats of one state do not replace
testing multiple states. Cold start, prompt caching and other work on the
machine can still affect timings.

The output keeps the exact requests, responses, hashes, status and per-trial
metrics. Review these distinctions when interpreting the results:

- **Localization:** explicitly stated coordinates are compared with the
  maximum-speed cell center in `fields.npz`. An x-only answer produces an
  x-axis error. Two axes give a projected error; all three are needed for a
  3D distance. Missing, ambiguous or unparseable coordinates remain unavailable,
  never zero. Check how many responses could be scored before comparing errors.
- **Grounding:** automatic rules flag contradictions and claims lacking the
  available evidence. They do not settle whether every sentence is true or
  whether the model used the image. Unflagged responses still need human review.
- **Latency:** replay callback time and HTTP/client wait time are logged
  separately. Replay uses an already computed summary and image; it does not
  measure the live C++ callback, SVD, rendering or solver execution. Failed and
  timed-out requests retain their status and must not be counted as successful
  responses when summarizing latency or localization. When a matching saved
  solver log is available, the manifest also includes
  `original_cpp_callback_wall_s` with its source. This is historical context,
  not a new A/B measurement.

No new CFD or model-quality result is implied by this script. To check a
backport in the actual solver, separately run the existing five-case demo and
`verify_demo.py`, including the 45-file baseline comparison. Unit tests cover
Python failure paths and fixture responses; they do not replace that solver
integration check.

## One run on this machine

8 vCPU, 7.7 GiB RAM, no GPU, llama.cpp b11429 with 4 threads, context 2048.
Callback times are what the C++ side measured around `analysis_func`.

| case | status | callback | HTTP | request | prompt tokens |
|---|---|---:|---:|---:|---:|
| no request | disabled | 0.8 s | - | - | - |
| numbers + image | ok | 70.6 s | 70.1 s | 50.5 KB | 1516 |
| numbers only | ok | 41.4 s | 41.4 s | 3.7 KB | 1062 |
| connection refused | error | 0.4 s | - | - | - |
| trickling server | timeout | 4.0 s | - | - | - |

All five runs completed ten steps and wrote identical fields (max difference
of final U and p against the no-request run: 0). This establishes unchanged saved
outputs in these runs, not a general numerical-stability result. Rendering took 0.4 s inside
the worker. Of the 70 s for the image request, 58 s went into prompt
processing and 11 s into generating 92 tokens. The recorded image-run server peak PSS was about 2.22 GiB.
These are measurements from one run, not repeated performance statistics.

Answers at step 5 (t = 5e-7 s), as returned:

numbers + image

> observations: The velocity magnitude |U| shows a high value near x=0.25 m, with a maximum of 82.5 m/s.
> possible_interpretation: The flow exhibits a localized high-speed region in the central x-domain.
> checks: The pressure field shows a significant pressure gradient near the high-velocity region.

numbers only

> observations: Residuals show small values, e.g., p final last is 9.19188e-07. Courant mean is 0.000337189.
> possible_interpretation: The simulation appears to be progressing with small residuals. Velocity SVD shows high leading energy fractions.
> checks: Check if linear-solver residuals are physical force balance. Verify velocity SVD centering.

Checked against the stored fields: every number the model quotes is in the
JSON it was given and is quoted correctly (82.5 m/s, 9.19e-07, Courant mean
3.4e-4, leading energy fractions above 0.9999). The spatial part is weaker.
The maximum |U| sits at the step corner, x = 0.0005 m, y = 0.013 m; the
picture spans x from -1.55 m to 0.60 m, so the corner is about three
quarters of the way along, not "central", and 0.25 m is off by 0.25 m. The minimum-p and maximum-|U| cells are close but distinct: zero-based
cell indices 10409 and 12090, respectively. Their proximity does not by
itself validate the model's claim of a strong pressure gradient. No
quantitative gradient evaluation was performed for that claim. An earlier
answer used different spatial wording; this is not evidence of reliable
localization.

What this shows is that numbers and a picture can be sent from inside the
solver, a structured answer comes back, and the tested connection-refusal and delayed-response cases
returned to the solver. Whether this E2B model reads the picture well enough to be
useful is an open question; one answer per run is not enough to say. The
minute or so per image request on CPU, mostly prompt processing, is a real
cost of this setup.

The image and numeric-only requests used different instructions and extra
numeric metadata, so this comparison does not isolate the effect of the image.
The maximum-speed value was supplied in text as well as being represented in
the image. Correctly quoting it is not proof of visual reasoning. The
numeric-only answer also asked to check force balance and SVD centering,
although the input already stated that residuals are not force balance and
that the SVD was uncentered.

SVD means **Singular Value Decomposition**. The legacy JSON key
`leading_energy_fraction` is retained for compatibility. Its value is
sigma_1 squared divided by the sum of squared singular values: a dominant
pattern's share of the numeric snapshot table. For Ux in this saved run it is
about 99.997%. It is not AI accuracy, a physical-stability test, or a measured
kinetic-energy fraction. The component matrices are uncentered and have no
cell-volume or density weighting.

The callback is synchronous: the solver waits for the response or timeout.
The normal worker deadline was 120 s; the deliberate timeout test used 4 s
with a 4.27 s overall acceptance limit. The latter is a recovery test, not
a four-second successful model response or a universal real-time guarantee.

See the [run report](../../../docs/results.md),
[saved evidence](../../../docs/evidence/README.md), and
[Korean illustrated guide](https://seungminyome.github.io/PythonFOAM/guide.ko.html).

## Not covered

MPI runs (callback disabled), the 3D raster fallback on a real 3D case,
larger models (the 12B QAT variant has not been tried on this 7.7 GiB
machine), long runs, and anything about the quality of the analysis.
