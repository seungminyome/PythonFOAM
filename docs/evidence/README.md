# Saved evidence: SwwR2e

This directory preserves the **October 13** evidence. The [October 17 evidence](2026-10-17/README.md) and [latest test report](../results.md) cover the newer executed code and paired model comparison.

The source run was recorded on 2026-10-13. Documentation and read-only rechecks were prepared on 2026-10-15; no new CFD or model inference is represented by these rechecks.

[Run report](../results.md) · [Interactive reader](https://seungminyome.github.io/PythonFOAM/guide.ko.html#raw-library) · [Download all original run files](https://github.com/seungminyome/PythonFOAM/releases/download/pod-insitu-demo-2026-10-13/run-archive-SwwR2e.tar.gz)

| File | Contents |
|---|---|
| [summary.json](summary.json) | 다섯 시험의 결과와 AI의 실제 답을 함께 확인해요. |
| [image_request_record.json](image_request_record.json) | input 안에 잔차·Courant 수·SVD·그림의 숫자 정보가 있어요. |
| [image_request_body.json](image_request_body.json) | 그림을 문자로 바꾼 데이터까지 생략 없이 들어 있어요. |
| [image_response.json](image_response.json) | api_response → choices → message → content에서 AI의 답을 찾아요. |
| [image_http_body.raw](image_http_body.raw) | HTTP의 머리말이 아니라, 실제 받은 응답 본문을 저장한 파일이에요. |
| [text_request_body.json](text_request_body.json) | 그림을 보낸 경우와 지시문·추가 정보가 다르다는 것도 확인할 수 있어요. |
| [text_response.json](text_response.json) | 잔차·Courant 수·SVD에 대한 답이 들어 있어요. |
| [demo-verification.json](demo-verification.json) | 단계 수, 파일 45개 일치, 걸린 시간을 확인해요. |
| [verification_recheck_20261015.json](verification_recheck_20261015.json) | 새 유체 계산이나 AI 실행 없이, 저장된 증거를 다시 검사한 결과예요. |
| [numeric_audit_20261015.json](numeric_audit_20261015.json) | 저장된 숫자에서 가장 빠른 위치와 첫 다섯 시점의 SVD를 다시 구했어요. |
| [image_run_log.txt](image_run_log.txt) | 5단계 → AI 답 → 6단계 → End가 차례로 있는지 확인해요. |
| [telemetry.jsonl](telemetry.jsonl) | JSONL 형식이에요. 한 줄이 한 단계에 해당해요. |
| [timings.json](timings.json) | 전체 실행 시간이에요. 본문의 AI 호출 시간과 구분해서 읽어요. |
| [resident-server.json](resident-server.json) | 모델 이름, CPU 설정, 그림 변환 모델을 불러온 기록이에요. |
| [build-inputs.json](build-inputs.json) | OpenFOAM 버전과 실행 파일·코드가 무엇이었는지 확인해요. |
| [source_HEAD.txt](source_HEAD.txt) | Git에 저장한 코드 버전을 구분하는 번호예요. |
| [image-metadata.json](image-metadata.json) | 그림이 어느 단계의 자료인지, 어떤 값을 보여주는지 확인해요. |
| [state.png](state.png) | 보낸 요청 본문 속 그림과 파일 내용이 같은 PNG 원본이에요. |
| [fields.npz](fields.npz) | 20,540개 칸의 위치·속도 3방향·압력을 담은 NPZ 파일이에요. |
| [python_svd_audit.npz](python_svd_audit.npz) | 첫 5시점만 뽑으면 AI에게 보낸 SVD 요약을 다시 계산할 수 있어요. |
| [python_module.py](python_module.py) | 실행 당시 저장한 python_module.py예요. |
| [pod_svd.py](pod_svd.py) | 실행 당시 저장한 pod_svd.py예요. |
| [pod_image.py](pod_image.py) | 실행 당시 저장한 pod_image.py예요. |
| [llm_client.py](llm_client.py) | 실행 당시 저장한 llm_client.py예요. |
| [bounded_ipc.py](bounded_ipc.py) | 실행 당시 저장한 bounded_ipc.py예요. |
| [errorresult.json](errorresult.json) | 연결하지 못한 일을 기록한 뒤 계산으로 돌아왔어요. |
| [timeoutresult.json](timeoutresult.json) | 기다릴 시간을 넘겼을 때 계산으로 돌아왔어요. |
| [derived_cells_step5.csv](derived_cells_step5.csv) | 숫자 원본에서 이번에 만든 CSV예요. 원본과 구분한 변환 자료예요. |
| [verify_demo.py](verify_demo.py) | 저장된 파일을 대조하는 코드예요. AI를 새로 실행하지 않아요. |

[manifest.json](manifest.json) records original paths, sizes and SHA-256 hashes. The files are byte-preserved copies unless identified as a recheck or derived export.

`derived_cells_step5.csv` is a table exported from `fields.npz`. `numeric_audit_20261015.json` contains the extrema and the SVD recomputed from the first five stored snapshots. `verification_recheck_20261015.json` is a fresh read-only check of the saved run. The source `.npz`, request, response and log files are unchanged.

The complete run archive in the release includes all five case directories and their fields. The smaller evidence ZIP is a selection, not a replacement for the complete run. Model weights are not included.

## Reading the files

JSON, JSONL, RAW and the solver log are text. NPZ stores NumPy arrays; use the CSV for a spreadsheet view. The interactive guide can display and download the selected originals without relying on neighboring files. An HTML preview in the GitHub file viewer shows source code; open the published reader or download the HTML instead.
