# PythonFOAM + Gemma 4 E2B: reading solver state during a run

[![tests](https://github.com/seungminyome/PythonFOAM/actions/workflows/tests.yml/badge.svg)](https://github.com/seungminyome/PythonFOAM/actions/workflows/tests.yml)
[![evidence](https://github.com/seungminyome/PythonFOAM/actions/workflows/evidence.yml/badge.svg)](https://github.com/seungminyome/PythonFOAM/actions/workflows/evidence.yml)
![OpenFOAM v2106](https://img.shields.io/badge/OpenFOAM-v2106-lightgrey)
![Python 3.10 | 3.12](https://img.shields.io/badge/python-3.10%20%7C%203.12-lightgrey)
[![license](https://img.shields.io/badge/license-Argonne%20OSS-blue.svg)](LICENSE)

[October 28](docs/results-20261028.md) · [October 27](docs/results-20261027.md) · [October 22, continued](docs/results-20261022-live.md) · [October 22 report](docs/results-20261022.md) · [October 20 report](docs/results-20261020.md) · [October 17 report](docs/results.md) · [Evidence](docs/evidence/README.md) · [How to run](Solver_Examples/PODFoam/llm_demo/README.md) · [Korean](https://github.com/seungminyome/PythonFOAM-Korean)

During a PODFoam run, a callback sends one step's numbers and a velocity/pressure
image, or several images from along the run, to a vision-language model served
by llama.cpp, stores the answer and lets the solver continue. The request can be
asynchronous: the solver keeps stepping and the answer is recorded when it
arrives. That much works. Nothing from the model goes back into the
computation. Gemma 4 E2B on the CPU, the original setup, gives answers that are
not usable. With the solver drawing pictures meant to be read (one field per
image, axes in percent with a grid; `LLM_IMAGE_STYLE=v2`) and Gemma 4 12B on a
GPU node, eleven requests from a running solver, each with its own plotted
window, placed the fastest flow within 10 % of the plotted range 9 times and
the lowest pressure 10 times, where one fixed answer would be right 4 times;
the written flow fields stayed identical to a run without requests
([October 22, continued](docs/results-20261022-live.md)). On October 27
([report](docs/results-20261027.md)), with one picture per field on its own
colour scale, 12B read whether the peak speed rose or fell in 29 of 30
sequences with a clear change, where with the solver's old pictures no model
did clearly better than one fixed answer; changes under 2 % are still
misread. A describe request every 250 steps over 24,000 steps cost 0.7 % of
run time on top of drawing the pictures, left every written file unchanged, and the answers followed the lowest-pressure spot as
it moved between vortex cores (89 of 96 within 10 %). The observer also runs on 2 MPI ranks.
On October 28 ([report](docs/results-20261028.md)) two requests ran side by
side (about 0.1 s of solver time per request), the callback's memory stopped
growing with the run, trend words are computed from the arrays, and 3D cases
are drawn through a plane slice. Shown three frames of a run about to crash,
the models said "unstable" only once the field had already blown up.

<img src="docs/evidence/2026-10-17/pod-llm-demo.LRfJBN/fixed-pod/llm_observation/state.png" width="640" alt="|U| and p at step 5, the image sent to the model">

*The image sent at step 5 of the October 17 run: |U| on top, kinematic pressure p below (640x360, one polygon per cell).*

## Quick start

Unit tests, no OpenFOAM or model needed (95 tests, about 50 s):

```bash
pip install -r Solver_Examples/PODFoam/llm_demo/requirements.txt
make test          # or: cd Solver_Examples/PODFoam/llm_demo && python3 -m unittest
make evidence      # every evidence file matches its manifest hash
```

Full run (OpenFOAM v2106, about 3.4 GB of disk for the model files, a few GB of RAM):

```bash
cd Solver_Examples/PODFoam
./validation/run_v2106.sh        # bridge check; its passed run is the reference case
./llm_demo/setup_runtime.sh      # Gemma 4 E2B Q4_0, image projector, llama.cpp b11429
python3 llm_demo/runtime.py start
./llm_demo/run_demo.sh           # builds PODFoam, runs the five cases, verifies
python3 llm_demo/runtime.py stop
```

Details and environment variables: [llm_demo/README.md](Solver_Examples/PODFoam/llm_demo/README.md).

## Implementation

```mermaid
sequenceDiagram
    participant S as PODFoam (C++)
    participant P as python_module.py
    participant W as worker process
    participant L as llama-server (Gemma 4 E2B)
    S->>P: analysis_func(state), after step 5
    P->>W: fork
    W->>W: numeric summary, state.png, fields.npz
    W->>L: POST /v1/chat/completions (JSON + PNG)
    L-->>W: three-field JSON reply
    W-->>P: result over pipe (deadline 120 s, else killed)
    P-->>S: return, steps 6 to 10 run as usual
```

- A Python callback added to PODFoam (OpenFOAM v2106; on October 22 also v2212
  in an Apptainer image on a GPU node). Right after a chosen
  time step it sends residuals, Courant number, continuity error, an SVD summary
  and a PNG of that step's |U| and p to a local llama.cpp server (Gemma 4 E2B
  Q4_0 with image projector) and stores the response. "Step 5" in this document
  is the fifth of the ten time steps (t = 5×10⁻⁷ s), the default; set
  `LLM_ANALYSIS_STEP` to change it.
- Three request modes (`LLM_MODE`): `observe` (numbers plus the image, the
  original), `describe` (one image; a description and the positions of the
  fastest flow and the lowest pressure as percent of the plotted ranges) and
  `sequence` (images captured at `LLM_SEQUENCE_STEPS`, sent together at the
  last one; how the flow changes, with fixed trend words). `LLM_IMAGE_XRANGE`
  plots a window of the domain instead of all of it.
- Synchronous by default: the solver waits for the reply or a deadline. With
  `LLM_ASYNC=1` the request step only forks the worker; every later step polls
  it without blocking, the reply is recorded with the step at which it
  arrived, a worker past its deadline is killed, and at most one request is in
  flight. At the last step a pending reply is waited for, or detached.
- If the server is absent or slow, the solver is never blocked beyond the
  deadline, in either mode.
- Verification scripts check that all steps completed, that every written
  field file is identical to a run without requests, that logs match the
  records, that the frames' arrays equal the written fields, and, for the
  synchronous image cases and the asynchronous sequence case, that the image
  hashes match the request body.
- `readable_image.py` draws one field per picture, axes in percent of the
  plotted range with a grid line every 10 % and the colour bar labelled with
  five values from the minimum to the maximum (v2). With `LLM_IMAGE_STYLE=v2`
  the callback draws these pictures for `describe` and `sequence` requests and
  builds the request with `readable_request.py`, the code the picture tests
  use; each live request body is checked to equal that builder applied to the
  frame on disk, byte for byte. The default is still the two-panel picture of
  `pod_image.py` (v1). `LLM_LONG_START` starts the asynchronous cases from a
  developed flow state; `run_live_sweep.py` adds describe requests at several
  steps, each with its own random window; `window_test.py` builds picture sets
  with random windows.
- `LLM_ANALYSIS_EVERY=N` sends a describe request every N steps (one in
  flight at most), each recorded in its own folder. In an MPI run the mesh
  and fields are gathered to the master rank, which alone calls the observer;
  the POD snapshot and SVD stay per rank. `sequence_test.py` builds trend sets
  from saved states, with the answer key's thresholds and the extrema in the
  prompt if asked.
- The October 17 measurements used revision `23089bb`; the October 20
  measurements used `9449085`, which added the modes, the asynchronous path
  and the plot window. The October 19 12B replay ran from `934da23`, whose
  request and scoring code equal `23089bb`. The October 22 picture test ran
  from `58e00d9`; the later October 22 runs from `354caf9` with uncommitted
  changes, published in `dee7731` with a review's fixes
  ([records](docs/results-20261022-live.md#records)). The October 27 runs used
  `6afbdeb` to `ab6b943` ([records](docs/results-20261027.md#records)).

## Measurements (2026-10-28, two in flight, telemetry, 3D slice, instability test)

- Two requests in flight (job 24929296, a request every 50 steps, two
  server slots): 118 of 120 answered, 112 sent while another was pending,
  2 skipped by the limit; 2,520 of 2,520 written files identical to the run
  without requests; +3.2 % wall time, about 0.1 s per request as with one in
  flight. One answered request's record was not written within the writer's
  0.2 s budget; the index now says so (`record_written`).
- Telemetry without a history (job 24929555): the Python heap over 24,000
  replayed states stays at most 0.52 MiB instead of 31.7 MiB, the last step
  takes 0.023 s instead of 0.699 s, and `telemetry.jsonl` is byte-identical.
- 3D slice (job 24929629): the step case extruded to 8 cells in z is cut at
  mid height; the 20,540 cut cells are drawn as polygons, the same on 2 ranks
  as serially (centres equal to 4.2×10⁻¹⁷ m), and 2D frames are unchanged.
- Instability test (jobs 24929533, 24929534): on 27 triples whose last frame
  is 1 to 10 steps before a crash and 27 from runs that ended, the four
  models were right on 30 to 33 of 54; a rule on the peak |U| growth gets
  33 and one on the cell-to-cell jump 38. Every model saw the triples ending
  one step before a crash, where the field has already blown up; none warned
  more than 5 steps ahead.

## Measurements (2026-10-27, reading change, requests every 250 steps, MPI)

Trend test: 45 three-time sequences of the developed flow, each with its own
random window; right answers for the peak-speed / lowest-pressure trend
(Slurm jobs 24903974 and 24903975):

| Model | Solver's v1 pictures | v2, own colour scale per picture | v2 + extrema in the note | Extrema only, no pictures |
|---|---:|---:|---:|---:|
| Gemma 4 12B | 14 / 15 | 32 / 28 | 33 / 28 | 32 / 28 |
| Gemma 4 26B-A4B | 16 / 19 | 31 / 36 | 33 / 33 | 36 / 37 |
| Gemma 4 31B | 18 / 20 | 32 / 33 | 37 / 41 | 35 / 42 |
| Qwen3.5-35B-A3B Q8_0 | 15 / 18 | 31 / 32 | 32 / 28 | 34 / 33 |
| One fixed answer | 15 / 20 | 15 / 20 | 15 / 20 | 15 / 20 |

Out of 45. On the 30 sequences whose peak speed changed by at least 2 %,
12B with v2 pictures was right in 29; most errors are changes under 2 %.
With the extrema in the note 31B read every clear speed change.

A describe request every 250 steps, 24,000 steps of 5×10⁻⁶ s from the
developed flow, Gemma 4 12B on an NVIDIA A30 (job 24903264): 96 of 96
answered, 2,016 of 2,016 written files identical to the same run without
requests (which drew the same pictures), 0.7 % more wall time per step, at
most 0.017 s in the callback at a request step (the last step waits for the
pending reply by design); lowest pressure within 10 % in 89 of 96 (one fixed answer 65),
and the answered position follows the lowest-pressure spot as it moves
between vortex cores (correlation 0.78 in x).

- 4-bit Qwen with the image-token setting llama.cpp recommends:
  Qwen3.5-35B-A3B and 27B placed the fastest flow of the developed flow in
  133 and 128 of 140 pictures, Gemma 4 106 to 113 (October 22).
- A cylinder flow (`offsetCylinder`, OpenFOAM-9 tutorial): the fastest flow
  in 32 to 39 of 40 pictures for 12B, 26B-A4B and 31B; the lowest pressure,
  a small spot beside a large dark wake, in 38 of 40 for 31B and 18 for 12B.
- Two repeats of the October 22 solver run on one A30 node gave identical
  answers to each other; against the first run on an RTX A6000 the request
  bodies were identical and the answers differed in text and in some
  positions, with the same counts within 10 %.
- MPI, 2 ranks: the frame has the same cells as the serial run's, centres
  equal to 4×10⁻¹⁷ m. The small POD mode-file differences of October 22 come
  from the BLAS thread count (identical with one thread).

## Measurements (2026-10-22, v2 pictures from the running solver)

PODFoam in OpenFOAM v2212 (Apptainer image) on a MedicineBow GPU node, Gemma 4
12B QAT on the node's NVIDIA RTX A6000 (Slurm job 24757460), v2 pictures. Every
case started from t = 0.1 s of a developed flow, with vortices rolling up
behind the step, and ran 6000 steps of 5×10⁻⁶ s.

| Run | Request at step | Reply recorded at step | Solver wait at the request step | Model wait | Files equal to baseline |
|---|---:|---:|---:|---:|---:|
| Describe one snapshot | 250 | 320 | 0.004 s | 3.17 s | 432 / 432 |
| Sequence of three snapshots | 3750 | 3823 | 0.004 s | 3.15 s | 432 / 432 |
| Connection refused | 250 | 261 | 0.004 s | 0.011 s | 432 / 432 |
| Server made to stall (4 s deadline) | 250 | 324 | 0.004 s | killed at the 4 s deadline | 432 / 432 |

The describe answer put the fastest flow 3.3 % and the lowest pressure 5.0 %
of the plotted range from the true cells. The sequence answer had the falling
peak speed and the moving fastest flow right and the pressure trend wrong.
Eleven more describe requests, at steps 500 to 5500 and each with its own
random window, all arrived while the solver ran (69 to 93 steps later), and
each body equalled the tested builder applied to the frame; 9 of 11
fastest-flow and 10 of 11 lowest-pressure answers were within 10 %, where one
fixed answer gets 4 and 4. In a shorter trial run the describe answer was 33 %
and 29 % off.

In the picture test repeated with the plotted window placed at random around
the fastest cell (one fixed answer: 7 to 10 of 48), 12B, 26B-A4B, 31B and
Qwen3.5-35B-A3B placed both extremes within 10 % in 45 to 48 of 48 v2
pictures for each of three window seeds, and in 2 to 17 of 48 with v1. In 35
states of the developed flow (one fixed answer: 16 and 17 of 140) they placed
the lowest pressure within 10 % in 130 to 139 of 140 v2 pictures and the
fastest flow in 106 to 121; most fastest-flow misses named another spot with
at least 90 % of the largest speed.

## Measurements (2026-10-22, picture-reading test on a GPU node)

The same 308 prepared requests, nearly all about pictures, sent to each of
seven Gemma 4 models in turn on one NVIDIA RTX A6000 (MedicineBow, Slurm job
24756981), llama.cpp b11429, temperature 0. No solver ran. v1 is the picture
the solver sends (two panels, axes in metres), v2 the new one (one field per
image, axes in percent with a grid line every 10 %). Synthetic: 32 pictures
with one bright |U| spot and one dark p spot. Planted: 32 pictures of 4 saved
states, each with a narrow |U| peak and p dip added. Right means within 10 %
of the plotted range.

| Model | Synthetic, fastest flow, v1 / v2 | Planted, fastest flow, v1 / v2 | Planted, lowest p, v1 / v2 | Median time per request |
|---|---:|---:|---:|---:|
| E2B Q4_0 (the solver's model; timed here on the GPU) | 4 / 11 | 2 / 10 | 3 / 6 | 1.01 s |
| E4B QAT | 9 / 15 | 4 / 15 | 4 / 5 | 1.31 s |
| 12B QAT | 9 / 32 | 5 / 32 | 9 / 25 | 2.86 s |
| 26B-A4B QAT | 17 / 32 | 15 / 31 | 5 / 20 | 2.18 s |
| 31B QAT | 18 / 32 | 17 / 32 | 9 / 24 | 6.33 s |
| One fixed answer | 5 | 6 | 6 | |

Out of 32. Every planted lowest-pressure miss of 12B, 26B-A4B and 31B named
the step corner, where the state without the dip has its own lowest pressure.
On 12 synthetic three-time sequences with a clear change, the same three
models called the peak-speed trend right in 12 of 12 when each image's colour
bar printed its own maximum, and in 5 to 10 when one colour scale was shared;
the 2 % threshold for "roughly constant" was not in the prompt, so the six
flat designs are not a fair test. In the saved flow without planted features
the extremes stay at the step corner and the trend words barely vary, so one
fixed answer already scores 24 of 24 positions; there, with numbers on the
colour bars, 26B-A4B and 31B read the pressure trend right in 11 and 12 of 14
sequences, 12B in 3. Two more E2B forms (BF16 projector, QAT weights) and the October 17
and 20 requests are in the [October 22 report](docs/results-20261022.md).

## Measurements (2026-10-20, asynchronous runs and replays)

3000 steps of 5×10⁻⁷ s, same machine and server. Each case once.

| Run | Request at step | Reply recorded at step | Solver wait at the request step | Model wait | Files equal to baseline |
|---|---:|---:|---:|---:|---:|
| Model off (baseline: request built, not sent) | 1250 | 1261 | 0.004 s | - | - |
| Describe one image | 250 | 1093 | 0.006 s | 34.0 s | 216 / 216 |
| Sequence of three images | 1250 | 2321 | 0.004 s | 43.4 s | 216 / 216 |
| Connection refused | 250 | 280 | 0.005 s | 0.002 s | 216 / 216 |
| Server made to stall (4 s deadline) | 250 | 353 | 0.005 s | killed at the 4 s deadline | 216 / 216 |

The callback took 0.008 to 0.019 s at the step at which a reply or error was
recorded (the solver waits for the child that writes the result files), about
0.1 s at the last step and at most 0.0052 s at every other step; a whole run
took about 0.05 s per step. Both replies arrived while the
solver was still running (843 and 1071 steps after the request). The model
waits are shorter than on October 17 mainly because the prompts are shorter
(570 and 907 tokens against 1541); 266 and 273 of those tokens were also still
in the server's cache from a trial run a few minutes earlier.

Replays of saved frames, three repeats each, two views (whole domain and a
window around the step):

| Question | Frames | Result |
|---|---|---|
| Where is the fastest flow? (percent of the plotted range) | 3 states × 2 views | 18 answers (6 frames, 3 repeats each), none within 10 % of the true spot; 14 to 18 % off in the whole-domain view (0.27 to 0.39 m), 50 to 80 % off in the window |
| How does the flow change? (trend words) | 3 frames × 2 views | Peak speed called `increasing` in both views while it falls from 60 to 47 (42) m/s; 1 of 3 words right in the whole-domain view, 2 of 3 in the window |

Details, the model's texts and the caveats are in the
[October 20 report](docs/results-20261020.md).

## Measurements (2026-10-19, Gemma 4 12B on a GPU node)

The October 17 paired replay (below) sent again with only the model name
changed: Gemma 4 12B QAT Q4_0 with its image projector on one NVIDIA A30
(MedicineBow, Slurm job 24696203), llama.cpp b11429 built from source with
CUDA, all layers on the GPU, context 2048.

| Model, machine | Condition | Position given | Error | Time per request |
|---|---|---|---:|---:|
| E2B, CPU, Oct 17 | Numbers only | (0.6012, 0.1143) m, all 3 | 60.92 cm | 14.5 to 55.6 s |
| E2B, CPU, Oct 17 | Numbers + image | (0.5, 0.1143) m, all 3 | 50.97 cm | 13.2 to 20.8 s |
| 12B, A30, Oct 19 | Numbers only | "unknown", all 3 | not scored | 2.0 to 3.3 s |
| 12B, A30, Oct 19 | Numbers + image | "unknown", all 3 | not scored | 2.1 to 2.7 s |

"Unknown" is not a zero error. The image answers add, as a possible
interpretation, high velocity "near x=0.00 m" (true x = 0.0005 m) with no y,
which the scorer does not read; two numbers-only answers blamed "the image"
although none was sent. The speed difference mixes model size, GPU against
CPU and a fresh server against a warm one. Details: [October 17 report](docs/results.md#same-replay-with-gemma-4-12b-on-a-gpu-2026-10-19),
[evidence](docs/evidence/2026-10-19-12b/README.md).

## Measurements (2026-10-17, run `pod-llm-demo.LRfJBN`)

8 vCPU, 7.8 GiB RAM, no GPU; llama-server on 4 threads, llama.cpp
b11429, context 2048. 20,540 cells, time step
10⁻⁷ s, ten steps. Each condition was run once on this date. A repeat on
October 19 gave the same step-5 hashes, the same image reply and the same
replay coordinates; the numbers-only reply and the wording of five replay
answers changed ([details](docs/results.md#repeat-on-2026-10-19)).

| Condition | Result | Steps | Files equal to baseline | Callback time |
|---|---|---:|---:|---:|
| No model request | baseline | 10 | - | 0.493 s |
| Numbers + image | answer stored | 10 | 45 / 45 | 78.256 s |
| Numbers only | answer stored | 10 | 45 / 45 | 39.672 s |
| Connection refused | error stored, run continues | 10 | 45 / 45 | 0.509 s |
| Server made to stall (4 s deadline) | timeout stored, run continues | 10 | 45 / 45 | 4.013 s |

Callback time is measured in C++ from just before the Python analysis call to
just after it returns. Of the 78.256 s in the image condition, rendering took
0.438 s and waiting for the model 77.560 s.

Using the saved step-5 state, the model was asked three paired times (six
requests) with the question, numbers and settings fixed and only the PNG added
or removed. The maximum speed, 82.53 m/s, was in the input for both conditions;
its location was not. The reference is cell 12090 at (0.0005, 0.0127) m.

| Condition | Claimed (x, y) m | In-plane error | Outcome |
|---|---|---:|---|
| Numbers only | (0.6012, 0.1143) | 60.92 cm | wrong in all 3 |
| Numbers + image | (0.5, 0.1143) | 50.97 cm | wrong in all 3 |

The numbers-only answers copied the domain's x and y upper bounds from the
input as the location. The image answers were about 10 cm closer and still
wrong.

## Open problems

1. Answer accuracy. With E2B, the default model, the descriptions are not
   usable. With v2 pictures, 12B and larger models place the fastest flow and
   the lowest pressure within 10 % in most pictures, also from a running
   solver and over a long run. With each picture on its own colour scale,
   12B reads clear changes in peak speed (29 of 30) but misses most changes
   under 2 %; the other models also miss clear changes (17 to 25 of 30).
   Trend words are now computed from the arrays in the callback. A small
   extreme next to a large region of similar colour (the cylinder's
   pressure) is missed by 12B.
2. Warning. The models tested do not see a coming crash in the pictures;
   simple numbers from the arrays (peak growth, cell-to-cell jumps) do as
   well or better.
3. Repeatability across hardware. The same request gives the same answer on
   the same node; on another GPU the text and some positions change.
4. Scope. 2D laminar cases and one extruded 3D case (no model has read a
   slice picture yet), 2 MPI ranks without a model request, up to two
   requests in flight. A request record can be lost when its writer exceeds
   its 0.2 s budget (1 of 118).

## Next steps

1. A model on slice pictures of a developed 3D flow.
2. The instability test without the stated frame times, and numeric
   warnings computed in the callback next to the model's answer.
3. A larger budget, or the worker itself, for writing request records.
4. Open the contribution to PythonFOAM: hooks, MPI gather, 3D slice, v2
   pictures, request builder, asynchronous and periodic paths, tests.
   Scripts for the GPU nodes are in [llm_demo/hpc/](Solver_Examples/PODFoam/llm_demo/hpc/README.md).

## Repository layout

```
Solver_Examples/PODFoam/      PODFoam solver (OpenFOAM v2106, also built in v2212) with the callback hooks
  validation/                 bridge check: ten steps, SVD round trip, verify.py
  llm_demo/                   callback module, llama-server client, v2 picture and request builder, five-case runners (sync and async),
                              describe sweep, requests every N steps, replay benchmarks (paired, describe, sequence), picture-reading,
                              random-window and trend tests, unit tests, requirements.txt
  llm_demo/hpc/               Slurm scripts for GPU nodes: the 12B paired replay, the picture tests, the v2 solver run and the periodic run (all run on MedicineBow)
docs/results-20261028.md      October 28: two requests in flight, telemetry without a history, computed trend words, 3D slice, instability test
docs/evidence/2026-10-28-inflight/       its two-in-flight run (Slurm job 24929296): summary, index, logs, comparison script, hash manifest
docs/evidence/2026-10-28-callback/       its callback check (Slurm job 24929555): comparisons, memory replay, hash manifest
docs/evidence/2026-10-28-3d/             its 3D slice test (Slurm job 24929629): case, frames, comparisons, hash manifest
docs/evidence/2026-10-28-instability/    its instability test (Slurm jobs 24929533, 24929534): answers, key, recount, hash manifest
docs/results-20261027.md      October 27: trend test, 4-bit Qwen, a cylinder flow, requests every 250 steps, repeats, MPI, POD files
docs/evidence/2026-10-27-picture-tests/  its picture tests (five Slurm jobs) and the cylinder runs: answers, keys, recount, hash manifest
docs/evidence/2026-10-27-solver/         its solver runs: periodic run, repeats, MPI, POD files, unstable attempts, hash manifest
docs/results-20261022-live.md October 22, continued: v2 pictures from the running solver, random windows, Qwen models
docs/evidence/2026-10-22-live-v2/       its solver run (Slurm job 24757460): frames, bodies, replies, logs, check script, hash manifest
docs/evidence/2026-10-22-window-test/   its picture tests (six Slurm jobs) and the developed flow: answers, keys, recount, hash manifest
docs/results-20261022.md      October 22 report: picture-reading test, seven Gemma 4 models, two picture styles
docs/evidence/2026-10-22-picture-test/  its records (Slurm job 24756981), answer key, independent re-scoring, hash manifest
docs/results-20261020.md      October 20 report: asynchronous runs, describe and sequence replays
docs/evidence/2026-10-20/     records of the October 20 runs and replays, hash manifest
docs/results.md               October 17 test report
docs/evidence/2026-10-17/     raw requests, responses, logs, verification, hash manifest
docs/evidence/2026-10-13/     earlier run (pod-llm-demo.SwwR2e) and its report, docs/results-20261013.md
docs/evidence/2026-10-19/     repeat of the October 17 run (pod-llm-demo.o5sNLJ), same hashes and replay coordinates
docs/evidence/2026-10-19-12b/ paired replay with Gemma 4 12B on an NVIDIA A30 (Slurm job 24696203), hash manifest
docs/evidence/check_manifest.py  verifies every evidence file against its manifest (also run in CI)
docs/upstream-project.md      original PythonFOAM README (other solvers, Docker, build notes)
.github/workflows/            tests.yml (unit tests, Python 3.10 and 3.12), evidence.yml (hashes, links)
CHANGELOG.md, Makefile
```

Other directories (`APMOSFoam`, `AEFoam`, `PINNFoam`, `TurbulenceModel_Examples`,
`Handson_Examples`) are unchanged from upstream.

## More

- [October 28](docs/results-20261028.md): two requests in flight, telemetry without a history, computed trend words, 3D slice, instability test
- [October 27](docs/results-20261027.md): reading change, 4-bit Qwen, a cylinder flow, a request every 250 steps, repeats, MPI
- [October 22, continued](docs/results-20261022-live.md): v2 pictures from the running solver with 12B, random windows, a developed flow, Qwen models
- [October 22 report](docs/results-20261022.md): picture-reading test, seven Gemma 4 models from E2B to 31B, two picture styles
- [October 20 report](docs/results-20261020.md): asynchronous runs, one-snapshot and sequence replays, caveats
- [October 17 report](docs/results.md): synchronous conditions, paired image/no-image replay
- [12B replay](docs/results.md#same-replay-with-gemma-4-12b-on-a-gpu-2026-10-19): the October 17 paired requests, Gemma 4 12B on a GPU node
- [Evidence](docs/evidence/README.md): raw requests and responses, logs, verification results, hash manifests
- October 28 downloads: [tests-2026-10-28](https://github.com/seungminyome/PythonFOAM/releases/tag/tests-2026-10-28) (the two-in-flight run's requests, replies and frames, the instability test set and its jobs)
- October 27 downloads: [tests-2026-10-27](https://github.com/seungminyome/PythonFOAM/releases/tag/tests-2026-10-27) (the five picture jobs and two new test sets, the cylinder runs, the periodic run's requests, replies and frames, the MPI and POD-file runs)
- Picture test downloads: [October 22](https://github.com/seungminyome/PythonFOAM/releases/tag/picture-test-2026-10-22) (the 308 requests with their answer key, the random-window sets, and every reply of the seven jobs)
- v2 solver run downloads: [October 22](https://github.com/seungminyome/PythonFOAM/releases/tag/pod-insitu-v2-2026-10-22) (every written time directory of the five cases and the eleven sweep cases, the trial run, the developed flow and the job records)
- Full run downloads: [October 20](https://github.com/seungminyome/PythonFOAM/releases/tag/pod-insitu-async-2026-10-20), [October 17](https://github.com/seungminyome/PythonFOAM/releases/tag/pod-insitu-tests-2026-10-17) (all saved results of the five-case runs and the executed sources, no model weights; the time directories of the October 20 windowed frame run are not included)
- [Changelog](CHANGELOG.md)
- [Korean repository](https://github.com/seungminyome/PythonFOAM-Korean) and its [illustrated results](https://seungminyome.github.io/PythonFOAM-Korean/)

## Acknowledgements and license

This extends the PODFoam example of [PythonFOAM](https://github.com/argonne-lcf/PythonFOAM)
(Argonne National Laboratory). The original description and setup notes are in
the [project reference](docs/upstream-project.md). The model is served with
[llama.cpp](https://github.com/ggml-org/llama.cpp). The [license](LICENSE) is unchanged.
