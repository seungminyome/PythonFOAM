# October 29 evidence: the merged code in a solver run

Slurm job 24936949 on MedicineBow, 2026-10-29, CPU node mbcpu-009, 7 min 20 s:
the checkout at `eff951b` (main after merging the callback, instability-test
and observer-3d branches and `record_written`; uncommitted changes were to
documents only, `git-status.txt`), built in the OpenFOAM v2212 image by
`validation/run_v2106.sh` ([merged_check.sbatch](merged_check.sbatch)).

| Check | Result |
|---|---|
| Build and bridge validation | PASS ([validation.log](validation.log)) |
| 2D step case, v2 frame at step 100, 110 steps | the frame's four files (`U.png`, `p.png`, `fields.npz`, `readable-metadata.json`) and the request body identical to the serial run of the 2026-10-27 MPI test (job 24903786); `telemetry.jsonl` 110 lines, no `.tmp` left |
| 3D case of the slice test, v2 frame at step 100, 110 steps | the slice (20,540 cells at z = 0.00714375 m), the frame's four files and the request body identical to the serial 3D run of job 24929629; `telemetry.jsonl` 110 lines, no `.tmp` left |

From [merged-check.json](merged-check.json); the solver logs are
`serial2d/log.PODFoam.gz` and `serial3d/log.PODFoam.gz`. No model was asked
(`LLM_ENABLED=0`). The run folder stays on the cluster at
`/cluster/medbow/gscratch/syome/github_repos/pod-merged-20261029/run-24936949`.
[manifest.json](manifest.json) lists every file here with its size and hash.
