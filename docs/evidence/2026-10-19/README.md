# October 19 evidence

Repeat of the October 17 tests on the same machine, against the same resident
llama-server, two days later. Solver run `pod-llm-demo.o5sNLJ`, documentation
commit `4187659`; the solver code is byte-identical to `23089bb`.

## Files

Same selection as [2026-10-17](../2026-10-17/README.md): the five-case
verification, the step-5 request, reply, image and arrays, and the three
paired replays under [ablation/](ablation/). [manifest.json](manifest.json)
lists every file with its hash; [unit-tests-56.txt](unit-tests-56.txt) is one
of the five passing test invocations.

## What matched October 17

- `fields.npz` and `state.png` at step 5 have the same SHA-256 as on October 17
  (`14b64e39…`, `05a876ff…`).
- All five cases completed ten steps with 45 files identical to the baseline;
  `demo-verification.json` says `PASS`.
- The reply to the image request from inside the solver is the same text as on
  October 17. The six replay answers are the same as on October 17
  (numbers only: x = 0.6012 m, y = 0.1143 m; with image: x = 0.5 m,
  y = 0.1143 m), so the position errors are again 60.92 cm and 50.97 cm.

## What differed

| | 2026-10-17 | 2026-10-19 |
|---|---:|---:|
| Callback, no request | 0.493 s | 0.517 s |
| Callback, image | 78.256 s | 72.256 s |
| Callback, numbers only | 39.672 s | 40.587 s |
| Callback, server error | 0.509 s | 0.813 s |
| Callback, timeout | 4.013 s | 4.026 s |
| Replay latency | 13–56 s | 13–56 s |

Both solver requests on October 19 started from a cold prompt cache
(`cache_n` 1), so the prompt-processing time of the image request
(58.6 s for 1541 tokens) and of the numbers-only request (30.2 s for 1080
tokens) are comparable on this date. The replay requests again reused
1457–1568 cached tokens after the first.

## Notes

The server process is the one started on October 11 (PID 4177294, eight days
of uptime). One of six `make test` invocations on this date failed before its
output was captured; the five recorded invocations passed 56/56.
