# October 28 evidence: can a model see a run going unstable?

Four vision-language models were shown three v2 frames of one pimpleFoam run
of the 2D step case and asked whether the run shows signs of numerical
instability. The models were Gemma 4 12B, 26B-A4B and 31B (QAT Q4_0) and
Qwen3.5-35B-A3B (Q8_0). Each frame is two pictures, |U| and p, each on its own
colour scale, in the window the solver plots (x 0 to 0.12 m, y 0 to 0.04 m).
The set has 70 triples: 27 whose last frame is 1 to 10 steps before a crash
(scored), 16 from the same runs further from the crash (not scored), and 27
from runs that did not crash (scored).

In short (counts from `reports/` and `independent-recount.json`):

- Every model said `unstable` for the 3 triples whose last frame is the step
  before the crash. In those frames the field has already blown up: the
  largest |U| in the window is 84.6 m/s, 3.0×10⁸ m/s and 1.5×10⁴⁰ m/s.
- Besides those, the models said `unstable` for 0 to 3 more triples. All of
  them came from one run, and the earliest ended 5 steps before its crash.
- No model said `unstable` for a run that did not crash. No model answered
  `cannot_tell`.
- Every triple a model called `unstable` had the peak |U| in the window grow
  by 30.8 % or more from the first to the last frame. A rule on that number
  alone (growth above 20 %) gets 33 of the 54 scored items right. The models
  get 30 to 33, and a fixed answer gets 27.

On this set the pictures added nothing beyond the colour-bar numbers.

## Jobs

| Job | What | Where | Time (MDT, 2026-10-28) |
|---|---|---|---|
| 24929408 | `central-dt2e-5` run again from t = 0.1 s, to see whether and when it diverges (two copies: every step written, every 10th step written) | CPU, `mb` (mbcpu-010) | 16:25 to 16:26 |
| 24929449 | `central-dt5e-6` run again for 4,000 steps | CPU (mbcpu-001) | 16:31 to 16:34 |
| 24929452 | the two upwind runs again for 2,000 steps each | CPU (mbcpu-010) | 16:33 to 16:36 |
| 24929495 | build and check of the test set (`instability_test.py build`, `check`) | CPU (mbcpu-009) | 16:45 to 16:48 |
| 24929533 | Gemma 4 12B, 26B-A4B, 31B on the 70 requests (`window_test.slurm`, `PICTURE_TEST_SCRIPT=instability_test.py`) | NVIDIA L40S (mbl40s-002) | 16:51 to 17:01 |
| 24929534 | Qwen3.5-35B-A3B Q8_0 on the 70 requests | NVIDIA L40S (mbl40s-002) | 16:51 to 16:54 |

Runs used but not made today: `central-dt3e-5` and `central-dt4e-5` (job
24929300, 2026-10-28 15:56), the October 27 runs that the reruns repeat (jobs
24903082 and 24903182), and the developed flow of October 22 (job 24757429).

## Runs

All runs are pimpleFoam (OpenFOAM v2212, laminar, PISO, ν = 1.56×10⁻⁵ m²/s,
inlet 32.2 m/s) on the same mesh of 20,540 cells. All but `developed` start
from its state at t = 0.1 s. They differ only in the scheme for div(phi,U),
the time step, the end time and how often they write (`flow/cases/`). Courant
numbers are the largest value the solver printed before each step, so each
one comes from the state written at the end of the step before
(`flow/logs-summary.json`).

| Run | div(phi,U) | Δt (s) | Steps | How it ended | Largest Courant number | States used | Triples |
|---|---|---|---:|---|---|---|---|
| `central-dt2e-5` | Gauss linear | 2×10⁻⁵ | 467 | floating point exception in step 467 (t = 0.10934 s) | 1.13 at step 1; 1.07 to 2.37 up to step 460; 2.06, 2.18, 2.27, 2.39, 2.70, 2.94 in steps 461 to 466; 1.7×10³⁸ in step 467 | every step, 1 to 466 | 10 scored, 12 early |
| `central-dt3e-5` | Gauss linear | 3×10⁻⁵ | 27 | floating point exception in step 27 | 1.70 (step 1) to 2.67 (step 25); 4.62 in step 27 | every step, 1 to 26 | 10 scored, 4 early |
| `central-dt4e-5` | Gauss linear | 4×10⁻⁵ | 10 | floating point exception in step 10 | 2.27 (step 1) to 2.86 (step 9); 1.4×10⁷ in step 10 | every step, 1 to 9 | 7 scored |
| `upwind-dt2e-5` | Gauss upwind | 2×10⁻⁵ | 2,000 | End | 0.90 to 1.34 | every 10th step | 7 |
| `upwind-dt4e-5` | Gauss upwind | 4×10⁻⁵ | 2,000 | End | 1.76 to 2.56 | every 10th step | 7 |
| `central-dt5e-6` | Gauss linear | 5×10⁻⁶ | 4,000 | End | 0.28 to 1.05 | every 50th step | 6 |
| `developed` | Gauss upwind | adaptive, at most 5×10⁻⁶ (maxCo 0.5) | 21,108 (t = 0 to 0.1 s) | End | 1.25 at step 2, at most 0.51 from step 11 | every 1 ms from t = 0.032 s | 7 |

- `central-dt2e-5` ran 150 steps on October 27 and finished, because 150
  steps was its end time. Run again from t = 0.1 s (job 24929408), it
  crashed in step 467. Its first 150 steps are byte for byte those of
  October 27: U, p and phi were compared at t = 0.10002, 0.1015 and 0.103 s
  (`flow/run-central-long-24929408.out`). A second copy that writes every
  10th step crashed in the same step with the same last Courant number (same
  output file). Over the
  run its largest Courant number rose to 1.89 (step 45), fell to 1.07
  (step 111) and rose again before the last six steps.
- The two upwind runs and `central-dt5e-6` ran 400 steps on October 27. Run
  again for 2,000 and 4,000 steps, they ended. Their first 400 steps are byte
  for byte the October 27 ones (U, p and phi compared at t = 0.108, 0.116,
  0.10025 and 0.102 s). The reruns were made because `central-dt2e-5` shows
  that 150 or 400 steps without a crash do not prove a run is stable.
- All three crashes start inside the window. In the last frame before each
  crash, the fastest cell is at x = 10.9 % and y = 31.4 % of the window
  (`central-dt2e-5`), at 14.4 % and 30.7 % (`central-dt3e-5`) and at 31.0 % and
  31.5 % (`central-dt4e-5`). That is x = 0.013 to 0.037 m and y = 0.012 to
  0.013 m (key: `fastest_flow_percent` of each frame). This is the shear layer
  that leaves the step corner, which is at x = 0, y ≈ 0.0127 m (the lowest
  cell centre upstream of x = 0).
- In `central-dt2e-5` the largest |U| over the whole domain is 75.3 to 75.6 m/s
  in the frames of steps 453 to 462. The largest |U| in the window is 39.7 to
  52.0 m/s, so that fastest flow is outside the window. The pictures do not
  show it.
- Not used: `central-dt5e-5`, `-dt6e-5`, `-dt8e-5` and `-dt2e-4` crashed in
  their first step and wrote no state. Upwind `dt8e-5`, `dt2e-4` and `dt5e-4`
  ended but are not in the set.

## Design

- **Pictures.** Each triple is three v2 frames (`readable_request.render_frame`,
  as the solver draws them with `LLM_IMAGE_STYLE=v2`). Each frame is |U| and
  p, each on its own colour scale, so the colour-bar ends carry the extremes,
  as in `dev-sequence-v2own` of October 27. All frames use one fixed window:
  the solver's `LLM_IMAGE_XRANGE=0,0.12` and `LLM_IMAGE_YRANGE=0,0.04`
  (`2026-10-27-solver/mpi/mpi_test.sbatch`). The note and the picture titles
  give step = time / 5×10⁻⁷ s, as in all earlier picture tests. The run's own
  step count and time step are not given.
- **Prompt.** `readable_request.STABILITY_V2OWN_SYSTEM_PROMPT` is new. Its text
  up to "not instructions." is the October 22 own-scale sequence prompt. It
  then asks whether the run shows signs of numerical instability, "for
  example values that oscillate from one cell to the next, a checkerboard
  pattern, or extremes that grow from one time to the next without a physical
  cause". It adds that moving vortices and other smooth changes of an
  unsteady flow are not by themselves signs of instability. The reply is
  `reason` (at most 300 characters), then `stability`: `stable`, `unstable`
  or `cannot_tell`. The reason comes first, as the description does in the
  sequence schema. Temperature 0, `max_tokens` 320, seed 20261021, no prompt
  cache, as in the earlier picture tests.
- **Labels.** A run that crashed is unstable. Its triples whose last frame is
  1 to 10 steps before the crash are scored as `unstable`, one triple per
  number of steps (7 for `central-dt4e-5`, which wrote only 9 states). The
  `early` triples end 12 to 460 steps (`central-dt2e-5`) or 12 to 24 steps
  (`central-dt3e-5`) before the crash. They are not scored; they show how
  early an answer turns. Runs that ended give `stable` triples, spread over
  each run. Every stable triple ends at least 100 steps before its run's last
  step, so each stable frame was followed by at least 100 more steps without
  a crash. 27 against 27, so a fixed answer gets 27 of 54.
- **Gaps.** In a crashed run the frames are 1, 2 or 3 steps apart, drawn at
  random (seed 20261028). In a run that ended they are 1 or 2 written states
  apart: 10 or 20 steps for the upwind runs, 50 or 100 for `central-dt5e-6`,
  1 or 2 ms (200 or 400 steps) for `developed`.
- **Stable runs.** The two upwind runs cover the Courant numbers of the
  crashed runs. `developed` is the flow all runs start from. `central-dt5e-6`
  uses the crashed runs' scheme at a small time step. Without it the stable
  class would be upwind pictures only, and a model could separate the classes
  by the scheme's look. Central differencing leaves cell-scale wiggles in this
  flow, and they show in its pictures.
- **Baselines.** The fixed answer, and two rules computed from the arrays in
  the key. The first is the peak |U| in the window, last frame over first.
  The second is the largest |U| difference across an interior face with both
  cells in the window, last frame over first. Each rule is reported at
  several thresholds. The report also gives the best single threshold, chosen
  on these same items, so it is an optimistic bound.

## What the pictures show

The pictures were looked at before any model ran; examples are in
[pictures/](pictures/).

- **The last state before each crash is plain to see.** The |U| colour bar
  runs to 84.63 m/s (`central-dt3e-5`), 3.049×10⁸ m/s (`central-dt4e-5`,
  `...steps00003-00006-00009-t3-U.png`) or 1.516×10⁴⁰ m/s (`central-dt2e-5`;
  p ±10⁴⁰ in `...steps00464-00465-00466-t3-p.png`). A small checkerboard
  cluster sits in the shear layer near the step corner, and the rest of the
  picture turns dark because the colour scale stretches.
- **A few steps earlier the sign is small.** It is a streak a few cells long
  near x = 10 to 16 %, y = 31 to 33 % of the window. In `central-dt2e-5` the
  colour-bar maximum also rises over steps 461 to 465: 41.3, 52.0, 86.4, 96.5,
  90.0 m/s (`...steps00461-00462-00463-t1-U.png` and `-t3-U.png`;
  `...steps00463-00464-00465-t3-U.png`; `central-dt3e-5`:
  `...steps00019-00022-00025-t3-U.png`).
- **Earlier states look like the stable runs.** In `central-dt4e-5` the state
  one step before the last (step 8) looked like a stable run's state. The
  largest |U| in the window falls from 36.97 m/s (step 1) to 36.61 m/s
  (step 8).
- **The stable central run has visible wiggles.** `central-dt5e-6` shows
  cell-scale stair steps, and in some frames a checkerboard-like patch at the
  bottom wall near x = 55 % (`...central-dt5e-6-steps01150-01200-01250-t3-U.png`).
  The upwind pictures are smooth (`...upwind-dt4e-5-steps00970-00980-00990-t3-U.png`).

## Results

All 280 requests (70 per model) were answered with valid JSON. Median prompt
tokens were 2,096 (Gemma) and 2,083 (Qwen). Median time per request on the
L40S was 1.92 s (12B), 1.55 s (26B-A4B), 3.57 s (31B) and 1.68 s (Qwen)
(`summary.json`).

Scored items (27 `unstable`, 27 `stable`):

| Answers from | Right / 54 | Unstable said unstable / 27 | Stable said stable / 27 | cannot_tell |
|---|---:|---:|---:|---:|
| Gemma 4 12B | 32 | 5 | 27 | 0 |
| Gemma 4 26B-A4B | 30 | 3 | 27 | 0 |
| Gemma 4 31B | 33 | 6 | 27 | 0 |
| Qwen3.5-35B-A3B | 32 | 5 | 27 | 0 |
| fixed answer | 27 | | | |
| peak \|U\| grows > 5 % | 30 | 6 | 24 | |
| peak \|U\| grows > 20 % | 33 | 6 | 27 | |
| largest \|U\| jump grows > 50 % | 38 | 11 | 27 | |
| largest \|U\| jump grows > 20 % | 36 | 14 | 22 | |

How early `unstable` is said (all 43 triples from the crashed runs, said
unstable / triples, by steps from the last frame to the crash):

| Steps to the crash | Triples | 12B | 26B-A4B | 31B | Qwen | peak \|U\| > 20 % | jump > 50 % |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| 2 to 3 | 6 | 1 | 0 | 1 | 1 | 1 | 2 |
| 4 to 6 | 9 | 1 | 0 | 2 | 1 | 2 | 4 |
| 7 to 10 | 9 | 0 | 0 | 0 | 0 | 0 | 2 |
| 11 to 25 | 7 | 0 | 0 | 0 | 0 | 0 | 0 |
| 26 to 100 | 4 | 0 | 0 | 0 | 0 | 0 | 0 |
| over 100 | 5 | 0 | 0 | 0 | 0 | 0 | 0 |

- **By run.** In `central-dt3e-5` and `central-dt4e-5` every model said
  `unstable` only for the triple ending 1 step before the crash. In
  `central-dt2e-5` the earliest `unstable` came 4 steps before the crash
  (12B), 1 step (26B-A4B), 5 steps (31B) and 5 steps (Qwen; Qwen also said
  `stable` for the triple ending 4 steps before). The four stable runs drew
  no `unstable` answer from any model (`independent-recount.json`:
  `first_unstable_answer_by_run`, `by_run`).
- **The models read the colour-bar numbers.** On the blown-up frames the
  reasons cite the extremes. 26B-A4B: "explode to extreme, unphysical
  magnitudes (e.g., |U| ~ 10^40 m/s ...)". 31B on `central-dt2e-5` steps 461
  to 463: "increases rapidly from 41.31 m/s to 86.42 m/s over a very short
  time interval (0.00004 s)". On `central-dt2e-5` steps 463 to 465 the
  largest |U| is 86.4, 96.5 and 90.0 m/s in the three frames, more than twice
  the 39.7 m/s ten steps earlier, and all four said `stable`. Qwen:
  "Velocity max decreases slightly (86→90→90 m/s) ... No instability signs".
  On the stable central run, which has cell-scale wiggles, all 24 answers
  (6 triples, 4 models) say `stable`, and every reason says there is no
  checkerboard pattern.
- **Pictures against numbers.** No model said `unstable` where the peak |U|
  grew by 20 % or less and the largest cell-to-cell jump by 50 % or less
  (`unstable_items_said_unstable_where_peak_rule_20_and_jump_rule_50_say_stable`
  is empty for all four). The smallest peak growth among the triples a model
  called `unstable` is 30.8 % (`central-dt2e-5` steps 460 to 462: 31B and
  Qwen). In five triples the largest jump grew 1.5 to 3.6 times while the
  peak changed by less than 4 %: `central-dt2e-5` steps 457 to 461 and 454 to
  460, and `central-dt3e-5` steps 16 to 22, 19 to 25 and 18 to 20. Every model
  said `stable` for all five.
- **A best threshold on these items is not a fair detector.** The best single
  threshold on the peak |U| ratio is 0.9936 (45 of 54); above 1 it is 1.001
  (38 of 54). These cut-offs work because the crashed runs' triples span 2 to
  6 steps, so their peaks hardly change. The stable triples span 20 to 800
  steps, so their peaks move by a few percent, mostly downward (the peak
  column of the reports' item table). That is a property of how the triples
  were drawn, not of instability. The best jump threshold, 1.355 (39 of 54),
  is also chosen on the same items.

## Files

| Path | What it contains |
|---|---|
| `test-set/design.json` | The build input: runs, roles, early steps-to-crash, window |
| `test-set/manifest.json` | The test set's manifest: every request's hash and design entry, label rule, runs (scheme, Δt, steps, crash step, Courant range), code hashes, build arguments |
| `test-set/truth.private.json` | The answer key: label, scored or not, steps to the crash, the run's own steps, and per frame the Courant number, extremes and largest jumps in the window, and the largest \|U\| over the domain |
| `job/build_instability_set.sbatch`, `job/build-instability-set-24929495.out` | The build job and its output |
| `job/window-test-24929533.out`, `job/window-test-24929534.out` | The two GPU jobs' outputs |
| `results/<job>/<model>/run.json` | Model alias, server note, test-set hashes |
| `results/<job>/<model>/instability-v2own/metrics.jsonl`, `summary.json` | One line per request: parsed answer and reason, score, request hash, tokens, server timings, wall time; the runner's summary |
| `reports/<job>.md` | `instability_test.py report` (code of `c9a1ba1`) on the job's results |
| `reports/<job>.job.md` | The report the job wrote (code of `8d6a10a`): the same counts; it writes \|U\| unescaped in table cells, which splits those rows, and lacks the growth-only threshold and the jump column of the table by run |
| `runtime/<job>/` | llama.cpp build, modules, GPU at the start, `sha256.txt` (llama.cpp files, test set, scripts); `server/<model>.cmd`, `.log.gz`, `.models.json`, `.gpu.txt` |
| `flow/run_*.sbatch`, `flow/run-*.out` | The flow jobs: today's reruns (24929408, 24929449, 24929452), the crashed runs (24929300), and the October 27 runs they repeat (24903182 with its script; 24903082, whose script was later overwritten, only its output) |
| `flow/cases/` | `controlDict` of each run, the two `fvSchemes`, `fvSolution`, `transportProperties`, `turbulenceProperties`, `0/U`, `0/p` (the same in all seven cases) |
| `flow/logs/` | gzip copies of the three crashed runs' `log.pimpleFoam` |
| `flow/summarize_logs.py`, `flow/logs-summary.json` | Steps, end and Courant numbers of the seven runs' logs; the whole series for the crashed runs |
| [pictures/](pictures/) | Pictures as sent, decoded from request bodies (named `<set>-<item>-t<time>-<field>.png`) |
| [independent-recount.py](independent-recount.py), `independent-recount.json` | A recount without the test code (below) |
| [manifest.json](manifest.json) | Origins, sizes and hashes of the files here |

The full test set (70 request bodies, the frames with their arrays, 190 MB)
is on the cluster at
`/cluster/medbow/gscratch/syome/github_repos/picture-test-20261021/instability-test-20261028`.
The jobs' archives, with every raw reply, are at
`/cluster/medbow/gscratch/syome/github_repos/PythonFOAM-inst/results/window-test-24929533.tar.gz`
and `window-test-24929534.tar.gz` (with `.sha256`). The runs' time
directories are in `flow-states-20261027/unstable/`, `flow-states-20261028/`
and `flow-states-20261022/long-100ms` under
`/cluster/medbow/gscratch/syome/github_repos/`. None of these is in a release.

## Recount

`python3 independent-recount.py` uses no third-party packages. From
`metrics.jsonl` and the answer key only, it recomputes every count cell of
the two reports:

- answered and right;
- the six answer cells per model and per numeric rule;
- the table by steps to the crash, and the table by run;
- the per-item marks;
- the best thresholds.

It computes the numeric ratios again from the per-frame numbers. It also
checks that the key's labels follow the rule (scored when 1 to 10 steps
before the crash; stable triples from runs that ended, at least 100 steps
before their end). Result: 0 key problems, and 1,410 report cells checked,
none different. It does not check the token and time columns.

## Not tested

- **Instability outside the window.** All three crashes start beside the step
  corner, inside the window. An instability that starts elsewhere would not
  be in the pictures. In `central-dt2e-5` the largest |U| over the domain
  (75.3 to 75.6 m/s in the frames of steps 453 to 462) is outside the window,
  and the pictures do not show it.
- **Other picture settings.** Shared colour scales, other image-token limits
  (all requests used 256 per image), the solver's v1 pictures, and a
  numbers-only prompt were not tried.
- **The solver callback.** It does not send this request; `LLM_MODE` has no
  stability value.
- **Repeats, other meshes, 3D cases, other solvers.** Each request was
  answered once, at temperature 0.
- **Independence.** The 70 triples come from 3 crashed and 4 stable runs and
  share frames, so they are not independent cases. The crashed runs are all
  one scheme, central differencing, switched on in a developed upwind flow.
- **Time between frames.** It differs between the classes (see the best
  threshold above). A model that called fast change `unstable` would have
  been penalised on the stable triples, not helped. Equal spacing was not
  tried.

## Notes

- Code that ran in the two GPU jobs: every script hashed in
  `runtime/<job>/sha256.txt` equals `8d6a10a` (40 of 40 files in each job).
  The test set was built with the same code; its manifest's 8 code hashes
  equal `8d6a10a`. The reports in `reports/<job>.md` were made afterwards
  with `c9a1ba1`, which changes only the report.
- Six of 12B's and five of Qwen's reasons stop at the 300-character limit of
  the schema. The answer word still follows them.
- `flow/run-central-long-24929408.out` ends with "0.13/U differs between the
  cases". Neither copy reached t = 0.13 s, so there was no file to compare.
- `truth.private.json` means withheld from the model input, not private
  personal information.
- The records contain cluster paths and server process ids as provenance.
