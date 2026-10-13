# PODFoam bridge validation on OpenFOAM v2106

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

Environment variables: `OPENFOAM_BASHRC` (default
`/usr/lib/openfoam/openfoam2106/etc/bashrc`), `PYTHON` (default
`/usr/bin/python3`, needs numpy), `POD_WORKSPACE` (default: parent of the
checkout). The executable is built into the run directory's `bin/`, so
`FOAM_USER_APPBIN` is left alone.

## What the script does

1. Runs the shipped case with the standard `pimpleFoam` to reproduce the
   known divergence of the original setup (`deltaT=1e-5`, LES, max Courant
   about 21, NaN in the second step). `checkMesh` reports 192 high-aspect-ratio
   cells and 16 faces above 70 degrees non-orthogonality. This is the
   `baseline-pimple` copy, run with floating-point traps off.
2. Stages a stabilised copy (`fixed-pimple`: laminar, initial U = (32.2 0 0),
   `deltaT=1e-7`, Euler, upwind convection, limited non-orthogonal correction,
   `DICGaussSeidel` pressure smoother) and runs `pimpleFoam` on it.
3. Stages the same copy with `python_module.py` from this directory as
   `fixed-pod`, runs the rebuilt PODFoam for ten steps with
   `podSvdInterval 10`, and compares it with `fixed-pimple`.

`prepare_case.py` holds the case edits; `python_module.py` is the minimal
bridge module (ten snapshots, five modes per component, written to
`python_svd_audit.npz` for the checks).

## Pass criteria (`verify.py`)

- Both solvers: exactly ten `Time =` entries at 1e-7 ... 1e-6 s, `End`, no
  `FOAM FATAL`, all residuals and written fields finite, no linear solve hitting
  the 1000-iteration cap, max Courant below 1.
- PODFoam log: ten `POD snapshot accepted` lines, one
  `POD SVD returned to OpenFOAM: rows=61620 modes=5 finite=true`,
  `Python finalized successfully`.
- The snapshots Python kept equal the written U fields (rtol 1e-10); the
  returned modes are orthonormal, satisfy the eigen-equation of the snapshot
  matrix, and equal the written `upod_*`, `vpod_*`, `wpod_*` fields.
- U and p of `fixed-pod` equal `fixed-pimple` at every step (rtol 1e-10,
  atol 1e-9).

The script prints `PASS` only if all checks succeed. A passing run
(`pod-v2106.c5jpOq`, 2026-10-10) gave max Courant 0.211, max snapshot error
5e-11, max mode error 5e-13, 45 field files checked.

## Solver changes behind this

`PODFoam.C`, `PythonCreate.H`, `PythonComm.H`, `pEqn.H`:

- v2106 argument handling (`setRootCaseLists.H`), NumPy C API import with error
  checking, the case directory on `sys.path` so `-case` works.
- Snapshots are copied into a NumPy array that Python owns (no
  `PyArray_SimpleNewFromData` views of solver memory); U and p are checked
  finite before the call.
- Return-value checks: native float64 ndarray, shape
  `(3*cells, min(truncation, snapshots))`, finite; written as
  `zeroGradient` fields.
- `pEqn.solve()` uses the `pFinal` solver on the final corrector, as
  `pimpleFoam` does in v2106; without it the POD solver drifts from the
  reference.
- `sigFpe::ignore` around Python initialisation, calls and finalisation:
  NumPy's import deliberately overflows while probing machine limits, which
  OpenFOAM's FPE trap would otherwise report as a solver divergence.
- `Py_FinalizeEx()` at the end, with the function objects released first.
- Optional `podSvdInterval` in `controlDict` (0 keeps the original
  write-time SVD schedule).

This is a connection test, not a physical validation of the case: the mesh
quality issues and the large initial pressure transient are still there.
