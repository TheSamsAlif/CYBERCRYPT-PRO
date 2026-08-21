"""
guide_screen.py
===============

Phase 5 : Guide page.

Everything a student needs to navigate the application:

    * How to use it        - encrypt / decrypt / analysis / export
    * Keyboard shortcuts   - the full shortcut list
    * Project information  - name, version, Python, framework,
                             architecture, algorithm stack, lines of
                             code, number of modules
    * Algorithm overview   - three premium cards (purpose, advantages,
                             limitations) reusing the analysis data

Lines of code and module counts are computed on the fly from the
cybercrypt/ package, so they always reflect the real project.
"""

from __future__ import annotations

import os
import sys

import customtkinter as ctk

from cybercrypt import __subtitle__, __title__, __version__
from cybercrypt.analysis import ALGORITHM_OVERVIEW, ALGORITHM_STACK
from cybercrypt.ui.screens.base_screen import BaseScreen
from cybercrypt.ui.theme import COLORS, FONTS, ICONS
from cybercrypt.ui.widgets import badge, glass_panel, section_heading

_PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))


def _project_stats() -> dict:
    """
    Count the Python modules and lines of code of cybercrypt/.

    Returns:
        {"modules": int, "lines": int} - computed once per build.
    """
    package = os.path.join(_PACKAGE_ROOT, "cybercrypt")
    modules = 0
    lines = 0
    for root, _dirs, files in os.walk(package):
        for name in files:
            if name.endswith(".py"):
                modules += 1
                try:
                    with open(os.path.join(root, name), encoding="utf-8") \
                            as handle:
                        lines += sum(1 for _ in handle)
                except OSError:
                    pass
    return {"modules": modules, "lines": lines}


_HELP_ITEMS = (
    ("How to Encrypt", ICONS["ENCRYPT"],
     "Type a message in the Encrypt screen, check the keys (or "
     "generate random ones) and press Encrypt. Watch the three "
     "layers run, then copy the cipher from the output box."),
    ("How to Decrypt", ICONS["DECRYPT"],
     "Paste the cipher into the Decrypt screen. The keys from the "
     "last encryption are pre-filled automatically - press Decrypt "
     "and the message is recovered in reverse order."),
    ("How to Read Analysis", ICONS["ANALYSIS"],
     "Open the Analysis screen after an encryption: message "
     "statistics, key information, performance timings, the "
     "educational strength meter, the encryption timeline and the "
     "algorithm overview."),
    ("How to Export Reports", ICONS["COPY"],
     "On the Analysis screen press TXT or JSON. The report is saved "
     "through a file dialog. Reports contain statistics only - the "
     "plain text is never written to disk."),
)

_SHORTCUTS = (
    ("Ctrl + Enter", "Run the main action of the current screen "
                     "(Encrypt / Decrypt)"),
    ("Ctrl + Shift + Enter", "Jump to the Decrypt screen and run it"),
    ("Ctrl + C", "Copy the output of the current screen"),
)


class GuideScreen(BaseScreen):
    """The help, shortcuts, project information and algorithms page."""

    # ------------------------------------------------------------------ #
    # Construction                                                        #
    # ------------------------------------------------------------------ #

    def _build_widgets(self):
        self._stats = _project_stats()

        self._page_header(
            "Guide",
            "How to use the application, its shortcuts and its "
            "project information.")

        self.scroll = self._page_scroll()

        self._build_help()
        self._build_shortcuts()
        self._build_project_info()
        self._build_algorithm_overview()

    def _section_heading(self, icon: str, heading: str):
        """A glass heading card for one section (shared widget)."""
        section_heading(self.scroll, icon, heading)
        return None

    # -- Help cards ---------------------------------------------------- #

    def _build_help(self):
        """Four how-to cards in a two by two grid."""
        self._section_heading(ICONS["GUIDE"], "How to Use the App")

        # Use a proper 2-column grid for consistent card sizing.
        grid = ctk.CTkFrame(self.scroll, fg_color="transparent")
        grid.pack(fill="x", padx=2)
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

        for index, (title, icon, body) in enumerate(_HELP_ITEMS):
            card = glass_panel(grid)
            row_pos = index // 2
            col_pos = index % 2
            card.grid(row=row_pos, column=col_pos, sticky="nsew",
                      padx=(0, 6) if col_pos == 0 else (6, 0),
                      pady=(0, 8))

            icon_box = ctk.CTkFrame(card, corner_radius=14, width=28,
                                    height=28,
                                    fg_color=COLORS["PRIMARY_DEEP"],
                                    border_width=1,
                                    border_color=COLORS["ACCENT"])
            icon_box.pack(side="left", padx=(16, 12), pady=14)
            icon_box.pack_propagate(False)
            icon_label = ctk.CTkLabel(icon_box, text=icon,
                                      font=("Segoe UI", 13, "bold"),
                                      text_color=COLORS["ACCENT"])
            icon_label.place(relx=0.5, rely=0.5, anchor="center")

            texts = ctk.CTkFrame(card, fg_color="transparent")
            texts.pack(side="left", fill="x", expand=True, pady=12)

            title_label = ctk.CTkLabel(texts, text=title,
                                       font=FONTS["BODY"],
                                       text_color=COLORS["TEXT"])
            title_label.pack(anchor="w")

            body_label = ctk.CTkLabel(
                texts, text=body,
                font=FONTS["MICRO"], text_color=COLORS["TEXT_MUTED"],
                justify="left", anchor="w", wraplength=420)
            body_label.pack(anchor="w", pady=(4, 0))

    # -- Shortcuts ------------------------------------------------------ #

    def _build_shortcuts(self):
        """The keyboard shortcut list."""
        self._section_heading(ICONS["INFO"], "Keyboard Shortcuts")

        card = glass_panel(self.scroll)
        card.pack(fill="x", padx=2, pady=(0, 8))

        for keys, description in _SHORTCUTS:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=5)

            key_badge = badge(row, keys, COLORS["ACCENT"])
            key_badge.pack(side="left")

            desc = ctk.CTkLabel(row, text=description,
                                font=FONTS["SMALL"],
                                text_color=COLORS["TEXT_MUTED"],
                                justify="left", anchor="w")
            desc.pack(side="left", padx=(16, 0))

    # -- Project information -------------------------------------------- #

    def _build_project_info(self):
        """Eight stat tiles about the project."""
        self._section_heading(ICONS["SHIELD"], "Project Information")

        framework = "CustomTkinter (Tkinter)"
        info = (
            ("Project Name", __title__, COLORS["ACCENT"]),
            ("Version", f"v{__version__}", COLORS["ACCENT"]),
            ("Python", sys.version.split()[0], COLORS["ACCENT"]),
            ("Framework", framework, COLORS["ACCENT"]),
            ("Architecture", "Modular \u00b7 Layered", COLORS["ACCENT"]),
            ("Algorithm Stack", ALGORITHM_STACK, COLORS["ACCENT"]),
            ("Lines of Code", f"~{self._stats['lines']}", COLORS["ACCENT"]),
            ("Modules", str(self._stats["modules"]), COLORS["ACCENT"]),
        )

        row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        row.pack(fill="x", padx=2, pady=(0, 8))

        for index, (caption, value, color) in enumerate(info):
            card = glass_panel(row)
            card.pack(side="left", fill="x", expand=True,
                      padx=4, pady=4)

            caption_label = ctk.CTkLabel(card, text=caption,
                                         font=FONTS["MICRO"],
                                         text_color=COLORS["TEXT_FAINT"])
            caption_label.pack(anchor="w", padx=14, pady=(12, 2))

            value_label = ctk.CTkLabel(
                card, text=value, font=FONTS["SMALL"],
                text_color=color, justify="left", anchor="w",
                wraplength=150)
            value_label.pack(anchor="w", padx=14, pady=(0, 12))

            if index % 4 == 3 and index < len(info) - 1:
                row = ctk.CTkFrame(self.scroll, fg_color="transparent")
                row.pack(fill="x", padx=2, pady=(0, 10))

    # -- Algorithm overview ---------------------------------------------- #

    def _build_algorithm_overview(self):
        """Three premium cards reusing the analysis data."""
        self._section_heading(ICONS["ALGO"], "Algorithm Overview")

        row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        row.pack(fill="x", padx=2, pady=(0, 12))

        for algorithm in ALGORITHM_OVERVIEW:
            card = glass_panel(row)
            card.pack(side="left", fill="x", expand=True,
                      padx=4, pady=4)

            icon_box = ctk.CTkFrame(card, corner_radius=16, width=32,
                                    height=32,
                                    fg_color=COLORS["PRIMARY_DEEP"],
                                    border_width=1,
                                    border_color=COLORS["ACCENT"])
            icon_box.pack(anchor="w", padx=16, pady=(14, 8))
            icon_box.pack_propagate(False)
            icon_label = ctk.CTkLabel(icon_box, text=algorithm["icon"],
                                      font=("Segoe UI", 15, "bold"),
                                      text_color=COLORS["ACCENT"])
            icon_label.place(relx=0.5, rely=0.5, anchor="center")

            name = ctk.CTkLabel(card, text=algorithm["name"],
                                font=FONTS["SUBHEADING"],
                                text_color=COLORS["TEXT"])
            name.pack(anchor="w", padx=16, pady=(0, 6))

            for caption, key, color in (
                    ("Purpose", "purpose", COLORS["TEXT_MUTED"]),
                    ("Advantages", "advantages", COLORS["SUCCESS"]),
                    ("Limitations", "limitations", COLORS["WARNING"])):
                line = ctk.CTkLabel(
                    card,
                    text=f"{caption}:  {algorithm[key]}",
                    font=FONTS["MICRO"], text_color=color,
                    justify="left", anchor="w", wraplength=260)
                line.pack(anchor="w", padx=16, pady=2)

            caption = ctk.CTkLabel(
                card, text=__subtitle__,
                font=FONTS["MICRO"], text_color=COLORS["TEXT_FAINT"])
            caption.pack(anchor="w", padx=16, pady=(10, 14))

    def on_show(self):
        """Force layout recalculation when the page becomes visible."""
        self.update_idletasks()

    def on_shortcut(self):
        """Ctrl+Enter scrolls the guide back to the top."""
        try:
            self.scroll._parent_canvas.yview_moveto(0.0)
        except Exception:
            pass
