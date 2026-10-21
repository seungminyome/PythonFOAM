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
binaries, `LLAMA_CUDA=13.4`, the L40S partition and the tarball layout.
`start_server.sh` fails fast if the server does not answer `/health` within ten
minutes; the log is in `llm-runtime-12b/server-*.log`.
