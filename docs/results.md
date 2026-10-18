# PythonFOAM multimodal integration: October 17 tests

Executed code: **23089bbf3447731852fa960d7d25ea18767a3f51**

Live run: **pod-llm-demo.LRfJBN**, 2026-10-17

Model: **Gemma 4 E2B Q4_0**, image projector, local CPU inference

[Repository](../README.md) · [Illustrated results, Korean](https://seungminyome.github.io/PythonFOAM/results-20261017.html) · [Evidence index](evidence/2026-10-17/README.md) · [October 13 report](results-20261013.md)

## Live solver test

I tested the callback in serial OpenFOAM v2106 with 20,540 cells and ten 10⁻⁷ s
steps. After step 5 (5 × 10⁻⁷ s), it sent numbers and a velocity/pressure image
from that step to Gemma, saved the answer, and returned to the solver. The answer
is recorded without changing solver fields, settings or control.

| Condition | Model result | Completed steps | Files matching baseline | C++-measured Python analysis callback |
|---|---|---:|---:|---:|
| No model request | Disabled | 10 | Baseline | 0.493 s |
| Numerical summary + image | Response recorded | 10 | 45 / 45 | 78.256 s |
| Numerical summary only | Response recorded | 10 | 45 / 45 | 39.672 s |
| Connection refused | Error recorded | 10 | 45 / 45 | 0.509 s |
| Deliberately delayed response | Timeout recorded | 10 | 45 / 45 | 4.013 s |

Each comparison matched all 45 saved files byte for byte: U, p and phi across
ten steps, plus 15 final POD-mode fields.
The no-request baseline still prepares the observation and image.

The timer surrounds the Python analysis call; preceding C++ field-copy and
diagnostic preparation are excluded. Within the image callback, summary
preparation took 0.006 s, rendering 0.438 s and HTTP/client wait 77.560 s.

Records: [run verification](evidence/2026-10-17/pod-llm-demo.LRfJBN/demo-verification.json),
[field/source/process checks](evidence/2026-10-17/independent-integration-check.json),
[image response](evidence/2026-10-17/pod-llm-demo.LRfJBN/fixed-pod/llm_response.json),
[56 passing Python/loopback tests](evidence/2026-10-17/unit-tests-56.txt).

## Image/no-image comparison

Three pairs used the saved step-5 state, keeping the question, numbers and
settings fixed while adding or omitting the PNG. Temperature was zero;
order was A1, B1, B2, A2, A3, B3.

The reference location was cell 12090 at **(0.0005381681, 0.0127144842, 0.00635) m**,
calculated from saved fields and withheld from the model.
Both inputs supplied the maximum speed, **82.5275161154 m/s**.

| Condition | Claimed (x, y), m, in all three responses | Planar location error |
|---|---|---:|
| Numbers only | (0.6012246511, 0.1142952356) | 60.92 cm |
| Numbers + image | (0.5, 0.1142952356) | 50.97 cm |

All six structured replies gave wrong locations. Numbers-only replies reused
upper domain bounds; image replies were about 10 cm closer.
The position scorer measured the errors correctly; the separate grounding
heuristic flagged none. Review against the data found unsupported locations and
contradictions, including replies denying supplied Courant-number evidence.

Evidence: [paired settings](evidence/2026-10-17/ablation/manifest.json),
[metrics](evidence/2026-10-17/ablation/summary.json),
[response review](evidence/2026-10-17/independent-ablation-review.json),
[field arrays](evidence/2026-10-17/pod-llm-demo.LRfJBN/fixed-pod/llm_observation/fields.npz).

## Limitations

These tests cover one short serial fluid case and two failure conditions.
Numerical and physical stability, MPI, solid solvers, long runs and early failure
prediction need separate tests.

The solver waited about 78 seconds for the image call. Asynchronous operation is
still to be implemented. The two normal live calls used different instructions
and metadata. In the paired replay, each pair's inputs differed only by the PNG.

Accuracy needs checking across more states. The maximum speed was supplied in
both inputs, so the location question is the useful check here. October 13's
approximately 25 cm error measured x alone; the current distances include y.

Replay requests took 13–56 s, excluding summary/rendering. Cached prompt tokens
rose from one to over 1,400. The model was already loaded; hash checks may also
have warmed the filesystem cache. Timing needs consistent cache conditions.
The [runtime record](evidence/2026-10-17/runtime-summary.json) lists
llama.cpp b11429, four CPU threads, context 2048, one slot, image-token cap 256,
reasoning off, and matching model/projector hashes. Comparison with the larger
12B model remains future work.

Both inputs retain the example's [Singular Value Decomposition (SVD) summary](../Solver_Examples/PODFoam/llm_demo/README.md#earlier-run-on-this-machine--october-13).
It supplies singular values and their fractions; spatial modes are omitted.
I have not tested whether this summary helps the model.

I plan to test more states and models, improve the field inputs, and let the
solver continue during analysis. That needs fixed snapshots, bounded pending
requests and clean worker shutdown.

## Check the evidence

The [release](https://github.com/seungminyome/PythonFOAM/releases/tag/pod-insitu-tests-2026-10-17)
provides checksums, records and `solver-evidence-LRfJBN.tar.gz`: all ten
time directories for five cases, pimpleFoam reference and executed sources,
without model weights. Repository records have a
[hash manifest](evidence/2026-10-17/manifest.json).

After unpacking, recheck with NumPy:

```bash
python3 pod-llm-demo.LRfJBN/sources/llm_demo/verify_demo.py pod-llm-demo.LRfJBN
```

This launches neither solver nor model. The archive README explains other
checks. The demo's smaller `run-archive.tar.gz` omitted intermediate directories.
Raw requests, responses and metrics remain unchanged; the public runtime summary
is derived. Raw local paths and no-remote-write fields describe the test session.
Publication changes documentation and evidence; executed code remains `23089bb`.
