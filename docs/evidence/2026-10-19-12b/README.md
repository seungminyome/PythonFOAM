# October 19 evidence, Gemma 4 12B on a GPU node

The October 17 paired replay sent again, this time to Gemma 4 12B QAT Q4_0 on
one NVIDIA A30 of the MedicineBow cluster (University of Wyoming). Slurm job
24696203, code `934da23`; the code that builds and scores the requests is
byte-identical to `23089bb`. No solver ran.

[October 17 report](../../results.md#same-replay-with-gemma-4-12b-on-a-gpu-2026-10-19) ·
[E2B records of the same requests](../2026-10-17/README.md)

## Files

| File | What it contains |
|---|---|
| [ablation/](ablation/) | The six requests, raw and parsed replies, results and metrics, the runner's [manifest](ablation/manifest.json) and [summary](ablation/summary.json), and the GPU name, model list and runtime manifest the job copied in |
| [answer-review.json](answer-review.json) | Manual review of the six answers, separate from the automatic metrics |
| [job/replay_12b.slurm](job/replay_12b.slurm) | The batch script as run, with the site lines |
| [job/pod-12b-replay-24696203.out](job/pod-12b-replay-24696203.out) | Job output |
| [job/sacct.txt](job/sacct.txt) | Slurm accounting for the GPU check (job 24695930), the build jobs and the replay |
| [runtime/server-20261019T090809Z.txt](runtime/server-20261019T090809Z.txt) | llama-server log |
| [runtime/build-24696057.txt](runtime/build-24696057.txt), [runtime/build_llama.sbatch](runtime/build_llama.sbatch) | Source build of llama.cpp b11429 with CUDA, and its batch script |
| [runtime/build-24695932.txt](runtime/build-24695932.txt), [runtime/build_llama-24695932.sacct-B.txt](runtime/build_llama-24695932.sacct-B.txt) | The failed first build on a CPU node, and its batch script |
| [runtime/sha256.txt](runtime/sha256.txt) | Hashes of the weights, the projector and the prebuilt llama.cpp archives (not used) |
| [manifest.json](manifest.json) | File origins, sizes and hashes |

## Setup

- The six request bodies are the October 17 ones with only `model` changed
  (`gemma-4-12b-it-qat-q4_0-vision`): same question, numbers and PNG
  (`05a876ff…`), seeds 20261017 to 20261019, order A1 B1 B2 A2 A3 B3.
- Gemma 4 12B QAT Q4_0 (11,907,350,576 parameters, 6,975,879,296-byte GGUF)
  and its image projector, from `google/gemma-4-12B-it-qat-q4_0-gguf`.
- llama.cpp b11429 (commit `d812350`, the same as for E2B) built from source
  with GCC 14.2.0 and CUDA 12.8; all layers on the GPU, context 2048, one
  slot, reasoning off. The server lowered the image-token limit from 256 to
  128 because `--ubatch-size` is 128. The image added 106 prompt tokens, as
  with E2B.
- The job started its own server, so the first request found an empty prompt
  cache (`cache_n` 0). The model loaded in 2.7 s; 7713 MiB of the 24576 MiB
  GPU memory were in use once the server answered.

## Results

| | E2B, CPU, 2026-10-17 | 12B, A30, 2026-10-19 |
|---|---:|---:|
| Numbers only: position given | (0.6012, 0.1143) m, 3 of 3 | none, "unknown" in 3 of 3 |
| Numbers only: distance from the true cell | 60.92 cm | not scored |
| Numbers + image: position given | (0.5, 0.1143) m, 3 of 3 | none, "unknown" in 3 of 3 |
| Numbers + image: distance from the true cell | 50.97 cm | not scored |
| Time per request, numbers only | 14.5 to 55.6 s | 2.0 to 3.3 s |
| Time per request, numbers + image | 13.2 to 20.8 s | 2.1 to 2.7 s |
| First prompt on an empty cache | 1461 tokens in 41.3 s | 1466 tokens in 1.6 s |
| Generation | 8.5 to 8.9 tokens/s | 62.3 to 62.8 tokens/s |
| Words per answer (under 45 asked) | 28 to 34 | 52 to 54 |

Neither model located the maximum. E2B gave a wrong position every time; 12B
gave none, which is not a zero error. All 12B answers quote the maximum speed
from the input correctly (82.5275 or 82.53 m/s). The three image answers add,
as a possible interpretation, that high velocity is "concentrated near
x=0.00 m". The true x is 0.000538 m, but no y is given, the same answers say
exact coordinates are not provided, and the scorer reads `observations` only,
so this is not counted. Two numbers-only answers blamed "the image" although
none was sent, and the same two read the SVD energy fraction of Ux as a flow
direction. The automatic checker flagged nothing;
[answer-review.json](answer-review.json) lists these points with the texts.

The time difference mixes a larger model, a GPU against a CPU, and a fresh
server against a warm one, so it isolates nothing.

## Notes

- The clone was at `934da23` with four site lines of `replay_12b.slurm`
  edited and not committed (account, partition, module, Python on PATH);
  [job/replay_12b.slurm](job/replay_12b.slurm) is the file as run.
- The prebuilt b11429 CUDA libraries need GLIBC_2.38 and MedicineBow has 2.34,
  so llama.cpp was built from source. The first build (job 24695932, CPU node)
  failed at the final link with `libcuda.so.1` not found; the second (job
  24696057, A30 node, CUDA stub library in `LDFLAGS`) worked in 6 min 22 s.
  Which of the two changes fixed the link was not isolated. An earlier `srun`
  (job 24695931) failed because its script sat in a login-node `/tmp`
  directory.
- [runtime/sha256.txt](runtime/sha256.txt) and
  [ablation/runtime_manifest_12b.json](ablation/runtime_manifest_12b.json)
  hash the prebuilt archives, which were downloaded but not used;
  `server_version` in the latter names the source build. The built binary was
  not hashed at run time.
- No solver ran, so there are no callback times. The 78.255546163 s in
  [ablation/manifest.json](ablation/manifest.json) is the October 17 E2B value,
  marked `recorded_not_new`.
- The job ran no unit tests.
- Not in this folder: the weights, the projector, the llama.cpp archives and
  binaries, and the job's own tarball, which holds the same 44 files as
  [ablation/](ablation/).
