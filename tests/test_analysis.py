"""
test_analysis.py
================

Unit tests for the Phase 4 Security Analysis data layer.

The AnalysisReport model is GUI-free on purpose, so every metric,
the strength score, the timeline and the TXT/JSON exporters can be
verified without opening a window.

Run them with:
    python run_tests.py
"""

from __future__ import annotations

import json
import unittest

from cybercrypt.analysis import (
    ALGORITHM_STACK,
    DISCLAIMER,
    AnalysisReport,
    build_analysis_report,
    educational_strength_score,
    format_duration,
    strength_band,
)

SAMPLE_TEXT = "Hello, CyberCrypt Pro! 2026 - Stay Secure."
KEYS = {"shift": 7, "vigenere_key": "SECRET", "seed": 12345}


def make_steps(cipher_text: str) -> list:
    """Three layer steps + the final complete step, as the engine emits."""
    return [
        {"key": "layer1", "elapsed": 0.001, "output": "first"},
        {"key": "layer2", "elapsed": 0.002, "output": "second"},
        {"key": "layer3", "elapsed": 0.003, "output": "third"},
        {"key": "complete", "elapsed": 0.0, "output": cipher_text},
    ]


def build_report(text: str = SAMPLE_TEXT) -> AnalysisReport:
    """A ready-to-assert report built from synthetic steps."""
    return build_analysis_report(text, KEYS, make_steps("CIPHER!"),
                                 decryption_time=0.5)


class TestStrengthBands(unittest.TestCase):
    """Band edges: the label must switch exactly at 20/40/60/80."""

    def test_band_edges(self):
        self.assertEqual(strength_band(0), "Very Basic")
        self.assertEqual(strength_band(19), "Very Basic")
        self.assertEqual(strength_band(20), "Basic")
        self.assertEqual(strength_band(39), "Basic")
        self.assertEqual(strength_band(40), "Educational")
        self.assertEqual(strength_band(59), "Educational")
        self.assertEqual(strength_band(60), "Layered")
        self.assertEqual(strength_band(79), "Layered")
        self.assertEqual(strength_band(80), "Advanced Demonstration")
        self.assertEqual(strength_band(100), "Advanced Demonstration")

    def test_out_of_range_clamps_to_lowest(self):
        self.assertEqual(strength_band(-5), "Very Basic")


class TestStrengthScore(unittest.TestCase):
    """The educational score stays inside 0..100 and grows with inputs."""

    def test_always_within_bounds(self):
        for args in [(0, 0, 0, 0), (50, 50, 5000, 128),
                     (7, 5, 100, 40)]:
            score = educational_strength_score(*args)
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 100)

    def test_empty_input_is_lowest(self):
        low = educational_strength_score(0, 0, 0, 0)
        rich = educational_strength_score(25, 25, 400, 100)
        self.assertLess(low, rich)

    def test_longer_key_raises_score(self):
        short = educational_strength_score(1, 5, 100, 30)
        long_ = educational_strength_score(20, 5, 100, 30)
        self.assertGreater(long_, short)

    def test_report_score_matches_function(self):
        report = build_report()
        expected = educational_strength_score(
            report.secret_key_length,
            report.random_key_length,
            report.char_count,
            report.unique_chars,
        )
        self.assertEqual(report.strength_score, expected)
        self.assertEqual(report.strength_level, strength_band(expected))


class TestFormatDuration(unittest.TestCase):
    """format_duration picks microseconds / milliseconds / seconds."""

    def test_microseconds(self):
        self.assertEqual(format_duration(0.0005), "500 \u00b5s")

    def test_milliseconds(self):
        self.assertEqual(format_duration(0.0031), "3.10 ms")

    def test_seconds(self):
        self.assertEqual(format_duration(2.5), "2.50 sec")


class TestBuildReport(unittest.TestCase):
    """Every dashboard metric must be computed from the run."""

    def test_message_statistics(self):
        text = "Hello World\nSecond line"
        report = build_analysis_report(text, KEYS, make_steps("x"),
                                       decryption_time=0.0)
        self.assertEqual(report.char_count, len(text))
        self.assertEqual(report.word_count, 4)
        self.assertEqual(report.line_count, 2)
        self.assertEqual(report.unique_chars, len(set(text)))
        self.assertEqual(report.whitespace_count, 3)

    def test_key_information(self):
        report = build_report()
        self.assertEqual(report.secret_key_length, len(KEYS["vigenere_key"]))
        self.assertEqual(report.random_key_length, len(str(KEYS["seed"])))
        self.assertEqual(report.generated_random_values, report.char_count)

    def test_performance_times(self):
        report = build_report()
        self.assertEqual(report.encryption_time, 0.006)   # three layers
        self.assertEqual(report.decryption_time, 0.5)
        self.assertEqual(report.average_layer_time, 0.002)
        self.assertEqual(report.total_time, 0.506)

    def test_output_analysis(self):
        report = build_report()
        self.assertEqual(report.cipher_length, len("CIPHER!"))
        self.assertEqual(report.printable_chars, 7)
        self.assertEqual(report.non_printable_chars, 0)
        self.assertEqual(report.encoding, "Custom 128-char alphabet")

    def test_timeline_shape(self):
        report = build_report()
        self.assertEqual([label for label, _ in report.timeline], [
            "Start",
            "Layer 1 - Caesar Cipher",
            "Layer 2 - Vigenere Cipher",
            "Layer 3 - Random XOR Layer",
            "Completed",
        ])
        self.assertEqual([ms for _, ms in report.timeline],
                         [0, 1, 2, 3, 0])

    def test_empty_message_still_reports(self):
        report = build_analysis_report("", KEYS, make_steps(""), 0.0)
        self.assertEqual(report.char_count, 0)
        self.assertEqual(report.word_count, 0)
        self.assertEqual(report.line_count, 0)
        self.assertEqual(report.cipher_length, 0)


class TestExports(unittest.TestCase):
    """Exports contain the report only - never the plain text."""

    def test_text_export_never_contains_plain_text(self):
        report = build_report()
        text = report.to_text()
        self.assertIn("Security Analysis Report", text)
        self.assertNotIn(SAMPLE_TEXT, text)
        self.assertIn(DISCLAIMER, text)

    def test_json_export_never_contains_plain_text(self):
        report = build_report()
        payload = report.to_json()
        self.assertNotIn(SAMPLE_TEXT, payload)
        data = json.loads(payload)
        self.assertEqual(data["output_analysis"]["cipher_length"], 7)
        self.assertEqual(data["key_information"]["secret_key_length"], 6)
        self.assertIn("educational_strength", data)
        self.assertIn("encryption_timeline", data)

    def test_json_report_round_trips(self):
        report = build_report()
        data = json.loads(report.to_json())
        self.assertEqual(data["generated"], report.timestamp)
        self.assertEqual(data["algorithm_stack"], ALGORITHM_STACK)
        self.assertEqual(len(data["encryption_timeline"]), 5)
        self.assertEqual(data["message_statistics"]["characters"],
                         report.char_count)


if __name__ == "__main__":
    unittest.main()
