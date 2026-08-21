"""
base_screen.py
==============

The common base class for every screen. Each screen lives inside
the content area of the main window and can react to being shown.

The base class also provides the shared page header used by every
screen, so titles and subtitles always sit at exactly the same
position and follow the same spacing (see theme.SPACING).
"""

from __future__ import annotations

import sys
import customtkinter as ctk

from cybercrypt.ui.theme import COLORS, FONTS, SPACING

# Approximate line height (px) of the page title / subtitle fonts.
_TITLE_LINE_PX = 32
_SUBTITLE_LINE_PX = 18


class BaseScreen(ctk.CTkFrame):
    """
    A transparent frame that fills the content area.

    Subclasses implement:
        _build_widgets() -> create all widgets (called once).
        on_show()        -> refresh data every time the screen opens.
        on_shortcut()    -> behaviour of the Ctrl+Enter shortcut.
    """

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app  # reference to the main window

        # Fill the whole content area.
        self.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Track the scrollable frame for scroll reset.
        self._scroll_widget = None

        self._build_widgets()

    # ------------------------------------------------------------------ #
    # Safe geometry accessors (winfo_height/width can be 1 before mapping)#
    # ------------------------------------------------------------------ #

    def safe_height(self) -> int:
        """
        Return this screen's real height in pixels.  If the widget
        hasn't been mapped yet (winfo_height() == 1), fall back to
        the app's known content-area height so layout math never
        computes against 1 px.
        """
        h = self.winfo_height()
        if h > 10:
            return h
        _, ch = self.app.content_size()
        return ch

    def safe_width(self) -> int:
        """
        Return this screen's real width in pixels.  Same fallback
        logic as safe_height().
        """
        w = self.winfo_width()
        if w > 10:
            return w
        cw, _ = self.app.content_size()
        return cw

    # ------------------------------------------------------------------ #
    # Shared page header (one grid for every screen)                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def header_top() -> int:
        """
        The Y position (px inside the screen) where the page title
        starts. Subtitle and content are derived from this value.
        """
        return SPACING["PAGE_TITLE_Y"]

    @staticmethod
    def content_top() -> int:
        """
        The Y position (px inside the screen) where the first section
        or the scrollable content starts - always below the header.
        """
        top = SPACING["PAGE_TITLE_Y"] + _TITLE_LINE_PX \
            + SPACING["TITLE_GAP"]
        return top + _SUBTITLE_LINE_PX + SPACING["SUBTITLE_GAP"]

    def _page_header(self, title_text: str, subtitle_text: str):
        """
        Place the standard page title + subtitle at the grid position.

        Arguments:
            title_text    : the page title.
            subtitle_text : the one-line subtitle under the title.

        Returns:
            (title_label, subtitle_label) so screens can update them.
        """
        title = ctk.CTkLabel(self, text=title_text,
                             font=FONTS["TITLE"],
                             text_color=COLORS["TEXT"])
        title.place(x=0, y=self.header_top(), anchor="nw")

        subtitle = ctk.CTkLabel(self, text=subtitle_text,
                                font=FONTS["BODY"],
                                text_color=COLORS["TEXT_MUTED"])
        subtitle.place(x=0, y=self.header_top() + _TITLE_LINE_PX
                       + SPACING["TITLE_GAP"], anchor="nw")
        return title, subtitle

    def _page_scroll(self, top: int = None) -> ctk.CTkScrollableFrame:
        """
        Create the standard scrollable content area below the header.

        This is the ONE primary scrolling container that works for ALL pages.
        It properly accounts for header and footer, removes nested scrollbars,
        and ensures every page scrolls from first pixel to last pixel.

        The scroll fills the available space exactly (it is re-fitted on
        every resize), so content is never clipped and never reaches
        into the footer or sidebar areas.

        Arguments:
            top : optional custom top offset (px); defaults to the
                  standard content position.

        Returns:
            A transparent CTkScrollableFrame filling the rest of the
            screen below the header.
        """
        top = self.content_top() if top is None else top
        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=COLORS["BORDER"],
            scrollbar_button_hover_color=COLORS["ACCENT"],
        )

        def _fit(_event=None):
            height = self.safe_height()
            if height < 10:
                return
            remaining = max(0, height - top)
            scroll.place(x=0, y=top, relwidth=1,
                         relheight=min(remaining / height, 1.0))

        self.bind("<Configure>", _fit)
        _fit()

        # Store reference for scroll reset on screen switch.
        self._scroll_widget = scroll

        return scroll

    def reset_scroll(self):
        """Reset the scroll position to the top (called on screen switch)."""
        if self._scroll_widget is not None:
            try:
                self._scroll_widget._parent_canvas.yview_moveto(0.0)
            except Exception:
                pass

    def _bind_mousewheel_recursive(self, widget, canvas):
        """
        Recursively bind mouse wheel events to explicitly route scrolling
        to the outer canvas, overriding default textbox/entry scrolling.
        """
        def on_scroll(event):
            try:
                if sys.platform.startswith("win"):
                    canvas.yview("scroll", -int(event.delta / 6), "units")
                elif sys.platform == "darwin":
                    canvas.yview("scroll", -event.delta, "units")
                else:
                    canvas.yview_scroll(-1 if event.num == 4 else 1, "units")
            except Exception:
                pass
            return "break"

        if not getattr(widget, "_mousewheel_bound", False):
            try:
                widget.bind("<MouseWheel>", on_scroll, add="+")
                widget.bind("<Button-4>", on_scroll, add="+")
                widget.bind("<Button-5>", on_scroll, add="+")
                widget._mousewheel_bound = True
            except Exception:
                pass

        try:
            children = widget.winfo_children()
        except Exception:
            children = []

        for child in children:
            self._bind_mousewheel_recursive(child, canvas)

    # ------------------------------------------------------------------ #
    # Hooks overridden by subclasses                                      #
    # ------------------------------------------------------------------ #

    def _build_widgets(self):
        """Create every widget of the screen (called once)."""
        raise NotImplementedError

    def on_show(self):
        """Called every time the screen becomes visible."""
        pass

    def on_shortcut(self):
        """Called when the user presses Ctrl+Enter."""
        pass
