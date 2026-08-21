"""
settings.py
===========

Persistent user preferences for CyberCrypt Pro.

Stored as a small JSON file next to the user's application data
(the desktop-app equivalent of localStorage):

    theme        "dark" | "light"     -> appearance mode
    time_format  "24" | "12"          -> clock display format

Load once at startup (before the window is built) and save on
every change. Corrupt / missing files fall back to defaults.
"""

from __future__ import annotations

import json
import os

# Defaults used when no settings file exists yet.
_DEFAULTS = {
    "theme": "dark",
    "time_format": "24",
}


def _settings_path() -> str:
    """Return the JSON file path in the user's app-data folder."""
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    folder = os.path.join(base, "CyberCrypt")
    try:
        os.makedirs(folder, exist_ok=True)
    except OSError:
        folder = os.path.expanduser("~")
    return os.path.join(folder, "settings.json")


def load_settings() -> dict:
    """
    Read the persisted preferences.

    Returns:
        A dict with at least "theme" and "time_format" keys.
    """
    path = _settings_path()
    data = dict(_DEFAULTS)
    try:
        with open(path, encoding="utf-8") as handle:
            stored = json.load(handle)
        if isinstance(stored, dict):
            data.update(stored)
    except (OSError, ValueError):
        pass  # missing or corrupt file -> defaults

    if data.get("theme") not in ("dark", "light"):
        data["theme"] = _DEFAULTS["theme"]
    if data.get("time_format") not in ("12", "24"):
        data["time_format"] = _DEFAULTS["time_format"]
    return data


def save_settings(settings: dict):
    """
    Persist the preferences to disk.

    Arguments:
        settings : dict with "theme" and "time_format" keys.
    """
    data = dict(_DEFAULTS)
    if isinstance(settings, dict):
        data.update(settings)
    try:
        with open(_settings_path(), "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
    except OSError:
        pass  # read-only home dir: preferences just won't persist
