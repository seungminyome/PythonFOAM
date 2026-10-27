# 2026-10-27 (in progress)

Job scripts and the first small results of the 2026-10-27 tests, kept here
until the full write-up. The scripts hold MedicineBow paths as they ran.

| File | What |
|---|---|
| `jobs/poddiff.sbatch` | Slurm job 24903065: why POD mode files differed between paired runs |
| `jobs/mpi_test.sbatch` | Slurm job 24903786: the observer on 2 MPI ranks against a serial run |
| `jobs/run_cylinder*.sbatch`, `jobs/run_unstable.sbatch` | the cylinder flow (coarse, fine, with PODFoam) and the attempts at an unstable flow |
| `results/poddiff-24903065-comparison.json` | mode files with unlimited BLAS threads differ (30 of 42); with one thread all 42 are identical |
| `results/mpi-24903786-frame-comparison.json` | serial and 2-rank frames at step 100: same 20540 cells and centres |
| `results/periodic-24903264-summary.json` | 96 describe requests every 250 steps (`run_periodic.py`) |

`manifest.json` lists every file with its size and SHA-256.
