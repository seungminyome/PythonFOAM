# Running the 12B model on a GPU node

Scripts to repeat the E2B measurements with Gemma 4 12B QAT Q4_0 on a cluster
GPU. The solver code, prompts, seeds and the saved state are the ones used on
2026-10-17; only the model and the machine change.

| Script | Does |
|---|---|
| `setup_12b.sh` | Downloads llama.cpp b11429 (CUDA build) and the 12B weights + image projector from `google/gemma-4-12B-it-qat-q4_0-gguf`, records SHA-256. About 8 GB. |
| `start_server.sh` / `stop_server.sh` | llama-server on the node's GPU with the same settings as the E2B runs (context 2048, one slot, 256 image tokens, reasoning off), all layers on the GPU. Writes `server.pid`. |
| `replay_12b.slurm` | Paired replay of the 2026-10-17 step-5 state: three pairs, numbers only vs numbers + image, seed 20261017. No OpenFOAM needed. |
| `demo_12b.slurm` | Bridge validation, the five solver conditions, verification, and the paired replay of the new state. Needs OpenFOAM v2106 on the node. |
| `build_llama_cuda.sh` | Fallback: build llama.cpp b11429 from source with CUDA if the prebuilt binary does not run (older glibc, other CUDA). |

## Before submitting

1. Accept the Gemma licence on
   [huggingface.co/google/gemma-4-12B-it-qat-q4_0-gguf](https://huggingface.co/google/gemma-4-12B-it-qat-q4_0-gguf)
   and create a read token. `export HF_TOKEN=hf_...` in the shell you submit from.
2. Edit the `module load` line in the `.slurm` file for your site (CUDA 12.8 or
   13.4 and a Python 3 with numpy; matplotlib and OpenFOAM v2106 for the demo).
   Set `LLAMA_CUDA=13.4` if the node's driver is too old for 12.8.
3. Check the partition and `--gres` syntax match the cluster.

## Submit

```bash
# package root: PODFoam/ and snapshot/ next to each other
export HF_TOKEN=hf_...
sbatch PODFoam/llm_demo/hpc/replay_12b.slurm     # 1 GPU, under an hour
sbatch PODFoam/llm_demo/hpc/demo_12b.slurm       # only if OpenFOAM v2106 is available
```

Results land in `results/`: `replay-12b-<jobid>.tar.gz` (six requests, replies,
`summary.json`, `manifest.json`, GPU name, runtime manifest) and
`demo-12b-<jobid>.tar.gz` (verification JSON, timings, `run-archive.tar.gz`,
the replay on the new state).

## What to compare

- Replay: `summary.json` → `numeric_only` and `numeric_plus_image`, position
  error against `ground_truth.private.json` (true cell at x = 0.000538 m,
  y = 0.01271 m). E2B gave 60.92 cm and 50.97 cm on this state.
- Demo: `timings.json` → `cpp_measured_full_callback_s` per case
  (E2B on CPU: 0.49 / 78.26 / 39.67 / 0.51 / 4.01 s), and
  `demo-verification.json` → `status` must be `PASS` with 45 identical files.
- `server_timings.cache_n` in each result: 1 means a cold prompt cache.

## Not checked here

The CUDA build and the 12B projector have not been run on this laptop (no GPU).
`start_server.sh` fails fast if the server does not answer `/health` within ten
minutes; the log is in `llm-runtime-12b/server-*.log`.
