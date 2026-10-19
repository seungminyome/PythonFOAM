# Changelog

Dates are when a run or change happened. Where a run is recorded, the code
revision that produced it is given.

## 2026-10-19

- Repeat of the October 17 run and replay (`docs/evidence/2026-10-19/`): same hashes, same answers.
- `llm_demo/hpc/`: scripts and Slurm jobs to repeat the measurements with Gemma 4 12B on a GPU node.
- Docs reorganised: evidence under dated folders, English-only pages here,
  Korean material moved to [PythonFOAM-Korean](https://github.com/seungminyome/PythonFOAM-Korean).
- CI: unit tests on Python 3.10 and 3.12; evidence files checked against their
  manifests; relative links checked.
- `CITATION.cff`, this changelog, a `Makefile`.
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
