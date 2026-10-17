"""Offline fixtures and loopback HTTP tests; no model or OpenFOAM process."""
from contextlib import contextmanager
import copy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
import struct
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import zlib

import numpy as np

import ablation_runner as runner


def png_chunk(kind, data):
    return (struct.pack(">I", len(data)) + kind + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff))


def fixture(directory, bundled=False, tied=False):
    case = Path(directory)
    images = case if bundled else case / "llm_observation"
    images.mkdir(parents=True, exist_ok=True)
    centres = np.array([[-0.5, 0.01, 0.00635], [0.0005, 0.0127, 0.00635], [0.5, 0.02, 0.00635]])
    velocity = np.array([[1., 0., 0.], [82.5, 0., 0.], [82.5 if tied else 2., 0., 0.]])
    np.savez_compressed(images / "fields.npz", centres=centres, U=velocity,
                        p=np.array([4., -3., 2.]), step=5, time_s=5e-7)
    fields_hash = runner.sha256((images / "fields.npz").read_bytes())
    png = b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    for key, value in {"FieldsSHA256": fields_hash, "Step": "5", "Time": "5e-7"}.items():
        png += png_chunk(b"tEXt", key.encode() + b"\0" + value.encode())
    png += png_chunk(b"IDAT", zlib.compress(b"\0\0\0\0")) + png_chunk(b"IEND", b"")
    (images / "state.png").write_bytes(png)
    image_summary = {"step": 5, "time_s": 5e-7, "cells": 3, "coordinate_unit": "m",
                     "projection_axes": ["x", "y"],
                     "ranges": {"speed_m_per_s": [1., 82.5], "p_m2_per_s2": [-3., 4.]},
                     "domain_extent_m": {"x": [-.5, .5], "y": [.01, .02]}}
    metadata = dict(image_summary, sha256=runner.sha256(png), fields_sha256=fields_hash)
    summary = {"step": 5, "time_s": 5e-7, "cells": 3, "image": image_summary,
               "courant": {"max": 0.208697}, "velocity_svd": {"method": "uncentered"}}
    runner.write_json(images / "image-metadata.json", metadata)
    name = "image_request_record.json" if bundled else "llm_request.json"
    runner.write_json(case / name, {"input": summary, "image": metadata})
    return case


@contextmanager
def serve(mode="ok"):
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            requests.append(self.rfile.read(int(self.headers["Content-Length"])))
            self.send_response(503 if mode == "http_error" else 200)
            self.end_headers()
            output = {"observations": "Maximum speed 82.5 m/s at x=0.25 m.",
                      "possible_interpretation": "May reflect acceleration.",
                      "checks": "Check a pressure gradient."}
            content = json.dumps({"choices": [{"message": {"content": json.dumps(output)},
                                                "finish_reason": "stop"}]}).encode()
            try:
                if mode == "stall":
                    time.sleep(0.6)
                self.wfile.write(b"broken JSON" if mode == "malformed" else content)
            except (BrokenPipeError, ConnectionResetError):
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1/chat/completions", requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)


class AblationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.case = fixture(self.root / "case")
        self.summary, self.truth, self.png, self.provenance = runner.load_case(self.case)

    def location(self, text):
        return runner.location_metrics(text, self.truth)

    def test_payloads_differ_only_by_png_and_do_not_leak_truth(self):
        pair = runner.make_payloads(self.summary, self.png, "fixed-model", 77)
        normalized = copy.deepcopy(pair["numeric_plus_image"])
        image = normalized["messages"][1]["content"].pop()
        self.assertEqual(normalized, pair["numeric_only"])
        self.assertEqual(image["type"], "image_url")
        self.assertIsInstance(pair["numeric_only"]["messages"][1]["content"], list)
        text = runner.encode_json(pair["numeric_only"]).decode()
        self.assertNotIn("0.0005", text)
        self.assertNotIn("0.0127", text)
        self.assertEqual(normalized["seed"], 77)
        self.assertEqual(normalized["temperature"], 0.0)

    def test_leaked_extrema_removed_and_unknown_schema_rejected(self):
        summary = copy.deepcopy(self.summary)
        summary["ground_truth"] = self.truth
        summary["image"]["max_speed_position"] = [0.0005, .0127, .00635]
        clean, removed = runner.sanitize_summary(summary)
        self.assertEqual(clean["image"], self.summary["image"])
        self.assertEqual(len(removed), 2)
        summary["extra"] = "x=0.0005 m"
        with self.assertRaises(ValueError):
            runner.sanitize_summary(summary)

    def test_bundled_case_and_tied_maximum(self):
        summary, truth, _, _ = runner.load_case(fixture(self.root / "bundle", bundled=True, tied=True))
        self.assertFalse(truth["unique_maximum"])
        self.assertEqual(truth["max_speed_cells"], [1, 2])
        metric = runner.location_metrics("Maximum speed at x=0.5 m, y=0.02 m.", truth)
        self.assertEqual(metric["projected_error_m"], 0.0)
        self.assertEqual(metric["reference_candidate_count"], 2)

    def test_tampered_fields_and_png_provenance_rejected(self):
        fields = self.png.parent / "fields.npz"
        fields.write_bytes(fields.read_bytes() + b"changed")
        with self.assertRaisesRegex(ValueError, "Fields do not match"):
            runner.load_case(self.case)
        fixture(self.case)
        png = self.png.read_bytes().replace(b"FieldsSHA256", b"WrongHashKey")
        self.png.write_bytes(png)
        with self.assertRaisesRegex(ValueError, "CRC mismatch"):
            runner.load_case(self.case)

    def test_snapshot_mismatch_rejected(self):
        path = self.case / "llm_request.json"
        record = runner.read_json(path)
        record["input"]["time_s"] = 6e-7
        runner.write_json(path, record)
        with self.assertRaisesRegex(ValueError, "step/time/cell count"):
            runner.load_case(self.case)

    def test_wrong_image_units_or_extent_are_rejected(self):
        path = self.case / "llm_request.json"
        original = runner.read_json(path)
        for key, value in (("coordinate_unit", "cm"),
                           ("domain_extent_m", {"x": [-5., 5.], "y": [.01, .02]}),
                           ("projection_axes", ["x", "x"])):
            record = copy.deepcopy(original)
            record["input"]["image"][key] = value
            runner.write_json(path, record)
            with self.subTest(key=key), self.assertRaises(ValueError):
                runner.load_case(self.case)

    def test_image_changed_after_verification_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "PNG changed"):
            runner.make_payloads(self.summary, self.png, "test", 1, expected_png_sha256="wrong")

    def test_units_signed_scientific_and_axis_only_distance(self):
        metric = self.location("Max |U| at x=+2.5e1 cm; speed 82.5 m/s.")
        self.assertEqual(metric["axes"], ["x"])
        self.assertAlmostEqual(metric["axis_errors_m"]["x"], .2495)
        self.assertIsNone(metric["euclidean_error_m"])
        self.assertIsNone(metric["projected_error_m"])
        metric = self.location("Maximum speed at x=−2.5e2 mm.")
        self.assertAlmostEqual(metric["coordinates_m"]["x"], -.25)

    def test_projected_and_full_distances_do_not_fill_missing_axes(self):
        metric = self.location("Maximum speed at x=0.0005 m, y=0.0127 m.")
        self.assertEqual(metric["projected_error_m"], 0.)
        self.assertIsNone(metric["euclidean_error_m"])
        metric = self.location("Maximum speed at (x,y,z)=(0.0005,0.0127,0.00635) m.")
        self.assertEqual(metric["euclidean_error_m"], 0.)
        self.assertIsNone(metric["projected_error_m"])

    def test_ambiguous_missing_and_unsupported_locations_stay_null(self):
        cases = ["Maximum speed at x=0.25.", "Maximum speed at x=NaN m.",
                 "Maximum speed at x=Inf m.", "Maximum speed at x=1e999 m.",
                 "Maximum speed at x=1e308 m.", "Maximum speed not at x=0.1 m.",
                 "Maximum speed is 82.5 m/s. Inlet x=-1 m.",
                 "Maximum speed at x=0.1 m; the outlet y=0.2 m.",
                 "Maximum speed at x=0.1 m ± 0.02 m.",
                 "Maximum speed at x=0.2 m or x=0.4 m.",
                 "Maximum speed at x=0.2-0.4 m.", "Maximum speed at x=0.2 m to 0.4 m.",
                 "Maximum speed at x=0.2 m/s.", "Maximum speed at x=0.2 m and y=0.3.",
                 "Maximum speed is unknown; x=0.25 m.", "Maximum speed may be at x=0.25 m.",
                 "Maximum speed at x=.2 m; minimum pressure at x=.3 m.",
                 "Pressure minimum at x=0.25 m.", "Maximum speed at x=.2 m, x=.2 m.",
                 "Maximum speed at (x,y,z)=(0.2,0.3) m.",
                 "Maximum speed at (x,y)=(0.1,0.2) m and (x,y)=(0.3,0.4) m."]
        for text in cases:
            with self.subTest(text=text):
                metric = self.location(text)
                self.assertEqual(metric["status"], "unscorable")
                self.assertIsNone(metric["euclidean_error_m"])
                self.assertIsNone(metric["axis_errors_m"])

    def test_grounding_flags_only_assertions_and_keeps_manual_review(self):
        output = {"observations": "Maximum speed 82.5 m/s. Strong pressure gradient exists.",
                  "possible_interpretation": "May indicate stability.",
                  "checks": "Check force balance and strong pressure gradient."}
        metric = runner.grounding_metrics(output, self.summary, self.truth)
        self.assertEqual(len(metric["unsupported_claim_flags"]), 1)
        self.assertEqual(metric["unsupported_claim_flags"][0]["field"], "observations")
        self.assertTrue(metric["numeric_checks"][0]["agrees_with_numeric_evidence"])
        self.assertTrue(metric["needs_human_review"])
        self.assertIsNone(metric["hallucination_free"])
        output["observations"] = "Maximum speed 10 m/s; max Courant 0.9."
        metric = runner.grounding_metrics(output, self.summary, self.truth)
        self.assertEqual(metric["numeric_contradiction_count"], 2)

    def test_assertions_in_checks_flagged_and_overflow_serializable(self):
        output = {"observations": "Maximum speed 1e999 m/s; max Courant 1e999.",
                  "possible_interpretation": "Unknown.",
                  "checks": "The pressure field shows a significant pressure gradient near the high-velocity region."}
        metric = runner.grounding_metrics(output, self.summary, self.truth)
        runner.encode_json(metric)
        self.assertEqual(len(metric["unsupported_claim_flags"]), 3)
        self.assertEqual(metric["unsupported_claim_flags"][-1]["field"], "checks")

    def test_default_offline_and_alternating_pairs(self):
        output = self.root / "prepared"
        with patch.object(runner, "request_local", side_effect=AssertionError("Must stay offline")):
            self.assertEqual(runner.main(["--case", str(self.case), "--output", str(output),
                                          "--repeats", "2", "--seed", "40"]), 0)
        manifest = runner.read_json(output / "manifest.json")
        self.assertEqual(manifest["mode"], "offline_preparation")
        self.assertEqual([r["condition"] for r in manifest["schedule"]],
                         ["numeric_only", "numeric_plus_image", "numeric_plus_image", "numeric_only"])
        self.assertEqual([r["seed"] for r in manifest["schedule"]], [40, 40, 41, 41])
        self.assertFalse((output / "metrics.jsonl").exists())
        with self.assertRaises(FileExistsError):
            runner.main(["--case", str(self.case), "--output", str(output)])

    def test_mock_execution_exact_bodies_response_hashes_and_latency_scope(self):
        output = self.root / "executed"
        with serve() as (endpoint, requests):
            result = runner.main(["--case", str(self.case), "--output", str(output),
                                  "--repeats", "1", "--execute", "--endpoint", endpoint])
        self.assertEqual(result, 0)
        metrics = [json.loads(line) for line in (output / "metrics.jsonl").read_text().splitlines()]
        self.assertEqual(len(requests), 2)
        for index, metric in enumerate(metrics):
            self.assertEqual(metric["request_sha256"], runner.sha256(requests[index]))
            trial = output / f"pair-001-{metric['condition']}"
            self.assertEqual((trial / "request_body.json").read_bytes(), requests[index])
            self.assertEqual(metric["raw_response_sha256"], runner.sha256((trial / "response.raw").read_bytes()))
            self.assertAlmostEqual(metric["location"]["axis_errors_m"]["x"], .2495)
            self.assertGreaterEqual(metric["replay_callback_wall_s"], metric["transport_wait_wall_s"])
            self.assertEqual(metric["status"], "ok")
        summary = runner.read_json(output / "summary.json")
        self.assertEqual(summary["numeric_only"]["location_errors_m_by_axes"], {"x": [.2495]})

    def test_failures_and_timeouts_are_logged_not_successes(self):
        payload = runner.make_payloads(self.summary, self.png, "test", 1)["numeric_only"]
        rows = []
        for mode in ("stall", "http_error", "malformed"):
            with self.subTest(mode=mode), serve(mode) as (endpoint, requests):
                metric = runner.run_trial(payload, self.root / mode, self.summary, self.truth,
                                          endpoint, .15 if mode == "stall" else 2.)
                self.assertFalse(metric["successful_response"])
                self.assertIsNone(metric["location"])
                self.assertIsNone(metric["grounding"])
                if mode == "stall":
                    self.assertEqual(metric["status"], "timeout")
                    self.assertLess(metric["transport_wait_wall_s"], 1.0)
                metric["condition"] = "numeric_only"
                rows.append(metric)
        report = runner.summarize(rows)["numeric_only"]
        self.assertEqual(report["attempted"], 3)
        self.assertEqual(report["successful"], 0)
        self.assertEqual(report["grounding_denominator_successful_responses"], 0)
        self.assertEqual(report["location_errors_m_by_axes"], {})

    def test_refused_connection_is_logged(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        payload = runner.make_payloads(self.summary, self.png, "test", 1)["numeric_only"]
        metric = runner.run_trial(payload, self.root / "refused", self.summary, self.truth,
                                  f"http://127.0.0.1:{port}/", 1.)
        self.assertEqual(metric["status"], "error")
        self.assertIsNone(metric["location"])


if __name__ == "__main__":
    unittest.main()
