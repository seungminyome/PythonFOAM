# October 13 evidence: `pod-llm-demo.SwwR2e`

Solver revision `9ae54d0`, recorded 2026-10-13; read-only rechecks added
2026-10-15 (no new solver or model run). The newer run with the revised code
and the paired replay is under [2026-10-17](../2026-10-17/README.md).

[Report](../../results-20261013.md) · [Download the complete run](https://github.com/seungminyome/PythonFOAM/releases/download/pod-insitu-demo-2026-10-13/run-archive-SwwR2e.tar.gz)

| File | Contents |
|---|---|
| [summary.json](summary.json) | Results of the five cases and the two model answers |
| [image_request_record.json](image_request_record.json) | The `input` sent with the image: residuals, Courant numbers, SVD summary, image ranges |
| [image_request_body.json](image_request_body.json) | Exact HTTP body of the image request, PNG included as a data URL |
| [image_response.json](image_response.json) | Response to the image request (`api_response.choices[0].message.content`) |
| [image_http_body.raw](image_http_body.raw) | Raw HTTP response body |
| [text_request_body.json](text_request_body.json) | Numbers-only request; note that its instructions differ from the image request |
| [text_response.json](text_response.json) | Response to the numbers-only request |
| [demo-verification.json](demo-verification.json) | Step counts, 45-file comparison, timings |
| [verification_recheck_20261015.json](verification_recheck_20261015.json) | Read-only recheck of the stored run |
| [numeric_audit_20261015.json](numeric_audit_20261015.json) | Extrema locations and the SVD recomputed from the first five snapshots |
| [image_run_log.txt](image_run_log.txt) | Solver log: step 5, model answer, step 6, `End` |
| [telemetry.jsonl](telemetry.jsonl) | One line per step |
| [timings.json](timings.json) | Whole-run timings and resource records |
| [resident-server.json](resident-server.json) | Model name, CPU settings, projector loaded |
| [build-inputs.json](build-inputs.json) | OpenFOAM version, binary and source hashes |
| [source_HEAD.txt](source_HEAD.txt) | Git revision of the executed code |
| [image-metadata.json](image-metadata.json) | Step, fields and source arrays behind the image |
| [state.png](state.png) | The PNG sent, identical to the one in the request body |
| [fields.npz](fields.npz) | Cell centres, velocity and pressure of the 20,540 cells |
| [python_svd_audit.npz](python_svd_audit.npz) | Stored velocity snapshots; the first five reproduce the SVD summary sent |
| [python_module.py](python_module.py), [pod_svd.py](pod_svd.py), [pod_image.py](pod_image.py), [llm_client.py](llm_client.py), [bounded_ipc.py](bounded_ipc.py) | Python sources as executed |
| [errorresult.json](errorresult.json) | Connection-refused case |
| [timeoutresult.json](timeoutresult.json) | Timeout case |
| [derived_cells_step5.csv](derived_cells_step5.csv) | `fields.npz` exported as a table (derived) |
| [verify_demo.py](verify_demo.py) | Verifier as executed; does not call the model |

[manifest.json](manifest.json) records original paths, sizes and SHA-256
hashes. Files are byte-preserved copies unless marked as a recheck or derived
export. The release archive holds all five case directories with their fields;
model weights are not included.
