# November 2 evidence: round 2 and the final PR branches

Slurm jobs of 2026-11-01 and 2026-11-02 on MedicineBow, University of Wyoming. The
folders below hold the records of each check: the pressure line, the three sibling
solvers, the error scenarios and the POD schedule on v2012 and v2212, and the cause of
the OpenFOAM 8 difference.

They also hold the flaky unit test, a model request on 2 MPI ranks, the 12B suites on
v2012 and OpenFOAM 8, the 6,000-step default on v2212, and `setup_12b.sh` with a real
download. Then come the slice pictures of the 3D case, the instability test without
stated times, and the checks of the final PR branches. The report is
[results-20261102.md](../../results-20261102.md).

## Code

Most round-2 runs used the PR tree `bf7a06e`, which was branch `pr/podfoam-observer`
on 2026-10-30. The original PODFoam is
[argonne-lcf/PythonFOAM](https://github.com/argonne-lcf/PythonFOAM) at `6fde869`.
Where a folder ran other code, its row says so.

The round-2 branches `r2/siblings` `34351f3`, `r2/flaky` `5b2a3de`, `78883f9` and
`041a88d`, `r2/gpu-suites` `c82c835` and `r2/setup12b` `0dfc260` and `2e77ed9` are
local and not on GitHub. Their changes are on the final branches `pr/podfoam-fix` at
`473c802` and `pr/podfoam-observer` at `cd23736`. `r2/instability` `6d38337` is on
`main` as `89733c6`.

Each job folder that records it has its `HEAD`. `git-status.txt` is empty in every one
except `instability/results/gpu-25080221/`. That job and the set build 25080121 ran on
`6677bac` with the four files of `6d38337` not yet committed, as
[logs/build-25080121.out](instability/logs/build-25080121.out) also shows. The SHA-256
of the four files are in [sha256.txt](instability/results/gpu-25080221/sha256.txt) and
in `code_sha256` of [test-set/manifest.json](instability/test-set/manifest.json). They
equal the blobs of `6d38337`, which changes only those four files.

## What ran

| Folder | Jobs | Code | Script | What it shows |
|---|---|---|---|---|
| `pfinal/` | 25080017; binaries from 24951137 to 24951140 | fork `bf7a06e`, original code `6fde869`, the images' `pimpleFoam` | [run_demo.sbatch](pfinal/demo/run_demo.sbatch), [inner.sh](pfinal/demo/inner.sh), [summarize.py](pfinal/demo/summarize.py) | Which pressure-solver dictionary each solve used, read from the solver name in the log (`p` = PCG, `pFinal` = GAMG): [summary.md](pfinal/demo/runs-25080017/summary.md), the 30 solver logs as gzip copies, [source-excerpts.md](pfinal/source-excerpts.md) with the OpenFOAM lines and [verify-20261102.txt](pfinal/verify-20261102.txt) (md5 of the copied source against the images) |
| `siblings/` | 25080208 to 25080213 (round 1), 25088384 to 25088390, 25088463 (round 2; 25088386 hung and was cancelled, 25088463 is its rerun) | original code `6fde869`; the one-line owned array of `34351f3` applied inside each job (`ported.diff`) | [siblings.sbatch](siblings/scripts/siblings.sbatch), [inner.sh](siblings/scripts/inner.sh), [sib2.sbatch](siblings/round2/scripts/sib2.sbatch), [inner2.sh](siblings/round2/scripts/inner2.sh), [compare2.py](siblings/round2/scripts/compare2.py), [port_patch.py](siblings/round2/scripts/port_patch.py) | `PODFoam_Debug`, `APMOSFoam` and `AEFoam` built and run on OpenFOAM 8 (shipped case) and v2106 (stabilised case) with the shipped module plus a snapshot dump (`module-recording.py`), with a Python copy (`module-copy.py`) and with the C++ owned array: [summary-all.json](siblings/round2/summary-all.json), `result.json` per run, `patch-dry-run.txt` of the fork's full diffs against the three solvers, the Keras test of job 25088390 |
| `scenarios/` | 25080002 (v2012), 25080003 (v2212); 25088377 to 25088380 (extra sets, v2012, v2212, v2106, 8) | fork `bf7a06e`, original code `6fde869` | [job.sbatch](scenarios/job.sbatch), [scenarios.py](scenarios/scenarios.py), [schedule.py](scenarios/schedule.py), [job_extra.sbatch](scenarios/job_extra.sbatch), [extra.py](scenarios/extra.py) | The 46 scenarios and the 26 schedule rows of v2012 and of v2212, compared row by row with the v2106 and 8 records of `ef78700` in `2026-10-30-versions/schedule/` by [compare4.py](scenarios/compare4.py) and [compare_sched4_ranks.py](scenarios/compare_sched4_ranks.py) ([compare4.json](scenarios/compare4.json), [compare_sched4_ranks.json](scenarios/compare_sched4_ranks.json)); all 26 schedule rows agree on the four versions; the older [compare_sched4.py](scenarios/compare_sched4.py) left the rank count out of its row key, so its [compare_sched4.json](scenarios/compare_sched4.json) holds 21 rows; with those records the scenarios have 47 names and 59 rows, because `traps-diverging-FOAM_SIGFPE-false` has no OpenFOAM 8 row and `traps-env-unset` ran only on 8; the 15 extra rows (compare, restart2, collated, traps2, late-overflow) on all four versions ([compare_extra.json](scenarios/compare_extra.json)); the decisive log lines ([messages.json](scenarios/messages.json)) |
| `of8-cause/` | 25080020 to 25080025, 25080040, 25080041, 25080389 | the images' `pimpleFoam` only; the frames compared are those of the matrix runs 24950782 and 24950783 | [run.sbatch](of8-cause/run.sbatch), [inner.sh](of8-cause/inner.sh), [run1.sbatch](of8-cause/run1.sbatch), [compare.py](of8-cause/compare.py) | Why OpenFOAM 8 differs from v2212: six `fvSolution` variants ([dicts/](of8-cause/dicts)) of the `relaxationFactors` block, 100 steps and one step, 2D and 3D, with every difference in [compare-final.json](of8-cause/compare-final.json) and [compare-1step.json](of8-cause/compare-1step.json); the source lines of both versions in [source-excerpts-relax.txt](of8-cause/source-excerpts-relax.txt); [NOTES.md](of8-cause/NOTES.md) |
| `flaky/` | 25080033, 25080034 (base); 25080195 to 25080198, 25080202, 25080203 (fixed test); 25088401, 25088402 (regression and probes) | `bf7a06e` (base); `r2/flaky` `78883f9` (load runs), `041a88d` (final) | [load.sbatch](flaky/load/load.sbatch), [run_one.sh](flaky/load/run_one.sh), [regress.sbatch](flaky/regress/regress.sbatch), [probe_refused30.py](flaky/regress/probe_refused30.py), the probes in [probe/](flaky/probe) | `test_connection_refused_is_reported_without_a_stall` under 8-copy load, 30 or 50 whole-module runs per job (`.out` files, `job.txt`, the failing runs' logs as gzip copies); the cause measured with cProfile in [probe-login-20261102.txt](flaky/probe/out/probe-login-20261102.txt); the regression of three test modules and 50 probes per Python in [regress/](flaky/regress) (`probes-summary.txt`) |
| `gpu-ranks/` | 25080027 (superseded: the wrapper recorded its own pid, and the frame comparison failed), 25080066 | fork `bf7a06e` | [ranks.sbatch](gpu-ranks/ranks.sbatch), [ranks_inner.sh](gpu-ranks/ranks_inner.sh), [rank_wrap.sh](gpu-ranks/rank_wrap.sh), [check_ranks.py](gpu-ranks/check_ranks.py) | One real Gemma 4 12B `describe` request at step 100 of 110, serial and on 2 MPI ranks, v2212 and OpenFOAM 8, NVIDIA A30: [ranks.json](gpu-ranks/run-25080066/ranks.json), [check.out](gpu-ranks/run-25080066/check.out), `llm_result.json`, the rank pid files, rank 1's log, the server's `/metrics` before and after each run |
| `gpu-suites/` | 25080035 (v2012), 25080036 (8), 25080037 (v2212, default 6,000 steps); 25080015 (reference runs) | `c82c835` for v2012 and 8: `bf7a06e` plus the change in [async_v2-version-override.patch](gpu-suites/records/async_v2-version-override.patch), a plain `git diff` that lets `async_v2.slurm` take the version from the environment; `bf7a06e` unedited for the default | [submit_suite.sh](gpu-suites/submit_suite.sh), [reference.sbatch](gpu-suites/ref/reference.sbatch), [collect.py](gpu-suites/collect.py), [frame_diff.py](gpu-suites/frame_diff.py) | The five asynchronous cases with Gemma 4 12B on an A30: `async-verification.json`, `summary.json`, `site.txt` and `server.cmd` per job in `records/gpu-suite-*/`, all three next to job 24950817 in [comparison.json](gpu-suites/records/comparison.json), the frames of the same run with no model requests on v2012 and 8 against 24950817 in [frame-diff-vs-24950817.json](gpu-suites/records/frame-diff-vs-24950817.json); the start directories' mesh checks in `start/` |
| `setup12b/` | 25080013 (GPU, A30); the download itself ran on the login node, outside Slurm | `bf7a06e` (`setup_12b.sh` as shipped); `r2/setup12b` `0dfc260` for `fixtest/` | [run_setup.sh](setup12b/run_setup.sh), [test_runtime.sbatch](setup12b/gpu/test_runtime.sbatch) | `setup_12b.sh` fetching the 7.9 GB for real without a token ([setup_12b.log](setup12b/setup_12b.log), [sha256.txt](setup12b/runtime/sha256.txt)); on the GPU node the prebuilt server as the script left it (step A), with its soname links restored (A2), the source build (B), the script again (C) and one chat request to the built server (D) in `gpu/run-25080013/`; the fixed script's run in `fixtest/` |
| `slice-3d/` | 25080032 (CPU: build, validation, four 300-step 3D runs, the test set), 25088316 (GPU, L40S: the 72 requests) | fork `bf7a06e` | [phase1.sbatch](slice-3d/scripts/phase1.sbatch), [phase1_inner.sh](slice-3d/scripts/phase1_inner.sh), [make_windows.py](slice-3d/scripts/make_windows.py), [phase2.sbatch](slice-3d/scripts/phase2.sbatch), [send_requests.py](slice-3d/scripts/send_requests.py) | Gemma 4 12B reading slice pictures of the extruded step case at four `POD_SLICE_Z`: [design.json](slice-3d/design.json) (written before the jobs), the test set's [manifest.json](slice-3d/phase1-25080032/testset/manifest.json), [truth.json](slice-3d/phase1-25080032/testset/truth.json) and [baseline.json](slice-3d/phase1-25080032/testset/baseline.json), the answers' [summary.json](slice-3d/phase2-25088316/results/summary.json) and [metrics.jsonl](slice-3d/phase2-25088316/results/metrics.jsonl), and `result.json`, `response.json`, `metrics.json` per request; [NOTES.md](slice-3d/NOTES.md) |
| `instability/` | 25080121 (the set), 25080221 (two models, L40S) | `r2/instability` `6d38337` on `main` `6677bac` (adds `instability_test2.py` and a `show_time=False` option) | [build_set.sbatch](instability/jobs/build_set.sbatch), [gpu_models.sbatch](instability/jobs/gpu_models.sbatch), [recount.py](instability/recount.py) | The instability test with no step or time in any request and frames 2×10⁻³ s apart in both classes: [DESIGN.md](instability/DESIGN.md) (written before the build), the set's [manifest.json](instability/test-set/manifest.json) with the text-identity check and its answer key [truth.private.json](instability/test-set/truth.private.json), the models' answers per item under `results/gpu-25080221/12b/` and `31b/`, [report.md](instability/results/gpu-25080221/report.md) and the independent [recount.json](instability/results/gpu-25080221/recount.json) with the item-by-item comparison against October 28 |
| `final-branches/` | Solver: 25090304 to 25090307, 25090315 to 25090319, 25090326 to 25090330, 25090332 to 25090335, 25090337 to 25090341, 25090471, 25090475 to 25090482. Observer: 25090610 to 25090612, 25090644, 25090645, 25090647, 25090963; 25090613, 25090614 and 25090616 stopped at start-up, 25090615 was cancelled before it started, and 25090646 hit a GPU fault. Fork `main`: 25092222. Load runs on the November tree: 25089961 to 25089963. Docker commands of the PR texts: 25090624, 25092824, 25093622, 25098200 | checked on `8954b25` and `24e9df6`, whose code equals the final `473c802` and `cd23736`; `main`'s CI list on `a1aea2e`, whose code equals `main` at `71ab2c3`; the load runs on `09d7d50`, whose code equals `276ea8e` | [fix/jobs/](final-branches/fix/jobs), [observer/jobs/](final-branches/observer/jobs), [main/jobs/ci.sbatch](final-branches/main/jobs/ci.sbatch) | The checks of the final PR branches: [fix/NOTES.md](final-branches/fix/NOTES.md) for builds and validation on OpenFOAM v2012, v2106, v2212 and 8, the Docker image, the comparison with the original PODFoam, scenarios, siblings, hooks and the 3D slice; [observer/NOTES.md](final-branches/observer/NOTES.md) for unit tests under load, the E2B quick start on v2106, the 12B suite and the 2-rank request on v2212; [plain/verify_r5.out](final-branches/plain/verify_r5.out), [pr-docs/verify_r6.out](final-branches/pr-docs/verify_r6.out), [pr-docs-r7/verify_r7.out](final-branches/pr-docs-r7/verify_r7.out), [pr-docs-r8/verify_r8.out](final-branches/pr-docs-r8/verify_r8.out), [pr-docs-r9/verify_r9.out](final-branches/pr-docs-r9/verify_r9.out), [pr-docs-r10/verify_r10.out](final-branches/pr-docs-r10/verify_r10.out), [pr-docs-r11/verify_r11.out](final-branches/pr-docs-r11/verify_r11.out), [pr-docs-r12/verify_r12.out](final-branches/pr-docs-r12/verify_r12.out), [pr-docs-r13/verify_r13.out](final-branches/pr-docs-r13/verify_r13.out) and [pr-docs-r14/verify_r14.out](final-branches/pr-docs-r14/verify_r14.out) show that only four READMEs, `HOOKS.md`, commit messages and dates changed after the checks; [docker-e2e-25090624.out](final-branches/docker-e2e/logs/docker-e2e-25090624.out) and [docker-e2e-25092824.out](final-branches/docker-e2e/logs/docker-e2e-25092824.out) for the PR texts' Docker commands on 8954b25/24e9df6 and d4ebf5c/ca68b32, and [docker-e2e/r6/](final-branches/docker-e2e/r6/logs/docker-e2e-25093622.out) on 6df2fa2/4414179, whose code equals the final branches'; [docker-e2e/github/](final-branches/docker-e2e/github/logs/docker-e2e-25098200.out) for the same commands on the final branches cloned from GitHub; [load-before-review/](final-branches/load-before-review/load.sbatch) for the whole `test_async` module under load on the November tree, 50 of 50, 50 of 50 and 30 of 30; [main/logs/ci-25092222.out](final-branches/main/logs/ci-25092222.out) for the fork's CI list; [setup12b-check/](final-branches/setup12b-check/setup.out) for the final `setup_12b.sh` on the fetched files; [sacct.txt](final-branches/sacct.txt) |

The pfinal demo runs the stabilised case of the validation with `p` = PCG/DIC (`relTol` 0.1), `pFinal` =
GAMG, `U` = `smoothSolver` and `UFinal` = PBiCGStab, so the solver name in each `Solving for` line names
the dictionary ([fvSolution](pfinal/demo/runs-25080017/v2106/case-fork-n1/system/fvSolution)). `fork-plainp`
is the fork rebuilt with the plain `pEqn.solve()`; on OpenFOAM 8 the fork's `#else` branch already is that
call, so there is no `fork-plainp` build on 8. `-n1` and `-n2` are `nOuterCorrectors` 1 and 2.

The sibling runs on v2106 use the stabilised settings of `validation/prepare_case.py`, because the
shipped `Run_Case` diverges in step 89 or 90 with all three solvers (jobs 25080211 to 25080213, as PODFoam
does in job 24951141). `AEFoam` never completes: with TensorFlow 2.20 and Keras 3.15 (installed into
`pydeps/tf`, kept on the cluster) the shipped module's `Input(shape=(int))` raises, the solver ignores the
`NULL` return and segfaults in the next step, so its numbers rest on the one snapshot matrix written
before the training call.

The of8-cause variants are: A as in the matrix runs, B without the `relaxationFactors` block, C = A plus
`pFinal 0.9` and `UFinal 0.9`, D tight solver tolerances without relaxation, E the equation factors only,
F the field factor only. [compare.py](of8-cause/compare.py) selects the 3D slice by the frame's `mesh_cells`
and compares as [compare_versions.py](../2026-10-30-versions/scripts/matrix/compare_versions.py) does.

The 2-rank case runs the validation bridge module `pod_svd.py` with its serial-only check taken out, as the
matrix runs of October 30 do ([ranks_inner.sh](gpu-ranks/ranks_inner.sh)).

The gpu-suites start directories for v2012 and 8 hold the `0.1` fields of job 24757460 (the same files as
24950817's start) beside that version's reference mesh, made by job 25080015
([reference.sbatch](gpu-suites/ref/reference.sbatch)); `start/mesh-check-*.txt` show equal mesh bodies, and
`boundary-diff-8.txt` the spelling difference of the boundary file on 8.

## Records left out

Not here, and kept on the cluster under `pod-versions-20261030/r2/`: the images (`.sif`), the solver
builds and the copied OpenFOAM source files, the time directories, frames and snapshot matrices, the
pictures and request bodies of the slice and instability sets, the model files and the 9 GB runtime that
`setup_12b.sh` fetched, `run-archive.tar.gz` of each suite, and the passing runs' logs of the flaky-test
load jobs (their counts are in the `.out` files). Solver logs and the failing test logs are gzip copies.
Paths inside the records are as recorded. Five records in `final-branches/` that name the model of an earlier commit trailer are derived copies with that one word replaced; the manifest marks them.

[sacct.txt](sacct.txt) has each job's state, node, partition and time; job 25088386 is the cancelled
sibling job, rerun as 25088463. The jobs that made the start states, 24757460
([October 22](../2026-10-22-live-v2/README.md)) and 24929629 ([October 28](../2026-10-28-3d/README.md)), and
the account runs 24951137 to 24951140 whose binaries the pfinal demo used
([October 30](../2026-10-30-versions/README.md)) are in those folders. [manifest.json](manifest.json) lists
every file here with its size and hash; [make_evidence.py](make_evidence.py) copied the files and wrote it.
