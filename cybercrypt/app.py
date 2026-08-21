"""
app.py
======

The main application window of CyberCrypt Pro.

Responsibilities:
    * window setup (title, icon, centering, minimum size, fade-in)
    * the animated glassmorphism background
    * the premium top bar (project name, current screen, clock,
      theme indicator, version)
    * the sidebar with glowing navigation indicators
    * the professional status bar
    * screen switching with a smooth window fade
    * glass confirmation dialogs
    * session statistics shared by all screens
"""

from __future__ import annotations

import math
import time
import tkinter as tk

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk

from cybercrypt import __subtitle__, __title__, __version__
from cybercrypt.analysis import AnalysisReport
from cybercrypt.ui import background as ui_background
from cybercrypt.ui.dialogs import GlassDialog
from cybercrypt.ui.screens.about_screen import AboutScreen
from cybercrypt.ui.screens.analysis_screen import AnalysisScreen
from cybercrypt.ui.screens.architecture_screen import ArchitectureScreen
from cybercrypt.ui.screens.dashboard_screen import DashboardScreen
from cybercrypt.ui.screens.decrypt_screen import DecryptScreen
from cybercrypt.ui.screens.encrypt_screen import EncryptScreen
from cybercrypt.ui.screens.guide_screen import GuideScreen

from cybercrypt.ui.statusbar import StatusBar
from cybercrypt.ui.theme import (
    COMPACT_WIDTH,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    COLORS,
    FONTS,
    ICONS,
    RADIUS,
    apply_theme,
    current_mode,
    subscribe,
)
from cybercrypt.ui import tooltip as ui_tooltip
from cybercrypt.ui.widgets import NavButton
from cybercrypt.utils.helpers import format_clock
from cybercrypt.utils.settings import load_settings, save_settings

# Sidebar navigation: two groups of (screen key, icon glyph, label).
_NAV_GROUPS = (
    ("WORKSPACE", (
        ("dashboard", ICONS["HOME"], "Dashboard"),
        ("encrypt",   ICONS["ENCRYPT"], "Encrypt"),
        ("decrypt",   ICONS["DECRYPT"], "Decrypt"),
        ("analysis",  ICONS["ANALYSIS"], "Analysis"),
    )),
    ("LEARN", (
        ("architecture", ICONS["ARCHITECTURE"], "Architecture"),
        ("guide",        ICONS["GUIDE"], "Guide"),
        ("about",        ICONS["ABOUT"], "About"),
    )),
)

# Flat list of every (key, icon, label) in visual order.
_NAV_ITEMS = tuple(
    item for _caption, items in _NAV_GROUPS for item in items)

# Window geometry.
_WINDOW_WIDTH = 1280
_WINDOW_HEIGHT = 820

# Screen key -> title shown in the top bar chip.
_SCREEN_TITLES = {
    "dashboard": "Dashboard",
    "encrypt": "Encrypt",
    "decrypt": "Decrypt",
    "analysis": "Analysis",
    "architecture": "Architecture",
    "guide": "Guide",
    "about": "About",
}

# Screen key -> screen class (built lazily on first visit).
_SCREEN_CLASSES = {
    "dashboard": DashboardScreen,
    "encrypt": EncryptScreen,
    "decrypt": DecryptScreen,
    "analysis": AnalysisScreen,
    "architecture": ArchitectureScreen,
    "guide": GuideScreen,
    "about": AboutScreen,
}

# Responsive layout fractions (relative to the window).
# Content area ends well above the status bar to prevent any overlap.
_TOP_BAR = (0.02, 0.02, 0.96, 0.085)
_SIDEBAR = (0.02, 0.14, 0.185, 0.79)
_CONTENT = (0.225, 0.14, 0.755, 0.79)
_STATUS_BAR = (0.02, 0.945, 0.96, 0.040)

# Compact (icon rail) layout, used when the window is narrower than
# COMPACT_WIDTH: a slim sidebar with icon-only items and a wider
# content column.
_SIDEBAR_RAIL = (0.02, 0.14, 0.085, 0.79)
_CONTENT_WIDE = (0.125, 0.14, 0.855, 0.79)


class _LazyScreens(dict):
    """
    A screens dictionary that builds a screen the first time it is
    accessed.

    The eight non-dashboard screens are expensive to construct, so
    they are created on first visit - the one-time cost is hidden
    behind the screen-switch fade. Dict lookups behave exactly like
    a plain dict once every screen has been built.
    """

    def __init__(self, app: "CyberCryptApp", content: ctk.CTkFrame):
        super().__init__()
        self._app = app
        self._content = content

    def __contains__(self, key: str) -> bool:
        # Membership checks must not force a build: any registered
        # screen key counts as "present" (it will be built on access).
        return key in _SCREEN_CLASSES

    def __missing__(self, key: str):
        screen = _SCREEN_CLASSES[key](self._content, self._app)
        screen.place_forget()
        dict.__setitem__(self, key, screen)
        return screen


class SessionState:
    """
    In-memory statistics for the current session.
    No database: everything resets when the app closes.
    """

    def __init__(self):
        self.encrypt_count = 0       # how many messages were encrypted
        self.decrypt_count = 0       # how many messages were decrypted
        self.processed_chars = 0     # total characters handled
        self.last_keys = None        # keys from the last encryption
        self.last_analysis = None    # AnalysisReport from the last run
        self.last_decrypt_time = 0.0 # decryption time (seconds) from the
                                     # most recent decrypt run


class CyberCryptApp(ctk.CTk):
    """The main window of the application."""

    def __init__(self):
        # Load persisted settings FIRST so theme applies before any widget
        # is created.
        self.settings = load_settings()
        self._time_format = self.settings.get("time_format", "24")
        self._sidebar_compact = False
        self._nav_button_frames = []  # for compact toggling

        super().__init__(fg_color=COLORS["BG"])

        # Shared session state.
        self.session = SessionState()

        # Screen management.
        self.screens = {}
        self.current_screen = None
        self.nav_buttons = {}
        self._switching = False
        self._pending_switch = None
        self._dialog_open = False

        # Window basics.
        self.title(f"{__title__} — {__subtitle__}")
        self.geometry(f"{_WINDOW_WIDTH}x{_WINDOW_HEIGHT}")
        self.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self._center_window()

        self._build_background()
        self._build_topbar()
        self._build_sidebar()
        self._build_statusbar()
        self._build_screens()
        self._sidebar_frame.lift()
        self.status_bar.lift()
        self._set_window_icon()

        # Subscribe to theme changes (from other parts of the app).
        subscribe(self._on_theme_changed)

        # Keyboard shortcuts (accessibility).
        self.bind("<Control-Return>", self._on_shortcut)
        self.bind("<Control-Shift-Return>", self._on_decrypt_shortcut)
        self.bind("<Control-c>", self._on_copy_shortcut)

        # Responsive sidebar: switch to icon rail below COMPACT_WIDTH.
        self.bind("<Configure>", self._on_configure)

        # Close gracefully: stop the background animation first.
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Render the first paint right now: _build_screens() already
        # placed the dashboard and its layout pass ran inside
        # _complete_switch(), so the window opens fully painted and
        # responsive instead of freezing while mainloop renders it.
        self.update_idletasks()

        # Live clock in the top bar.
        self._tick_clock()

    # ------------------------------------------------------------------ #
    # Construction                                                        #
    # ------------------------------------------------------------------ #

    def _center_window(self):
        """Place the window in the middle of the screen."""
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = max(0, (screen_width - _WINDOW_WIDTH) // 2)
        y = max(0, (screen_height - _WINDOW_HEIGHT) // 2)
        self.geometry(f"{_WINDOW_WIDTH}x{_WINDOW_HEIGHT}+{x}+{y}")

    def _build_background(self):
        """The animated glass backdrop behind everything."""
        self.bg_canvas = tk.Canvas(self, bg=COLORS["BG"],
                                   highlightthickness=0, bd=0)
        self.bg_canvas.pack(fill="both", expand=True)

        self.background = ui_background.GlassBackground(self.bg_canvas)
        self.bg_canvas.bind(
            "<Configure>",
            lambda event: self.background.request_refresh(event.width,
                                                          event.height),
        )
        self.background.start_motion()

    def _build_topbar(self):
        """The premium glass bar: logo, titles and live info chips."""
        bar = ctk.CTkFrame(self, corner_radius=RADIUS["PANEL"],
                           fg_color=COLORS["GLASS"],
                           border_width=1, border_color=COLORS["BORDER"])
        bar.place(relx=_TOP_BAR[0], rely=_TOP_BAR[1],
                  relwidth=_TOP_BAR[2], relheight=_TOP_BAR[3])

        # --- Logo ------------------------------------------------------- #
        logo_box = ctk.CTkFrame(bar, corner_radius=14, width=46, height=46,
                                fg_color=COLORS["PRIMARY_DEEP"],
                                border_width=1, border_color=COLORS["ACCENT"])
        logo_box.pack(side="left", padx=(14, 12))
        logo_label = ctk.CTkLabel(logo_box, text=ICONS["LOGO"],
                                  font=("Segoe UI", 22, "bold"),
                                  text_color=COLORS["ACCENT"])
        logo_label.place(relx=0.5, rely=0.5, anchor="center")

        # --- Titles ------------------------------------------------------- #
        titles = ctk.CTkFrame(bar, fg_color="transparent")
        titles.pack(side="left", padx=(0, 12))
        title = ctk.CTkLabel(titles, text=__title__,
                             font=("Segoe UI", 17, "bold"),
                             text_color=COLORS["TEXT"])
        title.pack(anchor="w")
        subtitle = ctk.CTkLabel(titles, text=__subtitle__,
                                font=FONTS["MICRO"],
                                text_color=COLORS["TEXT_MUTED"])
        subtitle.pack(anchor="w")

        # --- Live info chips (packed from right) -------------------------- #
        self._version_chip_frame, self._version_chip, _ = self._make_chip(
            bar, ICONS["SHIELD"], f"v{__version__}")
        self._theme_chip_frame, self._theme_chip, self._theme_chip_icon = self._make_chip(
            bar, ICONS["MOON"] if current_mode() == "dark" else ICONS["SUN"],
            "Dark" if current_mode() == "dark" else "Light")
        self._clock_chip_frame, self._clock_chip, _ = self._make_chip(
            bar, ICONS["CLOCK"], "--:--:--")
        self._screen_chip_frame, self._screen_chip, _ = self._make_chip(
            bar, ICONS["HOME"], "Dashboard")

        # Theme toggle: click the theme chip to cycle dark/light.
        self._theme_chip_frame.bind("<Button-1>", lambda _e: self.toggle_theme())
        self._theme_chip.bind("<Button-1>", lambda _e: self.toggle_theme())
        ui_tooltip.bind_tooltip(self._theme_chip_frame,
                                "Click to toggle theme")
        self._theme_chip_frame.configure(cursor="hand2")
        self._theme_chip.configure(cursor="hand2")

        # Clock toggle: click the clock chip to cycle 12/24 hour format.
        self._clock_chip_frame.bind("<Button-1>", lambda _e: self.toggle_time_format())
        self._clock_chip.bind("<Button-1>", lambda _e: self.toggle_time_format())
        ui_tooltip.bind_tooltip(self._clock_chip_frame,
                                "Click to toggle 12/24 hour")
        self._clock_chip_frame.configure(cursor="hand2")
        self._clock_chip.configure(cursor="hand2")

    def _make_chip(self, bar, icon: str, text: str):
        """
        A small glass info chip (icon + text) in the top bar.

        Arguments:
            bar  : the top bar frame.
            icon : icon glyph.
            text : chip label.

        Returns:
            (frame, text_label, icon_label) so the label and icon
            can be updated and the frame can be bound for clicks/tooltip.
        """
        chip = ctk.CTkFrame(bar, corner_radius=RADIUS["PILL"],
                            fg_color=COLORS["NAV"],
                            border_width=1,
                            border_color=COLORS["BORDER_SOFT"])
        chip.pack(side="right", padx=(14, 0), pady=4)

        icon_label = ctk.CTkLabel(chip, text=icon,
                                  font=("Segoe UI", 11),
                                  text_color=COLORS["TEXT_FAINT"])
        icon_label.pack(side="left", padx=(10, 4), pady=4)

        text_label = ctk.CTkLabel(chip, text=text,
                                  font=FONTS["SMALL"],
                                  text_color=COLORS["TEXT_MUTED"])
        text_label.pack(side="left", padx=(0, 10), pady=4)
        return chip, text_label, icon_label

    def _build_sidebar(self):
        """The glass navigation sidebar (two groups of items)."""
        self._sidebar_frame = ctk.CTkFrame(self, corner_radius=RADIUS["CARD"],
                                           fg_color=COLORS["GLASS"],
                                           border_width=1, border_color=COLORS["BORDER"])
        self._sidebar_frame.place(relx=_SIDEBAR[0], rely=_SIDEBAR[1],
                                  relwidth=_SIDEBAR[2], relheight=_SIDEBAR[3])

        self._nav_button_frames = []

        # Group captions.
        self._sidebar_caption_workspace = ctk.CTkLabel(self._sidebar_frame,
            text="NAVIGATION", font=FONTS["MICRO"], text_color=COLORS["TEXT_FAINT"])
        self._sidebar_caption_workspace.place(relx=0.08, rely=0.035, anchor="w")

        # Workspace group: four tools.
        for index in range(4):
            key, icon, label = _NAV_ITEMS[index]
            button = NavButton(self._sidebar_frame, icon, label,
                               command=lambda k=key: self.switch_screen(k))
            button.place(relx=0.07, rely=0.068 + index * 0.084,
                         relwidth=0.86, relheight=0.068)
            self.nav_buttons[key] = button
            self._nav_button_frames.append(button)

        # Divider between the groups.
        self._sidebar_divider = ctk.CTkFrame(self._sidebar_frame, height=1,
                                             fg_color=COLORS["BORDER_SOFT"],
                                             corner_radius=0)
        self._sidebar_divider.place(relx=0.08, rely=0.415, relwidth=0.84)

        # Learn group: study pages.
        self._sidebar_caption_learn = ctk.CTkLabel(self._sidebar_frame,
            text="LEARN", font=FONTS["MICRO"], text_color=COLORS["TEXT_FAINT"])
        self._sidebar_caption_learn.place(relx=0.08, rely=0.45, anchor="w")

        for index in range(4, len(_NAV_ITEMS)):
            key, icon, label = _NAV_ITEMS[index]
            button = NavButton(self._sidebar_frame, icon, label,
                               command=lambda k=key: self.switch_screen(k))
            button.place(relx=0.07, rely=0.483 + (index - 4) * 0.095,
                         relwidth=0.86, relheight=0.072)
            self.nav_buttons[key] = button
            self._nav_button_frames.append(button)

        # Footer hint.
        self._sidebar_hint = ctk.CTkLabel(self._sidebar_frame,
            text="Offline · No data leaves this device",
            font=FONTS["MICRO"], text_color=COLORS["TEXT_FAINT"])
        self._sidebar_hint.place(relx=0.08, rely=0.945, anchor="w")

    def _build_screens(self):
        """Create the content area and register the lazy screens.

        Only the dashboard is built eagerly; every other screen is
        constructed on its first visit, which keeps the startup fast
        without changing how screens are stored or switched.
        """
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.place(relx=_CONTENT[0], rely=_CONTENT[1],
                      relwidth=_CONTENT[2], relheight=_CONTENT[3])

        self.screens = _LazyScreens(self, content)
        self.switch_screen("dashboard")

    def _build_statusbar(self):
        """The professional status bar at the bottom."""
        self.status_bar = StatusBar(self)
        self.status_bar.place(relx=_STATUS_BAR[0], rely=_STATUS_BAR[1],
                              relwidth=_STATUS_BAR[2],
                              relheight=_STATUS_BAR[3])

    # ------------------------------------------------------------------ #
    # Responsive layout & theme handling                                  #
    # ------------------------------------------------------------------ #

    def _on_configure(self, event):
        """Handle root window configure: responsive sidebar switching."""
        if event.widget is not self:
            return
        width = event.width
        compact = width < COMPACT_WIDTH
        if compact != self._sidebar_compact:
            self._apply_sidebar_compact(compact)

    def _apply_sidebar_compact(self, compact: bool):
        """
        Switch sidebar between full labels and icon-only rail.

        Arguments:
            compact : True = icon rail, False = full labels.
        """
        self._sidebar_compact = compact
        if compact:
            # Hide captions, divider, hint.
            self._sidebar_caption_workspace.place_forget()
            self._sidebar_caption_learn.place_forget()
            self._sidebar_divider.place_forget()
            self._sidebar_hint.place_forget()
            # Switch sidebar frame geometry to rail.
            self._sidebar_frame.place_configure(
                relx=_SIDEBAR_RAIL[0], rely=_SIDEBAR_RAIL[1],
                relwidth=_SIDEBAR_RAIL[2], relheight=_SIDEBAR_RAIL[3])
            # Content area expands.
            for screen in self.screens.values():
                screen.place_configure(
                    relx=_CONTENT_WIDE[0], rely=_CONTENT_WIDE[1],
                    relwidth=_CONTENT_WIDE[2], relheight=_CONTENT_WIDE[3])
            # Compact each NavButton.
            for btn in self._nav_button_frames:
                btn.set_compact(True)
            # Re-place nav buttons in rail: stacked vertically with even spacing.
            for index, btn in enumerate(self._nav_button_frames):
                rely = 0.02 + index * 0.105
                btn.place_configure(relx=0.10, rely=rely, relwidth=0.80, relheight=0.09)
        else:
            # Restore full sidebar geometry.
            self._sidebar_frame.place_configure(
                relx=_SIDEBAR[0], rely=_SIDEBAR[1],
                relwidth=_SIDEBAR[2], relheight=_SIDEBAR[3])
            # Content area back to normal.
            for screen in self.screens.values():
                screen.place_configure(
                    relx=_CONTENT[0], rely=_CONTENT[1],
                    relwidth=_CONTENT[2], relheight=_CONTENT[3])
            # Restore captions, divider, hint.
            self._sidebar_caption_workspace.place(relx=0.08, rely=0.035, anchor="w")
            self._sidebar_divider.place(relx=0.08, rely=0.415, relwidth=0.84)
            self._sidebar_caption_learn.place(relx=0.08, rely=0.45, anchor="w")
            self._sidebar_hint.place(relx=0.08, rely=0.945, anchor="w")
            # Restore each NavButton to full layout.
            for btn in self._nav_button_frames:
                btn.set_compact(False)
            # Workspace group (first 4).
            for index in range(4):
                btn = self._nav_button_frames[index]
                btn.place_configure(relx=0.07, rely=0.068 + index * 0.084,
                                    relwidth=0.86, relheight=0.068)
            # Learn group (remaining).
            for index in range(4, len(self._nav_button_frames)):
                btn = self._nav_button_frames[index]
                btn.place_configure(relx=0.07, rely=0.483 + (index - 4) * 0.095,
                                    relwidth=0.86, relheight=0.072)

    def _on_theme_changed(self, mode: str):
        """
        Callback from theme.subscribe when the theme changes.

        Persists the new mode and updates the theme chip.
        """
        self.settings["theme"] = mode
        save_settings(self.settings)
        icon = ICONS["MOON"] if mode == "dark" else ICONS["SUN"]
        text = "Dark" if mode == "dark" else "Light"
        self._theme_chip.configure(text=text)
        self._theme_chip_icon.configure(text=icon)

    def toggle_theme(self):
        """Cycle the application theme (dark <-> light)."""
        new_mode = "light" if current_mode() == "dark" else "dark"
        apply_theme(new_mode, root=self)

    def toggle_time_format(self):
        """Cycle the clock format (12h <-> 24h)."""
        self._time_format = "12" if self._time_format == "24" else "24"
        self.settings["time_format"] = self._time_format
        save_settings(self.settings)
        # Immediate clock update.
        self._clock_chip.configure(text=format_clock(time.time(), self._time_format))

    # ------------------------------------------------------------------ #
    # Screen navigation                                                   #
    # ------------------------------------------------------------------ #

    def switch_screen(self, screen_key: str):
        """
        Switch to another screen.

        If a switch is still in progress (e.g. a heavy screen is
        rendering) the request is queued and executed when the
        current switch finishes, so navigation is never dropped.

        Arguments:
            screen_key : one of the registered screen keys.
        """
        if screen_key not in self.screens:
            return
        if screen_key == self.current_screen:
            return
        if self._switching:
            self._pending_switch = screen_key
            return

        self._switching = True
        self._complete_switch(screen_key)

    def _complete_switch(self, screen_key: str):
        """Finish the switch: swap the visible screen and fade back in."""
        target = self.screens[screen_key]

        # Hide the old screen, show the new one.
        if self.current_screen is not None:
            self.screens[self.current_screen].place_forget()
        target.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Force the mapping pass: on some systems (high-DPI, layered
        # windows) the fresh place() stays pending until idletasks run,
        # which would leave the new screen invisible.
        self.update_idletasks()

        # Refresh the new screen and reset its scroll position.
        self.current_screen = screen_key
        target.on_show()
        if hasattr(target, "reset_scroll"):
            target.reset_scroll()
        self._update_nav()
        self.set_status("Ready", kind="ready")

        self._switching = False

        # Run any navigation that was queued during this switch.
        pending = getattr(self, "_pending_switch", None)
        if pending is not None and pending != screen_key:
            self._pending_switch = None
            self.switch_screen(pending)

    def _update_nav(self):
        """Highlight the nav item of the active screen + top bar chip."""
        self._screen_chip.configure(
            text=_SCREEN_TITLES.get(self.current_screen, "Dashboard"))

        for key, button in self.nav_buttons.items():
            button.set_active(key == self.current_screen)

    # ------------------------------------------------------------------ #
    # Status & dialogs                                                    #
    # ------------------------------------------------------------------ #

    def set_status(self, text: str, kind: str = "idle"):
        """
        Update the status bar message.

        Arguments:
            text : e.g. "Encrypting...", "Completed", "Copied".
            kind : "idle", "ready", "busy", "success", "warning", "error".
        """
        self.status_bar.set_status(text, kind)

    def show_dialog(self, title: str, message: str, kind: str = "info",
                    on_result=None):
        """
        Show a modal glass dialog (one at a time).

        Arguments:
            title     : dialog heading.
            message   : body text.
            kind      : "success", "warning", "error", "info", "confirm".
            on_result : callback receiving True/False when closed.

        Returns:
            The dialog instance (for programmatic closing) or None if
            a dialog is already open.
        """
        if self._dialog_open:
            return None
        self._dialog_open = True

        def _finished(result):
            self._dialog_open = False
            if on_result is not None:
                on_result(result)

        dialog = GlassDialog.show(self, title, message, kind=kind,
                                  on_result=_finished)
        self._last_dialog = dialog
        return dialog

    def publish_analysis(self, report: AnalysisReport):
        """
        Store an analysis report and refresh the Analysis screen.

        Called by the Encrypt screen after a completed encryption.
        The report is kept even while the user is elsewhere, so the
        dashboard is already populated when they navigate to it.

        Arguments:
            report : the fresh AnalysisReport to publish.
        """
        self.session.last_analysis = report
        screen = self.screens.get("analysis")
        if (screen is not None and self.current_screen == "analysis"):
            screen.refresh_report(report)
            self.set_status("Analysis Updated", kind="success")

    # ------------------------------------------------------------------ #
    # Clock & shortcuts                                                   #
    # ------------------------------------------------------------------ #

    def _tick_clock(self):
        """Update the top bar clock once per second."""
        self._clock_chip.configure(
            text=format_clock(time.localtime(time.time()), self._time_format))
        self.after(1000, self._tick_clock)

    def _on_shortcut(self, _event):
        """Ctrl+Enter -> main action of the current screen."""
        screen = self.screens.get(self.current_screen)
        if screen is not None:
            screen.on_shortcut()

    def _on_decrypt_shortcut(self, _event):
        """Ctrl+Shift+Enter -> decrypt from anywhere."""
        screen = self.screens["decrypt"]
        if self.current_screen != "decrypt":
            self.switch_screen("decrypt")
        screen.on_shortcut()

    def _on_copy_shortcut(self, _event):
        """Ctrl+C -> copy the output of the current screen."""
        screen = self.screens.get(self.current_screen)
        if screen is not None and hasattr(screen, "_copy_result"):
            screen._copy_result()

    # ------------------------------------------------------------------ #
# Window geometry helpers                                              #
    # ------------------------------------------------------------------ #

    def content_size(self) -> tuple:
        """
        Return the content area's (width, height) in pixels, derived
        from the window's own geometry.  Correct even before the window
        is mapped (winfo_height() would return 1 at that point).
        """
        geo = self.geometry()                       # "1280x820+X+Y"
        parts = geo.split("+")
        try:
            w, h = int(parts[0].split("x")[0]), int(parts[0].split("x")[1])
        except (ValueError, IndexError):
            w, h = _WINDOW_WIDTH, _WINDOW_HEIGHT
        cw = int(w * _CONTENT[2])
        ch = int(h * _CONTENT[3])
        return cw, ch

    # ------------------------------------------------------------------ #
    # Window lifecycle                                                    #
    # ------------------------------------------------------------------ #

    def _on_close(self):
        """Stop animations and close the window cleanly."""
        try:
            self.background.stop_motion()
        except Exception:
            pass
        ui_tooltip.clear_tooltip()
        self.destroy()

    # ------------------------------------------------------------------ #
    # Window icon (generated, no asset file needed)                       #
    # ------------------------------------------------------------------ #

    def _set_window_icon(self):
        """Generate a hexagon logo and register several icon sizes."""
        photos = []
        for size in (16, 32, 64, 128):
            image = self._build_icon_image(size)
            photos.append(ImageTk.PhotoImage(image))
        self._icon_photos = photos
        self.iconphoto(True, *photos)

    @staticmethod
    def _build_icon_image(size: int) -> Image.Image:
        """
        Draw the CyberCrypt hexagon logo at a given size.

        Arguments:
            size : icon edge length in pixels.

        Returns:
            An RGBA image ready for iconphoto().
        """
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        half = size / 2

        # Rounded blue tile with accent outline.
        draw.rounded_rectangle((0, 0, size - 1, size - 1),
                               radius=size // 4, fill="#1D4ED8")
        draw.rounded_rectangle((max(1, size // 32), max(1, size // 32),
                                size - 2, size - 2),
                               radius=size // 4,
                               outline="#60A5FA", width=max(1, size // 32))

        # White hexagon - the "crypto shield".
        radius = size * 0.30
        points = [
            (half + radius * math.cos(math.radians(angle)),
             half + radius * math.sin(math.radians(angle)))
            for angle in range(0, 360, 60)
        ]
        draw.polygon(points, outline="#FFFFFF",
                     width=max(2, size // 16))
        return image
