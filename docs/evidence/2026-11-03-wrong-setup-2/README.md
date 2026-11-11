# November 3 evidence: wrong-setup test 2

The first wrong-setup test, of October 30, had five wrong runs, one per kind of change, and eight frames of
each that look alike. Besides the constant baseline, its only competitor was a rule on one number, the peak |U|. This test has 29
pairs of pimpleFoam runs of the 2D backward-facing step case. Each pair is one base setup drawn at
random. Run as written it is the normal run; run with one change it is the wrong run. One run is one
sample. The [plan](PLAN.md), the scoring, the baselines and the request set's manifest were committed
at `97c3c41` and `91544e6` before any model request was sent. The report is
[results-20261103.md](../../results-20261103.md).

Gemma 4 31B, as the 4-bit QAT Q4_0 file, answered 1,044 requests. Each request carries the pictures
of one frame, |U| and p, and a short text note. In the stated condition the note gives the intended
inlet speed and viscosity; in the blind condition it does not. Each condition ran at the model's
sampling temperature 0 and at 0.7 with two seeds, on three frames of each run. t0 is temperature 0;
t07a and t07b are temperature 0.7 with seeds a and b.

An answer is right when it calls a normal run `consistent` or a wrong run `inconsistent`. It is right
for the right reason when the cause it names is also the run's own change, `none` for a normal run.
The labels baseline of report.md is a logistic regression on the colour-bar numbers and the stated
setup, with five inputs. The colour-bar numbers are the four numbers printed at the ends of the two
colour bars. Four inputs come from them: U max and U min of the |U| colour bar divided by the stated
speed, and p min and p max of the p colour bar divided by the square of the stated speed. The fifth
is the logarithm of the stated viscosity. The regression is fitted while leaving one pair out at a time.

In short (counts from [results/report.md](results/report.md) and [Reasons](#reasons)):

- Primary result, stated condition, temperature 0, last frame of each run: 31B is right for 44 of 58.
  The baseline with most right answers, the labels baseline, is right for 45. They disagree on 27
  runs, 14 for the baseline and 13 for the model: exact McNemar p = 1. By the plan's criterion, p < 0.05, the
  conclusion "the model does better than the rules" is not shown.
- 31B catches wrong runs: 26 of 29. By kind, inlet speed 8 of 8, viscosity 8 of 8, inlet profile 6
  of 6, walls 4 of 7. The labels baseline catches 17: walls 7 of 7, speed 4, viscosity 2, profile 4.
- 31B raises false alarms: 11 of 29 normal runs are answered `inconsistent`. Nine of the eleven
  reasons say the picture shows no backward-facing step: "no step geometry (white area)", "no
  sudden expansion or separation zone". The plotted window begins at the step's corner, so no picture of
  this test has a white area. The same two phrases appear in 4 of the 26 reasons on caught wrong
  runs, and 7 of those 26 say there is no step. The labels baseline has one false alarm.
- Right for the right reason: 27 of 58. These are the 18 normal runs answered `consistent` and 9 wrong runs,
  speed 7 and walls 2. No viscosity run got the cause `viscosity`; the causes named were walls 3,
  other 3, inlet speed 1, inlet profile 1. All 6 profile runs got `inlet_speed`, with the colour bar's maximum
  below the stated speed as the reason.
- Blind, without the stated numbers, 31B answers `inconsistent` on 51 of 58 frames and is right for
  28, below the constant baseline's 29. The pixels-only baseline, which reads neither the stated nor the colour-bar
  numbers, gets 44.
- Sampling temperature 0.7 changes 10 of the 58 stated answers with each of the two seeds, and both
  seeds score lower: 34 and 38 of 58.
- The earlier frames, steps 6000 and 7000, stated, temperature 0: 37 and 42 of 58 right. All 174
  stated frames at temperature 0: 123 right.

## Jobs

| Job | What | Where | Time (MST, 2026-11-03) |
|---|---|---|---|
| 25106856 (array 0 to 11), 25106882 (task 12) | The 13 pilot runs | CPU, `teton` (ttest01, ttest02) | 20:07 to 20:18 |
| 25106926 (array 0 to 59) | The 60 pimpleFoam runs of the design, one task each; task 11 (B06-W) diverged | CPU, `teton` (ttest01 to ttest04, t286) | 20:21 to 20:49 |
| 25107036 | `flow-check`, `build`, `check`, `baselines` and `contact` | CPU (ttest01) | 20:49 to 20:54 |
| 25107037 | First GPU job; stopped after 42 s because the runner looked for a manifest key that was missing, before any request | NVIDIA RTX A6000 (mba6000-001) | 21:12 to 21:13 |
| 25107731 | Gemma 4 31B on the 1,044 requests (`window_test.slurm`, `PICTURE_TEST_SCRIPT=wrong_setup_test2.py`) | NVIDIA RTX A6000 (mba6000-001) | 21:14 to 22:26 |

Start and end times are in [job/sacct.txt](job/sacct.txt). The report and the reasons were made on a
login node on 2026-11-04 with `wrong_setup_test2.py report`. The note inside test-set/manifest.json
dates the added key "2026-11-03 21:20". The commit that holds it, `3363525`, is from 21:14:12 MST, so
the note's time is wrong. Commits: the plan at `97c3c41`, the unit tests at `33553c4`, B06 dropped
at `3bc6d51`, the request set's manifest and the baselines at `91544e6`, and the manifest key at
`3363525`. That last commit came after job 25107037 and before 25107731. The job scripts are in [jobs/](jobs/).

## Runs

All runs are laminar pimpleFoam runs on OpenFOAM v2212, with PISO and upwind for div(phi,U), on the
mesh of 20,540 cells. They use the settings of the first test: a fixed Δt of 5×10⁻⁶ s, 8,000 steps from
t = 0.1 s to t = 0.14 s, every 500th step written. Each run starts from a written state of the developed
flow of October 22, between t = 0.06 and 0.1 s, copied to a directory named `0.1`. The inlet speed of the base is set
on the inlet patch and the viscosity in `transportProperties`. The developed flow itself ran at
32.2 m/s and 1.56×10⁻⁵ m²/s. The step corner is at x = 0, y = 0.0127 m. The window is x 0 to 0.12 m, y 0 to 0.04 m. The step's
face is therefore the window's left edge below 32 % of its height, and the inlet and the upper wall lie
outside the window.

`flow-check` ([flow-check.json](flow-check.json)) accepted all 58 runs: each ended with `End` after
8,000 steps, and the last written U and `transportProperties` hold the design's entries. The largest
Courant number of a whole run is above 1 in 21 normal and 24 wrong runs. In 44 of them the maximum
comes in steps 2 to 41. The start state is the developed flow at 32.2 m/s and the base's inlet speed
differs, so the first steps adjust. B10-W, with the lower wall slipping, reaches 1.51 at step 5371.
From the first frame on, steps 6000 to 8000, the normal runs stay at or below 0.43 and ten wrong runs
lie above 0.5. These are the seven slip-wall runs at 0.81 to 2.05, viscosity ×100 at 23.5, ×300 at 172,
and inlet speed ×1.5 at 0.505. The table gives each run with its answers at step 8000 in the six sets; the step of the whole-run Courant
maximum is in parentheses. t0 is
temperature 0; t07a and t07b are temperature 0.7 with seeds a and b. `C` is `consistent`, `I` is
`inconsistent`, and the word after the colon is the cause the model named.

| Run | Stated speed, ν (m²/s) | Change | Co, whole run (step) | Co from step 6000 | stated t0 | stated t07a | stated t07b | blind t0 | blind t07a | blind t07b |
|---|---|---|---:|---:|---|---|---|---|---|---|
| B01-N | 37.3 m/s, 2.3e-05 | none | 1.59 (2) | 0.383 | C | I:other | I:walls | I:other | I:other | I:other |
| B01-W | 37.3 m/s, 2.3e-05 | lowerWall and upperWall slip for noSlip | 1.6 (2) | 0.806 | C | C | C | C | C | I:other |
| B02-N | 39.4 m/s, 2.4e-05 | none | 2.32 (2) | 0.387 | C | C | I:walls | I:other | I:walls | I:walls |
| B02-W | 39.4 m/s, 2.4e-05 | nu 0.00012 m²/s for 2.4e-05 m²/s | 2.25 (2) | 0.327 | I:other | I:walls | I:walls | I:other | I:other | I:other |
| B03-N | 29.2 m/s, 2.44e-05 | none | 0.981 (2) | 0.282 | I:other | I:other | C | I:other | I:other | I:walls |
| B03-W | 29.2 m/s, 2.44e-05 | lowerWall and upperWall slip for noSlip | 0.998 (4931) | 0.893 | I:walls | I:walls | I:walls | I:walls | I:walls | I:other |
| B04-N | 38.0 m/s, 2.2e-05 | none | 1.82 (2) | 0.39 | C | I:other | C | I:walls | I:walls | I:walls |
| B04-W | 38.0 m/s, 2.2e-05 | nu 0.0022 m²/s for 2.2e-05 m²/s | 43.9 (41) | 23.5 | I:inlet profile | I:inlet speed | C | I:inlet direction | I:other | I:inlet direction |
| B05-N | 24.8 m/s, 1.66e-05 | none | 2.38 (2) | 0.236 | I:other | I:other | I:walls | I:other | I:other | I:other |
| B05-W | 24.8 m/s, 1.66e-05 | inlet velocity 19.84 m/s for 24.8 m/s | 4.07 (3) | 0.178 | I:inlet speed | I:inlet speed | I:other | I:other | I:walls | I:other |
| B07-N | 28.9 m/s, 2.08e-05 | none | 1.05 (2) | 0.285 | C | I:other | C | I:other | I:walls | I:inlet direction |
| B07-W | 28.9 m/s, 2.08e-05 | nu 0.000624 m²/s for 2.08e-05 m²/s | 0.983 (3) | 0.202 | I:walls | I:walls | I:other | I:other | I:walls | I:other |
| B08-N | 33.5 m/s, 2.1e-05 | none | 0.367 (2) | 0.345 | C | C | I:other | I:walls | I:inlet direction | C |
| B08-W | 33.5 m/s, 2.1e-05 | inlet velocity 23.45 m/s for 33.5 m/s | 2.88 (2) | 0.21 | I:inlet speed | I:inlet speed | I:inlet speed | I:walls | I:other | I:inlet direction |
| B09-N | 39.1 m/s, 1.37e-05 | none | 2.18 (2) | 0.426 | C | C | C | C | C | I:other |
| B09-W | 39.1 m/s, 1.37e-05 | lowerWall slip for noSlip | 2.18 (2) | 1.02 | I:other | I:walls | I:walls | I:other | I:walls | I:inlet direction |
| B10-N | 35.2 m/s, 1.17e-05 | none | 0.991 (2) | 0.389 | C | I:start state | C | C | C | I:viscosity |
| B10-W | 35.2 m/s, 1.17e-05 | lowerWall slip for noSlip | 1.51 (5371) | 1.26 | C | C | C | I:other | I:other | I:inlet direction |
| B11-N | 30.5 m/s, 1.68e-05 | none | 0.563 (2) | 0.311 | C | I:start state | I:walls | I:other | I:walls | I:walls |
| B11-W | 30.5 m/s, 1.68e-05 | the lowest 0.75 of the inlet faces at velocity 0, the rest at 30.5 m/s | 8.77 (3) | 0.133 | I:inlet speed | I:inlet speed | I:inlet speed | C | I:other | I:walls |
| B12-N | 27.0 m/s, 2.32e-05 | none | 1.69 (2) | 0.261 | I:other | I:other | I:start state | I:walls | I:viscosity | I:walls |
| B12-W | 27.0 m/s, 2.32e-05 | lowerWall slip for noSlip | 1.69 (2) | 1.08 | I:other | C | I:walls | I:walls | I:walls | I:other |
| B13-N | 24.9 m/s, 2.42e-05 | none | 2.37 (2) | 0.232 | C | I:walls | C | I:walls | I:inlet direction | I:other |
| B13-W | 24.9 m/s, 2.42e-05 | inlet velocity 2.49 m/s for 24.9 m/s | 11 (3) | 0.223 | I:inlet speed | I:inlet speed | I:inlet speed | I:other | I:other | I:walls |
| B14-N | 31.4 m/s, 1.22e-05 | none | 0.389 (476) | 0.343 | C | C | C | I:other | I:walls | I:other |
| B14-W | 31.4 m/s, 1.22e-05 | the lowest 0.25 of the inlet faces at velocity 0, the rest at 31.4 m/s | 2.86 (2) | 0.219 | I:inlet speed | I:inlet speed | I:inlet speed | I:walls | I:walls | I:inlet direction |
| B15-N | 20.2 m/s, 1.38e-05 | none | 3.93 (3) | 0.208 | I:other | I:walls | I:other | I:other | I:walls | I:other |
| B15-W | 20.2 m/s, 1.38e-05 | the lowest 0.5 of the inlet faces at velocity 0, the rest at 20.2 m/s | 7.86 (3) | 0.135 | I:inlet speed | I:inlet speed | I:inlet speed | I:walls | C | C |
| B16-N | 31.2 m/s, 1.82e-05 | none | 0.423 (483) | 0.321 | I:other | I:start state | I:walls | I:walls | I:walls | I:walls |
| B16-W | 31.2 m/s, 1.82e-05 | nu 5.46e-05 m²/s for 1.82e-05 m²/s | 0.413 (505) | 0.249 | I:other | I:other | I:walls | I:other | I:other | I:other |
| B17-N | 24.3 m/s, 2.17e-05 | none | 2.55 (2) | 0.231 | C | C | C | I:other | I:other | I:inlet direction |
| B17-W | 24.3 m/s, 2.17e-05 | inlet velocity 12.15 m/s for 24.3 m/s | 7.05 (3) | 0.141 | I:inlet speed | I:inlet speed | I:inlet speed | I:other | I:other | I:walls |
| B18-N | 39.2 m/s, 1.78e-05 | none | 2.28 (2) | 0.395 | C | C | I:start state | I:viscosity | I:other | I:other |
| B18-W | 39.2 m/s, 1.78e-05 | inlet velocity 11.76 m/s for 39.2 m/s | 7.2 (3) | 0.139 | I:inlet speed | I:inlet speed | I:inlet speed | C | I:inlet direction | I:inlet direction |
| B19-N | 33.1 m/s, 1.85e-05 | none | 0.349 (24) | 0.349 | I:other | I:inlet speed | I:other | I:walls | I:walls | I:walls |
| B19-W | 33.1 m/s, 1.85e-05 | inlet velocity 49.65 m/s for 33.1 m/s | 5.62 (3) | 0.505 | I:inlet speed | I:inlet speed | I:inlet speed | I:other | I:walls | I:other |
| B20-N | 24.1 m/s, 1.56e-05 | none | 2.6 (2) | 0.221 | I:walls | I:other | I:other | I:walls | I:other | I:walls |
| B20-W | 24.1 m/s, 1.56e-05 | nu 0.000156 m²/s for 1.56e-05 m²/s | 2.55 (3) | 0.195 | I:walls | I:other | I:other | I:other | I:other | I:other |
| B21-N | 24.6 m/s, 2e-05 | none | 2.44 (2) | 0.226 | I:walls | I:inlet direction | C | I:walls | I:other | I:inlet direction |
| B21-W | 24.6 m/s, 2e-05 | nu 2e-06 m²/s for 2e-05 m²/s | 2.45 (2) | 0.276 | I:other | I:other | I:start state | I:walls | I:other | I:other |
| B22-N | 28.4 m/s, 1.93e-05 | none | 1.24 (2) | 0.283 | I:other | I:walls | I:other | I:walls | I:walls | I:viscosity |
| B22-W | 28.4 m/s, 1.93e-05 | nu 0.00579 m²/s for 1.93e-05 m²/s | 379 (25) | 172 | I:inlet speed | I:inlet speed | I:inlet speed | I:other | I:other | I:other |
| B23-N | 37.8 m/s, 2.23e-05 | none | 1.83 (2) | 0.38 | I:other | I:walls | I:other | I:walls | I:walls | I:other |
| B23-W | 37.8 m/s, 2.23e-05 | lowerWall slip for noSlip | 1.83 (2) | 0.827 | I:walls | I:walls | I:walls | I:walls | I:walls | I:other |
| B24-N | 38.9 m/s, 1.86e-05 | none | 2.11 (2) | 0.41 | I:other | I:other | I:walls | I:other | I:walls | I:other |
| B24-W | 38.9 m/s, 1.86e-05 | the lowest 0.25 of the inlet faces at velocity 0, the rest at 38.9 m/s | 1.1 (2) | 0.292 | I:inlet speed | I:inlet speed | I:walls | I:walls | I:other | I:other |
| B25-N | 21.5 m/s, 1.41e-05 | none | 3.46 (3) | 0.208 | C | C | C | I:walls | I:walls | I:walls |
| B25-W | 21.5 m/s, 1.41e-05 | the lowest 0.5 of the inlet faces at velocity 0, the rest at 21.5 m/s | 7.61 (3) | 0.152 | I:inlet speed | I:inlet speed | I:inlet speed | C | C | I:walls |
| B26-N | 27.3 m/s, 2.18e-05 | none | 1.59 (2) | 0.267 | C | C | C | I:other | C | I:other |
| B26-W | 27.3 m/s, 2.18e-05 | the lowest 0.75 of the inlet faces at velocity 0, the rest at 27.3 m/s | 9.1 (3) | 0.139 | I:inlet speed | I:inlet speed | I:inlet speed | I:other | I:other | I:walls |
| B27-N | 26.6 m/s, 1.56e-05 | none | 1.82 (2) | 0.263 | C | I:walls | C | C | C | I:other |
| B27-W | 26.6 m/s, 1.56e-05 | inlet velocity 33.25 m/s for 26.6 m/s | 0.405 (592) | 0.364 | I:other | I:other | I:other | I:walls | I:other | I:inlet direction |
| B28-N | 34.9 m/s, 1.94e-05 | none | 0.819 (2) | 0.37 | C | I:walls | C | I:walls | I:other | I:walls |
| B28-W | 34.9 m/s, 1.94e-05 | nu 0.000388 m²/s for 1.94e-05 m²/s | 0.744 (3) | 0.247 | I:walls | I:walls | I:walls | I:other | I:other | I:other |
| B29-N | 20.3 m/s, 1.34e-05 | none | 3.9 (3) | 0.21 | C | I:walls | I:walls | I:other | I:other | I:other |
| B29-W | 20.3 m/s, 1.34e-05 | inlet velocity 4.06 m/s for 20.3 m/s | 10.3 (3) | 0.34 | I:inlet speed | I:inlet speed | I:inlet speed | I:other | I:other | I:other |
| B30-N | 23.5 m/s, 1.44e-05 | none | 2.8 (2) | 0.239 | C | C | I:other | I:other | C | I:other |
| B30-W | 23.5 m/s, 1.44e-05 | lowerWall and upperWall slip for noSlip | 2.8 (2) | 2.05 | C | C | C | I:inlet direction | I:walls | C |

## Design

The plan is [PLAN.md](PLAN.md); [design.json](design.json) is the drawn design with the dropped pair
under `dropped_pairs`. The changes: inlet speed factors 0.1, 0.2, 0.3, 0.5, 0.7, 0.8, 1.25 and 1.5;
viscosity factors 0.1, 3, 5, 10, 20, 30, 100 and 300; `lowerWall` `slip` in 4 pairs and both walls
`slip` in 3; the lowest 0.25, 0.5 or 0.75 of the inlet faces at velocity 0, each twice. The ×1000
viscosity run diverged, as the plan's Deviations records. Inlet direction and start state were in the draft and were dropped after the
pilot, which is recorded in [pilot/](pilot/). Neither leaves a visible trace in the window.

- **Pictures.** Two single-field pictures of one written state, |U| and p, each on its own colour scale,
  in the solver's window. These are the v2 pictures of `picture_test.render_v2`. Steps 6000, 7000 and
  8000 of each run: 174 frames.
- **Prompt.** The system prompt says: "The case is a 2D incompressible laminar flow over a
  backward-facing step: a uniform inlet in +x upstream of the plotted part, no-slip stationary walls,
  a zero-gradient outlet, started from a developed state of this flow." In the stated condition it
  goes on: "The note gives the intended inlet speed and kinematic viscosity. Judge whether the
  pictures are consistent with this setup." In the blind condition: "The intended inlet speed and
  viscosity are not given. Judge whether the pictures are consistent with a run of this case set up
  as described." The rest of the prompt is the same in both. It asks for `reason`, under 300 characters; `assessment`, one of `consistent`, `inconsistent` and
  `cannot_tell`; and `cause`, one of `none`, `inlet_speed`, `viscosity`, `walls`, `inlet_profile`,
  `inlet_direction`, `start_state`, `other`. In the stated condition the note holds
  `intended_setup` with the base's inlet speed and viscosity. The blind note has no such field, and
  its task line says "the case as described" where the stated one says "the intended setup". Both
  runs of a pair get the same text.
- **Request settings.** `max_tokens` 320, no prompt cache, `seed` 20261103 for t0, 20261107 for t07a
  and 20261108 for t07b; temperature 0 or 0.7. Server: llama.cpp b11429, context 4096, batch and ubatch 512,
  an image-token limit of 256 per image, one slot, which takes one request at a time
  ([results/server-31b.cmd](results/server-31b.cmd)).
- **Scoring, fixed before any answer.** A normal run answered `consistent` or a wrong run
  `inconsistent` is right; `cannot_tell` is wrong on both. Right for the right reason adds that the
  cause is the run's own, `none` for a normal run. The primary score is on the step 8000 frames. Exact
  McNemar test against the baseline with most right answers, and a bootstrap over pairs for the 95 %
  interval of the share right. By the plan, the conclusion "the model does better than the rules"
  needs p < 0.05 on the primary frames in the stated condition at t0. Anything else is reported as
  "not shown".
- **Baselines**, computed by `wrong_setup_test2.py baselines` before the GPU jobs
  ([baselines.json](baselines.json)). The constant baseline answers `consistent` on every run. The
  peak |U| rule of the first test answers `consistent` when peak |U| lies between 1 and 2 times the
  stated speed. Three logistic regressions are fitted with leave-one-pair-out. One, the labels
  baseline, uses five numbers: U max and U min divided by the stated speed, p min and p max divided by its square, and the
  logarithm of the stated viscosity. Another uses those five plus three pixel shares, and the last uses
  the pixel shares alone.
  The first and third pixel shares are the parts of the |U| and the p picture drawn in the
  lowest 15 % of their colour scales. The second is how far along x such |U| pixels reach in the
  lowest quarter of the picture, as a share of its width.

## Leak check

`build` writes [test-set/leak-check.json](test-set/leak-check.json) and `check` runs before any GPU
time: 1,044 requests, no problem. All 174 request bodies of a set are the same text once the picture data and
the step, time and `intended_setup` fields are removed. Within a pair the two runs
have the same stated numbers, so any rule on the request text gets exactly 29 of 58 in each
condition. No run name is in any request. The answer key is in the [release](https://github.com/seungminyome/PythonFOAM/releases/tag/wrong-setup-2-2026-11-03), and its SHA-256 is
`truth_sha256` in [test-set/manifest.json](test-set/manifest.json); [test-set/truth.private.sha256](test-set/truth.private.sha256) holds its first 16 hex digits. Prompt tokens per request were 1,045 to
1,049 in the three stated sets and 1,013 to 1,014 in the three blind sets.

## What the pictures show

[contact-8000.png](contact-8000.png) has the step 8000 pictures of all 58 runs. The pictures were
opened before the plan was fixed only for the pilot runs ([pilot/](pilot/)); no model saw a pilot
frame.

- **Normal runs.** A fast stream above y about 35 to 40 % of the window, below it a slow wake with
  dark lines and spots, and a row of low-pressure cores in p.
- **Slip walls.** Smooth layered bands instead of spots; with `lowerWall` slip the flow along the
  bottom edge is not dark. The |U| maximum is as in a normal run; the |U| minimum is 0.026 to
  0.16 m/s in six of the seven runs, against at most 0.0061 m/s in a normal run.
- **Viscosity ×0.1.** Like a normal run, with more and smaller spots and low-pressure cores.
- **Viscosity ×3 to ×30.** Smooth layers, no spots, a smooth p. ×100 and ×300 are not developed
  flows. The ×300 run's colour bar ends at 359 m/s against a stated 28.4 m/s. The ×300 pictures
  show a jet along the bottom. The ×300 run ended normally after 8,000 steps. Its largest
  Courant number, 379, came at step 25.
- **Inlet speed and inlet profile.** The pattern of a normal run; the colour-bar numbers differ from
  the stated speed. The profile change does not reach the window as a shape; it shows as a lower
  flow rate.
- No picture has a white area: the window starts at the step's corner.

## Results

All 1,044 requests were answered with valid JSON, none with `cannot_tell` and none with an error.
Median time per answer on the A6000 was 4.00 s; the model time of the job was 70.0 min of 71.5.
[results/report.md](results/report.md) is the report of `wrong_setup_test2.py report`;
[results/reasons.jsonl](results/reasons.jsonl) lists each `inconsistent` answer on a wrong run's primary
frame in all six sets, 154 rows, with its reason,
the run's change and the cause named. The raw answers are in
`results/<set>/metrics.jsonl`.

Primary frames (58), right, and wrong runs caught by kind of change:

| Answers from | Stated | Blind | Normal right (stated, of 29) | Speed (of 8) | Viscosity (of 8) | Walls (of 7) | Profile (of 6) |
|---|---:|---:|---:|---:|---:|---:|---:|
| constant | 29 | 29 | 29 | 0 | 0 | 0 | 0 |
| peak \|U\| rule | 43 | | 29 | 6 | 2 | 0 | 6 |
| labels | 45 | 45 | 28 | 4 | 2 | 7 | 4 |
| labels + pixels | 44 | 44 | 25 | 4 | 4 | 7 | 4 |
| pixels only | 44 | 44 | 25 | 4 | 5 | 7 | 3 |
| 31B t0 | 44 | 28 | 18 | 8 | 8 | 4 | 6 |
| 31B t07a | 34 | 31 | 9 | 8 | 8 | 3 | 6 |
| 31B t07b | 38 | 28 | 13 | 8 | 7 | 4 | 6 |

The Speed, Viscosity, Walls and Profile columns are for the stated condition. Blind, 31B t0 catches speed 7, viscosity 8,
walls 6 and profile 4 of the wrong runs and answers 3 of 29 normal runs `consistent`. The regressions
that use the stated numbers are the same in both conditions by construction. The peak |U| rule needs the
stated speed. The plan scores it in the stated condition only, so its Blind cell is empty.

Stated, temperature 0, step 8000, 31B is compared with two baselines. Against the labels baseline,
13 frames only the model has right and 14 only the baseline (p = 1). The 95 % bootstrap interval of
the model's share right is 0.67 to 0.84, the baseline's 0.67 to 0.88. Against the constant baseline,
the model is right on 26 frames the constant is not, the wrong runs it catches. The constant is right
on 11 frames the model is not, the false alarms. Computed from the answers, p = 0.020. The report's constant row compares the constant with the
labels baseline, 17 against 1, p = 0.000145.

Right per step (of 58), stated and blind:

| Set | 6000 | 7000 | 8000 |
|---|---:|---:|---:|
| stated t0 | 37 | 42 | 44 |
| stated t07a | 37 | 32 | 34 |
| stated t07b | 35 | 43 | 38 |
| blind t0 | 29 | 28 | 28 |
| blind t07a | 30 | 27 | 31 |
| blind t07b | 28 | 28 | 28 |

At step 8000 all three stated sets give the same assessment on 41 of 58 frames, t0 and t07a on
48, t0 and t07b on 48. Blind, in the same order, the counts are 46, 53 and 48.

## Reasons

Read from `results/wrong-setup2-stated-t0/metrics.jsonl`, step 8000:

- Of the 11 false alarms, 9 reasons say there is no backward-facing step in the picture: "no step
  geometry (white area)", "no sudden expansion or separation zone", "not constrained by a
  backward-facing step". One says the pressure field shows checkerboarding, one that the separation
  zone is missing without saying the step is missing. The causes named are `other` for 9 and `walls` for 2.
- All 18 normal runs answered `consistent` name a separation or recirculation zone behind a step;
  12 of them also compare the maximum velocity with the stated speed. 6 of these 12 give a
  number: 4 the colour bar's maximum, 2 the stated speed alone.
- The 8 inlet-speed runs: 7 reasons compare the colour bar's maximum with the stated speed. The
  ×1.25 run (B27-W) is caught with the false alarms' sentence, "no step geometry (white area)",
  cause `other`.
- The 6 inlet-profile runs: all reasons compare the colour bar's maximum with the stated speed and
  name `inlet_speed`.
- The 8 viscosity runs: ×3, ×5 and ×0.1 "do not exhibit the characteristic separation and
  recirculation zone", cause `other`; ×10, ×20 and ×30 "uniform flow" or "no backward-facing step",
  cause `walls`; ×100 "a jet-like structure", `inlet_profile`; ×300 the 359 m/s maximum, `inlet_speed`.
  None names viscosity.
- The 7 slip-wall runs: 4 caught, 2 with cause `walls` and 2 with `other`, "a simple channel". The 3
  missed runs, both walls slip twice and lower wall once, are answered with "a recirculation zone and
  reattachment after a step" and "consistent with a backward-facing step flow at the given Reynolds
  number", with a sentence on the pressure field between them.

## Checks outside the design

- A threshold on the largest Courant number from the first frame on flags 10 of the 29 wrong runs with
  no false alarm. The threshold lies between 0.43, the normal runs' largest, and 0.5. It flags all 7
  slip-wall runs, viscosity ×100 and ×300 and inlet speed ×1.5. It needs the solver log, not a
  picture, and it was chosen after the counts were seen.
- The whole-run Courant number of the first test flagged three of its five wrong runs with no false
  alarm. Here it is above 1 in 21 of 29 normal runs, because each base's inlet speed differs from the start state's.

## Files

- [PLAN.md](PLAN.md): the plan with the pilot and the Deviations. [design.json](design.json): the
  design with the dropped pair. [flow-check.json](flow-check.json): the solver checks of the 58 runs.
  [baselines.json](baselines.json): the baselines' answers. [contact-8000.png](contact-8000.png).
- [pilot/](pilot/): design, flow check, visibility measure and contact sheet of the 13 pilot runs.
- [test-set/](test-set/): the request manifest with every request's hash, the leak check and the
  answer key's SHA-256 (`truth_sha256` in the manifest). The requests themselves, 1,044 files of 178 to 233 KB and 225 MB in all, are in the
  [release](https://github.com/seungminyome/PythonFOAM/releases/tag/wrong-setup-2-2026-11-03).
- [results/](results/): `run.json`, the server command, the six `metrics.jsonl` with every raw answer,
  the report and the reasons. `runtime/` holds the llama.cpp version, the GPU, the model file hashes
  and the server log as a gzip copy.
- [jobs/](jobs/): the three job scripts and the build job's output. [job/sacct.txt](job/sacct.txt)
  and the output of GPU job 25107731 as a gzip copy.
- [make_manifest.py](make_manifest.py) writes [manifest.json](manifest.json) and compares each
  byte-preserved file with its source.
