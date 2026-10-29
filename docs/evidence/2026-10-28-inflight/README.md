# October 28 evidence: two requests in flight

Slurm job 24929296 on MedicineBow, 2026-10-28, 16:42 to 16:55 MDT, node
mbl40s-001 (NVIDIA L40S): PODFoam in OpenFOAM v2212 (Apptainer image) with
a v2 describe request every 50 steps and at most two requests pending
(`LLM_ANALYSIS_EVERY=50`, `LLM_ASYNC_MAX_PENDING=2`), 6,000 steps of 5e-6 s
from t = 0.1 s of the developed flow, and the same run without requests;
Gemma 4 12B QAT served by llama.cpp b11429 with two slots (`--parallel 2`,
context 8192, 4096 per slot). Code: the checkout at `2ed6da2`
(`git/HEAD`, clean), run with `hpc/periodic_v2.slurm`:

```bash
POD_SUITE_RUN=<pod-llm-async.UM1RyJ of Slurm 24757460> PERIODIC_STEPS=6000 PERIODIC_FIRST=50 \
  PERIODIC_EVERY=50 PERIODIC_WRITE=50 PERIODIC_MAX_PENDING=2 LLM_PARALLEL=2 LLM_CTX=8192 \
  sbatch --account=<account> --partition=mb-a30,mb-l40s,mb-a6000 Solver_Examples/PODFoam/llm_demo/hpc/periodic_v2.slurm
```

[Report](../../results-20261028.md) · [The one-in-flight run](../2026-10-27-solver/README.md)

## Results

From [inflight.py](inflight.py) ([inflight.json](inflight.json)), against
the run of October 27 with one request every 250 steps and one pending at
most (Slurm 24903264, an NVIDIA A30 node):

| | Two in flight, every 50 steps | One in flight, every 250 steps |
|---|---:|---:|
| Requests planned / answered | 120 / 118 | 96 / 96 |
| Skipped because the limit was reached | 2 | 0 |
| Sent while another request was pending | 112 | 0 |
| Written files identical to the run without requests | 2,520 of 2,520 | 2,016 of 2,016 |
| Wall time per step, without / with requests | 0.06165 / 0.06363 s (+3.2 %) | 0.05794 / 0.05833 s (+0.7 %) |
| Extra wall time per answered request | 0.101 s | 0.097 s |
| Callback time at a request step, largest (last step excepted) | 0.046 s | 0.017 s |
| Reply after (last request excepted) | 50 to 111 steps | 85 to 144 steps |
| Model time, smallest / median / largest | 2.54 / 3.80 / 4.65 s | 4.15 / 4.73 / 5.25 s |
| Fastest flow within 10 % (one fixed answer) | 81 of 117 (62) | 65 of 96 (53) |
| Lowest pressure within 10 % (one fixed answer) | 106 of 117 (78) | 89 of 96 (65) |

- With two server slots the callback kept two requests going: 112 of the
  118 answered requests were sent while the one before was still pending,
  and the two steps that found two pending (4150 and 5550) were skipped and
  recorded, as designed.
- The run cost 3.2 % of wall time for five times as many requests; per
  request the extra time is about 0.1 s in both runs. Both runs without
  requests drew the same pictures, so this is the cost of the requests on
  top of drawing. One pair of runs each, on different nodes.
- One answered request has no result file. The reply to the request of step
  4100 arrived at step 4167 (`index.json`: status ok, model time 3.0 s), but
  its record in [step-004100/](step-004100/) has the request, the reply and
  the response record and no `llm_result.json`, and the log has no result
  line for it: the callback writes these files in a forked writer that is
  stopped after 0.2 s so that the solver never waits longer, and that step
  took 0.207 s. The solver was not affected. `run_periodic.py` stopped at
  the summary on this record; `periodic-summary.json` here was rebuilt with
  `run_periodic.py --summary-only` of `c85c79c`, which lists such requests
  in `records_missing` and leaves them out of the scores (117 scored).

## Files

| Path | What it contains |
|---|---|
| `periodic-summary.json` | Plan, every request (step, status, arrival step, model time, solver wait, bytes, parity checks, scores, parsed answer), file comparison with the twin, timings, memory; rebuilt as above |
| `timings.json`, `resident-server.json` | Wall time and memory peaks of both cases; the server the runs used |
| `periodic-describe/llm_requests/index.json` | The callback's index of the 120 request steps |
| `<case>/log.PODFoam.gz`, `telemetry.jsonl.gz`, `memory-samples.json.gz`, `timeline.json.gz` | Solver logs, per-step telemetry, memory samples and the callback's log lines of both cases (gzip copies) |
| `step-004100/` | The record of the request whose result file was not written |
| `pod-periodic-v2-24929296.out`, `periodic.log` | Job output and the runner's output (which ends at the KeyError) |
| `server-*.cmd`, `server-*.log.gz`, `models-*.json`, `gpu-*.txt`, `gpu-samples.csv.gz`, `nvidia-smi.txt`, `runtime_manifest_12b.json` | Server command line (two slots), log, model list, GPU memory, GPU samples every second, the 12B file hashes |
| `git/`, `executed-callback-source.sha256` | Code state at the start of the job and the hashes of the callback files that ran |
| [inflight.py](inflight.py), [inflight.json](inflight.json) | The comparison above |
| [manifest.json](manifest.json) | Origins, sizes and hashes of the files here |

The request bodies, replies and frames of every request and the cases
without time directories are in `inflight-24929296.tar.gz` of the
[tests-2026-10-28](https://github.com/seungminyome/PythonFOAM/releases/tag/tests-2026-10-28)
release. The records contain cluster paths and process ids as provenance.
