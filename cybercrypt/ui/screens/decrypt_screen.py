"""
decrypt_screen.py
=================

The decryption workspace - the mirror image of the encrypt screen
(Phase 3 educational flow):

    left  -> glass input card, the live pipeline panel and the
             glass output card
    right -> the keys panel, the step details panel and the
             Decrypt / Clear actions

Decrypting now *shows* the reverse process:

    Cipher Text
        ↓ Random XOR removed    (intermediate text revealed)
        ↓ Vigenere removed      (intermediate text revealed)
        ↓ Caesar removed        (original message revealed)
        ✓ Decryption complete

The keys from the last encryption are pre-filled automatically.
If any key is wrong, the output is garbage - expected behaviour
in cryptography, and a great thing to demonstrate.
"""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from cybercrypt.ui.panels import PipelinePanel, StepDetailsPanel, SummaryPopup
from cybercrypt.ui.screens.base_screen import BaseScreen
from cybercrypt.ui.theme import COLORS, FONTS, ICONS, RADIUS
from cybercrypt.ui.tooltip import bind_tooltip
from cybercrypt.ui.visualizer import (
    VisualRunner,
    build_decrypt_steps,
    format_seconds,
)
from cybercrypt.ui.widgets import (
    KeysPanel,
    Toast,
    glass_panel,
    primary_button,
    secondary_button,
)
from cybercrypt.utils.helpers import format_estimated_time

_FIELD_RADIUS = RADIUS["FIELD"]

# Pipeline captions: layer name, medallion glyph, hover explanation.
_PIPELINE_LAYERS = (
    "Random XOR Layer",
    "Vigenere Cipher",
    "Caesar Cipher",
)
_PIPELINE_ICONS = ("X", "V", "A")
_PIPELINE_TOOLTIPS = (
    "Remove the XOR keystream first - it was the last layer applied.",
    "Reverse the keyword shifts of the second layer.",
    "Shift every character back to its original position.",
)


class DecryptScreen(BaseScreen):
    """Decryption workspace with live layer-by-layer visualization."""

    # ------------------------------------------------------------------ #
    # Construction                                                        #
    # ------------------------------------------------------------------ #

    def _build_widgets(self):
        self._busy = False
        self.runner = VisualRunner(
            self, on_step=self._on_step, on_done=self._on_done)

        self._build_header()

        # Natural scrollable flow: content grows and scrolls, never clips.
        self.scroll = self._page_scroll()
        self._body = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self._body.pack(fill="both", expand=True, padx=2, pady=(0, 6))

        self._build_columns()
        self._build_input_card()
        self._build_pipeline()
        self._build_output_card()
        self._build_keys_panel()
        self._build_details_panel()
        self._build_actions()
        self._bind_mousewheel_recursive(self.scroll, self.scroll._parent_canvas)

    def _build_columns(self):
        """Left column stretches; right sidebar keeps a fixed width so
        it never collapses. Both remain visible at every window size.

        The body uses a two-column GRID (the customtkinter equivalent
        of `minmax(0,1fr) + flex-shrink:0`):
            column 0 (main)  -> weight=1  : grows / shrinks to fit
            column 1 (aside) -> weight=0  : fixed 360-420px, never
                                shrinks below its configured width.
        """
        self._body.grid_columnconfigure(0, weight=1)
        self._body.grid_columnconfigure(1, weight=0)

        self._left = ctk.CTkFrame(self._body, fg_color="transparent")
        self._left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self._right = ctk.CTkFrame(self._body, fg_color="transparent")
        self._right.configure(width=self._sidebar_width())
        self._right.grid_propagate(False)
        self._right.grid(row=0, column=1, sticky="n", padx=(6, 0))

        self.bind("<Configure>", self._on_screen_resize, add="+")

    def _sidebar_width(self) -> int:
        """
        Responsive fixed width for the right sidebar (flex-shrink:0).
        Desktop windows get the widest 420px, smaller windows taper to
        360px - but it never collapses below the minimum.

        Returns:
            A width in the 360..420 px range.
        """
        width = self.safe_width()
        if width >= 1500:
            return 420
        if width >= 1200:
            return 390
        if width >= 1050:
            return 375
        return 360

    def _on_screen_resize(self, _event=None):
        """Keep the sidebar width + textarea heights responsive."""
        try:
            self._right.configure(width=self._sidebar_width())
            self._apply_textarea_heights()
        except (tk.TclError, AttributeError):
            pass

    def _build_header(self):
        """Title and subtitle at the grid position (shared by every
        screen - see theme.SPACING)."""
        self._page_header(
            "Decrypt Text",
            "Watch the three layers being removed in reverse order, "
            "one step at a time.")

    def _build_input_card(self):
        """Left column, top: the glass input card."""
        card = glass_panel(self._left)
        card.pack(fill="x", pady=(0, 8))

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(header, text="Cipher Text", font=FONTS["SUBHEADING"],
                     text_color=COLORS["TEXT"]).pack(side="left")
        self.counter_label = ctk.CTkLabel(
            header, text="0 characters", font=FONTS["MICRO"],
            text_color=COLORS["TEXT_FAINT"])
        self.counter_label.pack(side="right")

        # Responsive textarea height (re-applied on every resize).
        self.input_box = ctk.CTkTextbox(
            card,
            corner_radius=_FIELD_RADIUS,
            fg_color=COLORS["GLASS_INPUT"],
            border_width=1,
            border_color=COLORS["BORDER"],
            text_color=COLORS["TEXT"],
            font=FONTS["MONO"],
            wrap="word",
            scrollbar_button_color=COLORS["BORDER"],
            scrollbar_button_hover_color=COLORS["ACCENT"],
        )
        self.input_box.pack(fill="x", padx=16)
        self.input_box.bind("<KeyRelease>", self._update_metrics)
        self._set_cursor_color(self.input_box)

        self.time_label = ctk.CTkLabel(
            card, text="Estimated time: 0 ms", font=FONTS["MICRO"],
            text_color=COLORS["TEXT_FAINT"], anchor="w")
        self.time_label.pack(anchor="w", padx=16, pady=(8, 14))

    def _build_pipeline(self):
        """Left column, middle: the live layer pipeline panel."""
        self.layers = PipelinePanel(
            self._left,
            layers=_PIPELINE_LAYERS,
            icons=_PIPELINE_ICONS,
            title="Decryption Pipeline",
            tooltips=_PIPELINE_TOOLTIPS,
        )
        self.layers.pack(fill="x", pady=(0, 8))

    def _build_output_card(self):
        """Left column, bottom: the glass output card."""
        card = glass_panel(self._left)
        card.pack(fill="x", pady=(0, 8))

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(header, text="Decrypted Text",
                     font=FONTS["SUBHEADING"],
                     text_color=COLORS["TEXT"]).pack(side="left")

        self._copy_button = secondary_button(
            header, f"{ICONS['COPY']}  Copy", self._copy_result, height=30)
        self._copy_button.pack(side="right")
        bind_tooltip(self._copy_button,
                     "Copy the recovered message to the clipboard.")

        # Responsive textarea height (re-applied on every resize).
        self.output_box = ctk.CTkTextbox(
            card,
            corner_radius=_FIELD_RADIUS,
            fg_color=COLORS["GLASS_INPUT"],
            border_width=1,
            border_color=COLORS["BORDER"],
            text_color=COLORS["SUCCESS"],
            font=FONTS["BODY"],
            wrap="word",
            scrollbar_button_color=COLORS["BORDER"],
            scrollbar_button_hover_color=COLORS["ACCENT"],
        )
        self.output_box.pack(fill="x", padx=16, pady=(0, 16))
        self.output_box.configure(state="disabled")

    def _build_keys_panel(self):
        """Right column, top: the three decryption keys."""
        self.keys_panel = KeysPanel(
            self._right,
            title=f"{ICONS['DECRYPT']}  Decryption Keys",
            subtitle="Use the exact keys from the encryption step.",
        )
        self.keys_panel.pack(fill="x", pady=(0, 8))
        bind_tooltip(
            self.keys_panel.auto_button,
            "Auto-fill the same random keys that were used for encryption.")

    def _build_details_panel(self):
        """Right column, middle: the live step details card."""
        self.details = StepDetailsPanel(self._right)
        self.details.pack(fill="x", pady=(0, 8))

    def _build_actions(self):
        """Right column, bottom: Decrypt and Clear actions."""
        row = ctk.CTkFrame(self._right, fg_color="transparent")
        row.pack(fill="x", pady=(0, 6))

        self.decrypt_button = primary_button(
            row, f"{ICONS['DECRYPT']}  Decrypt", self._decrypt, height=44)
        self.decrypt_button.pack(side="left", fill="both", expand=True,
                                 padx=(0, 4))
        bind_tooltip(self.decrypt_button,
                     "Remove all three layers and watch them live.")

        clear_button = secondary_button(
            row, f"{ICONS['CLEAR']}  Clear", self._confirm_clear, height=44)
        clear_button.pack(side="left", fill="both", expand=True,
                          padx=(4, 0))
        bind_tooltip(clear_button, "Clear the input, output and keys.")

    # ------------------------------------------------------------------ #
    # Actions                                                             #
    # ------------------------------------------------------------------ #

    def _decrypt(self):
        """
        Validate the input, run the three layers in reverse (instantly,
        in the background) and then play the recovery back layer by
        layer.
        """
        if self._busy:
            return

        cipher_text = self.input_box.get("1.0", "end-1c").strip()

        # --- Validation (beautiful glass error dialogs) ------------------- #
        if not cipher_text:
            self.app.show_dialog(
                "Empty Input",
                "Please paste some cipher text before decrypting.",
                kind="error",
            )
            return
        try:
            keys = self.keys_panel.get_keys()
        except ValueError as error:
            self.app.show_dialog("Invalid Keys", str(error), kind="error")
            return

        # --- Compute all layers once (fast, off the animation path) ------- #
        try:
            steps = build_decrypt_steps(
                cipher_text,
                shift=keys["shift"],
                vigenere_key=keys["vigenere_key"],
                seed=keys["seed"],
            )
        except Exception:
            self.app.show_dialog(
                "Unexpected Error",
                "Decryption could not be completed. Please check your "
                "cipher text and keys.",
                kind="error",
            )
            return

        # --- Start the visual playback ------------------------------------ #
        self._busy = True
        self.decrypt_button.configure(state="disabled",
                                      text="Decrypting...")
        self.app.set_status("Decrypting...", kind="busy")

        self.layers.reset_all()
        self.details.reset()
        self.layers.set_status_text("Processing...")

        self._run_char_count = len(cipher_text)
        self.runner.run(steps)

    def _on_step(self, index: int, state: str, step: dict):
        """
        One layer changed state: update the pipeline, the progress
        bar and the step details card.
        """
        if step["key"] == "complete":
            self.layers.set_status_text("Completed")
            self.layers.set_progress(3, "done")
            self.details.show_step(step, state)
            return

        self.layers.set_state(index, state)
        self.layers.set_progress(index, state)
        self.details.show_step(step, state)

    def _on_done(self, steps: list):
        """Reveal the recovered message, update stats, show the summary."""
        result = steps[-1]["output"]

        # Reveal the result.
        self._set_output(result)
        self.layers.set_status_text("Completed")
        self.decrypt_button.configure(state="normal")
        self.decrypt_button.configure(text=f"{ICONS['DECRYPT']}  Decrypt")
        self._busy = False

        # Update session statistics.
        self.app.session.decrypt_count += 1
        self.app.session.processed_chars += self._run_char_count

        # Remember the runtime for the next Analysis report (the
        # Performance card shows decryption time alongside encryption).
        total_time = sum(step.get("elapsed", 0.0) for step in steps[:-1])
        self.app.session.last_decrypt_time = total_time

        self.app.set_status("Completed", kind="success")
        Toast.show(self.app, "Decrypted successfully.", kind="success")

        # Premium summary popup (auto-dismisses).
        SummaryPopup.show(
            self.app,
            "Decryption Completed Successfully",
            [
                ("Recovered Characters", str(len(result))),
                ("Processing Time", format_seconds(total_time)),
                ("Layer Count", "3"),
                ("Overall Status", "Success"),
            ],
            kind="success",
        )

    def _copy_result(self):
        """Copy the decrypted output to the system clipboard."""
        output = self.output_box.get("1.0", "end-1c")
        if not output:
            Toast.show(self.app, "Nothing to copy yet.", kind="warning")
            return
        self.app.clipboard_clear()
        self.app.clipboard_append(output)
        self.app.set_status("Copied", kind="success")
        Toast.show(self.app, "Copied to clipboard.", kind="success")

    def _confirm_clear(self):
        """Ask before clearing all fields (glass confirmation dialog)."""
        self.app.show_dialog(
            "Clear All",
            "This will clear the input, output and key fields. Continue?",
            kind="confirm",
            on_result=lambda ok: self._clear_all() if ok else None,
        )

    def _clear_all(self):
        """Clear input, output and the key fields."""
        self.runner.cancel()
        self.input_box.delete("1.0", "end")
        self._set_output("")
        self.keys_panel.shift_var.set("")
        self.keys_panel.key_var.set("")
        self.keys_panel.seed_var.set("")
        self.layers.reset_all()
        self.details.reset()
        self._update_metrics()
        self.app.set_status("Cleared", kind="idle")

    # ------------------------------------------------------------------ #
    # Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _set_output(self, text: str):
        """Replace the output area contents (keeps it read-only)."""
        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.insert("1.0", text)
        self.output_box.configure(state="disabled")

    def _update_metrics(self, _event=None):
        """Refresh the character counter and the time estimate."""
        count = len(self.input_box.get("1.0", "end-1c"))
        self.counter_label.configure(text=f"{count} characters")
        self.time_label.configure(
            text=f"Estimated time: {format_estimated_time(count)}")

    @staticmethod
    def _set_cursor_color(textbox):
        """Give the typing cursor the accent colour."""
        try:
            textbox._textbox.configure(insertbackground=COLORS["ACCENT"])
        except (AttributeError, tk.TclError):
            pass  # older CTk versions: cursor stays default

    def _apply_textarea_heights(self):
        """
        Responsive textarea heights (desktop comfortable, laptop
        smaller, tablet compact) instead of a single fixed value.

        Uses the scroll container height (not the full screen height)
        so textareas fit within the actual visible area.
        """
        # Use the scroll frame height for more accurate sizing.
        try:
            height = self.scroll.winfo_height()
        except Exception:
            height = self.safe_height()
        if height >= 700:
            input_h, output_h = 120, 80
        elif height >= 560:
            input_h, output_h = 100, 70
        else:
            input_h, output_h = 80, 60
        try:
            self.input_box.configure(height=input_h)
            self.output_box.configure(height=output_h)
        except (AttributeError, tk.TclError):
            pass

    # ------------------------------------------------------------------ #
    # Screen lifecycle                                                    #
    # ------------------------------------------------------------------ #

    def on_show(self):
        """Pre-fill keys from the last encryption and focus the input."""
        self.update_idletasks()
        if self.runner.is_active:
            self.runner.cancel()
        if self.app.session.last_keys and not self.keys_panel.key_var.get():
            self.keys_panel.set_keys(self.app.session.last_keys)
        self._apply_textarea_heights()
        self._right.configure(width=self._sidebar_width())
        self.input_box.focus_set()
        self._bind_mousewheel_recursive(self.scroll, self.scroll._parent_canvas)

    def on_shortcut(self):
        """Ctrl+Enter triggers the decryption."""
        self._decrypt()
