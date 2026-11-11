# Snapshot copy alone on four OpenFOAM versions (2026-11-11)

In short: branch `pr/podfoam-snapshot-copy` changes one statement in `PythonComm.H` of four
solvers, and with it PODFoam hands Python the snapshots it should. The written U and p stay
byte-identical to the original PODFoam on OpenFOAM 8, v2012, v2106 and v2212.

The branch is `8d29128`, two commits on argonne-lcf/PythonFOAM `6fde869`: `74e6450` for
PODFoam and `8d29128` for `PODFoam_Debug`, `APMOSFoam` and `AEFoam`. Each file gains 12 lines:
NumPy allocates the snapshot array and the solver copies its buffer into it. The original
code gave Python a view of that buffer, and the next time step overwrote it.

## Runs

Slurm jobs 25191171 to 25191174 on MedicineBow, 2026-11-11, one per version ([sacct.txt](sacct.txt)).
Each job builds PODFoam twice, from `6fde869` and from the branch, and runs one case three ways:

| Name in the records | Solver | `python_module.py` |
|---|---|---|
| `recording` | original | the shipped module, which also saves every snapshot matrix it hands to the SVD |
| `copy` | original | the same, with a copy of each snapshot made in Python |
| `ported` | branch | the same as `recording` |

On OpenFOAM 8 the case is the shipped `Run_Case` with `endTime` 1.5e-4, 221 time steps and two
SVD windows. On v2012, v2106 and v2212 the shipped case diverges, so the case uses the settings
of the bridge validation, a fixed time step of 1e-7 and 60 time steps, three SVD windows.

## Results

| Version, job | Matrices | First two columns equal: original | Branch | Branch matrices equal the Python-side copy | U and p equal in all three, written times |
|---|---:|---:|---:|---|---|
| 8, 25191171 | 6 | 6 | 0 | all 6 | 2 of 2 |
| v2012, 25191173 | 9 | 9 | 0 | all 9 | 3 of 3 |
| v2106, 25191172 | 9 | 9 | 0 | all 9 | 3 of 3 |
| v2212, 25191174 | 9 | 9 | 0 | all 9 | 3 of 3 |

A matrix is one velocity component of one SVD window. "Equal" means equal in every byte.
All twelve builds and all twelve runs ended with exit status 0 and no Python traceback.

## Limits

- The check covers PODFoam. The same change in `PODFoam_Debug`, `APMOSFoam` and `AEFoam` was
  checked on OpenFOAM 8 and v2106 in jobs 25088384 to 25088390 of
  [2026-11-02-round2](../2026-11-02-round2/README.md), with the same patch except its
  allocation check.
- The runs are serial and short. The branch has no validation script; `pr/podfoam-fix` has one.

## Files

- [scripts/](scripts/): `small.sbatch`, `inner.sh` (runs inside the OpenFOAM image),
  `compare2.py` and the two modules.
- [runs/](runs/): per job `summary.txt` and `result.json` (the comparison), `branch.diff`
  (the branch's `PythonComm.H` against the original), `BRANCH`, `UPSTREAM`, the two build logs and
  `job.out`. The case folders, 156 to 348 MB per job, stay on the cluster.
