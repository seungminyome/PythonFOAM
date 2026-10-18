# PythonFOAM multimodal integration: October 17 tests

Executed code: **23089bbf3447731852fa960d7d25ea18767a3f51**

Live run: **pod-llm-demo.LRfJBN**, 2026-10-17

Model: **Gemma 4 E2B Q4_0**, with its image projector, local CPU inference

[Repository](../README.md) · [Illustrated results, Korean](https://seungminyome.github.io/PythonFOAM/results-20261017.html) · [Evidence index](evidence/2026-10-17/README.md) · [Earlier October 13 report](results-20261013.md)

## Result

The prototype delivers a running OpenFOAM solver's numerical diagnostics and
same-step field image to a local multimodal model, saves the model's observations,
and returns to the calculation. The five tested conditions all completed ten
steps. Each of the four comparison cases produced 45 field files byte-identical
to the no-request baseline, including connection-refusal and timeout cases.

The model's spatial interpretation remains unreliable. A controlled replay of
one snapshot returned incorrect maximum-speed coordinates in all six responses.
The live image callback took 78.256 seconds and blocked the solver while waiting.
Concurrent solver/inference execution has not been implemented or tested.

These results establish a tested integration prototype and identify accuracy and
latency limits. They do not establish a generally reliable engineering analyst,
failure predictor, or controller.

## Live solver integration

The test used serial OpenFOAM v2106, a 20,540-cell PODFoam fluid case, and ten time
steps of 10⁻⁷ seconds. The observation was requested after step 5, at 5 × 10⁻⁷
seconds of simulation time. This short initial-transient case tests the
connection; it is not a validated long-duration flow study.

```text
Complete step 5 → copy fields and diagnostics → render image
→ request and record model response → continue steps 6–10
```

The model's answer changes no solver fields, settings, time step or control
algorithm. The worker runs separately, but the calling solver waits for its
completion or timeout. This is synchronous observation.

| Condition | Model result | Completed steps | Files matching baseline | Full C++ callback |
|---|---|---:|---:|---:|
| No model request | Disabled | 10 | Baseline | 0.493 s |
| Numerical summary + image | Actual response | 10 | 45 / 45 | 78.256 s |
| Numerical summary only | Actual response | 10 | 45 / 45 | 39.672 s |
| Connection refused | Error recorded | 10 | 45 / 45 | 0.509 s |
| Deliberately delayed response | Timeout recorded | 10 | 45 / 45 | 4.013 s |

The 45 files are U, p and phi at all ten steps, plus 15 POD-mode fields at the
final step. They are not 45 independent physical experiments. File equality
establishes preserved saved outputs for these runs, not general numerical or
physical stability. The no-request case still prepares the observation and image.

The verifier checked step chronology, telemetry against solver logs, field/image
provenance, request bytes, callback deadlines and the saved-field comparisons.
Independent checks compared executed callback and C++ source hashes with the
tested commit and confirmed that recorded worker processes had exited. The error
fixtures cover the tested conditions, not every possible operating-system failure.

The two normal live calls use different demo instructions and numerical metadata.
Their answers and timings do not isolate the effect of adding an image. The
controlled comparison below addresses that separately.

Sources: [live verifier](evidence/2026-10-17/pod-llm-demo.LRfJBN/demo-verification.json),
[independent field/source check](evidence/2026-10-17/independent-integration-check.json),
[live image response](evidence/2026-10-17/pod-llm-demo.LRfJBN/fixed-pod/llm_response.json).

## Controlled image comparison

The replay runner used the saved step-5 state for three paired trials. The
question, numerical summary, model and generation settings were fixed within
each pair; only PNG inclusion changed. The execution order was A1, B1, B2, A2,
A3, B3. Temperature was zero. These are repetitions of one snapshot, not six
different flow states.

The ground-truth location was computed directly from the saved cell arrays and
withheld from the model: cell 12090, with center
**(0.0005381681, 0.0127144842, 0.00635) m**. The maximum-speed value,
**82.5275161154 m/s**, was already supplied in both inputs, so quoting it correctly
is not a visual score.

| Condition | Claimed (x, y), m, in all three responses | Planar location error |
|---|---|---:|
| Numbers only | (0.6012246511, 0.1142952356) | 60.92 cm |
| Numbers + image | (0.5, 0.1142952356) | 50.97 cm |

The numeric-only response reused the supplied upper domain bounds as the maximum
location. The image responses also gave an incorrect location. The image answer
was about 10 cm closer on this one snapshot, but neither condition demonstrated
accurate localization. The earlier October 13 error of about 25 cm was x-only;
it must not be compared directly with these x-y planar distances.

All six replies were valid structured responses. The position scorer correctly
measured their errors. The separate heuristic grounding rules flagged none of
them, while independent review identified the incorrect location claims and
additional unsupported or contradictory statements. Some replies denied the
presence of Courant-number evidence even though those values were provided.
Automatic review flags therefore cannot substitute for checking the actual data.

Sources: [paired settings and schedule](evidence/2026-10-17/ablation/manifest.json),
[original metrics](evidence/2026-10-17/ablation/summary.json),
[independent response review](evidence/2026-10-17/independent-ablation-review.json),
[field arrays](evidence/2026-10-17/pod-llm-demo.LRfJBN/fixed-pod/llm_observation/fields.npz).

## Timing and runtime

The actual server used llama.cpp b11429, four CPU threads, context length 2048,
one inference slot, image-token cap 256 and reasoning disabled. The E2B model is
different from the larger 12B example; this test establishes no model ranking.
Model and projector hashes matched the pinned files. See the
[public runtime summary](evidence/2026-10-17/runtime-summary.json).

For the live image callback, summary preparation took 0.006 s, image rendering
0.438 s and HTTP/client wait 77.560 s. The full C++ callback measurement was
78.256 s, including the surrounding work. Server wait is not a pure measure of
image interpretation or of network transport alone.

The controlled replay takes already prepared data, so it excludes live summary
and rendering work. Measured request times varied from roughly 13 to 56 seconds.
The first replay reused one prompt token, while subsequent requests reused more
than 1,400. The model was already resident, and file-hash checks may also have
warmed the filesystem cache. These timings cannot support a speed advantage for
the image condition.

## Input scope and remaining work

The numerical input includes time, residuals, Courant and continuity values,
field ranges and domain extents. A legacy velocity SVD (Singular Value
Decomposition) summary remains in both conditions. It is a supplementary input,
not the research objective, and its contribution was not tested. Its leading
squared-singular-value fraction describes the supplied snapshot matrix; it is
not AI accuracy or physical stability. Spatial modes are not sent to the model.

Next work is to test useful observations across more states, improve the
presentation of field information, and evaluate other models on the same data.
Reducing solver blocking requires a separately tested asynchronous path with
fixed snapshots, bounded outstanding requests and an explicit shutdown policy.
No asynchronous performance result is claimed here.

MPI execution, other solver families, long runs, larger models and early failure
prediction remain outside the demonstrated scope. The saved
[56-test Python/loopback record](evidence/2026-10-17/unit-tests-56.txt) covers
callback/client failure paths and replay validation; the live solver tests above
provide the separate integration evidence.

## Download and check the saved evidence

The [release](https://github.com/seungminyome/PythonFOAM/releases/tag/pod-insitu-tests-2026-10-17)
contains a selected evidence ZIP and a solver archive with all ten time directories
for all five cases, the materialized pimpleFoam reference, and executed sources.
No model weights are included. The selected repository records have a
[hash manifest](evidence/2026-10-17/manifest.json); the release has download checksums.

After unpacking `solver-evidence-LRfJBN.tar.gz`, use the executed verifier:

```bash
python3 pod-llm-demo.LRfJBN/sources/llm_demo/verify_demo.py pod-llm-demo.LRfJBN
```

This reads saved records and needs NumPy; it runs neither the solver nor the model.
The archive's README describes the additional reference and file checks. The
original small `run-archive.tar.gz` generated by the demo omitted intermediate
time directories and is not the full archive published in this release.

The original request, response and metric files are unchanged. Runtime metadata
in the public summary is explicitly derived. Historical local paths and
no-remote-write fields in raw records describe the testing session, not the
subsequent publication. New publication commits change documentation and attach
evidence; the executed code remains identified by `23089bb`.
