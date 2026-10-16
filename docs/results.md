# PODFoam–Gemma observation demo

Recorded run: **2026-10-13**, `pod-llm-demo.SwwR2e`
Evidence rechecked: **2026-10-15**
Solver source revision: `9ae54d0440bff8cbd0e65a5fc9f5ab7e06c3b2ee`

[Repository](../README.md) · [Illustrated explanation, Korean](https://seungminyome.github.io/PythonFOAM/guide.ko.html) · [Evidence index](evidence/README.md)

## Purpose and scope

The prototype reads a running OpenFOAM solver's state through PythonFOAM and asks a local multimodal model for an observation. The model response is stored for the user; it is not used to change fields, time steps or solver settings.

The test used a serial PODFoam fluid case with 20,540 cells and ten time steps of 10⁻⁷ s. The observation was requested after step 5, at t = 5 × 10⁻⁷ s. The run continued through step 10. This is a short initial-transient connection test, not a validated long-duration flow study.

## Data path

```text
PODFoam: complete step 5
    |
    +-- velocity snapshots, pressure, mesh geometry and numerical diagnostics
    |
Python callback: summarize values and render the same-step field image
    |
Local llama.cpp server: Gemma 4 E2B Q4_0 with its image projector
    |
Record request, response and timing
    |
PODFoam: continue steps 6–10
```

The solver waits synchronously while the callback prepares the input, requests a response and records the result. Worker isolation bounds the tested wait; it does not make the solver advance concurrently with inference.

The input included the step/time, cell count, normalized linear-solver residuals, Courant and continuity diagnostics, a componentwise velocity SVD summary, and a 640×360 PNG. The image showed velocity magnitude above kinematic pressure. It used the same step's cell values and cell polygons, with no interpolation between cell colors. The long, thin domain was stretched vertically for display.

The request also supplied field ranges and domain extents. In particular, the maximum-speed value was present in the numerical input. A correct quotation of that value does not establish that the model inferred it from the image.

Sources: [input record](evidence/image_request_record.json), [exact request body](evidence/image_request_body.json), [image metadata](evidence/image-metadata.json), [actual image](evidence/state.png).

## What was checked

The saved verifier compares telemetry with the solver log, checks step/time consistency, compares the image arrays with the written fields, verifies that the exact request contains the recorded PNG, and checks that the solver returns from the observation before step 6. It also compares the written field files with the no-request baseline and checks callback timing against the configured limit plus cleanup allowance.

| Case | Model result | Completed steps | Files matching baseline | C++-measured full callback |
|---|---|---:|---:|---:|
| No request | Disabled | 10 | Baseline | 0.754688 s |
| Numeric summary + image | Actual response | 10 | 45 / 45 | 70.604411 s |
| Numeric summary only | Actual response | 10 | 45 / 45 | 41.412413 s |
| Connection refused | Error recorded | 10 | 45 / 45 | 0.411067 s |
| Delayed-response fixture | Timeout recorded | 10 | 45 / 45 | 4.016922 s |

The 45 compared files are the ten steps' U, p and phi files plus 15 POD-mode files at the final step. They are file comparisons, not 45 independent physical experiments. The no-request case still performs observation preparation and renders an image, so it is not a measurement with all observation overhead removed.

The ordinary worker deadline was 120 s. The refusal and delayed-response tests used 4 s, with a 4.27 s acceptance limit including cleanup and scheduling allowances. These tests cover the recorded conditions, not all operating-system stalls or failure modes. A previous timeout failure in a separate solid-unloading path is not resolved by this POD result.

Sources: [original verification](evidence/demo-verification.json), [read-only recheck](evidence/verification_recheck_20261015.json), [solver log](evidence/image_run_log.txt), [verifier](evidence/verify_demo.py).

## Model response and field comparison

The image response stated:

> The velocity magnitude |U| shows a high value near x=0.25 m, with a maximum of 82.5 m/s.

It described a localized high-speed region in the central x-domain and asserted a significant pressure gradient near that region.

A direct check of the saved field arrays gives:

| Quantity | Result |
|---|---|
| Maximum velocity magnitude | 82.5275161154 m/s |
| Maximum-speed cell, zero-based index | 12090 |
| Its center | x = 0.0005381681 m, y = 0.0127144842 m |
| Minimum kinematic pressure | −9362.82606697 m²/s² |
| Minimum-pressure cell, zero-based index | 10409 |
| Its center | x = 0.0005390477 m, y = 0.0126848045 m |
| Difference between x = 0.25 m and the actual maximum-speed x | 0.2494618319 m |

The extrema are in nearby **different cells**. Their proximity does not quantify the pressure gradient. The maximum-speed cell is approximately 72% across the plotted x-range, rather than at its center. The response therefore provides no evidence of accurate localization.

The numeric-only response correctly quoted the supplied pressure residual and Courant mean and noted the high leading SVD fractions. It also asked to check whether residuals are force balance and whether the SVD was centered, although both points were already specified in the input. Quoting supplied values correctly is distinct from providing useful interpretation.

Sources: [image response](evidence/image_response.json), [numeric-only response](evidence/text_response.json), [extrema/SVD recheck](evidence/numeric_audit_20261015.json), [original arrays](evidence/fields.npz), [derived CSV](evidence/derived_cells_step5.csv).

## SVD interpretation

SVD means **Singular Value Decomposition**. POD means **Proper Orthogonal Decomposition**. In this demo, SVD is used to summarize stored velocity snapshots; the model is not trained by this operation.

The summary sent to the model uses the first five snapshots, separately for Ux, Uy and Uz. Each component matrix has 20,540 rows and five columns. No temporal mean is subtracted, and this summary does not use cell-volume or density weighting.

| Component | Leading squared-singular-value fraction, recomputed |
|---|---:|
| Ux | 0.999969763560 |
| Uy | 0.999912946318 |
| Uz | 0.999995496959 |

The fraction is σ₁² / Σᵢσᵢ². It describes the share of the snapshot matrix's squared norm carried by the leading mode. It is not model accuracy, a stability proof or a measured fraction of physical kinetic energy. Mean flow can dominate an uncentered decomposition. The Uz singular values are themselves close to zero, so a high ratio does not imply important out-of-plane motion.

The original POD calculation separately collects ten snapshots and writes five modes per component. The model request at step 5 does not use future snapshots from steps 6–10.

Sources: [summary callback](evidence/python_module.py), [POD routine](evidence/pod_svd.py), [saved snapshots](evidence/python_svd_audit.npz), [numerical recheck](evidence/numeric_audit_20261015.json).

## Runtime and resource cost

The saved runtime used OpenFOAM v2106, Python 3.10, a CPU-only llama.cpp b11429 server, four model threads and a context size of 2048. The recorded model identifier is `gemma-4-E2B-it-Q4_0-vision`; it is not the 12B variant.

| Measurement | Numeric + image | Numeric only |
|---|---:|---:|
| Full callback, measured in C++ | 70.604 s | 41.412 s |
| HTTP request duration | 70.149 s | 41.371 s |
| Whole solver process wall time | 72.689 s | 43.574 s |

The no-request process took 4.115 s. Image rendering inside the callback took about 0.419 s. The HTTP time includes more than image interpretation, and differences between cases are not an isolated measure of image cost.

During the image case, recorded peak server RSS was 2,336,328 KiB (about 2.23 GiB), and recorded peak server PSS was 2,331,095 KiB (about 2.22 GiB). The CFD/Python processes' recorded peak summed RSS was 241,584 KiB (about 236 MiB). Independently measured maxima should not be added and reported as a simultaneous system peak. The model was already loaded for these comparisons; startup cost is outside these measurements.

Sources: [timing/resource records](evidence/timings.json), [runtime settings](evidence/resident-server.json).

## Limits and next evaluation

The image and numeric-only requests differ in their system instructions and additional numerical metadata. Their different answers therefore do not establish the benefit of the image alone.

The next comparison should hold the model, prompt, numerical information and settings fixed while varying image inclusion. Across multiple states and repetitions, useful measures include localization error, unsupported claims, appropriate handling of missing information, user task accuracy, and runtime cost. The maximum value should not count as evidence of image understanding when it has already been supplied numerically.

MPI execution, a real 3D-case image fallback, other solver families, larger models, long runs, engineering analysis quality and early failure prediction remain outside the demonstrated scope.

## Evidence and reuse

The [release](https://github.com/seungminyome/PythonFOAM/releases/tag/pod-insitu-demo-2026-10-13) contains the complete recorded run archive, a smaller evidence bundle and offline Korean guides. The [manifest](evidence/manifest.json) records the origins, sizes and SHA-256 hashes of selected files. Derived exports and read-only rechecks are labeled separately from execution-time records.

The source revision above identifies the executed solver. Subsequent documentation changes correct interpretation and publish the evidence; they do not represent a new solver or inference run.
