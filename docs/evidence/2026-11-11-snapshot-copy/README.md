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
All eight builds succeeded, and all twelve runs ended with exit status 0 and no Python traceback.

## The other three solvers

Jobs 25191260 to 25191271 ran the same three ways for `PODFoam_Debug`, `APMOSFoam` and `AEFoam`,
each built from `6fde869` and from the branch on the four versions.

| Solver | Version | Matrices | First two columns equal: original | Branch | Branch matrices equal the Python-side copy | U and p equal in all three, written times |
|---|---|---:|---:|---:|---|---|
| `PODFoam_Debug` | 8 | 6 | 6 | 0 | all 6 | 2 of 2 |
| `PODFoam_Debug` | v2012, v2106, v2212 | 9 each | 9 | 0 | all 9 | 3 of 3 |
| `APMOSFoam`, 4 MPI ranks | 8 | 24 | 24 | 0 | all 24 | 2 of 2 |
| `APMOSFoam`, 4 MPI ranks | v2012, v2106, v2212 | 36 each | 36 | 0 | all 36 | 3 of 3 |
| `AEFoam` | 8, v2012, v2106, v2212 | 1 each | 1 | 0 | the 1 | 1 of 1 |

Every `AEFoam` run ends with a segmentation fault, exit status 139, after its first snapshot
matrix: after 101 time steps on OpenFOAM 8 and 21 on the others. It does so with the original
code and with the branch, so the table has one matrix and one written time per version for it.

## The branch in the original project's Docker image

Job 25191272 pulled `romitmaulik1/pythonfoam_docker` with rootless Podman and, as root, built
the branch's four solvers with the image's Python 3.6.9 and NumPy 1.19.5. All four built. PODFoam
then ran the shipped `Run_Case` for 221 time steps: of its 6 snapshot matrices, none has equal
first two columns. Record: [container/podman-small-25191272.txt](container/podman-small-25191272.txt).

## The PR's Docker lines as root, with Podman

Slurm job 25191239 pulled `romitmaulik1/pythonfoam_docker` from Docker Hub (digest
`sha256:32a99155…d84c`) with rootless Podman 5.2.5 and ran the Docker lines of the pull-request
texts in it as root, uid 0. `validation/run.sh` ended with `PASS` on `pr/podfoam-fix` (`473c802`)
and on `pr/podfoam-observer` (`9e278aa`). Records: [container/](container/).

A Docker daemon does not start on this cluster: job 25191209 stopped at "No subuid ranges found".
Podman takes the same `run` command. Earlier runs of the same lines used Apptainer as a normal user.

## Limits

- `AEFoam` is checked on its first snapshot matrix only, because every run of it crashes after
  that matrix.
- On v2012, v2106 and v2212 the case is the stabilised one, not the shipped one.
- The runs are short: 221 time steps on OpenFOAM 8 and 60 on the others. The branch has no validation script; `pr/podfoam-fix` has one.

## Files

- [scripts/](scripts/): `small.sbatch` for PODFoam and `sib.sbatch` for the other three, `inner.sh` (runs
  inside the OpenFOAM image), `compare2.py` and the two modules of each solver.
- [runs/](runs/): per job `summary.txt` and `result.json` (the comparison), `branch.diff`
  (the branch's `PythonComm.H` against the original), `BRANCH`, `UPSTREAM`, the two build logs and
  `job.out`. The case folders, 156 to 348 MB per job, stay on the cluster.
