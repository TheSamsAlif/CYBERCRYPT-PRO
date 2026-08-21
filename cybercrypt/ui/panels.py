"""
panels.py
=========

Phase 3 : the educational panels of the live visualization.

    PipelinePanel   -> glass card showing every layer as a vertical
                       flow: icon, name, live status dot + the
                       segmented progress bar at the bottom.
    StepDetailsPanel-> glass card with the current step's algorithm
                       name, purpose, advantages, limitations,
                       status, processing time and output preview.
    SummaryPopup    -> premium success popup with the operation
                       summary; disappears automatically.

All visual states are animated with the existing animate_color()
helper, and every animation is scheduled with after(), so the UI
never blocks.
"""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from cybercrypt.ui.animation import animate_color
from cybercrypt.ui.theme import COLORS, FONTS, ICONS, RADIUS
from cybercrypt.ui.tooltip import bind_tooltip
from cybercrypt.ui.visualizer import format_seconds, preview_text

# ---------------------------------------------------------------------- #
# Colour presets per pipeline state                                       #
# ---------------------------------------------------------------------- #

_STATE_STYLE = {
    # medallion fill, medallion border, icon colour, dot, word
    "pending": (COLORS["GLASS_INPUT"], COLORS["BORDER_SOFT"],
                COLORS["TEXT_FAINT"], COLORS["BORDER_SOFT"], COLORS["TEXT_FAINT"]),
    "running": (COLORS["PRIMARY_DEEP"], COLORS["ACCENT"],
                COLORS["ACCENT"], COLORS["ACCENT"], COLORS["ACCENT"]),
    "done":    (COLORS["TINT_SUCCESS"], COLORS["SUCCESS"],
                COLORS["SUCCESS"], COLORS["SUCCESS"], COLORS["SUCCESS"]),
    "error":   (COLORS["TINT_ERROR"], COLORS["ERROR"],
                COLORS["ERROR"], COLORS["ERROR"], COLORS["ERROR"]),
}

_STATUS_WORDS = {
    "pending": "Idle",
    "running": "Running",
    "done":    "Done",
    "error":   "Error",
}


# ---------------------------------------------------------------------- #
# Pipeline panel                                                          #
# ---------------------------------------------------------------------- #

class PipelinePanel(ctk.CTkFrame):
    """
    The vertical "how encryption works" flow:

        [icon] Caesar Cipher        ● Running
                     ↓
        [icon] Vigenere Cipher      ● Done
                     ↓
        [icon] Random XOR Layer     ● Idle

    with a segmented progress bar (3 layers + Complete) at the bottom.

    The state API matches the old LayerIndicator so existing code
    keeps working:
        set_state(index, state)   ("pending" / "running" / "done" / "error")
        set_status_text(text)
        reset_all()
    """

    def __init__(self, parent, layers: tuple = ("Caesar", "Vigenere", "XOR"),
                 icons: tuple = ("A", "V", "X"),
                 title: str = "Encryption Pipeline",
                 tooltips: tuple = ()):
        super().__init__(
            parent,
            corner_radius=RADIUS["CARD"],
            fg_color=COLORS["GLASS"],
            border_width=1,
            border_color=COLORS["BORDER"],
        )
        self._rows = []
        self._segments = []
        self._pulse_token = 0
        self._build(layers, icons, title, tooltips)

    # ------------------------------------------------------------------ #
    # Construction                                                        #
    # ------------------------------------------------------------------ #

    def _build(self, layers, icons, title, tooltips):
        """Create the header, the layer rows and the progress bar."""
        # --- Header ------------------------------------------------------ #
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(6, 2))

        heading = ctk.CTkLabel(header, text=title,
                               font=FONTS["SUBHEADING"],
                               text_color=COLORS["TEXT"])
        heading.pack(side="left")

        self.status_label = ctk.CTkLabel(header, text="Idle",
                                         font=FONTS["SMALL"],
                                         text_color=COLORS["TEXT_FAINT"])
        self.status_label.pack(side="right", padx=(8, 4))

        # --- Layer rows --------------------------------------------------- #
        for index, (name, icon) in enumerate(zip(layers, icons)):
            tooltip = tooltips[index] if index < len(tooltips) else None
            row = self._build_row(name, icon, tooltip)
            row["frame"].pack(fill="x", padx=14, pady=1)
            self._rows.append(row)

            if index < len(layers) - 1:
                arrow = ctk.CTkLabel(self, text=ICONS["ARROW"],
                                     font=FONTS["SMALL"],
                                     text_color=COLORS["TEXT_FAINT"])
                arrow.pack(pady=0)

        # --- Segmented progress bar --------------------------------------- #
        progress = ctk.CTkFrame(self, fg_color="transparent")
        progress.pack(fill="x", padx=14, pady=(4, 8))
        # Uniform weighting: every segment shares the available width and
        # never forces the parent to a huge requested width.
        progress.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="seg")

        for label in ("Layer 1", "Layer 2", "Layer 3", "Complete"):
            segment = ctk.CTkFrame(progress,
                                   corner_radius=RADIUS["CHIP"],
                                   fg_color=COLORS["GLASS_INPUT"],
                                   border_width=1,
                                   border_color=COLORS["BORDER_SOFT"],
                                   height=12)
            segment.grid(row=0, column=len(self._segments), sticky="ew",
                         padx=(0, 6 if label != "Complete" else 0))
            caption = ctk.CTkLabel(segment, text=label, font=FONTS["MICRO"],
                                   text_color=COLORS["TEXT_FAINT"])
            caption.place(relx=0.5, rely=0.5, anchor="center")
            self._segments.append(segment)

    def _build_row(self, name: str, icon: str, tooltip: str = None) -> dict:
        """Create one layer row: medallion, name, dot and status word."""
        row = ctk.CTkFrame(self, fg_color="transparent")

        medallion = ctk.CTkFrame(row, corner_radius=13, width=26, height=26,
                                 fg_color=COLORS["GLASS_INPUT"],
                                 border_width=1,
                                 border_color=COLORS["BORDER_SOFT"])
        medallion.pack(side="left", pady=1)
        medallion.pack_propagate(False)

        icon_label = ctk.CTkLabel(medallion, text=icon,
                                  font=("Segoe UI", 11, "bold"),
                                  text_color=COLORS["TEXT_FAINT"])
        icon_label.place(relx=0.5, rely=0.5, anchor="center")

        name_label = ctk.CTkLabel(row, text=name, font=FONTS["BODY"],
                                  text_color=COLORS["TEXT"])
        name_label.pack(side="left", padx=(10, 0))

        state_word = ctk.CTkLabel(row, text="Idle", font=FONTS["MICRO"],
                                  text_color=COLORS["TEXT_FAINT"])
        state_word.pack(side="right", padx=(0, 6))

        dot = ctk.CTkLabel(row, text=ICONS["DOT"], font=("Segoe UI", 8),
                           text_color=COLORS["BORDER_SOFT"])
        dot.pack(side="right", padx=(0, 4))

        # A tooltip on the row fires even when the pointer is over
        # the children, because every child forwards the same text.
        if tooltip:
            for child in (row, medallion, icon_label, name_label,
                          state_word, dot):
                bind_tooltip(child, tooltip)

        return {"frame": row, "medallion": medallion, "icon": icon_label,
                "dot": dot, "word": state_word}

    # ------------------------------------------------------------------ #
    # State API                                                           #
    # ------------------------------------------------------------------ #

    def set_state(self, index: int, state: str):
        """
        Set one layer's visual state.

        Arguments:
            index : which row (0, 1, 2).
            state : "pending", "running", "done" or "error".
        """
        if index >= len(self._rows):
            return
        if state not in _STATE_STYLE:
            state = "pending"

        fill, border, icon_color, dot_color, word_color = _STATE_STYLE[state]
        row = self._rows[index]

        # Animate the medallion colours smoothly.
        animate_color(row["medallion"], fill, duration_ms=220,
                      property_name="fg_color")
        animate_color(row["medallion"], border, duration_ms=220,
                      property_name="border_color")
        row["icon"].configure(text_color=icon_color)

        # The running layer pulses; other states stop any pulse.
        self._pulse_token += 1
        if state == "running":
            self._pulse(index, self._pulse_token)

        row["dot"].configure(text_color=dot_color)
        row["word"].configure(text=_STATUS_WORDS[state],
                              text_color=word_color)

    def set_status_text(self, text: str):
        """Update the overall status word on the right of the header."""
        self.status_label.configure(text=text)

    def reset_all(self):
        """Return every row and progress segment to the idle state."""
        self._pulse_token += 1
        for index in range(len(self._rows)):
            self.set_state(index, "pending")
        for index in range(len(self._segments)):
            self._set_segment(index, "pending")
        self.set_status_text("Idle")

    # ------------------------------------------------------------------ #
    # Progress segments                                                   #
    # ------------------------------------------------------------------ #

    def set_progress(self, index: int, state: str):
        """
        Set one segment of the progress bar.

        Arguments:
            index : 0..2 for the layers, 3 for "Complete".
            state : "pending", "running" or "done".
        """
        if 0 <= index < len(self._segments):
            self._set_segment(index, state)

    def _set_segment(self, index: int, state: str):
        """Animate one progress segment's fill and border."""
        segment = self._segments[index]
        if state == "done":
            animate_color(segment, COLORS["TINT_SUCCESS"], duration_ms=260,
                          property_name="fg_color")
            animate_color(segment, COLORS["SUCCESS"], duration_ms=260,
                          property_name="border_color")
        elif state == "running":
            animate_color(segment, COLORS["PRIMARY_DEEP"], duration_ms=260,
                          property_name="fg_color")
            animate_color(segment, COLORS["ACCENT"], duration_ms=260,
                          property_name="border_color")
        else:
            animate_color(segment, COLORS["GLASS_INPUT"], duration_ms=220,
                          property_name="fg_color")
            animate_color(segment, COLORS["BORDER_SOFT"], duration_ms=220,
                          property_name="border_color")

    # ------------------------------------------------------------------ #
    # Pulse animation (running layer)                                     #
    # ------------------------------------------------------------------ #

    def _pulse(self, index: int, token: int):
        """
        Softly blink the running layer's dot.

        Arguments:
            index : the running row.
            token : cancels older pulses when a new state is set.
        """
        if index >= len(self._rows):
            return
        dot = self._rows[index]["dot"]

        def _blink(step: int):
            if token != self._pulse_token:
                return
            try:
                color = (COLORS["ACCENT"] if step % 2 == 0
                         else COLORS["TEXT_FAINT"])
                dot.configure(text_color=color)
            except tk.TclError:
                return
            self.after(260, lambda: _blink(step + 1))

        _blink(0)


# ---------------------------------------------------------------------- #
# Step details panel                                                      #
# ---------------------------------------------------------------------- #

class StepDetailsPanel(ctk.CTkFrame):
    """
    The "what is happening right now" card.

    Shows the current layer's:
        * algorithm name and tagline
        * live status word (Idle / Running / Done)
        * purpose, advantages and limitations (one line each)
        * processing time
        * a preview of the intermediate output

    Usage:
        details = StepDetailsPanel(parent)
        details.show_step(step_dict, "running")
        details.reset()
    """

    def __init__(self, parent):
        super().__init__(
            parent,
            corner_radius=RADIUS["CARD"],
            fg_color=COLORS["GLASS"],
            border_width=1,
            border_color=COLORS["BORDER"],
        )
        self._build()

    # ------------------------------------------------------------------ #
    # Construction                                                        #
    # ------------------------------------------------------------------ #

    def _build(self):
        """Create every label of the card.

        The whole card uses a natural (pack) flow so its height grows
        with the text - no fixed height, no overlapping text.
        """
        pad = 14

        # Header: title (left) + status (right).
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=pad, pady=(10, 2))
        heading = ctk.CTkLabel(header, text="Step Details",
                               font=FONTS["SUBHEADING"],
                               text_color=COLORS["TEXT"])
        heading.pack(side="left")
        self.status_label = ctk.CTkLabel(header, text="Status: Idle",
                                         font=FONTS["SMALL"],
                                         text_color=COLORS["TEXT_FAINT"])
        self.status_label.pack(side="right")

        # Algorithm name + tagline.
        self.name_label = ctk.CTkLabel(
            self, text="Waiting", font=FONTS["HEADING"],
            text_color=COLORS["ACCENT"], anchor="w", justify="left")
        self.name_label.pack(fill="x", padx=pad)

        self.tagline_label = ctk.CTkLabel(
            self, text="", font=FONTS["MICRO"],
            text_color=COLORS["TEXT_FAINT"], anchor="w", justify="left")
        self.tagline_label.pack(fill="x", padx=pad, pady=(0, 2))

        self.time_label = ctk.CTkLabel(
            self, text="", font=FONTS["MONO_SMALL"],
            text_color=COLORS["TEXT_FAINT"], anchor="w")
        self.time_label.pack(fill="x", padx=pad, pady=(0, 2))

        self._divider()

        # Purpose / advantages / limitations (one after another).
        self.purpose_label = self._section("Purpose", COLORS["TEXT"], pad)
        self.advantages_label = self._section("Advantages",
                                               COLORS["SUCCESS"], pad)
        self.limitations_label = self._section("Limitations",
                                               COLORS["WARNING"], pad)

        self._divider()

        # Output preview at the bottom.
        preview_caption = ctk.CTkLabel(self, text="Output Preview",
                                       font=FONTS["MICRO"],
                                       text_color=COLORS["TEXT_FAINT"],
                                       anchor="w")
        preview_caption.pack(fill="x", padx=pad, pady=(2, 0))

        self.preview_label = ctk.CTkLabel(
            self, text="—", font=FONTS["MONO_SMALL"],
            text_color=COLORS["TEXT_MUTED"], justify="left", anchor="w",
            wraplength=330)
        self.preview_label.pack(fill="x", padx=(pad + 8, pad),
                                pady=(0, 10))

    def _divider(self):
        """A thin horizontal rule."""
        divider = ctk.CTkFrame(self, height=1, fg_color=COLORS["BORDER_SOFT"],
                               corner_radius=0)
        divider.pack(fill="x", padx=14, pady=(1, 2))

    def _section(self, caption: str, color: str, pad: int) -> ctk.CTkLabel:
        """Create a caption + text pair using natural flow."""
        ctk.CTkLabel(self, text=caption, font=FONTS["MICRO"],
                     text_color=color, anchor="w").pack(
            fill="x", padx=pad, pady=(1, 0))
        text_label = ctk.CTkLabel(
            self, text="", font=FONTS["SMALL"],
            text_color=COLORS["TEXT_MUTED"], justify="left", anchor="w",
            wraplength=330)
        text_label.pack(fill="x", padx=(pad + 8, pad), pady=(0, 0))
        return text_label

    # ------------------------------------------------------------------ #
    # State API                                                           #
    # ------------------------------------------------------------------ #

    def show_step(self, step: dict, state: str = "done"):
        """
        Fill the card with one step's information.

        Arguments:
            step  : a step dictionary from visualizer.build_*_steps().
            state : "running" or "done".
        """
        is_running = (state == "running")

        self.name_label.configure(text=step["title"])

        direction = step.get("direction", "")
        if direction == "applied":
            action_text = "being applied to the text"
        elif direction == "removed":
            action_text = "being removed from the text"
        else:
            action_text = "finished"
        self.tagline_label.configure(
            text=f"{step.get('tagline', '')} · {action_text}")

        status_word = "Running..." if is_running else "Completed"
        status_color = COLORS["ACCENT"] if is_running else COLORS["SUCCESS"]
        self.status_label.configure(text=f"Status: {status_word}",
                                    text_color=status_color)

        if step.get("elapsed", 0.0) > 0:
            self.time_label.configure(
                text=f"{format_seconds(step['elapsed'])}")
        else:
            self.time_label.configure(text="")

        self.purpose_label.configure(text=step.get("purpose", ""))
        self.advantages_label.configure(text=step.get("advantages", ""))
        self.limitations_label.configure(text=step.get("limitations", ""))

        if step.get("key") == "complete":
            self.preview_label.configure(text="✓  " + preview_text(
                step.get("output", ""), limit=60))
        elif step.get("output") is not None and not is_running:
            self.preview_label.configure(
                text=preview_text(step["output"], limit=60))
        else:
            self.preview_label.configure(text="computing...")

    def reset(self):
        """Return the card to the waiting state."""
        self.name_label.configure(text="Waiting")
        self.tagline_label.configure(text="")
        self.status_label.configure(text="Status: Idle",
                                    text_color=COLORS["TEXT_FAINT"])
        self.time_label.configure(text="")
        self.purpose_label.configure(
            text="Watch each layer transform the text, one step at a time.")
        self.advantages_label.configure(text="")
        self.limitations_label.configure(text="")
        self.preview_label.configure(text="—")


# ---------------------------------------------------------------------- #
# Summary popup                                                           #
# ---------------------------------------------------------------------- #

class SummaryPopup:
    """
    A premium success card that floats over the window and
    disappears automatically:

        [✓]  Encryption Completed Successfully

             Characters        42
             Key Length        8
             Layers            3
             Time              0.0043 sec

    Usage:
        SummaryPopup.show(app, "Encryption Completed Successfully",
                          [("Characters", "42"), ...])

    The popup closes itself after a few seconds, or instantly when
    clicked / when Escape is pressed.
    """

    _DISPLAY_MS = 4200   # how long the popup stays before fading out

    @staticmethod
    def show(parent, title: str, stats: list, kind: str = "success"):
        """
        Display the summary popup.

        Arguments:
            parent : the root window.
            title  : headline (e.g. "Encryption Completed Successfully").
            stats  : list of (label, value) pairs shown as a grid.
            kind   : "success" or "error".
        """
        accent = COLORS["SUCCESS"] if kind == "success" else COLORS["ERROR"]
        tint = (COLORS["TINT_SUCCESS"] if kind == "success"
                else COLORS["TINT_ERROR"])

        # --- Dim overlay (no grab: the popup is only a notification) ------ #
        overlay = ctk.CTkFrame(parent, fg_color=COLORS["OVERLAY"],
                               corner_radius=0)
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        overlay.lift()

        # --- Glass card ---------------------------------------------------- #
        card = ctk.CTkFrame(overlay, corner_radius=RADIUS["CARD"],
                            fg_color=COLORS["GLASS_INPUT"],
                            border_width=1, border_color=accent,
                            width=440)
        card.place(relx=0.5, rely=0.5, anchor="center")

        # Success medallion with a "pop" animation.
        medallion = ctk.CTkFrame(card, corner_radius=34, width=68, height=68,
                                 fg_color=tint, border_width=2,
                                 border_color=accent)
        medallion.pack(pady=(30, 12))
        icon_label = ctk.CTkLabel(medallion, text=ICONS["CHECK"],
                                  font=("Segoe UI", 30, "bold"),
                                  text_color=accent)
        icon_label.place(relx=0.5, rely=0.5, anchor="center")

        title_label = ctk.CTkLabel(card, text=title,
                                   font=FONTS["HEADING"],
                                   text_color=COLORS["TEXT"])
        title_label.pack(pady=(0, 16))

        # --- Stats grid (label / value) ------------------------------------- #
        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(padx=36, pady=(0, 22))

        for index, (label, value) in enumerate(stats):
            column = index % 2
            row = index // 2

            caption = ctk.CTkLabel(grid, text=label, font=FONTS["MICRO"],
                                   text_color=COLORS["TEXT_FAINT"])
            caption.grid(row=row * 2, column=column, sticky="w",
                         padx=(0 if column == 0 else 24, 0), pady=(0, 1))

            value_label = ctk.CTkLabel(grid, text=value,
                                       font=FONTS["SUBHEADING"],
                                       text_color=COLORS["TEXT"])
            value_label.grid(row=row * 2 + 1, column=column, sticky="w",
                             padx=(0 if column == 0 else 24, 0), pady=(0, 8))

        # --- Auto close ------------------------------------------------------ #
        def _close():
            try:
                animate_color(card, COLORS["GLASS_INPUT"], duration_ms=180,
                              on_finish=overlay.destroy)
            except tk.TclError:
                overlay.destroy()

        overlay.after(SummaryPopup._DISPLAY_MS, _close)
        overlay.bind("<Button-1>", lambda _e: _close())
        overlay.bind("<Escape>", lambda _e: _close())

        # Gentle fade-in: the card brightens into place.
        animate_color(card, COLORS["GLASS"], duration_ms=240,
                      start_color=COLORS["GLASS_INPUT"],
                      property_name="fg_color")
        animate_color(card, COLORS["BORDER"], duration_ms=240,
                      start_color=COLORS["BORDER_SOFT"],
                      property_name="border_color")
