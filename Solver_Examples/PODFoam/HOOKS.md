# PODFoam's optional Python hooks

PODFoam imports `python_module.py` from the case folder. The module must define two
functions, or the solver stops at start-up:

- `snapshot_func(array, rank)` receives U on this rank as a `(cells, 3)` float64
  array, once per collected snapshot.
- `svd_func(rank)` returns the modes as a native float64 ndarray of shape
  `(3*cells, modes)` with at least one mode. The u modes fill the first `cells` rows,
  then come v and w. The solver writes the first `podTruncation` modes;
  `podTruncation` is a `controlDict` entry with default 5.

`Run_Case/python_module.py` is the shipped example of both, and
[validation/README.md](validation/README.md) gives the full return contract.

Two more functions are optional:

- `mesh_func(centres, volumes, solution_d, rank, poly_points, poly_offsets,
  poly_cells[, slice_plane])` runs once at start-up, before the first time step, if
  `analysis_func` exists.
- `analysis_func(state)` runs once per time step, after the PIMPLE loop and the POD
  step and before `runTime.write()`. At a write step, that time's U and p are not yet
  on disk during the call.

They change neither U nor p. With `analysis_func` defined, the POD step collects a
snapshot at every time step, as "POD schedule" below explains.

## `mesh_func` arguments

All cell arrays cover the whole mesh and are gathered in rank order. A serial run
keeps the mesh's own cell order.

| Argument | Type and shape | Meaning |
|---|---|---|
| `centres` | float64 `(cells, 3)` | cell centres, m |
| `volumes` | float64 `(cells,)` | cell volumes, m³ |
| `solution_d` | tuple of 3 ints | `mesh.solutionD()`: 1 for a solved direction, -1 for an empty one |
| `rank` | int | always 0: only the master rank calls the hooks |
| `poly_points` | float64 `(P, 3)` | the points of all polygons, polygon after polygon |
| `poly_offsets` | int64 `(F + 1,)` | polygon `i` has the points `poly_offsets[i]:poly_offsets[i+1]`; `poly_offsets[0]` is 0 |
| `poly_cells` | int64 `(F,)` | the cell of each polygon, as an index into `centres` |
| `slice_plane` | dict | meshes without an `empty` patch only, see below |

`slice_plane` has these keys:

- `normal`: always `(0.0, 0.0, 1.0)`.
- `z_m`: z of the cut plane.
- `requested_z_m`: `POD_SLICE_Z`, or the middle of the z range.
- `z_source`: `"POD_SLICE_Z"` or `"middle of the mesh z range"`.
- `moved_off_mesh_points`: bool.
- `mesh_z_range_m`: `(z_min, z_max)`.

When no cut could be made, it holds `normal`, `z_m` None, `z_source`, `error` with a
message, and `mesh_z_range_m`.

## `state`

| Key | Type | Meaning |
|---|---|---|
| `schema_version` | int | 1 |
| `time_s`, `delta_t_s`, `end_time_s` | float | this step's time, time step and the end time, s |
| `step` | int | OpenFOAM's time index, which a restart continues |
| `snapshot_count` | int | the snapshots this run has collected so far, this step's included; from time 0 it equals `step` |
| `cells` | int | cells of the whole mesh |
| `residuals` | dict | per field `Ux`, `Uy`, `Uz` and `p`, this step's floats `initial_first`, `initial_last`, `final_last` and ints `linear_solves`, `iterations_total` |
| `courant` | dict | `mean`, `max`, recomputed from the completed step's `phi`, and `phase` |
| `continuity` | dict | `local`, `global`, `cumulative` and `phase` |
| `p_cells` | float64 `(cells,)` | kinematic pressure of every cell, m²/s² |
| `u_cells` | float64 `(cells, 3)` | velocity of every cell, m/s |

`residuals` leaves out empty directions, and it leaves out U when the momentum
predictor is off. `p_cells` and `u_cells` are in the same order as `centres`. If they
cannot be allocated, the call goes on without them.

On OpenFOAM 8, `residuals` has two more limits. There `Residuals<Type>` clears the
lists of one type, scalar or vector, at that type's first solve in a time step. A
field with no solve in a time step, for example through `maxIter 0`, keeps an earlier
step's list unless another field of its type is solved. A mesh motion deletes the
lists. With `moveMeshOuterCorrectors` on a moving mesh, they hold only the last outer
corrector's solves, and `initial_first`, `linear_solves` and `iterations_total` cover
only that corrector.

## Behaviour

All arrays are copies, so Python never sees solver memory. The return value of
`analysis_func` is ignored. An exception in `analysis_func` gives a warning and the run
goes on; the hook is called again at the next time step. An exception in `mesh_func`
gives a warning, and `analysis_func` runs without it. A module whose `analysis_func` or
`mesh_func` is not callable gets one warning and runs without that hook.

**Cost per time step.** With `analysis_func` defined, every rank sends its U and p to
the master rank at every time step. The master copies them into two new arrays and a
dictionary, whether or not the module uses them. The Courant and continuity numbers
add a face sum and a divergence of `phi`. In a large parallel case the master holds U
and p of the whole mesh at every time step.

**Threads.** The solver holds the interpreter lock outside its calls into Python. A
thread that the module starts runs only while the solver is inside such a call. These
calls include the import of `python_module`, the four functions and `Py_FinalizeEx()`
at the end. `Py_FinalizeEx()` waits for non-daemon threads, so a module that starts one
must also stop it.

**Floating-point traps.** The traps are off for all of `PythonCreate.H` and for each
time step's `PythonComm.H` block, as [validation/README.md](validation/README.md)
explains. These blocks also hold the mesh gathers, the plane cut, the gathers at each
time step and the Courant and continuity numbers, so these run without traps too.

**Parallel runs.** The master rank gathers the mesh, U and p in rank order, and only
the master calls the two hooks. Either the module on every rank defines them, or none
does. Otherwise the run stops at start-up. `snapshot_func` and `svd_func` stay per
rank.

**Cell polygons.** A case with an `empty` patch passes one polygon for each cell that
has a face on its first `empty` patch, taken from that face. A cell without such a
face gets no polygon. A patch that holds both the front and the back faces lists every
cell twice; only the first face of each cell is kept.

**Meshes without an `empty` patch.** A 3D mesh has none. `PythonSlice.H` cuts such a
mesh with the plane z = `POD_SLICE_Z`, by default the middle of the z range, and
passes one polygon per cut cell plus `slice_plane`. A plane through mesh points is
moved off them, and the solver log says so. The choice rests on the patch type alone,
so a 2D axisymmetric case with `wedge` patches and no `empty` patch is sliced too.

**POD schedule.** With `podSvdInterval` at its default of 0, a module without
`analysis_func` collects a snapshot at every time step except a write step with
snapshots collected since the last SVD. The SVD runs there instead. A module with
`analysis_func` collects a snapshot at every time step, and its SVD runs at write steps.
At this default the SVD windows and the mode files of the two modules differ. With
`podSvdInterval` above 0, every time step collects a snapshot and the SVD runs every
`podSvdInterval` snapshots, with or without `analysis_func`. U and p are the same
either way.
