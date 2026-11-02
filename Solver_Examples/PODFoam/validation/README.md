# PODFoam bridge validation

`validation/run.sh` runs ten serial time steps of the PODFoam case, which has 20,540
cells, and checks the round trip between C++ and Python. Every snapshot must reach
Python as its own array. NumPy returns five SVD modes per velocity component, and the
modes must come back as OpenFOAM fields. The solver must finish normally. The script
works on copies and leaves `Run_Case` unchanged.

```bash
cd Solver_Examples/PODFoam
./validation/run.sh                      # new directory validation/runs/pod-<version>.XXXXXX
./validation/run.sh --resume <run-dir>   # reuse the mesh and the pimpleFoam run
./validation/run.sh --baseline           # also run the shipped case with pimpleFoam (recorded only)
./validation/run.sh --baseline --resume <run-dir>   # both; --baseline comes first
```

The script supports the openfoam.com versions v2012, v2106 and v2212 and OpenFOAM 8
from openfoam.org. It uses the OpenFOAM that is already sourced, and v2106 when none
is. To choose another installation, set `OPENFOAM_BASHRC` to its bashrc and
`POD_OPENFOAM_VERSION` to the `WM_PROJECT_VERSION` it reports. If the two do not
match, the script removes the run directory it has just made and stops. The run
directory is named after the version:

```bash
OPENFOAM_BASHRC=/usr/lib/openfoam/openfoam2212/etc/bashrc POD_OPENFOAM_VERSION=v2212 ./validation/run.sh
OPENFOAM_BASHRC=/opt/openfoam8/etc/bashrc POD_OPENFOAM_VERSION=8 ./validation/run.sh
```

`PYTHON` names a Python 3 interpreter and defaults to `python3` on `PATH`. Its own
site-packages must hold numpy, because the script sets `PYTHONNOUSERSITE=1` and unsets
`PYTHONPATH`. If it is not the system Python, put its `lib` folder on
`LD_LIBRARY_PATH`; otherwise the script stops at `Unresolved shared libraries`.
`POD_WORKSPACE` sets where the runs go. Its default is `validation/runs/`, which
`.gitignore` covers.

The script points `FOAM_USER_APPBIN` at the run directory's `bin/`, so your own
application folder is not written. It sets `PYTHONUNBUFFERED=1`. Without it, Python's
`print()` output in `log.PODFoam` is block-buffered. It reaches the log in pieces, out
of step with the solver's lines, and the part still in the buffer is lost when a run
dies. Python sizes the buffer from the file system's block size. The scratch file
system of the cluster where this validation was tested has 1 MB blocks, so without
the variable a validation run's output would appear there in one piece at its end.
On a local disk with 4 KB blocks it would appear every few kilobytes. Runs outside
the script, such as `Run_Case/Allrun` or a PODFoam started by hand, need the variable
too, or `print(..., flush=True)`.

The validation takes about one minute on one core, build included. It passed with
Python 3.11 on all four versions. On OpenFOAM 8 it also passed with Python 3.6.9 in the
Docker image that the top-level README names.

## What the script does

1. It stages `fixed-pimple`, a stabilised copy of the shipped case with the settings
   in the table below, and runs `pimpleFoam` on it.
2. It stages the same copy with `python_module.py` from this directory as `fixed-pod`.
   The rebuilt PODFoam runs on it for ten steps with `podSvdInterval 10`, and the
   result is compared with `fixed-pimple`.
3. With `--baseline`, it also stages `baseline-pimple`. This is the shipped case with a
   generated `controlDict` that fixes `deltaT=1e-5` and ten steps. The standard
   `pimpleFoam` runs on it with floating-point traps off. On openfoam.com the script
   sets `FOAM_SIGFPE=false`. On openfoam.org it removes the variable, because any
   value, even an empty one, turns the traps on. The outcome is only recorded, in
   `baseline-pimple/log.pimpleFoam` and `baseline-pimple/exit-status`. On openfoam.com
   this copy reaches a max Courant of about 21 and NaN in the second step. On
   OpenFOAM 8 it finishes its ten steps.

| Setting | Value in `fixed-pimple` |
|---|---|
| Turbulence | laminar |
| Initial U | `(32.2 0 0)` |
| Time step | fixed, `deltaT=1e-7` |
| Time scheme | Euler |
| Convection | upwind |
| Non-orthogonal correction | limited |
| Non-orthogonal correctors | 2 |
| Pressure smoother | `DICGaussSeidel` |
| Steps | ten, every step written |

If `wmake`, `blockMesh`, `pimpleFoam` or PODFoam fails, the script stops and names the
log to read.

The staged copies drop the shipped `0/uniform/time`, which holds a restart `deltaT` of
1 s. With `adjustTimeStep yes`, the shipped case takes its first step from that file,
not from `controlDict`, and `maxCo` cuts it to about 0.012 s.

With that file in place, an `endTime` below about 0.006 s gives a run with zero steps
that still ends normally.

The shipped `Run_Case` adjusts its time step with `maxCo 1`. On openfoam.com it
diverges within about 90 steps, with and without this change.

`prepare_case.py` makes the case edits. It stops if an edit does not find its text in
`Run_Case`. `python_module.py` is the minimal bridge module: it keeps ten snapshots,
returns five modes per component and writes the snapshots, the modes and the singular
values to `python_svd_audit.npz` for the checks.

## What `verify.py` checks

For both solvers:

- the log has exactly ten `Time =` entries, at 1e-7 ... 1e-6 s, then `End`, and no
  `FOAM FATAL`;
- no `nan` or `inf` appears anywhere in the log;
- the log holds at least 80 residual values, and all of them are finite;
- no linear solve reaches the 1000-iteration cap;
- max Courant stays below 1;
- each of the ten time folders exists, and every field file in it is finite and holds
  its whole internal field;
- max |U| in the written fields stays below 1000 m/s.

For `fixed-pod`:

- the log has ten `POD snapshot accepted` lines, ten `deltaT = 1e-07` entries, the
  line `POD SVD returned to OpenFOAM: rows=61620 modes=5 finite=true` and
  `Python finalized successfully`;
- `python_svd_audit.npz` holds snapshots of shape `(20540, 3, 10)` and modes of shape
  `(61620, 5)`, and these and the singular values are all finite;
- the snapshots that Python kept equal the written U fields, with rtol 1e-10 and
  atol 1e-9;
- the singular values that the module wrote equal those of an independent
  `np.linalg.svd` of the kept snapshots, with rtol 1e-9;
- the returned modes are orthonormal, satisfy the eigen-equation of the snapshot
  matrix with these singular values and equal the written `upod_*`, `vpod_*` and
  `wpod_*` fields;
- U and p equal those of `fixed-pimple` at every time step, with rtol 1e-10 and
  atol 1e-9.
  On openfoam.com this rests on the pressure-solver selection described under "U and
  p on openfoam.com" below.

The script prints `PASS` only if every check succeeds. A passing run gives these
values:

| Passing run | Value |
|---|---|
| Max Courant | about 0.211, and 0.212 on OpenFOAM 8 |
| Max snapshot error | about 5e-11 |
| Max mode error | about 5e-13 |
| Field files checked in `fixed-pod` | 45 |

## What a module must provide

PODFoam imports `python_module.py` from the case folder. The module must define two
functions:

- `snapshot_func(array, rank)` receives U on this rank as a `(cells, 3)` float64 array.
- `svd_func(rank)` returns the modes as a native float64 ndarray of shape
  `(3*cells, modes)` with at least one mode. The u modes fill the first `cells` rows,
  then come v and w.

The solver stops at start-up if either function is missing or not callable. It writes
the first `podTruncation` modes; `podTruncation` is a `controlDict` entry with
default 5, and a value below 1 stops the run at start-up. A module that returns more
modes gets one warning in the log.
`Run_Case/python_module.py` is the shipped example.

## What changes in PODFoam

These changes affect results:

- **POD modes.** Each snapshot now reaches Python as an array that NumPy owns.
  PODFoam before this change passed a view of a C++ buffer that the next time step
  overwrote. The shipped module kept the first snapshot of a window as such a view,
  so the first two columns of every snapshot matrix were equal. Now the first column
  holds the first snapshot. On OpenFOAM 8, with that overwrite reproduced in
  Python, all modes have the same cell values as in PODFoam before this change. On
  openfoam.com U and p change as well; see "U and p on openfoam.com".
- **Mode files.** The modes are written as dimensionless `zeroGradient` fields.
  PODFoam before this change wrote the modes into copies of U's components, with U's
  dimensions and calculated patches that kept U's boundary values.
- **POD schedule at write steps.** With `podSvdInterval` 0, a write step runs the SVD
  if snapshots have been collected since the last SVD. Otherwise it collects a
  snapshot. PODFoam before this change ran `svd_func` at every write step. The shipped
  case writes every 100 steps, so its schedule stays the same. With `writeInterval 1`,
  or with two write steps in a row, a write step now collects a snapshot where the SVD
  ran before.
- **U and p on openfoam.com.** As in `pimpleFoam` of v2012, v2106 and v2212, the
  pressure solve uses `pFinal` only on the last non-orthogonal pass of the final
  corrector. Every other pass uses the `p` solver. With one outer corrector, as in this
  case, a plain `pEqn.solve()` selects `pFinal` at every corrector on these versions.
  On openfoam.org `pimpleFoam` calls a plain `pEqn.solve()`, and so does PODFoam. On
  OpenFOAM 8, U, p and phi stay byte-identical to those of PODFoam before this change.

These changes can stop a run or change how it behaves:

- **Floating-point traps.** The traps are on in the solver, as in `pimpleFoam`. They
  are off for all of `PythonCreate.H`, for each time step's `PythonComm.H` block and
  for finalisation, because NumPy's import overflows on purpose while it probes
  machine limits. Besides the calls into Python, these blocks copy U into the
  snapshots and write the mode fields. `PythonFpeOff` in `PythonCompat.H` switches
  them off; on openfoam.com it is `sigFpe::ignore`. PODFoam
  before this change constructed `argList` with `initialise=false`, which skips the
  signal set-up in `argList::parse`, so its traps were off. A run that went on through
  an overflow there now stops with SIGFPE.
- **Checked calls.** A failed import, a missing function, or an error or `SystemExit`
  in `snapshot_func` or `svd_func` stops the solver with the Python traceback. U and p
  must be finite before a snapshot. `svd_func` must return a native float64 ndarray of
  shape `(3*cells, modes)` with at least one mode, and the modes written must be
  finite. Each check stops the run with its own message. Only the message for a wrong
  shape names the shape received. In short tests the shipped module with
  `online_mode = False` stopped at `writeInterval` 3 and 6 with `Non-finite SVD result`,
  because a tiny negative eigenvalue gives a NaN under `np.sqrt`.
- **Mode count.** Only the first `podTruncation` modes are written, and more columns
  give one warning per run. PODFoam before this change fixed that count at 5 in
  `PythonCreate.H`.
- **Fixed cell count.** If the number of cells changes, the POD step stops the run with
  `POD requires a fixed cell count`. PODFoam before this change allocated its buffer
  once, at start-up, and did not check the count.
- **Parallel runs.** All ranks must write the same number of modes, because the
  boundary update of each mode exchanges data between them. A rank writes the smaller
  of what it returns and `podTruncation`. If the counts differ, the run stops and says
  so. A rank with fewer cells than modes returns fewer modes and stops the run with the
  same message. A rank without cells takes the count of the others.
- **Python threads.** `Py_FinalizeEx()` runs at the end, after the Python function
  references are released. It waits for non-daemon threads, so a module that starts one
  must also stop it, or the solver does not exit. A failed flush of Python's stdio at
  exit gives a warning, not an error. The solver holds the interpreter lock outside its
  calls into Python, so a thread that the module starts runs only during those calls.
- **`sys.path`.** The case directory comes first, so `-case` finds the case's module.
  The launch folder stays on the path after it.
- **Log.** Each time step prints a `Time =` line with its deltaT, which the validation
  reads. Each collected snapshot prints `POD snapshot accepted:` with the snapshot
  count and the time. Each SVD prints `POD SVD returned to OpenFOAM:` with the rows and
  the modes written. The timing lines stay. `setRootCaseLists.H` prints the OpenFOAM
  banner and the full header. `Python and NumPy initialized successfully` replaces the
  six start-up lines from `initialize python` on, and `Python finalized successfully`
  comes before `End`.

`podSvdInterval` is a new, optional `controlDict` entry. At 0, the default, the write
steps run the SVD as described under "POD schedule at write steps". Above 0, every time
step collects a snapshot, and the SVD runs every `podSvdInterval` snapshots. An SVD on
a time step that writes nothing else then makes a time folder that holds only mode
files. If that folder is the newest, `startFrom latestTime` stops on the missing `p`.

The mode files are written outside `runTime.write()`, so `purgeWrite` does not count
these folders. This is read from the code; no run has tested it.

This validation covers PODFoam only. `PODFoam_Debug`, `APMOSFoam` and `AEFoam` get the
same owning snapshot array: a copy of their buffer, with a check of the allocation.
Nothing else in them changes, and their `pEqn.H` keeps the plain `pEqn.solve()`.

This is a connection test, not a physical validation of the case. The case keeps these
problems:

- `log.checkMesh` reports 192 cells with a high aspect ratio.
- It reports 16 faces with non-orthogonality above 70 degrees.
- The initial pressure transient is large.
