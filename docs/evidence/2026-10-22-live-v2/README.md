# October 22 evidence: v2 pictures from the running solver

Slurm job 24757460 on MedicineBow (University of Wyoming), one NVIDIA RTX
A6000 (49,140 MiB), 2026-10-22 from 09:49 to 10:57 MDT. OpenFOAM v2212 in an
Apptainer image, PODFoam built in it against a conda Python 3.11; llama.cpp
b11429 (commit `d812350`) on the host GPU serving Gemma 4 12B QAT Q4_0. Code:
the checkout at `354caf9` with uncommitted changes ([job/code-state/](job/code-state/)).

[Report](../../results-20261022-live.md) ·
[How it is run](../../../Solver_Examples/PODFoam/llm_demo/hpc/README.md#v2-pictures-from-the-running-solver-async_v2slurm-run-2026-10-22) ·
[Release with the complete outputs](https://github.com/seungminyome/PythonFOAM/releases/tag/pod-insitu-v2-2026-10-22) ·
[Picture tests and the developed flow](../2026-10-22-window-test/README.md)

## What ran

- Start state: t = 0.1 s of a `pimpleFoam` run of the same mesh (job
  24757429). The hashes of its `U`, `p` and `phi` are in
  `suite/async-settings.json`; the run's settings and output are in
  [../2026-10-22-window-test/flow/](../2026-10-22-window-test/flow/), its
  states in the release.
- Suite (`run_async_cases.py`, `pod-llm-async.UM1RyJ`): five cases of 6000
  steps of 5e-6 s, written every 250 steps, all pictures in the window x 0 to
  0.12 m, y 0 to 0.04 m. Describe, connection refused and stall at step 250;
  sequence frames at 3000, 3250 and 3750, sent at 3750.
- Sweep (`run_live_sweep.py`): eleven more cases from the same state, one
  describe request at step 500, 1000, ..., 5500, each with its own random
  window, 300 more steps each, two cases at a time.
- Trial (job 24757458, `pod-llm-async.yIW1TX`, earlier the same morning): 600
  steps, describe at step 100, sequence at 200, 300 and 500, sweep requests at
  200 and 300.

## Files

| Path | What it contains |
|---|---|
| `suite/async-settings.json`, `summary.json`, `async-verification.json`, `timings.json` | Settings; the verifier's result (PASS) with every case's checks, the answers and their scores; wall times and peak memory |
| `suite/build-inputs.json`, `environment.txt`, `log.build`, `resident-server.json`, `sha256.json` | The build inputs, the environment, the build log, the server the cases used, and the hash of every file of the run as packed (the archive in the release) |
| `suite/executed-callback-source/` | The callback sources the cases ran (`pod_svd.py` is `validation/python_module.py`) |
| `suite/<case>/llm_request.json`, `llm_result.json`, `llm_response.json`, `llm_http_response.raw` | Per case: the request record (without the picture bytes), the result (status, arrival step, solver stall, timings), the record with the parsed reply, and the raw HTTP reply |
| `suite/<case>/log.PODFoam.gz`, `telemetry.jsonl.gz`, `timeline.json.gz`, `memory-samples.json.gz` | Gzip copies of the solver log, the per-step telemetry (6000 lines), the callback and model events with wall-clock stamps, and the memory samples (every 0.5 s) |
| `suite/async-describe/llm_request_body.json`, `suite/async-sequence/llm_request_body.json` | The two request bodies as sent, pictures included (base64) |
| `suite/async-describe/llm_observation/step-000250/`, `suite/async-sequence/llm_observation/step-003000/` (and 3250, 3750) | The frames: `U.png`, `p.png`, `fields.npz` (cell centres, U, p) and `readable-metadata.json` |
| `suite/async-timeout/timeout-fixture.json` | The stalling test server's record |
| `sweep/sweep-plan.json`, `sweep/sweep-summary.json` | The eleven requests with their windows; the sweep's checks, answers and scores |
| `sweep/describe-stepNNNNNN/` | Per case: request record, result, reply, raw reply and the frame |
| `sweep/fields-vs-baseline.json`, `sweep/compare_sweep_fields.py` | Every file the eleven cases wrote after the start, compared with the baseline's: byte comparison, and for the files that differ the largest difference relative to the largest value |
| `trial/` | The trial's settings, verification, summary, timings, the describe and sequence results, the sweep plan and summary, and the job output |
| `job/pod-async-v2-24757460.out`, `job/async_v2.slurm` | The job output and the job script as run |
| `job/code-state/` | `HEAD`, `git status`, the uncommitted changes as a patch and the new files as a tarball, recorded from the checkout the job ran from |
| `job/server/`, `job/nvidia-smi.txt`, `job/gpu-samples.csv.gz`, `job/runtime_manifest_12b.json` | The llama-server command line, log, model list and GPU memory once ready; the GPU at the start and its memory and load every second; the hashes of the 12B files |
| [check-live.py](check-live.py), [check-live.json](check-live.json) | The check below and its output |
| [courant-spectrum.py](courant-spectrum.py), [courant-spectrum.json](courant-spectrum.json) | The period of the largest Courant number in the baseline case, and its output |
| [manifest.json](manifest.json) | Origins, sizes and hashes of the files here |

## Checking

In this folder, with numpy:

```bash
python3 check-live.py               # writes check-live.json
python3 courant-spectrum.py
python3 ../check_manifest.py .
```

`check-live.py` uses only the files here. It rebuilds every request body from
its frame with the executed `readable_request.py` and compares it with the
body sent: byte for byte for the two suite bodies, by the SHA-256 the client
recorded for the eleven sweep bodies (13 of 13 equal). It recomputes the true
fastest and lowest-pressure cells from each frame's arrays, the distances of
the answers, the sequence's trend words and the best fixed answer over the
sweep, and asserts that they agree with the run's own records. It prints the
numbers of the report: 3.28 and 5.03 % for the suite's describe answer; speed
and region right, pressure wrong for the sequence; 9 and 10 of 11 within 10 %
in the sweep, 4 and 4 for one fixed answer.

`compare_sweep_fields.py` needs the time directories, which are in the
release: extract `solver-evidence-UM1RyJ.tar.gz` and `sweep-UM1RyJ.tar.gz`
and pass it the two folders.

## Notes

- Code state. No file of the checkout changed after 09:42 and the job started
  at 09:49; the state was recorded at 10:41. All 62 sources the run recorded
  (`sources/` and `executed-callback-source/` in the suite archive) equal the
  checkout. The published commit differs from it; the report's
  [Records](../../results-20261022-live.md#records) list how.
- The describe body is the same bytes in `async-describe`,
  `async-server-error` and `async-timeout` (same frame, same request); only
  the `async-describe` copy is here. The frames of `async-no-llm` (steps 3000,
  3250, 3750) are byte-identical to those of `async-sequence`, and those of
  `async-server-error` and `async-timeout` (step 250) to that of
  `async-describe`, in all four files; they are not repeated here.
- Written fields. In the suite every case's 432 compared files equal the
  baseline's. In the sweep, `U`, `p`, `phi` and the time files of every
  written directory equal the baseline's (858 files); the POD mode files that
  PODFoam writes from its own SVD (`upod_*`, `vpod_*`, `wpod_*`, 2,145 files)
  differ by at most 9.4e-12 of their largest value. The sweep ran two cases at
  a time with no BLAS thread limit (the version of `run_live_sweep.py` in the
  code state); the cause of the difference was not isolated.
- The sweep archive leaves out `python_svd_audit.npz` (the audit file PODFoam
  writes at the end of every run, 120 MB per case) and the matplotlib cache;
  the suite archive keeps them.
- Gzip copies (kind `gzip copy` in the manifest) were made with no name and
  mtime 0; the manifest gives the hash of the uncompressed bytes too.
- The records contain cluster paths and process ids as provenance.
