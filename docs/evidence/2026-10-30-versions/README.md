# October 30 evidence: OpenFOAM versions and upstream's PODFoam

Slurm jobs of 2026-10-30 on MedicineBow (University of Wyoming): PODFoam with the
observer on OpenFOAM v2012, v2106, v2212 and 8, each in an Apptainer image, and the
comparison with upstream's PODFoam at `6fde869`. The report is
[results-20261030.md](../../results-20261030.md).
[report_numbers.py](report_numbers.py) reads the report's numbers from the records here
and writes [report-numbers.json](report-numbers.json).

## Code

Most jobs ran `b17763d`, a local commit of the PR tree (branch `pr/podfoam-observer`
with an earlier README) that is not on GitHub. Its code equals `bf7a06e` and `main`:
[code-identity.txt](code-identity.txt) lists the blob of each of the 64 files under
`Solver_Examples/PODFoam`, without the three READMEs, read from git objects. Under that
folder, only `llm_demo/README.md` and `llm_demo/hpc/README.md` differ between `b17763d` and
`bf7a06e`.
The 24 files that only `main` has (experiment scripts, their tests) are listed there as
well. No job here runs them, apart from the unit tests.

Each job's folder has its `HEAD`; `git-status.txt` is empty for every job that records it.

## What ran

| Folder | Jobs | Code | What ran | Result |
|---|---|---|---|---|
| `matrix/` | 24950780 to 24950783 | `b17763d` | [version_check.sbatch](scripts/matrix/version_check.sbatch): build and bridge validation, then the observer with no model (`LLM_ENABLED=0`), v2 frame at step 100, 110 steps from t = 0.1 s: `serial2d`, `serial3d`, `par2d`, `par3d` | [compare.out](compare.out), [version-compare.json](version-compare.json); all PASS, all four cases end on all four versions |
| `commits/` | 24950784 to 24950791 | `2a93911`, `69cc2c1` | [try_version.sh](scripts/try_version.sh): the validation at commits 2 and 3 of the PR tree | PASS on all four |
| `stand-in/` | 24950794 to 24950797 | `b17763d` | [suites.sbatch](scripts/stand-in/suites.sbatch): validation, `run_demo.sh` both suites and the v2 asynchronous suite, against [stub_server.py](scripts/stand-in/stub_server.py) | all exit 0 with `PASS` |
| `documented-commands/` | 24950840 to 24950843 | `b17763d` | [doc_commands.sh](scripts/refix-jobs/doc_commands.sh): the observer commands of `llm_demo/README.md` in a fresh copy | 45 of 45 files equal, `DOC COMMANDS PASS` |
| `quick-start-24950804/` | 24950804 | `b17763d` | [quick_steps.sh](scripts/refix-jobs/quick_steps.sh): the quick start in order in the v2106 image, Gemma 4 E2B on 8 CPUs | [steps.tsv](quick-start-24950804/steps.tsv): 10 of 10 exit 0, both suites PASS |
| `gpu-suite-24950817/` | 24950816 (reference), 24950817 | `b17763d` | [submit_suite.sh](scripts/gpu/submit_suite.sh): `async_v2.slurm` unedited, v2212, Gemma 4 12B, NVIDIA A30, `LLM_LONG_STEPS=1000` | `async-verification.json` PASS |
| `gpu-suite-24949283/` | 24949283 | `fae10ba` | The same at `fae10ba`, whose `async_v2.slurm` and code differ from `b17763d`, on an NVIDIA L40S | `async-verification.json` PASS |
| `gpu-versions-24950818/` | 24950818 | `b17763d` | [part_a.sbatch](scripts/gpu/part_a.sbatch): one server on the host GPU, each image in turn, one real `describe` request at step 100 of 110, NVIDIA A30 | `part-a.json`: `ok` on all four |
| `gpu-versions-24949167/` | 24949167 | `fae10ba` | The same on an NVIDIA L40S | `part-a.json`: `ok` on all four |
| `docker-24950798/` | 24950798 | `b17763d` | [docker_inner.sh](scripts/refix-jobs/docker_inner.sh): upstream's image `romitmaulik1/pythonfoam_docker` (Ubuntu 18.04, OpenFOAM 8, Python 3.6.9): validation with only OpenFOAM sourced, `wclean && wmake`, the shipped `Run_Case` for 120 s | PASS; exit 0; 1,349 steps, stopped by the timeout |
| `upstream-comparison/` | 24951136 to 24951140 | `bf7a06e` | [pod_account.sbatch](scripts/matrix/pod_account.sbatch): upstream's and this fork's build, upstream's module, each difference accounted for | `account.json` in each folder |
| | 24951141 | `bf7a06e` | [upstream_regression.sbatch](scripts/matrix/upstream_regression.sbatch): shipped `Run_Case` with `LESModel` added, v2106 | `regression.json`: exit 1 after 90 steps, exit 136 after 87 |
| | 24950800 to 24950803 | `2a93911` | The comparison at commit 2 of the PR tree, which has no hooks: shipped and stabilised on 8, stabilised on v2106 and v2212 | the same counts and sizes |
| | 24948188 to 24948191 | `adcaec7` | The same on v2012, v2106, v2212, and the regression on v2106. The C++ of `adcaec7` differs from `bf7a06e` | the same counts and sizes |
| `schedule/` | 24950748, 24950749 | `ef78700` | [schedule.py](scripts/schedule/schedule.py): the POD schedule against a table predicted from the stated rule, 20 runs of this fork and 6 of upstream's build, v2106 and 8; [scenarios.py](scripts/schedule/scenarios.py): 46 failure and edge cases | `schedule.json`: 0 problems; `scenarios.json` |
| | 24949780, 24949782 | `fae10ba` | The schedule check at `fae10ba`, which differs from `b17763d` | 24949782: 0 problems. 24949780 (v2106): 2 log-count problems on 2 ranks (`step 4: 0 snapshots in C++ log, expected 1` and the same at step 1), cause not examined; none in 24950748 |
| `unit-tests/` | 24951126 | merged `main` (`41ca1bf`) | [unit_merged.sbatch](scripts/unit_merged.sbatch), a fresh clone, Python 3.10.22 and 3.12.15: the module list of `tests.yml`, then `make test` | 156 tests, OK, four times |
| | 24950761, 24951079 | `cabcfc6`, `bf7a06e` | [unit_tests.sbatch](scripts/matrix/unit_tests.sbatch), Python 3.10 and 3.12 | 156 tests OK; the PR tree's three modules, 83 tests OK |

The matrix runs use two cases that are not in the PR tree, copied into each run by
[version_check_inner.sh](scripts/matrix/version_check_inner.sh): the developed flow at
t = 0.1 s of job 24757460 (`pod-async-v2/run-24757460/.../async-no-llm`) and the extruded
case of job 24929629 (`pod-3d-20261028/run-24929629/case3d`, 164,320 cells). On 2 ranks the
script takes the rank check out of the case's `pod_svd.py`. Each run also adds a
`momentumTransport` file, read by OpenFOAM 8, with the settings of `turbulenceProperties`.

[compare_versions.py](scripts/matrix/compare_versions.py) orders each frame's cells by
position, because a parallel run gathers them rank by rank. |ΔU| is the magnitude of the
difference per cell, |Δp| is taken after removing each frame's mean p, and both frames'
peak and range come from the first of the pair. `frame-hashes.json` gives the SHA-256 of the
four files of each frame, which stay on the cluster.

`telemetry_lines_differ_only_in_run_id` in `version-compare.json` is `false` for v2212
against the earlier frames, because those runs were longer. Over the first 110 lines the
telemetry differs only in `end_time_s` and `run_id`.

[compare_pod_account.py](scripts/matrix/compare_pod_account.py) compares `U`, `p` and `phi`
by hash at every written time. When they differ, it takes the largest difference over the
numbers in the file, so for U a difference in one component. It compares each POD mode's
cell values, and each module's saved snapshot matrices column by column. The modules are
in each folder: `module-recording.py` is upstream's with the save added, and
`module-overwrite.py` also reproduces upstream's overwrite of the first column in Python.
`fork-plainp` is this fork's solver with the `#ifdef` of `pEqn.H` replaced by upstream's
plain `pEqn.solve()`.

## Records left out

Not here, and kept on the cluster under `pod-versions-20261030/`: the images (`.sif`), the
solver builds, the time directories and frames, the request bodies, the model files and
`run-archive.tar.gz` of each suite. Solver logs and telemetry are gzip copies. Paths inside the
records are as recorded.

[hf-no-token.txt](hf-no-token.txt) records two requests without a token for the 12B weights and
projector, both answered 200. `setup_12b.sh` itself ran only with a stand-in `curl` (job
24950752, not kept here); it has not fetched the files in this form.

[sacct.txt](sacct.txt) has each job's state, node, partition and time. [manifest.json](manifest.json)
lists every file here with its size and hash.
