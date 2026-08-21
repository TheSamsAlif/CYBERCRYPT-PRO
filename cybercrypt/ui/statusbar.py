"""
statusbar.py
============

The professional bottom status bar.

Shows a status dot + message on the left (Ready, Encrypting...,
Completed, Copied, ...) and permanent context info on the right.
"""

from __future__ import annotations

import customtkinter as ctk

from cybercrypt import __version__
from cybercrypt.ui.theme import COLORS, FONTS, ICONS, RADIUS

# Status kinds -> dot colour.
_STATUS_COLORS = {
    "idle":    COLORS["TEXT_FAINT"],
    "ready":   COLORS["SUCCESS"],
    "busy":    COLORS["ACCENT"],
    "success": COLORS["SUCCESS"],
    "warning": COLORS["WARNING"],
    "error":   COLORS["ERROR"],
}


class StatusBar(ctk.CTkFrame):
    """
    A slim glass strip pinned to the bottom of the window.

    Usage:
        status_bar = StatusBar(parent)
        status_bar.set_status("Encrypting...", kind="busy")
    """

    def __init__(self, parent):
        super().__init__(
            parent,
            corner_radius=RADIUS["PANEL"],
            fg_color=COLORS["GLASS"],
            border_width=1,
            border_color=COLORS["BORDER_SOFT"],
        )

        # --- Left: status dot + message --- #
        self.dot = ctk.CTkLabel(self, text=ICONS["DOT"],
                                font=("Segoe UI", 9),
                                text_color=COLORS["TEXT_FAINT"])
        self.dot.pack(side="left", padx=(16, 6), pady=6)

        self.label = ctk.CTkLabel(self, text="Ready",
                                  font=FONTS["SMALL"],
                                  text_color=COLORS["TEXT_MUTED"])
        self.label.pack(side="left", pady=6)

        # --- Right: permanent context info --- #
        self.info = ctk.CTkLabel(
            self,
            text=f"Educational Demo   ·   v{__version__}   ·   Fully Offline",
            font=FONTS["MICRO"],
            text_color=COLORS["TEXT_FAINT"],
        )
        self.info.pack(side="right", padx=16, pady=6)

    def set_status(self, text: str, kind: str = "idle"):
        """
        Update the status message and its colour.

        Arguments:
            text : the message (e.g. "Encrypting...", "Completed").
            kind : "idle", "ready", "busy", "success", "warning",
                   "error" - controls the dot colour.
        """
        color = _STATUS_COLORS.get(kind, COLORS["TEXT_FAINT"])
        self.dot.configure(text_color=color)
        self.label.configure(text=text)
