#!/usr/bin/env python3
"""Recount the 2026-10-30 wrong-setup test from the recorded answers, the answer key and the gzipped
solver logs, without wrong_setup_test.py or picture_test.py, and compare with the report.

Run in this folder:  python3 recount.py   (standard library only; writes recount.json)

Inputs: test-set/truth.private.json (class, run, step and numbers of each frame),
test-set/manifest.json (the runs and their log numbers), test-set/leak-check.json,
test-set/request-text-example.json, results/<job>/<model>/wrong-setup-v2own/metrics.jsonl (one
parsed answer per request), flow/logs/<run>.log.gz and reports/combined.md.

It recounts, per model: answered, right, the six answer cells, right by run and the mark of every
frame; the rule on the peak |U| from the key's numbers; each number's range over the normal frames
or logs and which wrong runs fall outside. It reads every log again: 8,000 steps, an End line, no
floating point exception, and the Courant numbers, residuals and continuity errors stored in the
key and the manifest. It checks the labels, that each step and time has 5 normal and 5 wrong
frames, and the leak check's text hashes. Every recomputed table line is looked up in the report.
Beyond the report: whether each model answers alike for the pairs of normal frames that show one
flow time (flow/normal-overlap.json), the answers by step, and how often a model's answers change
within a run.
"""
import gzip
import hashlib
import json
from pathlib import Path
import re
import statistics

HERE = Path(__file__).resolve().parent
SET = "wrong-setup-v2own"
RIGHT = {"normal": "consistent", "wrong": "inconsistent"}
MARK = {"consistent": "c", "inconsistent": "i", "cannot_tell": "?", None: "-"}
INLET = 32.2
FRAME_NUMBERS = (("courant_max", "largest Courant number"), ("courant_mean", "mean Courant number"),
                 ("Ux_initial", "Ux initial residual"), ("Uy_initial", "Uy initial residual"),
                 ("p_initial", "p initial residual, first solve"),
                 ("Ux_final", "Ux final residual"), ("Uy_final", "Uy final residual"),
                 ("p_final", "p final residual, last solve"),
                 ("continuity_local", "continuity error, sum local"),
                 ("continuity_global_abs", "continuity error, global (absolute)"),
                 ("continuity_cumulative_abs", "continuity error, cumulative (absolute)"),
                 ("max_speed_m_per_s", "peak \\|U\\| in the window (m/s)"),
                 ("min_pressure_m2_per_s2", "lowest p in the window (m^2/s^2)"))
LOG_NUMBERS = (("courant_max_whole_run", "largest Courant number, whole run"),
               ("courant_max_from_first_frame", "largest Courant number, from the first frame on"),
               ("courant_mean_from_first_frame", "mean Courant number, from the first frame on"),
               ("last_Ux_initial", "Ux initial residual, last step"),
               ("last_Uy_initial", "Uy initial residual, last step"),
               ("last_p_initial", "p initial residual, first solve of the last step"),
               ("last_Ux_final", "Ux final residual, last step"),
               ("last_Uy_final", "Uy final residual, last step"),
               ("last_p_final", "p final residual, last solve of the last step"),
               ("last_continuity_local", "continuity error, sum local, last step"),
               ("last_continuity_global_abs", "continuity error, global (absolute), last step"),
               ("last_continuity_cumulative_abs", "continuity error, cumulative (absolute), last step"))


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def g(value):
    return f"{value:.4g}"


def span(low, high):
    return g(low) if g(low) == g(high) else f"{g(low)} to {g(high)}"


def read_log(path):
    """Per step: Courant numbers before the step, first initial and last final residual per field,
    last continuity errors. And the end of the log."""
    steps, courant, ended, crashed = [], None, False, False
    with gzip.open(path, "rt", errors="replace") as stream:
        for line in stream:
            if line.startswith("Courant Number mean:"):
                fields = line.split()
                courant = (float(fields[3]), float(fields[5]))
            elif line.startswith("Time = "):
                steps.append({"time": line.split("=")[1].strip(), "courant_mean": courant[0], "courant_max": courant[1]})
            elif "Solving for" in line and steps:
                match = re.search(r"Solving for (\w+), Initial residual = ([^,]+), Final residual = ([^,]+),", line)
                steps[-1].setdefault(match.group(1) + "_initial", float(match.group(2)))
                steps[-1][match.group(1) + "_final"] = float(match.group(3))
            elif line.startswith("time step continuity errors") and steps:
                numbers = re.findall(r"= ([^,\s]+)", line)
                steps[-1]["continuity_local"] = float(numbers[0])
                steps[-1]["continuity_global_abs"] = abs(float(numbers[1]))
                steps[-1]["continuity_cumulative_abs"] = abs(float(numbers[2]))
            elif line.strip() == "End":
                ended = True
            elif "sigFpe::sigHandler" in line:
                crashed = True
    return steps, ended, crashed


def main():
    truth = json.loads((HERE / "test-set" / "truth.private.json").read_text())
    manifest = json.loads((HERE / "test-set" / "manifest.json").read_text())
    leak = json.loads((HERE / "test-set" / "leak-check.json").read_text())
    keys = {name.split("/", 1)[1]: key for name, key in truth.items()}
    report = set((HERE / "reports" / "combined.md").read_text().splitlines())
    problems, checked = [], 0

    def look(line):
        nonlocal checked
        checked += 1
        if line not in report:
            problems.append(f"not in the report: {line}")

    # the key
    runs = manifest["runs"]
    names = [r["name"] for r in runs]
    wrong_runs = [r["name"] for r in runs if r["class"] == "wrong"]
    steps_wanted = list(range(4500, 8001, 500))
    for run in runs:
        frames = sorted(k["run_step"] for k in keys.values() if k["run"] == run["name"])
        if frames != steps_wanted:
            problems.append(f"{run['name']}: frames at {frames}")
    for name, key in keys.items():
        if key["assessment"] != RIGHT[key["class"]]:
            problems.append(f"{name}: label does not follow the class")
        if abs(key["time_s"] - (0.1 + key["run_step"] * 5e-6)) > 1e-9:
            problems.append(f"{name}: time {key['time_s']}")
    # the leak check, from its stored hashes and the key's classes
    groups = {}
    for name, digest in leak["text_sha256_by_request"].items():
        groups.setdefault(digest, []).append(keys[name]["class"])
    balance = sorted((g2.count("normal"), g2.count("wrong")) for g2 in groups.values())
    if balance != [(5, 5)] * 8:
        problems.append(f"text groups: {balance}")
    example = (HERE / "test-set" / "request-text-example.json").read_bytes()
    if hashlib.sha256(example).hexdigest() != leak["text_sha256_by_request"]["N1-step04500"]:
        problems.append("the example text does not have the hash the leak check lists")
    # the logs
    log_numbers = {}
    for run in runs:
        steps, ended, crashed = read_log(HERE / "flow" / "logs" / f"{run['name']}.log.gz")
        log_numbers[run["name"]] = {"steps": len(steps), "ended": ended, "crashed": crashed}
        if len(steps) != 8000 or not ended or crashed:
            problems.append(f"{run['name']}: {len(steps)} steps, End {ended}, crash {crashed}")
        for name, key in keys.items():
            if key["run"] == run["name"]:
                block = steps[key["run_step"] - 1]
                for number, _ in FRAME_NUMBERS[:11]:
                    if block[number] != key["numeric"][number]:
                        problems.append(f"{name}: {number} {block[number]} in the log, {key['numeric'][number]} in the key")
        late = steps[4499:]
        last = steps[-1]
        again = {"courant_max_whole_run": max(s["courant_max"] for s in steps),
                 "courant_max_from_first_frame": max(s["courant_max"] for s in late),
                 "courant_mean_from_first_frame": sum(s["courant_mean"] for s in late) / len(late),
                 **{"last_" + k: last[k] for k in ("Ux_initial", "Uy_initial", "p_initial", "Ux_final", "Uy_final", "p_final",
                                                   "continuity_local", "continuity_global_abs", "continuity_cumulative_abs")}}
        for number, value in again.items():
            if value != run["log"][number]:
                problems.append(f"{run['name']}: {number} {value} in the log, {run['log'][number]} in the manifest")
        log_numbers[run["name"]].update(courant_max_whole_run=again["courant_max_whole_run"],
                                        courant_max_at_step=[s["courant_max"] for s in steps].index(again["courant_max_whole_run"]) + 1,
                                        steps_with_courant_above_1=sum(s["courant_max"] > 1 for s in steps))
    # the answers
    columns = []
    for path in sorted((HERE / "results").glob(f"*/*/{SET}/metrics.jsonl")):
        meta = json.loads((path.parents[1] / "run.json").read_text())
        answers = {row["name"]: row["structured_output"]["assessment"] if row["successful_response"] else None for row in rows(path)}
        if set(answers) != set(keys):
            problems.append(f"{path}: other frames than the key's")
        columns.append((meta["model"], answers))
    columns.sort(key=lambda c: ["gemma-4-12b", "gemma-4-26", "gemma-4-31", "qwen"].index(
        next(p for p in ("gemma-4-12b", "gemma-4-26", "gemma-4-31", "qwen") if c[0].startswith(p))))
    rule = {name: "consistent" if INLET <= key["numeric"]["max_speed_m_per_s"] <= 2 * INLET else "inconsistent"
            for name, key in keys.items()}
    counts = {}
    rule_label = "Rule: peak \\|U\\| in the window between 1 and 2 times 32.2 m/s"
    for label, answers in columns + [(rule_label, rule)]:
        normal = [n for n, k in keys.items() if k["class"] == "normal"]
        wrong = [n for n, k in keys.items() if k["class"] == "wrong"]
        said = lambda group, word: sum(answers.get(n) == word for n in group)
        right = said(normal, "consistent") + said(wrong, "inconsistent")
        counts[label] = {"answered": sum(answers.get(n) is not None for n in keys), "right": right,
                         "normal": {w: said(normal, w) for w in RIGHT.values()} | {"cannot_tell": said(normal, "cannot_tell")},
                         "wrong": {w: said(wrong, w) for w in RIGHT.values()} | {"cannot_tell": said(wrong, "cannot_tell")},
                         "by_run": {run: sum(answers.get(n) == RIGHT[k["class"]] for n, k in keys.items() if k["run"] == run) for run in names}}
        look(f"| {label} | {counts[label]['answered']} | {right} | {said(normal, 'consistent')} of 40 | {said(normal, 'inconsistent')} | "
             f"{said(normal, 'cannot_tell')} | {said(wrong, 'inconsistent')} of 40 | {said(wrong, 'consistent')} | {said(wrong, 'cannot_tell')} |")
    look("| Constant baseline | | 40 | | | | | | |")
    for run in runs:
        look(f"| {run['name']} | {run['class']} | {run['change']} | "
             + " | ".join(f"{counts[label]['by_run'][run['name']]} of 8" for label, _ in columns + [(rule_label, rule)]) + " |")
    # the numbers
    outside_frames, outside_logs = {}, {}
    for number, label in FRAME_NUMBERS:
        normal = [k["numeric"][number] for k in keys.values() if k["class"] == "normal"]
        low, high = min(normal), max(normal)
        cells = []
        for run in wrong_runs:
            values = [k["numeric"][number] for k in keys.values() if k["run"] == run]
            count = sum(not low <= v <= high for v in values)
            outside_frames.setdefault(number, {})[run] = count
            cells.append(f"{span(min(values), max(values))} ({count})")
        look(f"| {label} | {span(low, high)} | " + " | ".join(cells) + " |")
    for number, label in LOG_NUMBERS:
        values = [r["log"][number] for r in runs if r["class"] == "normal"]
        low, high = min(values), max(values)
        cells = []
        for run in runs:
            if run["class"] == "wrong":
                value = run["log"][number]
                outside_logs.setdefault(number, {})[run["name"]] = not low <= value <= high
                cells.append(g(value) + (" \\*" if not low <= value <= high else ""))
        look(f"| {label} | {span(low, high)} | " + " | ".join(cells) + " |")
    # every frame
    for name, key in keys.items():
        look(f"| {name} | {key['class']} | {key['numeric']['max_speed_m_per_s']:.4g} | {key['numeric']['min_pressure_m2_per_s2']:.4g} | "
             f"{MARK[rule[name]]} | " + " | ".join(MARK[a.get(name)] for _, a in columns) + " |")
    # the same flow state under another step and time
    overlap = json.loads((HERE / "flow" / "normal-overlap.json").read_text())
    def frame_name(text):
        run, _, step = text.split()
        return f"{run}-step{int(step):05d}"
    pairs = [(frame_name(p["a"]), frame_name(p["b"])) for p in overlap["pairs"]]
    same_state = {model: {"pairs": len(pairs), "same_answer": sum(a.get(x) == a.get(y) for x, y in pairs)} for model, a in columns}
    # the answers by step and how often they change along a run
    by_step, changes = {}, {}
    for model, answers in columns:
        by_step[model] = {str(step): {group: sum(answers.get(n) == RIGHT[group] for n, k in keys.items() if k["class"] == group and k["run_step"] == step)
                                      for group in RIGHT} for step in steps_wanted}
        changes[model] = {}
        for run in names:
            series = [answers.get(f"{run}-step{step:05d}") for step in steps_wanted]
            changes[model][run] = sum(x != y for x, y in zip(series, series[1:]))
    # the prompt length must not differ between the classes at one step
    tokens = {}
    for path in sorted((HERE / "results").glob(f"*/*/{SET}/metrics.jsonl")):
        meta = json.loads((path.parents[1] / "run.json").read_text())
        at_step = {}
        for row in rows(path):
            key = keys[row["name"]]
            at_step.setdefault(key["run_step"], {}).setdefault(key["class"], set()).add((row.get("usage") or {}).get("prompt_tokens"))
        tokens[meta["model"]] = {"same_prompt_tokens_in_both_classes_at_each_step": all(v["normal"] == v["wrong"] for v in at_step.values()),
                                 "prompt_tokens": sorted({t for v in at_step.values() for s in v.values() for t in s}),
                                 "median_wall_s": statistics.median(row["replay_wall_s"] for row in rows(path))}
    out = {"problems": problems, "report_lines_checked": checked, "counts": counts, "logs": log_numbers,
           "frames_outside_normal_range": outside_frames, "logs_outside_normal_range": outside_logs, "prompt_tokens": tokens,
           "same_flow_state_other_label": same_state, "right_by_step": by_step, "answer_changes_along_each_run": changes,
           "text_groups_normal_wrong": balance}
    (HERE / "recount.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(f"{checked} report lines checked, {len(problems)} problems")
    for line in problems[:40]:
        print(line)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
