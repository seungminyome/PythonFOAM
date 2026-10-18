# PythonFOAM: Local LLM Integration

This project tests whether a local language model can help a user understand a running fluid simulation. At a selected step, it sends numbers and a flow image from OpenFOAM to Gemma, saves the answer, and continues the calculation. The answer is for the user and does not change the simulation.

The connection works in the tested case. Getting reliable interpretations of the flow is still an open problem.

## What this fork adds

[PythonFOAM](https://github.com/argonne-lcf/PythonFOAM) already provides the OpenFOAM–Python connection and the PODFoam example. This fork adds:

- A connection to a local Gemma 4 E2B model, with numerical summaries and velocity/pressure images as input.
- Saved answers and error records, with timeout handling so the simulation can continue when a request fails.
- Tests comparing saved simulation outputs with model requests enabled, disabled, failed or timed out.
- A comparison of model answers with and without the image, keeping the question and numbers fixed.

## What the tests showed

In the October 17 test, all five conditions finished, including connection failure and timeout. The saved output files in each comparison run matched those from the run without a model request, byte for byte.

On one saved flow state, all six answers in the image/no-image comparison gave the wrong maximum-speed location. The simulation also pauses for the answer: the call with an image took about 78 seconds on CPU.

This is a working integration prototype, not yet a validated real-time analysis tool. The next steps are to check answers across more flow states and let the simulation continue while the model processes a saved state.

## Read further

Start with the [test report](docs/results.md) for the experimental conditions, measurements and limitations.

- [Recorded requests, responses and logs](docs/evidence/2026-10-17/README.md)
- [Run the demo](Solver_Examples/PODFoam/llm_demo/README.md)
- [그림으로 보는 한국어 설명](https://seungminyome.github.io/PythonFOAM/)

The original PythonFOAM description and setup notes are retained in the [project reference](docs/upstream-project.md). The integration remains under the repository's [Argonne open-source license](LICENSE).
