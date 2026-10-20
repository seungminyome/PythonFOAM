# Changelog

Dates are when a run or change happened. Where a run is recorded, the code
revision that produced it is given.

## 2026-10-20 (code `9449085`)

- Asynchronous requests (`LLM_ASYNC=1`): the request step forks the worker and
  returns; later steps poll without blocking and record the arrival step; a
  late worker is killed by the same polling; pending requests are bounded; at
  the last step a pending request is waited for or detached.
- Request modes: `describe` (one image, description plus the positions of the
  fastest flow and the lowest pressure as percent of the plotted ranges) and
  `sequence` (frames captured at chosen steps, sent together, trend words).
- `LLM_IMAGE_XRANGE` / `LLM_IMAGE_YRANGE` plot a window of the domain.
- `PythonAnalysis.H` passes `end_time_s`.
- `run_async_cases.py`, `verify_async.py` (`POD_SUITE=async`),
  `snapshot_runner.py`, `test_async.py` (14 tests, 70 in all).
- Runs: five asynchronous cases on 3000 steps (`pod-llm-async.pp7agC`),
  windowed frames (`pod-llm-async.8YC6bG`), describe and sequence replays.
  Report: [docs/results-20261020.md](docs/results-20261020.md).

## 2026-10-19

- `CITATION.cff` removed: there is no paper to cite yet. 12B is now the first item under next steps.
- `test_callback.py`: the image-rendering test gets a 4 s callback deadline; 1 s was too short on a shared CI runner. Test only, solver code unchanged.
- Repeat of the October 17 run and replay (`docs/evidence/2026-10-19/`): same hashes, same answers.
- `llm_demo/hpc/`: scripts and Slurm jobs to repeat the measurements with Gemma 4 12B on a GPU node.
- Docs reorganised: evidence under dated folders, English-only pages here,
  Korean material moved to [PythonFOAM-Korean](https://github.com/seungminyome/PythonFOAM-Korean).
- CI: unit tests on Python 3.10 and 3.12; evidence files checked against their
  manifests; relative links checked.
- This changelog and a `Makefile`.
- README states what "step 5" is and gives the test machine specification.

## 2026-10-18

- October 17 report and evidence published. Release
  [pod-insitu-tests-2026-10-17](https://github.com/seungminyome/PythonFOAM/releases/tag/pod-insitu-tests-2026-10-17).

## 2026-10-17 (code `23089bb`)

- Five-case solver run `pod-llm-demo.LRfJBN` and the paired image/no-image
  replay (`ablation_runner.py`). 56 unit tests.
- Callback hardening: absolute worker deadline, result files written by a
  separate short-lived child, request and response size limits in the client.

## 2026-10-13 (code `9ae54d0`)

- First run with the image path inside PODFoam, `pod-llm-demo.SwwR2e`. Release
  [pod-insitu-demo-2026-10-13](https://github.com/seungminyome/PythonFOAM/releases/tag/pod-insitu-demo-2026-10-13).
- `analysis_func` hook in PODFoam, `mesh_func` with cell polygons,
  `pod_image.py`, `bounded_ipc.py`, `llm_client.py`, five-case runner and verifier.

## 2026-10-10

- PODFoam built on OpenFOAM v2106; bridge validation `pod-v2106.c5jpOq` passed
  (snapshot and SVD round trip). First numbers-only request to the local model.

## 2026-10-08

- Project start.
