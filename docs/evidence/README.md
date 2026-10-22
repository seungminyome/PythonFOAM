# Evidence

Recorded runs, one directory per test date (`2026-10-19-12b` holds that
day's 12B replay on a GPU node, `2026-10-22-picture-test` the picture-reading
test). Requests, responses, arrays and
logs keep their recorded bytes (in 2026-10-20 the solver logs and telemetry
are gzip copies); each directory has a hash manifest.

| Directory | Run | Code | Report |
|---|---|---|---|
| [2026-10-22-picture-test/](2026-10-22-picture-test/README.md) | Slurm job 24756981: the same 308 prepared requests to each of seven Gemma 4 models (E2B to 31B) on an NVIDIA RTX A6000 (MedicineBow); answer key and an independent re-scoring | `58e00d9` | [results-20261022.md](../results-20261022.md) |
| [2026-10-20/](2026-10-20/README.md) | `pod-llm-async.pp7agC`: five asynchronous cases on 3000 steps; `pod-llm-async.8YC6bG`: windowed frames; describe and sequence replays | `9449085` | [results-20261020.md](../results-20261020.md) |
| [2026-10-19-12b/](2026-10-19-12b/README.md) | Slurm job 24696203: the October 17 paired replay with Gemma 4 12B QAT on an NVIDIA A30 (MedicineBow); no position scored, the image answers say only "near x=0.00 m" | `934da23` (request and scoring code equal to `23089bb`) | [results.md](../results.md#same-replay-with-gemma-4-12b-on-a-gpu-2026-10-19) |
| [2026-10-19/](2026-10-19/README.md) | `pod-llm-demo.o5sNLJ`: repeat of the October 17 run and replay, same hashes and replay coordinates | `23089bb` (code), `4187659` (docs) | [results.md](../results.md#repeat-on-2026-10-19) |
| [2026-10-17/](2026-10-17/README.md) | `pod-llm-demo.LRfJBN`: five solver cases and the paired image/no-image replay | `23089bb` | [results.md](../results.md) |
| [2026-10-13/](2026-10-13/README.md) | `pod-llm-demo.SwwR2e`: first five-case run with the image path | `9ae54d0` | [results-20261013.md](../results-20261013.md) |

The picture test's two archives (the input bundle with all 308 requests and
the job's results with every raw reply) are assets of the
[picture-test-2026-10-22](https://github.com/seungminyome/PythonFOAM/releases/tag/picture-test-2026-10-22)
release. Complete solver outputs (all time directories) are release assets, not in the
repository (for 2026-10-20 the five cases of `pod-llm-async.pp7agC`; the
windowed frame run `pod-llm-async.8YC6bG` is not in the release, and this
repository has its frames and run records but not its time directories): [2026-10-20](https://github.com/seungminyome/PythonFOAM/releases/tag/pod-insitu-async-2026-10-20),
[2026-10-17](https://github.com/seungminyome/PythonFOAM/releases/tag/pod-insitu-tests-2026-10-17),
[2026-10-13](https://github.com/seungminyome/PythonFOAM/releases/tag/pod-insitu-demo-2026-10-13).
