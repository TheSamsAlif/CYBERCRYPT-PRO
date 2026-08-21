"""
background.py
=============

Renders the living glassmorphism backdrop of the application:

    * a deep navy vertical gradient (the "space" background)
    * soft glowing orbs that FLOAT very slowly across the screen

How it stays cheap (low CPU):
    - The gradient image is regenerated ONLY when the window size
      changes, and resizing is debounced (waits ~90 ms).
    - The orbs are plain canvas images; the animation loop only
      moves them a pixel or two every 50 ms with canvas.coords().
    - Orb images are cached and reused, never rebuilt.

Tkinter has no native blur, so the frosted glass is simulated:
translucent-looking panel colours + crisp light borders + these
soft glows together create the effect.
"""

from __future__ import annotations

import math
import tkinter as tk

from PIL import Image, ImageFilter, ImageTk

from cybercrypt.ui.theme import COLORS

_GRADIENT_SIZE = 400       # gradient sampled once, then stretched
_ORB_SIZE = 360            # size of each glow orb image
_ORB_BLUR = 40             # how soft the glow edges are
_MOTION_INTERVAL_MS = 50   # frame rate of the orb animation (~20 fps)
_MOTION_POLL_MS = 500      # slow poll while the window is hidden
_RESIZE_DEBOUNCE_MS = 90   # wait before rebuilding after a resize


class GlassBackground:
    """
    Draws the animated backdrop on a Tk canvas.

    Usage:
        canvas = tk.Canvas(root)
        background = GlassBackground(canvas)
        canvas.bind("<Configure>",
                    lambda e: background.request_refresh(e.width, e.height))
        background.start_motion()
    """

    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self._gradient_photo = None
        self._last_size = (0, 0)

        # Motion state.
        self._time = 0.0
        self._motion_after = None

        # Debounced resize state.
        self._pending_size = None
        self._debounce_after = None

        # Cached orb images: key (color, alpha) -> Image / PhotoImage.
        self._orb_image_cache = {}
        self._orb_photos = []      # PhotoImage per orb (keep refs)
        self._orb_items = []       # canvas item ids
        self._orb_configs = []     # motion parameters per orb

    # ------------------------------------------------------------------ #
    # Public API                                                          #
    # ------------------------------------------------------------------ #

    def request_refresh(self, width: int, height: int):
        """
        Ask for the backdrop to be rebuilt.

        The actual rebuild is debounced so that fast window resizing
        does not regenerate the gradient on every single frame.

        Arguments:
            width  : current canvas width in pixels.
            height : current canvas height in pixels.
        """
        self._pending_size = (width, height)
        if self._debounce_after is None:
            self._debounce_after = self.canvas.after(
                _RESIZE_DEBOUNCE_MS, self._do_refresh)

    def start_motion(self):
        """Start the slow floating animation of the orbs."""
        if self._motion_after is not None:
            return
        self._motion_loop()

    def stop_motion(self):
        """Stop the animation (called before the window closes)."""
        if self._motion_after is not None:
            try:
                self.canvas.after_cancel(self._motion_after)
            except tk.TclError:
                pass
            self._motion_after = None

    # ------------------------------------------------------------------ #
    # Refresh pipeline                                                    #
    # ------------------------------------------------------------------ #

    def refresh_palette(self):
        """
        Rebuild the backdrop with the current theme palette.

        Called after a light/dark switch; forces the gradient and
        orbs to regenerate even though the window size is unchanged.
        """
        width, height = self._last_size
        if width < 2 or height < 2:
            return
        self._orb_image_cache.clear()
        self._last_size = (0, 0)
        self.refresh(width, height)

    def _do_refresh(self):
        """Perform the debounced rebuild with the latest size."""
        self._debounce_after = None
        if self._pending_size is None:
            return
        width, height = self._pending_size
        self._pending_size = None
        self.refresh(width, height)

    def refresh(self, width: int, height: int):
        """
        Rebuild the backdrop image when the window size changes.

        Arguments:
            width  : current canvas width in pixels.
            height : current canvas height in pixels.
        """
        # Skip when the size did not change (avoids needless work).
        if (width, height) == self._last_size:
            return
        if width < 2 or height < 2:
            return
        self._last_size = (width, height)

        # 1) Build the gradient and draw it on the canvas.
        gradient = self._build_gradient(width, height)
        self._gradient_photo = ImageTk.PhotoImage(gradient)
        self.canvas.delete("backdrop")
        self.canvas.create_image(0, 0, anchor="nw",
                                 image=self._gradient_photo,
                                 tags="backdrop")
        self.canvas.tag_lower("backdrop")

        # 2) (Re)create the floating orbs above the gradient.
        self._rebuild_orbs(width, height)

    # ------------------------------------------------------------------ #
    # Gradient                                                            #
    # ------------------------------------------------------------------ #

    def _build_gradient(self, width: int, height: int) -> Image.Image:
        """
        Create a smooth vertical gradient from BG to BG_HIGH.

        Returns:
            An RGB image with the gradient stretched to the window size.
        """
        start = self._rgb(COLORS["BG"])
        end = self._rgb(COLORS["BG_HIGH"])

        column = Image.new("RGB", (1, _GRADIENT_SIZE))
        for row in range(_GRADIENT_SIZE):
            factor = row / (_GRADIENT_SIZE - 1)
            color = tuple(
                round(start[i] + (end[i] - start[i]) * factor)
                for i in range(3)
            )
            column.putpixel((0, row), color)

        return column.resize((width, height))

    # ------------------------------------------------------------------ #
    # Floating orbs                                                       #
    # ------------------------------------------------------------------ #

    def _rebuild_orbs(self, width: int, height: int):
        """Create the orb canvas items at their base positions."""
        # Remove old orb items (their photo refs are dropped as well).
        for item in self._orb_items:
            self.canvas.delete(item)
        self._orb_items = []
        self._orb_photos = []
        self._orb_configs = []

        base_positions = [
            (width * 0.06, height * 0.10, COLORS["ORB_1"], 64, 12, 0.028, 0.0),
            (width * 0.94, height * 0.88, COLORS["ORB_2"], 52, 16, 0.022, math.pi),
            (width * 0.86, height * 0.18, COLORS["ORB_3"], 42, 10, 0.033, math.pi / 2),
        ]
        # (center_x, center_y, color, alpha, amplitude, speed, phase)

        for center_x, center_y, color, alpha, amplitude, speed, phase in base_positions:
            orb_image = self._get_orb_image(color, alpha)
            photo = ImageTk.PhotoImage(orb_image)
            item = self.canvas.create_image(center_x, center_y,
                                            image=photo, tags="orb")
            self._orb_photos.append(photo)
            self._orb_items.append(item)
            self._orb_configs.append({
                "cx": center_x,
                "cy": center_y,
                "amplitude": amplitude,
                "speed": speed,
                "phase": phase,
            })

    def _get_orb_image(self, color: str, alpha: int) -> Image.Image:
        """
        Return a cached soft glow orb image, creating it once.

        Arguments:
            color : hex colour of the glow.
            alpha : maximum opacity of the glow centre (0..255).

        Returns:
            A square RGBA image fading to transparent at the edges.
        """
        key = (color, alpha)
        if key not in self._orb_image_cache:
            self._orb_image_cache[key] = self._make_orb(color, alpha)
        return self._orb_image_cache[key]

    def _make_orb(self, color: str, alpha: int) -> Image.Image:
        """
        Create one soft radial glow as an RGBA image.

        Arguments:
            color : hex colour of the glow.
            alpha : maximum opacity of the glow centre (0..255).

        Returns:
            A square RGBA image that fades to transparent.
        """
        # A 1-pixel column whose brightness fades from alpha to 0.
        column = Image.new("L", (1, _ORB_SIZE))
        for row in range(_ORB_SIZE):
            fade = alpha * (1 - row / _ORB_SIZE)
            column.putpixel((0, row), int(fade))

        # Stretch the column into a smooth radial disc.
        disc = column.resize((_ORB_SIZE, _ORB_SIZE))

        # Give the disc the requested colour and use it as the alpha.
        orb = Image.new("RGBA", (_ORB_SIZE, _ORB_SIZE), self._rgb(color))
        orb.putalpha(disc)

        # Blur it further for a really soft, dreamy glow.
        return orb.filter(ImageFilter.GaussianBlur(_ORB_BLUR))

    # ------------------------------------------------------------------ #
    # Motion loop                                                         #
    # ------------------------------------------------------------------ #

    def _motion_loop(self):
        """
        One frame of the animation: drift every orb along a slow
        sine path around its base position, then schedule the next.

        While the window is minimized or hidden the loop only polls
        slowly, so a hidden app costs almost no CPU.
        """
        if not self.canvas.winfo_viewable():
            try:
                self._motion_after = self.canvas.after(
                    _MOTION_POLL_MS, self._motion_loop)
            except tk.TclError:
                self._motion_after = None
            return

        self._time += 1
        for item, config in zip(self._orb_items, self._orb_configs):
            # Very slow oscillation: x and y drift a few pixels.
            drift_x = math.sin(self._time * config["speed"] + config["phase"])
            drift_y = math.cos(self._time * config["speed"] * 0.7
                               + config["phase"])
            new_x = config["cx"] + drift_x * config["amplitude"]
            new_y = config["cy"] + drift_y * config["amplitude"]
            try:
                self.canvas.coords(item, new_x, new_y)
            except tk.TclError:
                return  # canvas is gone; stop quietly

        try:
            self._motion_after = self.canvas.after(
                _MOTION_INTERVAL_MS, self._motion_loop)
        except tk.TclError:
            self._motion_after = None

    # ------------------------------------------------------------------ #
    # Utilities                                                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _rgb(hex_color: str) -> tuple:
        """Convert a hex colour into an (r, g, b) tuple."""
        value = hex_color.lstrip("#")
        return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))
