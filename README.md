# PythonFOAM multimodal model integration

This fork connects the PODFoam example to a local Gemma 4 E2B model. During an OpenFOAM run, a Python callback sends the model numerical diagnostics and a velocity/pressure image from the same time step. The callback saves the response and returns to the calculation. The response is for the user; it does not change the solver's fields or settings.

[Test report](docs/results.md) · [Run the demo](Solver_Examples/PODFoam/llm_demo/README.md) · [Data](docs/evidence/2026-10-17/README.md) · [한국어 설명](https://seungminyome.github.io/PythonFOAM/)

## Test results — October 17, 2026

The test used serial OpenFOAM v2106 and quantized Gemma 4 E2B on CPU. The model was called after step 5. All five conditions completed ten steps, and each of the four comparison runs produced 45 saved field files identical, byte for byte, to those from the run without a model request. The tested code was `23089bb`; the saved run is `pod-llm-demo.LRfJBN`.

| Case | Outcome | Python callback time |
|---|---|---:|
| No model request | Baseline; image rendered locally | 0.493 s |
| Numbers and image | Response saved | 78.256 s |
| Numbers only | Response saved | 39.672 s |
| Connection refused | Returned to calculation | 0.509 s |
| Deliberately delayed response | Timed out; returned to calculation | 4.013 s |

The solver waits for the callback to finish. Letting the solver continue during inference is still to be implemented. The times above were measured once per condition around the Python callback. The file comparison checks that the saved outputs stayed unchanged in these runs; physical accuracy needs separate validation. The two normal model calls use different prompts, so their timings do not isolate the cost of the image.

In a separate comparison, the same question, numerical input and model settings were used with and without the PNG. Three pairs were run on one saved snapshot. All six responses gave the wrong maximum-speed location: the planar error was **60.92 cm with numbers alone and 50.97 cm with the image**. Both inputs already contained the maximum-speed value. Only one flow snapshot has been tested this way.

Location errors were calculated automatically, but the separate grounding checks raised no flags. The [report](docs/results.md) includes a check of the responses against the data. Prompt caching also affected the comparison timings, so they cannot establish a speed benefit from adding the image.

The connection works in this test case. The next work is to improve the accuracy of the observations, test more flow states and let the solver continue while the model is processing a snapshot.

[Results and responses, Korean](https://seungminyome.github.io/PythonFOAM/results-20261017.html) · [Earlier October 13 run](docs/results-20261013.md)

![Velocity and kinematic-pressure image sent to the model at step 5](docs/evidence/2026-10-17/pod-llm-demo.LRfJBN/fixed-pod/llm_observation/state.png)

*Actual input image. The vertical axis is stretched; the displayed shape is not to scale.*

## Read or download

| Material | Link |
|---|---|
| October 17 results and responses | [Read in browser](https://seungminyome.github.io/PythonFOAM/results-20261017.html) |
| Requests, responses, metrics and step-5 arrays | [Browse data](docs/evidence/2026-10-17/README.md) |
| Solver fields, all ten saved steps | [Download solver data](https://github.com/seungminyome/PythonFOAM/releases/download/pod-insitu-tests-2026-10-17/solver-evidence-LRfJBN.tar.gz) |
| Selected data and offline documentation | [Download ZIP](https://github.com/seungminyome/PythonFOAM/releases/download/pod-insitu-tests-2026-10-17/evidence-20261017.zip) |
| Download checksums | [SHA256SUMS.txt](https://github.com/seungminyome/PythonFOAM/releases/download/pod-insitu-tests-2026-10-17/SHA256SUMS.txt) |
| Illustrated introduction, based on the October 13 run | [Read overview](https://seungminyome.github.io/PythonFOAM/overview.ko.html) |
| Detailed explanation and earlier evidence reader | [Read guide](https://seungminyome.github.io/PythonFOAM/guide.ko.html) |

The ZIP contains the documentation published with the October 17 results and its linked data for offline reading. The larger solver archive includes all saved time directories used in the 45-file comparison. The older illustrated guides contain their October 13 data. Model weights are downloaded separately when running the demo.

## Reproduce or inspect

Start with the [PODFoam bridge validation](Solver_Examples/PODFoam/validation/README.md), then follow the [local-model demo instructions](Solver_Examples/PODFoam/llm_demo/README.md). The tested environment was OpenFOAM v2106, Python 3.10, NumPy, matplotlib, and a local CPU llama.cpp server running `gemma-4-E2B-it-Q4_0-vision`.

To check the saved run, unpack the solver archive and run its verifier:

```bash
python3 pod-llm-demo.LRfJBN/sources/llm_demo/verify_demo.py pod-llm-demo.LRfJBN
```

This requires NumPy and reads the saved files without running CFD or making a model request. Details are in the [test report](docs/results.md).

The [comparison runner](Solver_Examples/PODFoam/llm_demo/README.md#controlled-replay-benchmark) prepares matched requests with and without an image. Sending them requires `--execute`. The saved results include six requests from this runner and the five solver cases above. The Python unit and local HTTP tests also passed: [56-test log](docs/evidence/2026-10-17/unit-tests-56.txt).

## Upstream project

PythonFOAM connects OpenFOAM with Python for in-situ analysis. This fork builds on [argonne-lcf/PythonFOAM](https://github.com/argonne-lcf/PythonFOAM). The original project description, other solver examples and setup notes are retained in [the project reference](docs/upstream-project.md).

The integration remains under the repository's [Argonne open-source license](LICENSE).
