"""
theme.py
========

The design system of CyberCrypt Pro.
Every colour, font, shape and icon constant lives here so that the
rest of the code stays clean and the whole app can be re-skinned by
editing this single file.

Theme system (Phase 6 upgrade):
    * two full palettes - DARK_COLORS and LIGHT_COLORS - with the
      same keys, so every widget resolves its colours through the
      active COLORS dict
    * COLORS always holds the ACTIVE palette; switching a theme
      mutates it in place, so lazy references never go stale
    * apply_theme(mode, root) re-colours every existing widget by
      remapping their current colour values through the old->new
      palette, then notifies subscribers (background, charts,
      tooltips) so canvas-drawn content redraws too
    * every hard-coded tint from widgets / panels / dialogs /
      charts / tooltip / background now has a token in the palettes
"""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

# ---------------------------------------------------------------------- #
# Dark palette (the original "deep space glass" look)                     #
# ---------------------------------------------------------------------- #
DARK_COLORS = {
    # Backgrounds
    "BG":            "#070B16",   # deep space navy (window background)
    "BG_HIGH":       "#0A1022",   # lighter end of the gradient
    "SHADOW":        "#03050C",   # fake soft shadow tone behind cards
    "OVERLAY":       "#0A0F1F",   # modal dialog dim overlay

    # Glass surfaces (simulated frosted glass)
    "GLASS":         "#0F1930",   # glass panel fill
    "GLASS_LIGHT":   "#14264A",   # glass on hover / active
    "GLASS_HOVER":   "#14233E",   # card hover fill (subtle)
    "GLASS_INPUT":   "#0C1526",   # text fields and entries
    "NAV":           "#0D1730",   # sidebar buttons at rest

    # Borders (white ~ 18% opacity look)
    "BORDER":        "#2B3E66",   # standard glass border
    "BORDER_SOFT":   "#1D2C4D",   # subtle divider lines
    "BORDER_GLOW":   "#3B82F6",   # hover glow border

    # Brand accents
    "PRIMARY":       "#3B82F6",   # primary blue
    "PRIMARY_DEEP":  "#1E3A8A",   # deep blue (pressed / active nav)
    "ACCENT":        "#60A5FA",   # light accent blue
    "ON_PRIMARY":    "#FFFFFF",   # text on primary buttons

    # Status colours
    "SUCCESS":       "#22C55E",
    "WARNING":       "#F59E0B",
    "ERROR":         "#EF4444",

    # Text
    "TEXT":          "#FFFFFF",   # primary text (white)
    "TEXT_MUTED":    "#A0AEC0",   # secondary text
    "TEXT_FAINT":    "#5B6E96",   # hints and captions

    # Focus / accessibility
    "FOCUS":         "#60A5FA",   # visible keyboard focus ring

    # Tints (previously hardcoded fills)
    "TINT_SUCCESS":  "#0E2418",   # success toast / medallion fill
    "TINT_WARNING":  "#291D0B",   # warning fill
    "TINT_ERROR":    "#2A1016",   # error fill
    "TINT_INFO":     "#0E1B31",   # info fill
    "TINT_BLUE":     "#12264D",   # blue icon medallion fill
    "TINT_GREEN":    "#0E2A1C",   # green icon medallion fill
    "PRESSED":       "#0A1226",   # secondary button press flash

    # Charts
    "RING_BG":       "#13203C",   # progress ring track

    # Tooltip
    "TOOLTIP_BG":    "#0C1526",
    "TOOLTIP_FG":    "#B8C4DC",

    # Background orbs
    "ORB_1":         "#3B82F6",
    "ORB_2":         "#60A5FA",
    "ORB_3":         "#4F46E5",
}

# ---------------------------------------------------------------------- #
# Light palette (Linear / Vercel inspired: crisp white glass)             #
# ---------------------------------------------------------------------- #
LIGHT_COLORS = {
    # Backgrounds
    "BG":            "#E9EDF5",   # soft cool light grey
    "BG_HIGH":       "#F6F8FC",   # lighter end of the gradient
    "SHADOW":        "#C2CBDD",   # soft grey shadow behind cards
    "OVERLAY":       "#8E9AB2",   # modal dialog dim overlay

    # Glass surfaces
    "GLASS":         "#FFFFFF",   # glass panel fill
    "GLASS_LIGHT":   "#E2EBFA",   # glass on hover / active
    "GLASS_HOVER":   "#F1F5FC",   # card hover fill (subtle)
    "GLASS_INPUT":   "#F2F5FA",   # text fields and entries
    "NAV":           "#EDF1F8",   # sidebar buttons at rest

    # Borders
    "BORDER":        "#C9D4E6",   # standard glass border
    "BORDER_SOFT":   "#DCE4F2",   # subtle divider lines
    "BORDER_GLOW":   "#3B82F6",   # hover glow border

    # Brand accents
    "PRIMARY":       "#2563EB",   # primary blue (contrast on white)
    "PRIMARY_DEEP":  "#1E3A8A",   # deep blue (pressed / active nav)
    "ACCENT":        "#2563EB",   # visible accent on light surfaces
    "ON_PRIMARY":    "#FFFFFF",   # text on primary buttons

    # Status colours
    "SUCCESS":       "#16A34A",
    "WARNING":       "#D97706",
    "ERROR":         "#DC2626",

    # Text
    "TEXT":          "#0B1424",   # primary text (near-black navy)
    "TEXT_MUTED":    "#47586F",   # secondary text
    "TEXT_FAINT":    "#6E7E96",   # hints and captions

    # Focus / accessibility
    "FOCUS":         "#2563EB",   # visible keyboard focus ring

    # Tints
    "TINT_SUCCESS":   "#DCF9E7",
    "TINT_WARNING":   "#FCF0CE",
    "TINT_ERROR":     "#FBE0DD",
    "TINT_INFO":      "#DCE9FB",
    "TINT_BLUE":      "#DCE9FB",
    "TINT_GREEN":     "#DCF9E7",
    "PRESSED":        "#D7E2F4",

    # Charts
    "RING_BG":        "#E3E9F4",

    # Tooltip (stays dark in both themes: maximum contrast)
    "TOOLTIP_BG":     "#1E293B",
    "TOOLTIP_FG":     "#E2E8F0",

    # Background orbs (soft pastel glows on light surfaces)
    "ORB_1": "#93C5FD",
    "ORB_2": "#C7D2FE",
    "ORB_3": "#A5B4FC",
}

# ---------------------------------------------------------------------- #
# Active palette (mutated in place by apply_theme)                        #
# ---------------------------------------------------------------------- #
COLORS = dict(DARK_COLORS)

# Which palette each mode maps to.
_PALETTES = {
    "dark": DARK_COLORS,
    "light": LIGHT_COLORS,
}

# Subscribers that must redraw when the theme changes (canvas content).
_theme_handlers = []


def subscribe(handler) -> None:
    """
    Register a callable invoked (with no arguments) after every
    theme switch. Used by canvas-drawn widgets (background, rings,
    timelines, tooltips) to redraw with the new palette.

    Arguments:
        handler : zero-argument callable.
    """
    _theme_handlers.append(handler)


def current_mode() -> str:
    """Return the active appearance mode ("dark" or "light")."""
    return ctk.get_appearance_mode().lower()


def apply_theme(mode: str, root=None) -> None:
    """
    Switch the whole application to the given appearance mode.

    Steps:
        1. ctk appearance mode (affects internal defaults).
        2. swap the active COLORS dict contents (in place).
        3. re-colour every existing widget by mapping its current
           colour values through the old->new palette.
        4. notify subscribers (background, charts, tooltip) to
           redraw canvas content.

    Args:
        mode : "dark" or "light".
        root : the root window to re-colour (optional).
    """
    mode = mode if mode in _PALETTES else "dark"
    old = dict(COLORS)
    new = _PALETTES[mode]

    try:
        ctk.set_appearance_mode(mode)
    except Exception:
        pass  # some customtkinter builds reject repeated calls

    COLORS.clear()
    COLORS.update(new)
    _PALETTES[mode] = new

    if root is not None:
        _recolor_tree(root, old, new)
    for handler in list(_theme_handlers):
        try:
            handler()
        except Exception:
            pass  # a subscriber must never break a theme switch


def _recolor_tree(root, old: dict, new: dict) -> None:
    """Remap every colour value of every widget through old -> new."""
    # Reverse map: old colour value -> new colour value.
    remap = {}
    for key, value in old.items():
        remap[value] = new.get(key, value)
    remap.update(remap)  # identity entries are implicit below

    _COLOR_OPTIONS = (
        "fg_color", "hover_color", "border_color", "text_color",
        "placeholder_text_color", "scrollbar_button_color",
        "scrollbar_button_hover_color", "progress_color",
    )

    pending = list(root.winfo_children()) if root is not None else []
    while pending:
        widget = pending.pop()
        try:
            if not widget.winfo_exists():
                continue
            for option in _COLOR_OPTIONS:
                try:
                    value = widget.cget(option)
                except (tk.TclError, TypeError):
                    continue
                replaced = remap.get(value, value)
                if replaced != value:
                    try:
                        widget.configure(**{option: replaced})
                    except tk.TclError:
                        pass
            pending.extend(widget.winfo_children())
        except tk.TclError:
            continue


# ---------------------------------------------------------------------- #
# Icons (geometric glyphs - consistently rendered by Segoe UI Symbol)     #
# ---------------------------------------------------------------------- #
ICONS = {
    "LOGO":     "✦",
    "HOME":     "◈",
    "ENCRYPT":  "▣",
    "DECRYPT":  "▤",
    "ABOUT":    "❖",
    "CLOCK":    "◷",
    "MOON":     "◐",
    "SUN":      "☀",
    "GENERATE": "✚",
    "CLEAR":    "✕",
    "ERROR":    "✕",
    "COPY":     "❏",
    "CHECK":    "✓",
    "INFO":     "ℹ",
    "ARROW":    "→",
    "DOT":      "●",
    "SESSIONS": "▣",
    "ALGO":     "✦",
    "LAYERS":   "◫",
    "STATUS":   "●",
    "SHIELD":   "⬡",
    "ANALYSIS": "◔",

    "PRESENTATION": "▶",
    "VIVA":         "◉",
    "ARCHITECTURE": "▦",
    "GUIDE":        "☰",
    "PLAY":         "▶",
    "PAUSE":        "‖",
    "RESTART":      "↺",
    "PREV":         "←",
    "NEXT":         "→",
}

# ---------------------------------------------------------------------- #
# Fonts (consistent hierarchy)                                            #
# ---------------------------------------------------------------------- #
FONTS = {
    "DISPLAY":    ("Segoe UI", 34, "bold"),   # hero heading
    "TITLE":      ("Segoe UI", 24, "bold"),   # page heading
    "HEADING":    ("Segoe UI", 17, "bold"),   # card heading
    "SUBHEADING": ("Segoe UI", 14, "bold"),   # section title
    "BODY":       ("Segoe UI", 13),           # body text
    "SMALL":      ("Segoe UI", 11),           # secondary text
    "MICRO":      ("Segoe UI", 10),           # captions
    "MONO":       ("Consolas", 13),           # code / output
    "MONO_SMALL": ("Consolas", 11),           # formulas
    "STAT_NUMBER": ("Segoe UI", 26, "bold"),  # big stat card numbers
}

# ---------------------------------------------------------------------- #
# Shape & spacing                                                         #
# ---------------------------------------------------------------------- #
RADIUS = {
    "CARD":   26,   # large glass panels
    "PANEL":  20,   # medium panels
    "FIELD":  12,   # entries and text boxes
    "BUTTON": 16,   # action buttons
    "PILL":   13,   # small badges and chips
    "CHIP":   12,   # layer status chips
}

# ---------------------------------------------------------------------- #
# Design grid (one global spacing system for every screen)                #
# ---------------------------------------------------------------------- #
# Every page follows the same vertical rhythm (pixels inside the screen):
#
#   [top bar of the window]
#   ~29 px  (structural gap - see app.py _CONTENT)
#   PAGE_TITLE_Y = 30        -> page title
#   TITLE_GAP   = 8          ->
#   (~32 px title line)      -> subtitle
#   SUBTITLE_GAP = 24        ->
#   (~18 px subtitle line)   -> first section / card
#
# All values are pixels so every screen looks identical at any window
# size; screens place their content below CONTENT_TOP using CARD_GAP.
SPACING = {
    "PAGE_TITLE_Y": 30,      # px: page title top edge (below the top bar)
    "TITLE_GAP": 8,          # px: title bottom -> subtitle top
    "SUBTITLE_GAP": 24,      # px: subtitle bottom -> first card / scroll
    "CONTENT_TOP": 112,      # px: computed - see base_screen.header_top()

    "SECTION_GAP": 24,       # px: between two sections
    "CARD_GAP": 20,          # px: between two cards / panels
    "CARD_PAD_X": 20,        # px: card inner left/right padding
    "CARD_PAD_TOP": 14,      # px: card inner top padding
    "CARD_PAD_BOTTOM": 16,   # px: card inner bottom padding
    "HEADING_GAP": 12,       # px: below a section heading card
}

# Approximate line heights (px) of the font hierarchy, used to lay
# out the page header in pixels.
_FONT_LINE = {
    "DISPLAY": 48,
    "TITLE": 32,
    "HEADING": 24,
    "SUBHEADING": 20,
    "BODY": 18,
    "SMALL": 16,
    "MICRO": 14,
}

# Shadow offset of glass cards (pixels down), creates the soft shadow.
SHADOW_OFFSET = 7

# Window sizes that trigger the compact layout tiers.
# "compact"       -> sidebar collapses to an icon rail, spacing tightens
# "minimum"       -> smallest supported window size
COMPACT_WIDTH = 1080       # below this the sidebar becomes icons only
MIN_WINDOW_WIDTH = 900
MIN_WINDOW_HEIGHT = 620