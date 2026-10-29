# October 28 evidence: v2 observer pictures of a 3D case through a plane slice

Solver runs of 2026-10-28 on MedicineBow (University of Wyoming), one CPU
node per job: PODFoam in OpenFOAM v2212 (Apptainer image `of2212.sif`), the
observer with v2 pictures and no model (`LLM_ENABLED=0`).

## What was changed

Until now v2 pictures needed one polygon per cell from the empty patch of a 2D
case, and a 3D case was refused. Now (commits `07759b0` and `127a1dc`):

- `PythonSlice.H` cuts a 3D mesh (no empty patch) with OpenFOAM's
  `cuttingPlane` at z = `LLM_SLICE_Z`, default the middle of the mesh's z
  range, normal (0 0 1), not triangulated: one polygon per cut cell, its
  section. A plane through mesh points lies on the faces between two cells;
  it is moved halfway to the next point plane above. `PythonCreate.H` passes
  the polygons through the existing `mesh_func` arguments (per-rank cell
  offsets, gathered to the master) and describes the plane in an eighth
  argument. A 2D case gets the seven-argument call as before.
- Python (`pod_image.plane_slice`, `python_module.py`,
  `readable_request.render_frame`): a v2 frame of a 3D case holds only the
  slice cells. `fields.npz` keeps their centres (the 3D cell centres), U and
  p, plus `mesh_cells`, `polygon_points` and `polygon_offsets`;
  `readable-metadata.json` gets `slice`. The request is built as for 2D.

## Jobs

| Job | What | Code | Result |
|---|---|---|---|
| 24929463, 24929474 | compile checks (wmake only; that script is not kept) | working tree before `07759b0` | 24929463 failed (`MeshedSurface.H` not found: `Make/options` lacked the surfMesh include); 24929474 compiled with no warnings |
| 24929484 | slice test, first attempt | `07759b0` | stopped at the job's own cell-map check: its tolerance (10⁻¹² m) was below the precision of the written cell centres (difference 1.0×10⁻¹¹ m); [output](slice-test-24929484.out) |
| 24929500 | slice test | `07759b0` | every check passed; the geometry line of the run with `LLM_SLICE_Z=abc` said `slice z=0` although no slice was made (fixed in `127a1dc`); [output](run-24929500/slice-test-24929500.out), [comparison](run-24929500/frame-comparison.json) |
| 24929629 | slice test, final code | `c7a25d3` (code of `127a1dc`) | the results below; [output](slice-test-24929629.out) |

The job outputs and run folders stay on the cluster in
`/cluster/medbow/gscratch/syome/github_repos/pod-3d-20261028/`; the final run
is `run-24929629` there (time directories, frames, request records, logs).

## The 3D case

- Made by [make_case3d.py](make_case3d.py) from the staged 2D step case
  (20,540 cells, developed flow at t = 0.1 s, the case of the 2026-10-27 MPI
  test): its `blockMeshDict` with 8 cells in z instead of 1 (z from 0 to
  0.0127 m, the thickness of the 2D mesh) and the front and back patches
  changed from `empty` to `wall`; 164,320 cells.
- checkMesh ([log](case3d/log.checkMesh)) fails one check, high aspect ratio:
  largest 7601.13, 1,536 cells (8 × 192). The 2D mesh of the bridge
  validation reports the same largest ratio for 192 cells (its checkMesh log
  in `run-24929629/pod-v2212.x73dcD/` on the cluster).
- Start state: U and p of the 2D case at t = 0.1 s copied into each of the 8
  layers, Uz = 0; boundary conditions as in 2D, with no-slip walls front and
  back (p zero gradient). The cell map was checked with OpenFOAM's cell
  centres ([case3d-check.json](case3d-check.json)): 8 cells per 2D cell, x
  and y equal within 1.0×10⁻¹¹ m (centres written with 12 digits; the two
  closest 2D centres are 1.2×10⁻⁵ m apart).
- This start is not a developed 3D flow: the front and back walls start
  acting at t = 0.1 s, and the runs are 150 steps of 5×10⁻⁶ s.

## Runs

All with `LLM_ENABLED=0 LLM_MODE=describe LLM_IMAGE_STYLE=v2 LLM_ASYNC=1
LLM_ANALYSIS_STEP=100 LLM_IMAGE_XRANGE=0,0.12 LLM_IMAGE_YRANGE=0,0.04`
(other values per row), time step 5×10⁻⁶ s from t = 0.1 s, one BLAS thread.

| Case | Ranks | Steps | Observer | Slice | Written |
|---|---|---|---|---|---|
| `serial3d` | 1 | 150 | yes | default | every 50 steps |
| `par3d` | 2, scotch | 150 | yes | default | every 50 steps, reconstructed |
| `noobs3d` | 1 | 150 | no: `python_module.py` is the POD module, no `analysis_func` | none | every 50 steps |
| `slicez3d` | 1 | 10, frame at step 5 | yes | `LLM_SLICE_Z=0.002` | no |
| `badz3d` | 1 | 4, request at step 2 | yes | `LLM_SLICE_Z=abc` | no |
| `outz3d` | 1 | 4, request at step 2 | yes | `LLM_SLICE_Z=1.0` | no |
| `serial2d` | 1 | 120 | yes | 2D case, no slice | no |

The bridge validation (`validation/run_v2106.sh`, 2D, ten steps) ran first
with the same build.

## Results

From [frame-comparison.json](frame-comparison.json) (written by
[compare_3d.py](compare_3d.py)) unless another file is named.

- **The slice.** The middle of the z range, 0.00635 m, lies on the point
  plane between the fourth and the fifth cell layer (counted from z = 0), so
  the plane moved to 0.00714375 m, the middle of the fifth cell layer. It
  cuts 20,540 cells, one per 2D cell, whose centres all lie at
  z = 0.00714375 m (to 5×10⁻¹⁸ m). The frame holds those 20,540 of the
  164,320 cells.
- **Serial and 2 ranks.** The same 20,540 cells, matched by mesh cell label
  (through decomposePar's `cellProcAddressing`) and sorted by centre; centres
  equal to 4.2×10⁻¹⁷ m, polygon vertices identical (each polygon's vertices
  sorted); U within 2.5×10⁻³ m/s (largest component 37.2 m/s) and p within
  0.036 m²/s² (largest |p| 282), the differences of a parallel solve. The
  ranks held 10,293 and 10,247 of the slice cells.
- **Frame against the written fields** at t = 0.1005 s (step 100): equal
  within the 12 digits of the written files (largest relative difference
  4.9×10⁻¹²), serially and for the reconstructed 2-rank run.
- **Observer against no observer.** All 63 files of the three written time
  directories (U, p, phi, POD mode files, `uniform/time`) identical.
- **The tools that read frames.** `readable_request.load_frame` (every hash
  checked) and `picture_test.load_v2` (answer key) read the slice frame; the
  request body the callback wrote equals `describe_v2_payload` applied to the
  frame; the request note gives 20,540 cells and the plotted range as for 2D.
  Answer key: fastest flow at 27.5 % / 42.3 % (x / y of the plotted range),
  lowest pressure at 31.0 % / 25.5 %.
- **`LLM_SLICE_Z=0.002`.** Not on mesh points, not moved; 20,540 cells, the
  centres at z = 0.00238125 m (second layer).
- **Refusals.** `LLM_SLICE_Z=abc`: solver warning "No plane slice for the
  observer: LLM_SLICE_Z is not a finite number: 'abc'", geometry line `slice
  none`; the request at step 2 ends with `callback_error` ("v2 pictures of a
  3D case need a plane slice: no plane slice: ..."). `LLM_SLICE_Z=1.0`: the
  plane cuts no cells, solver warning "The observer's plane slice z=1 cuts no
  cells; v2 pictures will be refused", `callback_error` ("... the plane z = 1
  m cuts no cells"). Both runs went on to the end (`runs` in
  frame-comparison.json, logs in `badz3d/`, `outz3d/`).
- **2D unchanged.** The bridge validation passes ([validation.log](validation.log)).
  The 2D frame at step 100 is identical, file for file (`U.png`, `p.png`,
  `fields.npz`, `readable-metadata.json`), to the serial frame of the
  2026-10-27 MPI test (job 24903786), and so is the request body.
- **Repeat.** Every frame file, request body and written file is identical
  between jobs 24929500 and 24929629: 68 of 68 files in `serial3d` and in
  `par3d`, 63 in `noobs3d`, 5 in `slicez3d` and `serial2d`; the two refused
  runs write none ([repeat-comparison.json](repeat-comparison.json), from
  [compare_runs.py](compare_runs.py)).

## The pictures

[U.png](serial3d/llm_observation/step-000100/U.png) and
[p.png](serial3d/llm_observation/step-000100/p.png): the serial slice frame at
step 100, plotted x 0 to 0.12 m and y 0 to 0.04 m behind the step.

Looked at by eye: they look right. Each cell is a flat patch of colour, as in
the 2D pictures. The picture shows the step flow seen in the 2D frame of the
same step: the shear layer leaves the step corner at about 32 % of the height
(the step is 0.0127 m of 0.04 m), fast flow above it with two bright spots
near x = 28 % and 60 %, slow recirculating flow below, and low-pressure cores
near x = 31 % and 60 %. Largest |U| in the window 37.24 m/s (2D 37.21). The
pressure colour bars differ: −281.6 to 90.9 m²/s² in the slice picture,
−335.0 to 43.9 in the 2D picture (`colour_range` in `serial3d/llm_result.json`
and `serial2d/llm_result.json`); over the whole slice p differs from the 2D
frame by up to 213 m²/s² (`slice_vs_2d_frame`). The 3D case has friction
walls front and back while the outlet pressure is fixed, which would raise
the pressure upstream; this test does not check that physics. The 2-rank pictures look the same,
and the slice at z = 0.002 m (step 5, not kept here) shows the same structure
at that earlier time. Neither the pictures nor the request say that they show
a slice; the frame metadata does.

## Not tested

- Only this mesh: hexahedra extruded in z, a plane normal to z. Polyhedral or
  tetrahedral meshes, non-convex cells, planes through points of an
  unstructured mesh and slices in other directions were not tried.
  `cuttingPlane` skips cells it cannot cut (a "Failed cuts" warning; none
  here); such cells would be white holes in the picture.
- No model was asked: nothing here says how well a model reads slice
  pictures.
- The 3D flow itself: 150 steps from a 2D state with walls added, not a
  validated 3D solution.
- Sequence mode and v1 pictures of a 3D case in the solver (sequence: unit
  test with synthetic geometry only; v1 keeps its raster, not run).
- Other OpenFOAM versions than v2212 (the code was not compiled for v2106 or
  openfoam.org; `PythonSlice.H` is included in every build, so a v2106
  compile failure would also hit 2D cases), more than 2 ranks, more than one
  node.
- Wedge meshes and single-layer meshes bounded by symmetry or cyclic patches,
  which have no `empty` patch and would be cut at mid z. On a graded or
  unstructured mesh the plane is moved halfway to the nearest point plane
  above once and not checked again.
- A `python_module.py` older than this branch: its `mesh_func` takes seven
  arguments and fails on the eighth, so such a 3D case gets no pictures (on
  `main` before this branch it got the v1 raster).
- A review on 2026-10-29 (jobs 24936879, 24936904 and 24936930) reran the
  comparisons (same results) and ran 2-rank cases where one rank cuts no
  cells (`LLM_SLICE_Z` 0.002 and 0.012 with a decomposition in z): correct
  frames. It also found that PODFoam stops at the second SVD ("Expected SVD
  shape") when fields are written more often than every 5 steps; this is on
  `main` already and does not concern the runs here (written every 50).

## Files

| Path | What it contains |
|---|---|
| `slice_test.sbatch`, `slice_test_inner.sh` | The job scripts as submitted (Slurm 24929629): build and validation, the 3D case, the seven runs, the comparison |
| `make_case3d.py` | Makes the 3D case: `blockMeshDict`, start fields, cell-map check |
| `compare_3d.py`, `frame-comparison.json` | The checks above and their results |
| `compare_runs.py`, `repeat-comparison.json` | Jobs 24929500 and 24929629 compared file by file |
| `case3d-check.json`, `case3d/` | Cell-map check; the 3D `blockMeshDict`, blockMesh and checkMesh logs |
| `slice-test-24929629.out`, `validation.log`, `HEAD`, `git-status.txt`, `changes.patch` | Job output, bridge validation log, code state seen by the job |
| `serial3d/` | Solver log (gzip), request and result records, and the frame's two pictures and metadata (`fields.npz` stays on the cluster) |
| `par3d/` | Solver log (gzip), result record, frame metadata, decomposition settings and logs |
| `noobs3d/`, `slicez3d/`, `badz3d/`, `outz3d/`, `serial2d/` | Solver logs (gzip); result records (none for `noobs3d`, which has no observer); frame metadata of `slicez3d` |
| `run-24929500/` | Output and comparison of the complete run with `07759b0` |
| `slice-test-24929484.out` | Output of the first attempt |
| [manifest.json](manifest.json) | Origins, sizes and hashes of the files here |

## Notes

- The job deleted the POD module's audit files (`python_svd_audit.npz`,
  about 200 MB per case). The records contain cluster paths and process ids
  as provenance.
- `git-status.txt` lists `llm_demo/README.md` as modified: its notes on 3D
  cases were written while the job ran and do not affect the runs.
- The POD module of the 2-rank case was patched in its copy only (its rank
  check, as in the 2026-10-27 MPI test; see `slice_test_inner.sh`).
- The first steps of the 3D runs are slow (PDE compute up to 38 s per step;
  the median over the 150 serial steps is 2.84 s), as the walls start acting;
  the result of the refused request at step 2 of `badz3d` and `outz3d` was
  therefore collected at step 3, 27.5 s later.
