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
| `build_llama_cuda.sh` | Fallback: build llama.cpp b11429 from source with CUDA if the prebuilt binary does not run (older glibc, other CUDA). |

## Getting the files onto the cluster

Either works; the job scripts detect the layout.

```bash
git clone https://github.com/seungminyome/PythonFOAM.git && cd PythonFOAM
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
sbatch --account=<account> --partition=mb-a30 PODFoam/llm_demo/hpc/picture_test.slurm
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
the published E2B answers). With `GH_TOKEN` (contents write access) and
`RESULTS_RELEASE=<tag>` the job also uploads the tarball to that GitHub
release. With `CLEANUP_MODELS=1` it deletes the model files it downloaded
itself (`fetched.txt`), with `CLEANUP_MODELS=all` the `models/<key>` folders of
every key in `MODELS`; the 12B files are never deleted. Use neither while
another job uses the same `POD_LLM_RUNTIME`. Before any model starts, the job
runs `picture_test.py check`, which compares every request file and the answer
key with the manifest.

Run on 2026-10-22 as Slurm job 24756981, on one NVIDIA RTX A6000 (49,140
MiB; the command above names mb-a30, and the records do not say which
partition the job ran in): all seven models, 308 of 308 requests each; the
seven model runs took 83 minutes, model loading included. With llama.cpp
b11429 every model loaded and answered, 26B-A4B and 31B included; 31B had
20,128 MiB of GPU memory in use when its server first reported ready. Whether
31B fits in the 24 GB of an A30 was not tried. Results:
[October 22 report](../../../../docs/results-20261022.md),
[evidence](../../../../docs/evidence/2026-10-22-picture-test/README.md).

## Tested on

MedicineBow (University of Wyoming ARCC), 2026-10-19, paired replay only:
`replay_12b.slurm` from `934da23`, Slurm job 24696203, 35 s on one NVIDIA A30
(24 GB). Site lines used ([as run](../../../../docs/evidence/2026-10-19-12b/job/replay_12b.slurm)):

```bash
#SBATCH --account=<account>
#SBATCH --partition=mb-l40s,mb-a30
module load arcc/1.0 gcc/14.2.0 cuda-toolkit/12.8.0
export PATH=<python 3 with numpy>/bin:$PATH
```

The prebuilt b11429 CUDA libraries need GLIBC_2.38 and MedicineBow has 2.34,
so llama.cpp was built from source with `build_llama_cuda.sh` (job 24696057,
6 min 22 s; [batch script](../../../../docs/evidence/2026-10-19-12b/runtime/build_llama.sbatch)):

```bash
#!/bin/bash
#SBATCH --partition=mb-a30,mb-l40s
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
module load arcc/1.0 gcc/14.2.0 cuda-toolkit/12.8.0
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

`demo_12b.slurm` (MedicineBow has no OpenFOAM module), the prebuilt CUDA
binaries, `LLAMA_CUDA=13.4`, the L40S partition and the tarball layout of the
12B scripts (`picture_test.slurm` ran from its own bundle with the same layout
on 2026-10-22).
`start_server.sh` fails fast if the server does not answer `/health` within ten
minutes; the log is in `llm-runtime-12b/server-*.log`.
