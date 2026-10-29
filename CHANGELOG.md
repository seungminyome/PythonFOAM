# Changelog

Dates are when a run or change happened. Where a run is recorded, the code
revision that produced it is given.

## 2026-10-28, callback: telemetry without a history of all states, computed trend words (`16d665e`)

- `python_module.py`: `telemetry.jsonl` is no longer rewritten at the last
  step from a history of every state. Each step's line is encoded when the
  step arrives; a forked child with a deadline appends the pending lines to
  `telemetry.jsonl.tmp` every 500 lines or 60 s, and the last step appends
  the rest and renames the file. The finished file has the same bytes as
  before. The callback keeps the first state and the last three (the SVD
  summary's window start and residual trend); the request worker no longer
  writes the telemetry. Over the 24,000 recorded states of the October 27
  periodic run the Python heap stayed at most 0.515 MiB (tracemalloc's peak;
  0.067 MiB after the last state, which came right after an append) instead
  of growing to 31.7 MiB, and the last step took 0.023 s instead of 0.699 s;
  each step now encodes its line (in PODFoam the callback's median time per
  step rose from 0.079 to 0.107 ms to 0.163 to 0.217 ms), and a step with an
  append took 13.7 to 22.0 ms.
- v2 sequences: `llm_result.json` records `computed_trends`, the answer key's
  three trend words from the frames' arrays inside the plotted range, and
  `computed_trends_agreement` against the model's words; nothing new is
  sent. `LLM_SEQUENCE_PROMPT=t` or `tn` sends the `-t` or `-tn` form of the
  October 27 trend test; the default request is unchanged byte for byte.
- `verify_async.py` checks `computed_trends` and the `t`/`tn` bodies when a
  run has them.
- Tests: telemetry against main's callback (2,345 steps, two batch sizes),
  memory over 6,000 steps, killed, failed and abandoned appends, a state that
  cannot be encoded, the time trigger; computed trends against the picture
  tests' functions, the `t` and `tn` bodies, refusals; 107 in the suite.
- Run: Slurm job 24929555 (CPU, mbcpu-010): main's and this callback on the
  staged step case, 1,250 steps with LLM_ENABLED=0, describe at step 100,
  sequence at steps 100, 150 and 200, the `tn` form, and the describe case on
  2 MPI ranks. Every written file, `telemetry.jsonl` (1,250 lines) and the
  request bodies identical between main and the branch; the records differ
  only in run-dependent values and the new `computed_trends`; the `tn` body
  equals the tested builder. On 2 ranks the log lines match only as sorted
  lists and the POD audit file is unreadable in both runs (both ranks write
  it); the comparison was rerun with that handled (job 24929607). Records in
  [docs/evidence/2026-10-28-callback/](docs/evidence/2026-10-28-callback/README.md).
## 2026-10-28, instability test (`8d6a10a`, report `c9a1ba1`, review fixes `660f8c4`)

- `readable_request.py`: `STABILITY_V2OWN_SYSTEM_PROMPT` and
  `stability_v2_payload()` ask whether three v2 frames (own colour scales)
  show signs of numerical instability. `llm_client.py` has the `stability`
  reply schema (`reason`, then `stable`, `unstable` or `cannot_tell`); it is
  not an `LLM_MODE`, so the solver still refuses it. `snapshot_runner.py`
  scores it and `picture_test.py` summarises it. Existing request bodies are
  unchanged byte for byte (golden tests).
- New `instability_test.py`: builds the set from pimpleFoam runs (runs that
  crashed give `unstable` triples labelled by steps to the crash, runs that
  ended give `stable` ones), runs it through `picture_test.py`, and reports
  the balanced score, how early `unstable` is said, answers by run and two
  numeric baselines. New `test_instability_test.py` (12 tests since
  `660f8c4`; 107 with `test_llm_client`, `test_callback`,
  `test_ablation_runner`, `test_async` and `test_picture_test`, in any order
  and with `unittest discover`).
- Runs: `central-dt2e-5` run again from t = 0.1 s crashed in step 467 (job
  24929408); the two upwind runs (2,000 steps) and `central-dt5e-6` (4,000
  steps) ended (24929452, 24929449); test set build (24929495); Gemma 4 12B,
  26B-A4B, 31B and Qwen3.5-35B-A3B on its 70 requests (24929533,
  24929534). Records in
  [docs/evidence/2026-10-28-instability/](docs/evidence/2026-10-28-instability/README.md).
- Review fixes (`660f8c4`). `instability_test.main()` replaced
  `picture_test`'s set lists and never put them back, so `test_picture_test`
  failed (3 errors) when it ran after `test_instability_test` in one process,
  as with `unittest discover`; `main()` now restores them, also after an
  error. A run counts as crashed only when its log has a floating point
  exception trace (`Foam::sigFpe`) and no `End`; `report` refuses run
  folders made with different answer keys. Built again with this code, the
  set has the same answer key and request bodies, and `report` gives the same
  reports (job 24929764). The evidence README now says that the requests'
  stated frame times alone separate the two classes (54 of 54 scored items),
  that the upwind runs overlap most, not all, of the crashed runs' Courant
  numbers, and where the central runs' largest |U| outside the window is
  (`flow/domain_max.py`).

## 2026-10-27, reading change, 4-bit Qwen, a cylinder flow, requests every 250 steps, MPI (`6afbdeb`, `df72c24`, `ab6b943`)

- `readable_request.py`: sequence prompts that state the answer key's
  thresholds (`thresholds=True`), add each time's extrema to the note
  (`numbers=`) or send the note without pictures (`images=False`); with the
  defaults the bodies are unchanged byte for byte. New `sequence_test.py`
  builds trend sets from saved states in five forms; `window_test.py` and
  `sequence_test.py` take `--dt` and `--y-span`.
- `python_module.py`: `LLM_ANALYSIS_EVERY=N` sends a describe request every N
  steps (v2 only), each recorded in `llm_requests/step-NNNNNN/` with an index;
  the bytes moved over the worker pipe are recorded; `LLM_KILL_JOIN_S`
  defaults to 0.1 s. New `run_periodic.py` and `hpc/periodic_v2.slurm` run a
  long case with requests and its twin and compare them.
- PODFoam: in a parallel run the mesh and the fields are gathered to the
  master rank (`PythonGather.H`), which alone calls `mesh_func` and
  `analysis_func`; the Python path includes the case root. `pod_image.py`
  keeps one polygon per cell when a 2D patch lists both faces.
- GPU scripts: 4-bit Qwen rows in `models.tsv`; `start_server.sh` passes
  `LLM_IMAGE_MIN_TOKENS`; `window_test.slurm` runs `PICTURE_TEST_SCRIPT` and
  loads `POD_HOST_MODULES`; `async_v2.slurm` runs only the sweep when
  `POD_SUITE_RUN` is set. `pack_run.py` records sources changed since the
  build instead of refusing to pack.
- Tests: periodic requests, their records and refusals; 95 in the suite.
- Runs: trend test (jobs 24903974, 24903975), 4-bit Qwen (24903976,
  24903977), a cylinder flow (24903978 and the flow runs), a request every
  250 steps over 24,000 steps (24903264), two repeats of the October 22
  solver run (24903298, 24903263 with 24903755), MPI (24903786), POD files
  (24903065), unstable-flow attempts. Report
  [docs/results-20261027.md](docs/results-20261027.md), records in
  [docs/evidence/2026-10-27-picture-tests/](docs/evidence/2026-10-27-picture-tests/README.md)
  and [docs/evidence/2026-10-27-solver/](docs/evidence/2026-10-27-solver/README.md),
  archives in the `tests-2026-10-27` release.
- README, evidence index, pages index, `llm_demo/README.md` and
  `hpc/README.md` give the results; open problems and next steps updated.

## 2026-10-22, v2 pictures from the running solver, random windows, Qwen models (runs from `354caf9` with uncommitted changes; published in `dee7731`)

- New in `llm_demo/`: `readable_request.py` (the v2 request builder, moved out
  of `picture_test.py` and shared by the picture tests and the callback),
  `run_live_sweep.py` (describe requests at several steps of a running
  solver, each with its own random window) and `window_test.py` (picture sets
  with the plotted window placed at random around the fastest cell). In
  `llm_demo/hpc/`: `async_v2.slurm` (the asynchronous suite with v2 pictures
  and the sweep, OpenFOAM in an Apptainer image, llama-server on the host
  GPU) and `window_test.slurm`; four Qwen rows in `models.tsv`;
  `start_server.sh` reads `LLM_IMAGE_TOKENS`.
- `python_module.py`: `LLM_IMAGE_STYLE=v2` draws one picture per field for
  `describe` and `sequence` requests, writes each frame (arrays, pictures,
  metadata last) to its own folder and never overwrites or sends a frame left
  by an earlier run; v2 requests send `max_tokens` 320, the picture-test seed
  and no prompt cache; a v2 describe request keeps no SVD window.
  `LLM_KILL_JOIN_S` sets how long a killed worker may take to be reaped. The
  default (`v1`) is unchanged.
- `run_async_cases.py`, `verify_async.py`: `LLM_LONG_START` starts every case
  from a developed state (mesh and start files checked by hash); for v2 runs
  the verifier checks that each request body equals the builder applied to
  the frame on disk, byte for byte, that frame arrays equal the written
  fields, and scores the answers. `run_demo.sh` and `validation/run_v2106.sh`
  take the OpenFOAM version from `POD_OPENFOAM_VERSION` and the Python
  library name from the interpreter. `pack_run.py` records the git state the
  job script took on the host.
- Tests: golden tests that rebuild two published picture-test requests from
  their pictures byte for byte and pin five more by hash; v2 callback tests
  (describe, sequence, refusals, reruns in the same folder); 92 in the suite.
- Runs: the five asynchronous cases with v2 pictures and Gemma 4 12B from a
  developed flow, and eleven sweep requests (job 24757460); random-window
  tests for eleven models, three window seeds and a larger image-token limit
  (jobs 24757344, 24757382 to 24757384); a developed flow with random windows
  (job 24757459); four Qwen models on the 308 requests (job 24757327); the
  flow runs 24757337 and 24757429. Report
  [docs/results-20261022-live.md](docs/results-20261022-live.md), records in
  [docs/evidence/2026-10-22-live-v2/](docs/evidence/2026-10-22-live-v2/README.md)
  and [docs/evidence/2026-10-22-window-test/](docs/evidence/2026-10-22-window-test/README.md),
  archives in the new `pod-insitu-v2-2026-10-22` release and the
  `picture-test-2026-10-22` release.
- README, evidence index, pages index, `llm_demo/README.md` and
  `hpc/README.md` give the results; open problems and next steps updated.
  `.gitignore` covers all `pod-*.out` job logs.

## 2026-10-22, picture-reading test (prepared 2026-10-21 in `58e00d9`, run as Slurm job 24756981)

- New in `llm_demo/`: `readable_image.py` (one field per picture, axes in
  percent of the plotted range with a grid line every 10 %, colour bar
  labelled with five values from the minimum to the maximum), `foam_fields.py` (reader for ASCII OpenFOAM fields
  and the empty-patch polygons), `picture_test.py` (build, check, run and
  report a fixed set of picture requests scored against a withheld key) and
  `test_picture_test.py` (13 tests, 83 in the suite). In `llm_demo/hpc/`:
  `models.tsv` (seven Gemma 4 models at pinned revisions and hashes),
  `fetch_models.sh` and `picture_test.slurm`; `start_server.sh` and
  `stop_server.sh` accept model, context, batch and state-folder overrides
  and behave as before when they are unset.
- Run: 308 requests to each of seven Gemma 4 models (E2B in three forms, E4B,
  12B, 26B-A4B, 31B) on one NVIDIA RTX A6000. Report
  [docs/results-20261022.md](docs/results-20261022.md), records with the
  answer key and an independent re-scoring in
  [docs/evidence/2026-10-22-picture-test/](docs/evidence/2026-10-22-picture-test/README.md),
  both archives in the `picture-test-2026-10-22` release.
- README, evidence index, `hpc/README.md`, `llm_demo/README.md` and the pages
  index give the results; open problems and next steps updated. `hpc/README.md`
  and the comment in `models.tsv` say that e2b-qat also has another projector
  file (BF16, like e2b-bf16), and that in the saved flow the trend words, not
  the flow, stay the same. `Makefile`: the tests take about 30 s.
- The temporary pre-release `picture-test-input-20261021`, which carried the
  input bundle to the cluster, was removed; the bundle is an asset of the new
  release.

## 2026-10-20, 12B replay published (run of 2026-10-19, code `934da23`)

- Records of the October 19 paired replay with Gemma 4 12B QAT on an NVIDIA A30
  in [docs/evidence/2026-10-19-12b/](docs/evidence/2026-10-19-12b/README.md):
  six requests and replies, job script and output, Slurm accounting, server and
  build logs, hash manifest, and a manual review of the answers. All six
  answers say the position is unknown; 2.0 to 3.3 s per request.
- New section in the October 17 report and a 12B table in the README;
  corrected statements that 12B was untested (README, October 20 report,
  `hpc/README.md`); a 12B paragraph and link on the pages index; links from
  the evidence index, the 2026-10-17 and 2026-10-19 evidence pages and
  `llm_demo/README.md`.
- `hpc/README.md`: "Tested on" with the MedicineBow site lines and the source
  build of llama.cpp (the prebuilt b11429 libraries need GLIBC_2.38); the 12B
  server lowers the image-token limit to 128.
- `replay_12b.slurm`, `demo_12b.slurm`: `HF_TOKEN` only needed to download the
  weights; account and partition go on the `sbatch` command line.
  `setup_12b.sh` also hashes the `llama-server` in use.
- `.gitignore`: the 12B runtime folder and job outputs; `check_links.py`
  skips the runtime folder.

## 2026-10-20, corrections (documents and tests)

Every number in the October 17 to 20 pages was checked against the records
again.

- October 20 report and README: in the refused and stalled cases the
  request-step callback was 0.005 s, not 0.004 s; the step at which a reply
  was recorded took 0.008 to 0.019 s; the model waits were shorter than on
  October 17 mainly because the prompts were shorter, and the trial that
  warmed the cache ran minutes, not an hour, before; max |U| at step 750 is
  49.6 m/s; the fastest cell moved 4 mm rather than staying in one cell; the
  whole-domain plot spans x = -1.55 to 0.60 m; replay latencies, prompt sizes
  and the size of one image (about 106 prompt tokens, not 270) corrected; two
  quotations corrected.
- October 17 report and October 19 notes: two replies, not one, misread the
  Courant evidence; on October 19 the coordinates were the same but the
  numbers-only reply and the wording of five replay answers changed; the
  machine has 7.8 GiB of RAM.
- `make test` and the CI tests include `test_async.py` (70 tests). Two of its
  tests assumed a fast machine and failed on the CI runner: the detached-worker
  test now waits for the reply file, and the sequence test checks the fork
  steps strictly and leaves out the last step, which may wait for a late reply.
  The other step-time bounds are 0.5 s.
- `docs/evidence/2026-10-20/manifest.json` lists the four replay manifests,
  with corrected origin paths and the gzip copies marked as such.
- `llm_demo/README.md`: replay commands fixed (the last frame is
  `llm_observation/` itself); from the published frames they rebuild the 24
  replay requests byte for byte; full trend vocabulary; notes on
  `LLM_MAX_TOKENS` and the asynchronous runner; the SVD summary goes only with
  observe requests.
- Pages index: the October 20 paragraph names its code and run, keeps the
  position result apart from the sequence question, and links the October 20
  report and evidence.

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
- Repeat of the October 17 run and replay (`docs/evidence/2026-10-19/`): same hashes, the same image reply and replay coordinates; the numbers-only reply and the wording of five replay answers changed.
- `llm_demo/hpc/`: scripts and Slurm jobs to repeat the measurements with Gemma 4 12B on a GPU node.
- Paired replay with Gemma 4 12B QAT on an NVIDIA A30 (MedicineBow, Slurm job
  24696203, code `934da23`); published on 2026-10-20.
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
