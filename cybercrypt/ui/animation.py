"""
animation.py
============

Smooth, lightweight animations for a premium feel:

    animate_color     -> smoothly change any colour property
    bind_hover        -> smooth hover for CTk buttons
    bind_smart_hover  -> hover with leave-guard (ignores child
                         widgets, used by glass cards / nav items)
    bind_press_flash  -> click press animation (button "scale" feel)
    bind_focus_ring   -> visible keyboard focus ring
    fade_sequence     -> staggered fade-in for loading cards
    fade_window       -> whole-window alpha fade (screen transitions)

All animations run on widget.after() so they never block the UI,
and every loop is protected against errors raised after a widget
is destroyed (e.g. while closing the window).
"""

from __future__ import annotations

import tkinter as tk

from cybercrypt.utils.helpers import interpolate_color

# Fixed animation timing (milliseconds).
_ANIMATION_STEP_MS = 16  # roughly 60 frames per second


def animate_color(widget, target_color: str, duration_ms: int = 180,
                  start_color: str = None, on_finish=None,
                  property_name: str = "fg_color"):
    """
    Smoothly animate a colour property of a widget.

    Arguments:
        widget        : the CTk widget to animate.
        target_color  : colour to end at (hex string).
        duration_ms   : total animation time in milliseconds.
        start_color   : optional starting colour (defaults to current).
        on_finish     : optional callback called when animation ends.
        property_name : which property to animate ("fg_color",
                        "border_color", ...).
    """
    # Cancel any previous animation running on the same property.
    token = getattr(widget, "_anim_token_" + property_name, 0) + 1
    setattr(widget, "_anim_token_" + property_name, token)

    # The colour we start from: the widget's current colour.
    current = start_color or widget.cget(property_name)
    if current == target_color:
        if on_finish is not None:
            on_finish()
        return

    steps = max(1, int(duration_ms / _ANIMATION_STEP_MS))

    def _step(index: int):
        """Advance the animation by one frame."""
        # Stop if a newer animation took over, or the widget is gone.
        if getattr(widget, "_anim_token_" + property_name, 0) != token:
            return
        try:
            if index >= steps:
                widget.configure(**{property_name: target_color})
                if on_finish is not None:
                    on_finish()
                return
            factor = index / steps
            color = interpolate_color(current, target_color, factor)
            widget.configure(**{property_name: color})
            widget.after(_ANIMATION_STEP_MS, lambda: _step(index + 1))
        except tk.TclError:
            return  # widget was destroyed; stop quietly

    _step(1)


def _resolve(color) -> str:
    """
    Resolve a colour argument at event time.

    Colours may be plain hex strings OR zero-argument callables
    (e.g. ``lambda: COLORS["ACCENT"]``). Callables are evaluated
    when the event fires, so hover / press / focus effects always
    use the CURRENT theme palette after a light/dark switch.

    Arguments:
        color : hex string or callable returning one.

    Returns:
        The resolved hex colour string.
    """
    if callable(color):
        return color()
    return color


def bind_hover(widget, normal_color, hover_color,
               normal_border=None, hover_border=None):
    """
    Attach a smooth hover effect to a CTk button.

    Arguments:
        widget        : the CTk widget to attach the effect to.
        normal_color  : colour at rest (hex or callable).
        hover_color   : colour while the mouse is over the widget.
        normal_border : optional border colour at rest.
        hover_border  : optional border colour while hovering.
    """
    def _on_enter(_event):
        animate_color(widget, _resolve(hover_color), duration_ms=150,
                      property_name="fg_color")
        if hover_border is not None:
            animate_color(widget, _resolve(hover_border), duration_ms=150,
                          property_name="border_color")

    def _on_leave(_event):
        animate_color(widget, _resolve(normal_color), duration_ms=200,
                      property_name="fg_color")
        if normal_border is not None:
            animate_color(widget, _resolve(normal_border), duration_ms=200,
                          property_name="border_color")

    widget.bind("<Enter>", _on_enter)
    widget.bind("<Leave>", _on_leave)


def bind_smart_hover(widget, normal_color, hover_color,
                     normal_border=None, hover_border=None,
                     enabled: callable = None):
    """
    Hover effect that ignores events caused by crossing child widgets.

    Tk fires Enter/Leave when the pointer moves onto a child label,
    which would make card hovers flicker. We detect that with
    winfo_containing() and simply ignore such events.

    Arguments:
        widget        : the widget to attach the effect to.
        normal_color  : colour at rest (hex or callable).
        hover_color   : colour while hovering.
        normal_border : optional border colour at rest.
        hover_border  : optional border colour while hovering.
        enabled       : optional callable returning True when the
                        hover is allowed (e.g. active nav items).
    """
    def _pointer_still_inside(event) -> bool:
        """True when the pointer is over the widget or its children."""
        try:
            under = event.widget.winfo_containing(event.x_root, event.y_root)
        except tk.TclError:
            return False
        node = under
        while node is not None:
            if node == widget:
                return True
            try:
                node = node.master
            except tk.TclError:
                return False
        return False

    def _on_enter(event):
        if enabled is not None and not enabled():
            return
        animate_color(widget, _resolve(hover_color), duration_ms=160,
                      property_name="fg_color")
        if hover_border is not None:
            animate_color(widget, _resolve(hover_border), duration_ms=160,
                          property_name="border_color")

    def _on_leave(event):
        if _pointer_still_inside(event):
            return  # moving onto a child, not leaving the widget
        if enabled is not None and not enabled():
            return
        animate_color(widget, _resolve(normal_color), duration_ms=240,
                      property_name="fg_color")
        if normal_border is not None:
            animate_color(widget, _resolve(normal_border), duration_ms=240,
                          property_name="border_color")

    widget.bind("<Enter>", _on_enter)
    widget.bind("<Leave>", _on_leave)


def bind_press_flash(widget, pressed_color, normal_color=None,
                     property_name: str = "fg_color"):
    """
    Simulate a "button scale" click: quickly darken on press,
    ease back on release.

    Arguments:
        widget        : the widget to attach the effect to.
        pressed_color : colour while the button is pressed
                        (hex or callable).
        normal_color  : colour to return to (defaults to the
                        current colour at press time).
        property_name : colour property to animate.
    """
    def _on_press(_event):
        base = _resolve(normal_color) if normal_color else \
            widget.cget(property_name)
        widget._cc_press_base = base
        animate_color(widget, _resolve(pressed_color), duration_ms=50,
                      start_color=base, property_name=property_name)

    def _on_release(_event):
        base = getattr(widget, "_cc_press_base", None)
        if base:
            animate_color(widget, base, duration_ms=140,
                          property_name=property_name)

    widget.bind("<ButtonPress-1>", _on_press)
    widget.bind("<ButtonRelease-1>", _on_release)


def bind_focus_ring(widget, focus_color,
                    property_name: str = "border_color"):
    """
    Show a visible focus ring for keyboard navigation.

    When the widget receives keyboard focus its border smoothly
    turns into the focus colour; on blur it returns to the
    colour it had before.

    Arguments:
        widget        : the widget to attach the effect to.
        focus_color   : the focus ring colour (hex or callable).
        property_name : colour property used as the ring.
    """
    def _on_focus_in(_event):
        widget._cc_focus_base = widget.cget(property_name)
        animate_color(widget, _resolve(focus_color), duration_ms=150,
                      property_name=property_name)

    def _on_focus_out(_event):
        base = getattr(widget, "_cc_focus_base", None)
        if base:
            animate_color(widget, base, duration_ms=200,
                          property_name=property_name)

    widget.bind("<FocusIn>", _on_focus_in)
    widget.bind("<FocusOut>", _on_focus_out)


def bind_input_focus(widget, focus_color, normal_border=None):
    """
    A focus glow for text fields (entries and text boxes).

    On focus the border animates to the accent focus ring; on blur
    it returns to the normal border. Also registers the widget as
    reachable with the Tab key.

    Arguments:
        widget        : the CTkEntry / CTkTextbox to enhance.
        focus_color   : the focus ring colour (hex or callable).
        normal_border : the border colour to return to (optional;
                        defaults to the colour seen on blur).
    """
    def _on_focus_in(_event):
        widget._cc_focus_base = widget.cget("border_color")
        animate_color(widget, _resolve(focus_color), duration_ms=150,
                      property_name="border_color")

    def _on_focus_out(_event):
        base = getattr(widget, "_cc_focus_base", None) \
            or _resolve(normal_border)
        if not base or base == _resolve(focus_color):
            return
        animate_color(widget, base, duration_ms=220,
                      property_name="border_color")

    widget.bind("<FocusIn>", _on_focus_in)
    widget.bind("<FocusOut>", _on_focus_out)


def fade_sequence(widgets: list, from_color: str, to_color: str,
                  delay_ms: int = 110, duration_ms: int = 260,
                  property_name: str = "fg_color"):
    """
    Fade a list of widgets in one after the other (staggered).

    Used to make cards "load" gracefully when a screen opens.

    Arguments:
        widgets       : widgets to animate, in visual order.
        from_color    : starting colour of each fade.
        to_color      : target colour.
        delay_ms      : delay between the start of each widget.
        duration_ms   : duration of each single fade.
        property_name : colour property to animate.
    """
    for index, widget in enumerate(widgets):
        widget.after(index * delay_ms, lambda w=widget: animate_color(
            w, to_color, duration_ms=duration_ms,
            start_color=from_color, property_name=property_name))


def fade_window(window, target_alpha: float, steps: int = 10,
                interval_ms: int = 12, on_finish=None):
    """
    Smoothly fade the alpha (opacity) of the whole window.

    Arguments:
        window       : the root window.
        target_alpha : final opacity, 0.0 (invisible) .. 1.0 (solid).
        steps        : number of frames in the animation.
        interval_ms  : delay between frames.
        on_finish    : optional callback called when the fade completes.
    """
    def _step(index: int):
        try:
            alpha = target_alpha * (index + 1) / steps
            window.attributes("-alpha", max(0.0, min(1.0, alpha)))
            if index + 1 < steps:
                window.after(interval_ms, lambda: _step(index + 1))
            elif on_finish is not None:
                on_finish()
        except tk.TclError:
            return  # window was closed; stop quietly

    _step(0)
