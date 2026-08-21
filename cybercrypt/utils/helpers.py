"""
helpers.py
==========

Tiny colour utility functions used for smooth colour animations
(glass hover effects, fades, glowing accents).
"""

from __future__ import annotations

import time


def hex_to_rgb(hex_color: str) -> tuple:
    """
    Convert a hex colour like "#3B82F6" into an (r, g, b) tuple.

    Arguments:
        hex_color : colour string starting with '#'.

    Returns:
        A tuple of three integers in the range 0..255.
    """
    value = hex_color.lstrip("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def rgb_to_hex(red: int, green: int, blue: int) -> str:
    """
    Convert (r, g, b) values back into a hex colour string.

    Arguments:
        red, green, blue : colour components in the range 0..255.

    Returns:
        A colour string like "#3B82F6".
    """
    return f"#{red:02X}{green:02X}{blue:02X}"


def interpolate_color(color_a: str, color_b: str, factor: float) -> str:
    """
    Mix two colours together.

    Arguments:
        color_a : starting colour.
        color_b : target colour.
        factor  : 0.0 (all A) .. 1.0 (all B).

    Returns:
        The interpolated colour as a hex string.
    """
    factor = max(0.0, min(1.0, factor))
    start = hex_to_rgb(color_a)
    end = hex_to_rgb(color_b)

    mixed = tuple(
        round(start[i] + (end[i] - start[i]) * factor)
        for i in range(3)
    )
    return rgb_to_hex(*mixed)


def clamp_int(value: int, low: int, high: int) -> int:
    """
    Keep an integer inside the inclusive range [low, high].

    Arguments:
        value : the number to clamp.
        low   : minimum allowed value.
        high  : maximum allowed value.

    Returns:
        The clamped value.
    """
    return max(low, min(high, value))


def format_clock(timestamp, time_format: str = "24") -> str:
    """
    Format a time for the top-bar clock.

    Arguments:
        timestamp   : a time.struct_time (or any time.strftime input).
        time_format : "24" for 24-hour (20:45), "12" for 12-hour
                      with AM/PM (08:45 PM).

    Returns:
        A string like "20:45:32" or "08:45:32 PM".
    """
    if time_format == "12":
        return time.strftime("%I:%M:%S %p", timestamp)
    return time.strftime("%H:%M:%S", timestamp)


def format_estimated_time(character_count: int) -> str:
    """
    Estimate how long the three-layer engine takes for a text.

    The engine processes roughly 0.02 ms per character, so even a
    long message completes in a few milliseconds. This is a pure
    UX helper - it does not affect the engine itself.

    Arguments:
        character_count : length of the text to process.

    Returns:
        A short human-readable estimate like "< 1 ms".
    """
    if character_count <= 0:
        return "0 ms"

    estimated_ms = character_count * 0.02
    if estimated_ms < 1:
        return "< 1 ms"
    return f"≈ {estimated_ms:.1f} ms"
