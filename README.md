# PythonFOAM: a vision-language observer for OpenFOAM runs

[![tests](https://github.com/seungminyome/PythonFOAM/actions/workflows/tests.yml/badge.svg)](https://github.com/seungminyome/PythonFOAM/actions/workflows/tests.yml)
[![evidence](https://github.com/seungminyome/PythonFOAM/actions/workflows/evidence.yml/badge.svg)](https://github.com/seungminyome/PythonFOAM/actions/workflows/evidence.yml)
![OpenFOAM v2012 | v2106 | v2212 | 8](https://img.shields.io/badge/OpenFOAM-v2012%20%7C%20v2106%20%7C%20v2212%20%7C%208-lightgrey)
![Python 3.10 | 3.12](https://img.shields.io/badge/python-3.10%20%7C%203.12-lightgrey)
[![license](https://img.shields.io/badge/license-Argonne%20OSS-blue.svg)](LICENSE)

[Results page](https://seungminyome.github.io/PythonFOAM/) · [Latest report](docs/results-20261103.md) · [How to run](Solver_Examples/PODFoam/llm_demo/README.md) · [GPU nodes](Solver_Examples/PODFoam/llm_demo/hpc/README.md) · [Korean](https://github.com/seungminyome/PythonFOAM-Korean)

While OpenFOAM runs, Python draws the flow and asks a local picture-reading model
what it sees. This repository shows what such a model can and cannot read from
solver pictures. It builds on the PODFoam example of
[PythonFOAM](https://github.com/argonne-lcf/PythonFOAM); the model runs under
[llama.cpp](https://github.com/ggml-org/llama.cpp) on the same machine, and nothing
it says goes back into the solver.

## What we found

The model was Gemma 4 (12B for most tests, E2B and 31B where named). It got the two
pictures below, |U| and p of one time step, and a question.

| Question put to the model | What happened | Verdict |
|---|---|---|
| Where is the flow fastest, and where is the pressure lowest? | In most pictures it points at the right spot. Always guessing the usual spot does far worse. | Works |
| Can it do that while the solver is running? | Yes. A request every 250 steps adds under 1 % to the run time, and every file the solver writes stays the same. | Works |
| Between snapshots, is the flow speeding up or slowing down? | It reads the trend when the change is 2 % or more. Smaller changes it misreads. | Works for clear changes |
| Is this run about to crash? | It only says so once the field has already blown up. A simple rule on the numbers does as well or better. | No |
| Was this run set up wrong? | A first test looked promising. A second, fairer test (29 pairs of runs, the plan fixed before any request) shows no lead over a simple rule. The model catches more wrong runs but also calls normal runs wrong. | Not shown |
| Does a bigger model help? | The small E2B model gives no usable answers. 12B is enough for positions. 31B sees small pressure spots better, and is no better at judging setups. | Partly |

Every line rests on a recorded run with its counts and a baseline: the
[results page](https://seungminyome.github.io/PythonFOAM/) has them, and the
[evidence folders](docs/evidence/README.md) hold the raw answers with hash manifests.
The latest report, [November 3](docs/results-20261103.md), is the second wrong-setup
test.

<img src="docs/evidence/2026-10-22-live-v2/suite/async-describe/llm_observation/step-000250/U.png" width="415" alt="|U| at t = 0.10125 s in the window x 0 to 0.12 m, y 0 to 0.04 m: a row of vortices behind the step"> <img src="docs/evidence/2026-10-22-live-v2/suite/async-describe/llm_observation/step-000250/p.png" width="415" alt="p at the same time: low-pressure vortex cores at y about 20 to 30 %">

*What the model sees: |U| and p of step 250 of a developed backward-facing-step
flow, drawn by the running solver and sent to Gemma 4 12B.*

Two things to keep in mind. All tests used 2D laminar flows and one extruded 3D
case, so other flows may read differently. Only positions and fixed words are
scored; the free-text descriptions are not.

## How it works

The solver calls a Python hook once per time step. At a request step the hook forks
a worker, which draws the pictures and posts them to llama-server, the HTTP server
of llama.cpp. The solver keeps stepping, and the answer is read and recorded at a
later step together with the arrays it came from.

```mermaid
sequenceDiagram
    participant S as PODFoam (C++)
    participant P as python_module.py
    participant W as worker
    participant L as llama-server
    S->>P: analysis_func(state) at a request step
    P->>W: fork
    P-->>S: return, the solver keeps stepping
    W->>L: pictures and request
    L-->>W: answer
    W-->>P: answer, read at a later step
```

The requests can be synchronous or asynchronous, once or every N steps, with up to
eight in flight. MPI runs gather the fields to the master rank, and 3D meshes are
drawn through a plane slice. The three request modes, the two picture styles and
every setting are in [llm_demo/README.md](Solver_Examples/PODFoam/llm_demo/README.md).

## Quick start

Unit tests and evidence hashes need neither OpenFOAM nor a model:

```bash
pip install -r Solver_Examples/PODFoam/llm_demo/requirements.txt
make test          # 165 tests, about 2 minutes
make evidence      # every file in a manifest matches its hash
```

With an OpenFOAM sourced (v2012, v2106, v2212 or 8) and Python 3.10 to 3.12, the
five-case suite with the small Gemma 4 E2B model on the CPU exercises the coupling
and the verification. The model files are about 3.4 GB, and no token is needed:

```bash
export PYTHON=<python>    # default: python3 on PATH
export PATH=$(dirname "$PYTHON"):$PATH
export LD_LIBRARY_PATH=$(dirname "$PYTHON")/../lib:$LD_LIBRARY_PATH   # if not the system Python
cd Solver_Examples/PODFoam
./validation/run.sh              # bridge check; its passed run is the reference run
./llm_demo/setup_runtime.sh      # Gemma 4 E2B Q4_0, image projector, llama.cpp b11429
python3 llm_demo/runtime.py start
./llm_demo/run_demo.sh           # builds PODFoam, runs the five cases, verifies
python3 llm_demo/runtime.py stop
```

The GPU runs of the reports, with Gemma 4 12B and v2 pictures on a Slurm node, are
in [llm_demo/hpc/README.md](Solver_Examples/PODFoam/llm_demo/hpc/README.md).

## Reports

Each report records the setup, hardware, code revision and Slurm jobs of its runs.

- [November 3](docs/results-20261103.md): wrong-setup test 2, 29 pairs of runs
  against rules on the same pictures.
- [November 2](docs/results-20261102.md): the PR branches on four OpenFOAM versions,
  why OpenFOAM 8 differs, 3D slice pictures, the crash test without times.
- [October 30](docs/results-20261030.md): OpenFOAM versions, the original PODFoam,
  the first wrong-setup test.
- [October 28](docs/results-20261028.md): two requests in flight, 3D slices, the
  crash test.
- [Results page](https://seungminyome.github.io/PythonFOAM/) with all reports and
  downloads · [Evidence index](docs/evidence/README.md) ·
  [Changelog](CHANGELOG.md) · [Korean repository](https://github.com/seungminyome/PythonFOAM-Korean).

The observer lives in `Solver_Examples/PODFoam/`: the `Python*.H` hooks and
`llm_demo/`. The other examples are as in argonne-lcf/PythonFOAM. Branch
`pr/podfoam-fix` holds the PODFoam fix alone, and `pr/podfoam-observer` adds the
hooks and the observer. [HOOKS.md](Solver_Examples/PODFoam/HOOKS.md) describes the
two hooks and the [validation README](Solver_Examples/PODFoam/validation/README.md)
the bridge check.

## Citation

If you use the observer, please cite PythonFOAM and this repository:

```bibtex
@article{maulik2022pythonfoam,
  title   = {PythonFOAM: In-situ data analyses with OpenFOAM and Python},
  author  = {Maulik, Romit and Fytanidis, Dimitrios K. and Lusch, Bethany and
             Vishwanath, Venkatram and Patel, Saumil},
  journal = {Journal of Computational Science},
  volume  = {62},
  pages   = {101750},
  year    = {2022},
  doi     = {10.1016/j.jocs.2022.101750}
}

@software{yome2026observer,
  author = {Yome, Seungmin},
  title  = {PythonFOAM: a vision-language observer for OpenFOAM runs},
  year   = {2026},
  url    = {https://github.com/seungminyome/PythonFOAM}
}
```

## Acknowledgements

This extends the PODFoam example of [PythonFOAM](https://github.com/argonne-lcf/PythonFOAM)
by Argonne National Laboratory; its original description and setup notes are
in the [project reference](docs/upstream-project.md). The models are served
with [llama.cpp](https://github.com/ggml-org/llama.cpp); the model weights
are not part of this repository and come with their own licences. The GPU
and CPU-node runs in the reports used the MedicineBow cluster of the
University of Wyoming Advanced Research Computing Center.

## License

The PythonFOAM open-source [license](LICENSE) of UChicago Argonne, LLC
applies unchanged.
