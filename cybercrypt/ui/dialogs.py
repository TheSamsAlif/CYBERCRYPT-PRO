"""
dialogs.py
==========

Custom glassmorphism modal dialogs, replacing any basic tkinter
dialogs:

    GlassDialog.show(parent, title, message, kind, on_result)

Kinds: "success", "warning", "error", "info", "confirm".

A dim overlay covers the window, a glass card fades in with an
icon medallion, and the buttons are the same premium buttons used
everywhere else. Keyboard: Enter confirms, Escape cancels.
"""

from __future__ import annotations

import customtkinter as ctk

from cybercrypt.ui.animation import animate_color
from cybercrypt.ui.theme import COLORS, FONTS, ICONS, RADIUS
from cybercrypt.ui.widgets import primary_button, secondary_button

# kind -> (icon glyph, accent colour, medallion tint fill)
# Tint fills resolve at call time so dialogs stay correct after a
# light/dark switch.
def _style(kind: str):
    return {
        "success": (ICONS["CHECK"], COLORS["SUCCESS"], COLORS["TINT_SUCCESS"]),
        "warning": ("!", COLORS["WARNING"], COLORS["TINT_WARNING"]),
        "error":   (ICONS["ERROR"], COLORS["ERROR"], COLORS["TINT_ERROR"]),
        "info":    (ICONS["INFO"], COLORS["ACCENT"], COLORS["TINT_INFO"]),
        "confirm": (ICONS["INFO"], COLORS["ACCENT"], COLORS["TINT_INFO"]),
    }.get(kind, (ICONS["INFO"], COLORS["ACCENT"], COLORS["TINT_INFO"]))

_CARD_WIDTH = 460      # fixed dialog width (height follows content)
_MESSAGE_WRAP = 380    # message text wrapping width


class GlassDialog:
    """
    A modal glass dialog.

    Usage:
        GlassDialog.show(parent, "Clear All", "Continue?", kind="confirm",
                         on_result=lambda ok: do_something(ok))

    The dialog keeps a window grab, so the rest of the app is
    blocked until it is closed.
    """

    @staticmethod
    def show(parent, title: str, message: str, kind: str = "info",
             on_result=None):
        """
        Display a modal glass dialog.

        Arguments:
            parent    : the root window.
            title     : dialog heading.
            message   : body text.
            kind      : "success", "warning", "error", "info", "confirm".
            on_result : callback receiving True / False when a button
                        is pressed (informational dialogs pass True
                        when OK is clicked).

        Returns:
            The dialog instance (used by the app to close it
            programmatically if needed).
        """
        icon, accent, tint = _style(kind)
        is_confirm = (kind == "confirm")

        # --- Dim overlay covering the whole window ----------------------- #
        overlay = ctk.CTkFrame(parent, fg_color=COLORS["OVERLAY"],
                               corner_radius=0)
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        overlay.lift()

        # --- Glass card --------------------------------------------------- #
        card = ctk.CTkFrame(overlay, corner_radius=RADIUS["CARD"],
                            fg_color=COLORS["GLASS_INPUT"],
                            border_width=1, border_color=COLORS["BORDER_SOFT"],
                            width=_CARD_WIDTH)
        card.place(relx=0.5, rely=0.5, anchor="center")

        # Icon medallion.
        medallion = ctk.CTkFrame(card, corner_radius=30, width=60, height=60,
                                 fg_color=tint, border_width=1,
                                 border_color=accent)
        medallion.pack(pady=(26, 10))
        icon_label = ctk.CTkLabel(medallion, text=icon,
                                  font=("Segoe UI", 26, "bold"),
                                  text_color=accent)
        icon_label.place(relx=0.5, rely=0.5, anchor="center")

        # Title and message.
        title_label = ctk.CTkLabel(card, text=title,
                                   font=FONTS["HEADING"],
                                   text_color=COLORS["TEXT"])
        title_label.pack(pady=(0, 6))

        message_label = ctk.CTkLabel(
            card, text=message,
            font=FONTS["BODY"],
            text_color=COLORS["TEXT_MUTED"],
            justify="center", wraplength=_MESSAGE_WRAP,
        )
        message_label.pack(padx=28, pady=(0, 4))

        # --- Buttons ------------------------------------------------------- #
        button_row = ctk.CTkFrame(card, fg_color="transparent")
        button_row.pack(pady=(12, 24))

        def close(result: bool):
            """Animate out, release the grab and report the result."""
            try:
                overlay.grab_release()
            except Exception:
                pass

            def _cleanup():
                overlay.destroy()
                if on_result is not None:
                    on_result(result)

            animate_color(card, COLORS["GLASS_INPUT"], duration_ms=160,
                          on_finish=_cleanup)

        ok_button = primary_button(button_row, "OK",
                                   lambda: close(True))
        ok_button.pack(side="left", padx=(0, 8), pady=(0, 0))

        if is_confirm:
            cancel_button = secondary_button(button_row, "Cancel",
                                             lambda: close(False))
            cancel_button.pack(side="left", padx=(8, 0))

        # --- Interaction ---------------------------------------------------- #
        overlay.grab_set()               # block the rest of the app
        ok_button.focus_set()            # focus for keyboard users

        overlay.bind("<Escape>", lambda _e: close(False))
        if not is_confirm:
            overlay.bind("<Return>", lambda _e: close(True))

        # Gentle fade-in: the card brightens into place.
        animate_color(card, COLORS["GLASS"], duration_ms=220,
                      start_color=COLORS["GLASS_INPUT"],
                      property_name="fg_color")
        animate_color(card, COLORS["BORDER"], duration_ms=220,
                      start_color=COLORS["BORDER_SOFT"],
                      property_name="border_color")

        dialog = GlassDialog()
        dialog.overlay = overlay
        dialog.card = card
        return dialog

    # ------------------------------------------------------------------ #
    # Programmatic close (used by the smoke test and edge cases)          #
    # ------------------------------------------------------------------ #

    def close(self, result: bool = True):
        """Close the dialog as if a button had been pressed."""
        if not hasattr(self, "overlay"):
            return
        try:
            self.overlay.grab_release()
        except Exception:
            pass
        self.overlay.destroy()
        self.overlay = None
