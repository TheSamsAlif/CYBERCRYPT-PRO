"""
run_tests.py
============

Runs the full unit-test suite of CyberCrypt Pro.

Usage:
    python run_tests.py
"""

from __future__ import annotations

import os
import sys
import unittest

# Make the project importable from anywhere.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def main() -> int:
    """Discover and run every test inside the tests/ folder."""
    suite = unittest.defaultTestLoader.discover(
        os.path.join(PROJECT_ROOT, "tests"),
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
