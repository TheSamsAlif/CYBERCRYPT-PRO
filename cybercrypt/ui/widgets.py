"""
widgets.py
==========

Reusable premium glass components:

    glass_panel           -> the base frosted-glass frame
    primary_button        -> glowing blue action button
    secondary_button      -> quiet glass button
    GlassCard             -> glass panel + soft shadow + hover glow
    NavButton             -> sidebar item with indicator + active glow
    LayerIndicator        -> the three-layer status chips
    badge                 -> small status pill
    Toast                 -> floating notification (success / error / ...)
    KeysPanel             -> the three encryption keys editor (shared
                             by the encrypt and decrypt screens)

Every button supports the full animation set: hover glow, click
flash and a visible keyboard focus ring.
"""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from cybercrypt.core.alphabet import INDEX
from cybercrypt.core.engine import EncryptionEngine
from cybercrypt.ui.animation import (
    animate_color,
    bind_focus_ring,
    bind_hover,
    bind_input_focus,
    bind_press_flash,
    bind_smart_hover,
)
from cybercrypt.ui.theme import COLORS, FONTS, ICONS, RADIUS

# Colour map used by toasts: kind -> (border, accent fill). Resolved
# at call time so the correct palette is used after a theme switch.
def _toast_style(kind: str):
    return {
        "success": (COLORS["SUCCESS"], COLORS["TINT_SUCCESS"]),
        "error":   (COLORS["ERROR"], COLORS["TINT_ERROR"]),
        "warning": (COLORS["WARNING"], COLORS["TINT_WARNING"]),
        "info":    (COLORS["ACCENT"], COLORS["TINT_INFO"]),
    }.get(kind, (COLORS["ACCENT"], COLORS["TINT_INFO"]))

# Toast icon prefix per kind.
_TOAST_ICONS = {
    "success": ICONS["CHECK"],
    "error":   ICONS["ERROR"],
    "warning": "!",
    "info":    ICONS["INFO"],
}


# ---------------------------------------------------------------------- #
# Glass panel                                                             #
# ---------------------------------------------------------------------- #

def glass_panel(parent, **kwargs) -> ctk.CTkFrame:
    """
    Create a frosted-glass panel with the standard styling.

    Arguments:
        parent : the parent widget.
        kwargs : optional overrides (corner_radius, fg_color, ...).

    Returns:
        A configured CTkFrame.
    """
    style = {
        "corner_radius": RADIUS["CARD"],
        "fg_color": COLORS["GLASS"],
        "border_width": 1,
        "border_color": COLORS["BORDER"],
    }
    style.update(kwargs)
    return ctk.CTkFrame(parent, **style)


# ---------------------------------------------------------------------- #
# Glass card (panel + shadow + hover)                                     #
# ---------------------------------------------------------------------- #

class GlassCard:
    """
    A premium glass card: rounded panel, soft shadow underneath,
    hover glow (border lights up) and hover elevation (rises 2 px).

    Usage:
        card = GlassCard(parent, relx=0, rely=0.1, relwidth=0.5,
                         relheight=0.3)
        card = GlassCard(parent, x=0, y=112, relwidth=0.6,
                         relheight=0.25)   # pixel placement (grid)
        ... add children to card.panel ...

    The shadow is simulated with a darker rounded frame offset
    below the panel (Tk has no real shadow rendering).
    """

    def __init__(self, parent, relx: float = None, rely: float = None,
                 x: int = None, y: int = None,
                 relwidth: float = 0.0, relheight: float = 0.0,
                 radius: int = None, hover: bool = True):
        radius = radius or RADIUS["CARD"]

        self._relx = relx
        self._rely = rely
        self._relwidth = relwidth
        self._relheight = relheight
        self._x = x
        self._y = y
        self._pixel = x is not None

        def _args(y_offset):
            if self._pixel:
                return {"x": self._x, "y": self._y + y_offset,
                        "relwidth": self._relwidth,
                        "relheight": self._relheight}
            return {"relx": self._relx, "rely": self._rely,
                    "relwidth": self._relwidth,
                    "relheight": self._relheight, "y": y_offset}

        # Stored on self: _raise_card() re-places the panel on every
        # hover event, so the argument builder must stay reachable.
        self._args = _args

        # Soft shadow: a darker frame, offset a few pixels down.
        self.shadow = ctk.CTkFrame(parent, corner_radius=radius + 6,
                                   fg_color=COLORS["SHADOW"],
                                   border_width=0)
        self.shadow.place(**self._args(7))

        # The glass panel itself (created after -> sits above shadow).
        self.panel = ctk.CTkFrame(parent, corner_radius=radius,
                                  fg_color=COLORS["GLASS"],
                                  border_width=1,
                                  border_color=COLORS["BORDER"])
        self.panel.place(**self._args(0))

        if hover:
            bind_smart_hover(
                self.panel,
                lambda: COLORS["GLASS"], lambda: COLORS["GLASS_HOVER"],
                lambda: COLORS["BORDER"], lambda: COLORS["ACCENT"],
                enabled=lambda: True,
            )
            self.panel.bind("<Enter>", lambda _e: self._raise_card(-2))
            self.panel.bind("<Leave>", lambda _e: self._raise_card(0))

    def relocate(self, relx: float = None, rely: float = None,
                 relwidth: float = None, relheight: float = None):
        """
        Move / resize the card after construction (used by resize
        handlers so layouts stay correct at every window size).
        Relative coordinates only; pixel-placed cards keep their
        position.
        """
        if relx is not None:
            self._relx = relx
        if rely is not None:
            self._rely = rely
        if relwidth is not None:
            self._relwidth = relwidth
        if relheight is not None:
            self._relheight = relheight
        try:
            self.panel.place(**self._args(0))
            self.shadow.place(**self._args(7))
        except tk.TclError:
            return  # widget is gone

    # ------------------------------------------------------------------ #
    # Hover elevation                                                     #
    # ------------------------------------------------------------------ #

    def _raise_card(self, offset_y: int):
        """
        Shift the card vertically (hover elevation).

        Arguments:
            offset_y : -2 lifts the card, 0 puts it back down.
        """
        try:
            self.panel.place(**self._args(offset_y))
        except tk.TclError:
            return  # widget is gone


# ---------------------------------------------------------------------- #
# Buttons                                                                 #
# ---------------------------------------------------------------------- #

def _attach_button_animations(button, pressed_color: str):
    """
    Add click flash + focus ring to a button.

    Arguments:
        button        : the CTkButton to enhance.
        pressed_color : colour while the button is pressed down.
    """
    bind_press_flash(button, pressed_color)
    bind_focus_ring(button, COLORS["FOCUS"])


def primary_button(parent, text: str, command, **kwargs) -> ctk.CTkButton:
    """
    The main glowing blue action button.

    Hover glow, click flash and a keyboard focus ring included.

    Arguments:
        parent  : the parent widget.
        text    : button label.
        command : callback fired when clicked.
        kwargs  : optional overrides.

    Returns:
        A configured CTkButton.
    """
    height = kwargs.pop("height", 46)

    button = ctk.CTkButton(
        parent,
        text=text,
        command=command,
        corner_radius=RADIUS["BUTTON"],
        fg_color=COLORS["PRIMARY"],
        hover_color=COLORS["PRIMARY"],   # animated manually below
        border_width=1,
        border_color=COLORS["PRIMARY"],  # blends; focus turns it accent
        text_color=COLORS["ON_PRIMARY"],
        font=FONTS["SUBHEADING"],
        height=height,
        cursor="hand2",
        **kwargs,
    )
    # Smooth hover glow instead of the instant default hover.
    bind_hover(button, lambda: COLORS["PRIMARY"], lambda: COLORS["ACCENT"])
    _attach_button_animations(button, lambda: COLORS["PRIMARY_DEEP"])
    return button


def secondary_button(parent, text: str, command, **kwargs) -> ctk.CTkButton:
    """
    A quiet glass button used for less important actions.

    Hover glow, click flash and a keyboard focus ring included.

    Arguments:
        parent  : the parent widget.
        text    : button label.
        command : callback fired when clicked.
        kwargs  : optional overrides.

    Returns:
        A configured CTkButton.
    """
    height = kwargs.pop("height", 42)

    button = ctk.CTkButton(
        parent,
        text=text,
        command=command,
        corner_radius=RADIUS["BUTTON"],
        fg_color=COLORS["NAV"],
        hover_color=COLORS["NAV"],   # animated manually below
        border_width=1,
        border_color=COLORS["BORDER"],
        text_color=COLORS["TEXT"],
        font=FONTS["BODY"],
        height=height,
        cursor="hand2",
        **kwargs,
    )
    bind_hover(button, lambda: COLORS["NAV"], lambda: COLORS["GLASS_LIGHT"],
               lambda: COLORS["BORDER"], lambda: COLORS["PRIMARY"])
    _attach_button_animations(button, lambda: COLORS["PRESSED"])
    return button


# ---------------------------------------------------------------------- #
# Input factories (entries and text boxes)                                #
# ---------------------------------------------------------------------- #

def make_entry(parent, variable=None, placeholder: str = "",
               width: int = 360, height: int = 44, **kwargs) -> ctk.CTkEntry:
    """
    The standard text field used across every screen.

    Includes the accent focus ring for keyboard users.

    Arguments:
        parent      : the parent widget.
        variable    : optional tk.StringVar bound to the field.
        placeholder : hint text shown while the field is empty.
        width       : field width.
        height      : field height.
        kwargs      : optional overrides.

    Returns:
        A configured CTkEntry.
    """
    entry = ctk.CTkEntry(
        parent,
        textvariable=variable,
        placeholder_text=placeholder,
        placeholder_text_color=COLORS["TEXT_FAINT"],
        corner_radius=RADIUS["FIELD"],
        fg_color=COLORS["GLASS_INPUT"],
        border_width=1,
        border_color=COLORS["BORDER"],
        text_color=COLORS["TEXT"],
        font=FONTS["BODY"],
        width=width,
        height=height,
        **kwargs,
    )
    bind_input_focus(entry, lambda: COLORS["FOCUS"])
    return entry


def make_textbox(parent, width: int = 460, height: int = 160,
                 **kwargs) -> ctk.CTkTextbox:
    """
    The standard multi-line text area (input / output).

    Includes the accent focus ring for keyboard users.

    Arguments:
        parent  : the parent widget.
        width   : box width.
        height  : box height.
        kwargs  : optional overrides.

    Returns:
        A configured CTkTextbox.
    """
    box = ctk.CTkTextbox(
        parent,
        corner_radius=RADIUS["FIELD"],
        fg_color=COLORS["GLASS_INPUT"],
        border_width=1,
        border_color=COLORS["BORDER"],
        text_color=COLORS["TEXT"],
        font=FONTS["BODY"],
        wrap="word",
        width=width,
        height=height,
        **kwargs,
    )
    bind_input_focus(box, lambda: COLORS["FOCUS"])
    return box


# ---------------------------------------------------------------------- #
# Sidebar navigation item                                                 #
# ---------------------------------------------------------------------- #

class NavButton(ctk.CTkFrame):
    """
    A premium sidebar item: icon + label + a left indicator bar.

    The active item glows (deep blue fill + accent border), its
    indicator bar lights up and everything animates smoothly.
    """

    def __init__(self, parent, icon: str, text: str, command,
                 height: int = 50):
        super().__init__(
            parent,
            corner_radius=RADIUS["PANEL"],
            fg_color=COLORS["NAV"],
            border_width=1,
            border_color=COLORS["BORDER_SOFT"],
            height=height,
        )
        # Make the item reachable with the Tab key (CTkFrame filters
        # this option, so it is set on the underlying Tk frame directly).
        tk.Frame.configure(self, takefocus=1)
        self._command = command
        self._active = False

        # Left indicator bar (subtle at rest, glows when active).
        self.indicator = ctk.CTkFrame(self, corner_radius=2, width=4,
                                      height=20,
                                      fg_color=COLORS["BORDER_SOFT"])
        self.indicator.place(x=9, rely=0.5, anchor="w")

        self.icon_label = ctk.CTkLabel(self, text=icon,
                                       font=("Segoe UI", 15),
                                       text_color=COLORS["TEXT_MUTED"],
                                       width=22)
        self.icon_label.place(relx=0.10, rely=0.5, anchor="w")

        self.text_label = ctk.CTkLabel(self, text=text,
                                       font=FONTS["BODY"],
                                       text_color=COLORS["TEXT_MUTED"])
        self.text_label.place(relx=0.24, rely=0.5, anchor="w")

        # Clickable on the frame and on every child widget.
        self.bind("<Button-1>", self._on_click)
        self.icon_label.bind("<Button-1>", self._on_click)
        self.text_label.bind("<Button-1>", self._on_click)
        self.indicator.bind("<Button-1>", self._on_click)

        # Hover (disabled while the item is the active page).
        bind_smart_hover(
            self,
            lambda: COLORS["NAV"], lambda: COLORS["GLASS_LIGHT"],
            lambda: COLORS["BORDER_SOFT"], lambda: COLORS["BORDER"],
            enabled=lambda: not self._active,
        )

        # Keyboard accessibility: Tab reaches the item, Enter / Space
        # activates it, and a visible focus ring shows where the focus is.
        self.bind("<Return>", self._on_click)
        self.bind("<space>", self._on_click)
        bind_focus_ring(self, lambda: COLORS["FOCUS"])

    # ------------------------------------------------------------------ #
    # Behaviour                                                           #
    # ------------------------------------------------------------------ #

    def _on_click(self, _event):
        """Fire the navigation command."""
        self.focus_set()
        self._command()

    def set_active(self, active: bool):
        """
        Highlight this item as the current page (or revert it).

        Arguments:
            active : True when this is the selected page.
        """
        self._active = active

        fill = COLORS["PRIMARY_DEEP"] if active else COLORS["NAV"]
        border = COLORS["ACCENT"] if active else COLORS["BORDER_SOFT"]
        indicator = COLORS["ACCENT"] if active else COLORS["BORDER_SOFT"]
        text_color = COLORS["TEXT"] if active else COLORS["TEXT_MUTED"]
        icon_color = COLORS["ACCENT"] if active else COLORS["TEXT_MUTED"]

        animate_color(self, fill, duration_ms=240, property_name="fg_color")
        animate_color(self, border, duration_ms=240,
                      property_name="border_color")
        animate_color(self.indicator, indicator, duration_ms=240,
                      property_name="fg_color")
        self.text_label.configure(text_color=text_color)
        self.icon_label.configure(text_color=icon_color)

    def set_compact(self, compact: bool):
        """
        Switch between full row and icon-only rail mode.

        In compact mode the label hides and the icon centres itself,
        which lets the sidebar shrink to a slim icon rail on narrow
        windows.

        Arguments:
            compact : True to show only the icon.
        """
        if compact:
            self.text_label.place_forget()
            self.icon_label.place(relx=0.5, rely=0.5, anchor="center")
            self.indicator.place(x=4, rely=0.5, anchor="w")
        else:
            self.icon_label.place(relx=0.10, rely=0.5, anchor="w")
            self.text_label.place(relx=0.24, rely=0.5, anchor="w")
            self.indicator.place(x=9, rely=0.5, anchor="w")


# ---------------------------------------------------------------------- #
# Layer status indicator                                                  #
# ---------------------------------------------------------------------- #

class LayerIndicator(ctk.CTkFrame):
    """
    Shows the three encryption layers as status chips.

    Each chip has three states:
        pending -> faint dot   (waiting)
        active  -> blue dot    (processing)
        done    -> green dot   (completed)

    Usage:
        layers = LayerIndicator(parent, ("Caesar", "Vigenere", "XOR"))
        layers.set_state(0, "active")   # chip 0 starts processing
        layers.set_state(1, "done")     # chip 1 finished
        layers.reset_all()
    """

    _STATE_COLORS = {
        "pending": (COLORS["BORDER_SOFT"], COLORS["TEXT_FAINT"]),
        "active":  (COLORS["ACCENT"], COLORS["ACCENT"]),
        "done":    (COLORS["SUCCESS"], COLORS["SUCCESS"]),
    }

    def __init__(self, parent, layers: tuple = ("Caesar", "Vigenere", "XOR")):
        super().__init__(
            parent,
            corner_radius=RADIUS["PANEL"],
            fg_color=COLORS["GLASS"],
            border_width=1,
            border_color=COLORS["BORDER"],
        )
        self._chips = []

        for name in layers:
            chip = ctk.CTkFrame(self, corner_radius=RADIUS["CHIP"],
                                fg_color=COLORS["GLASS_INPUT"],
                                border_width=1,
                                border_color=COLORS["BORDER_SOFT"])
            chip.pack(side="left", padx=(0, 8), pady=8)

            dot = ctk.CTkLabel(chip, text=ICONS["DOT"],
                               font=("Segoe UI", 8),
                               text_color=COLORS["TEXT_FAINT"])
            dot.pack(side="left", padx=(10, 4), pady=5)

            label = ctk.CTkLabel(chip, text=name, font=FONTS["MICRO"],
                                 text_color=COLORS["TEXT_MUTED"])
            label.pack(side="left", padx=(0, 10), pady=5)

            self._chips.append({"chip": chip, "dot": dot, "label": label})

        # Overall status word on the right.
        self.status_label = ctk.CTkLabel(self, text="Idle",
                                         font=FONTS["SMALL"],
                                         text_color=COLORS["TEXT_FAINT"])
        self.status_label.place(relx=0.97, rely=0.5, anchor="e")

    # ------------------------------------------------------------------ #
    # States                                                              #
    # ------------------------------------------------------------------ #

    def set_state(self, index: int, state: str):
        """
        Set one chip's visual state.

        Arguments:
            index : which chip (0, 1, 2).
            state : "pending", "active" or "done".
        """
        if index >= len(self._chips):
            return
        chip_color, dot_color = self._STATE_COLORS.get(
            state, self._STATE_COLORS["pending"])

        chip = self._chips[index]
        animate_color(chip["chip"], COLORS["GLASS_LIGHT"], duration_ms=180,
                      property_name="fg_color") if state != "pending" else \
            animate_color(chip["chip"], COLORS["GLASS_INPUT"], 180,
                          property_name="fg_color")
        animate_color(chip["chip"], chip_color, duration_ms=180,
                      property_name="border_color")
        chip["dot"].configure(text_color=dot_color)

    def set_status_text(self, text: str):
        """Update the overall status word (e.g. "Processing...")."""
        self.status_label.configure(text=text)

    def reset_all(self):
        """Return every chip to the pending state."""
        for index in range(len(self._chips)):
            self.set_state(index, "pending")
        self.set_status_text("Idle")


# ---------------------------------------------------------------------- #
# Badge                                                                   #
# ---------------------------------------------------------------------- #

def badge(parent, text: str, color: str = COLORS["ACCENT"], **kwargs) -> ctk.CTkFrame:
    """
    A small status pill (e.g. "Educational Demo").

    Arguments:
        parent : the parent widget.
        text   : pill label.
        color  : accent colour of the pill.
        kwargs : optional overrides.

    Returns:
        A CTkFrame containing the label.
    """
    pill = ctk.CTkFrame(
        parent,
        corner_radius=RADIUS["PILL"],
        fg_color=COLORS["GLASS"],
        border_width=1,
        border_color=color,
        **kwargs,
    )
    label = ctk.CTkLabel(pill, text=text, text_color=color,
                         font=FONTS["SMALL"])
    label.pack(padx=14, pady=4)
    return pill


# ---------------------------------------------------------------------- #
# Section heading (shared by every scrollable page)                       #
# ---------------------------------------------------------------------- #

def section_heading(parent, icon: str, heading: str,
                    right_text: str = "") -> ctk.CTkFrame:
    """
    The standard glass heading card that opens a section on every
    scrollable page (Guide, Architecture, ...).

    Arguments:
        parent      : the scrollable frame (or any container).
        icon        : the section icon glyph.
        heading     : the section title.
        right_text  : optional faint caption on the right edge
                      (e.g. "6 questions").

    Returns:
        The heading card frame.
    """
    card = glass_panel(parent)
    card.pack(fill="x", padx=2, pady=(0, 8))

    icon_box = ctk.CTkFrame(card, corner_radius=16, width=32, height=32,
                            fg_color=COLORS["PRIMARY_DEEP"],
                            border_width=1, border_color=COLORS["ACCENT"])
    icon_box.pack(side="left", padx=(18, 12), pady=10)
    icon_box.pack_propagate(False)
    icon_label = ctk.CTkLabel(icon_box, text=icon,
                              font=("Segoe UI", 15, "bold"),
                              text_color=COLORS["ACCENT"])
    icon_label.place(relx=0.5, rely=0.5, anchor="center")

    heading_label = ctk.CTkLabel(card, text=heading,
                                 font=FONTS["SUBHEADING"],
                                 text_color=COLORS["TEXT"])
    heading_label.pack(side="left", pady=10)

    if right_text:
        right = ctk.CTkLabel(card, text=right_text,
                             font=FONTS["MICRO"],
                             text_color=COLORS["TEXT_FAINT"])
        right.pack(side="right", padx=18)
    return card


# ---------------------------------------------------------------------- #
# Toast notification                                                      #
# ---------------------------------------------------------------------- #

class Toast:
    """
    A floating notification near the bottom of the window that
    fades in, stays a moment and fades out.

    Usage:
        Toast.show(parent, "Copied to clipboard", kind="success")
    """

    _DISPLAY_MS = 2300   # how long the toast stays visible

    @staticmethod
    def show(parent, message: str, kind: str = "success"):
        """
        Display a toast notification.

        Arguments:
            parent  : the widget the toast floats above (usually root).
            message : the text to display.
            kind    : "success", "error", "warning" or "info".
        """
        border_color, fill = _toast_style(kind)
        icon = _TOAST_ICONS.get(kind, ICONS["INFO"])

        frame = ctk.CTkFrame(
            parent,
            corner_radius=RADIUS["PANEL"],
            fg_color=fill,
            border_width=1,
            border_color=border_color,
        )
        label = ctk.CTkLabel(frame, text=f"{icon}  {message}",
                             text_color=COLORS["TEXT"],
                             font=FONTS["BODY"])
        label.pack(padx=22, pady=10)

        # Centre it near the bottom of the window (above the status bar).
        frame.place(relx=0.5, rely=0.86, anchor="center")
        frame.lift()

        # Smoothly brighten the glass (fade-in effect).
        animate_color(frame, COLORS["GLASS_LIGHT"], duration_ms=220,
                      start_color=fill, on_finish=lambda: _finish(frame))

        def _finish(toast_frame):
            # Hold, then fade out and destroy the toast.
            toast_frame.after(Toast._DISPLAY_MS, lambda: _close(toast_frame))

        def _close(toast_frame):
            try:
                animate_color(toast_frame, fill, duration_ms=220,
                              on_finish=toast_frame.destroy)
            except tk.TclError:
                return


# ---------------------------------------------------------------------- #
# Keys panel (shared by encrypt + decrypt screens)                        #
# ---------------------------------------------------------------------- #

class KeysPanel(ctk.CTkFrame):
    """
    The glass panel where the user enters the three keys:

        1. Caesar shift   (whole number, 1..127)
        2. Vigenere key   (keyword, letters / numbers)
        3. Random seed    (whole number)

    Offers a one-click "Generate Key" button that fills all three
    fields with fresh random values.
    """

    def __init__(self, parent, title: str, subtitle: str = ""):
        super().__init__(
            parent,
            corner_radius=RADIUS["CARD"],
            fg_color=COLORS["GLASS"],
            border_width=1,
            border_color=COLORS["BORDER"],
        )
        self.title = title
        self.subtitle = subtitle

        # Input variables for the three key fields.
        self.shift_var = tk.StringVar()
        self.key_var = tk.StringVar()
        self.seed_var = tk.StringVar()

        self._build_widgets()

    # ------------------------------------------------------------------ #
    # Layout                                                              #
    # ------------------------------------------------------------------ #

    def _build_widgets(self):
        """Create every label, entry and button inside the panel.

        The panel uses a natural (pack) flow so it grows with its
        content instead of using fixed relative positions.
        """
        pad = 16
        header = ctk.CTkLabel(self, text=self.title, font=FONTS["HEADING"],
                              text_color=COLORS["TEXT"], anchor="w")
        header.pack(fill="x", padx=pad, pady=(12, 2))

        if self.subtitle:
            sub = ctk.CTkLabel(self, text=self.subtitle, font=FONTS["MICRO"],
                               text_color=COLORS["TEXT_MUTED"], anchor="w")
            sub.pack(fill="x", padx=pad, pady=(0, 6))

        # --- Caesar shift ------------------------------------------------ #
        self._add_field_label("Caesar Shift", pad)
        self.shift_entry = self._add_entry(self.shift_var,
                                           placeholder="e.g. 7 (1 - 127)",
                                           pad=pad)

        # --- Vigenere key ------------------------------------------------ #
        self._add_field_label("Vigenere Key", pad)
        self.key_entry = self._add_entry(self.key_var,
                                         placeholder="e.g. SECRETKEY",
                                         pad=pad)

        # --- Random seed -------------------------------------------------- #
        self._add_field_label("Random Seed", pad)
        self.seed_entry = self._add_entry(self.seed_var,
                                          placeholder="e.g. 123456",
                                          pad=pad)

        # --- Generate Key -------------------------------------------------- #
        self.auto_button = secondary_button(
            self,
            f"{ICONS['GENERATE']}  Generate Key",
            self.generate_keys,
            height=40,
        )
        self.auto_button.pack(fill="x", padx=pad, pady=(10, 14))

    def _add_field_label(self, text: str, pad: int):
        """Place a small caption above an entry field."""
        label = ctk.CTkLabel(self, text=text, font=FONTS["SMALL"],
                             text_color=COLORS["TEXT_MUTED"], anchor="w")
        label.pack(fill="x", padx=pad, pady=(4, 2))

    def _add_entry(self, variable, placeholder: str,
                   pad: int) -> ctk.CTkEntry:
        """
        Create a styled entry field inside the panel.

        Returns:
            The created CTkEntry.
        """
        entry = make_entry(
            self,
            variable=variable,
            placeholder=placeholder,
            width=120, height=42,
        )
        entry.pack(fill="x", padx=pad, pady=(0, 2))
        return entry

    # ------------------------------------------------------------------ #
    # Behaviour                                                           #
    # ------------------------------------------------------------------ #

    def generate_keys(self):
        """Fill all three fields with fresh random keys."""
        keys = EncryptionEngine.generate_random_keys()
        self.shift_var.set(str(keys["shift"]))
        self.key_var.set(keys["vigenere_key"])
        self.seed_var.set(str(keys["seed"]))

    def get_keys(self) -> dict:
        """
        Read and validate the three keys.

        Returns:
            A dictionary: {"shift": int, "vigenere_key": str, "seed": int}

        Raises:
            ValueError : with a friendly message when a field is invalid.
        """
        # --- Caesar shift --- #
        shift_text = self.shift_var.get().strip()
        try:
            shift = int(shift_text)
        except ValueError:
            raise ValueError("Caesar shift must be a whole number (1 - 127).")
        if not 1 <= shift <= 127:
            raise ValueError("Caesar shift must be between 1 and 127.")

        # --- Vigenere key --- #
        vigenere_key = self.key_var.get().strip()
        if not vigenere_key:
            raise ValueError("Please enter a Vigenere key.")
        if not any(char in INDEX for char in vigenere_key):
            raise ValueError("Vigenere key must contain letters or numbers.")

        # --- Random seed --- #
        seed_text = self.seed_var.get().strip()
        try:
            seed = int(seed_text)
        except ValueError:
            raise ValueError("Random seed must be a whole number.")

        return {"shift": shift, "vigenere_key": vigenere_key, "seed": seed}

    def set_keys(self, keys: dict):
        """
        Pre-fill the fields (used to restore the last keys used).

        Arguments:
            keys : a dictionary with the three key values.
        """
        if not keys:
            return
        self.shift_var.set(str(keys.get("shift", "")))
        self.key_var.set(keys.get("vigenere_key", ""))
        self.seed_var.set(str(keys.get("seed", "")))
