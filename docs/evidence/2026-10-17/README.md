# October 17 evidence

Records behind the [October 17 report](../../results.md). Solver run
`pod-llm-demo.LRfJBN`, code `23089bbf3447731852fa960d7d25ea18767a3f51`.

[Korean results](https://seungminyome.github.io/PythonFOAM-Korean/results-20261017.html) ·
[Downloads](https://github.com/seungminyome/PythonFOAM/releases/tag/pod-insitu-tests-2026-10-17)

## Files

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

[ablation/](ablation/) holds the three paired replays, one `pair-*` folder per
request with the body sent, the raw and parsed reply, result and metrics. These
were sent after the solver run, from the saved step-5 state. The same
requests, with only the model name changed, were sent to Gemma 4 12B on a GPU
node on October 19: [2026-10-19-12b](../2026-10-19-12b/README.md).

## Complete run

This folder has the records worth reading. `solver-evidence-LRfJBN.tar.gz` in
the release also has every time directory of the five runs, the pimpleFoam
reference case and the verifier, with a `README.txt` on how to check the files
without rerunning anything. `SHA256SUMS.txt` covers the release files. The
smaller `run-archive.tar.gz` that the demo script writes skips intermediate
time steps; use the release archive for the full record.

## Notes

Requests, replies, arrays and logs are the recorded bytes. `runtime-summary.json`
is a trimmed copy of the runtime record and is marked as derived in the
manifest. Some records contain paths from the test machine; the links above are
the published locations.
