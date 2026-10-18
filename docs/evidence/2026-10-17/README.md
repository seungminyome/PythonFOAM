# October 17 evidence

These files accompany the [October 17 report](../../results.md). The solver
run was `pod-llm-demo.LRfJBN`, using revision
`23089bbf3447731852fa960d7d25ea18767a3f51`.

[Korean results](https://seungminyome.github.io/PythonFOAM/results-20261017.html) ·
[Downloads](https://github.com/seungminyome/PythonFOAM/releases/tag/pod-insitu-tests-2026-10-17)

## Find a record

| File | What it contains |
|---|---|
| [test-results.json](test-results.json) | Summary of the solver tests and controlled comparison |
| [independent-integration-check.json](independent-integration-check.json) | Source checks, the 45 compared files, and the order of solver events |
| [runtime-summary.json](runtime-summary.json) | Model and projector hashes, plus server settings |
| [unit-tests-56.txt](unit-tests-56.txt) | Output from the 56 Python and local HTTP tests |
| [manifest.json](manifest.json) | File origins, sizes, hashes, and labels identifying originals and derived records |
| [Solver verification](pod-llm-demo.LRfJBN/demo-verification.json) | Results of checking the five solver cases |
| [Image request](pod-llm-demo.LRfJBN/fixed-pod/llm_request_body.json) | Request sent from the solver, including the PNG |
| [Image response](pod-llm-demo.LRfJBN/fixed-pod/llm_response.json) | Model reply during that solver run |
| [state.png](pod-llm-demo.LRfJBN/fixed-pod/llm_observation/state.png) | Image sent at step 5 |
| [fields.npz](pod-llm-demo.LRfJBN/fixed-pod/llm_observation/fields.npz) | Cell coordinates, velocity and pressure behind the image |
| [Replay manifest](ablation/manifest.json) | Shared question, settings, seeds, request hashes and execution order |
| [Replay summary](ablation/summary.json) | Scores produced by the automatic evaluator |
| [Response review](independent-ablation-review.json) | Separate review of the answers and claims the automatic checks missed |
| [Reference coordinates](ablation/ground_truth.private.json) | Maximum-speed coordinates used for scoring; they were withheld from the model |

The [ablation](ablation/) folder holds the three paired comparisons. Each
`pair-*` subfolder contains the request, raw response, parsed response, result
and metrics. These are separate from the requests made during the solver run.
For the meaning and limits of the scores and timings, see the report's
[limitations](../../results.md#limitations).

## Download the complete run

This directory contains selected records. The release file
`solver-evidence-LRfJBN.tar.gz` also contains all ten saved time directories
for each of the five solver cases, the pimpleFoam reference case, and the
verification code. Its `README.txt` explains how to check the saved files
without rerunning the solver or model.

The evidence ZIP includes the Korean results page and its linked files for
offline reading. `SHA256SUMS.txt` lists checksums for both archives. The older
automatically generated `run-archive.tar.gz` omits intermediate time steps;
use `solver-evidence-LRfJBN.tar.gz` for the complete solver record.

## About the saved files

Requests, replies, arrays and logs retain their recorded bytes.
`runtime-summary.json` is a shortened version of the runtime information;
the manifest identifies it as derived. Original records may contain local
paths, so use the relative links above to open the published files.
Any `remote_writes` entries describe the test session before publication.
