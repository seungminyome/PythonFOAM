# PODFoam bridge validation

Ten serial time steps of the PODFoam case (20,540 cells) to check that the
C++/Python round trip is intact: every snapshot reaches Python as its own
array, NumPy returns five SVD modes per velocity component, the modes come
back as OpenFOAM fields, and the solver finishes normally. `Run_Case` itself
is not modified; the script works on copies.

```bash
cd Solver_Examples/PODFoam
./validation/run_v2106.sh                      # new directory ../../../pod-v2106.XXXXXX
./validation/run_v2106.sh --resume <run-dir>   # reuse mesh and reference solver output
```

The script, whatever its name, supports OpenFOAM v2012, v2106 and v2212
(openfoam.com) and OpenFOAM 8 (openfoam.org). It takes the version and the bashrc
of an OpenFOAM already sourced; with none sourced it uses v2106. To choose another,
set `OPENFOAM_BASHRC` to that installation's bashrc and `POD_OPENFOAM_VERSION` to
the version it reports (`WM_PROJECT_VERSION`). The script stops if the two differ,
and the run directory is named after the version:

```bash
OPENFOAM_BASHRC=/usr/lib/openfoam/openfoam2212/etc/bashrc POD_OPENFOAM_VERSION=v2212 ./validation/run_v2106.sh
OPENFOAM_BASHRC=/opt/openfoam8/etc/bashrc POD_OPENFOAM_VERSION=8 ./validation/run_v2106.sh
```

Other environment variables: `PYTHON` (default `python3` on `PATH`, needs numpy) and
`POD_WORKSPACE` (default: parent of the checkout). If `PYTHON` is not the system
Python, put its `lib` folder on `LD_LIBRARY_PATH`; otherwise the script stops at
`Unresolved shared libraries`. The script points `FOAM_USER_APPBIN` at the run
directory's `bin/`, so your own application folder is not written.

The validation passed with Python 3.11 on all four versions, and on OpenFOAM 8 also
with Python 3.6.9 in the Docker image the top-level README names.

## What the script does

1. Stages `baseline-pimple`, a copy of the shipped case with `LESModel Smagorinsky`
   added and a generated `controlDict` (fixed `deltaT=1e-5`, ten steps), and runs the
   standard `pimpleFoam` on it with floating-point traps off (`FOAM_SIGFPE=false` on
   openfoam.com; on openfoam.org the variable is unset, because any value turns them
   on). The outcome is only recorded (`baseline-pimple/log.pimpleFoam`,
   `baseline-pimple/exit-status`): on openfoam.com this copy reaches max Courant about
   21 and NaN in the second step, and on OpenFOAM 8 it finishes its ten steps.
   `log.checkMesh` reports 192 high-aspect-ratio cells and 16 faces above 70 degrees
   non-orthogonality. The shipped `Run_Case` differs from this copy: it adjusts its
   time step (`maxCo 1`), and on openfoam.com, with `LESModel` added by hand, it diverges
   within about 90 steps with upstream's build and with this code.
2. Stages a stabilised copy (`fixed-pimple`: laminar, initial U = (32.2 0 0),
   `deltaT=1e-7`, Euler, upwind convection, limited non-orthogonal correction,
   `DICGaussSeidel` pressure smoother) and runs `pimpleFoam` on it.
3. Stages the same copy with `python_module.py` from this directory as
   `fixed-pod`, runs the rebuilt PODFoam for ten steps with
   `podSvdInterval 10`, and compares it with `fixed-pimple`.

`prepare_case.py` holds the case edits and stops if one does not find its text in
`Run_Case`; `python_module.py` is the minimal bridge module (ten snapshots, five modes
per component, written to `python_svd_audit.npz` for the checks).

## Pass criteria (`verify.py`)

- Both solvers: exactly ten `Time =` entries at 1e-7 ... 1e-6 s, `End`, no
  `FOAM FATAL`, all residuals and written fields finite, no linear solve hitting
  the 1000-iteration cap, max Courant below 1.
- PODFoam log: ten `POD snapshot accepted` lines, a
  `POD SVD returned to OpenFOAM: rows=61620 modes=5 finite=true` line,
  `Python finalized successfully`.
- The snapshots Python kept equal the written U fields (rtol 1e-10, atol 1e-9); the
  returned modes are orthonormal, satisfy the eigen-equation of the snapshot
  matrix, and equal the written `upod_*`, `vpod_*`, `wpod_*` fields.
- U and p of `fixed-pod` equal `fixed-pimple` at every step (rtol 1e-10,
  atol 1e-9).

The script prints `PASS` only if all checks succeed. A passing run gives about
max Courant 0.211 (0.212 on OpenFOAM 8), max snapshot error 5e-11, max mode error
5e-13, and 45 field files checked in `fixed-pod`.

## What changes from upstream's PODFoam

Results change in these ways:

- **POD modes.** Each snapshot reaches Python as an array that Python owns. Upstream's
  module keeps the first snapshot of a window as a view of the C++ buffer, which the
  next snapshot overwrites, so in upstream's build the first two columns of every
  snapshot matrix are equal. Here the first column holds the first snapshot. With that
  overwrite reproduced in Python, the cell values of all modes equal upstream's.
- **Mode files.** The modes are written as dimensionless `zeroGradient` fields.
  Upstream's are copies of U's components, with U's dimensions and boundary conditions.
- **U and p on openfoam.com.** The pressure solve uses the `p` solver until the final
  corrector and `pFinal` there, as that version's `pimpleFoam` does. With one outer
  corrector, as in this case, a plain `pEqn.solve()` selects `pFinal` at every corrector
  there. On openfoam.org `pimpleFoam` has a plain `pEqn.solve()`, and so does this code,
  so U, p and phi stay byte-identical to upstream's on OpenFOAM 8.

Runs can stop or behave differently in these ways:

- **Floating-point traps** are on in the solver, as in `pimpleFoam`, and off around
  Python initialisation, calls and finalisation (`PythonFpeOff` in `PythonCompat.H`,
  which is `sigFpe::ignore` on openfoam.com), because NumPy's import overflows on
  purpose while probing machine limits. Upstream's argument handling leaves them off,
  so a run that goes on through an overflow there stops with SIGFPE here.
- **Checked calls.** A failed import, a missing function, or an error or `SystemExit` in
  `snapshot_func` or `svd_func` stops the solver with the Python traceback. U and p must
  be finite before a snapshot. `svd_func` must return a native float64 ndarray of shape
  `(3*cells, modes)` with 1 to `truncation` modes and finite values. `online_mode = False`
  in the shipped module stopped this way at `writeInterval` 3 and 6 in short tests: a
  tiny negative eigenvalue gives a NaN under `np.sqrt`.
- **Parallel runs.** All ranks must return the same number of modes, because the boundary
  update of each mode exchanges data between them; otherwise the run stops and says so.
  A rank without cells takes the others' count.
- **Python threads.** `Py_FinalizeEx()` runs at the end, after the Python function
  references are released. It waits for non-daemon threads, so a module that starts one
  must also stop it, or the solver does not exit.
- **`sys.path`.** The case directory comes first, so `-case` finds the case's module. The
  launch folder stays on the path after it.
- **Log.** Each step prints a `Time =` line with its deltaT, which the validation reads.
  Upstream's timing lines stay.

`podSvdInterval` in `controlDict` is new and optional. At 0, the default, a module with
`snapshot_func` and `svd_func` keeps the original schedule: a write step runs the SVD
instead of collecting a snapshot, if snapshots have been collected since the last SVD.
Above 0, every step collects a snapshot and the SVD runs every `podSvdInterval`
snapshots. An SVD on a step that writes nothing else then makes a time folder holding
only POD fields. If that is the newest folder, `startFrom latestTime` stops on the
missing `p`, and `purgeWrite` does not remove these folders.

This covers PODFoam only. `PODFoam_Debug` and `APMOSFoam` have the same
`array[:,0].reshape(-1,1)` line over a C++ buffer, `AEFoam` has `np.expand_dims` there,
and their `pEqn.H` have the plain `pEqn.solve()`. They were read, not run.

This is a connection test, not a physical validation of the case: the mesh
quality issues and the large initial pressure transient are still there.
