"""
visualizer.py
=============

Phase 3 : live layer-by-layer visualization.

The encryption engine stays untouched. This module only *reads*
the individual cipher functions (caesar, vigenere, random XOR)
to show the user what each layer does to the text.

Two jobs:

    1. build_encrypt_steps() / build_decrypt_steps()
       run every layer once and capture:
           - the intermediate output of that layer
           - the real processing time (perf_counter)
           - the educational text (purpose, advantages, ...)

    2. VisualRunner
       plays the steps back with smooth staggered UI updates.
       It only schedules after() callbacks, so the UI never
       freezes and the CPU stays idle between steps.
"""

from __future__ import annotations

import time

from cybercrypt.core import caesar_cipher, random_layer, vigenere_cipher
from cybercrypt.ui.theme import ICONS

# ---------------------------------------------------------------------- #
# Educational content (one entry per layer)                               #
# ---------------------------------------------------------------------- #

LAYER_INFO = {
    "caesar": {
        "title": "Caesar Cipher",
        "icon": "A",
        "tagline": "Layer 1 of 3",
        "purpose": "Shift every character forward by a fixed number of "
                   "positions in the alphabet.",
        "advantages": "Dead simple to understand and verify by hand.",
        "limitations": "Only 128 possible shifts - trivial to brute force "
                       "on its own.",
    },
    "vigenere": {
        "title": "Vigenere Cipher",
        "icon": "V",
        "tagline": "Layer 2 of 3",
        "purpose": "Shift every character by a different amount, driven "
                   "by a repeating keyword.",
        "advantages": "A keyword defeats simple frequency analysis.",
        "limitations": "A short or repeated keyword can still leak patterns.",
    },
    "random": {
        "title": "Random XOR Layer",
        "icon": "X",
        "tagline": "Layer 3 of 3",
        "purpose": "XOR every character with a pseudo-random keystream "
                   "generated from the numeric seed.",
        "advantages": "XOR is its own inverse - the same code encrypts "
                      "and decrypts.",
        "limitations": "Security depends on the seed staying secret.",
    },
}

# Description used while the panel is waiting for a run.
_IDLE_DETAILS = {
    "title": "Waiting",
    "icon": ICONS["INFO"],
    "tagline": "Press the action button",
    "purpose": "Watch each layer transform the text, one step at a time.",
    "advantages": "Every intermediate output is shown as it happens.",
    "limitations": "The final result is identical to running all layers "
                   "at once.",
}


def _measure(function, *args):
    """
    Run one cipher layer and time it.

    Arguments:
        function : the cipher function (e.g. caesar_cipher.encrypt).
        args     : the arguments for that function.

    Returns:
        (output, elapsed_seconds)
    """
    started = time.perf_counter()
    output = function(*args)
    return output, time.perf_counter() - started


def build_encrypt_steps(plain_text: str, shift: int, vigenere_key: str,
                        seed: int) -> list:
    """
    Run the three layers in encryption order and capture every
    intermediate output.

    Arguments:
        plain_text   : the original message.
        shift        : Caesar shift.
        vigenere_key : Vigenere keyword.
        seed         : random XOR seed.

    Returns:
        A list of step dictionaries (one per layer) plus a trailing
        "complete" step describing the finished operation.

    The output of each layer is produced by the exact same functions
    the engine uses, so the final text is bit-for-bit identical to
    EncryptionEngine.encrypt_text().
    """
    step_one, time_one = _measure(caesar_cipher.encrypt, plain_text, shift)
    step_two, time_two = _measure(
        vigenere_cipher.encrypt, step_one, vigenere_key)
    step_three, time_three = _measure(
        random_layer.encrypt, step_two, seed)

    steps = [
        _make_step("caesar", step_one, time_one, direction="applied"),
        _make_step("vigenere", step_two, time_two, direction="applied"),
        _make_step("random", step_three, time_three, direction="applied"),
    ]
    steps.append(_make_complete_step("Encryption complete", step_three))
    return steps


def build_decrypt_steps(cipher_text: str, shift: int, vigenere_key: str,
                        seed: int) -> list:
    """
    Run the three layers in decryption order (exact reverse) and
    capture every intermediate output.

    Arguments:
        cipher_text  : the encrypted message.
        shift        : the same Caesar shift.
        vigenere_key : the same keyword.
        seed         : the same seed.

    Returns:
        A list of step dictionaries (random -> vigenere -> caesar)
        plus a trailing "complete" step.

    The recovered text is identical to EncryptionEngine.decrypt_text().
    """
    step_one, time_one = _measure(random_layer.decrypt, cipher_text, seed)
    step_two, time_two = _measure(
        vigenere_cipher.decrypt, step_one, vigenere_key)
    step_three, time_three = _measure(
        caesar_cipher.decrypt, step_two, shift)

    steps = [
        _make_step("random", step_one, time_one, direction="removed"),
        _make_step("vigenere", step_two, time_two, direction="removed"),
        _make_step("caesar", step_three, time_three, direction="removed"),
    ]
    steps.append(_make_complete_step("Decryption complete", step_three))
    return steps


def _make_step(layer_key: str, output: str, elapsed: float,
               direction: str) -> dict:
    """
    Build one step dictionary from a layer result.

    Arguments:
        layer_key : "caesar", "vigenere" or "random".
        output    : the intermediate text after this layer.
        elapsed   : processing time in seconds.
        direction : "applied" (encrypt) or "removed" (decrypt).

    Returns:
        A dictionary with all fields the panels need.
    """
    info = LAYER_INFO[layer_key]
    return {
        "key": layer_key,
        "title": info["title"],
        "icon": info["icon"],
        "tagline": info["tagline"],
        "purpose": info["purpose"],
        "advantages": info["advantages"],
        "limitations": info["limitations"],
        "output": output,
        "elapsed": elapsed,
        "direction": direction,
    }


def _make_complete_step(title: str, output: str) -> dict:
    """
    The final step of a run ("Encryption complete").

    Arguments:
        title  : heading text.
        output : the final result (cipher or recovered text).

    Returns:
        A step dictionary with key "complete".
    """
    return {
        "key": "complete",
        "title": title,
        "icon": ICONS["CHECK"],
        "tagline": "All three layers",
        "purpose": "Every layer has been applied in the documented order.",
        "advantages": "",
        "limitations": "",
        "output": output,
        "elapsed": 0.0,
        "direction": "done",
    }


def format_seconds(elapsed: float) -> str:
    """
    Format a processing time for display.

    Arguments:
        elapsed : seconds as a float.

    Returns:
        e.g. "0.0012 sec"
    """
    return f"{elapsed:.4f} sec"


def preview_text(text: str, limit: int = 42) -> str:
    """
    Shorten a text for output previews.

    Arguments:
        text  : the full intermediate output.
        limit : maximum number of characters to show.

    Returns:
        The truncated text with an ellipsis, or "(empty)".
    """
    if not text:
        return "(empty)"
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


# ---------------------------------------------------------------------- #
# Playback runner                                                         #
# ---------------------------------------------------------------------- #

class VisualRunner:
    """
    Plays a list of steps back with smooth staggered timing.

    The runner never blocks the UI: every state change is scheduled
    with after(). It fires three kinds of callbacks:

        on_step(index, state, step)
            state is "running" (layer starting) or "done" (layer
            finished and its intermediate output is ready).

        on_progress(step_index, state)
            for the segmented progress bar.

        on_done(steps)
            the whole run finished.

    Usage:
        runner = VisualRunner(app, on_step=..., on_progress=...,
                              on_done=...)
        runner.run(steps)
    """

    _RUNNING_MS = 650   # how long a layer stays in the "running" state
    _DONE_MS = 450      # how long its result stays visible afterwards

    def __init__(self, root, on_step=None, on_progress=None, on_done=None):
        self._root = root
        self._on_step = on_step
        self._on_progress = on_progress
        self._on_done = on_done
        self._after_ids = []
        self._active = False

    # ------------------------------------------------------------------ #
    # Public API                                                          #
    # ------------------------------------------------------------------ #

    def run(self, steps: list):
        """
        Start playing the steps.

        Arguments:
            steps : the list from build_encrypt_steps() /
                    build_decrypt_steps() (last entry = complete).
        """
        self.cancel()
        self._active = True
        self._after_ids = []

        layer_steps = steps[:-1]          # the three real layers
        complete = steps[-1]              # the final "complete" step
        step_ms = self._RUNNING_MS + self._DONE_MS

        for index, step in enumerate(layer_steps):
            start_at = index * step_ms
            self._schedule(start_at, self._step_running, index, step)
            self._schedule(start_at + self._RUNNING_MS,
                           self._step_done, index, step)

        # The "complete" step and the finish callback.
        self._schedule(len(layer_steps) * step_ms,
                       self._step_complete, len(layer_steps), complete)
        self._schedule(len(layer_steps) * step_ms + self._DONE_MS,
                       self._finish, steps)

    def cancel(self):
        """Stop the run and discard every pending callback."""
        self._active = False
        for after_id in self._after_ids:
            try:
                self._root.after_cancel(after_id)
            except Exception:
                pass
        self._after_ids = []

    @property
    def is_active(self) -> bool:
        """True while a run is playing."""
        return self._active

    # ------------------------------------------------------------------ #
    # Internals                                                           #
    # ------------------------------------------------------------------ #

    def _schedule(self, delay_ms: int, callback, *args):
        """Schedule one callback and remember its id for cancel()."""
        def _safe():
            if not self._active:
                return
            try:
                callback(*args)
            except Exception:
                pass  # widgets may be gone (window closed mid-run)
        after_id = self._root.after(delay_ms, _safe)
        self._after_ids.append(after_id)

    def _step_running(self, index: int, step: dict):
        """Notify that a layer just started."""
        self._active = True
        if self._on_step is not None:
            self._on_step(index, "running", step)
        if self._on_progress is not None:
            self._on_progress(index, "running")

    def _step_done(self, index: int, step: dict):
        """Notify that a layer finished."""
        if self._on_step is not None:
            self._on_step(index, "done", step)
        if self._on_progress is not None:
            self._on_progress(index, "done")

    def _step_complete(self, index: int, step: dict):
        """The final "complete" step (all layers finished)."""
        if self._on_step is not None:
            self._on_step(index, "done", step)

    def _finish(self, steps: list):
        """The whole run finished."""
        self._active = False
        if self._on_done is not None:
            try:
                self._on_done(steps)
            except Exception:
                pass
