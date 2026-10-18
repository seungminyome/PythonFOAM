# October 17 integration and controlled replay evidence

Executed source: **23089bbf3447731852fa960d7d25ea18767a3f51**.
Live solver run: **pod-llm-demo.LRfJBN**.

[English report](../../results.md) · [Korean results page](https://seungminyome.github.io/PythonFOAM/results-20261017.html) · [Downloads](https://github.com/seungminyome/PythonFOAM/releases/tag/pod-insitu-tests-2026-10-17)

Five live solver conditions completed ten steps. Each comparison run matched all
45 saved field files against the no-request baseline. A separate replay used
three pairs on one snapshot, with the same question, numerical input and settings
and only the PNG inclusion varied. All six location answers were incorrect.

| Record | Contents |
|---|---|
| [test-results.json](test-results.json) | Combined result and interpretation recorded after the actual tests |
| [independent-integration-check.json](independent-integration-check.json) | Source identity, explicit 45-file inventory and live solver chronology |
| [runtime-summary.json](runtime-summary.json) | Derived public summary of model/projector hashes and active server settings |
| [unit-tests-56.txt](unit-tests-56.txt) | Saved pre-commit Python unit and loopback test record |
| [manifest.json](manifest.json) | Origins, sizes, hashes and original/derived labels for these selected files |
| [Live-run verification](pod-llm-demo.LRfJBN/demo-verification.json) | Five-case verifier result |
| [Image request](pod-llm-demo.LRfJBN/fixed-pod/llm_request_body.json) | Exact live request, including the PNG |
| [Image response](pod-llm-demo.LRfJBN/fixed-pod/llm_response.json) | Live model response; distinct from the controlled replay |
| [Actual PNG](pod-llm-demo.LRfJBN/fixed-pod/llm_observation/state.png) | Step-5 input image |
| [Image arrays](pod-llm-demo.LRfJBN/fixed-pod/llm_observation/fields.npz) | Cell coordinates, velocity and pressure used to draw and score the image |
| [Replay manifest](ablation/manifest.json) | Question, settings, request hashes and execution order |
| [Replay summary](ablation/summary.json) | Original automatic metrics, including their limitations |
| [Independent response review](independent-ablation-review.json) | Incorrect/unsupported claims missed by the automatic grounding flags |
| [Evaluator coordinates](ablation/ground_truth.private.json) | Ground truth withheld from the model; “private” means evaluator-only |

The `ablation/pair-*` folders contain all six exact requests, raw replies,
parsed replies, result records and metrics. The planar errors were 60.92 cm for
numeric-only and 50.97 cm with the image. Repeats of this one snapshot are not
independent flow cases. Prompt caching affects timings. Zero automatic grounding
flags is not a finding that the replies are correct.

The selected records are byte-preserved except `runtime-summary.json`, which is
explicitly derived and omits process/memory addresses and absolute runtime paths.
Original records can retain local paths as provenance; use the relative links in
this index to access published files. Historical `remote_writes` fields describe
the testing session before publication. No model weights or credentials are included.

This directory is a **selection**, not the full set of solver fields. The release
archive `solver-evidence-LRfJBN.tar.gz` includes all ten time directories for each
of the five solver cases, the materialized pimpleFoam reference, and the executed
verification sources. The original automatically generated `run-archive.tar.gz`
excluded intermediate steps and is not used as the full verification archive.

After unpacking the solver archive, its `README.txt` explains how to verify the
saved records without running OpenFOAM or making a model request. The release's
`SHA256SUMS.txt` covers both downloadable archives. The evidence ZIP includes the
Korean results HTML with these linked files for offline reading.
