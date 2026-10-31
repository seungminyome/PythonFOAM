# PODFoam's optional Python hooks

PODFoam calls two optional functions of the case's `python_module.py`, besides
`snapshot_func` and `svd_func`:

- `mesh_func(centres, volumes, solution_d, rank, poly_points, poly_offsets,
  poly_cells[, slice_plane])`, once at start-up, if `analysis_func` exists.
- `analysis_func(state)`, after every completed step.

`state` is a dictionary with these keys:

- `schema_version`, `time_s`, `delta_t_s`, `end_time_s`, `step`, `cells`.
- `residuals`: for `Ux`, `Uy`, `Uz` and `p`, this step's `initial_first`,
  `initial_last`, `final_last`, `linear_solves` and `iterations_total`. Empty
  directions are left out, and so is U without the momentum predictor.
- `courant`: `mean`, `max` and `phase`, recomputed from the completed step's `phi`.
- `continuity`: `local`, `global`, `cumulative` and `phase`.
- `p_cells`, `u_cells`: kinematic pressure and velocity of all cells.

All arrays are copies, so Python never sees solver memory. The return value of
`analysis_func` is ignored. An exception in either function gives a warning and
the run goes on.

**Parallel runs.** The master rank gathers the mesh, U and p in rank order and alone
calls the two functions, which every rank's module must define or none. `snapshot_func`
and `svd_func` stay per rank.

**3D meshes.** A 2D case passes one polygon per cell from its first `empty` patch.
A 3D mesh has none, so `PythonSlice.H` cuts it with the plane z = `POD_SLICE_Z`, by
default the middle of the z range, and passes one polygon per cut cell, plus
`slice_plane`. A plane through mesh points is moved off them, which the solver log says.

**POD schedule.** With `podSvdInterval` at its default of 0, a module without these
functions keeps the original schedule: a write step runs the SVD instead of
collecting a snapshot, if snapshots have been collected since the last SVD. A module
with `analysis_func` gets a snapshot at every step and an SVD at write steps, or every
`podSvdInterval` snapshots if that is set.
