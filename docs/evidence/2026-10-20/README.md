# October 20 evidence

Records behind the [October 20 report](../../results-20261020.md). Code
`9449085` (solver code and callback changed since `23089bb`: asynchronous
path, describe and sequence modes, plot window, `end_time_s` in the state).

## Folders

| Folder | What it holds |
|---|---|
| [pod-llm-async.pp7agC/](pod-llm-async.pp7agC/) | Five asynchronous cases on a 3000-step run, whole-domain images: verification, timings, settings, per-case request, reply, result, timeline, compressed solver log and telemetry; the frames the baseline, describe and sequence cases rendered (PNG, arrays, metadata); the callback sources as executed |
| [pod-llm-async.8YC6bG/](pod-llm-async.8YC6bG/) | Frames rendered with the plot window x = -0.05 to 0.15 m (no model request), steps 250, 1250, 2750 |
| [replay/describe-full/](replay/describe-full/) | Describe requests on the whole-domain frames of steps 250, 750, 1250, three repeats each |
| [replay/describe-window/](replay/describe-window/) | Describe requests on the windowed frames of steps 250, 1250, 2750, three repeats each |
| [replay/sequence-full/](replay/sequence-full/) | Three sequence requests with the whole-domain frames 250, 750, 1250 |
| [replay/sequence-window/](replay/sequence-window/) | Three sequence requests with the windowed frames 250, 1250, 2750 |
| [unit-tests-70.txt](unit-tests-70.txt) | Output of the 70 unit tests |

Each replay folder has `manifest.json` (frames, schedule, prompts' hashes),
`ground_truth.private.json` (reference positions and trends from the arrays,
never sent to the model), one `*.request.json` per request, and per request a
folder with the body sent, the raw and parsed reply, the result and the
scores; `summary.json` aggregates them.

## Files

`log.PODFoam.gz` and `telemetry.jsonl.gz` are gzip copies of the solver log
and the per-step telemetry (3000 lines); `timeline.json` keeps the model and
callback lines with wall-clock stamps. Everything else is the recorded bytes.
[manifest.json](manifest.json) lists every file with its size and SHA-256;
`python3 docs/evidence/check_manifest.py docs/evidence/2026-10-20` checks them.

The complete solver outputs (every written time directory of the five cases)
are a release asset, not in the repository: [pod-insitu-async-2026-10-20](https://github.com/seungminyome/PythonFOAM/releases/tag/pod-insitu-async-2026-10-20) (`solver-evidence-pp7agC.tar.gz`, about 600 MB, with `SHA256SUMS.txt`).

Some records contain paths from the test machine; the published locations
are the ones in this folder.
