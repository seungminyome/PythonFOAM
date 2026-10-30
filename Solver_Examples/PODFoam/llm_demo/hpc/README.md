# Running the 12B model on a GPU node

Scripts to repeat the E2B measurements with Gemma 4 12B QAT Q4_0 on a cluster
GPU. The paired replay sends the 2026-10-17 requests with only the model name
changed. The solver and callback code have changed since 2026-10-17
(`9449085`), so `demo_12b.slurm` does not rerun the October 17 code.

The paired replay has been run once, on MedicineBow (2026-10-19): see
[Tested on](#tested-on) and the
[records](../../../../docs/evidence/2026-10-19-12b/README.md).

| Script | Does |
|---|---|
| `setup_12b.sh` | Downloads llama.cpp b11429 (CUDA build) and the 12B weights + image projector from `google/gemma-4-12B-it-qat-q4_0-gguf`, records SHA-256 of these and of the `llama-server` in use. About 8 GB. |
| `start_server.sh` / `stop_server.sh` | llama-server on the node's GPU with the same settings as the E2B runs (context 2048, one slot, 256 image tokens requested, reasoning off), all layers on the GPU. Writes `server.pid`. With the 12B projector the server lowers the image-token limit to 128 because `--ubatch-size` is 128. |
| `replay_12b.slurm` | Paired replay of the 2026-10-17 step-5 state: three pairs, numbers only vs numbers + image, seed 20261017. No OpenFOAM needed. |
| `demo_12b.slurm` | Bridge validation, the five solver conditions, verification, and the paired replay of the new state. Needs OpenFOAM v2106 on the node. |
| `picture_test.slurm`, `fetch_models.sh`, `models.tsv` | The picture-reading test for several model sizes (prepared 2026-10-21, run 2026-10-22); see [below](#picture-reading-test-run-2026-10-22). |
| `window_test.slurm` | The random-window picture test (`window_test.py`) for the models in `MODELS`; see [below](#random-window-test-and-qwen-models-run-2026-10-22). |
| `async_v2.slurm` | The asynchronous suite with v2 pictures from the running solver and Gemma 4 12B, started from a developed flow, then the describe sweep; OpenFOAM in an Apptainer image, llama-server on the host GPU; see [below](#v2-pictures-from-the-running-solver-async_v2slurm-run-2026-10-22). |
| `periodic_v2.slurm` | A long run with a v2 describe request every N steps and its twin without requests (`run_periodic.py`), from the baseline staging of an `async_v2.slurm` run; cost, memory and pipe traffic. |
| `build_llama_cuda.sh` | Fallback: build llama.cpp b11429 from source with CUDA if the prebuilt binary does not run (older glibc, other CUDA). |

## Getting the files onto the cluster

Either works; the job scripts detect the layout.

```bash
git clone <URL of this repository> PythonFOAM && cd PythonFOAM
# or: tar -xzf pythonfoam-12b-hpc-20261019.tar.gz && cd pythonfoam-12b-hpc
```

The saved state for the replay is in the repository
(`docs/evidence/2026-10-17/pod-llm-demo.LRfJBN/fixed-pod`), so a clone needs
nothing else. If compute nodes have no internet, run the download once on the
login node before submitting:

```bash
export HF_TOKEN=hf_... POD_LLM_RUNTIME=$PWD/llm-runtime-12b
bash Solver_Examples/PODFoam/llm_demo/hpc/setup_12b.sh
```

## Before submitting

1. Accept the Gemma licence on
   [huggingface.co/google/gemma-4-12B-it-qat-q4_0-gguf](https://huggingface.co/google/gemma-4-12B-it-qat-q4_0-gguf)
   and create a read token. `export HF_TOKEN=hf_...` in the shell you submit from.
2. Edit the site lines in the `.slurm` file (CUDA 12.8 or 13.4 and a Python 3
   with numpy; matplotlib and OpenFOAM v2106 for the demo). `LLAMA_CUDA=13.4`
   selects the CUDA 13 build, which needs a driver of version 580 or newer.
   `async_v2.slurm` and `periodic_v2.slurm` have no lines to edit; they read
   `SIF` and `PYTHON` (required) and `POD_HOST_MODULES` (optional) from the
   environment and write them, with `module list`, to `site.txt`. `SIF` is an
   OpenFOAM v2212 image with its compilers and its bashrc at
   `/usr/lib/openfoam/openfoam2212/etc/bashrc` (set `OPENFOAM_BASHRC` if it is
   elsewhere), for example from
   `apptainer pull docker://opencfd/openfoam-dev:2212`.
3. Check the partition and `--gres` syntax match the cluster; give the account
   and partition on the `sbatch` command line.
4. `HF_TOKEN` is needed only while the weights are not yet in
   `POD_LLM_RUNTIME`.

## Submit

```bash
# from the repository root (or the tarball root)
export HF_TOKEN=hf_...
sbatch Solver_Examples/PODFoam/llm_demo/hpc/replay_12b.slurm   # 1 GPU; 35 s on an A30 once the runtime is in place
sbatch Solver_Examples/PODFoam/llm_demo/hpc/demo_12b.slurm     # only if OpenFOAM v2106 is available
# from the tarball the path is PODFoam/llm_demo/hpc/...
```

Results land in `results/`: `replay-12b-<jobid>.tar.gz` (six requests, replies,
`summary.json`, `manifest.json`, GPU name, runtime manifest) and
`demo-12b-<jobid>.tar.gz` (verification JSON, timings, `run-archive.tar.gz`,
the replay on the new state).

## What to compare

- Replay: `summary.json` → `numeric_only` and `numeric_plus_image`, position
  error against `ground_truth.private.json` (true cell at x = 0.000538 m,
  y = 0.01271 m). E2B gave 60.92 cm and 50.97 cm on this state; 12B on an A30
  said the position is unknown in all six answers, so nothing was scored.
- Demo: `timings.json` → `cpp_measured_full_callback_s` per case
  (E2B on CPU: 0.49 / 78.26 / 39.67 / 0.51 / 4.01 s), and
  `demo-verification.json` → `status` must be `PASS` with 45 identical files.
- `server_timings.cache_n` in each result: 0 or 1 means a cold prompt cache (0
  on a freshly started server, as in the 12B run).

## Picture-reading test (run 2026-10-22)

`picture_test.slurm` sends one prepared set of 308 requests to each model in
`MODELS`, one model after another on one GPU. The set is built on a
workstation with `picture_test.py build` (matplotlib needed) and copied to the
cluster; the job itself needs only Python 3 with numpy and no OpenFOAM.

| Set | Requests | Content |
|---|---:|---|
| `oct17-paired` | 6 | the 2026-10-17 paired requests; only the model name changes |
| `oct17-paired-cold` | 6 | the same six with `cache_prompt: false` |
| `oct20-replay` | 24 | the 2026-10-20 describe and sequence requests; only the model name changes |
| `control-position-v1`, `-v2` | 32 each | synthetic fields with one bright \|U\| spot and one dark p spot at chosen places, whole domain and window |
| `planted-position-v1`, `-v2` | 32 each | saved states (steps 1000, 2500, 4000, 5500) with one narrow \|U\| peak and one narrow p dip added at least 15 % away from the step corner |
| `control-trend-v1`, `-v2`, `-v2own` | 18 each | synthetic three-time sequences: every speed trend x pressure trend x spot motion once |
| `flow-describe-v1`, `-v2` | 24 each | saved states every 500 steps up to step 6000, whole domain and window |
| `flow-sequence-v1`, `-v2`, `-v2own` | 14 each | seven triples of saved states, whole domain and window |

v1 is the picture the solver sends (`pod_image.py`: two panels, 640x360,
colour range per picture). v2 is `readable_image.py`: one field per picture,
1024x576, axes in percent of the plotted range with a grid line every 10 %,
the colour bar labelled with five values from the minimum to the maximum, and
in sequences one colour range for all frames. v2own is v2 with each picture's own colour range; its prompt
differs from the v2 prompt only in the colour-scale sentence and in what the
trends are judged from (colours or colour-bar numbers), so v2 against v2own
isolates the shared colour range. v2 also sends about five times
the image tokens of v1. The new sets send `cache_prompt: false`, so every
prompt is processed in full. The flow states come from a PODFoam run without
model requests (6000 steps of 5e-7 s, written every 250 steps; the first 12
written times are identical to the 2026-10-20 run). In every flow state the
fastest flow and the lowest pressure are at the step corner and the trend
words are the same in nearly every sequence, so each summary also gives the
score of one fixed
answer (`constant_answer_baseline`); the controls and planted sets are where
reading can be told apart from a fixed answer.

Models (`models.tsv`, pinned revisions and SHA-256; none of these repositories
needs a token):

| Key | Repository, files | Download |
|---|---|---:|
| `e2b` | `ggml-org/gemma-4-E2B-it-GGUF`, Q4_0 + Q8_0 projector, the pair used on the CPU | 3.4 GB |
| `e2b-bf16` | the same Q4_0 weights + the BF16 projector of that repository | 1.0 GB more |
| `e2b-qat` | `google/gemma-4-E2B-it-qat-q4_0-gguf`, BF16 projector | 4.3 GB |
| `e4b` | `google/gemma-4-E4B-it-qat-q4_0-gguf`, BF16 projector | 6.1 GB |
| `12b` | `google/gemma-4-12B-it-qat-q4_0-gguf`, the files of 2026-10-19 | 7.2 GB |
| `26b` | `google/gemma-4-26B-A4B-it-qat-q4_0-gguf`, BF16 projector | 15.6 GB |
| `31b` | `google/gemma-4-31B-it-qat-q4_0-gguf`, BF16 projector | 18.9 GB |
| `qwen3vl-8b` | `Qwen/Qwen3-VL-8B-Instruct-GGUF`, Q8_0 + F16 projector (added 2026-10-22) | 9.9 GB |
| `qwen3vl-32b` | `Qwen/Qwen3-VL-32B-Instruct-GGUF`, Q8_0 + F16 projector | 36.0 GB |
| `qwen35-27b` | `unsloth/Qwen3.5-27B-GGUF`, Q8_0 + BF16 projector (a third-party conversion) | 29.5 GB |
| `qwen35-35b` | `ggml-org/Qwen3.5-35B-A3B-GGUF`, Q8_0 + Q8_0 projector | 37.5 GB |
| `qwen3vl-32b-q4` | the same repository, Q4_K_M + F16 projector (added 2026-10-27, same weight precision as the Gemma QAT files) | 21.0 GB |
| `qwen35-27b-q4` | `unsloth/Qwen3.5-27B-GGUF`, Q4_K_M + BF16 projector | 17.7 GB |
| `qwen35-35b-q4` | `unsloth/Qwen3.5-35B-A3B-GGUF`, Q4_K_M + BF16 projector | 22.9 GB |

e2b against e2b-bf16 changes only the projector; e2b-qat has other weights
and Google's own projector file (BF16, like the one of e2b-bf16). Every model gets the same server: context 4096 (a v2 sequence
with six images is about 2,200 prompt tokens), batch and ubatch 512 (so no
projector lowers the 256-token image limit), all layers on the GPU, otherwise
as `start_server.sh`. The job keeps its server's pid, log and stamp files in
`results/picture-test-<jobid>/server/` (`POD_LLM_STATE`) and uses port
20000 + job id mod 10000, so it does not meet another job's server.

```bash
# on the cluster, from the package root
export POD_LLM_RUNTIME=<folder that holds llama-b11429-cuda/ from the 12B run>
bash PODFoam/llm_demo/hpc/fetch_models.sh e2b e2b-bf16 e2b-qat e4b 12b 26b 31b   # login node if compute nodes are offline
sbatch --account=<account> --partition=<partition> PODFoam/llm_demo/hpc/picture_test.slurm
# fewer models: sbatch --export=ALL,MODELS="e2b 12b" ...
```

Results land in `results/picture-test-<jobid>.tar.gz`: one folder per model
(each set's `summary.json` and `metrics.jsonl`, every reply; the sent request
bodies are left out because each is the prepared body with the model name
replaced, and its SHA-256 is in `metrics.jsonl`), the server log and command
line per model, `llama-server-version.txt`, `nvidia-smi.txt`, `modules.txt`,
`sha256.txt` (llama.cpp folder, test set, scripts), `failed.txt` if anything
failed, the job log so far, and `report.md` (`picture_test.py report`: counts
out of attempted requests, the fixed-answer score, item-by-item v1/v2 and
v2/v2own comparisons, and for each model how many 2026-10-17/20 answers equal
the published E2B answers). With `GH_TOKEN` (contents write access),
`RESULTS_REPO=<owner/name>` and `RESULTS_RELEASE=<tag>` the job also uploads the
tarball to that GitHub release. With `CLEANUP_MODELS=1` it deletes the model
files it downloaded itself (`fetched.txt`), with `CLEANUP_MODELS=all` the
`models/<key>` folders of every key in `MODELS`; the 12B files are never
deleted. Use neither while another job uses the same `POD_LLM_RUNTIME`. Before any model starts, the job
runs `picture_test.py check`, which compares every request file and the answer
key with the manifest.

Run on 2026-10-22 as Slurm job 24756981, on one NVIDIA RTX A6000 (49,140
MiB; submitted to the mb-a6000 partition, because the scheduler expected the
mb-a30 queue to start it two weeks later): all seven models, 308 of 308 requests each; the
seven model runs took 83 minutes, model loading included. With llama.cpp
b11429 every model loaded and answered, 26B-A4B and 31B included; 31B had
20,128 MiB of GPU memory in use when its server first reported ready. Whether
31B fits in the 24 GB of an A30 was not tried. Results:
[October 22 report](../../../../docs/results-20261022.md),
[evidence](../../../../docs/evidence/2026-10-22-picture-test/README.md).

## Random-window test and Qwen models (run 2026-10-22)

In the flow states of the picture test the fastest flow and the lowest
pressure sit at the step corner, so one fixed answer scores 24 of 24.
`window_test.py` draws the same states with the plotted window placed at
random around the fastest cell, so that the answer moves from picture to
picture (see the [llm_demo README](../README.md#random-window-picture-test-window_testpy)).
`window_test.slurm` runs a set like `picture_test.slurm` does; `LLM_CTX` and
`LLM_IMAGE_TOKENS` (default 4096 and 256, read by `start_server.sh`) can be
raised to test the image-token cap, and `LLM_IMAGE_MIN_TOKENS` passes
`--image-min-tokens` (the 1024 that llama.cpp suggests for Qwen-VL).
`PICTURE_TEST_SCRIPT=sequence_test.py` runs a trend set built by
`sequence_test.py` instead.

```bash
python3 Solver_Examples/PODFoam/llm_demo/window_test.py build --states <case> \
    --centres docs/evidence/2026-10-20/pod-llm-async.pp7agC/async-no-llm/llm_observation/step-000250/fields.npz \
    --old-manifest <picture-test-20261021/manifest.json> --output <set> [--seed N] [--first-step N --describe-every N --last-step N]
export POD_LLM_RUNTIME=$PWD/llm-runtime-12b PICTURE_TEST_SET=<set>
sbatch --export=ALL,MODELS="12b 26b 31b qwen35-35b" --account=<account> --partition=<partition> \
    Solver_Examples/PODFoam/llm_demo/hpc/window_test.slurm
```

Runs on 2026-10-22, all on one RTX A6000: the four Qwen models on the 308
picture-test requests (job 24757327); the start-up states (a `pimpleFoam` run
of 6000 steps of 5e-7 s in the v2212 image, job 24757337, states every 500
steps) with four random windows each (96 requests) for eleven models (job
24757344), the six largest again with two other window seeds (jobs 24757384,
24757383) and with `LLM_IMAGE_TOKENS=1024 LLM_CTX=8192` (job 24757382); and a
developed flow (below) with four windows on each of 35 states (280 requests,
job 24757459). Results: [report](../../../../docs/results-20261022-live.md),
[evidence](../../../../docs/evidence/2026-10-22-window-test/README.md).

## v2 pictures from the running solver (`async_v2.slurm`, run 2026-10-22)

MedicineBow has no OpenFOAM module, but OpenFOAM v2212 runs in an Apptainer
image (the one used for solids4foam there). PODFoam builds in it unchanged
against a conda Python 3.11 with numpy and matplotlib (the image has no
Python), and its bridge validation passes there:

```bash
module load apptainer
apptainer exec <of2212.sif> bash -c '
    source /usr/lib/openfoam/openfoam2212/etc/bashrc
    export LD_LIBRARY_PATH=<conda>/lib:$LD_LIBRARY_PATH POD_OPENFOAM_VERSION=v2212 PYTHON=<conda>/bin/python3
    Solver_Examples/PODFoam/validation/run_v2106.sh'      # writes $POD_WORKSPACE/pod-v2212.XXXXXX
```

The image shares the host's network and process namespaces, so the solver's
callback inside it reaches a llama-server started on the host GPU at
127.0.0.1. `async_v2.slurm` starts the server (12B, context 4096, batch and
ubatch 512, the picture-test settings), records the git state of the
checkout on the host (the image has no git; `pack_run.py` copies it), and
runs `run_demo.sh` with `POD_SUITE=async` and `LLM_IMAGE_STYLE=v2` in the
image, then `run_live_sweep.py`. Where that file is not in the tree, the job
ends after the suite and refuses `POD_SUITE_RUN` (the sweep only).

```bash
# from the repository root, after a validation run and a developed run of the same mesh
export SIF=<of2212.sif> PYTHON=<conda>/bin/python3   # required: the image, a Python 3 with numpy + matplotlib
export POD_HOST_MODULES="<modules>"                  # optional: what the source-built llama-server needs
export POD_REFERENCE_RUN=<pod-v2212.XXXXXX> LLM_LONG_START=<developed case>/0.1
sbatch --account=<account> --partition=<partition> Solver_Examples/PODFoam/llm_demo/hpc/async_v2.slurm
```

Apptainer comes from the `PATH`, or else from `module load apptainer`.

Defaults: 6000 steps of 5e-6 s from the start state, written every 250
steps, the describe request at step 250, sequence frames at 3000, 3250 and
3750, the window x 0 to 0.12 m, y 0 to 0.04 m, then eleven sweep requests
every 500 steps (`SWEEP_STEPS`, `SWEEP_PARALLEL`). `LLM_KILL_JOIN_S=0.2`:
on these nodes a killed worker forked from the 0.5 GB solver takes about
40 ms to be reaped, longer than the default of then, 0.02 s (0.1 s since
2026-10-27). The developed state came
from `pimpleFoam` in the same image on the validation run's `fixed-pimple`
case with only `controlDict` changed: 100 ms with an adaptive time step
(`maxCo 0.5`, `maxDeltaT 5e-6`), written every 1 ms (job 24757429). Run on
2026-10-22 as Slurm job 24757460; results in the
[report](../../../../docs/results-20261022-live.md), records in the
[evidence](../../../../docs/evidence/2026-10-22-live-v2/README.md).

On these nodes two timing unit tests (`test_image_rendered_when_request_disabled`,
`test_timeout_is_detected_by_polling`) fail with the default `LLM_KILL_JOIN_S`
for the same reason, also with the code before these changes, and pass with
`LLM_KILL_JOIN_S=0.2`; `test_connection_refused_is_reported_without_a_stall`
sometimes exceeds its 0.5 s bound by a few hundredths of a second.

## Runs of 2026-10-27

From the repository root on MedicineBow, with the conda Python first on
`PATH` (the system `python3` has no numpy) and the CUDA modules the
source-built llama-server needs (arcc/1.0, gcc/14.2.0 and cuda-toolkit/12.8.0
there):

```bash
export PATH=<python 3 with numpy>/bin:$PATH POD_LLM_RUNTIME=$PWD/llm-runtime-12b
export POD_HOST_MODULES="<modules>"
# trend test (sequence_test.py set), Gemma and Qwen
PICTURE_TEST_SET=<developed-sequence-test-20261027> PICTURE_TEST_SCRIPT=sequence_test.py \
  sbatch --export=ALL,MODELS="12b 26b 31b" --account=<account> --partition=<partition> \
  Solver_Examples/PODFoam/llm_demo/hpc/window_test.slurm
# 4-bit Qwen with the recommended image tokens
PICTURE_TEST_SET=<window set> LLM_IMAGE_TOKENS=1024 LLM_IMAGE_MIN_TOKENS=1024 LLM_CTX=8192 \
  sbatch --export=ALL,MODELS="qwen3vl-32b-q4 qwen35-27b-q4 qwen35-35b-q4" --account=<account> \
  --partition=<partition> Solver_Examples/PODFoam/llm_demo/hpc/window_test.slurm
# a describe request every 250 steps, 24,000 steps, and its twin
SIF=<of2212.sif> PYTHON=<conda>/bin/python3 POD_SUITE_RUN=<pod-llm-async.XXXXXX of a PASSed async_v2.slurm run> \
  sbatch --account=<account> --partition=<partition> Solver_Examples/PODFoam/llm_demo/hpc/periodic_v2.slurm
```

Jobs 24903974 to 24903978 (picture tests), 24903264 (periodic), 24903298 and
24903263 (repeats of the October 22 suite with `async_v2.slurm`; with
`POD_SUITE_RUN` set, `async_v2.slurm` runs only the sweep, as job 24903755
did), on the mb-a30 partition except 24903975 to 24903977 on mb-l40s. The first
two picture-test submissions that started stopped at once because
`window_test.slurm` no longer loaded the CUDA module
(`libcudart.so.12` not found); `POD_HOST_MODULES` was added for that. Results in the
[report](../../../../docs/results-20261027.md), records in the
[picture-test evidence](../../../../docs/evidence/2026-10-27-picture-tests/README.md)
and the [solver evidence](../../../../docs/evidence/2026-10-27-solver/README.md).

## Tested on

MedicineBow (University of Wyoming ARCC), 2026-10-19, paired replay only:
`replay_12b.slurm` from `934da23`, Slurm job 24696203, 35 s on one NVIDIA A30
(24 GB), partition mb-a30, modules arcc/1.0, gcc/14.2.0 and cuda-toolkit/12.8.0.
The site lines ([as run](../../../../docs/evidence/2026-10-19-12b/job/replay_12b.slurm)):

```bash
#SBATCH --account=<account>
#SBATCH --partition=<partition>
module load <modules>
export PATH=<python 3 with numpy>/bin:$PATH
```

The prebuilt b11429 CUDA libraries need GLIBC_2.38 and MedicineBow has 2.34,
so llama.cpp was built from source with `build_llama_cuda.sh` (job 24696057,
6 min 22 s, partition mb-a30, the same modules;
[batch script](../../../../docs/evidence/2026-10-19-12b/runtime/build_llama.sbatch)):

```bash
#!/bin/bash
#SBATCH --partition=<partition>
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
module load <modules>
export POD_LLM_RUNTIME=$PWD/llm-runtime-12b
export CMAKE_CUDA_ARCHITECTURES="80;89;90" BUILD_JOBS=16
export LDFLAGS="-L<cuda-toolkit>/lib64/stubs"
rm -rf "$POD_LLM_RUNTIME/llama.cpp-build"   # CMake reads LDFLAGS only on a fresh configure
mv "$POD_LLM_RUNTIME/llama-b11429-cuda" "$POD_LLM_RUNTIME/llama-b11429-cuda.prebuilt" 2>/dev/null || true
bash Solver_Examples/PODFoam/llm_demo/hpc/build_llama_cuda.sh
```

A first build on a CPU node without the stubs (job 24695932) failed at the
final link, `libcuda.so.1` not found; which of the two changes fixed it was not
isolated.

## Not checked here

`demo_12b.slurm` (the synchronous suite with OpenFOAM v2106 on the GPU node;
the asynchronous suite ran in the v2212 image instead), the prebuilt CUDA
binaries, `LLAMA_CUDA=13.4` and the tarball layout of the
12B scripts (`picture_test.slurm` ran from its own bundle with the same layout
on 2026-10-22).
`async_v2.slurm` and `periodic_v2.slurm` as they are now (settings from the
environment, `site.txt`, the sweep only when its file is in the tree) have run
only with stub commands, not on a GPU node; the jobs named above ran the earlier
text of these scripts, which held the site's paths and modules.
`start_server.sh` fails fast if the server does not answer `/health` within ten
minutes; the log is in `llm-runtime-12b/server-*.log`.
