# October 22, continued: v2 pictures from the running solver, random windows, more models

Slurm jobs 24757327, 24757344, 24757382 to 24757384, 24757459 and 24757460 on MedicineBow, each on one NVIDIA RTX A6000 (49,140 MiB); the flow runs 24757337 and 24757429 on CPU nodes · llama.cpp b11429 (commit `d812350`) · 2026-10-22, 03:14 to 11:38 MDT · code: [Records](#records)

[README](../README.md) · [Evidence: picture tests](evidence/2026-10-22-window-test/README.md) · [Evidence: solver run](evidence/2026-10-22-live-v2/README.md) · [How to run](../Solver_Examples/PODFoam/llm_demo/README.md#v2-pictures-from-the-solver-llm_image_stylev2) · Downloads: [picture tests](https://github.com/seungminyome/PythonFOAM/releases/tag/picture-test-2026-10-22), [solver run](https://github.com/seungminyome/PythonFOAM/releases/tag/pod-insitu-v2-2026-10-22) · [Korean](https://github.com/seungminyome/PythonFOAM-Korean/blob/main/docs/results-20261022-live.md)

The [first October 22 report](results-20261022.md) left two gaps. The solver
still drew the v1 picture, and in the saved flow states one fixed answer
scored as well as any model, because the fastest flow and the lowest pressure
stayed at the step corner. Since then:

- The callback draws v2 pictures and sends them in `describe` and `sequence`
  requests (`LLM_IMAGE_STYLE=v2`), built by the same code as the picture test.
- OpenFOAM v2212 runs on the GPU nodes in an Apptainer image, and PODFoam
  builds there unchanged.
- Gemma 4 12B answered from inside a running solver: the five asynchronous
  cases, started from a developed flow, then eleven more describe requests at
  different steps, each with its own window.
- The picture test was repeated with the plotted window placed at random
  around the fastest cell, so that the right answer moves from picture to
  picture: eleven models, three window seeds, a larger image-token limit and
  a developed flow.
- Four Qwen models answered the 308 requests of the first picture test.

## The solver draws the v2 picture

With `LLM_IMAGE_STYLE=v2` the callback writes, for each captured step, a
folder with the arrays (`fields.npz`), one 1024×576 picture per field (|U|,
then p) and a metadata file written last. The request is built from that
folder by `readable_request.py`, which the picture test now also uses, so the
solver sends exactly the kind of request that was scored on saved pictures:
the same prompts, `max_tokens` 320, the same seed and no prompt cache. A
sequence sends each picture on its own colour scale, with the numbers on the
colour bars (the v2own style that read the clear trends best). The default is
still v1, which leaves the earlier behaviour byte for byte. A v2 describe
request carries no SVD summary, so the callback then keeps no snapshot window.

Checks that run with every v2 solver run (`verify_async.py`): each request
body equals the builder applied to the frame folder on disk, byte for byte;
the frame's arrays equal the fields the solver wrote at that step; the
pictures' hashes are the ones in the request; and the answer is scored against
the arrays. A unit test rebuilds two of the published picture-test requests
from their pictures and gets the same bytes, and pins five more by hash.
The suite now has 92 unit tests. On a MedicineBow compute node with Python
3.10, 3.11 and 3.12 the new tests pass; the three timing tests named in
[hpc/README.md](../Solver_Examples/PODFoam/llm_demo/hpc/README.md#v2-pictures-from-the-running-solver-async_v2slurm-run-2026-10-22)
fail there in some runs, as they did before these changes.
With the published code, the 152 v2 and 120 v1 bodies of the first picture
test rebuilt from their pictures, the first report regenerated from its
answers, and six window frames redrawn from their states are byte-identical to
the originals.

## A developed flow

The October 20 runs and the saved states of the picture test cover the first
3 ms after the flow starts from rest. There the fastest cell sits at the step
corner, x 1.6 to 12 mm and y 12.6 to 13.6 mm, and one fixed answer is right
almost every time. For a flow that moves, `pimpleFoam` ran the same case (2D,
laminar, inlet 32.2 m/s, ν = 1.56×10⁻⁵ m²/s) in the v2212 image to t = 0.1 s,
about one and a half flow-through times of the 2.15 m channel at the inlet
speed: 21,108 steps with an adaptive time step (Slurm job 24757429, 18 min on
a CPU node). The time step kept the Courant number at about 0.5 (at most
0.507, after one start-up step at 1.25) until it reached its 5×10⁻⁶ s limit at
t = 0.011 s; after t = 0.03 s the Courant number was at most 0.34. Fields were
written every millisecond.

In the states from t = 0.032 s on, vortices roll up behind the step and travel
downstream. In the 35 states from 0.032 to 0.1 s used below, the fastest cell
is at x 22 to 75 mm and y 16 to 21 mm. In the solver run from t = 0.1 s, the
largest Courant number, which follows the largest speed, rose and fell between
0.23 and 0.35 with a period of about 2.7 ms (spectral peak at about 370 Hz in
the 0.03 s record of every step).

<img src="evidence/2026-10-22-live-v2/suite/async-describe/llm_observation/step-000250/U.png" width="415" alt="|U| at t = 0.10125 s in the window x 0 to 0.12 m, y 0 to 0.04 m: a row of vortices behind the step"> <img src="evidence/2026-10-22-live-v2/suite/async-describe/llm_observation/step-000250/p.png" width="415" alt="p at the same time: low-pressure vortex cores at y about 25 to 30 %">

*The two pictures the solver sent at step 250 of the run below (t = 0.10125 s): |U| (left) and p (right), window x 0 to 0.12 m, y 0 to 0.04 m.*

## Random windows

`window_test.py` draws saved states with the plotted window placed at random
around the fastest cell: the cell at least 15 % from every edge, at least 200
cells inside, 0.03 to 0.114 m high and 1.5 to 4 heights wide. The answer key
and scoring are those of the picture test (within 10 % of the plotted range).
Since every picture has its own window, the fixed-answer score is now one
answer for the whole set: the best single integer (x, y), counted over all
pictures.

The first set uses the start-up states: a `pimpleFoam` run of 6000 steps of
5×10⁻⁷ s in the v2212 image (job 24757337), 12 states every 500 steps, four
windows each, in v1 and in v2 (48 pictures per style).

| Model | Fastest flow, v1 / v2 | Lowest p, v1 / v2 | v2 median distance, fastest / lowest p | Median time per v2 request |
|---|---:|---:|---:|---:|
| E2B Q4_0, Q8_0 projector | 6 / 5 | 7 / 14 | 27.8 / 16.0 % | 1.03 s |
| E2B Q4_0, BF16 projector | 5 / 5 | 5 / 13 | 27.3 / 17.8 % | 1.06 s |
| E2B QAT | 5 / 3 | 5 / 8 | 25.5 / 19.6 % | 1.00 s |
| E4B QAT | 8 / 16 | 5 / 13 | 16.0 / 13.6 % | 1.43 s |
| 12B QAT | 10 / **46** | 17 / **47** | 3.5 / 1.8 % | 3.19 s |
| 26B-A4B QAT | 3 / **47** | 6 / **47** | 2.6 / 1.7 % | 2.43 s |
| 31B QAT | 13 / **45** | 15 / **48** | 3.1 / 2.0 % | 7.51 s |
| Qwen3-VL-8B Q8_0 | 3 / 21 | 4 / 36 | 11.4 / 6.4 % | 2.44 s |
| Qwen3-VL-32B Q8_0 | 0 / 38 | 2 / 39 | 4.6 / 5.1 % | 10.99 s |
| Qwen3.5-27B Q8_0 | 2 / 43 | 3 / 46 | 4.8 / 2.6 % | 8.47 s |
| Qwen3.5-35B-A3B Q8_0 | 5 / **47** | 3 / 46 | 3.1 / 2.5 % | 2.30 s |
| One fixed answer | 7 | 7 | | |

Counts out of 48 (job 24757344).

With random windows the fixed answer gets 7 of 48, and 12B, 26B-A4B, 31B and
Qwen3.5-35B-A3B still place both extremes within 10 % in 45 to 48 of 48 v2
pictures. With v1 the same four get 3 to 17 of 48. The E2B forms stay at or
below the fixed answer for the fastest flow (3 to 6 of 48) in both styles;
E4B gets 16 and 13 with v2.

The six strongest models were run again on the same states with two other
window seeds, and on the first set with the image-token limit raised from 256
to 1024 (context 8192):

| Model | Seed 1 | Seed 1, image-token limit 1024 | Seed 2 | Seed 3 | Seeds 1 to 3 together |
|---|---:|---:|---:|---:|---:|
| 12B QAT | 46 / 47 | 46 / 47 | 48 / 48 | 47 / 48 | 141 / 143 |
| 26B-A4B QAT | 47 / 47 | 46 / 47 | 48 / 48 | 48 / 48 | 143 / 143 |
| 31B QAT | 45 / 48 | 46 / 48 | 46 / 48 | 45 / 48 | 136 / 144 |
| Qwen3-VL-32B Q8_0 | 38 / 39 | 36 / 46 | 34 / 41 | 36 / 41 | 108 / 121 |
| Qwen3.5-27B Q8_0 | 43 / 46 | 47 / 48 | 44 / 48 | 44 / 48 | 131 / 142 |
| Qwen3.5-35B-A3B Q8_0 | 47 / 46 | 48 / 48 | 48 / 48 | 48 / 48 | 143 / 142 |
| One fixed answer | 7 / 7 | 7 / 7 | 9 / 9 | 9 / 10 | 25 / 26 |

v2 only; fastest flow / lowest pressure within 10 %, out of 48 per seed and 144
together (jobs 24757344, 24757382, 24757384, 24757383). With v1 every one of
these models stayed at 0 to 17 of 48 in each seed.

Raising the limit did not change the Gemma requests (1,051 prompt tokens
either way); the Qwen requests grew from about 1,020 to about 1,670 tokens.
The llama.cpp log warns that Qwen-VL models need at least 1,024 image tokens
for grounding tasks and suggests `--image-min-tokens 1024`; that setting was
not tried, so the Qwen numbers are a lower bound for these models in this
server, not their best.

## The developed flow, random windows

The same test on 35 states of the developed run (t = 0.032 to 0.1 s, every
2 ms), four random windows each (job 24757459, 140 pictures per style). One
fixed answer gets 16 (fastest flow) and 17 (lowest pressure) of 140.

| Model | Fastest flow, v1 / v2 | Lowest p, v1 / v2 | v2 median distance, fastest / lowest p | Median time per v2 request |
|---|---:|---:|---:|---:|
| E4B QAT | 16 / 39 | 21 / 34 | 13.8 / 21.1 % | 1.4 s |
| 12B QAT | 12 / **108** | 30 / **130** | 3.4 / 2.4 % | 3.1 s |
| 26B-A4B QAT | 19 / **113** | 22 / **139** | 3.6 / 2.2 % | 2.4 s |
| 31B QAT | 17 / **106** | 25 / **133** | 3.6 / 1.8 % | 7.3 s |
| Qwen3.5-27B Q8_0 | 10 / **109** | 19 / **136** | 3.4 / 2.9 % | 8.5 s |
| Qwen3.5-35B-A3B Q8_0 | 8 / **121** | 11 / **134** | 4.4 / 2.9 % | 2.1 s |
| One fixed answer | 16 | 17 | | |

Counts out of 140.

The lowest pressure, a vortex core, was found about as often as in the
start-up states: 130 to 139 of 140 for the five larger models. The fastest
flow was harder: 106 to 121 of 140 (76 to 86 %), against 91 to 99 % over the
three window seeds of the start-up states. Most of these misses named another
spot almost as fast: for 12B, 26B-A4B, 31B and Qwen3.5-27B, 19 to 30 of their
27 to 34 misses point at a cell with at least 90 % of the largest speed in the
window. With v1 the same models got 8 to 19 of 140 fastest-flow positions
right, about the fixed answer.

<img src="evidence/2026-10-22-window-test/pictures/developed-flow-window-v2-step080000-w3-U.png" width="415" alt="Developed flow, |U| at t = 0.04 s in a random window: 12B within 0.4 %"> <img src="evidence/2026-10-22-window-test/pictures/developed-flow-window-v2-step124000-w1-U.png" width="415" alt="Developed flow, |U| at t = 0.062 s in a tall window: the brightest spot at y 19 % is little brighter than the free stream above it">

*Developed flow, v2 |U|. Left, t = 0.04 s: 12B within 0.4 %. Right, t = 0.062 s: the brightest spot (y 19 %, 35.1 m/s) is little faster than the free stream above it; 12B answered y 80 %, where the speed is 32.5 m/s (61 % off).*

## Qwen models on the 308 requests of the first picture test

The same 308 requests and answer key as the first October 22 test, sent to
four Qwen models (job 24757327), all Q8_0 (the Gemma models were 4-bit), with
the image-token limit of 256.

| Model | Synthetic, fastest / lowest p, v2 | Planted, fastest / lowest p, v2 | Saved flow, fastest / lowest p, v2 | Clear synthetic trends, speed / p, v2own | Weights | GPU memory when ready | Median per request |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3-VL-8B | 18 / 19 | 28 / 18 | 19 / 23 | 12 / 12 | 8.7 GB | 9,946 MiB | 2.31 s |
| Qwen3-VL-32B | 32 / 29 | 32 / 25 | 18 / 17 | 12 / 12 | 34.8 GB | 35,340 MiB | 10.83 s |
| Qwen3.5-27B | 32 / 30 | 32 / 21 | 24 / 24 | 12 / 12 | 28.6 GB | 27,768 MiB | 8.29 s |
| Qwen3.5-35B-A3B | 32 / 32 | 32 / 30 | 24 / 24 | 12 / 12 | 36.9 GB | 35,860 MiB | 2.07 s |
| 12B QAT (first test) | 32 / 32 | 32 / 25 | 22 / 22 | 12 / 12 | 7.0 GB | 7,966 MiB | 2.86 s |
| One fixed answer | 5 / 5 | 6 / 6 | 24 / 24 | 6 / 6 | | | |

Synthetic and planted out of 32, saved flow out of 24, clear trends out of 12.

Qwen3.5-35B-A3B, a mixture-of-experts model (about 3 B parameters active per
token), is the only one that matched or beat 12B in every score column here;
it was also the fastest of the four. On the planted pictures it found the planted
pressure dip in 30 of 32, where 12B, 26B-A4B and 31B named the step corner in
7 to 12. With one shared colour scale (v2) the four got 7 to 12 of the 12 clear
speed changes and 5 to 9 of the pressure changes right; with the numbers on
the colour bars (v2own) all four read all 12 clear changes in both fields.
On the saved flow's pressure trend (14 sequences, v2own) they were right in
10, 6, 12 and 14 (8B, 32B, 27B, 35B-A3B); 12B was right in 3. With v1
pictures they got 2 to 12 of 32 fastest-flow positions right in the synthetic
and planted sets. Per-set counts are in the job's
[report](evidence/2026-10-22-window-test/reports/picture-test-24757327.md).

## Requests from the running solver

The asynchronous suite of October 20, now with v2 pictures and Gemma 4 12B on
the node's GPU (job 24757460). PODFoam was built in the v2212 image against a
conda Python 3.11; its bridge validation passed there first. Every case
started from the developed state at t = 0.1 s (the mesh and start files are
checked by hash) and ran 6000 steps of 5×10⁻⁶ s to t = 0.13 s, written every
250 steps; the Courant number stayed at or below 0.347. The plotted window
was x 0 to 0.12 m, y 0 to 0.04 m (the pictures above).

| Run | Request at step | Reply recorded at step | Solver wait at the request step | Model wait | Files equal to baseline |
|---|---:|---:|---:|---:|---:|
| Model off (baseline: request built, not sent) | 3750 | 3763 | 0.003 s | - | - |
| Describe one snapshot | 250 | 320 | 0.004 s | 3.17 s | 432 / 432 |
| Sequence of three snapshots (steps 3000, 3250, 3750) | 3750 | 3823 | 0.004 s | 3.15 s | 432 / 432 |
| Connection refused | 250 | 261 | 0.004 s | 0.011 s | 432 / 432 |
| Server made to stall (4 s deadline) | 250 | 324 | 0.004 s | killed at the 4 s deadline | 432 / 432 |

Each case took 323 to 324 s of wall time (0.054 s per step); the callback took
at most 0.007 s at the steps without a request or reply, 0.023 to 0.044 s at
the step at which a reply or error was recorded, and about 0.19 s at the last
step, where the telemetry is written. The describe request had 998 prompt
tokens, the sequence request 2,168; neither used the prompt cache. Every
written field of every case equals the baseline's: the requests changed nothing
in the computation.

What the model said:

- Describe, step 250: fastest flow at (40, 45) % of the window, true (37.1,
  46.5), 3.3 % away; lowest pressure at (35, 30) %, true (38.0, 25.9), 5.0 %
  away. Both within 10 %.
- Sequence, steps 3000, 3250 and 3750: peak speed decreasing (right: 38.6 to
  34.8 m/s), the fastest flow moves (right: 24 % of the window), lowest
  pressure more negative (wrong: it rose from -365 to -224 m²/s²).

A shorter trial run before it (job 24757458: 600 steps from the same state,
request at step 100, sequence at 200, 300 and 500) passed the same checks;
there the describe answer was 33 % and 29 % away, and all three trend words
were right.

Both request bodies equal the tested builder applied to the frames on disk,
byte for byte. The describe body is the same bytes in the describe,
connection-refused and stall cases (same frame, same request).

### Eleven more requests, each with its own window

After the suite, `run_live_sweep.py` ran eleven more cases from the same start
state, each with one describe request at step R = 500, 1000, ..., 5500 and
stopping 300 steps later. Each window was placed at random around the fastest
cell of the baseline's state at R, by the rule of the window test: 0.09 to
0.32 m wide, 0.037 to 0.106 m high, 6,154 to 10,793 cells. Two cases ran at a
time.

| Request at step | Reply recorded at step | Fastest flow, distance | Lowest pressure, distance |
|---:|---:|---:|---:|
| 500 | 571 | 2.7 % | 0.8 % |
| 1000 | 1078 | 0.8 % | 1.8 % |
| 1500 | 1569 | **40.8 %** | 4.5 % |
| 2000 | 2092 | 1.6 % | 3.2 % |
| 2500 | 2593 | 3.5 % | 3.7 % |
| 3000 | 3078 | 3.2 % | 2.4 % |
| 3500 | 3589 | 4.0 % | 0.8 % |
| 4000 | 4092 | 4.9 % | 2.2 % |
| 4500 | 4575 | 3.6 % | 1.1 % |
| 5000 | 5076 | 0.5 % | 1.9 % |
| 5500 | 5584 | **13.2 %** | **24.1 %** |

Distance from the true cell in percent of the plotted range; bold is more
than 10 %.

- All eleven answers arrived while the solver was running, 69 to 93 steps
  after the request (2.85 to 3.39 s of model time). The solver's callback took
  at most 0.005 s at a request step.
- Every request body equals the builder applied to the frame on disk, byte
  for byte, and every frame's arrays equal the baseline's written fields at
  that step.
- 9 of 11 fastest-flow and 10 of 11 lowest-pressure answers were within
  10 %, with median distances of 3.5 % and 2.2 %. One fixed answer for all
  eleven would get 4 and 4.
- At step 1500 the answer put the fastest flow in the free stream at the top
  of the window (y 90 %, 32.5 m/s) instead of the spot just above the shear
  layer (y 49 %, 35.5 m/s). At step 5500 the picture has two bright spots and
  two pressure minima of similar strength; the fastest-flow answer fell
  between the spots (26.5 against 37.8 m/s), and the lowest-pressure answer
  named the other minimum (-337 against -359 m²/s²).

In every written directory of the eleven cases, U, p, phi and the time files
are byte-identical to the baseline's (858 files). The POD mode files that
PODFoam writes from its own SVD (upod, vpod, wpod; 2,145 files) differ from
the baseline's by at most 9.4×10⁻¹² of their largest value, while in the
suite, whose cases ran one at a time, they were identical. The cause was not
isolated. The sweep cases ran two at a time without a thread limit; the
published sweep script runs each case with one BLAS thread.

## Time and memory

| | |
|---|---|
| Solver step with the callback | 0.054 s (6000 steps in 323 to 324 s per case) |
| Callback, median over all steps | 0.00005 s |
| 12B answer, suite and sweep | 2.85 to 3.39 s (describe 998 prompt tokens, sequence 2,168) |
| GPU memory, whole job (sampled every second) | 7,966 to 7,996 MiB of 49,140 |
| Solver with Python callback and worker, peak resident memory | 560 to 582 MiB |
| llama-server, peak resident memory on the host | 1.3 GiB (baseline case) to 2.8 GiB |
| Job 24757460: build, five cases, eleven sweep cases | 68 min |
| Developed flow, `pimpleFoam`, 21,108 steps (job 24757429) | 18 min |
| Window tests, six to eleven models each (jobs 24757344, 24757382 to 24757384) | 56 to 70 min |
| Qwen on the 308 requests (job 24757327) | 2 h 4 min |
| Developed-flow window test, six models (job 24757459) | 1 h 53 min |

12B used about 8,000 of the A6000's 49,140 MiB; it also ran on a 24 GB A30 on
October 19. When their servers were ready, 26B-A4B used 15,892 MiB, 31B
20,128 MiB and the Qwen models in Q8_0 9,946 to 35,860 MiB; these ran only on
the A6000.

## What this shows and what it does not

Shown:

- The solver draws the v2 pictures and asks a GPU-served 12B model during the
  run without changing the computation. In the fifteen runs with a request
  (four suite cases, eleven sweep cases) the written flow fields are
  byte-identical to the baseline run, the callback took at most 0.005 s at a
  request step, and every answer arrived within 93 steps (about 3 s).
- What the solver sends is what was tested: every live request body equals
  the picture-test builder applied to the frame on disk, byte for byte.
- With random windows, where one fixed answer gets 7 to 10 of 48, 12B, 26B-A4B,
  31B and Qwen3.5-35B-A3B place both extremes within 10 % in 45 to 48 of 48
  pictures in each of three window seeds. In the live sweep, 12B was within
  10 % in 9 and 10 of 11 answers, where a fixed answer gets 4.
- In the developed flow, with vortices behind the step and random windows,
  12B, 26B-A4B, 31B and Qwen3.5-35B-A3B placed the lowest pressure within
  10 % in 130 to 139 of 140 pictures and the fastest flow in 106 to 121,
  where one fixed answer gets 16 and 17. Most fastest-flow misses named
  another spot with at least 90 % of the largest speed.

Not shown:

- Reading how the flow changes. The trend question was asked twice from a
  running solver (here and in the trial run): the pressure trend was wrong
  once. In the start-up states of the replays the trend words barely vary.
- Repeatability of the live numbers. Each suite case ran once, the trial's
  describe answer was 33 % off, and the sweep is eleven requests.
- Other cases. One 2D laminar flow over a backward-facing step, one mesh of
  20,540 cells, one serial process, OpenFOAM v2212 in a container (the
  October 13 to 20 runs used v2106; the bridge validation passes on both).
- The text of the answers. Only the two positions and the three trend words
  are scored; the descriptions were not checked.
- A fair Qwen comparison. The Qwen models ran in Q8_0 against Gemma's 4-bit
  files, and below the image-token minimum that llama.cpp suggests for them.
- Any use of the answers. Nothing from the model goes back into the solver.

## Next

1. Ask the trend question with the 2 % threshold in the prompt, on sequences
   of the developed flow, where the trend words vary.
2. Requests every N steps in one run, with more than one in flight, and
   longer runs; measure memory and the pipe traffic.
3. Qwen with `--image-min-tokens 1024`, and 4-bit Qwen files, to compare the
   families at equal settings.
4. Prepare the callback hooks, the v2 pictures, the request builder, the
   asynchronous path and their tests as a contribution to the PythonFOAM
   repository.

## Records

- Code. The window and Qwen jobs (24757327, 24757344, 24757382 to 24757384)
  ran from the picture-test bundle: the `llm_demo` of `58e00d9` with
  `window_test.py`, `window_test.slurm` and the Qwen rows of `models.tsv`
  added and, from job 24757382 on, `start_server.sh` reading
  `LLM_IMAGE_TOKENS`; each job's `sha256.txt` hashes the scripts it ran.
  Jobs 24757459 and 24757460 ran from the checkout at `354caf9` with
  uncommitted changes; the patch, the status and the new files are in the
  [evidence](evidence/2026-10-22-live-v2/README.md), and all 62 sources the
  solver run recorded equal them. The published code, commit `dee7731`, adds a
  review's fixes, none of which changes a request body. `python_module.py`
  refuses a frame folder left by an earlier run, checks the `max_tokens` rule,
  reports a refused sequence setting once and allows the telemetry writer more
  time on long runs. `run_live_sweep.py` runs each case with one BLAS thread
  and records every failed check instead of stopping. `verify_async.py`,
  `pack_run.py`, `run_demo.sh` and the job script record and check more.
- [Evidence for the picture tests](evidence/2026-10-22-window-test/README.md):
  each job's report, every parsed answer with its score (`metrics.jsonl`),
  the answer keys of the four window sets, server logs, example pictures, the
  developed run's settings, and a recount without the test code that
  reproduces every count cell of the six reports.
- [Evidence for the solver run](evidence/2026-10-22-live-v2/README.md):
  settings, verification, timings, per case the request, reply and result,
  the request bodies, the frames (pictures and arrays), compressed logs and
  telemetry; the sweep's plan, summary, frames and replies; the comparison of
  every sweep field with the baseline; the job script, its output, the server
  records and the code state; and a check script that rebuilds every request
  body from its frame and recomputes every score from the arrays.
- Downloads. [picture-test-2026-10-22](https://github.com/seungminyome/PythonFOAM/releases/tag/picture-test-2026-10-22):
  the archives of all window and Qwen jobs and their test sets.
  [pod-insitu-v2-2026-10-22](https://github.com/seungminyome/PythonFOAM/releases/tag/pod-insitu-v2-2026-10-22):
  the suite's complete outputs (every time directory), the eleven sweep cases,
  the trial run, the developed flow with its 101 written states, and the job
  records.
