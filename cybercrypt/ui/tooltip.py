"""
tooltip.py
==========

Phase 3 : lightweight glass tooltips.

bind_tooltip(widget, text) attaches a small explanation bubble to
any widget. The bubble appears after a short hover delay, follows
the mouse, stays on screen and disappears on leave / click /
keyboard focus change.

Implementation notes:
    * a single overrideredirect Toplevel is reused by all tooltips
      (cheap, no flicker, one window per app)
    * the label is a plain tk.Label for speed - a Toplevel cannot
      be a CTk widget
    * all scheduling uses after(), so nothing ever blocks
"""

from __future__ import annotations

import tkinter as tk

from cybercrypt.ui.theme import COLORS, FONTS

_HOVER_DELAY_MS = 450   # how long the mouse must stay before showing
_HIDE_DELAY_MS = 150    # grace period before hiding after leave
_MARGIN = 14            # distance from the pointer
_WRAP = 320             # maximum tooltip width in pixels

# Shared bubble state (created lazily on first use).
_bubble = None          # the Toplevel
_label = None           # its tk.Label
_timer = None           # pending show / hide after id
_root = None            # any living widget of the app (for after_cancel)
_widget = None          # the widget the bubble belongs to


def bind_tooltip(widget, text: str):
    """
    Attach an explanation bubble to a widget.

    Arguments:
        widget : any Tk / CTk widget.
        text   : the explanation to show on hover.
    """
    def _on_enter(_event):
        _schedule_show(widget, text)

    def _on_leave(_event):
        _schedule_hide()

    widget.bind("<Enter>", _on_enter, add="+")
    widget.bind("<Leave>", _on_leave, add="+")
    widget.bind("<Button-1>", lambda _e: _hide_now(), add="+")


def _schedule_show(widget, text: str):
    """Show the bubble after the hover delay (only if still hovering)."""
    global _timer, _root
    _cancel_timer()
    _root = widget
    _timer = widget.after(_HOVER_DELAY_MS, lambda: _show(widget, text))


def _schedule_hide():
    """Hide the bubble a moment after the pointer leaves."""
    global _timer
    _cancel_timer()
    if _bubble is not None and _root is not None:
        _timer = _root.after(_HIDE_DELAY_MS, _hide_now)


def _show(widget, text: str):
    """Create or update the shared bubble and place it near the mouse."""
    global _bubble, _label, _widget
    if not widget.winfo_exists():
        return
    _widget = widget

    if _bubble is None:
        _bubble = tk.Toplevel(widget)
        _bubble.overrideredirect(True)
        _bubble.attributes("-topmost", True)
        _label = tk.Label(
            _bubble,
            text=text,
            background=COLORS["TOOLTIP_BG"],
            foreground=COLORS["TOOLTIP_FG"],
            font=FONTS["MICRO"],
            justify="left",
            wraplength=_WRAP,
            padx=10,
            pady=6,
            borderwidth=1,
            relief="solid",
            highlightbackground=COLORS["BORDER"],
            highlightcolor=COLORS["BORDER"],
            highlightthickness=1,
        )
        _label.pack()

    # Re-apply colours on every show so tooltips always match the
    # current theme (palette may have switched while hidden).
    _label.configure(
        text=text,
        background=COLORS["TOOLTIP_BG"],
        foreground=COLORS["TOOLTIP_FG"],
        highlightbackground=COLORS["BORDER"],
        highlightcolor=COLORS["BORDER"],
    )
    _bubble.update_idletasks()

    # Place the bubble above the pointer, keeping it on screen.
    pointer_x = widget.winfo_pointerx()
    pointer_y = widget.winfo_pointery()
    width = _bubble.winfo_reqwidth()
    height = _bubble.winfo_reqheight()
    screen_width = widget.winfo_screenwidth()

    x = min(pointer_x + _MARGIN, screen_width - width - 6)
    y = pointer_y - height - _MARGIN
    if y < 6:
        y = pointer_y + _MARGIN   # below the pointer if no room above

    _bubble.geometry(f"+{x}+{y}")
    _bubble.deiconify()
    _bubble.lift()


def _hide_now():
    """Remove the bubble immediately."""
    global _widget
    _cancel_timer()
    _widget = None
    if _bubble is not None:
        try:
            _bubble.withdraw()
        except tk.TclError:
            return


def _cancel_timer():
    """Cancel any pending show / hide callback."""
    global _timer
    if _timer is not None:
        try:
            _root.after_cancel(_timer)
        except Exception:
            pass
        _timer = None


def clear_tooltip():
    """Hide the bubble (called when the window closes)."""
    _hide_now()
