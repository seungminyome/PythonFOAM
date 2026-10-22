# October 22 evidence: random-window picture tests, Qwen models, a developed flow

Six Slurm jobs on MedicineBow (University of Wyoming), each on one NVIDIA RTX
A6000 (49,140 MiB), on 2026-10-22 between 03:14 and 11:38 MDT, and the two
flow runs whose states they use. No solver ran in these jobs; the solver run
with v2 pictures is in [2026-10-22-live-v2](../2026-10-22-live-v2/README.md).

[Report](../../results-20261022-live.md) ·
[How the sets are built and run](../../../Solver_Examples/PODFoam/llm_demo/hpc/README.md#random-window-test-and-qwen-models-run-2026-10-22) ·
[Release with every archive](https://github.com/seungminyome/PythonFOAM/releases/tag/picture-test-2026-10-22)

## Jobs

| Job | Requests | Models | Time (MDT) |
|---|---|---|---|
| 24757327 | the 308 requests of the first October 22 test (`picture-test-20261021`) | Qwen3-VL-8B, Qwen3-VL-32B, Qwen3.5-27B, Qwen3.5-35B-A3B | 03:14 to 05:18 |
| 24757344 | `seed1`: 12 start-up states, 4 random windows each, v1 and v2 (96) | E2B (three forms), E4B, 12B, 26B-A4B, 31B and the four Qwen models | 03:43 to 04:53 |
| 24757382 | `seed1`, with image-token limit 1024 and context 8192 | 12B, 26B-A4B, 31B, Qwen3-VL-32B, Qwen3.5-27B, Qwen3.5-35B-A3B | 06:20 to 07:19 |
| 24757384 | `seed2`: the same states, other windows (96) | the same six | 06:21 to 07:17 |
| 24757383 | `seed3`: the same states, other windows (96) | the same six | 06:20 to 07:17 |
| 24757459 | `developed`: 35 states of a developed flow, 4 windows each (280) | 12B, 26B-A4B, 31B, Qwen3.5-35B-A3B, Qwen3.5-27B, E4B | 09:46 to 11:38 |
| 24757337 | `pimpleFoam`, 6000 steps of 5e-7 s from rest: the states of `seed1` to `seed3` | (CPU) | 03:35 to 03:41 |
| 24757429 | `pimpleFoam` to t = 0.1 s with an adaptive step: the states of `developed` and the start of the solver run | (CPU) | 08:52 to 09:11 |

Window seeds: `seed1` 20261022, `seed2` 20261122, `seed3` 20261023,
`developed` 20261025 (the set names `-s2` and `-s3` of the release do not
follow the seed order). States: `seed1` to `seed3` every 500 steps from 500 to
6000 (t = 0.25 to 3 ms); `developed` every 4000 steps of 5e-7 s from 64000 to
200000 (t = 0.032 to 0.1 s).

## Files

| Path | What it contains |
|---|---|
| `reports/<job>.md` | Each job's own report (`picture_test.py report` or `window_test.py report`): counts per model and set, the fixed-answer column, token and time medians |
| `results/<job>/<model>/run.json` | Model alias, server note (repository, revision, files, settings), sets, timeout, hashes of the test-set manifest and answer key |
| `results/<job>/<model>/<set>/metrics.jsonl`, `summary.json` | One line per request: the parsed answer and its score, the hashes of the sent and prepared request, tokens, server timings, wall time; the runner's summary of the set |
| `results/picture-test-24757327/<model>/oct17-paired*/<request>/result.json` | The client record of each October 17 reply |
| `test-sets/<set>/manifest.json`, `truth.private.json` | For `seed1`, `seed2`, `seed3` and `developed`: the manifest (request hashes, build arguments, window rule, code hashes) and the answer key. The key of the 308 requests is in [../2026-10-22-picture-test/test-set/](../2026-10-22-picture-test/test-set/) |
| [pictures/](pictures/) | Pictures as sent, decoded from request bodies (listed below) |
| `runtime/<job>/` | The llama-server build, loaded modules, the GPU at the start, and `sha256.txt`: the hashes of the llama.cpp files, the test set and the scripts the job ran |
| `runtime/<job>/server/<model>.cmd`, `.log.gz`, `.models.json`, `.gpu.txt` | Per model: the server command line, its log (gzip copy), the model list it served and the GPU memory once it answered |
| `job/<job>.out` | The job output, as the job copied it into its archive |
| [flow/](flow/) | Job scripts and outputs of the two flow runs, the developed case's settings (`system/`, `constant/`) and a summary of its log |
| `miss-analysis/<job>.json`, [miss_analysis.py](miss_analysis.py) | For every position answer more than 10 % off in a window job: the speed (or pressure) at the cell the model named, relative to the true extreme. The script needs the frames of the test set, which are in the release |
| [independent-recount.py](independent-recount.py), [independent-recount.json](independent-recount.json) | A recount without the test code (below) |
| [manifest.json](manifest.json) | Origins, sizes and hashes of the files here |

Pictures: `seed1-flow-window-v1-step003000-w4.png` and
`seed1-flow-window-v2-step003000-w4-U.png` / `-p.png` (one request in both
styles; 12B was 26 % off with v1 and 1.9 % with v2);
`developed-flow-window-v2-step080000-w3-U.png` / `-p.png` (12B within 0.4 %);
`developed-flow-window-v2-step124000-w1-U.png` (12B 61 % off: the brightest
spot, at y 19 %, is little brighter than the free stream above it, where the
answer was).

## Setup

- Models: the Gemma rows of `models.tsv` as in the
  [first October 22 test](../2026-10-22-picture-test/README.md#setup); the
  Qwen rows are Q8_0 builds with their own projectors:
  `Qwen/Qwen3-VL-8B-Instruct-GGUF@f982a075…`,
  `Qwen/Qwen3-VL-32B-Instruct-GGUF@e3e1fe0c…`,
  `unsloth/Qwen3.5-27B-GGUF@3221f178…` and
  `ggml-org/Qwen3.5-35B-A3B-GGUF@3127ef0b…`. Every file passed its SHA-256
  check before the model ran.
- Servers: llama.cpp b11429 (commit `d812350`), `--n-gpu-layers 99`, context
  4096, batch and ubatch 512, image-token limit 256, one slot, reasoning off;
  job 24757382 used an image-token limit of 1024 and context 8192.
- Requests and scoring as in the first test: temperature 0, `max_tokens` 320,
  seed 20261021, no prompt cache; right within 10 % of the plotted range. In
  the window sets every request has its own plotted range, so the
  fixed-answer column is the best single integer answer over the whole set.

## Recount

`python3 independent-recount.py` (no third-party packages) recomputes, from
`metrics.jsonl` and the answer keys only, every count cell of the six reports:
answered; fastest flow and lowest pressure within 10 %; the three trend words;
the fixed-answer column; and, for the 308 requests, the October 17 "located"
counts, which it reads from the runner's location field. Against the six reports: 134 rows checked, none differ. It also
writes the numbers the report derives: median distances, the clear-change
trend counts, the three seeds combined and where the fastest cell lies in each
set. It does not check the token and time columns.

## Notes

- The footer of the window-test reports says the fixed-answer column is "what
  one fixed answer per plotted range would get". The column holds one fixed
  answer for the whole set, as described above; the label was corrected in
  `window_test.py` after these jobs. The recount checks the numbers.
- In the window jobs each model folder also has `summary.json` files with 0
  attempted requests for the sets of the 308-request test, which were not run;
  they are left out here.
- The job archives have a second copy of each server log, named by model and
  made before the server stopped; the stamped logs used here are complete.
- The llama.cpp log warns, for every Qwen model, that Qwen-VL models need at
  least 1024 image tokens for grounding tasks and suggests
  `--image-min-tokens 1024`. That option was not used.
- Code that ran: the `llm_demo` folder of `58e00d9` from the picture-test
  bundle, with `window_test.py` and `window_test.slurm` added, the Qwen rows
  in `models.tsv` and, from job 24757382 on, `start_server.sh` reading
  `LLM_IMAGE_TOKENS`; `runtime/<job>/sha256.txt` has the hash of every script.
  Job 24757459 ran from the checkout of the solver run (see
  [2026-10-22-live-v2](../2026-10-22-live-v2/README.md)).
- `seed1` to `seed3` were built with the code of the picture-test bundle plus
  `window_test.py`, `developed` with the code of the solver run, after the
  request builder moved to `readable_request.py`; the hashes are in each
  manifest. The prompts and the picture style are the same.
- `truth.private.json` means withheld from the model input, not private
  personal information.
- The records contain cluster paths and server process ids as provenance.
