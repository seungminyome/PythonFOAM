# PythonFOAM: in-situ observer/logger

This fork adds a PythonFOAM callback-based in-situ **observer/logger** to the PODFoam example. During a run, the solver passes a numerical summary and a same-step velocity/pressure image to a local multimodal model, records the response, and resumes calculation. Model output does not change solver fields, settings or control algorithms. The recorded run used Gemma.

**[Project overview and illustrated guides](https://seungminyome.github.io/PythonFOAM/)** · **[Run report](docs/results.md)** · **[Saved data](docs/evidence/README.md)** · **[Code and execution instructions](Solver_Examples/PODFoam/llm_demo/README.md)**

## Latest tested result — 2026-10-17

The run `pod-llm-demo.LRfJBN` tested code revision `23089bb` with serial OpenFOAM v2106 and a local quantized Gemma 4 E2B multimodal model. At step 5, the callback passed numerical diagnostics and a same-step field image to the model, saved its response, and returned to the remaining calculation. All five conditions completed 10 steps; each of the four comparison runs produced 45 files byte-identical to the no-request baseline.

| Case | Outcome | Full callback time |
|---|---|---:|
| No model request | Baseline; image rendered locally | 0.493 s |
| Numbers and image | Actual model response | 78.256 s |
| Numbers only | Actual model response | 39.672 s |
| Connection refused | Returned to calculation | 0.509 s |
| Deliberately delayed response | Timed out; returned to calculation | 4.013 s |

The callback is **synchronous: the solver waits**. Concurrent solver/inference execution has not been implemented or tested. These are single-run measurements, not averages. Identical files establish unchanged saved outputs in these tests, not general numerical stability or physical accuracy. The two normal calls above use different demo prompts and are not the controlled image comparison.

In a separate controlled replay, three paired trials used one saved snapshot with the same question, numeric input and model settings, changing only PNG inclusion. All six responses gave the wrong maximum-speed location: **60.92 cm planar error with numbers alone; 50.97 cm with the image**. The maximum-speed value was supplied in both inputs, so quoting it correctly is not evidence of image understanding. These repeats do not establish performance across different flow states.

The automatic grounding rules raised no flags, but independent review found incorrect claims. They remain review aids, not a complete truth check. Prompt reuse affected replay timings, so the measurements do not establish a speed advantage from image inclusion.

This is a working, tested integration prototype. Reliable spatial interpretation remains unresolved. The next priorities are evaluating useful observations across more states and reducing solver blocking; these are follow-up work, not completed features.

[Latest illustrated results, Korean](https://seungminyome.github.io/PythonFOAM/results-20261017.html) · [English test report](docs/results.md) · [Latest evidence](docs/evidence/2026-10-17/README.md) · [Earlier October 13 run](docs/results-20261013.md)

![Velocity and kinematic-pressure image sent to the model at step 5](docs/evidence/2026-10-17/pod-llm-demo.LRfJBN/fixed-pod/llm_observation/state.png)

*Actual input image. The vertical axis is stretched; the displayed shape is not to scale.*

## Read or download

| Material | Link |
|---|---|
| Latest results with actual responses | [Read in browser](https://seungminyome.github.io/PythonFOAM/results-20261017.html) |
| Latest requests, responses, metrics and step-5 arrays | [Browse evidence](docs/evidence/2026-10-17/README.md) |
| Latest solver fields, all ten saved steps | [Download solver evidence](https://github.com/seungminyome/PythonFOAM/releases/download/pod-insitu-tests-2026-10-17/solver-evidence-LRfJBN.tar.gz) |
| Latest selected evidence and offline results page | [Download evidence ZIP](https://github.com/seungminyome/PythonFOAM/releases/download/pod-insitu-tests-2026-10-17/evidence-20261017.zip) |
| Download checksums | [SHA256SUMS.txt](https://github.com/seungminyome/PythonFOAM/releases/download/pod-insitu-tests-2026-10-17/SHA256SUMS.txt) |
| Illustrated introduction, based on the October 13 run | [Read overview](https://seungminyome.github.io/PythonFOAM/overview.ko.html) |
| Detailed explanation and earlier evidence reader | [Read guide](https://seungminyome.github.io/PythonFOAM/guide.ko.html) |

The latest evidence ZIP keeps the results page beside its linked data for offline reading. The larger solver archive includes all saved time directories used in the 45-file comparison. The older illustrated guides embed their own October 13 evidence. No model weights are included.

## Reproduce or inspect

Start with the [PODFoam bridge validation](Solver_Examples/PODFoam/validation/README.md), then follow the [local-model demo instructions](Solver_Examples/PODFoam/llm_demo/README.md). The tested environment was OpenFOAM v2106, Python 3.10, NumPy, matplotlib, and a local CPU llama.cpp server running `gemma-4-E2B-it-Q4_0-vision`.

To inspect the existing run without executing CFD or the model, unpack the complete run archive and run:

```bash
python3 Solver_Examples/PODFoam/llm_demo/verify_demo.py /path/to/pod-llm-demo.LRfJBN
```

This check requires NumPy. Details of the request, response, field comparisons and read-only recheck are in the [run report](docs/results.md).

A local [controlled replay benchmark](Solver_Examples/PODFoam/llm_demo/README.md#controlled-replay-benchmark) prepares numeric-only and numeric-plus-image requests with identical questions, summaries and generation settings. Its default mode sends no requests. The October 17 evidence includes an actual six-request execution in addition to the five live solver cases. Python unit and loopback tests passed **56 tests** before the tested source was committed; [saved test log](docs/evidence/2026-10-17/unit-tests-56.txt).

## Upstream project

PythonFOAM connects OpenFOAM with Python for in-situ analysis. This fork builds on [argonne-lcf/PythonFOAM](https://github.com/argonne-lcf/PythonFOAM). The original project description, other solver examples and setup notes are retained in [the project reference](docs/upstream-project.md).

The integration remains under the repository's [Argonne open-source license](LICENSE).
