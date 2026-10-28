# October 27 evidence: a request every 250 steps, repeats, MPI, POD files, unstable attempts

Solver runs of 2026-10-27 on MedicineBow (University of Wyoming): PODFoam in
OpenFOAM v2212 (Apptainer image `of2212.sif`), Gemma 4 12B QAT on the GPU of
node mba30-005 (NVIDIA A30), and CPU jobs. The picture tests of the same day
are in [2026-10-27-picture-tests](../2026-10-27-picture-tests/README.md).

[Report](../../results-20261027.md) ·
[Release with every archive](https://github.com/seungminyome/PythonFOAM/releases/tag/tests-2026-10-27)

## Jobs

| Job | What | Where | Time (MDT) |
|---|---|---|---|
| 24903264 | 24,000 steps of 5e-6 s from t = 0.1 s with a describe request every 250 steps (96 requests), and the same run without requests | A30, mba30-005 | 08:49 to 09:37 |
| 24903298 | repeat 1 of the October 22 suite (five asynchronous cases) and its eleven-request sweep | A30, mba30-005 | 08:51 to 09:41 |
| 24903263, 24903755 | repeat 2: the suite (24903263), then the sweep alone (24903755) | A30, mba30-005 | 08:46 to 09:41 |
| 24903786 | the observer on 2 MPI ranks against a serial run (600 steps, frame at step 100, no model) | CPU, mbcpu-001 | 09:26 to 09:28 |
| 24903065 | why POD mode files differed between paired runs: six runs of 600 steps | CPU, mbcpu-001 | 08:47 to 08:52 |
| 24903082, 24903162, 24903182 | attempts at an unstable flow: `pimpleFoam` with larger time steps and central differencing | CPU | 08:28 to 08:40 |

## Results in this folder

| Folder | Result |
|---|---|
| [periodic/](periodic/) | 96 of 96 requests answered; all 2,016 written files identical to the run without requests; wall time per step 0.05833 s against 0.05794 s (+0.7 %; the run without requests drew the same pictures; one pair of runs, with other jobs on the node); the callback took at most 0.017 s at a request step, except the last step, which waits for the pending reply by design (6.8 s); 4,009 to 4,461 bytes back over the pipe per request; fastest flow within 10 % in 65 of 96 (one fixed answer: 53), lowest pressure in 89 of 96 (fixed: 65). [tracking.py](periodic/tracking.py): the answered x follows the true x of the lowest pressure with correlation 0.78, of the fastest flow 0.35 ([tracking.png](periodic/tracking.png)). [misses.py](periodic/misses.py): 27 of the 31 fastest-flow misses named a spot with at least 90 % of the largest speed, 5 of the 7 lowest-pressure misses a spot at least 90 % as low. [memory.py](periodic/memory.py): at the low point of each 250-step cycle the solver process grows by 85 MiB without and 70 MiB with requests; 32 MiB of that is the callback's per-step history |
| [repeats/](repeats/) | Both repeats PASS; every written field equal to the first run's except the POD mode files of the sweep; the 13 request bodies equal the first run's; the 13 answers identical between the two repeats, none identical to the first run's (A6000) in every field; sweep counts 9 and 10 of 11 within 10 % as in the first run ([compare-repeats.py](repeats/compare-repeats.py)) |
| [mpi/](mpi/) | 2 ranks: 20,540 cells in both frames, cell centres equal to 4e-17 m, U within 7.5e-4 m/s (of 37.2) and p within 0.021 m²/s² (of 335) of the serial frame |
| [poddiff/](poddiff/) | With 8 BLAS threads all 30 POD mode files differ from the one-thread run, alone or paired, by at most 1.0e-13 (largest value in that file 0.098, so about 1e-12 relative), while the other 12 written files (the flow fields) are identical; with one thread all 42 files are identical, also paired ([mode_differences.py](poddiff/mode_differences.py)) |
| [unstable/](unstable/) | Nine attempts ([unstable-summary.json](unstable/unstable-summary.json)): upwind convection ran to the end at every time step tried (largest Courant number up to 28); central differencing stopped with a floating point exception at the first step when the Courant number was 4.5 or 11, and ran to the end at 1.54 or below |

## Files

| Path | What it contains |
|---|---|
| `periodic/periodic-summary.json` | `run_periodic.py`'s summary: plan, every request (step, status, arrival step, model time, solver wait, bytes, parity checks, scores, parsed answer), file comparison with the twin, timings, memory |
| `periodic/periodic-describe/llm_requests/index.json` | The callback's index of the 96 request records (the records themselves, with bodies and frames, are in the release) |
| `periodic/<case>/log.PODFoam.gz`, `telemetry.jsonl.gz`, `memory-samples.json.gz`, `timeline.json.gz` | Solver log, per-step telemetry, memory samples and the timeline of the callback's lines of both cases (gzip copies) |
| `periodic/memory.py`, `memory.json` | The solver's memory at the low point of each 250-step cycle (the POD module's snapshots swing it within a cycle), with and without requests, and the size of the callback's per-step history; reads `<case>/memory-samples.json.gz` and `timeline.json.gz` |
| `periodic/misses.py`, `misses.json` | For each answer more than 10 % off, the speed or pressure at the cell named relative to the true extreme; needs the frames of `periodic-describe` from the release archive |
| `periodic/` other files | Job output and run log, server command, log and model list, GPU samples, the callback sources' hashes, the code state (HEAD, status, patch) |
| `repeats/<job>/` | Verification, summary, timings, build inputs, code state, the hash list of every suite file (`sha256.json.gz`), the describe and sequence results, the sweep summary, the eleven sweep results and the hash list of every sweep file; job outputs and server files |
| `repeats/run1-sweep-sha256.json.gz` | The hash list of the first run's sweep, made with [hash_tree.py](repeats/hash_tree.py) from its archive (`sweep-UM1RyJ.tar.gz` of the pod-insitu-v2-2026-10-22 release) |
| `repeats/compare-repeats.py`, `.json` | The comparison above, from the files here and in [../2026-10-22-live-v2/](../2026-10-22-live-v2/README.md) |
| `mpi/` | Job script and output, frame comparison, the bridge validation's log, both solver logs (gzip), the decomposition settings and logs, the code state |
| `poddiff/` | Job script and output, the hash comparison of every written file with run A, the size of the differences |
| `unstable/` | Job script, outputs, the summary script and its result |
| [manifest.json](manifest.json) | Origins, sizes and hashes of the files here |

## Notes

- Code that ran. Periodic run and both repeats: the Python callback equal to
  `df72c24` (all six callback files; `pod_svd.py` is the case's own module).
  The repeats compiled PODFoam with sources equal to `df72c24` except
  `PythonCreate.H` and `PythonGather.H`, which got the parallel fixes
  (`globalPath`, `scatterList`) after these builds; the runs are serial. The
  periodic run used the PODFoam binary of the October 22 run (Slurm 24757460).
  MPI test: every compiled source equal to `df72c24`. The code state each job
  saw is in its `HEAD`, `git-status.txt` and `changes.patch`.
- Repeat 1 (24903298) and repeat 2 (24903263) ended with exit 1 after their
  suites passed. Repeat 1: `pack_run.py` refused to pack because
  `PythonCreate.H` in the source tree had changed after the build; the archive
  was made afterwards with `pack_run.py` of `ab6b943`, which records the
  changed files instead (`source_tree_changed_since_build` in
  `build-inputs.json`). Repeat 2: its sweep stopped at a syntax error in
  `window_test.py` (fixed in `df72c24`); job 24903755 ran the sweep alone.
  An earlier repeat 1 (24903262) stopped at compilation (`pythonGatherToMaster`
  not declared) and is not kept.
- POD-difference job: it exited with 1 after writing `comparison.json`, at the
  script's last line (a step count per run under `set -e`); every run printed
  exit 0.
- The repeats' time directories and the periodic run's time directories are
  not in the release: the repeats' hash lists here show they equal the first
  run's, and the periodic run's byte comparison (`periodic-summary.json`:
  2,016 equal, 0 differing) shows they equal the twin's.
- MPI test: `pod_svd.py`, the case's POD module, refuses ranks other than 0;
  the test changed that check in its copy only (see `mpi_test.sbatch`).
- The records contain cluster paths and process ids as provenance.
