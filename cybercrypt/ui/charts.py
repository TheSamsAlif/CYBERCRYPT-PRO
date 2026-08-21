"""
charts.py
=========

Phase 4 : lightweight canvas-based visualizations for the Security
Analysis dashboard. Everything is drawn with Tk Canvas / CTk widgets
(no matplotlib, no external charting library).

    AnimatedCounter   -> a number that counts up smoothly
    ProgressBar       -> horizontal animated fill bar
    ProgressRing      -> circular progress ring (canvas arcs)
    FlowChart         -> glass node flow with animated arrows
    TimelineChart     -> vertical step timeline (canvas)

Every animation runs on after() in small steps, so the dashboard
stays lightweight and never blocks the UI.
"""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from cybercrypt.ui.animation import fade_sequence
from cybercrypt.ui.theme import COLORS, FONTS, RADIUS

# Chart palette (reuses the design system colours). Colours are read
# lazily from the active palette when each chart is built; every chart
# also offers refresh() to re-read them after a theme switch.
_BAR_BG = COLORS["GLASS_INPUT"]
_FILL_ACCENT = COLORS["ACCENT"]
_FILL_SUCCESS = COLORS["SUCCESS"]
_FILL_WARNING = COLORS["WARNING"]

_STEP_MS = 16   # animation frame interval


# ---------------------------------------------------------------------- #
# Animated counter                                                        #
# ---------------------------------------------------------------------- #

def animate_counter(label: ctk.CTkLabel, target: int,
                    duration_ms: int = 700, suffix: str = ""):
    """
    Smoothly count a label from its current value to a new target.

    Arguments:
        label       : the CTkLabel showing the number.
        target      : the number to end at.
        duration_ms : total animation time.
        suffix      : optional text after the number (e.g. " chars").
    """
    try:
        current = int(str(label.cget("text")).split(" ")[0])
    except (ValueError, TypeError):
        current = 0
    total = max(0, int(target) - current)
    if total == 0:
        label.configure(text=f"{target}{suffix}")
        return
    steps = max(1, int(duration_ms / _STEP_MS))

    def _step(index: int):
        if index > steps:
            label.configure(text=f"{target}{suffix}")
            return
        value = current + int(total * index / steps)
        label.configure(text=f"{value}{suffix}")
        label.after(_STEP_MS, lambda: _step(index + 1))

    _step(1)


# ---------------------------------------------------------------------- #
# Horizontal progress bar                                                 #
# ---------------------------------------------------------------------- #

class ProgressBar(ctk.CTkFrame):
    """
    A rounded horizontal bar with an animated fill.

    Usage:
        bar = ProgressBar(parent, width=220, height=10)
        bar.set_fraction(0.65)
    """

    def __init__(self, parent, width: int = 200, height: int = 10,
                 fill_color: str = _FILL_ACCENT,
                 bg_color: str = _BAR_BG):
        super().__init__(parent, fg_color="transparent",
                         width=width, height=height)
        self._width = width
        self._height = height
        self._fill_color = fill_color
        self._fraction = 0.0

        self._bg = ctk.CTkFrame(self, fg_color=bg_color,
                                corner_radius=height // 2)
        self._bg.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._fill = ctk.CTkFrame(self, fg_color=fill_color,
                                  corner_radius=height // 2)
        self._fill.place(relx=0, rely=0, relwidth=0, relheight=1)

    def set_fraction(self, fraction: float, animate: bool = True):
        """
        Animate the fill to a new fraction (0.0 .. 1.0).

        Arguments:
            fraction : the new fill amount.
            animate  : False jumps instantly (used on first paint).
        """
        fraction = max(0.0, min(1.0, fraction))
        if not animate:
            self._fill.place(relx=0, rely=0,
                             relwidth=fraction, relheight=1)
            self._fraction = fraction
            return

        start = self._fraction
        steps = max(1, int(240 / _STEP_MS))

        def _step(index: int):
            if index > steps:
                self._fill.place(relx=0, rely=0,
                                 relwidth=fraction, relheight=1)
                self._fraction = fraction
                return
            current = start + (fraction - start) * index / steps
            self._fill.place(relx=0, rely=0, relwidth=current,
                             relheight=1)
            self.after(_STEP_MS, lambda: _step(index + 1))

        _step(1)


# ---------------------------------------------------------------------- #
# Circular progress ring                                                  #
# ---------------------------------------------------------------------- #

class ProgressRing(ctk.CTkFrame):
    """
    A circular progress indicator drawn on a Tk Canvas.

    Usage:
        ring = ProgressRing(parent, size=120, thickness=12)
        ring.set_fraction(0.72)          # animate to 72%
        ring.set_text("72")              # number in the middle
    """

    def __init__(self, parent, size: int = 120, thickness: int = 12,
                 color: str = None, bg_color: str = None):
        super().__init__(parent, fg_color="transparent",
                         width=size, height=size)
        self._size = size
        self._thickness = thickness
        self._color = color or COLORS["ACCENT"]
        self._bg_color = bg_color or COLORS["RING_BG"]
        self._fraction = 0.0

        self._canvas = tk.Canvas(self, width=size, height=size,
                                 bg=COLORS["GLASS"],
                                 highlightthickness=0, bd=0)
        self._canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._padding = thickness // 2 + 2
        self._extent = 359.9   # full circle minus a seam

        self._bg_item = self._canvas.create_arc(
            self._padding, self._padding,
            size - self._padding, size - self._padding,
            start=90, extent=-self._extent,
            style="arc", outline=self._bg_color,
            width=thickness)
        self._fg_item = self._canvas.create_arc(
            self._padding, self._padding,
            size - self._padding, size - self._padding,
            start=90, extent=0,
            style="arc", outline=self._color,
            width=thickness)

        self._text_item = self._canvas.create_text(
            size / 2, size / 2, text="0",
            fill=COLORS["TEXT"], font=FONTS["HEADING"])

    def refresh(self):
        """
        Re-apply the current theme palette.

        Called after a light/dark switch; updates the canvas backing,
        the ring track and the centre text colour.
        """
        self._canvas.configure(bg=COLORS["GLASS"])
        self._canvas.itemconfigure(self._bg_item,
                                   outline=COLORS["RING_BG"])
        self._canvas.itemconfigure(self._fg_item,
                                   outline=self._color)
        self._canvas.itemconfigure(self._text_item,
                                   fill=COLORS["TEXT"])

    def set_fraction(self, fraction: float, animate: bool = True):
        """
        Animate the arc to a new fraction (0.0 .. 1.0).

        Arguments:
            fraction : the new fill amount.
            animate  : False jumps instantly.
        """
        fraction = max(0.0, min(1.0, fraction))
        if not animate:
            self._canvas.itemconfigure(
                self._fg_item, extent=-self._extent * fraction)
            self._fraction = fraction
            return

        start = self._fraction
        steps = max(1, int(500 / _STEP_MS))

        def _step(index: int):
            if index > steps:
                self._canvas.itemconfigure(
                    self._fg_item, extent=-self._extent * fraction)
                self._fraction = fraction
                return
            current = start + (fraction - start) * index / steps
            self._canvas.itemconfigure(
                self._fg_item, extent=-self._extent * current)
            self.after(_STEP_MS, lambda: _step(index + 1))

        _step(1)

    def set_text(self, text: str):
        """Update the number in the middle of the ring."""
        self._canvas.itemconfigure(self._text_item, text=text)

    def set_color(self, color: str):
        """Change the ring colour (used when the strength band changes)."""
        self._color = color
        self._canvas.itemconfigure(self._fg_item, outline=color)


# ---------------------------------------------------------------------- #
# Flow chart (animated node flow)                                        #
# ---------------------------------------------------------------------- #

class FlowChart(ctk.CTkFrame):
    """
    A step flow: glass nodes connected by animated arrows.

    A small bright dot travels down (or across) each connector on a
    loop, which makes the flow feel alive without heavy CPU use. The
    animation automatically idles while the widget is not mapped.

    Usage:
        chart = FlowChart(parent, [
            ("▣", "Input", "your message"),
            ("A", "Caesar", "shift"),
        ])
        chart.pack(fill="x")
        chart.reveal()
    """

    _CONNECTOR_SIZE = 44   # height (vertical) / width (horizontal)
    _DOT_STEP_MS = 30

    def __init__(self, parent, steps: list, direction: str = "vertical",
                 node_height: int = 74):
        """
        Arguments:
            parent      : the parent widget.
            steps       : list of (icon, title, subtitle) tuples.
            direction   : "vertical" (top to bottom) or "horizontal"
                          (left to right).
            node_height : height of each node card.
        """
        super().__init__(parent, fg_color="transparent")
        self._steps = list(steps)
        self._direction = direction
        self._node_height = node_height
        self._connectors = []
        self._nodes = []
        self._after_handles = []

        for index, (icon, title, subtitle) in enumerate(self._steps):
            node = self._build_node(icon, title, subtitle)
            if direction == "vertical":
                node.pack(fill="x", padx=10, pady=(2, 2))
            else:
                node.pack(side="left", fill="y", padx=(2, 2),
                          expand=True)
            self._nodes.append(node)

            if index < len(self._steps) - 1:
                connector = self._build_connector()
                if direction == "vertical":
                    connector.pack(fill="x", padx=18)
                else:
                    connector.pack(side="left", fill="y",
                                   expand=True)
                self._connectors.append(connector)

    def _build_node(self, icon: str, title: str,
                    subtitle: str) -> ctk.CTkFrame:
        """One glass node card with icon, title and subtitle."""
        node = ctk.CTkFrame(self, corner_radius=RADIUS["PANEL"],
                            fg_color=COLORS["GLASS"],
                            border_width=1, border_color=COLORS["BORDER"],
                            height=self._node_height)
        node.pack_propagate(False)

        icon_label = ctk.CTkLabel(node, text=icon,
                                  font=("Segoe UI", 16, "bold"),
                                  text_color=COLORS["ACCENT"],
                                  width=30)
        icon_label.pack(side="left", padx=(16, 8), pady=8)

        texts = ctk.CTkFrame(node, fg_color="transparent")
        texts.pack(side="left", pady=8)

        title_label = ctk.CTkLabel(texts, text=title,
                                   font=FONTS["SMALL"],
                                   text_color=COLORS["TEXT"],
                                   justify="left", anchor="w",
                                   wraplength=150)
        title_label.pack(anchor="w")

        if subtitle:
            sub_label = ctk.CTkLabel(texts, text=subtitle,
                                     font=FONTS["MICRO"],
                                     text_color=COLORS["TEXT_MUTED"],
                                     justify="left", anchor="w",
                                     wraplength=150)
            sub_label.pack(anchor="w", pady=(1, 0))

        return node

    def _build_connector(self) -> tk.Canvas:
        """A small canvas drawing the animated flow arrow."""
        if self._direction == "vertical":
            canvas = tk.Canvas(self, bg=COLORS["GLASS"],
                               highlightthickness=0, bd=0,
                               height=self._CONNECTOR_SIZE)
        else:
            canvas = tk.Canvas(self, bg=COLORS["GLASS"],
                               highlightthickness=0, bd=0,
                               width=self._CONNECTOR_SIZE)
        self._animate_connector(canvas, 0)
        return canvas

    def _animate_connector(self, canvas: tk.Canvas, tick: int):
        """
        Draw one frame of a traveling dot on a connector canvas.

        The dot (with a fading tail) moves from one end of the
        connector to the other, then the loop restarts after a short
        pause. While the chart is not mapped the frame is skipped
        (keeps CPU usage at zero when the page is hidden).
        """
        try:
            if not self.winfo_ismapped():
                self._schedule(canvas, tick)
                return

            canvas.delete("all")
            width = max(2, canvas.winfo_width())
            height = max(2, canvas.winfo_height())
            if width < 5 or height < 5:
                self._schedule(canvas, tick)
                return

            vertical = self._direction == "vertical"
            length = height if vertical else width
            half = width / 2 if vertical else height / 2

            # The static line.
            if vertical:
                canvas.create_line(half, 2, half, height - 2,
                                   fill=COLORS["BORDER_SOFT"], width=2)
            else:
                canvas.create_line(2, half, width - 2, half,
                                   fill=COLORS["BORDER_SOFT"], width=2)

            # Traveling dot with a two-part tail (cycle: 2 length units).
            cycle = (length - 4) * 2
            phase = tick % cycle
            if phase < length - 4:
                dot = phase
            else:
                dot = (length - 4) - (phase - (length - 4))

            if vertical:
                canvas.create_oval(half - 4, dot - 4, half + 4, dot + 4,
                                   fill=COLORS["ACCENT"], outline="")
                canvas.create_oval(half - 3, dot - 11, half + 3, dot - 5,
                                   fill=COLORS["PRIMARY_DEEP"], outline="")
                canvas.create_oval(half - 2, dot - 17, half + 2, dot - 13,
                                   fill=COLORS["BORDER"], outline="")
            else:
                canvas.create_oval(dot - 4, half - 4, dot + 4, half + 4,
                                   fill=COLORS["ACCENT"], outline="")
                canvas.create_oval(dot - 11, half - 3, dot - 5, half + 3,
                                   fill=COLORS["PRIMARY_DEEP"], outline="")
                canvas.create_oval(dot - 17, half - 2, dot - 13, half + 2,
                                   fill=COLORS["BORDER"], outline="")
        except tk.TclError:
            return  # widget destroyed; stop quietly

        self._schedule(canvas, tick + 1)

    def _schedule(self, canvas: tk.Canvas, tick: int):
        """Schedule the next connector frame (bounded handle list)."""
        handle = self.after(self._DOT_STEP_MS,
                            lambda: self._animate_connector(canvas, tick))
        self._after_handles.append(handle)
        if len(self._after_handles) > 50:
            self._after_handles.pop(0)

    # ------------------------------------------------------------------ #
    # Public API                                                          #
    # ------------------------------------------------------------------ #

    def reveal(self, animate: bool = True):
        """
        Staggered fade-in of the nodes (used when the page opens).

        Arguments:
            animate : False jumps instantly (used on first paint).
        """
        if not animate:
            for node in self._nodes:
                node.configure(fg_color=COLORS["GLASS"])
            return
        fade_sequence(
            self._nodes,
            from_color=COLORS["GLASS_INPUT"],
            to_color=COLORS["GLASS"],
            delay_ms=90, duration_ms=240,
        )

    def refresh(self):
        """
        Re-apply the current theme palette to the canvases.

        The connector lines and travelling dots already read the
        palette every frame; this re-tints the canvas backing and
        node widgets after a light/dark switch.
        """
        try:
            for canvas in self._connectors:
                canvas.configure(bg=COLORS["GLASS"])
        except tk.TclError:
            return

    def stop(self):
        """Stop every animation loop (used when the app closes)."""
        for handle in self._after_handles:
            try:
                self.after_cancel(handle)
            except tk.TclError:
                pass
        self._after_handles.clear()


# ---------------------------------------------------------------------- #
# Timeline chart                                                          #
# ---------------------------------------------------------------------- #

class TimelineChart(ctk.CTkFrame):
    """
    A vertical step-by-step timeline:

        [Start] ── 0 ms
        [Layer 1 - Caesar] ── 0.31 ms
        ...

    Usage:
        chart = TimelineChart(parent, height=230)
        chart.set_entries([("Start", 0), ("Layer 1 - Caesar", 1), ...])
    """

    _NODE_RADIUS = 6

    def __init__(self, parent, height: int = 210):
        super().__init__(parent, fg_color="transparent",
                         height=height)
        self._height = height
        self._canvas = tk.Canvas(self, bg=COLORS["GLASS"],
                                 highlightthickness=0, bd=0)
        self._canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._entries = []
        self._canvas.bind("<Configure>",
                          lambda _e: self._redraw(animate=False))

    def set_entries(self, entries: list, animate: bool = True):
        """
        Redraw the timeline for a list of (label, duration_ms) entries.

        Arguments:
            entries : e.g. [("Start", 0), ("Layer 1 - Caesar", 1), ...].
            animate : stagger the node drawing (False = instant).
        """
        self._entries = list(entries)
        self._redraw(animate)

    def refresh(self):
        """
        Re-apply the current theme palette (after a light/dark switch).
        """
        self._canvas.configure(bg=COLORS["GLASS"])
        self._redraw(animate=False)

    def _redraw(self, animate: bool):
        """Draw every node on the current canvas size."""
        self._canvas.delete("all")

        count = len(self._entries)
        if count == 0:
            return

        canvas_width = max(10, self._canvas.winfo_width())
        canvas_height = max(10, self._canvas.winfo_height())
        if canvas_width < 20:   # not laid out yet - measure lazily
            canvas_width = 640
        if canvas_height < 20:
            canvas_height = self._height

        line_x = 60
        top = 14
        bottom = canvas_height - 14
        self._canvas.create_line(
            line_x, top, line_x, bottom,
            fill=COLORS["BORDER_SOFT"], width=2)

        step_y = (bottom - top) / max(1, count - 1)

        def _draw(index: int):
            if index >= count:
                return
            label, duration_ms = self._entries[index]
            y = top + index * step_y
            node_color = (COLORS["SUCCESS"] if index == count - 1
                          else COLORS["ACCENT"])

            self._canvas.create_oval(
                line_x - self._NODE_RADIUS, y - self._NODE_RADIUS,
                line_x + self._NODE_RADIUS, y + self._NODE_RADIUS,
                fill=COLORS["GLASS"], outline=node_color, width=2)

            self._canvas.create_text(
                line_x - 14, y, text=label,
                fill=COLORS["TEXT"], font=FONTS["SMALL"],
                anchor="e", justify="right")

            self._canvas.create_text(
                line_x + 14, y,
                text=(f"{duration_ms} ms" if duration_ms else "\u2014"),
                fill=COLORS["TEXT_MUTED"], font=FONTS["MONO_SMALL"],
                anchor="w")

            if animate and index < count - 1:
                self.after(120 * index, lambda: _draw(index + 1))
            else:
                _draw(index + 1)

        _draw(0)
