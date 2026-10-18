# PythonFOAM: Local LLM Integration

I am testing whether a local language model can help a user understand a running fluid simulation. At a selected step, a PythonFOAM callback sends numerical summaries and a flow image from OpenFOAM to Gemma, running locally on CPU through llama.cpp. It saves the answer and returns to the calculation. The answer is for the user and does not change the simulation.

The model responded during the test run and the calculation resumed. Reliable flow interpretation remains an open problem.

## What this fork adds

[PythonFOAM](https://github.com/argonne-lcf/PythonFOAM) already provides the OpenFOAM–Python connection and the PODFoam example. This fork adds:

- A callback that sends a numerical summary and velocity/pressure image to a local Gemma 4 E2B model.
- Saved answers and error records, with timeout handling so the simulation can continue when a request fails.
- Five test cases checking saved outputs: no request, numbers only, numbers with an image, connection refusal, and timeout.
- A comparison of model answers with and without the image, keeping the question and numbers fixed.

## What the tests showed

On October 17, all five test cases finished, including connection failure and timeout. The saved output files in each comparison run matched those from the run without a model request, byte for byte.

On one saved flow state, all six answers in the image/no-image comparison gave the wrong maximum-speed location. The simulation also pauses for the answer: the call with an image took about 78 seconds on CPU.

The current prototype needs further validation for real-time use. Next, I plan to check answers across more flow states and let the simulation continue while the model processes a saved state.

## Read further

Start with the [test report](docs/results.md) for the experimental conditions, measurements and limitations.

- [Recorded requests, responses and logs](docs/evidence/2026-10-17/README.md)
- [Run the demo](Solver_Examples/PODFoam/llm_demo/README.md)
- [그림으로 보는 한국어 설명](https://seungminyome.github.io/PythonFOAM/)

The original PythonFOAM description and setup notes are retained in the [project reference](docs/upstream-project.md). The integration remains under the repository's [Argonne open-source license](LICENSE).
