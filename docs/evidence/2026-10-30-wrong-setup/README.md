# October 30 evidence: can a model see that a run was set up wrong?

Earlier tests scored answers that can be computed from the arrays. This one tests a case where a
model might add something: a run that is set up wrong, whose solver log ends normally, and for
which nobody wrote a rule in advance. Four vision-language models (Gemma 4 12B, 26B-A4B and 31B,
QAT Q4_0, and Qwen3.5-35B-A3B, Q8_0) were shown two v2 pictures of one state of a pimpleFoam run
of the 2D step case, were told the intended setup in words and were asked whether the pictures are
consistent with it. No kind of mistake is named. The set has 80 requests: 8 states each of five
normal runs and of five runs with one changed entry.

In short (counts from `reports/combined.md` and `recount.json`):

- By the scoring fixed in the design, Gemma 4 31B was right for 67 of 80. Gemma 4 12B, 26B-A4B and Qwen3.5-35B-A3B were right for 41, 42 and 45, against a
  constant baseline of 40 and 56 for a rule on the peak |U| that needs no reference run.
- The three lower models said `consistent` nearly every time: for 79, 78 and 75 of 80 frames, including pictures whose colour bar ends at 11.6 m/s
  under a stated inlet speed of 32.2 m/s.
- 31B's lead over the rule rests on one run. The two differ on 15 frames: 31B is right on 13 (M2 8, M4 4, M3 1), the rule on 2. Without M4's
  frames it is 63 against 56 of 72, without M2's 59 against 56 of 72, without both 55 against 56 of 64. Counting a wrong frame as caught only when
  the reason is the low speed gives 54 against 56 of 80.
- 31B caught M1 (inlet speed) and M5 (half inlet), 8 of 8 each, by comparing the colour bar's upper label with the stated speed, the rule's comparison. That is
  one number against a number in the prompt, in one sentence for both runs. It does not answer why a model is needed.
- M2 (viscosity) is the only change that models seem to notice and that no number here needing no reference run flags: 31B 8 of 8, Qwen 5, 26B-A4B 2, 12B 0. The
  frames show no vortices and a smooth p. The recirculation that most of these reasons deny is there, over more of the window than in any normal frame. No reason
  names viscosity, and it is one run whose frames are nearly alike, so this is the only candidate answer in this test and a weak one.
- No model saw M3 (slip walls): 31B 1 of 8, the others 0. M4's change (moving wall) is not in the pictures, so M4 cannot show whether a model notices it; 31B's
  4 of 8 carry the sentence of its 2 false alarms in 40 normal frames, and no reason names a wall. For both false alarms the same flow state under another
  step and time got `consistent`.
- "The solver log looks normal" holds strictly only for M2 and M4. The largest Courant number goes above 1 in M1, M3 and M5, which flags all three with no
  reference run: 64 of 80 with no false alarm, a check outside the design.
- Given a normal run to compare with, the four numbers at the ends of the two colour bars alone get 75 of 80 (68 with each normal run held out of its own range),
  also outside the design.
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
| 24947868 | `flow/frame_facts.py`: what the frames, the mesh and the pictures hold | CPU (t506) | 16:59 |

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
  inlet, before the first frame, M3 later and repeatedly. None crashed. So only the logs of M2 and M4 look
  normal throughout.
- In 0.04 s a flow at 32.2 m/s travels 1.29 m: 10.7 window lengths, about 2 lengths of the channel behind
  the step and 0.56 of the domain. The bulk flow follows the inlet at once because the flow is
  incompressible, but what comes from the inlet by convection does not arrive: from the inlet to the step
  takes at least 0.051 s. So M5's split of the inlet does not reach the window. At the last frame the upper
  half of the channel runs faster than the lower half by 29.8 m/s at x = −1.5 m, 3.2 m/s at x = −0.9 m and
  0.0 m/s at x = −0.3 m, and just upstream of the step's lip (x = −0.0093 m) the core profile is flat at 16.8 to
  16.9 m/s against 32.8 to 33.3 m/s in N5. M5 shows in the window as half the flow rate, with no jet. At 3.22 m/s
  the run lasts 1.07 window lengths, so M1's frames still hold what the start state left in the window and they
  still change: their fastest flow, 11.6 to 13.6 m/s, is reverse flow left from that state.
- **The five normal runs are pieces of one trajectory.** The solver is deterministic and the developed run
  had reached Δt = 5×10⁻⁶ s by t = 0.0113 s, so a normal run reproduces it: the states of N1 differ from the
  developed run's written states at the same time by at most 1.2×10⁻⁵ m/s. The 40 normal frames hold 24 different
  flow times. The 16 pairs of frames at one flow time (N1 at step 8,000 and N2 at step 6,000, for example)
  differ by at most 4.3×10⁻⁴ m/s and 0.015 m²/s² and by at most 163 pixels below the title
  (`flow/normal-overlap.json`). The answers on these pairs are in Results.
- M4 is closer to N5 than the other normal runs are: over the window cells at the same step the mean
  absolute difference of |U| from N5 is 0.60 to 1.16 m/s for M4 and 1.77 to 3.33 m/s for N1 to N4; M2, M3,
  M5 and M1 lie at 5.5 to 6.8, 6.4 to 7.1, 7.5 to 8.1 and 11.8 to 12.2 m/s (`flow/against-n5.json`).
- **M4's change is not in the pictures.** The reverse flow along the moved wall reaches down to y = 0.113 m
  and the pictures end at y = 0.04 m. The mean velocity difference from N5 at the same step over the window's
  cells is 2.6 to 5.1 % of 32.2 m/s, against 8.5 to 19.7 % for N1 to N4. Placed on the colour bar's 256
  colours, at most 4.6 % of the plotted pixels of an |U| picture lie more than 16 colours from N5's, against 16
  to 76 % for N1 to N4; for p it is 10 to 46 % against 32 to 94 %, because each picture has its own bar and the
  ends of M4's p bar lie up to 54 m²/s² from N5's. M4's frames stay in the counts, as the scoring is fixed, but
  M4 cannot show whether a model notices the change (`flow/frame-facts.json`).

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
  actual change or its visible effect. `reasons-to-judge.jsonl` lists them with each run's change. The labels
  are under Second question.

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
  fastest flow is a thin jet near the bottom, and it runs backward.
- **M2-viscosity: different in pattern, not in the peak.** No spots or vortices, smooth layers; p is a smooth
  gradient from left to right with no low-pressure cores. The colour bar ends at 37 to 38 m/s, as in a normal run.
  The recirculation is there, larger and weaker than in a normal run (table under What the counts rest on).
- **M3-slip-walls: different to a careful eye.** One long dark band instead of a row of spots, and fast flow against
  the bottom edge where the normal runs are dark. The colour bar ends at 37 m/s, as in a normal run.
- **M4-moving-wall: no visible difference.** The moved wall and its reverse flow are outside the window, and the pictures
  look like N5's at the same step with the spots moved by 1 to 2 % of the window.
- **M5-half-inlet: visible in the numbers.** The pattern of a normal run with the colour bar ending at 18 to 20 m/s,
  below the stated 32.2. The inlet's split and its jet do not reach the window; the visible effect is the lower speed.

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
  of 32.2 m/s." All 17 quoted maxima (31B's 16 and 12B's one) equal the colour-bar label of their frame. A colour-bar
  maximum below 32.2 holds on M1 8 of 8, on M5 8 of 8 and on 0 of the other 64 frames, exactly the frames where 31B gives
  this reason; this comparison was written after the answers were read. It is the rule's comparison, one number against a
  number in the prompt. 31B uses the same sentence on both runs, so it does not tell them apart, and it reads M5's half flow
  rate as a low inlet speed. On these 16 frames 12B flagged 1, 26B-A4B 0 and Qwen 0. 12B on M1 at step 8,000: "a high-speed jet
  near the bottom wall and a recirculation zone behind a step-like geometry ... consistent with flow over a backward-facing
  step". 12B's one `inconsistent` (M1, step 6,000) gives the same comparison as 31B.
- **M2.** What the frames show is the absence of vortices and a smooth p. The recirculation is not missing (table under What the
  counts rest on), and the bubble is longer than the window. The word "recirculation" is in 13 of the 15 `inconsistent`
  reasons (31B 7 of 8, whose eighth says no flow separation; Qwen 5 of 5; 26B-A4B 1 of 2), always as something the frames lack, so
  these reasons are wrong as statements about the flow. 31B's 8 rest first on a missing step, for example "a simple channel
  flow with a boundary layer at the bottom, but there is no backward-facing step geometry (no white area indicating a
  missing cell region) and no recirculation zone". Qwen's 5, on steps 6,000 to 8,000: "smooth gradient with no recirculation
  or step effect; pressure lacks expected low-pressure zone downstream of step". Its "smooth gradient" and "lacks expected
  low-pressure zone" are accurate: lowest p is −112 to −98 m²/s² against −466 to −216 in normal frames. 26B-A4B's 2 cite no
  recirculation (step 4,500) and a pressure rise toward the outlet (step 8,000), which normal frames have too. No
  `inconsistent` reason mentions viscosity.
- **M3 and M4.** 31B's 5 `inconsistent` answers (1 on M3, 4 on M4) use the words "no evidence of a backward-facing
  step", as do its 2 false alarms on normal frames. None says that a wall slips or moves. The 4 on M4 fall on steps 4,500,
  5,500, 6,500 and 8,000; at those steps 31B flagged N5 only at 5,500. M4's change is not in the pictures, so they are not
  catches of it.
- **The missing step.** 31B gives one of two grounds in all its 31 `inconsistent` answers: the speed below the stated 32.2 m/s (16) or
  no step geometry (15: M2 8, M4 4, M3 1, N4 1, N5 1). No other model gives the second. It describes the plot window, not a
  fault. The step's lip lies on the left edge (x = 0, y = 0.0127 m, 32 % of the height), the window starts there, and all 160 pictures
  have 0 white pixels inside the axes, while the prompt says white areas have no cells. The wording comes on 8 of 8 M2 frames against 7
  of the other 72, so M2's look seems to trigger it. The recirculation it denies is there: Ux < 0 in 29.5 % and 28.7 % of the window's cells on
  the two normal frames, 43 to 45 % on M2.
- **31B's two false alarms do not hold on the same flow state.** N4 at step 6,500 got `inconsistent`; N5 at step 4,500 shows the same flow
  time (velocity differs by at most 1.6×10⁻⁴ m/s) and got `consistent`: "a recirculation zone and shear layer consistent with a
  backward-facing step". N5 at step 5,500 got `inconsistent`; N4 at step 7,500 (2.5×10⁻⁵ m/s) got `consistent`: "a flow separation and
  recirculation zone at the bottom left". In both pairs the |U| pictures are the same below the title, and the p pictures differ in at most 24
  pixels; the title's step and time differ. Over the 16 pairs of normal frames at one flow time, 31B gave the same answer for 14 and the other
  three models for all 16 (`recount.json`: `same_flow_state_other_label`).

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
- A user with a wrong setup usually has no normal run to compare with. The next section gives the checks that need none.

## What the counts rest on

This section was computed after the answers were read, so it lies outside the design. The question, the runs and the scoring are as fixed
before; the counts above stand. `recount.py` looks up each table line below in this file and writes the counts to `recount.json`
(`what_the_counts_rest_on`); the flow numbers are in `flow/frame-facts.json`.

**31B against the rule.** They differ on 15 frames: 31B right and the rule wrong on 13 (M2 8, M4 4, M3 1), the rule right and 31B wrong on 2 (N4 at step
6,500, N5 at step 5,500).

| Frames counted | Frames | 31B right | Rule right |
|---|---:|---:|---:|
| All | 80 | 67 | 56 |
| Without M4 | 72 | 63 | 56 |
| Without M2 | 72 | 59 | 56 |
| Without M2 and M4 | 64 | 55 | 56 |
| All, 31B's `inconsistent` counted only with the speed reason | 80 | 54 | 56 |

- M4's 4 cannot come from the change, which is not in the pictures. If M4's frames count as what they look like, 31B's false alarms are 6 of 48 rather than 2 of
  40. No reader of the pictures can be expected to reach more than 72 of 80 under the fixed scoring.
- M2's 8 frames are close to one observation. Neighbouring frames of M2 differ by a mean of 1.56 to 2.55 of the colour bar's 256 colours in the |U| picture and 1.22 to
  2.06 in the p picture, against 4.99 to 25.44 and 9.48 to 70.23 for the normal runs.
- In favour of a real signal on M2: three of the four models flag it, and Qwen (5 of 8) and 26B-A4B (2 of 8) flag nothing else in the whole set. It is still one run.

**Reverse flow.** The share of the window with Ux < 0, by area and by cells (the mesh is finer near the walls), the share of the window's part below the step's height
by area, and the lowest Ux in the window.

| Frames | Window, by area | Window, by cells | Below the step's height, by area | Lowest Ux (m/s) |
|---|---:|---:|---:|---:|
| Normal runs | 11.4 to 14.2 % | 22.5 to 33.7 % | 35.8 to 44.6 % | -24.1 to -12.9 |
| M1-inlet-speed | 62.1 to 68.5 % | 77.8 to 81.7 % | 75.2 to 87.2 % | -13.6 to -11.6 |
| M2-viscosity | 17.2 to 19.2 % | 43.0 to 45.1 % | 54.2 to 60.5 % | -3.86 to -3.09 |
| M3-slip-walls | 10.7 to 12.0 % | 28.4 to 32.2 % | 33.7 to 37.7 % | -29.5 to -25.7 |
| M4-moving-wall | 12.5 to 14.1 % | 28.6 to 31.1 % | 39.3 to 44.4 % | -23.6 to -13.1 |
| M5-half-inlet | 7.3 to 10.3 % | 14.1 to 23.5 % | 23.0 to 32.4 % | -12.5 to -7.54 |

M2 has more reverse flow than any normal frame, and it is weak. Next to the lower wall it covers 98.3 % of the window's length (normal frames 40.8 to 67.5 %), unbroken from x = 2.5 mm
to x = 0.1215 m at step 4,500 and x = 0.1475 m at step 8,000, so the bubble is longer than the window.

**Checks that need no reference run.** Only the first line is in the design.

| Check | Right of 80 | False alarms of 40 | M1 | M2 | M3 | M4 | M5 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Peak \|U\| rule (the design's) | 56 | 0 | 8 | 0 | 0 | 0 | 8 |
| Largest Courant number of the whole run above 1, flagging all the run's frames | 64 | 0 | 8 | 0 | 8 | 0 | 8 |
| Courant number above 1 at the frame's own step | 44 | 0 | 0 | 0 | 4 | 0 | 0 |
| The rule or the whole run's Courant number | 64 | 0 | 8 | 0 | 8 | 0 | 8 |
| Gemma 4 31B | 67 | 2 | 8 | 8 | 1 | 4 | 8 |

The largest Courant number of the whole run is 10.69 in M1 (above 1 in steps 2 to 1,037), 5.49 in M5 (steps 2 to 118) and 1.31 in M3 (1,904 steps between 5,095 and 7,566), against 0.341 to
0.347 in the normal runs, 0.284 in M2 and 0.348 in M4. M1's and M5's spikes come before the first frame, and only 4 of M3's 8 frames show a number above 1 themselves. M2 is the only run
where a model catches something that none of these numbers catches; 31B's 4 on M4 are not catches, as M4's change is not in the pictures.

**The numbers on the colour bars alone.** The ends of the two bars are printed in each picture. Every cut and range below was chosen knowing the classes, and all but the |U| upper end against
the stated 32.2 m/s (the rule's 56) need a normal run to compare with.

| Numbers printed on the pictures | Flagged when | Right of 80 | False alarms of 40 | M1 | M2 | M3 | M4 | M5 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Lowest p alone | above -163.8 | 64 | 0 | 8 | 8 | 0 | 0 | 8 |
| p range alone | below 193.2 | 64 | 0 | 8 | 8 | 0 | 0 | 8 |
| \|U\| upper end alone | below 27.21 | 56 | 0 | 8 | 0 | 0 | 0 | 8 |
| p upper end alone | below 28.37 | 55 | 8 | 8 | 8 | 0 | 4 | 3 |
| \|U\| lower end alone | below 0.0002645 | 53 | 4 | 2 | 8 | 0 | 1 | 6 |
| Any of the four ends outside the normal frames' range | outside | 75 | 0 | 8 | 8 | 8 | 3 | 8 |
| \|U\| lower end above 0.00589 or lowest p above -215.6 | above | 73 | 0 | 8 | 8 | 8 | 1 | 8 |
| The same four ends, each normal run against the other four runs' range | outside | 68 | 7 | 8 | 8 | 8 | 3 | 8 |

Given a normal run, these numbers do as well as 31B or better and they catch M2 and M3, so M2 escapes only the checks that need no reference run. M3 is caught 8 of 8 by the
lower end of the |U| bar (0.0079 to 0.113 m/s against at most 0.0059 m/s), because its walls slip; no model used it. M4's 3 are one end each and small: the p upper end at step 6,000, the |U| lower end at
step 7,000, the |U| upper end at step 7,500. The last line is the fairer figure, since the two before it take the normal range from the frames they are scored on. Its wrong frames are compared with all five normal runs; each of the five four-run ranges also flags 35 of the 40.

## Second question

Of the 37 `inconsistent` reasons on wrong frames, how many name the actual change or its visible effect. This is a judgement by one AI agent (`reason-judgement.json`: its rule, its blinding and its labels), with no second
judge and no human check, and the numbers below are its labels as given.

| Run | `inconsistent` reasons | Names it | Partly | No |
|---|---:|---:|---:|---:|
| M1-inlet-speed | 9 | 9 | 0 | 0 |
| M2-viscosity | 15 | 5 | 9 | 1 |
| M3-slip-walls | 1 | 0 | 0 | 1 |
| M4-moving-wall | 4 | 0 | 0 | 4 |
| M5-half-inlet | 8 | 0 | 8 | 0 |
| All wrong runs | 37 | 14 | 17 | 6 |

- By model, names it / partly / no: 12B 1 / 0 / 0, 26B-A4B 0 / 1 / 1, 31B 8 / 16 / 5, Qwen 5 / 0 / 0. The 2 false alarms on normal frames are labelled as not there.
- Counting only "names it" gives 14 of 37: M1's 9, one number compared with the prompt, and Qwen's 5 on M2, which name the smooth field.
- M2's 9 "partly" rest on phrases such as "no recirculation" and "simple channel flow", which the judge's notes take as close to the vortex-free look. The first is false as a statement about the flow. 31B's wording comes on 8 of 8 M2
  frames against 7 of the other 72, so M2's look seems to trigger it, which speaks for "partly"; a strict reading moves them to "no".
- M5's 8 "partly" are a judgement call. The judge's list for M5 holds a closed half, a jet and other flow near the step. The closed half and the jet are not in the pictures, and the clearest visible effect is the lower speed, which these reasons state and read
  as a low inlet speed. A strict reading of the list moves all 8 to "no"; taking the lower speed as the visible effect would move them to "names it".
- `reasons-to-judge.jsonl` gives only each run's change. `judge-facts.json` adds what the frames hold, measured without any answer, for a further judge: among them that M2's recirculation is not missing, that M4's change and M5's jet are not in the
  pictures and that no picture has a white area. The labels above were made without it; the judge's notes reach the same facts on M2, M4 and M5.
- The `domain_m` and `inlet_x_m` in `reason-judgement.json` are the extents of the cell centres. The mesh's inlet is at x = −1.651 m and its outlet at x = 0.635 m.

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
| `reason-judgement.json` | The labels on the reasons by one AI agent, with its rule, blinding and measurements |
| `judge-facts.json`, `flow/judge_facts.py` | What the frames hold, for a further judge of the reasons, and the script that writes it |
| `results/window-test-24947089/<model>/` | `run.json` (model alias, server note, set hashes); `wrong-setup-v2own/metrics.jsonl` (one line per request: parsed answer and reason, score, request hash, tokens, timings) and `summary.json` |
| `runtime/window-test-24947089/` | llama.cpp build, modules, GPU, `sha256.txt` (llama.cpp files, set, scripts); `server/<model>.cmd`, `.log.gz`, `.models.json`, `.gpu.txt` |
| `flow/cases/` | `controlDict`, `fvSchemes`, `fvSolution`, `transportProperties` (and M2's), `turbulenceProperties`, `p-boundary.txt` and each run's `U-boundary.<run>.txt` (the same in all runs apart from the named change) |
| `flow/logs/<run>.log.gz` | gzip copies of the ten `log.pimpleFoam` |
| `flow/flow-check.json` | `wrong_setup_test.py flow-check`: each run's log numbers and the inlet flux |
| `flow/normal_overlap.py`, `flow/normal-overlap.json` | The normal frames at one flow time, compared |
| `flow/against_n5.py`, `flow/against-n5.json` | Each run's mean distance from N5 at the same step |
| `flow/frame_facts.py`, `flow/frame-facts.json` | Colour-bar ends, reverse flow, the layer of M4's wall, M5's profile, white pixels and each picture against N5's and its neighbour, from the arrays, the mesh and the pixels |
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
and the manifest. It checks the labels, and from the text hashes that each of the 8 texts has 5 normal and 5 wrong frames. Beyond the report it writes the
answers on the pairs at one flow time, the right answers by step, how often the answer changes along a run, and the prompt tokens by class. It recomputes the tables of
What the counts rest on and Second question and looks each line up in this file, and it checks each label in `reason-judgement.json` against the recorded answer and that the colour-bar ends in
`flow/frame-facts.json` are the key's peak |U| and lowest p. Result: 121 report lines and 30 lines of this file checked, 0 problems.

## Not tested

- **Independence.** The 80 frames come from 10 runs and neighbouring frames of a run look alike, M2's most of all. The normal runs are one trajectory, with 24
  different flow times in 40 frames, and all wrong runs start from one state. So these counts are not 80 independent cases. The models' results on M2
  rest on one run; a second wrong viscosity was not tried.
- **Other changes and other windows.** Five kinds of mistake were tried, on one case and one window. M4's wall and M5's inlet lie outside the
  window, and M3's upper wall too, so M4 does not test whether a model notices a moving wall. A whole-domain picture was not tried.
- **Other prompts.** The prompt does not say where the step lies relative to the window; the window starts at the step, so the pictures have no
  white area. 31B gave the missing step as a reason in 15 answers. Each request was answered once, at temperature 0, with this one wording,
  which was fixed before any answer.
- **The solver callback.** It does not send this request; `LLM_MODE` has no such value.
- **M1's frames as a developed state.** The prompt says the pictures show a developed state; in M1 the window has not been flushed by the end of
  the run.

## Notes

- Code that ran: `97db7eb` for the set and the GPU job, unchanged since (`runtime/window-test-24947089/sha256.txt`,
  `job/after-run-24947316.out`). Its `prepare` writes the ten cases that ran byte for byte (job 24947327). Unit tests: 152 pass on
  Python 3.10 and 3.12 (job 24947320), 27 of them in `test_wrong_setup_test`. `flow/frame_facts.py` reads the mesh with `foam_fields.py` and `pod_image.py` of that code.
- The GPU job ran in partition `non-investor-gpu` on mbl40s-003, an NVIDIA L40S, the GPU model of the instability test (`job/submit_gpu.sh`). `mb-l40s` itself
  was held by week-long jobs.
- One of 26B-A4B's reasons stops at the 300-character limit of the schema. The answer word still follows it.
- `truth.private.json` means withheld from the model input, not private personal information.
- The records contain cluster paths and server process ids as provenance.
