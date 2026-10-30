# Evidence

Recorded runs, one directory per test date (`2026-10-28-inflight`,
`2026-10-28-callback`, `2026-10-28-3d` and `2026-10-28-instability` hold
the tests of October 28, `2026-10-27-solver` and
`2026-10-27-picture-tests` hold the solver runs and the picture tests of
October 27, `2026-10-19-12b` holds that
day's 12B replay on a GPU node, `2026-10-22-picture-test` the picture-reading
test, `2026-10-22-window-test` the later picture tests, `2026-10-22-live-v2`
the solver run with v2 pictures). Requests, responses, arrays and
logs keep their recorded bytes (in 2026-10-20 the solver logs and telemetry
are gzip copies); each directory has a hash manifest.

| Directory | Run | Code | Report |
|---|---|---|---|
| [2026-10-30-wrong-setup/](2026-10-30-wrong-setup/README.md) | Slurm job 24947089: can a model see that a run was set up wrong? 80 one-frame requests from five normal and five wrongly set-up pimpleFoam runs, four models; job 24946879: the runs; 24946942: the set's build; answer key, leak check and a recount | `97db7eb` | this folder's README |
| [2026-10-29-merged-check/](2026-10-29-merged-check/README.md) | Slurm job 24936949: the merged code built and validated, a 2D and a 3D v2 frame equal to earlier runs | `eff951b` | [results-20261028.md](../results-20261028.md) |
| [2026-10-28-inflight/](2026-10-28-inflight/README.md) | Slurm job 24929296: a describe request every 50 steps with two in flight and a two-slot server, 6,000 steps, and its twin; comparison with the one-in-flight run of October 27 | `2ed6da2` (summary rebuilt with `c85c79c`) | [results-20261028.md](../results-20261028.md) |
| [2026-10-28-callback/](2026-10-28-callback/README.md) | Slurm job 24929555 (CPU): main's and the new callback on the step case, 1,250 steps without model requests (describe, sequence, the `tn` sequence form, 2 MPI ranks), every written file and `telemetry.jsonl` compared; the telemetry of 24,000 recorded states replayed under tracemalloc; comparison rerun in job 24929607 | `16d665e` (branch `callback-telemetry-trends`) against `2ed6da2` | this folder's README |
| [2026-10-28-instability/](2026-10-28-instability/README.md) | Slurm jobs 24929533 and 24929534: can a model see a run going unstable? 70 three-frame requests from three crashed and four stable pimpleFoam runs, four models; jobs 24929408, 24929449, 24929452: the flow reruns; 24929495: the set's build; 24929764: checks after the review; answer key and a recount | `8d6a10a` (report `c9a1ba1`, review fixes `660f8c4`) | the folder's README |
| [2026-10-28-3d/](2026-10-28-3d/README.md) | Slurm job 24929629 (and 24929500): v2 observer pictures of a 3D case through a plane slice; the step case extruded to 8 cells in z, serially and on 2 ranks, without the observer, with `LLM_SLICE_Z` set and refused, the 2D case and the bridge validation; no model | `c7a25d3` (`07759b0` for 24929500) | this folder's README |
| [2026-10-27-solver/](2026-10-27-solver/README.md) | Slurm job 24903264: a describe request every 250 steps over 24,000 steps and its twin; jobs 24903298 and 24903263/24903755: two repeats of the October 22 suite and sweep; 24903786: MPI, 2 ranks; 24903065: POD mode files and BLAS threads; unstable-flow attempts; comparison and tracking scripts | `6afbdeb` with changes, `df72c24` (recorded per job) | [results-20261027.md](../results-20261027.md) |
| [2026-10-27-picture-tests/](2026-10-27-picture-tests/README.md) | Slurm jobs 24903974 and 24903975 (trend test, four models), 24903976 and 24903977 (4-bit Qwen, recommended image tokens), 24903978 (cylinder flow); the cylinder flow runs; answer keys and a recount | `ab6b943` | [results-20261027.md](../results-20261027.md) |
| [2026-10-22-live-v2/](2026-10-22-live-v2/README.md) | Slurm job 24757460: `pod-llm-async.UM1RyJ`, the five asynchronous cases with v2 pictures and Gemma 4 12B on an NVIDIA RTX A6000, from a developed flow; eleven describe requests with random windows; a trial run (job 24757458); check script | `354caf9` with uncommitted changes (recorded) | [results-20261022-live.md](../results-20261022-live.md) |
| [2026-10-22-window-test/](2026-10-22-window-test/README.md) | Slurm jobs 24757327 (four Qwen models, the 308 requests), 24757344 and 24757382 to 24757384 (random windows, eleven models, three seeds, image-token limit 1024), 24757459 (developed flow, random windows); the developed flow run (job 24757429); answer keys and a recount | picture-test bundle (`58e00d9` + `window_test.py`); job 24757459 as job 24757460 | [results-20261022-live.md](../results-20261022-live.md) |
| [2026-10-22-picture-test/](2026-10-22-picture-test/README.md) | Slurm job 24756981: the same 308 prepared requests to each of seven Gemma 4 models (E2B to 31B) on an NVIDIA RTX A6000 (MedicineBow); answer key and an independent re-scoring | `58e00d9` | [results-20261022.md](../results-20261022.md) |
| [2026-10-20/](2026-10-20/README.md) | `pod-llm-async.pp7agC`: five asynchronous cases on 3000 steps; `pod-llm-async.8YC6bG`: windowed frames; describe and sequence replays | `9449085` | [results-20261020.md](../results-20261020.md) |
| [2026-10-19-12b/](2026-10-19-12b/README.md) | Slurm job 24696203: the October 17 paired replay with Gemma 4 12B QAT on an NVIDIA A30 (MedicineBow); no position scored, the image answers say only "near x=0.00 m" | `934da23` (request and scoring code equal to `23089bb`) | [results.md](../results.md#same-replay-with-gemma-4-12b-on-a-gpu-2026-10-19) |
| [2026-10-19/](2026-10-19/README.md) | `pod-llm-demo.o5sNLJ`: repeat of the October 17 run and replay, same hashes and replay coordinates | `23089bb` (code), `4187659` (docs) | [results.md](../results.md#repeat-on-2026-10-19) |
| [2026-10-17/](2026-10-17/README.md) | `pod-llm-demo.LRfJBN`: five solver cases and the paired image/no-image replay | `23089bb` | [results.md](../results.md) |
| [2026-10-13/](2026-10-13/README.md) | `pod-llm-demo.SwwR2e`: first five-case run with the image path | `9ae54d0` | [results-20261013.md](../results-20261013.md) |

The October 27 archives (the five picture jobs, the two new test sets, the
cylinder runs, the periodic run without time directories, the MPI and
POD-file runs, the unstable attempts) are assets of the
[tests-2026-10-27](https://github.com/seungminyome/PythonFOAM/releases/tag/tests-2026-10-27)
release. The picture tests' archives (the input bundles with all requests and answer
keys, and each job's results with every raw reply) are assets of the
[picture-test-2026-10-22](https://github.com/seungminyome/PythonFOAM/releases/tag/picture-test-2026-10-22)
release; the v2 solver run's complete outputs, the trial run and the developed
flow are assets of
[pod-insitu-v2-2026-10-22](https://github.com/seungminyome/PythonFOAM/releases/tag/pod-insitu-v2-2026-10-22). Complete solver outputs (all time directories) are release assets, not in the
repository (for 2026-10-20 the five cases of `pod-llm-async.pp7agC`; the
windowed frame run `pod-llm-async.8YC6bG` is not in the release, and this
repository has its frames and run records but not its time directories): [2026-10-20](https://github.com/seungminyome/PythonFOAM/releases/tag/pod-insitu-async-2026-10-20),
[2026-10-17](https://github.com/seungminyome/PythonFOAM/releases/tag/pod-insitu-tests-2026-10-17),
[2026-10-13](https://github.com/seungminyome/PythonFOAM/releases/tag/pod-insitu-demo-2026-10-13).
