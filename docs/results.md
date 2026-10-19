# October 17 tests

Code `23089bb` · run `pod-llm-demo.LRfJBN` · Gemma 4 E2B Q4_0 with image projector, llama.cpp b11429 on CPU

[README](../README.md) · [Evidence](evidence/2026-10-17/README.md) · [October 13 run](results-20261013.md) · [Korean, illustrated](https://seungminyome.github.io/PythonFOAM-Korean/results-20261017.html)

## Five solver runs

Serial PODFoam on OpenFOAM v2106, 20,540 cells, ten steps of 1e-7 s. After
step 5 the callback sends that step's numbers and a |U|/p image to the model,
stores the reply and returns. Nothing in the reply goes back into the solver.

| Run | Model | Steps | Files equal to baseline | Callback time |
|---|---|---:|---:|---:|
| No request (baseline) | off | 10 | - | 0.493 s |
| Numbers + image | reply stored | 10 | 45 / 45 | 78.256 s |
| Numbers only | reply stored | 10 | 45 / 45 | 39.672 s |
| Connection refused | error stored | 10 | 45 / 45 | 0.509 s |
| Server made to stall (4 s deadline) | timeout stored | 10 | 45 / 45 | 4.013 s |

The 45 files are U, p and phi for each of the ten steps plus the 15 POD mode
fields written at the end. The baseline run still builds the summary and
renders the image, which is where its half second goes.

Callback time is measured in C++ around the Python call. Inside the image
callback: summary 0.006 s, rendering 0.438 s, waiting for the server 77.560 s.

Records: [demo-verification.json](evidence/2026-10-17/pod-llm-demo.LRfJBN/demo-verification.json),
[integration check](evidence/2026-10-17/independent-integration-check.json),
[reply to the image request](evidence/2026-10-17/pod-llm-demo.LRfJBN/fixed-pod/llm_response.json),
[unit test output](evidence/2026-10-17/unit-tests-56.txt).

## Same state, with and without the image

The two live requests above use different prompts, so they are not a fair
image/no-image comparison. For that, the step-5 state was saved and sent again
three times per condition with the question, numbers and settings identical and
only the PNG added or removed. Temperature 0, order A1 B1 B2 A2 A3 B3
(A = numbers only, B = numbers + image).

Both conditions were told the maximum speed, 82.5275 m/s, and asked where it
is. The true cell is 12090 at (0.000538, 0.012714, 0.00635) m. That location was
never sent.

| Condition | Answer (x, y) m, same in all three | Distance from the true cell |
|---|---|---:|
| Numbers only | (0.6012, 0.1143) | 60.92 cm |
| Numbers + image | (0.5, 0.1143) | 50.97 cm |

All six answers put the maximum in the wrong place. The numbers-only answers
took the domain's upper x and y bounds straight from the summary. With the image,
x moved to 0.5 m and y stayed at the bound, about 10 cm closer and still far
off. The automatic claim checker flagged nothing. Reading the answers against the
data turned up more: unsupported statements about location, and one reply that
said the Courant number was missing when it was in the input.

Records: [pair settings](evidence/2026-10-17/ablation/manifest.json),
[scores](evidence/2026-10-17/ablation/summary.json),
[answer review](evidence/2026-10-17/independent-ablation-review.json),
[field arrays](evidence/2026-10-17/pod-llm-demo.LRfJBN/fixed-pod/llm_observation/fields.npz).

## What this shows, and what it does not

Works: sending numbers and an image from inside the solver, getting a
structured reply, carrying on with identical results, and recovering from a
dead or stalled server within the deadline.

Not shown: that the model reads the picture usefully. One flow state, six
answers, all wrong on location. More states and a larger model are needed
before saying anything about accuracy.

Cost: the solver waits about 78 s for an image reply on this CPU. The replay
requests took 13–56 s, but cached prompt tokens went from 1 to over 1,400
between requests, so those times do not isolate the cost of the image.
Server settings are in [runtime-summary.json](evidence/2026-10-17/runtime-summary.json):
four threads, context 2048, one slot, image tokens capped at 256, reasoning off.

Both conditions also received the [SVD summary](../Solver_Examples/PODFoam/llm_demo/README.md#svd-summary)
(singular values only, no spatial modes). Whether it helps has not been tested.

The 25 cm error reported for October 13 was measured along x only; the
distances above include y. Do not compare the two.

Not covered at all: MPI, 3D cases, long runs, solid solvers, predicting
failures ahead of time.

Next: repeat the paired comparison on several states, let the solver keep
running while the model works (frozen snapshot, bounded queue, clean worker
shutdown), re-measure cost with the cache controlled, repeat the five
conditions and the paired replay with the 12B model on a machine with more
memory (this one has 7.7 GiB RAM and no GPU; the E2B server alone peaked at
2.2 GiB).

## Checking the evidence yourself

The [release](https://github.com/seungminyome/PythonFOAM/releases/tag/pod-insitu-tests-2026-10-17)
has `solver-evidence-LRfJBN.tar.gz` (all ten time directories for the five
runs, the pimpleFoam reference and the sources as executed, no weights) and
checksums. Files in this repository are listed with hashes in
[manifest.json](evidence/2026-10-17/manifest.json).

After unpacking:

```bash
python3 pod-llm-demo.LRfJBN/sources/llm_demo/verify_demo.py pod-llm-demo.LRfJBN
```

This reads the saved files only; it runs neither the solver nor the model.
