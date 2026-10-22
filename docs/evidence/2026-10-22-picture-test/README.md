# October 22 evidence, picture-reading test on a GPU node

Slurm job 24756981 on MedicineBow (University of Wyoming), one NVIDIA RTX
A6000 (49,140 MiB). On 2026-10-22 the model runs went from 01:20 to 02:43 MDT,
and the results reached the release at 02:45. The same 308 prepared requests
of `picture_test.py` were sent to each of seven Gemma 4 models in turn. No
solver ran. Code `58e00d9`.

[Report](../../results-20261022.md) ·
[How the set is built and run](../../../Solver_Examples/PODFoam/llm_demo/hpc/README.md#picture-reading-test-run-2026-10-22) ·
[Release with both archives](https://github.com/seungminyome/PythonFOAM/releases/tag/picture-test-2026-10-22)

## Files

| File | What it contains |
|---|---|
| [report.md](report.md) | The job's own summary (`picture_test.py report`): counts per model, set and mode, the fixed-answer scores, item-by-item v1/v2 and v2/v2own comparisons, agreement with the published E2B answers |
| `results/<model>/run.json` | Model alias, server note (repository, revision, files, server settings), sets, timeout, hashes of the test-set manifest and the answer key |
| `results/<model>/<set>/metrics.jsonl` | One line per request: the parsed answer and its score against the key, the hashes of the sent and the prepared request, prompt and completion tokens, server timings, wall time. For the two October 17 sets the location and grounding checks take the place of the parsed answer and score. |
| `results/<model>/oct17-paired*/<request>/result.json` | The client record of each October 17 reply, with the reply text and its parsed fields |
| `results/<model>/<set>/summary.json` | The runner's summary of that set |
| [test-set/manifest.json](test-set/manifest.json), [test-set/truth.private.json](test-set/truth.private.json) | The manifest of the test set (request hashes, build arguments, code hash) and the answer key |
| [pictures/](pictures/) | Seven pictures as sent, decoded from the request bodies |
| [runtime/server/](runtime/server/) | Per model: the llama-server command line, its log, the model list it served and the GPU memory once it answered (stamps below) |
| [runtime/llama-server-version.txt](runtime/llama-server-version.txt), [modules.txt](runtime/modules.txt), [nvidia-smi.txt](runtime/nvidia-smi.txt), [sha256.txt](runtime/sha256.txt) | The llama-server build, the loaded modules, the GPU at the start, and the hashes of the llama.cpp folder, the test set and the scripts |
| [job/job-so-far.out](job/job-so-far.out) | The job log, copied when the results were packed |
| [independent-rescore.py](independent-rescore.py), [independent-rescore.json](independent-rescore.json) | A re-scoring without `picture_test.py`. It recomputes every count cell of `report.md` from the answers and the key (the answered counts from the replies' status), checks the fixed-answer column and the item-by-item lines (518 checks, none differ), and derives the other numbers the report cites: totals, distances, trend designs, planted misses, the October 17 replies, time and memory. It does not check the token and time columns or the comparison with the published answers. Run it in this folder. |
| [manifest.json](manifest.json) | Origins, sizes and hashes of the files here |

Server stamps in `runtime/server/`: `20261022T072022Z` e2b, `T072559Z`
e2b-bf16, `T073132Z` e2b-qat, `T073701Z` e4b, `T074412Z` 12b, `T075904Z`
26b, `T081056Z` 31b.

## Setup

- Test set `picture-test-20261021`: manifest `52430fe7…`, answer key
  `01ecaed3…`. Before the first model the job ran `picture_test.py check`:
  308 requests checked, 0 problems. Every model file passed its SHA-256
  check.
- Models, from `run.json`:

  | Key | Served as | Repository @ revision, files |
  |---|---|---|
  | e2b | `gemma-4-E2B-it-Q4_0-vision` | `ggml-org/gemma-4-E2B-it-GGUF@b4243c15…`, `gemma-4-E2B-it-Q4_0.gguf` + `mmproj-gemma-4-E2B-it-Q8_0.gguf` |
  | e2b-bf16 | `gemma-4-E2B-it-Q4_0-bf16proj-vision` | same repository and weights + `mmproj-gemma-4-E2B-it-BF16.gguf` |
  | e2b-qat | `gemma-4-E2B-it-qat-q4_0-vision` | `google/gemma-4-E2B-it-qat-q4_0-gguf@675cff42…` |
  | e4b | `gemma-4-E4B-it-qat-q4_0-vision` | `google/gemma-4-E4B-it-qat-q4_0-gguf@4b4a2c1d…` |
  | 12b | `gemma-4-12b-it-qat-q4_0-vision` | `google/gemma-4-12B-it-qat-q4_0-gguf@29d09777…`, the files of 2026-10-19 |
  | 26b | `gemma-4-26B-A4B-it-qat-q4_0-vision` | `google/gemma-4-26B-A4B-it-qat-q4_0-gguf@d1c082be…` |
  | 31b | `gemma-4-31B-it-qat-q4_0-vision` | `google/gemma-4-31B-it-qat-q4_0-gguf@59dde245…` |

- Each model got its own server, started by the job: llama.cpp b11429
  (commit `d812350`, the source build of 2026-10-19), `--n-gpu-layers 99`,
  context 4096, batch and ubatch 512, image-token limit 256, one slot,
  reasoning off, port 26981. The command lines are in `runtime/server/*.cmd`.
  The GPU memory line was written when each server first answered `/health`,
  before any request.
- Projector types, read afterwards from the GGUF headers of the pinned files
  on Hugging Face (the job did not record them): Q8_0 for e2b, BF16 for all
  the others. The e2b-qat projector is Google's own file, not the BF16 file of
  e2b-bf16.

## Notes

- The input bundle (`pythonfoam-picture-test-20261021.tar.gz`, sha256
  `b4a3e332…`) holds the `llm_demo` folder of commit `58e00d9` (git archive),
  the test set, Korean instructions (`README.ko.md`), `SOURCE.txt` and
  `SHA256SUMS`. In
  [runtime/sha256.txt](runtime/sha256.txt) every script equals that commit
  except `hpc/picture_test.slurm` (`de18f174…`), whose site lines (module and
  PATH) were edited on the cluster; that file is not in the results.
- The job ran on an RTX A6000; the instructions named the A30 partition.
  Which partition was used is not in the records.
- The job archive (`picture-test-24756981.tar.gz`, sha256 `a8ea6c79…`, in the
  release) also has, for every request, the raw reply, the parsed reply, the
  client record and its metrics; of these only the client records of the
  October 17 replies are in this folder. The sent request
  bodies were not kept: each is the prepared body with `model` replaced, and
  `metrics.jsonl` gives the hashes of both.
- The archive has a second copy of each server log, command line, model list
  and GPU line under the model's name. Those logs are the first part of the
  ones in `server/`, copied before the server stopped (73 or 74 bytes
  shorter); the other three files are identical. Only the `server/` copies
  are here.
- Files named `*.log` at the source are stored as `.txt` because
  `.gitignore` excludes `*.log`; bytes unchanged.
- `job-so-far.out` was copied after the report was printed, so the packing
  and upload lines are not in it.
- `oct17-paired` and `oct20-replay` are the published request bodies with only
  the model name changed, so they use the server's prompt cache;
  `oct17-paired-cold` and the new sets send `cache_prompt: false`.
- `truth.private.json` means withheld from the model input, not private
  personal information.
- The records contain cluster paths and server PIDs as provenance.
