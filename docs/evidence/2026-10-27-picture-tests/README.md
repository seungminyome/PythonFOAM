# October 27 evidence: trend test, 4-bit Qwen, a cylinder flow

Five Slurm jobs on MedicineBow (University of Wyoming), each on one GPU, on
2026-10-27 between 12:44 and 16:10 MDT, and the cylinder flow runs whose
states one of them uses. No solver ran in these jobs; the solver runs of the
same day are in [2026-10-27-solver](../2026-10-27-solver/README.md).

[Report](../../results-20261027.md) ·
[How the sets are built and run](../../../Solver_Examples/PODFoam/llm_demo/README.md#trend-test-on-a-developed-flow-sequence_testpy) ·
[Release with every archive](https://github.com/seungminyome/PythonFOAM/releases/tag/tests-2026-10-27)

## Jobs

| Job | Requests | Models | GPU (node) | Time (MDT) |
|---|---|---|---|---|
| 24903974 | `developed-sequence`: 45 three-time sequences of the developed flow in five forms (225) | 12B, 26B-A4B, 31B (Gemma 4 QAT) | NVIDIA A30 (mba30-005) | 12:44 to 13:48 |
| 24903975 | the same 225 | Qwen3.5-35B-A3B Q8_0 | NVIDIA L40S (mbl40s-007) | 14:55 to 15:03 |
| 24903976 | `seed1` of October 22 (96: 48 v1, 48 v2), image-token limit and minimum 1024, context 8192 | Qwen3-VL-32B, Qwen3.5-27B, Qwen3.5-35B-A3B, all Q4_K_M | NVIDIA L40S (mbl40s-001) | 14:58 to 15:26 |
| 24903977 | `developed` of October 22 (280: 140 v1, 140 v2), same settings | the same three | NVIDIA L40S (mbl40s-002) | 14:58 to 16:10 |
| 24903978 | `cylinder`: 10 states of a cylinder flow, 4 random windows each, v1 and v2 (80) | 12B, 26B-A4B, 31B | NVIDIA A30 (mba30-005) | 13:02 to 13:24 |
| 24903081, 24903218 | `pimpleFoam`, the cylinder flow (1,800 and 7,200 cells), t = 0 to 150 s | (CPU) | | 08:28 to 08:53 |
| 24903180, 24903356 | PODFoam with the callback on the two cylinder meshes: the frame is drawn | (CPU) | | 08:38 to 08:55 |

The five sets of `developed-sequence`, one triple each:

| Set | Pictures | Prompt |
|---|---|---|
| `dev-sequence-v1` | the solver's two-panel pictures (`pod_image.py`), one per time | the October 20 sequence prompt |
| `dev-sequence-v2own` | one picture per field and time, each on its own colour scale | the October 22 prompt: compare the colour-bar numbers |
| `dev-sequence-v2own-t` | the same | plus the answer key's thresholds (2 % for the trend words, 5 % for the region) |
| `dev-sequence-v2own-tn` | the same | plus each time's largest \|U\| and lowest p in the note |
| `dev-sequence-numbers` | none | the numbers and the thresholds only |

The 45 triples were drawn (seed 20261027) from 195 candidates on the states
of the developed flow of October 22 (job 24757429, which used an adaptive
time step; the states are named by nominal steps of 5×10⁻⁷ s: every 1 ms
from t = 0.032 to 0.1 s, gaps of 1, 2 and 3 ms), balanced over the nine
combinations of speed and pressure trend as far as the flow has them. One
window per triple, placed at random so that the fastest cell of every frame is
at least 15 % of the span from each edge. True words: speed 15 increasing,
15 decreasing, 15 roughly constant; pressure 20 more negative, 18 less
negative, 7 roughly constant; region 39 moves, 6 same place. 30 triples change
the peak speed and 38 the lowest pressure by at least 2 %.

The cylinder flow is the `offsetCylinder` case of the OpenFOAM-9 tutorials
(`pimpleFoam`, laminar), on its mesh (1,800 cells) and on a mesh with twice
the cells in each direction (7,200); the set uses the fine run, every 5 s from
t = 100 to 145 s (the flow is steady: the ten states differ by at most
6×10⁻⁵ m/s in |U|), windows placed at random around the fastest cell (span in y
0.8 to 2.5 m, which may reach below the bottom wall: white, no cells). In all
ten states the fastest flow and the lowest pressure are the same two cells,
beside the cylinder (`cylinder_extreme_cells` in the recount): the set tests
another geometry, not a changing flow.

## Files

| Path | What it contains |
|---|---|
| `reports/<job>.md` | Each job's own report (`window_test.py report` or `sequence_test.py report`) |
| `results/<job>/<model>/run.json` | Model alias, server note (repository, revision, files, settings), sets, hashes of the test-set manifest and answer key |
| `results/<job>/<model>/<set>/metrics.jsonl`, `summary.json` | One line per request: the parsed answer and its score, request hashes, tokens, server timings, wall time; the runner's summary |
| `test-sets/developed-sequence/`, `test-sets/cylinder/` | The manifest (request hashes, build arguments, window rule, code hashes) and the answer key of the two new sets. The keys of `seed1` and `developed` are in [../2026-10-22-window-test/test-sets/](../2026-10-22-window-test/test-sets/) |
| [pictures/](pictures/) | Pictures as sent, decoded from request bodies (listed below) |
| `runtime/<job>/` | The llama-server build, loaded modules, the GPU at the start and `sha256.txt` (llama.cpp files, test set, scripts) |
| `runtime/<job>/server/<model>.cmd`, `.log.gz`, `.models.json`, `.gpu.txt` | Per model: server command line, log (gzip copy), model list, GPU memory once it answered |
| `job/<job>.out` | The job output |
| [flow/](flow/) | The cylinder runs: job scripts and outputs, the cases' `system/` and `constant/` (without the mesh), a summary of each log ([summarize_cylinder_log.py](flow/summarize_cylinder_log.py)) |
| [cylinder_misses.py](cylinder_misses.py), [cylinder-misses.json](cylinder-misses.json) | Where 12B put the lowest pressure when it missed (8 behind the cylinder, 4 at its lower rear, 10 below it), the pressure there, and how much the ten states differ; needs the test set's frames from the release |
| [cylinder-miss-analysis.json](cylinder-miss-analysis.json) | For every cylinder position answer more than 10 % off: the speed or pressure at the cell named, relative to the true extreme ([../2026-10-22-window-test/miss_analysis.py](../2026-10-22-window-test/miss_analysis.py); needs the test set's frames from the release) |
| [independent-recount.py](independent-recount.py), [independent-recount.json](independent-recount.json) | A recount without the test code (below) |
| [manifest.json](manifest.json) | Origins, sizes and hashes of the files here |

Pictures: `dev-sequence-v1-gap006000-steps102000-108000-114000-t1.png` to
`-t3.png` (the three v1 pictures of one triple: peak speed falls 5.4 %, lowest
pressure rises 32 %; 12B answered increasing and more negative) and
`dev-sequence-v2own-...-t1-U.png` to `-t3-p.png` (the same triple, |U| and p
for each time on its own scale; 12B answered both right);
`cylinder-flow-window-v2-step054000-w1-U.png` / `-p.png` and
`cylinder-flow-window-v1-step054000-w1.png` (one cylinder window; 12B put the
lowest pressure 44 % of the range away from the true cell, in the wake).

## Setup

- Models: the Gemma rows of `models.tsv` as on October 22; the 4-bit Qwen rows
  `qwen3vl-32b-q4` (`Qwen/Qwen3-VL-32B-Instruct-GGUF@e3e1fe0c…`, Q4_K_M),
  `qwen35-27b-q4` (`unsloth/Qwen3.5-27B-GGUF@3221f178…`, Q4_K_M) and
  `qwen35-35b-q4` (`unsloth/Qwen3.5-35B-A3B-GGUF@bc014a17…`, Q4_K_M), each
  with its own projector; every file passed its SHA-256 check before the model
  ran. Job 24903975 used the Q8_0 Qwen3.5-35B-A3B of October 22.
- Servers: llama.cpp b11429 (commit `d812350`), `--n-gpu-layers 99`, one slot,
  reasoning off; context 4096 and image-token limit 256, except jobs 24903976
  and 24903977: context 8192, `--image-max-tokens 1024` and
  `--image-min-tokens 1024` (the setting the llama.cpp log recommends for
  Qwen-VL models). The window_test.slurm of `ab6b943` loads the CUDA modules
  named in `POD_HOST_MODULES`.
- Requests and scoring as on October 22: temperature 0, `max_tokens` 320,
  seed 20261021, no prompt cache; a position is right within 10 % of the
  plotted range; trend words as in the key (2 % relative change, 5 % of the
  range for the region). The fixed-answer column is the best single answer
  over the whole set.

## Recount

`python3 independent-recount.py` (no third-party packages) recomputes, from
`metrics.jsonl` and the answer keys only, every count cell of the five
reports: answered; fastest flow and lowest pressure within 10 %; the three
trend words; the fixed-answer column. Against the five reports: 38 rows
checked, none differ. It also writes the numbers the report derives: median
distances, the trend words on the triples with a clear change, the words each
model gave, the 4-bit Qwen counts next to the October 22 counts on the same
sets, and where the cylinder's extremes are. It does not check the token and
time columns.

## Notes

- Code that ran: every script hashed in `runtime/<job>/sha256.txt` equals
  `ab6b943` (38 of 38 files). The `developed-sequence` set was built with the
  code of `6afbdeb` (its manifest hashes 9 of 9 files equal), the `cylinder`
  set with code equal to `df72c24` (8 of 8).
- Of the first submissions of these five jobs (24903916 to 24903920), the
  two that started (24903916 and 24903920) stopped within a minute: the
  server could not load `libcudart.so.12` because the job script no longer
  loaded the CUDA module. The other three were cancelled before they started.
  None produced answers and they are not kept; `POD_HOST_MODULES` was added
  for the resubmission.
- In the window jobs each model folder also has `summary.json` files with 0
  attempted requests for sets they did not run; they are left out here.
- The cylinder set's manifest names its test "picture-window test 2026-10-22
  (window seed 20261028)": the label `window_test.py` writes; the set was built
  on October 27.
- `truth.private.json` means withheld from the model input, not private
  personal information.
- The records contain cluster paths and server process ids as provenance.
