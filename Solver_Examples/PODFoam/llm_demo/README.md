# PODFoam with a local vision-language model looking over its shoulder

At one time step PODFoam hands a small open-source vision-language model
(Gemma 4 E2B, Q4_0, served by llama.cpp on localhost, CPU only) a numeric
summary of the step and a picture of that step's |U| and p fields, gets a
short structured answer back, and carries on. The model only looks: nothing
it returns reaches U, p or any solver setting, and if the server is dead or
slow the solver gets control back within a fixed deadline.

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
python3 -m unittest test_llm_client test_callback -v
```

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
of final U and p against the no-request run: 0). Rendering took 0.4 s inside
the worker. Of the 70 s for the image request, 58 s went into prompt
processing and 11 s into generating 92 tokens. The server used about 2.3 GiB
PSS.

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
quarters of the way along, not "central", and 0.25 m is off by 0.25 m. The
remark about a strong pressure gradient next to the fast region does match
the fields (minimum p is in the same cell as maximum |U|). In an earlier run
with the same code the model put the maximum "near the right edge", so the
spatial wording changes from run to run while the region is roughly right.

What this shows is that numbers and a picture can be sent from inside the
solver, a structured answer comes back, and a dead or slow server does not
stall the run. Whether a 2B-class model reads the picture well enough to be
useful is an open question; one answer per run is not enough to say. The
minute or so per image request on CPU, mostly prompt processing, is a real
cost of this setup.

## Not covered

MPI runs (callback disabled), the 3D raster fallback on a real 3D case,
larger models (the 12B QAT variant has not been tried on this 7.7 GiB
machine), long runs, and anything about the quality of the analysis.
