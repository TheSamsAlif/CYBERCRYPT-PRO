"""
analysis.py
===========

Phase 4 : the Security Analysis Dashboard data layer.

This module turns the last encryption run into an `AnalysisReport`:
pure statistics about the message, the keys, the timings, the
cipher output and an *educational* complexity score.

IMPORTANT (read before presenting):
    * Every number here is an EDUCATIONAL metric.
    * The strength score describes how interesting the *demo* is,
      NOT how secure the ciphertext is. Classical ciphers like
      Caesar / Vigenere are trivially broken by modern computers.
    * Reports never contain the plain text - privacy by design.

The module is GUI-free, so it can be unit-tested without a window.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field

# The layers of the demo, in their fixed application order.
LAYER_NAMES = ("Caesar Cipher", "Vigenere Cipher", "Random XOR Layer")
ALGORITHM_STACK = "Caesar \u2192 Vigen\u00e8re \u2192 Random XOR"

# Educational strength bands (used by the strength meter card).
STRENGTH_BANDS = (
    (0, 19, "Very Basic"),
    (20, 39, "Basic"),
    (40, 59, "Educational"),
    (60, 79, "Layered"),
    (80, 100, "Advanced Demonstration"),
)

DISCLAIMER = (
    "This score reflects the educational complexity of the "
    "demonstration, not real-world cryptographic strength."
)


def strength_band(score: int) -> str:
    """
    Map a score to its educational label.

    Arguments:
        score : 0..100.

    Returns:
        e.g. "Educational" or "Advanced Demonstration".
    """
    for low, high, label in STRENGTH_BANDS:
        if low <= score <= high:
            return label
    return "Very Basic"


def educational_strength_score(secret_key_length: int,
                              random_key_length: int,
                              char_count: int,
                              unique_chars: int) -> int:
    """
    Compute the educational complexity score (0..100).

    The score combines four easy-to-explain factors:

        25 pts  the three-layer stack itself (Caesar, Vigenere, XOR)
        0..20   keyword length          (a longer keyword is richer)
        0..15   seed digits             (a bigger seed is richer)
        0..25   message length          (longer messages exercise more)
        0..15   character diversity     (unique characters used)

    Arguments:
        secret_key_length : length of the Vigenere keyword.
        random_key_length : number of digits in the XOR seed.
        char_count        : length of the plain message.
        unique_chars      : distinct characters in the message.

    Returns:
        An integer 0..100.
    """
    score = 25
    score += min(20, secret_key_length * 2)
    score += min(15, random_key_length * 3)
    score += min(25, char_count // 2)
    score += min(15, unique_chars)
    return max(0, min(100, score))


def format_duration(seconds: float) -> str:
    """
    Format a processing duration for display.

    Arguments:
        seconds : processing time in seconds.

    Returns:
        e.g. "0.0031 sec" or "3.1 ms".
    """
    if seconds < 0.001:
        return f"{seconds * 1_000_000:.0f} \u00b5s"
    if seconds < 1:
        return f"{seconds * 1000:.2f} ms"
    return f"{seconds:.2f} sec"


@dataclass
class AnalysisReport:
    """Everything the Security Analysis dashboard displays."""

    # --- Header -------------------------------------------------------- #
    timestamp: str = ""                    # when the report was created
    algorithm_stack: str = ALGORITHM_STACK

    # --- Message statistics --------------------------------------------- #
    char_count: int = 0
    word_count: int = 0
    line_count: int = 0
    unique_chars: int = 0
    whitespace_count: int = 0

    # --- Key information ------------------------------------------------- #
    secret_key_length: int = 0             # Vigenere keyword length
    random_key_length: int = 0             # digits in the XOR seed
    generated_random_values: int = 0       # keystream values produced

    # --- Performance ------------------------------------------------------ #
    encryption_time: float = 0.0           # seconds (3 layers)
    decryption_time: float = 0.0           # seconds (3 layers, reverse)
    average_layer_time: float = 0.0        # encryption_time / 3
    total_time: float = 0.0                # encryption + decryption

    # --- Educational strength --------------------------------------------- #
    strength_score: int = 0
    strength_level: str = "Very Basic"

    # --- Output analysis --------------------------------------------------- #
    cipher_length: int = 0
    printable_chars: int = 0
    non_printable_chars: int = 0
    encoding: str = "Custom 128-char alphabet"

    # --- Timeline: [(label, duration_ms)] ---------------------------------- #
    timeline: list = field(default_factory=list)

    def as_dict(self) -> dict:
        """Flat dictionary used by the JSON exporter."""
        return {
            "generated": self.timestamp,
            "algorithm_stack": self.algorithm_stack,
            "message_statistics": {
                "characters": self.char_count,
                "words": self.word_count,
                "lines": self.line_count,
                "unique_characters": self.unique_chars,
                "whitespace": self.whitespace_count,
            },
            "key_information": {
                "secret_key_length": self.secret_key_length,
                "random_key_length": self.random_key_length,
                "generated_random_values": self.generated_random_values,
            },
            "performance": {
                "encryption_time_seconds": round(self.encryption_time, 6),
                "decryption_time_seconds": round(self.decryption_time, 6),
                "average_layer_time_seconds": round(
                    self.average_layer_time, 6),
                "total_processing_time_seconds": round(self.total_time, 6),
            },
            "educational_strength": {
                "score": self.strength_score,
                "level": self.strength_level,
                "disclaimer": DISCLAIMER,
            },
            "output_analysis": {
                "cipher_length": self.cipher_length,
                "printable_characters": self.printable_chars,
                "non_printable_characters": self.non_printable_chars,
                "encoding_used": self.encoding,
            },
            "encryption_timeline": [
                {"step": label, "duration_ms": ms}
                for label, ms in self.timeline
            ],
        }

    # ------------------------------------------------------------------ #
    # Exporters (only the report - never the plain text)                  #
    # ------------------------------------------------------------------ #

    def to_text(self) -> str:
        """
        Render the report as a readable text file.

        Returns:
            The full report text (no plain text anywhere).
        """
        lines = [
            "CyberCrypt Pro - Security Analysis Report",
            "==========================================",
            f"Generated : {self.timestamp}",
            f"Algorithm : {self.algorithm_stack}",
            "",
            "Note: all metrics are educational. They describe the "
            "demonstration, not real-world cryptographic strength.",
            "",
            "MESSAGE STATISTICS",
            f"  Characters ......... {self.char_count}",
            f"  Words .............. {self.word_count}",
            f"  Lines .............. {self.line_count}",
            f"  Unique characters .. {self.unique_chars}",
            f"  Whitespace ......... {self.whitespace_count}",
            "",
            "KEY INFORMATION",
            f"  Secret key length ... {self.secret_key_length}",
            f"  Random key length ... {self.random_key_length}",
            f"  Random values ....... {self.generated_random_values}",
            "",
            "PERFORMANCE",
            f"  Encryption time ..... {format_duration(self.encryption_time)}",
            f"  Decryption time ..... {format_duration(self.decryption_time)}",
            f"  Average layer time .. {format_duration(self.average_layer_time)}",
            f"  Total time .......... {format_duration(self.total_time)}",
            "",
            "EDUCATIONAL STRENGTH (not real-world security)",
            f"  Score ............... {self.strength_score} / 100",
            f"  Level ............... {self.strength_level}",
            "",
            "OUTPUT ANALYSIS",
            f"  Cipher length ....... {self.cipher_length}",
            f"  Printable characters. {self.printable_chars}",
            f"  Non-printable ....... {self.non_printable_chars}",
            f"  Encoding ............ {self.encoding}",
            "",
            "ENCRYPTION TIMELINE",
        ]
        for label, ms in self.timeline:
            lines.append(f"  {label}: {ms} ms")
        lines += [
            "",
            DISCLAIMER,
            "",
        ]
        return "\n".join(lines)

    def to_json(self) -> str:
        """
        Render the report as formatted JSON.

        Returns:
            A JSON string (no plain text anywhere).
        """
        return json.dumps(self.as_dict(), indent=2)


def build_analysis_report(plain_text: str, keys: dict,
                          steps: list,
                          decryption_time: float = 0.0) -> AnalysisReport:
    """
    Build a full report from one encryption run.

    Arguments:
        plain_text      : the original message (only its statistics
                          are stored - the text itself never is).
        keys            : {"shift": int, "vigenere_key": str, "seed": int}.
        steps           : the step list from visualizer.build_encrypt_steps()
                          (the final entry holds the ciphertext).
        decryption_time : optional time of the matching decryption run.

    Returns:
        A populated AnalysisReport.
    """
    report = AnalysisReport()
    report.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    # --- Message statistics --------------------------------------------- #
    report.char_count = len(plain_text)
    report.word_count = len(plain_text.split())
    report.line_count = plain_text.count("\n") + (1 if plain_text else 0)
    report.unique_chars = len(set(plain_text))
    report.whitespace_count = sum(1 for char in plain_text
                                  if char.isspace())

    # --- Key information -------------------------------------------------- #
    vigenere_key = keys.get("vigenere_key", "")
    seed = keys.get("seed", 0)
    report.secret_key_length = len(vigenere_key)
    report.random_key_length = len(str(seed))
    report.generated_random_values = report.char_count

    # --- Performance ------------------------------------------------------- #
    layer_steps = steps[:-1]   # the three real layers
    report.encryption_time = sum(
        step.get("elapsed", 0.0) for step in layer_steps)
    report.decryption_time = decryption_time
    report.average_layer_time = (
        report.encryption_time / 3 if report.encryption_time else 0.0)
    report.total_time = report.encryption_time + report.decryption_time

    # --- Educational strength --------------------------------------------- #
    report.strength_score = educational_strength_score(
        report.secret_key_length,
        report.random_key_length,
        report.char_count,
        report.unique_chars,
    )
    report.strength_level = strength_band(report.strength_score)

    # --- Output analysis --------------------------------------------------- #
    cipher_text = steps[-1].get("output", "")
    report.cipher_length = len(cipher_text)
    report.printable_chars = sum(1 for char in cipher_text
                                 if char.isprintable())
    report.non_printable_chars = (
        report.cipher_length - report.printable_chars)
    report.encoding = "Custom 128-char alphabet"

    # --- Timeline ---------------------------------------------------------- #
    report.timeline = [
        ("Start", 0),
    ]
    for index, step in enumerate(layer_steps):
        report.timeline.append((
            f"Layer {index + 1} - {LAYER_NAMES[index]}",
            int(round(step.get("elapsed", 0.0) * 1000)),
        ))
    report.timeline.append(("Completed", 0))

    return report


# Re-exported for the dashboard's algorithm overview card (keeps the
# educational text in one place - no duplicated strings).
_CAESAR_INFO = {
    "name": "Caesar Cipher",
    "icon": "A",
    "purpose": "Shift every character forward by a fixed number of "
               "positions in the 128-char alphabet.",
    "advantages": "Dead simple to understand and verify by hand.",
    "limitations": "Only 128 possible shifts - trivial to brute force.",
}
_VIGENERE_INFO = {
    "name": "Vigen\u00e8re Cipher",
    "icon": "V",
    "purpose": "Shift every character by a different amount, driven "
               "by a repeating keyword.",
    "advantages": "A keyword defeats simple frequency analysis.",
    "limitations": "A short or repeated keyword can leak patterns.",
}
_RANDOM_INFO = {
    "name": "Random XOR Layer",
    "icon": "X",
    "purpose": "XOR every character with a pseudo-random keystream "
               "generated from the numeric seed.",
    "advantages": "XOR is its own inverse - the same code encrypts "
                  "and decrypts.",
    "limitations": "Security depends on the seed staying secret.",
}

ALGORITHM_OVERVIEW = (_CAESAR_INFO, _VIGENERE_INFO, _RANDOM_INFO)
