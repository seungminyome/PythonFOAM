# October 30 evidence: can a model see that a run was set up wrong?

Earlier tests scored answers that can be computed from the arrays. This one tests a case where a
model might add something: a run that is set up wrong, whose solver log ends normally, and for
which nobody wrote a rule in advance. Four vision-language models (Gemma 4 12B, 26B-A4B and 31B,
QAT Q4_0, and Qwen3.5-35B-A3B, Q8_0) were shown two v2 pictures of one state of a pimpleFoam run
of the 2D step case, were told the intended setup in words and were asked whether the pictures are
consistent with it. No kind of mistake is named. The set has 80 requests: 8 states each of five
normal runs and of five runs with one changed entry.

In short (counts from `reports/combined.md` and `recount.json`):

- Gemma 4 31B was right for 67 of 80. Gemma 4 12B, 26B-A4B and Qwen3.5-35B-A3B were right for 41, 42 and 45, against a constant baseline of 40 and
  56 for a rule on the peak |U| that needs no reference run.
- The three lower models said `consistent` nearly every time: for 79, 78 and 75 of 80 frames, including pictures whose colour bar ends at 11.6 m/s
  under a stated inlet speed of 32.2 m/s.
- 31B caught M1 (inlet speed) and M5 (half inlet), 8 of 8 each, by comparing the colour-bar maximum with the stated speed, as the rule does.
- M2 (viscosity) is the one change that a model caught and the rule did not: 31B 8 of 8, Qwen 5, 26B-A4B 2, 12B 0. These reasons point to the missing
  recirculation; 31B's also say that no step is visible, which is true of every picture in the set.
- No model saw M3 (slip walls): 31B 1 of 8, the others 0. M4 (moving wall, outside the window) gets 4 of 8 from 31B with the same sentence as its
  2 false alarms in 40 normal frames, and no reason names a wall. For both false alarms the same flow state under another step and
  time got `consistent`.
- The request text gives nothing away: any rule on it gets 40 of 80 (see Leak check).

## Jobs

| Job | What | Where | Time (MDT, 2026-10-30) |
|---|---|---|---|
| 24946869 | The ten cases written (`wrong_setup_test.py prepare`) | CPU (ttest01) | 15:22 |
| 24946879 (array 0 to 9) | The ten pimpleFoam runs, one task each | CPU, `teton` (ttest03, ttest04, t285 to t294, t513, t514) | 15:24 to 15:36 |
| 24946942 | `flow-check`, `build`, `check` and `contact` | CPU (t518) | 15:36 to 15:38 |
| 24947055, 24947079 | `flow/normal_overlap.py`, `flow/against_n5.py` | CPU (t495, ttest02) | 15:41, 15:47 |
| 24947089 | Gemma 4 12B, 26B-A4B, 31B and Qwen3.5-35B-A3B Q8_0 on the 80 requests (`window_test.slurm`, `PICTURE_TEST_SCRIPT=wrong_setup_test.py`) | NVIDIA L40S (mbl40s-003) | 15:59 to 16:12 |
| 24947316 | `check` again, `report` (combined and per model), the reasons | CPU (t347) | 16:13 |
| 24947320 | Unit tests, Python 3.10 and 3.12 | CPU (wi005) | 16:14 to 16:18 |
| 24947327 | The ten cases written again with `97db7eb` and compared | CPU (ttest01) | 16:17 |

Start and end times are in `job/sacct.txt`. Commits: `97db7eb` (code; the set was built with it),
`e2a4d6e` ([notes on the pictures](pictures-notes.md), committed before any request was sent).

## Runs

All runs are pimpleFoam (OpenFOAM v2212, laminar, PISO, upwind for div(phi,U)) on the mesh of 20,540
cells, with the settings of `flow-states-20261022/long-100ms` except for a fixed Δt of 5×10⁻⁶ s: 8,000
steps from t = 0.1 s to t = 0.14 s, every 500th step written (`flow/cases/`). Each run starts from a
written state of that developed flow, copied to a directory named `0.1` without its `uniform/` folder,
so all runs have the same steps and times. The step corner is at x = 0, y = 0.0127 m; the channel
runs from x = −1.651 m to x = 0.635 m, and its upper wall is at y = 0.1143 m, so the upper wall and the
inlet are outside the window (x 0 to 0.12 m, y 0 to 0.04 m).

| Run | Start state | Change | End | Largest Courant number (step) | Steps above Courant 1 | Inlet flux, last state (m³/s per mesh depth) |
|---|---|---|---|---|---:|---:|
| N1 | t = 0.06 s | none | End | 0.341 (4,974) | 0 | −0.04155 |
| N2 | t = 0.07 s | none | End | 0.344 (7,248) | 0 | −0.04155 |
| N3 | t = 0.08 s | none | End | 0.347 (7,413) | 0 | −0.04155 |
| N4 | t = 0.09 s | none | End | 0.347 (5,413) | 0 | −0.04155 |
| N5 | t = 0.1 s | none | End | 0.347 (3,413) | 0 | −0.04155 |
| M1-inlet-speed | t = 0.1 s | inlet velocity 3.22 m/s instead of 32.2 m/s | End | 10.7 (3) | 1,036 (steps 2 to 1,037) | −0.004155 |
| M2-viscosity | t = 0.1 s | ν = 1.56×10⁻³ m²/s instead of 1.56×10⁻⁵ m²/s | End | 0.284 (1) | 0 | −0.04155 |
| M3-slip-walls | t = 0.1 s | `lowerWall` and `upperWall` `slip` instead of `noSlip` | End | 1.31 (5,432) | 1,904 (between steps 5,095 and 7,566) | −0.04155 |
| M4-moving-wall | t = 0.1 s | `upperWall` `fixedValue (-32.2 0 0)` instead of `noSlip` | End | 0.348 (3,392) | 0 | −0.04155 |
| M5-half-inlet | t = 0.1 s | inlet faces whose centre lies in the lower half at velocity 0 (32 of 65), the others at 32.2 m/s | End | 5.49 (3) | 117 (steps 2 to 118) | −0.02077 |

- Every run ended with `End` after 8,000 steps; no change was replaced. `wrong_setup_test.py flow-check`
  refuses a log with a crash, another number of steps or a time step other than the design's, and a last
  written U or `transportProperties` without the design's entries (`flow/flow-check.json`).
- M1, M3 and M5 went above Courant number 1. M1 and M5 did so right after the sudden change of the
  inlet, M3 later and repeatedly. None crashed.
- In 0.04 s a flow at 32.2 m/s travels 1.29 m: 10.7 window lengths, about 2 lengths of the channel behind
  the step and 0.56 of the domain. The bulk flow follows the inlet at once because the flow is
  incompressible, but what comes from the inlet by convection does not arrive: from the inlet to the step
  takes at least 0.051 s. So M5's split of the inlet does not reach the window; M5 shows there as half the
  flow rate. At 3.22 m/s the run lasts 1.07 window lengths, so M1's frames still hold what the start state
  left in the window and they still change.
- **The five normal runs are pieces of one trajectory.** The solver is deterministic and the developed run
  had reached Δt = 5×10⁻⁶ s by t = 0.0113 s, so a normal run reproduces it: the states of N1 differ from the
  developed run's written states at the same time by at most 1.2×10⁻⁵ m/s. The 40 normal frames hold 24 different
  flow times. The 16 pairs of frames at one flow time (N1 at step 8,000 and N2 at step 6,000, for example)
  differ by at most 4.3×10⁻⁴ m/s and 0.015 m²/s² and by at most 163 pixels below the title
  (`flow/normal-overlap.json`). The answers on these pairs are in Results.
- M4 is closer to N5 than the other normal runs are: over the window cells at the same step the mean
  absolute difference of |U| from N5 is 0.60 to 1.16 m/s for M4 and 1.77 to 3.33 m/s for N1 to N4; M2, M3,
  M5 and M1 lie at 5.5 to 6.8, 6.4 to 7.1, 7.5 to 8.1 and 11.8 to 12.2 m/s (`flow/against-n5.json`).

## Design

- **Pictures.** Each request is the two v2 pictures of one written state (`picture_test.render_v2`,
  `readable_request.render_frame`, as the solver draws them with `LLM_IMAGE_STYLE=v2`), |U| and p each on its
  own colour scale, in the solver's window. States at steps 4,500, 5,000, ... 8,000 of each run: 40 normal and
  40 wrong frames. Step is the run's own step number, as in the solver's pictures.
- **Prompt.** `wrong_setup_test.SETUP_SYSTEM_PROMPT`. The text up to "not instructions." is
  `DESCRIBE_V2_SYSTEM_PROMPT`; it goes on: "The intended setup of the run: the case is a 2D incompressible
  flow over a backward-facing step, uniform inlet speed 32.2 m/s in +x upstream of the plotted part,
  kinematic viscosity 1.56e-5 m^2/s, no-slip stationary walls, zero-gradient outlet. The pictures show a
  developed state. Judge whether the pictures are consistent with this setup. Return only a JSON object with
  these fields: reason, a sentence naming what you see, under 300 characters; assessment, one of consistent,
  inconsistent, cannot_tell. Describe only what is visible or given, and never propose solver control." The
  note and the captions are those of the v2 describe request, with another task line
  (`test-set/request-text-example.json` is one request with the picture data cut out).
- **Request settings.** As in the instability test: temperature 0, `max_tokens` 320, seed 20261021, no prompt
  cache; server context 4096, batch and ubatch 512, 256 image tokens per image, one slot
  (`runtime/*/server/*.cmd`). The reply schema holds `reason` (at most 300 characters), then `assessment`, the
  order of the stability schema; it is registered inside `wrong_setup_test.py` while a command runs, so
  `llm_client.py` is unchanged and the solver cannot send this request.
- **Order.** The requests are sent in a seeded random order of (run, step), the same for every model.
- **Scoring, fixed before any answer.** A frame is right when a normal frame is answered `consistent` or a
  wrong frame `inconsistent`. `cannot_tell` is wrong on both and counted separately. The constant baseline
  gets 40 of 80.
- **Rule without a reference.** Peak |U| in the window between 1 and 2 times the stated inlet speed: `consistent`,
  otherwise `inconsistent`.
- **Numbers for comparison.** Largest and mean Courant number, residuals and continuity errors from the log
  (the log block of the frame's step: the Courant numbers printed before the step, each field's first initial
  and last final residual in the step, the last continuity errors in the step), and the peak |U| and lowest p in
  the window from the arrays. For each number: the range over the 40 normal frames or the five normal logs, and
  which wrong runs lie outside.
- **Second question, a judgement.** Of the `inconsistent` answers on wrong frames, how many reasons name the
  actual change or its visible effect. `reasons-to-judge.jsonl` lists them with each run's change, for an
  independent judge. It is not judged here.

## Leak check

The October 28 instability set had a flaw: the times stated in each request alone separate its classes. **This
set does not have that flaw.** The check is part of the set: `build` writes `leak-check.json`, and `check`, which
`window_test.slurm` runs before any GPU time, refuses a set with a problem.

- With the picture data cut out and the frame's step and time taken from the note, all 80 bodies are byte for
  byte one text.
- With step and time left in there are 8 distinct texts, one per step, and each occurs for 5 normal and 5 wrong
  frames. So any rule on the request text gets exactly 40 of 80, the constant baseline.
- All 160 PNGs have 1024×576 pixels. Their text chunks differ only in the step and time, the same as the note's,
  and in `FieldsSHA256`, a hash of the frame's arrays; the server passes only the pixels to the model. The titles
  in the pictures state the same step and time.
- No run name occurs in any request text. File names and the manifest are not sent.
- After the run: prompt tokens at one step are the same in both classes for all four models (980 to 982 for Gemma, 969 to 971 for Qwen; `recount.json`: `prompt_tokens`).
- The one number outside the pictures that differs by class is the request's size in bytes, because smooth
  pictures compress better: a threshold on it would get 51 of 80. The server does not pass it on, so no model
  sees it.

## What the pictures show

The pictures were opened before any request was sent; [the notes](pictures-notes.md) were committed first
(`e2a4d6e`). One frame of each run is in [contact-sheet.png](contact-sheet.png).

- **Normal runs.** A fast stream above y about 35 to 40 % of the window, peak 35 to 39 m/s, and below it a slow wake
  with thin dark lines and spots; p shows a row of low-pressure cores, down to −216 to −466 m²/s².
- **M1-inlet-speed: plainly different.** The colour bar ends at 11.6 to 13.6 m/s, far below the stated 32.2. The
  fastest flow is a thin jet near the bottom.
- **M2-viscosity: different in pattern, not in the peak.** No spots or vortices, smooth layers; p is a smooth
  gradient from left to right with no low-pressure cores. The colour bar ends at 37 to 38 m/s, as in a normal run.
- **M3-slip-walls: different to a careful eye.** One long dark band instead of a row of spots, and fast flow against
  the bottom edge where the normal runs are dark. The colour bar ends at 37 m/s, as in a normal run.
- **M4-moving-wall: no visible difference.** The moved wall is outside the window, and the pictures look like N5's at
  the same step with the spots moved by 1 to 2 % of the window.
- **M5-half-inlet: visible in the numbers.** The pattern of a normal run with the colour bar ending at 18 to 20 m/s,
  below the stated 32.2.

## Results

All 320 requests (80 per model) were answered with valid JSON. Median prompt tokens were 981.5 (Gemma) and
970.5 (Qwen); median time per request on the L40S was 1.73 s (12B), 1.23 s (26B-A4B), 3.51 s (31B) and 0.92 s
(Qwen). No model answered `cannot_tell`. The false alarm rate is the complement of the normal column.

| Answers from | Right of 80 | Normal said `consistent` (of 40) | Wrong said `inconsistent` (of 40) |
|---|---:|---:|---:|
| Gemma 4 12B | 41 | 40 | 1 |
| Gemma 4 26B-A4B | 42 | 40 | 2 |
| Gemma 4 31B | 67 | 38 | 29 |
| Qwen3.5-35B-A3B Q8_0 | 45 | 40 | 5 |
| Rule: peak \|U\| between 1 and 2 times 32.2 m/s | 56 | 40 | 16 |
| Constant baseline | 40 | | |

Right of the 8 frames of each run:

| Run | 12B | 26B-A4B | 31B | Qwen | Rule |
|---|---:|---:|---:|---:|---:|
| N1 | 8 | 8 | 8 | 8 | 8 |
| N2 | 8 | 8 | 8 | 8 | 8 |
| N3 | 8 | 8 | 8 | 8 | 8 |
| N4 | 8 | 8 | 7 | 8 | 8 |
| N5 | 8 | 8 | 7 | 8 | 8 |
| M1-inlet-speed | 1 | 0 | 8 | 0 | 8 |
| M2-viscosity | 0 | 2 | 8 | 5 | 0 |
| M3-slip-walls | 0 | 0 | 1 | 0 | 0 |
| M4-moving-wall | 0 | 0 | 4 | 0 | 0 |
| M5-half-inlet | 0 | 0 | 8 | 0 | 8 |

What the reasons say (all 37 `inconsistent` reasons on wrong frames are in `reasons-to-judge.jsonl`):

- **M1 and M5.** All 16 of 31B's reasons compare the colour-bar maximum with the stated speed, for example "The
  maximum velocity magnitude shown is 11.58 m/s, which is significantly lower than the specified uniform inlet speed
  of 32.2 m/s." This is what the rule does. The other three models gave `consistent` in 47 of their 48 answers on these frames: 12B on M1 at
  step 8,000: "a high-speed jet near the bottom wall and a recirculation zone behind a step-like geometry ...
  consistent with flow over a backward-facing step". 12B's one `inconsistent` (M1, step 6,000) gives the same comparison
  as 31B.
- **M2.** 31B's 8 reasons say there is no step geometry and no separation or recirculation, for example "a simple channel
  flow with a boundary layer at the bottom, but there is no backward-facing step geometry (no white area indicating a
  missing cell region) and no recirculation zone". Qwen's 5, on steps 6,000 to 8,000: "smooth gradient with no recirculation
  or step effect; pressure lacks expected low-pressure zone downstream of step". 26B-A4B's 2 cite the missing recirculation
  (step 4,500) and a pressure rise toward the outlet (step 8,000). No `inconsistent` reason mentions viscosity.
- **M3 and M4.** 31B's 5 `inconsistent` answers (1 on M3, 4 on M4) use the words "no evidence of a backward-facing
  step", as do its 2 false alarms on normal frames. None says that a wall slips or moves. In the window the step
  itself is never visible, in any run.
- **31B's two kinds of reason.** All its 31 `inconsistent` answers are either the speed below the stated 32.2 m/s (16) or no
  step geometry (15: M2 8, M4 4, N4 and N5 2, M3 1). Its two false alarms flip with the label: N4 at step 6,500 and N5 at
  step 5,500 show the flow times of N5 at step 4,500 and N4 at step 7,500, and 31B said `consistent` for those. Over the 16
  pairs of normal frames at one flow time, 31B gave the same answer for 14 and the other three models for all 16
  (`recount.json`: `same_flow_state_other_label`).

The second question (how many reasons name the actual change or its visible effect) is a judgement left to an independent
judge; the 37 reasons are 1 from 12B, 2 from 26B-A4B, 29 from 31B and 5 from Qwen.

Numbers at the frames, from the arrays and the log block of each frame's step: the range over the 40 normal frames, each wrong
run's range, and in brackets how many of its 8 frames lie outside the normal range.

| number | normal frames | M1 | M2 | M3 | M4 | M5 |
|---|---|---|---|---|---|---|
| largest Courant number | 0.2312 to 0.3367 | 0.2692 to 0.3573 (3) | 0.2158 to 0.2257 (8) | 0.7158 to 1.3 (8) | 0.2488 to 0.3432 (1) | 0.1256 to 0.208 (8) |
| mean Courant number | 0.01698 to 0.01714 | 0.002692 to 0.002749 (8) | 0.01687 (8) | 0.01714 to 0.01719 (8) | 0.01717 to 0.01732 (8) | 0.008752 to 0.008802 (8) |
| Ux initial residual | 6.357e-06 to 1.203e-05 | 9.58e-06 to 1.378e-05 (2) | 5.493e-06 to 1.152e-05 (2) | 4.455e-06 to 4.861e-06 (8) | 6.953e-06 to 1.084e-05 (0) | 2.544e-05 to 3.63e-05 (8) |
| Uy initial residual | 0.0001687 to 0.000436 | 7.342e-05 to 0.0001603 (8) | 1.428e-05 to 2.227e-05 (8) | 2.377e-05 to 4.098e-05 (8) | 0.0002111 to 0.0004049 (0) | 0.0001456 to 0.0002012 (5) |
| p initial residual, first solve | 0.009193 to 0.03345 | 0.002529 to 0.006147 (8) | 0.01809 to 0.02304 (0) | 0.003643 to 0.006371 (8) | 0.01048 to 0.03046 (0) | 0.002666 to 0.004239 (8) |
| Ux final residual | 1.923e-08 to 9.945e-06 | 6.489e-10 to 9.926e-06 (4) | 1.568e-08 to 9.216e-06 (2) | 4.455e-06 to 4.861e-06 (0) | 2.087e-08 to 9.613e-06 (0) | 1.39e-09 to 4.147e-09 (8) |
| Uy final residual | 2.632e-07 to 1.043e-06 | 6.596e-09 to 8.816e-09 (8) | 7.772e-08 to 1.498e-07 (8) | 1.95e-08 to 8.081e-08 (8) | 3.197e-07 to 9.631e-07 (0) | 1.708e-08 to 1.021e-07 (8) |
| p final residual, last solve | 3.297e-07 to 9.998e-07 | 6.57e-07 to 9.736e-07 (0) | 6.953e-07 to 9.181e-07 (0) | 7.79e-07 to 9.847e-07 (0) | 4.062e-07 to 9.648e-07 (0) | 5.648e-07 to 9.41e-07 (0) |
| continuity error, sum local | 4.271e-13 to 1.167e-12 | 1.196e-13 to 1.906e-13 (8) | 1.22e-13 to 1.663e-13 (8) | 4.914e-13 to 6.369e-13 (0) | 6.15e-13 to 1.241e-12 (2) | 2.563e-13 to 4.325e-13 (7) |
| continuity error, global (absolute) | 1.369e-14 to 1.653e-13 | 7.86e-15 to 2.112e-14 (5) | 1.578e-16 to 2.924e-14 (4) | 3.56e-14 to 8.004e-14 (0) | 2.965e-14 to 1.151e-13 (0) | 1.427e-14 to 5.793e-14 (0) |
| continuity error, cumulative (absolute) | 2.041e-09 to 7.244e-09 | 9.172e-09 to 9.899e-09 (8) | 1.12e-08 to 2.485e-08 (8) | 2.302e-09 to 3.627e-09 (0) | 1.519e-10 to 2.434e-09 (6) | 8.106e-09 to 8.226e-09 (8) |
| peak \|U\| in the window (m/s) | 34.73 to 39.44 | 11.58 to 13.62 (8) | 36.95 to 38.12 (0) | 36.69 to 37.3 (0) | 35.62 to 39.51 (1) | 18.1 to 19.7 (8) |
| lowest p in the window (m^2/s^2) | -465.6 to -215.6 | -69.59 to -43.01 (8) | -112.1 to -98.08 (8) | -330 to -293.2 (0) | -464.1 to -248.8 (0) | -111.5 to -60.4 (8) |

Numbers per run from the logs: the range over the five normal logs and each wrong run's value, marked \* when outside.

| number | normal runs | M1 | M2 | M3 | M4 | M5 |
|---|---|---|---|---|---|---|
| largest Courant number, whole run | 0.3414 to 0.3467 | 10.69 \* | 0.2836 \* | 1.309 \* | 0.3479 \* | 5.488 \* |
| largest Courant number, from the first frame on | 0.3414 to 0.3467 | 0.3586 \* | 0.2257 \* | 1.309 \* | 0.3468 \* | 0.2086 \* |
| mean Courant number, from the first frame on | 0.01707 to 0.01709 | 0.002715 \* | 0.01687 \* | 0.01718 \* | 0.01724 \* | 0.008769 \* |
| Ux initial residual, last step | 8.673e-06 to 1.203e-05 | 9.694e-06 | 5.493e-06 \* | 4.652e-06 \* | 9.133e-06 | 2.544e-05 \* |
| Uy initial residual, last step | 0.0002232 to 0.000436 | 7.342e-05 \* | 1.428e-05 \* | 2.377e-05 \* | 0.0003374 | 0.0001466 \* |
| p initial residual, first solve of the last step | 0.01025 to 0.02998 | 0.006147 \* | 0.02304 | 0.003643 \* | 0.02743 | 0.004149 \* |
| Ux final residual, last step | 2.16e-08 to 9.843e-06 | 9.694e-06 | 5.493e-06 | 4.652e-06 | 9.133e-06 | 2.183e-09 \* |
| Uy final residual, last step | 3.895e-07 to 1.043e-06 | 7.638e-09 \* | 1.498e-07 \* | 1.95e-08 \* | 5.103e-07 | 4.255e-08 \* |
| p final residual, last solve of the last step | 6.902e-07 to 9.543e-07 | 8.51e-07 | 9.181e-07 | 9.118e-07 | 8.809e-07 | 5.648e-07 \* |
| continuity error, sum local, last step | 6.718e-13 to 1.167e-12 | 1.789e-13 \* | 1.663e-13 \* | 5.727e-13 \* | 9.398e-13 | 2.563e-13 \* |
| continuity error, global (absolute), last step | 1.455e-14 to 1.653e-13 | 1.866e-14 | 2.151e-14 | 4.256e-14 | 9.402e-14 | 1.427e-14 \* |
| continuity error, cumulative (absolute), last step | 4.348e-09 to 7.237e-09 | 9.899e-09 \* | 2.485e-08 \* | 3.425e-09 \* | 2.434e-09 \* | 8.226e-09 \* |

- Given a normal run to compare with, the mean Courant number lies outside the normal range at every frame of all five wrong
  runs: far below it for M1 (0.0027 against 0.0170 to 0.0171) and M5 (0.0088), by 0.7 % for M2, and above it by at most 0.25 % for
  M3 and 1.0 % for M4. The normal range comes from one trajectory, so other normal runs might lie outside it too.
- Peak |U| singles out M1 and M5, lowest p M1, M2 and M5. M3 shows in the largest Courant number (0.72 to 1.30 against 0.23 to 0.34) and
  the residuals. M4 lies outside at all 8 frames only in the mean Courant number, at 6 of 8 in the cumulative continuity error
  and at 1 or 2 in three other numbers.
- A user with a wrong setup usually has no normal run to compare with. Without one, the peak rule above catches M1 and M5 and nothing
  else.

## Files

| Path | What it contains |
|---|---|
| `test-set/design.json` | The build input: settings, frame steps and each run's change, with the patches and ν its files must hold |
| `test-set/manifest.json` | The set's manifest: every request's hash and design entry, the runs with their log numbers, code hashes, build arguments |
| `test-set/truth.private.json` | The answer key: class, word, run, change and per frame the numbers from the arrays and the log |
| `test-set/leak-check.json` | The leak check, with each request's text hash |
| `test-set/numbers.json` | The comparison with the normal runs, written at the build, before any answer |
| `test-set/request-text-example.json` | The request of N1 at step 4,500 with the picture data cut out; its hash is in `leak-check.json` |
| [contact-sheet.png](contact-sheet.png) | The two pictures of each run at step 8,000 |
| [pictures-notes.md](pictures-notes.md) | What the pictures showed before any model saw them |
| `reports/combined.md` | `wrong_setup_test.py report` on the four models (the same bytes as the job's `report.md`): all tables and every frame's answers |
| `reports/12b.md`, `26b.md`, `31b.md`, `qwen35-35b.md` | The same report for each model alone |
| `reasons-to-judge.jsonl` | Each `inconsistent` answer on a wrong frame with the run's actual change |
| `results/window-test-24947089/<model>/` | `run.json` (model alias, server note, set hashes); `wrong-setup-v2own/metrics.jsonl` (one line per request: parsed answer and reason, score, request hash, tokens, timings) and `summary.json` |
| `runtime/window-test-24947089/` | llama.cpp build, modules, GPU, `sha256.txt` (llama.cpp files, set, scripts); `server/<model>.cmd`, `.log.gz`, `.models.json`, `.gpu.txt` |
| `flow/cases/` | `controlDict`, `fvSchemes`, `fvSolution`, `transportProperties` (and M2's), `turbulenceProperties`, `p-boundary.txt` and each run's `U-boundary.<run>.txt` (the same in all runs apart from the named change) |
| `flow/logs/<run>.log.gz` | gzip copies of the ten `log.pimpleFoam` |
| `flow/flow-check.json` | `wrong_setup_test.py flow-check`: each run's log numbers and the inlet flux |
| `flow/normal_overlap.py`, `flow/normal-overlap.json` | The normal frames at one flow time, compared |
| `flow/against_n5.py`, `flow/against-n5.json` | Each run's mean distance from N5 at the same step |
| `job/` | The job scripts and their outputs, `submit_gpu.sh` (the settings of the GPU job), `make_evidence.py` (the copy into this folder), `sacct.txt` |
| [recount.py](recount.py), `recount.json` | A recount without the test code (below) |
| [manifest.json](manifest.json) | Origins, sizes and hashes of the files here |

The set with its frames and arrays (`wrong-setup-test-20261030`, 90 MB) and the job's results with every raw reply
(`results/window-test-24947089`, also as `.tar.gz`) stay on the cluster in `wrong-setup-20261030/`, and the ten runs' time directories in
`flow-states-20261030/`, under `/cluster/medbow/gscratch/syome/github_repos/`.

## Recount

`python3 recount.py` uses no third-party packages. From `metrics.jsonl`, the answer key and the gzipped logs it recomputes the model and rule
tables, the table by run, both tables of numbers and the mark of every frame, and looks each line up in `reports/combined.md`. It reads the
ten logs again (8,000 steps, `End`, no floating point exception) and compares each Courant number, residual and continuity error with the key
and the manifest. It checks the labels, and from the text hashes that each of the 8 texts has 5 normal and 5 wrong frames. Result: 121 report
lines checked, 0 problems. Beyond the report it writes the answers on the pairs at one flow time, the right answers by step, how often the
answer changes along a run, and the prompt tokens by class.

## Not tested

- **Independence.** The 80 frames come from 10 runs and neighbouring frames of a run look alike. The normal runs are one trajectory, with 24
  different flow times in 40 frames, and all wrong runs start from one state. So these counts are not 80 independent cases. 31B's result on M2
  rests on one run.
- **Other changes and other windows.** Five kinds of mistake were tried, on one case and one window. M4's wall and M5's inlet lie outside the
  window, and M3's upper wall too. A whole-domain picture was not tried.
- **Other prompts.** The prompt does not say where the step lies relative to the window; the window lies behind it, so the pictures have no
  white area. 31B gave the missing step as a reason in 15 answers. Each request was answered once, at temperature 0, with this one wording,
  which was fixed before any answer.
- **The solver callback.** It does not send this request; `LLM_MODE` has no such value.
- **M1's frames as a developed state.** The prompt says the pictures show a developed state; in M1 the window has not been flushed by the end of
  the run.

## Notes

- Code that ran: `97db7eb` for the set and the GPU job, unchanged since (`runtime/window-test-24947089/sha256.txt`,
  `job/after-run-24947316.out`). Its `prepare` writes the ten cases that ran byte for byte (job 24947327). Unit tests: 152 pass on
  Python 3.10 and 3.12 (job 24947320), 27 of them in `test_wrong_setup_test`.
- The GPU job ran in partition `non-investor-gpu` on mbl40s-003, an NVIDIA L40S, the GPU model of the instability test (`job/submit_gpu.sh`). `mb-l40s` itself
  was held by week-long jobs.
- One of 26B-A4B's reasons stops at the 300-character limit of the schema. The answer word still follows it.
- `truth.private.json` means withheld from the model input, not private personal information.
- The records contain cluster paths and server process ids as provenance.
